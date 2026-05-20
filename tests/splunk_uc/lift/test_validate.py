"""Tests for the ``lift-validate`` verb.

The verb is the §5 firewall: it must reject any diff that touches a
firewalled field, that fails to lift the score strictly, or whose
identity does not match the on-disk sidecar. On a clean diff it writes
the lifted content back to the sidecar. (``--skip-md-regen`` is
accepted for backward compatibility but is a no-op since F21 close
on 2026-05-18 — the per-UC ``.md`` companion was deleted and the LLM
markdown twin now lives only in ``dist/uc/UC-X.Y.Z/uc.md``.)
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import validate  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"
BRONZE = FIXTURE_DIR / "UC-15-bronze-baseline.json"
SILVER = FIXTURE_DIR / "UC-15-silver-target.json"


def _stage_uc(tmp_path: Path, fixture: Path = BRONZE) -> tuple[Path, Path]:
    """Copy the named fixture into a temp content tree."""
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    shutil.copy(fixture, sidecar)
    return tmp_path / "content", sidecar


def _write_diff(
    tmp_path: Path,
    uc_id: str,
    lifted: dict[str, object],
    *,
    target_tier: str = "silver",
    diff_uc_id: str | None = None,
) -> Path:
    diff_path = tmp_path / f"lift-{uc_id}.diff.json"
    payload = {
        "uc_id": diff_uc_id if diff_uc_id is not None else uc_id.removeprefix("UC-"),
        "target_tier": target_tier,
        "lifted_fields": lifted,
    }
    diff_path.write_text(json.dumps(payload))
    return diff_path


def _silver_lifted_fields() -> dict[str, object]:
    """Subset of the Silver fixture that, when applied to Bronze, lifts the score."""
    silver = json.loads(SILVER.read_text())
    return {
        "description": silver["description"],
        "value": silver["value"],
        "dataSources": silver["dataSources"],
        "detailedImplementation": silver["detailedImplementation"],
        "knownFalsePositives": silver["knownFalsePositives"],
        "references": silver["references"],
    }


def test_validate_accepts_proper_silver_lift(tmp_path: Path) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    after = json.loads(sidecar.read_text())
    silver = json.loads(SILVER.read_text())
    assert after["description"] == silver["description"]
    assert after["detailedImplementation"] == silver["detailedImplementation"]
    baseline = json.loads(BRONZE.read_text())
    assert after["spl"] == baseline["spl"]
    assert after["id"] == baseline["id"]


def test_validate_rejects_diff_that_touches_firewalled_field(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"spl": "search index=evil"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "firewall" in captured.err.lower()
    assert "spl" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_grandma_explanation(tmp_path: Path, capsys) -> None:
    """grandmaExplanation is firewalled — a dedicated generator owns it."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        {"grandmaExplanation": "We help keep computer rooms healthy."},
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "grandmaExplanation" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_field_outside_lift_surface(tmp_path: Path, capsys) -> None:
    """A field name that's not in LIFT_SURFACE_FIELDS is rejected."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"pancakes": "delicious"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "pancakes" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_when_post_score_not_strictly_greater(tmp_path: Path, capsys) -> None:
    """Applying an unchanged value must NOT raise the score."""
    content_root, sidecar = _stage_uc(tmp_path)
    baseline = json.loads(BRONZE.read_text())
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        {"description": baseline["description"]},
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "score" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == baseline


def test_validate_rejects_uc_id_mismatch(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        _silver_lifted_fields(),
        diff_uc_id="15.99.99",
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "uc_id" in captured.err.lower() or "id" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_target_tier_mismatch(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        _silver_lifted_fields(),
        target_tier="gold",
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--target-tier",
            "silver",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "tier" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_malformed_diff(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = tmp_path / "broken.diff.json"
    diff_path.write_text(json.dumps({"not_a_diff": True}))
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "diff" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_dry_run_does_not_write_sidecar(tmp_path: Path) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--dry-run",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_unknown_uc_returns_1(tmp_path: Path, capsys) -> None:
    (tmp_path / "content").mkdir()
    diff_path = _write_diff(tmp_path, "UC-99.99.99", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-99.99.99",
            "--diff",
            str(diff_path),
            "--content-root",
            str(tmp_path / "content"),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "lift-validate:" in captured.err
    assert "UC-99.99.99" in captured.err


def test_validate_emits_json_summary_on_success(tmp_path: Path, capsys) -> None:
    """The happy-path stdout payload is parseable JSON with before/after scores."""
    content_root, _sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
            "--json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["uc_id"] == "UC-15.1.1"
    assert payload["score_before"] == 20
    assert payload["score_after"] > 20
    assert payload["wrote"].endswith("UC-15.1.1.json")


def test_validate_rejects_diff_with_value_of_wrong_type(tmp_path: Path, capsys) -> None:
    """references is array-typed; a string value must be rejected."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"references": "https://example.com"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "references" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_does_not_emit_in_tree_md_companion(tmp_path: Path) -> None:
    """Lift-validate never writes ``content/.../UC-X.Y.Z.md`` (post-F21).

    Before F21 close (2026-05-18) the validator invoked
    ``generate-md-from-json --files <sidecar>`` after a successful
    lift to keep the per-UC ``.md`` companion in lock-step with the
    sidecar. The companions have been deleted from the tree and the
    LLM-friendly markdown twin now lives only in
    ``dist/uc/UC-X.Y.Z/uc.md`` (emitted at build time by
    ``tools/build/templates/uc.py::render_markdown_twin``).

    This test pins the new invariant: even when the caller omits
    ``--skip-md-regen``, the validator must not write a sibling
    ``.md`` next to the JSON sidecar.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    md_path = sidecar.with_suffix(".md")
    assert not md_path.exists()
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
        ]
    )
    assert exit_code == 0
    assert not md_path.exists(), (
        ".md companion must not be regenerated post-F21 close"
    )


def test_validate_emits_canonical_utf8_when_writing(tmp_path: Path) -> None:
    """Written sidecar must use raw UTF-8, not ``\\u2014`` escape sequences.

    The catalog convention is raw UTF-8 (>97 % of UCs); a regression
    here would create a churn-storm of meaningless escape changes the
    next time anyone runs the lift loop.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    raw = sidecar.read_text(encoding="utf-8")
    assert "\u2014" in raw
    assert "\\u2014" not in raw


# ---------------------------------------------------------------------------
# MITRE ATT&CK ID hardening (PR-4 follow-up #1)
#
# The schema regex in ``schemas/uc.schema.json`` permits ``TA<digits>``
# (tactic IDs) as well as ``T<digits>`` (technique IDs), but the
# downstream gate ``scripts/simulate_controltest.py`` is stricter — it
# rejects tactic IDs as hard failures. ``lift-validate`` must catch
# this at validate time so the orchestrator never produces a UC that
# is rejected by a CI gate it doesn't run locally.
# ---------------------------------------------------------------------------


def test_validate_rejects_mitre_tactic_id_in_lift(tmp_path: Path, capsys) -> None:
    """``TA<digits>`` (tactic ID) in ``mitreAttack`` is rejected.

    Reproduces the UC-15.3.1 incident where a subagent emitted
    ``TA0006`` and the failure surfaced only at the post-push
    ``simulate_controltest.py`` gate.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    lifted = _silver_lifted_fields()
    lifted["mitreAttack"] = ["T1078", "TA0006"]  # tactic id smuggled in
    diff_path = _write_diff(tmp_path, "UC-15.1.1", lifted)
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "mitreAttack" in captured.err
    assert "TA0006" in captured.err
    # Sidecar must be byte-identical to the pre-lift baseline on refusal.
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_accepts_valid_mitre_technique_ids(tmp_path: Path) -> None:
    """Bare technique IDs (``T<digits>``), sub-techniques (``T<digits>.<digits>``),
    and the ``N/A (<reason>)`` escape hatch must all be accepted."""
    content_root, _sidecar = _stage_uc(tmp_path)
    lifted = _silver_lifted_fields()
    lifted["mitreAttack"] = ["T1078", "T1078.001", "N/A (operational telemetry)"]
    diff_path = _write_diff(tmp_path, "UC-15.1.1", lifted)
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0


def test_validate_rejects_garbage_mitre_id(tmp_path: Path, capsys) -> None:
    """A free-form string that does not match T#### / T####.### / N/A (...)
    is rejected with the same code path used for tactic IDs."""
    content_root, _sidecar = _stage_uc(tmp_path)
    lifted = _silver_lifted_fields()
    lifted["mitreAttack"] = ["lateral movement"]  # not an ID at all
    diff_path = _write_diff(tmp_path, "UC-15.1.1", lifted)
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "mitreAttack" in captured.err
    assert "lateral movement" in captured.err


# ---------------------------------------------------------------------------
# Canonical sidecar key ordering (PR-4 follow-up #2)
#
# After a lift-validate write, the on-disk sidecar must already be in
# the canonical key order used by the rest of the generator chain so
# the post-lift ``make sync-generated`` cascade reorders zero keys.
# ---------------------------------------------------------------------------


def test_validate_writes_sidecar_in_canonical_key_order(tmp_path: Path) -> None:
    """A newly lifted sidecar's keys must follow ``SIDECAR_FIELD_ORDER``.

    The bronze fixture happens to be in canonical order already. The
    diff adds ``knownFalsePositives`` and ``references`` — which were
    already in the fixture — and a new ``detailedImplementation``
    (lift-surface field). ``detailedImplementation`` is not in the
    canonical order tuple, so it must be preserved at the end.
    """
    from splunk_uc._uc_sidecar import SIDECAR_FIELD_ORDER

    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    keys = list(json.loads(sidecar.read_text()).keys())
    # Filter the canonical order down to keys actually present, then
    # the on-disk key order must start with that filtered sequence.
    expected_prefix = [k for k in SIDECAR_FIELD_ORDER if k in keys]
    assert keys[: len(expected_prefix)] == expected_prefix, (
        f"on-disk key order diverges from canonical:\n"
        f"  got prefix: {keys[: len(expected_prefix)]}\n"
        f"  expected:   {expected_prefix}"
    )


def test_validate_canonical_order_appends_unknown_keys_at_end(tmp_path: Path) -> None:
    """Lift-surface fields outside ``SIDECAR_FIELD_ORDER`` (e.g.
    ``detailedImplementation``) land after all canonical keys, in the
    order the diff introduced them."""
    from splunk_uc._uc_sidecar import SIDECAR_FIELD_ORDER

    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    keys = list(json.loads(sidecar.read_text()).keys())
    canonical_keys = [k for k in keys if k in SIDECAR_FIELD_ORDER]
    extra_keys = [k for k in keys if k not in SIDECAR_FIELD_ORDER]
    # Every canonical key must come before every non-canonical key.
    if extra_keys:
        last_canonical = max(keys.index(k) for k in canonical_keys)
        first_extra = min(keys.index(k) for k in extra_keys)
        assert last_canonical < first_extra, (
            f"non-canonical keys appear before canonical ones:\n"
            f"  canonical positions: {[keys.index(k) for k in canonical_keys]}\n"
            f"  extra positions:    {[keys.index(k) for k in extra_keys]}"
        )


# ---------------------------------------------------------------------------
# Direct-helper coverage for the §5 firewall branches that the existing
# CLI-driven tests don't naturally reach.
# ---------------------------------------------------------------------------


def test_load_diff_raises_when_path_unreadable(tmp_path: Path) -> None:
    """Pin lines 143-144: OSError on ``diff_path.read_text``."""
    import pytest

    missing = tmp_path / "nope" / "missing.json"
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._load_diff(missing)
    assert "cannot read diff file" in str(excinfo.value)


def test_load_diff_raises_when_json_invalid(tmp_path: Path) -> None:
    """Pin lines 147-148: JSONDecodeError on ``json.loads``."""
    import pytest

    bad = tmp_path / "broken.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._load_diff(bad)
    assert "not valid JSON" in str(excinfo.value)


def test_load_diff_raises_when_payload_is_not_dict(tmp_path: Path) -> None:
    """Pin line 150: top-level payload not a JSON object."""
    import pytest

    p = tmp_path / "list.json"
    p.write_text(json.dumps(["a", "b"]), encoding="utf-8")
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._load_diff(p)
    assert "must be a JSON object" in str(excinfo.value)


def test_load_diff_raises_when_lifted_fields_is_not_dict(tmp_path: Path) -> None:
    """Pin line 155: ``lifted_fields`` not an object."""
    import pytest

    p = tmp_path / "wrong-shape.json"
    p.write_text(
        json.dumps(
            {"uc_id": "15.1.1", "target_tier": "silver", "lifted_fields": ["not", "a", "dict"]}
        ),
        encoding="utf-8",
    )
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._load_diff(p)
    assert "lifted_fields must be an object" in str(excinfo.value)


def test_validate_lifted_types_raises_when_schema_drifts() -> None:
    """Pin line 211: no schema fragment for a field on the lift surface.

    Constructed by passing a schema with empty ``properties`` so every
    lookup returns ``None`` and the drift guard fires.
    """
    import pytest

    diff = {"lifted_fields": {"description": "anything"}}
    schema_with_no_properties: dict[str, object] = {"properties": {}}
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._validate_lifted_types(diff, schema_with_no_properties)
    assert "no schema fragment for lifted field" in str(excinfo.value)


def test_check_lifted_mitre_techniques_returns_early_when_value_not_list() -> None:
    """Pin line 239: defensive guard against non-list ``mitreAttack``.

    The per-field schema validation is what actually catches the bad
    type at the CLI level. Calling the helper directly with a non-list
    value exercises the defensive return that prevents the regex loop
    from crashing if the validation ordering ever changes.
    """
    # No raise → returned early.
    validate._check_lifted_mitre_techniques(
        {"lifted_fields": {"mitreAttack": "not-a-list"}}
    )


def test_check_identity_preserved_raises_when_id_changes() -> None:
    """Pin line 276: identity field flipped by the diff."""
    import pytest

    original = {"id": "15.1.1", "title": "Original"}
    lifted = {"id": "15.1.1", "title": "Lifted"}
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._check_identity_preserved(original, lifted)
    assert "identity field 'title' changed" in str(excinfo.value)


def test_run_strict_audits_raises_when_subprocess_returns_nonzero(
    monkeypatch,
) -> None:
    """Pin lines 289-299: strict audit chain surfaces a non-zero rc.

    Monkeypatches ``subprocess.run`` so the test stays hermetic — we
    don't actually want to fork & re-enter the dispatcher.
    """
    import subprocess as _subproc

    import pytest

    class _FakeResult:
        def __init__(self, rc: int) -> None:
            self.returncode = rc
            self.stdout = "stdout-content"
            self.stderr = "stderr-content"

    captured: list[list[str]] = []

    def _fake_run(cmd: list[str], **kwargs: object) -> _FakeResult:
        captured.append(cmd)
        # First verb passes; second fails. Pin the rc-handling branch
        # and that we actually iterate STRICT_AUDIT_VERBS in order.
        return _FakeResult(0 if len(captured) == 1 else 2)

    monkeypatch.setattr(validate, "subprocess", _subproc)
    monkeypatch.setattr(validate.subprocess, "run", _fake_run)
    with pytest.raises(validate._ValidationError) as excinfo:
        validate._run_strict_audits()
    msg = str(excinfo.value)
    assert "strict audit" in msg
    assert "exit 2" in msg
    assert "stdout-content" in msg
    assert "stderr-content" in msg


def test_run_strict_audits_passes_clean_when_every_verb_returns_zero(
    monkeypatch,
) -> None:
    """Companion of the failure test: every verb returns 0 → no raise."""
    import subprocess as _subproc

    class _FakeResult:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(validate, "subprocess", _subproc)
    monkeypatch.setattr(validate.subprocess, "run", lambda *a, **kw: _FakeResult())
    # No raise.
    validate._run_strict_audits()


def test_validate_strict_mode_reverts_when_audit_chain_fails(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    """Pin lines 421-426: ``--strict`` failure reverts the sidecar bytes.

    Hermetic by monkeypatching ``_run_strict_audits`` so we never fork.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    original_bytes = sidecar.read_bytes()

    def _boom() -> None:
        raise validate._ValidationError("simulated strict-audit failure")

    monkeypatch.setattr(validate, "_run_strict_audits", _boom)

    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--strict",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "simulated strict-audit failure" in err
    # Bytes must be reverted to the pre-lift content.
    assert sidecar.read_bytes() == original_bytes


def test_validate_reverts_when_regen_markdown_raises(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    """Pin lines 432-438: ``_regen_markdown`` failure reverts sidecar bytes.

    The shipped ``_regen_markdown`` is a no-op stub, so we monkeypatch
    it to raise so the rollback branch is exercised. Drops the
    ``--skip-md-regen`` flag so the regen path is entered.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    original_bytes = sidecar.read_bytes()

    def _boom(_path: Path) -> None:
        raise validate._ValidationError("simulated markdown-regen failure")

    monkeypatch.setattr(validate, "_regen_markdown", _boom)

    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "simulated markdown-regen failure" in err
    assert sidecar.read_bytes() == original_bytes


def test_validate_reraises_unexpected_exception_and_reverts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Pin the ``except Exception: ... raise`` block (lines 436-438).

    Forces an unexpected exception by monkeypatching ``score_uc`` so
    the second call raises a ``RuntimeError``. The validator must
    write the original bytes back and propagate the exception.
    """
    import pytest

    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    original_bytes = sidecar.read_bytes()

    # Stash a reference to the genuine implementation, then replace it
    # with a wrapper that returns the first time (so the pre-lift score
    # is computed normally) and raises on the second call.
    real_score = validate.score_uc
    call_count = {"n": 0}

    def _wrapped(*a: object, **kw: object) -> object:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return real_score(*a, **kw)
        raise RuntimeError("synthetic post-lift score error")

    monkeypatch.setattr(validate, "score_uc", _wrapped)

    with pytest.raises(RuntimeError, match="synthetic post-lift score error"):
        validate.main(
            [
                "UC-15.1.1",
                "--diff",
                str(diff_path),
                "--content-root",
                str(content_root),
                "--skip-md-regen",
            ]
        )
    # Even though the exception propagates, the rollback in the
    # ``except Exception`` block must have restored the sidecar.
    assert sidecar.read_bytes() == original_bytes
