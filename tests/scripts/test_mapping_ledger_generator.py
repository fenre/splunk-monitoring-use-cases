"""Coverage-uplift suite for ``splunk_uc.generators.mapping_ledger``.

The signed-provenance ledger generator had 0% test coverage prior to this
file. The strategy is:

* Pure helpers (``canonical_dump``, ``sha256_hex``, ``_git_short``,
  ``mapping_id_of``, ``canonical_entry_payload``, ``compute_merkle_root``,
  ``normalise_version``, ``resolve_regulation_id``,
  ``signoff_status_for``, ``render``, ``_structural_diff``) — exercise
  directly with hand-crafted fixtures.
* IO + subprocess helpers (``catalogue_head_commit``, ``commit_date_iso``,
  ``deterministic_generated_at``, ``_populate_git_caches_bulk``,
  ``load_regulation_index``, ``iter_uc_sidecars``, ``load_signoffs``,
  ``build_auxiliary_sources``) — exercise with ``tmp_path`` and
  ``monkeypatch`` overrides of the module constants and
  ``ml.subprocess.run``.
* Orchestration (``build_ledger_inputs``, ``build_ledger``, ``main``,
  ``_preview_diff``) — full happy-path + error-path coverage with a small
  fixture catalogue.

All tests are hermetic: no real CWD, no real git, no real filesystem
outside the per-test ``tmp_path``.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.generators import mapping_ledger as ml  # noqa: E402

# ---------------------------------------------------------------------------
# Test-isolation fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_git_caches():
    """Reset module-level git caches so test order is irrelevant."""
    ml._git_first_seen_cache.clear()
    ml._git_last_modified_cache.clear()
    ml._git_bulk_populated = False
    yield
    ml._git_first_seen_cache.clear()
    ml._git_last_modified_cache.clear()
    ml._git_bulk_populated = False


def _wire_repo(monkeypatch, tmp_path: Path) -> Path:
    """Build a small fixture repo under ``tmp_path`` and rewire the module."""
    repo = tmp_path / "repo"
    (repo / "content" / "cat-01-foo").mkdir(parents=True)
    (repo / "data" / "provenance").mkdir(parents=True)
    monkeypatch.setattr(ml, "ROOT", repo)
    monkeypatch.setattr(ml, "CONTENT_DIR", repo / "content")
    monkeypatch.setattr(ml, "REGULATIONS_JSON", repo / "data" / "regulations.json")
    monkeypatch.setattr(
        ml, "LEDGER_PATH", repo / "data" / "provenance" / "mapping-ledger.json"
    )
    monkeypatch.setattr(ml, "SIGNOFFS_DIR", repo / "data" / "provenance")
    return repo


def _regulations_payload() -> dict[str, Any]:
    return {
        "frameworks": [
            {"id": "gdpr", "versions": [{"version": "2016/679"}]},
            {"id": "pci-dss", "versions": [{"version": "4.0"}]},
            {"id": "meta-multi", "versions": []},
        ]
    }


def _uc(
    uc_id: str,
    *,
    regulation: str = "GDPR",
    version: str = "2016/679",
    clause: str = "Art.32",
    mode: str = "satisfies",
    assurance: str = "full",
    derivation: dict[str, Any] | None = None,
    extra_compliance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    compliance = [
        {
            "regulation": regulation,
            "version": version,
            "clause": clause,
            "mode": mode,
            "assurance": assurance,
        }
    ]
    if derivation is not None:
        compliance[0]["derivationSource"] = derivation
    if extra_compliance:
        compliance.extend(extra_compliance)
    return {"id": uc_id, "compliance": compliance}


def _write_uc(repo: Path, filename: str, payload: dict[str, Any]) -> Path:
    target = repo / "content" / "cat-01-foo" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_canonical_dump_is_sorted_and_compact():
    out = ml.canonical_dump({"b": 2, "a": 1})
    assert out == '{"a":1,"b":2}'


def test_canonical_dump_preserves_unicode():
    out = ml.canonical_dump({"ü": "日本"})
    assert "ü" in out
    assert "日本" in out


def test_sha256_hex_matches_known_value():
    assert ml.sha256_hex("") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


@pytest.mark.parametrize(
    "sha,expected",
    [
        ("abc1234def", "abc1234"),
        ("short", "short"),  # input shorter than 7 chars
        ("a" * 40, "aaaaaaa"),
    ],
)
def test_git_short(sha, expected):
    assert ml._git_short(sha) == expected


def test_mapping_id_of_concatenates_parts():
    entry = ml.LedgerInput(
        uc_id="1.1.1",
        uc_path=pathlib.Path("/tmp/x.json"),
        regulation_id="gdpr",
        regulation_version="2016/679",
        clause="Art.32",
        mode="satisfies",
        assurance="full",
        derivation_source=None,
    )
    assert ml.mapping_id_of(entry) == "1.1.1::gdpr@2016/679::Art.32::satisfies::full"


def test_canonical_entry_payload_without_derivation():
    entry = ml.LedgerInput(
        uc_id="1.1.1",
        uc_path=pathlib.Path("/tmp/x.json"),
        regulation_id="gdpr",
        regulation_version="2016/679",
        clause="Art.32",
        mode="satisfies",
        assurance="full",
        derivation_source=None,
    )
    payload = ml.canonical_entry_payload(entry, "mid")
    assert "derivationSource" not in payload
    assert payload["mappingId"] == "mid"
    assert payload["regulationId"] == "gdpr"


def test_canonical_entry_payload_with_derivation_omits_optional_fields():
    entry = ml.LedgerInput(
        uc_id="1.1.1",
        uc_path=pathlib.Path("/tmp/x.json"),
        regulation_id="uk-gdpr",
        regulation_version="2018-final",
        clause="Art.32",
        mode="satisfies",
        assurance="full",
        derivation_source={
            "parentRegulation": "GDPR",
            "parentVersion": "2016/679",
            "parentClause": "Art.32",
            "inheritanceMode": "identity",
        },
    )
    payload = ml.canonical_entry_payload(entry, "mid")
    ds = payload["derivationSource"]
    assert ds["parentRegulation"] == "GDPR"
    assert "parentAssurance" not in ds
    assert "divergenceNote" not in ds


def test_canonical_entry_payload_with_derivation_includes_optionals_when_set():
    entry = ml.LedgerInput(
        uc_id="1.1.1",
        uc_path=pathlib.Path("/tmp/x.json"),
        regulation_id="uk-gdpr",
        regulation_version="2018-final",
        clause="Art.32",
        mode="satisfies",
        assurance="full",
        derivation_source={
            "parentRegulation": "GDPR",
            "parentVersion": "2016/679",
            "parentClause": "Art.32",
            "inheritanceMode": "modify",
            "parentAssurance": "partial",
            "divergenceNote": "UK-specific tightening",
        },
    )
    payload = ml.canonical_entry_payload(entry, "mid")
    ds = payload["derivationSource"]
    assert ds["parentAssurance"] == "partial"
    assert ds["divergenceNote"] == "UK-specific tightening"


def test_canonical_entry_payload_with_empty_derivation_uses_blank_strings():
    """Empty-dict derivation should still emit the 4 required fields."""
    entry = ml.LedgerInput(
        uc_id="1.1.1",
        uc_path=pathlib.Path("/tmp/x.json"),
        regulation_id="x",
        regulation_version="1",
        clause="c",
        mode="satisfies",
        assurance="full",
        derivation_source={"parentRegulation": ""},  # truthy dict, mostly empty
    )
    payload = ml.canonical_entry_payload(entry, "mid")
    ds = payload["derivationSource"]
    assert ds == {
        "parentRegulation": "",
        "parentVersion": "",
        "parentClause": "",
        "inheritanceMode": "",
    }


def test_compute_merkle_root_changes_when_entries_change():
    e1 = {"canonicalHash": "aa"}
    e2 = {"canonicalHash": "bb"}
    r1 = ml.compute_merkle_root([e1, e2])
    r2 = ml.compute_merkle_root([e1])
    assert r1 != r2


def test_compute_merkle_root_handles_empty():
    h = ml.compute_merkle_root([])
    # Domain-separator-only hash, deterministic.
    assert h == ml.compute_merkle_root([])
    assert len(h) == 64


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2016/679", "2016/679"),
        ("  2016/679  ", "2016/679"),
        ("", "n/a"),
        ("   ", "n/a"),
    ],
)
def test_normalise_version(raw, expected):
    assert ml.normalise_version("gdpr", raw) == expected


# ---------------------------------------------------------------------------
# Regulation index + name resolution
# ---------------------------------------------------------------------------


def test_load_regulation_index_includes_meta_multi_na(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations_payload()), encoding="utf-8"
    )
    idx = ml.load_regulation_index()
    assert idx["gdpr"] == {"2016/679"}
    assert idx["pci-dss"] == {"4.0"}
    # meta-multi gets the 'n/a' sentinel even without explicit versions.
    assert "n/a" in idx["meta-multi"]


def test_resolve_regulation_id_uses_name_table():
    idx = {"gdpr": {"2016/679"}}
    assert ml.resolve_regulation_id("GDPR", idx) == "gdpr"


def test_resolve_regulation_id_lowercase_match_when_table_misses():
    idx = {"acme-x": {"1.0"}}
    assert ml.resolve_regulation_id("ACME-X", idx) == "acme-x"


def test_resolve_regulation_id_raises_when_unknown():
    with pytest.raises(KeyError, match="no entry in"):
        ml.resolve_regulation_id("Unknown-Reg", {})


# ---------------------------------------------------------------------------
# iter_uc_sidecars
# ---------------------------------------------------------------------------


def test_iter_uc_sidecars_returns_nothing_when_content_dir_missing(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(ml, "CONTENT_DIR", tmp_path / "no-such-dir")
    assert list(ml.iter_uc_sidecars()) == []


def test_iter_uc_sidecars_dedupes_by_id(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    _write_uc(repo, "UC-1.1.1.json", {"id": "1.1.1"})
    _write_uc(repo, "UC-1.1.1-dup.json", {"id": "1.1.1"})
    paths = list(ml.iter_uc_sidecars())
    assert len(paths) == 1


def test_iter_uc_sidecars_skips_malformed_json(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    bad = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    bad.write_text("{ broken", encoding="utf-8")
    _write_uc(repo, "UC-1.1.2.json", {"id": "1.1.2"})
    paths = list(ml.iter_uc_sidecars())
    assert len(paths) == 1
    assert paths[0].name == "UC-1.1.2.json"


def test_iter_uc_sidecars_skips_non_dict_payloads(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        "[1, 2]", encoding="utf-8"
    )
    _write_uc(repo, "UC-1.1.2.json", {"id": "1.1.2"})
    paths = list(ml.iter_uc_sidecars())
    assert len(paths) == 1


def test_iter_uc_sidecars_skips_payload_missing_id(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-noid.json").write_text(
        json.dumps({"title": "no id here"}), encoding="utf-8"
    )
    _write_uc(repo, "UC-1.1.2.json", {"id": "1.1.2"})
    paths = list(ml.iter_uc_sidecars())
    assert len(paths) == 1


# ---------------------------------------------------------------------------
# _populate_git_caches_bulk + git_*_commit helpers
# ---------------------------------------------------------------------------


def _fake_git_log(stdout: str):
    """Return a fake subprocess.run that returns ``stdout`` once."""

    class _R:
        def __init__(self, out: str):
            self.stdout = out

    def runner(*_a, **_k):
        return _R(stdout)

    return runner


def test_populate_git_caches_bulk_short_circuits_when_no_paths(monkeypatch):
    """Empty path list flips the populated flag without calling git."""
    called = {"n": 0}

    def fake_run(*_a, **_k):
        called["n"] += 1
        return type("X", (), {"stdout": ""})()

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    ml._populate_git_caches_bulk([])
    assert ml._git_bulk_populated is True
    assert called["n"] == 0


def test_populate_git_caches_bulk_idempotent(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    p = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    p.write_text("{}", encoding="utf-8")
    ml._git_bulk_populated = True
    called = {"n": 0}
    monkeypatch.setattr(ml.subprocess, "run", lambda *a, **k: called.update(n=1))
    ml._populate_git_caches_bulk([p])
    assert called["n"] == 0


def test_populate_git_caches_bulk_handles_subprocess_error_pass1(
    monkeypatch, tmp_path: Path
):
    repo = _wire_repo(monkeypatch, tmp_path)
    p = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    p.write_text("{}", encoding="utf-8")

    def fake_run(*_a, **_k):
        raise OSError("git not found")

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    ml._populate_git_caches_bulk([p])
    # Cache stays empty; flag flipped so we never retry.
    assert ml._git_bulk_populated is True
    assert p not in ml._git_first_seen_cache


def test_populate_git_caches_bulk_handles_subprocess_error_pass2(
    monkeypatch, tmp_path: Path
):
    repo = _wire_repo(monkeypatch, tmp_path)
    p = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    p.write_text("{}", encoding="utf-8")

    calls = {"n": 0}

    def fake_run(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            # Pass 1 succeeds with a lastModified record.
            return type("R", (), {"stdout": "abc1234abc1234abc1234abc1234abc1234abc12\ncontent/cat-01-foo/UC-1.1.1.json\n"})()
        # Pass 2 fails.
        raise subprocess.SubprocessError("boom")

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    ml._populate_git_caches_bulk([p])
    assert ml._git_bulk_populated is True
    # Pass 1 result survived; pass 2 left first-seen unpopulated.
    assert ml._git_last_modified_cache[p] == "abc1234"
    assert p not in ml._git_first_seen_cache


def test_populate_git_caches_bulk_happy_path(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    p = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    p.write_text("{}", encoding="utf-8")
    sha_new = "aaaaaaa" + "0" * 33
    sha_old = "bbbbbbb" + "0" * 33

    # Pass 1 lastModified: newest-first → take the first record we see.
    pass1 = f"{sha_new}\ncontent/cat-01-foo/UC-1.1.1.json\n{sha_old}\ncontent/cat-01-foo/UC-1.1.1.json\n"
    # Pass 2 firstSeen --diff-filter=A: walk newest-first and overwrite.
    pass2 = pass1
    outputs = iter([pass1, pass2])

    def fake_run(*_a, **_k):
        return type("R", (), {"stdout": next(outputs)})()

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    ml._populate_git_caches_bulk([p])
    assert ml._git_last_modified_cache[p] == sha_new[:7]
    # firstSeen ends up as the LAST add seen → sha_old.
    assert ml._git_first_seen_cache[p] == sha_old[:7]


def test_populate_git_caches_bulk_ignores_path_lines_before_first_sha(
    monkeypatch, tmp_path: Path
):
    repo = _wire_repo(monkeypatch, tmp_path)
    p = repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
    p.write_text("{}", encoding="utf-8")
    sha = "f" * 40
    # A leading path line before any sha exercises the `current_sha is None`
    # continuation in both passes. A trailing empty line exercises the
    # `if not line: continue` branch.
    blob = f"\ncontent/cat-01-foo/UC-1.1.1.json\n{sha}\ncontent/cat-01-foo/UC-1.1.1.json\n\n"
    outputs = iter([blob, blob])

    def fake_run(*_a, **_k):
        return type("R", (), {"stdout": next(outputs)})()

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    ml._populate_git_caches_bulk([p])
    assert ml._git_last_modified_cache[p] == sha[:7]
    assert ml._git_first_seen_cache[p] == sha[:7]


def test_git_first_seen_and_last_modified_helpers_return_cache_value():
    p = pathlib.Path("/tmp/uc.json")
    ml._git_first_seen_cache[p] = "deadbee"
    ml._git_last_modified_cache[p] = "feedbee"
    assert ml.git_first_seen_commit(p) == "deadbee"
    assert ml.git_last_modified_commit(p) == "feedbee"
    assert ml.git_first_seen_commit(pathlib.Path("/missing")) is None


# ---------------------------------------------------------------------------
# catalogue_head_commit + commit_date_iso + deterministic_generated_at
# ---------------------------------------------------------------------------


def test_catalogue_head_commit_uses_subprocess_output(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "abc1234\n"})(),
    )
    assert ml.catalogue_head_commit() == "abc1234"


def test_catalogue_head_commit_rejects_non_hex(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "not-a-hash"})(),
    )
    assert ml.catalogue_head_commit() == "0000000"


def test_catalogue_head_commit_handles_subprocess_error(monkeypatch):
    def fake_run(*_a, **_k):
        raise OSError("no git")

    monkeypatch.setattr(ml.subprocess, "run", fake_run)
    assert ml.catalogue_head_commit() == "0000000"


def test_commit_date_iso_returns_none_on_empty(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "  \n"})(),
    )
    assert ml.commit_date_iso("abc") is None


def test_commit_date_iso_normalises_aware_datetime(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "2026-05-20T10:00:00+02:00\n"})(),
    )
    assert ml.commit_date_iso("abc") == "2026-05-20T08:00:00Z"


def test_commit_date_iso_handles_naive_datetime(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "2026-05-20T10:00:00\n"})(),
    )
    assert ml.commit_date_iso("abc") == "2026-05-20T10:00:00Z"


def test_commit_date_iso_returns_none_on_subprocess_error(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("no git")),
    )
    assert ml.commit_date_iso("abc") is None


def test_commit_date_iso_returns_none_on_value_error(monkeypatch):
    monkeypatch.setattr(
        ml.subprocess,
        "run",
        lambda *a, **k: type("R", (), {"stdout": "not-a-date\n"})(),
    )
    assert ml.commit_date_iso("abc") is None


def test_deterministic_generated_at_uses_git_when_available(monkeypatch):
    monkeypatch.setattr(ml, "commit_date_iso", lambda _c: "2026-05-20T00:00:00Z")
    assert ml.deterministic_generated_at("abc") == "2026-05-20T00:00:00Z"


def test_deterministic_generated_at_falls_back_to_fixed_epoch(monkeypatch):
    monkeypatch.setattr(ml, "commit_date_iso", lambda _c: None)
    assert ml.deterministic_generated_at("abc") == "2026-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# load_signoffs
# ---------------------------------------------------------------------------


def test_load_signoffs_returns_empty_when_files_missing(monkeypatch, tmp_path: Path):
    _wire_repo(monkeypatch, tmp_path)
    out = ml.load_signoffs()
    assert out == {"peer": [], "legal": [], "sme": []}


def test_load_signoffs_skips_malformed_json(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "provenance" / "peer-review-signoffs.json").write_text(
        "{ broken", encoding="utf-8"
    )
    out = ml.load_signoffs()
    assert out["peer"] == []


def test_load_signoffs_returns_signoffs_list(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "provenance" / "peer-review-signoffs.json").write_text(
        json.dumps({"signoffs": [{"scope": ["1.1.1"], "pr": "#42"}]}),
        encoding="utf-8",
    )
    out = ml.load_signoffs()
    assert out["peer"] == [{"scope": ["1.1.1"], "pr": "#42"}]


def test_load_signoffs_skips_non_list_entries(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "provenance" / "sme-signoffs.json").write_text(
        json.dumps({"signoffs": "not-a-list"}), encoding="utf-8"
    )
    out = ml.load_signoffs()
    assert out["sme"] == []


# ---------------------------------------------------------------------------
# signoff_status_for
# ---------------------------------------------------------------------------


def _entry(**overrides) -> ml.LedgerInput:
    base = {
        "uc_id": "1.1.1",
        "uc_path": pathlib.Path("/tmp/x.json"),
        "regulation_id": "gdpr",
        "regulation_version": "2016/679",
        "clause": "Art.32",
        "mode": "satisfies",
        "assurance": "full",
        "derivation_source": None,
    }
    base.update(overrides)
    return ml.LedgerInput(**base)


def test_signoff_status_for_marks_peer_required_and_signed_when_scope_matches():
    out = ml.signoff_status_for(
        _entry(),
        signoffs={"peer": [{"scope": ["1.1.1"], "pr": "#42"}], "legal": [], "sme": []},
        baselines={},
    )
    assert out["peer"]["status"] == "signed"
    assert out["peer"]["latestSignoffPr"] == "#42"


def test_signoff_status_for_marks_peer_signed_with_direct_commit_when_no_pr():
    out = ml.signoff_status_for(
        _entry(),
        signoffs={"peer": [{"scope": ["1.1.1"]}], "legal": [], "sme": []},
        baselines={},
    )
    assert out["peer"]["latestSignoffPr"] == "direct-commit"


def test_signoff_status_for_marks_peer_pending_when_no_scope_match():
    out = ml.signoff_status_for(
        _entry(uc_id="9.9.9"),
        signoffs={"peer": [{"scope": ["1.1.1"], "pr": "#42"}], "legal": [], "sme": []},
        baselines={},
    )
    assert out["peer"]["status"] == "pending"


def test_signoff_status_for_legal_required_only_when_full_assurance():
    out = ml.signoff_status_for(
        _entry(assurance="partial"),
        signoffs={"peer": [], "legal": [], "sme": []},
        baselines={},
    )
    assert out["legal"] == {"required": False, "status": "not-required"}


def test_signoff_status_for_sme_required_when_detects_violation_mode():
    out = ml.signoff_status_for(
        _entry(mode="detects-violation-of", assurance="partial"),
        signoffs={"peer": [], "legal": [], "sme": []},
        baselines={},
    )
    assert out["sme"]["required"] is True
    assert out["sme"]["status"] == "pending"


def test_signoff_status_for_sme_required_when_full_assurance():
    out = ml.signoff_status_for(
        _entry(mode="satisfies", assurance="full"),
        signoffs={"peer": [], "legal": [], "sme": []},
        baselines={},
    )
    assert out["sme"]["required"] is True


# ---------------------------------------------------------------------------
# build_ledger_inputs (validation + filtering)
# ---------------------------------------------------------------------------


def test_build_ledger_inputs_filters_out_invalid_compliance(
    monkeypatch, tmp_path: Path
):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations_payload()), encoding="utf-8"
    )
    _write_uc(
        repo,
        "UC-1.1.1.json",
        {
            "id": "1.1.1",
            "compliance": [
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32",
                 "mode": "satisfies", "assurance": "full"},
                {"regulation": "", "version": "x", "clause": "x", "mode": "satisfies",
                 "assurance": "full"},  # skipped: blank regulation
                {"regulation": "GDPR", "version": "2016/679", "clause": "",
                 "mode": "satisfies", "assurance": "full"},  # skipped: blank clause
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art.5",
                 "mode": "unknown-mode", "assurance": "full"},  # skipped: bad mode
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art.5",
                 "mode": "satisfies", "assurance": "unsupported"},  # skipped: bad assurance
            ],
        },
    )
    _write_uc(repo, "UC-1.1.2.json", {"id": ""})  # skipped: empty id
    idx = ml.load_regulation_index()
    inputs = ml.build_ledger_inputs(idx)
    assert len(inputs) == 1
    assert inputs[0].clause == "Art.32"


def test_build_ledger_inputs_exits_on_unresolved_regulation(
    monkeypatch, tmp_path: Path, capsys
):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations_payload()), encoding="utf-8"
    )
    _write_uc(
        repo,
        "UC-1.1.1.json",
        _uc("1.1.1", regulation="MadeUpRegThatDoesNotExist"),
    )
    idx = ml.load_regulation_index()
    with pytest.raises(SystemExit) as exc:
        ml.build_ledger_inputs(idx)
    err = capsys.readouterr().err
    assert exc.value.code == 2
    assert "FATAL: unresolved regulation names" in err
    assert "1.1.1" in err


# ---------------------------------------------------------------------------
# build_ledger_entry
# ---------------------------------------------------------------------------


def test_build_ledger_entry_uses_cache_when_present():
    entry = _entry(uc_path=pathlib.Path("/tmp/uc.json"))
    ml._git_first_seen_cache[entry.uc_path] = "first01"
    ml._git_last_modified_cache[entry.uc_path] = "last001"
    record = ml.build_ledger_entry(
        entry,
        signoffs={"peer": [], "legal": [], "sme": []},
        baselines={},
        head_commit="head001",
    )
    assert record["firstSeenCommit"] == "first01"
    assert record["lastModifiedCommit"] == "last001"
    assert "canonicalHash" in record


def test_build_ledger_entry_falls_back_to_head_when_no_cache():
    entry = _entry(uc_path=pathlib.Path("/tmp/uncached.json"))
    record = ml.build_ledger_entry(
        entry,
        signoffs={"peer": [], "legal": [], "sme": []},
        baselines={},
        head_commit="head001",
    )
    assert record["firstSeenCommit"] == "head001"
    assert record["lastModifiedCommit"] == "head001"


# ---------------------------------------------------------------------------
# build_ledger (orchestration)
# ---------------------------------------------------------------------------


def _build_full_repo(monkeypatch, tmp_path: Path) -> Path:
    """Hydrate a repo with regulations, UCs, signoffs, and stubbed git."""
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations_payload()), encoding="utf-8"
    )
    _write_uc(repo, "UC-1.1.1.json", _uc("1.1.1"))
    _write_uc(
        repo,
        "UC-2.2.2.json",
        _uc(
            "2.2.2",
            regulation="PCI-DSS",
            version="4.0",
            clause="10.2.1",
            mode="detects-violation-of",
            assurance="partial",
        ),
    )

    monkeypatch.setattr(ml, "catalogue_head_commit", lambda: "abc1234")
    monkeypatch.setattr(ml, "commit_date_iso", lambda _c: "2026-05-20T00:00:00Z")
    # Disable git cache population — keep everything fast and offline.
    monkeypatch.setattr(ml, "_populate_git_caches_bulk", lambda _p: None)
    return repo


def test_build_ledger_produces_canonical_artefact(monkeypatch, tmp_path: Path):
    _build_full_repo(monkeypatch, tmp_path)
    ledger = ml.build_ledger()
    assert ledger["schemaVersion"] == ml.SCHEMA_VERSION
    assert ledger["catalogueCommit"] == "abc1234"
    assert ledger["entryCount"] == 2
    assert len(ledger["entries"]) == 2
    # Entries are sorted by mappingId.
    ids = [e["mappingId"] for e in ledger["entries"]]
    assert ids == sorted(ids)
    # Signature is unsigned by default.
    assert ledger["signature"]["state"] == "unsigned"


def test_build_ledger_includes_baselines_from_signoff_files(
    monkeypatch, tmp_path: Path
):
    repo = _build_full_repo(monkeypatch, tmp_path)
    (repo / "data" / "provenance" / "peer-review-signoffs.json").write_text(
        json.dumps({"baseline_commit": "baseabc", "signoffs": []}), encoding="utf-8"
    )
    (repo / "data" / "provenance" / "legal-review-signoffs.json").write_text(
        "{ malformed", encoding="utf-8"
    )
    ledger = ml.build_ledger()
    # The baseline shouldn't surface in the public artefact directly, but the
    # malformed-JSON path should not crash either.
    assert ledger["entryCount"] == 2


def test_build_ledger_aborts_on_mapping_id_collision_with_divergent_hash(
    monkeypatch, tmp_path: Path, capsys
):
    repo = _build_full_repo(monkeypatch, tmp_path)
    # Two sidecars with the same compliance tuple but different
    # derivationSource → identical mappingId, divergent canonicalHash.
    _write_uc(
        repo,
        "UC-1.1.1-dup.json",
        _uc(
            "1.1.1",
            derivation={
                "parentRegulation": "GDPR",
                "parentVersion": "2016/679",
                "parentClause": "Art.32",
                "inheritanceMode": "modify",
                "divergenceNote": "diverge",
            },
        ),
    )
    # Re-write the first sidecar to enforce dedup ordering.
    _write_uc(repo, "UC-1.1.1.json", _uc("1.1.1"))
    # Disable dedup-by-uid so both records make it into the list.
    monkeypatch.setattr(ml, "iter_uc_sidecars", lambda: sorted(
        [
            repo / "content" / "cat-01-foo" / "UC-1.1.1.json",
            repo / "content" / "cat-01-foo" / "UC-1.1.1-dup.json",
        ]
    ))
    with pytest.raises(SystemExit) as exc:
        ml.build_ledger()
    assert exc.value.code == 2
    assert "FATAL: mappingId collisions" in capsys.readouterr().err


def test_build_ledger_attaches_auxiliary_sources_when_present(
    monkeypatch, tmp_path: Path
):
    repo = _build_full_repo(monkeypatch, tmp_path)
    (repo / "data" / "splunkbase-catalog.json").write_text("{}", encoding="utf-8")
    ledger = ml.build_ledger()
    assert "auxiliarySources" in ledger
    assert ledger["auxiliarySources"][0]["path"] == "data/splunkbase-catalog.json"


def test_build_ledger_dedupes_identical_mapping_ids_silently(monkeypatch, tmp_path: Path):
    repo = _build_full_repo(monkeypatch, tmp_path)
    # Two UCs with the same id and identical compliance entry produce
    # the same canonicalHash → second occurrence is silently dropped.
    twin_path = _write_uc(repo, "UC-1.1.1-twin.json", _uc("1.1.1"))
    monkeypatch.setattr(
        ml,
        "iter_uc_sidecars",
        lambda: sorted(
            [
                repo / "content" / "cat-01-foo" / "UC-1.1.1.json",
                repo / "content" / "cat-01-foo" / "UC-2.2.2.json",
                twin_path,
            ]
        ),
    )
    ledger = ml.build_ledger()
    # Only the unique mappingIds survive → still 2 entries.
    assert ledger["entryCount"] == 2


# ---------------------------------------------------------------------------
# build_auxiliary_sources
# ---------------------------------------------------------------------------


def test_build_auxiliary_sources_skips_missing(monkeypatch, tmp_path: Path, capsys):
    _wire_repo(monkeypatch, tmp_path)
    out = ml.build_auxiliary_sources()
    err = capsys.readouterr().err
    assert out == []
    assert "auxiliary source missing" in err


def test_build_auxiliary_sources_includes_present_files(
    monkeypatch, tmp_path: Path
):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "splunkbase-catalog.json").write_text(
        "{}", encoding="utf-8"
    )
    out = ml.build_auxiliary_sources()
    assert len(out) == 1
    assert out[0]["path"] == "data/splunkbase-catalog.json"
    assert out[0]["bytes"] == 2
    assert len(out[0]["sha256"]) == 64


def test_build_auxiliary_sources_skips_unreadable(monkeypatch, tmp_path: Path, capsys):
    _wire_repo(monkeypatch, tmp_path)

    def fake_exists(self):
        return True

    def fake_read_bytes(self):
        raise PermissionError("denied")

    # Patch only on the absolute path comparison — easiest via the Path class.
    monkeypatch.setattr(pathlib.Path, "exists", fake_exists)
    monkeypatch.setattr(pathlib.Path, "read_bytes", fake_read_bytes)
    out = ml.build_auxiliary_sources()
    err = capsys.readouterr().err
    assert out == []
    assert "unreadable" in err


# ---------------------------------------------------------------------------
# render + _structural_diff + _preview_diff
# ---------------------------------------------------------------------------


def test_render_appends_trailing_newline():
    ledger = {"hello": "world"}
    out = ml.render(ledger)
    assert out.endswith("\n")
    assert out.startswith("{")


def test_structural_diff_strips_timestamp_fields():
    a = '{\n  "generatedAt": "2026-05-20T00:00:00Z",\n  "x": 1\n}\n'
    b = '{\n  "generatedAt": "2026-05-21T00:00:00Z",\n  "x": 1\n}\n'
    assert ml._structural_diff(a, b) is False


def test_structural_diff_detects_real_content_change():
    a = '{\n  "x": 1\n}\n'
    b = '{\n  "x": 2\n}\n'
    assert ml._structural_diff(a, b) is True


def test_structural_diff_strips_catalogue_commit_too():
    a = '{\n  "catalogueCommit": "abc1234",\n  "x": 1\n}\n'
    b = '{\n  "catalogueCommit": "def5678",\n  "x": 1\n}\n'
    assert ml._structural_diff(a, b) is False


def test_preview_diff_writes_to_stderr_when_diff_present(capsys):
    ml._preview_diff("a\n", "b\n")
    err = capsys.readouterr().err
    assert "diff preview" in err
    assert "-a" in err and "+b" in err


def test_preview_diff_is_silent_when_inputs_identical(capsys):
    ml._preview_diff("same\n", "same\n")
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _stub_build_ledger(monkeypatch, ledger: dict[str, Any]) -> None:
    monkeypatch.setattr(ml, "build_ledger", lambda: ledger)


def _example_ledger(merkle: str = "f" * 64) -> dict[str, Any]:
    return {
        "schemaVersion": "1.1.0",
        "generatedAt": "2026-05-20T00:00:00Z",
        "catalogueCommit": "abc1234",
        "entryCount": 1,
        "merkleRoot": merkle,
        "entries": [{"mappingId": "x", "canonicalHash": "abc"}],
        "signature": {"state": "unsigned"},
    }


def test_main_write_mode_writes_ledger_to_disk(monkeypatch, tmp_path: Path, capsys):
    _wire_repo(monkeypatch, tmp_path)
    _stub_build_ledger(monkeypatch, _example_ledger())
    rc = ml.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert ml.LEDGER_PATH.exists()
    assert "Wrote" in out


def test_main_check_returns_one_when_ledger_missing(
    monkeypatch, tmp_path: Path, capsys
):
    _wire_repo(monkeypatch, tmp_path)
    _stub_build_ledger(monkeypatch, _example_ledger())
    rc = ml.main(["--check"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "does not exist" in err


def test_main_check_returns_zero_when_ledger_matches(
    monkeypatch, tmp_path: Path, capsys
):
    _wire_repo(monkeypatch, tmp_path)
    ledger = _example_ledger()
    _stub_build_ledger(monkeypatch, ledger)
    # Write the rendered ledger first so a subsequent --check matches.
    ml.main([])
    capsys.readouterr()
    rc = ml.main(["--check"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "is up to date" in out


def test_main_check_returns_one_when_ledger_diverges(
    monkeypatch, tmp_path: Path, capsys
):
    _wire_repo(monkeypatch, tmp_path)
    ledger = _example_ledger()
    _stub_build_ledger(monkeypatch, ledger)
    # Write a stale version, then mutate the in-memory ledger so the
    # rerun differs structurally.
    ml.LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ml.LEDGER_PATH.write_text(ml.render(ledger), encoding="utf-8")
    _stub_build_ledger(monkeypatch, _example_ledger(merkle="0" * 64))
    rc = ml.main(["--check"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "is stale" in err
    assert "diff preview" in err
