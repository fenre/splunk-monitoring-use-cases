"""Tests for ``splunk_uc.audits.mapping_ledger``.

Phase 5.4 signed-provenance ledger audit. The audit is structurally
small (a handful of pure helpers + an orchestrating ``main``) but
was sitting at ~10 % coverage because every previous test path
required a real ``data/provenance/mapping-ledger.json`` AND a
matching live UC corpus. This file builds a synthetic, internally
consistent ledger inside ``tmp_path`` and drives every audit helper
against it, with monkey-patched subprocess + ``shutil.which`` for
the git / ``gh`` paths.

Every test stays hermetic — no real ledger is opened, no real
``git``/``gh`` binary is invoked, no real UC sidecar is read. The
audit's reliance on the generator's canonicalisation primitives
(``canonical_dump``, ``sha256_hex``, ``compute_merkle_root``,
``mapping_id_of``) is preserved unchanged so any future drift in
the generator immediately surfaces here.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import mapping_ledger as audit
from splunk_uc.generators import mapping_ledger as gen


# --------------------------------------------------------------------- #
# Hermetic ledger builder
# --------------------------------------------------------------------- #


def _entry(
    *,
    uc_id: str = "1.1.1",
    regulation_id: str = "iso27001-2022",
    clause: str = "A.8.16",
    mode: str = "satisfies",
    assurance: str = "full",
) -> tuple[dict[str, Any], str]:
    """Build one fully-canonical ledger entry and return
    (entry_dict, mappingId)."""

    li = gen.LedgerInput(
        uc_id=uc_id,
        uc_path=Path(f"content/cat-01-foo/UC-{uc_id}.json"),
        regulation_id=regulation_id,
        regulation_version="2022",
        clause=clause,
        mode=mode,
        assurance=assurance,
        # derivation_source is an optional dict (parent regulation
        # propagation metadata); ``None`` matches the most common
        # sidecar shape and keeps the canonical payload minimal.
        derivation_source=None,
    )
    mid = gen.mapping_id_of(li)
    canonical = gen.canonical_entry_payload(li, mid)
    canonical["canonicalHash"] = gen.sha256_hex(gen.canonical_dump(canonical))
    # Schema requires three extra ledger-metadata fields per entry —
    # they are NOT part of the canonical payload (they don't feed the
    # hash) but they ARE required by the JSON schema, so a hermetic
    # test ledger needs them or ``validate_schema`` flags every entry
    # as missing required properties.
    canonical["firstSeenCommit"] = "abc1234"
    canonical["lastModifiedCommit"] = "abc1234"
    canonical["signoffStatus"] = {
        "peer": {"required": False, "status": "not-required"},
        "legal": {"required": False, "status": "not-required"},
        "sme": {"required": False, "status": "not-required"},
    }
    return canonical, mid


def _ledger(
    entries: list[dict[str, Any]],
    *,
    state: str = "unsigned",
    commit: str = "abc1234",
    extra_sig: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a fully consistent ledger dict — entries are pre-sorted,
    entryCount matches, merkleRoot is recomputed, signature envelope
    is well-formed."""

    sorted_entries = sorted(entries, key=lambda e: e["mappingId"])
    sig: dict[str, Any] = {"state": state}
    if state == "attested":
        sig["commit"] = commit
    if extra_sig:
        sig.update(extra_sig)
    return {
        "schemaVersion": "1.1.0",
        "generatedAt": "2026-05-20T00:00:00Z",
        "catalogueCommit": commit,
        "merkleRoot": gen.compute_merkle_root(sorted_entries),
        "hashAlgorithm": "sha256",
        # ``canonicalisation`` is an object per the schema — three
        # required keys document the hash contract.
        "canonicalisation": {
            "algorithm": "rfc8785",
            "jsonForm": "utf-8-nfc-sorted-keys-no-whitespace",
            "fieldOrder": list(gen.CANONICAL_FIELD_ORDER),
        },
        "entryCount": len(sorted_entries),
        "signature": sig,
        "entries": sorted_entries,
    }


# --------------------------------------------------------------------- #
# validate_schema
# --------------------------------------------------------------------- #


def test_validate_schema_accepts_canonical_ledger() -> None:
    entry, _ = _entry()
    assert audit.validate_schema(_ledger([entry])) == []


def test_validate_schema_rejects_missing_top_level_field() -> None:
    """When ``jsonschema`` is available, this surfaces a path-tagged
    error; when it isn't, the manual fallback fires. Either way the
    audit MUST report a missing-field error."""

    bad = _ledger([_entry()[0]])
    del bad["merkleRoot"]
    errors = audit.validate_schema(bad)
    assert errors
    assert any("merkleRoot" in e for e in errors)


def test_validate_schema_fallback_when_jsonschema_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate a dev box without ``jsonschema`` installed — the
    audit must fall back to the structural top-level-field check
    instead of crashing on ImportError."""

    import builtins

    real_import = builtins.__import__

    def _no_jsonschema(name: str, *a: object, **kw: object) -> object:
        if name == "jsonschema":
            raise ImportError("simulated: jsonschema missing")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _no_jsonschema)

    bad = _ledger([_entry()[0]])
    del bad["entryCount"]
    errors = audit.validate_schema(bad)
    assert any("entryCount" in e for e in errors)


# --------------------------------------------------------------------- #
# audit_entry_hashes
# --------------------------------------------------------------------- #


def test_audit_entry_hashes_passes_on_correct_hash() -> None:
    entry, _ = _entry()
    assert audit.audit_entry_hashes(_ledger([entry])) == []


def test_audit_entry_hashes_flags_mismatch() -> None:
    entry, mid = _entry()
    entry["canonicalHash"] = "0" * 64  # corrupt
    errors = audit.audit_entry_hashes(_ledger([entry]))
    assert len(errors) == 1
    assert "canonicalHash mismatch" in errors[0]
    assert mid in errors[0]


def test_audit_entry_hashes_flags_duplicate_mapping_id() -> None:
    entry, _ = _entry()
    dup = dict(entry)  # same mappingId
    errors = audit.audit_entry_hashes(_ledger([entry, dup]))
    assert any("duplicate mappingId" in e for e in errors)


# --------------------------------------------------------------------- #
# audit_merkle_root
# --------------------------------------------------------------------- #


def test_audit_merkle_root_passes_on_canonical_root() -> None:
    entry, _ = _entry()
    assert audit.audit_merkle_root(_ledger([entry])) == []


def test_audit_merkle_root_flags_mismatch() -> None:
    entry, _ = _entry()
    ledger = _ledger([entry])
    ledger["merkleRoot"] = "deadbeef" * 8  # corrupt
    errors = audit.audit_merkle_root(ledger)
    assert errors and "merkleRoot mismatch" in errors[0]


# --------------------------------------------------------------------- #
# audit_entry_count
# --------------------------------------------------------------------- #


def test_audit_entry_count_passes_on_match() -> None:
    entry, _ = _entry()
    assert audit.audit_entry_count(_ledger([entry])) == []


def test_audit_entry_count_flags_mismatch() -> None:
    entry, _ = _entry()
    ledger = _ledger([entry])
    ledger["entryCount"] = 99
    errors = audit.audit_entry_count(ledger)
    assert errors and "stored=99" in errors[0]


# --------------------------------------------------------------------- #
# audit_sort_order
# --------------------------------------------------------------------- #


def test_audit_sort_order_passes_when_sorted() -> None:
    e1, _ = _entry(uc_id="1.1.1")
    e2, _ = _entry(uc_id="1.1.2")
    assert audit.audit_sort_order(_ledger([e1, e2])) == []


def test_audit_sort_order_flags_out_of_order_entries() -> None:
    e1, _ = _entry(uc_id="1.1.1")
    e2, _ = _entry(uc_id="1.1.2")
    bad = _ledger([e1, e2])
    bad["entries"] = list(reversed(bad["entries"]))  # break sort
    errors = audit.audit_sort_order(bad)
    assert errors and "not sorted" in errors[0]


# --------------------------------------------------------------------- #
# audit_referential_integrity — gather_sidecar_mappings is monkey-
# patched so we don't depend on the real corpus.
# --------------------------------------------------------------------- #


def test_referential_integrity_passes_when_sets_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry, mid = _entry()
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})
    assert audit.audit_referential_integrity(_ledger([entry])) == []


def test_referential_integrity_flags_sidecar_missing_from_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    e1, mid1 = _entry(uc_id="1.1.1")
    _, mid2 = _entry(uc_id="1.1.2")  # in sidecars but not ledger
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid1, mid2})
    errors = audit.audit_referential_integrity(_ledger([e1]))
    assert any("has no ledger entry" in e for e in errors)
    assert any(mid2 in e for e in errors)


def test_referential_integrity_flags_ledger_orphan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    e1, mid1 = _entry(uc_id="1.1.1")
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: set())
    errors = audit.audit_referential_integrity(_ledger([e1]))
    assert any("has no backing sidecar" in e for e in errors)
    assert any(mid1 in e for e in errors)


def test_referential_integrity_truncates_to_twenty_per_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A massive drift must not flood the report with 1k+ lines — the
    audit truncates each side at 20 plus a "…and N more" line."""

    extra_ids = {f"sidecar-only-{i:03d}" for i in range(25)}
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: extra_ids)
    errors = audit.audit_referential_integrity(_ledger([]))
    truncation_lines = [e for e in errors if "more sidecar mappings missing" in e]
    assert len(truncation_lines) == 1
    assert "5 more" in truncation_lines[0]  # 25 - 20 = 5


# --------------------------------------------------------------------- #
# audit_catalogue_commit — subprocess.run mocked
# --------------------------------------------------------------------- #


def _fake_proc(stdout: str = "", rc: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=rc, stdout=stdout, stderr="")


def test_audit_catalogue_commit_passes_when_head_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _fake_proc("abc1234\n"))
    ledger = _ledger([_entry()[0]], commit="abc1234")
    assert audit.audit_catalogue_commit(ledger) == []


def test_audit_catalogue_commit_warns_on_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mismatch must emit an *informational* warning, not a hard error
    (the generator's own --check step is the enforcement layer)."""

    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _fake_proc("deadbee\n"))
    ledger = _ledger([_entry()[0]], commit="abc1234")
    warnings = audit.audit_catalogue_commit(ledger)
    assert len(warnings) == 1
    assert "informational" in warnings[0]
    assert "abc1234" in warnings[0]
    assert "deadbee" in warnings[0]


def test_audit_catalogue_commit_silent_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise OSError("git not installed")

    monkeypatch.setattr(audit.subprocess, "run", _raise)
    assert audit.audit_catalogue_commit(_ledger([_entry()[0]])) == []


def test_audit_catalogue_commit_silent_on_malformed_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-hex head (e.g. detached, broken repo) gracefully degrades
    to "no opinion"."""

    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _fake_proc("not-a-sha\n"))
    assert audit.audit_catalogue_commit(_ledger([_entry()[0]])) == []


# --------------------------------------------------------------------- #
# audit_signature_envelope
# --------------------------------------------------------------------- #


def test_signature_envelope_unsigned_passes_by_default(tmp_path: Path) -> None:
    ledger = _ledger([_entry()[0]], state="unsigned")
    assert audit.audit_signature_envelope(
        ledger, verify_signature=False, require_signature=False, ledger_file=tmp_path / "x"
    ) == []


def test_signature_envelope_unsigned_fails_when_required(tmp_path: Path) -> None:
    ledger = _ledger([_entry()[0]], state="unsigned")
    errors = audit.audit_signature_envelope(
        ledger, verify_signature=False, require_signature=True, ledger_file=tmp_path / "x"
    )
    assert errors and "state=unsigned" in errors[0]


def test_signature_envelope_attested_passes_with_matching_commit(
    tmp_path: Path,
) -> None:
    ledger = _ledger([_entry()[0]], state="attested", commit="abc1234")
    assert audit.audit_signature_envelope(
        ledger, verify_signature=False, require_signature=False, ledger_file=tmp_path / "x"
    ) == []


def test_signature_envelope_attested_flags_commit_mismatch(
    tmp_path: Path,
) -> None:
    entry, _ = _entry()
    ledger = _ledger(
        [entry],
        state="attested",
        commit="abc1234",
        extra_sig={"commit": "other999"},
    )
    errors = audit.audit_signature_envelope(
        ledger, verify_signature=False, require_signature=False, ledger_file=tmp_path / "x"
    )
    assert any("does not match" in e for e in errors)


def test_signature_envelope_unknown_state_is_fatal(tmp_path: Path) -> None:
    ledger = _ledger([_entry()[0]])
    ledger["signature"] = {"state": "weird"}
    errors = audit.audit_signature_envelope(
        ledger, verify_signature=False, require_signature=False, ledger_file=tmp_path / "x"
    )
    assert errors and "unknown state" in errors[0]


# --------------------------------------------------------------------- #
# _resolve_bundle_path — three candidate roots
# --------------------------------------------------------------------- #


def test_resolve_bundle_path_finds_sibling_of_ledger_file(
    tmp_path: Path,
) -> None:
    ledger_file = tmp_path / "mapping-ledger.json"
    ledger_file.write_text("{}", encoding="utf-8")
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{}", encoding="utf-8")
    resolved = audit._resolve_bundle_path("bundle.json", ledger_file)
    assert resolved == bundle.resolve()


def test_resolve_bundle_path_returns_none_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Point ROOT at an empty tmp_path so the "repo-relative" and
    # "dist/" candidates also miss.
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    ledger_file = tmp_path / "ledger.json"
    ledger_file.touch()
    assert audit._resolve_bundle_path("nope.json", ledger_file) is None


# --------------------------------------------------------------------- #
# _run_gh_attestation_verify — gh CLI mocked
# --------------------------------------------------------------------- #


def test_gh_verify_skips_when_gh_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: None)
    errors = audit._run_gh_attestation_verify(
        sig={"bundlePath": "x.bundle"},
        ledger={},
        ledger_file=tmp_path / "x.json",
    )
    assert errors and "`gh` CLI is not installed" in errors[0]


def test_gh_verify_no_op_when_no_bundle_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Signature envelopes that record the attestation only on
    GitHub (no local bundle) skip verification cleanly."""

    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    assert audit._run_gh_attestation_verify(
        sig={},  # no bundlePath
        ledger={},
        ledger_file=tmp_path / "x.json",
    ) == []


def test_gh_verify_reports_missing_bundle_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    errors = audit._run_gh_attestation_verify(
        sig={"bundlePath": "missing.bundle"},
        ledger={},
        ledger_file=tmp_path / "x.json",
    )
    assert errors and "not found" in errors[0]


def test_gh_verify_reports_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    bundle = tmp_path / "b.bundle"
    bundle.touch()
    ledger_file = tmp_path / "ledger.json"
    ledger_file.touch()

    def _boom(*a: object, **k: object) -> None:
        raise OSError("fork failed")

    monkeypatch.setattr(audit.subprocess, "run", _boom)
    errors = audit._run_gh_attestation_verify(
        sig={"bundlePath": "b.bundle"},
        ledger={},
        ledger_file=ledger_file,
    )
    assert errors and "failed to execute" in errors[0]


def test_gh_verify_reports_rejection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    bundle = tmp_path / "b.bundle"
    bundle.touch()
    ledger_file = tmp_path / "ledger.json"
    ledger_file.touch()

    def _reject(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=a[0],
            returncode=1,
            stdout="",
            stderr="bundle verification failed",
        )

    monkeypatch.setattr(audit.subprocess, "run", _reject)
    errors = audit._run_gh_attestation_verify(
        sig={"bundlePath": "b.bundle"},
        ledger={},
        ledger_file=ledger_file,
    )
    assert errors and "rejected the bundle" in errors[0]


def test_gh_verify_passes_silently_on_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    bundle = tmp_path / "b.bundle"
    bundle.touch()
    ledger_file = tmp_path / "ledger.json"
    ledger_file.touch()
    monkeypatch.setattr(
        audit.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(args=a[0], returncode=0, stdout="ok", stderr=""),
    )
    assert audit._run_gh_attestation_verify(
        sig={"bundlePath": "b.bundle"},
        ledger={},
        ledger_file=ledger_file,
    ) == []


# --------------------------------------------------------------------- #
# write_report
# --------------------------------------------------------------------- #


def test_write_report_writes_pass_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = tmp_path / "audit-out.json"
    monkeypatch.setattr(audit, "REPORT_PATH", report)
    ledger = _ledger([_entry()[0]])

    audit.write_report([], ledger)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["errorCount"] == 0
    assert payload["errors"] == []
    assert payload["ledgerSummary"]["entryCount"] == ledger["entryCount"]
    assert payload["ledgerSummary"]["signatureState"] == "unsigned"


def test_write_report_writes_fail_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = tmp_path / "audit-out.json"
    monkeypatch.setattr(audit, "REPORT_PATH", report)
    audit.write_report(["something is wrong"], _ledger([_entry()[0]]))
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["errorCount"] == 1
    assert payload["errors"] == ["something is wrong"]


# --------------------------------------------------------------------- #
# main — orchestration with mocked sub-audits
# --------------------------------------------------------------------- #


def _hermetic_main_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ledger: dict[str, Any],
) -> Path:
    """Set up ``ROOT``, ``LEDGER_PATH`` + ``REPORT_PATH`` inside
    ``tmp_path``, stub git/gh subprocess + ``gather_sidecar_mappings``
    so ``main`` runs in isolation, and write ``ledger`` to disk.

    ``ROOT`` MUST be repointed too because ``main``'s FATAL print
    calls ``LEDGER_PATH.relative_to(ROOT)`` — leaving ROOT at the
    real repo root would raise ``ValueError: ... not in the subpath
    of ...`` and obscure the assertion we actually care about.

    Returns the report path so callers can introspect it.
    """

    ledger_path = tmp_path / "mapping-ledger.json"
    report_path = tmp_path / "report.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(audit, "REPORT_PATH", report_path)
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _fake_proc("abc1234\n"))
    return report_path


def test_main_returns_one_when_ledger_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LEDGER_PATH", tmp_path / "no-such.json")
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "does not exist" in err


def test_main_returns_one_on_invalid_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LEDGER_PATH", ledger_path)
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "not valid JSON" in err


def test_main_pass_path_writes_report_and_returns_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entry, mid = _entry()
    ledger = _ledger([entry])
    report_path = _hermetic_main_env(tmp_path, monkeypatch, ledger)
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})

    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PASS: mapping ledger OK" in out
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"


def test_main_fail_path_emits_error_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entry, mid = _entry()
    ledger = _ledger([entry])
    ledger["entryCount"] = 99  # induce a known mismatch
    _hermetic_main_env(tmp_path, monkeypatch, ledger)
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})

    rc = audit.main([])
    cap = capsys.readouterr()
    assert rc == 1
    assert "FAIL: mapping-ledger audit found issues" in cap.err
    assert "entryCount" in cap.err


def test_main_truncates_long_error_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Stub validate_schema to return 50 errors; main MUST print the
    first 40 then a "…and 10 more" summary."""

    entry, mid = _entry()
    ledger = _ledger([entry])
    _hermetic_main_env(tmp_path, monkeypatch, ledger)
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})
    monkeypatch.setattr(
        audit,
        "validate_schema",
        lambda lg: [f"schema: synthetic-error-{i}" for i in range(50)],
    )

    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "and 10 more errors" in err


def test_main_emits_catalogue_commit_warning_to_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A catalogue-commit / git-HEAD divergence is informational — it
    should print a WARN line on stderr but still exit 0."""

    entry, mid = _entry()
    ledger = _ledger([entry], commit="abc1234")
    ledger_path = tmp_path / "ledger.json"
    report_path = tmp_path / "report.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(audit, "REPORT_PATH", report_path)
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})
    # Stub head MUST be valid hex (7-40 chars) — the audit's
    # ``re.fullmatch(r"[0-9a-f]{7,40}", head)`` guard otherwise
    # silently returns ``[]`` and the WARN never fires.
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _fake_proc("deadbee\n"))

    rc = audit.main([])
    cap = capsys.readouterr()
    assert rc == 0
    assert "WARN" in cap.err
    assert "informational" in cap.err


def test_main_require_signature_promotes_unsigned_to_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry, mid = _entry()
    ledger = _ledger([entry], state="unsigned")
    _hermetic_main_env(tmp_path, monkeypatch, ledger)
    monkeypatch.setattr(audit, "gather_sidecar_mappings", lambda: {mid})
    assert audit.main(["--require-signature"]) == 1


# --------------------------------------------------------------------- #
# gather_sidecar_mappings — exercise only the no-corpus path so we
# don't depend on the live UC tree.
# --------------------------------------------------------------------- #


def test_gather_sidecar_mappings_returns_empty_when_no_sidecars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub ``iter_uc_sidecars`` to an empty iterator so we exercise
    the gather loop without touching the real corpus."""

    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter([]))
    assert audit.gather_sidecar_mappings() == set()


def test_gather_sidecar_mappings_handles_minimal_sidecar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """One synthetic UC with one valid compliance entry must produce
    exactly one mappingId via the generator's helpers."""

    sidecar = tmp_path / "UC-1.1.1.json"
    sidecar.write_text(
        json.dumps(
            {
                "id": "1.1.1",
                "compliance": [
                    {
                        "regulation": "iso27001-2022",
                        "version": "2022",
                        "clause": "A.8.16",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter([sidecar]))
    monkeypatch.setattr(
        audit,
        "load_regulation_index",
        lambda: {"iso27001-2022": {"iso27001-2022", "iso/iec 27001:2022"}},
    )
    monkeypatch.setattr(
        audit, "resolve_regulation_id", lambda name, idx: "iso27001-2022"
    )
    monkeypatch.setattr(
        audit, "normalise_version", lambda rid, v: "2022"
    )

    result = audit.gather_sidecar_mappings()
    assert len(result) == 1
