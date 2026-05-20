"""Hermetic unit tests for ``splunk_uc.audits.cim_spl_alignment``.

P16 wave VV (2026-05-19). Walks the JSON SSOT and surfaces three classes
of drift between ``cimModels`` array declarations and ``cimSpl`` queries:
LOW non-canonical token (``Network Traffic`` instead of
``Network_Traffic``), MED ``cimSpl`` present with no ``datamodel=...``
reference, HIGH ``cimSpl`` references a datamodel not declared in
``cimModels``.

Tests pin every documented contract:

* Module-level invariants (``RE_DATAMODEL`` matches the documented
  shape including backtick-wrapped names, ``CANONICAL_DATAMODELS`` is
  the documented frozen 26-entry set, ``TOKEN_NORMALISATION`` is the
  6-entry alias table).
* ``Finding`` NamedTuple shape (6 fields, ``snippet`` defaulting to
  ``""``).
* ``_extract_datamodels_from_spl`` matrix (one match, multiple matches,
  dotted-sub-name strips at first ``.``, spaces normalised to
  underscores, case-insensitive prefix, backtick-wrapped name).
* ``_check_uc`` matrix (no ``cimModels`` → no findings; canonical token
  only → no findings; non-canonical token → LOW with normalisation
  advice; descriptive label like ``Network_Traffic.All_Traffic`` →
  canonical base extracted, no findings; ``cimSpl`` empty → no
  findings; ``cimSpl`` present but no ``datamodel=`` → MED; ``cimSpl``
  references undeclared canonical model → HIGH; ``cimSpl`` references
  unknown non-canonical name → not flagged (skipped via the
  ``in CANONICAL_DATAMODELS`` filter); non-string entries in
  ``cimModels`` silently skipped; empty/whitespace entries skipped).
* ``main()`` CLI matrix (clean run → 0; HIGH finding without
  ``--strict --check`` → 0; HIGH finding with ``--strict --check`` →
  1; ``argv=None`` falls through; ``--help`` lists ``--check`` and
  ``--strict``; output formatting; snippet truncation; finding sort
  order).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

import splunk_uc.audits._uc_walk as uc_walk
import splunk_uc.audits.cim_spl_alignment as csa


# ----------------------------------------------------------- module constants --
def test_re_datamodel_matches_quoted_unquoted_and_case_insensitive() -> None:
    """The compiled regex pins every documented capture shape.

    Note the character class ``[A-Za-z0-9_ ]`` is intentionally greedy:
    spaces, underscores, and digits are all valid name chars. The
    capture only stops at a non-class char (``.``, ``|``, ``\\n``, etc.)
    or end of string. ``_extract_datamodels_from_spl`` post-processes
    by stripping, splitting on ``.``, and replacing spaces with ``_``.
    """
    pat = csa.RE_DATAMODEL
    # base case
    assert (
        pat.search("| tstats count from datamodel=Network_Traffic").group("name")
        == "Network_Traffic"
    )
    # backtick-wrapped name (backtick is consumed by the optional prefix)
    assert pat.search("| from datamodel=`Authentication`").group("name") == "Authentication"
    # case-insensitive keyword
    assert pat.search("| from DATAMODEL=Endpoint").group("name") == "Endpoint"
    # tab around `=` keeps captured value clean
    assert pat.search("| from datamodel\t=\tEmail").group("name") == "Email"
    # numerical chars in name
    assert pat.search("| from datamodel=Foo123").group("name") == "Foo123"
    # leading non-alpha → no match
    assert pat.search("| from datamodel=_underscore_first") is None
    # dot terminates the capture
    assert (
        pat.search("| from datamodel=Network_Traffic.All_Traffic").group("name")
        == "Network_Traffic"
    )


def test_canonical_datamodels_has_expected_membership() -> None:
    expected = {
        "Alerts",
        "Application_State",
        "Authentication",
        "Certificates",
        "Change",
        "Compute_Inventory",
        "Databases",
        "DLP",
        "Email",
        "Endpoint",
        "Event_Signatures",
        "Interprocess_Messaging",
        "Intrusion_Detection",
        "Inventory",
        "JVM",
        "Malware",
        "Network_Resolution",
        "Network_Sessions",
        "Network_Traffic",
        "Performance",
        "Splunk_Audit",
        "Ticket_Management",
        "Updates",
        "Vulnerabilities",
        "Web",
        "Risk",
        "Service_KPI_Summary",
    }
    assert csa.CANONICAL_DATAMODELS == expected


def test_token_normalisation_is_six_entry_alias_table() -> None:
    assert csa.TOKEN_NORMALISATION == {
        "Network Traffic": "Network_Traffic",
        "Ticket Management": "Ticket_Management",
        "Intrusion Detection": "Intrusion_Detection",
        "Network Sessions": "Network_Sessions",
        "Network Resolution": "Network_Resolution",
        "Compute Inventory": "Compute_Inventory",
    }


def test_finding_namedtuple_shape() -> None:
    f = csa.Finding(
        severity="HIGH",
        kind="cim-spl-datamodel-mismatch",
        uc_id="UC-1.1.1",
        file="UC-1.1.1.json",
        message="something",
    )
    assert f.severity == "HIGH"
    assert f.kind == "cim-spl-datamodel-mismatch"
    assert f.uc_id == "UC-1.1.1"
    assert f.file == "UC-1.1.1.json"
    assert f.message == "something"
    assert f.snippet == ""  # default


# ---------------------------------------- _extract_datamodels_from_spl matrix --
def test_extract_datamodels_single() -> None:
    spl = "| tstats count from datamodel=Network_Traffic"
    assert csa._extract_datamodels_from_spl(spl) == {"Network_Traffic"}


def test_extract_datamodels_multiple() -> None:
    """Each ``datamodel=`` occurrence is captured; ``.`` terminates names."""
    spl = (
        "| tstats count from datamodel=Network_Traffic.All_Traffic"
        "\n| append [tstats count from datamodel=Authentication]"
    )
    assert csa._extract_datamodels_from_spl(spl) == {
        "Network_Traffic",
        "Authentication",
    }


def test_extract_datamodels_dotted_strips_after_first_dot() -> None:
    """``datamodel=Foo.Bar`` is treated as a reference to ``Foo``."""
    spl = "| tstats count from datamodel=Network_Traffic.All_Traffic"
    assert csa._extract_datamodels_from_spl(spl) == {"Network_Traffic"}


def test_extract_datamodels_spaces_normalised_to_underscore() -> None:
    """Captured names with spaces get normalised via str.replace.

    The regex's character class permits spaces, so a literal
    ``datamodel=Network Traffic.x`` is captured up to the ``.`` and
    then split-on-dot drops the suffix. The remaining name is
    space-normalised to ``Network_Traffic``.
    """
    spl = "| tstats count from datamodel=Network Traffic.x"
    assert csa._extract_datamodels_from_spl(spl) == {"Network_Traffic"}


def test_extract_datamodels_backtick_wrapped() -> None:
    spl = "| tstats count from datamodel=`Authentication`"
    assert csa._extract_datamodels_from_spl(spl) == {"Authentication"}


def test_extract_datamodels_empty_returns_empty_set() -> None:
    assert csa._extract_datamodels_from_spl("") == set()
    assert csa._extract_datamodels_from_spl("| stats count") == set()


# ---------------------------------------------------------------- fixtures ----
class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        *,
        cim_models: Any = ...,
        cim_spl: Any = ...,
    ) -> None: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Synthetic ``content/cat-<n>-<slug>/`` corpus with patched REPO/CONTENT."""
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(uc_walk, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Factory writing a synthetic UC sidecar under ``content/cat-1-test/``."""
    cat = fake_repo / "content" / "cat-1-test"
    cat.mkdir(exist_ok=True)

    def _factory(
        uc_id: str,
        *,
        cim_models: Any = ...,
        cim_spl: Any = ...,
    ) -> None:
        payload: dict[str, Any] = {"id": uc_id}
        if cim_models is not ...:
            payload["cimModels"] = cim_models
        if cim_spl is not ...:
            payload["cimSpl"] = cim_spl
        path = cat / f"UC-{uc_id}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

    return _factory


# -------------------------------------------------------------- _check_uc ----
def test_check_uc_no_cim_models_returns_empty() -> None:
    """Sidecar without ``cimModels`` → no findings."""
    assert csa._check_uc("UC-1.1.1", "uc.json", {}) == []


def test_check_uc_canonical_only_returns_empty() -> None:
    """``cimModels=['Authentication']`` and no SPL → no findings."""
    payload = {"cimModels": ["Authentication"]}
    assert csa._check_uc("UC-1.1.1", "uc.json", payload) == []


def test_check_uc_non_canonical_token_emits_low() -> None:
    """``Network Traffic`` (spaced) → LOW with normalisation advice."""
    payload = {"cimModels": ["Network Traffic"]}
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "LOW"
    assert f.kind == "cim-models-nonstandard-token"
    assert "'Network Traffic' -> 'Network_Traffic'" in f.message
    assert f.snippet == "Network Traffic"


def test_check_uc_descriptive_subdataset_label_extracts_canonical_base() -> None:
    """``Network_Traffic.All_Traffic`` → canonical base ``Network_Traffic``."""
    payload = {
        "cimModels": ["Network_Traffic.All_Traffic"],
        "cimSpl": "| tstats count from datamodel=Network_Traffic",
    }
    assert csa._check_uc("UC-1.1.1", "uc.json", payload) == []


def test_check_uc_unrecognised_token_silently_dropped() -> None:
    """Unknown label that's not a canonical or alias and has no dotted base."""
    payload = {"cimModels": ["Some Random Label"]}
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []  # ignored


def test_check_uc_unrecognised_token_with_unknown_dotted_base() -> None:
    """``Foo.Bar`` where ``Foo`` is not canonical → no findings."""
    payload = {"cimModels": ["Foo.Bar"]}
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []


def test_check_uc_non_string_entries_silently_skipped() -> None:
    payload = {
        "cimModels": [123, None, {"x": 1}, "Authentication"],
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []  # canonical entry matched, non-strings dropped


def test_check_uc_empty_or_whitespace_entries_silently_skipped() -> None:
    payload = {"cimModels": ["", "   ", "Endpoint"]}
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []


def test_check_uc_cim_spl_empty_returns_no_findings() -> None:
    """``cimSpl`` whitespace-only short-circuits before MED check."""
    payload = {"cimModels": ["Authentication"], "cimSpl": "   "}
    assert csa._check_uc("UC-1.1.1", "uc.json", payload) == []


def test_check_uc_cim_spl_no_datamodel_emits_med() -> None:
    """``cimSpl`` present with no ``datamodel=`` → MED."""
    payload = {
        "cimModels": ["Authentication"],
        "cimSpl": "index=main sourcetype=auth | stats count",
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "MED"
    assert f.kind == "cim-spl-datamodel-missing"
    assert "no `datamodel=...`" in f.message
    assert f.snippet == "Authentication"


def test_check_uc_cim_spl_undeclared_canonical_model_emits_high() -> None:
    """``cimSpl`` references undeclared canonical model → HIGH."""
    payload = {
        "cimModels": ["Authentication"],
        "cimSpl": "| tstats count from datamodel=Network_Traffic",
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "HIGH"
    assert f.kind == "cim-spl-datamodel-mismatch"
    assert "Network_Traffic" in f.message
    assert "'Authentication'" in f.message
    assert f.snippet == "Network_Traffic"


def test_check_uc_cim_spl_unknown_model_not_flagged() -> None:
    """``cimSpl`` references a non-canonical model → not flagged."""
    payload = {
        "cimModels": ["Authentication"],
        "cimSpl": "| tstats count from datamodel=Some_Custom_Model",
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []  # mismatch filter requires canonical


def test_check_uc_cim_spl_matching_model_no_findings() -> None:
    """``cimSpl`` references the declared canonical model → no findings."""
    payload = {
        "cimModels": ["Network_Traffic"],
        "cimSpl": "| tstats count from datamodel=Network_Traffic.All_Traffic",
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    assert findings == []


def test_check_uc_low_and_high_can_co_occur() -> None:
    """Non-canonical token + mismatched SPL → LOW and HIGH together."""
    payload = {
        "cimModels": ["Network Traffic"],  # LOW: normalisation
        "cimSpl": "| tstats count from datamodel=Authentication",  # HIGH: undeclared
    }
    findings = csa._check_uc("UC-1.1.1", "uc.json", payload)
    severities = {f.severity for f in findings}
    assert severities == {"LOW", "HIGH"}


# ----------------------------------------------------------------- main() ----
def test_main_clean_exit_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean UC corpus → exit 0 with the header banner."""
    make_uc("1.1.1", cim_models=["Authentication"])
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    assert "CIM <-> SPL alignment audit" in out
    assert "Sidecars scanned: 1" in out
    assert "Findings by severity:" in out


def test_main_empty_corpus_exit_zero(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty content tree → exit 0 with ``Sidecars scanned: 0``."""
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    assert "Sidecars scanned: 0" in out


def test_main_high_finding_without_strict_check_exits_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """HIGH finding without --strict --check still exits 0."""
    make_uc(
        "1.1.1",
        cim_models=["Authentication"],
        cim_spl="| tstats count from datamodel=Network_Traffic",
    )
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    assert "[HIGH]" in out
    assert "cim-spl-datamodel-mismatch" in out
    assert "snippet: Network_Traffic" in out


def test_main_high_finding_with_strict_check_exits_one(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """HIGH finding with --strict --check → exit 1."""
    make_uc(
        "1.1.1",
        cim_models=["Authentication"],
        cim_spl="| tstats count from datamodel=Network_Traffic",
    )
    assert csa.main(["--strict", "--check"]) == 1


def test_main_high_finding_with_check_only_still_exits_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--check WITHOUT --strict still exits 0 (the documented backlog mode)."""
    make_uc(
        "1.1.1",
        cim_models=["Authentication"],
        cim_spl="| tstats count from datamodel=Network_Traffic",
    )
    assert csa.main(["--check"]) == 0


def test_main_high_finding_with_strict_only_still_exits_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """--strict WITHOUT --check still exits 0 (both flags required)."""
    make_uc(
        "1.1.1",
        cim_models=["Authentication"],
        cim_spl="| tstats count from datamodel=Network_Traffic",
    )
    assert csa.main(["--strict"]) == 0


def test_main_med_finding_does_not_change_exit_code(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """MED finding alone never blocks even with --strict --check."""
    make_uc(
        "1.1.1",
        cim_models=["Authentication"],
        cim_spl="index=main sourcetype=auth | stats count",
    )
    assert csa.main(["--strict", "--check"]) == 0
    out = capsys.readouterr().out
    assert "[MED]" in out


def test_main_argv_none_falls_through(
    fake_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(csa.sys, "argv", ["audit"])
    assert csa.main() == 0


def test_main_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        csa.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--check" in out
    assert "--strict" in out


def test_main_findings_sorted_high_med_low(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When multiple severities are present, FINDINGS block sorts HIGH first."""
    make_uc(
        "1.1.1",
        cim_models=["Network Traffic"],  # LOW
        cim_spl="| tstats count from datamodel=Authentication",  # HIGH (undeclared)
    )
    make_uc(
        "1.1.2",
        cim_models=["Authentication"],
        cim_spl="index=main | stats count",  # MED
    )
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    # Verify HIGH appears before MED appears before LOW in the FINDINGS block.
    high_pos = out.find("[HIGH]")
    med_pos = out.find("[MED]")
    low_pos = out.find("[LOW]")
    assert 0 < high_pos < med_pos < low_pos


def test_main_long_snippet_truncated_at_200(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``snippet`` truncated at 200 characters in output."""
    # Construct a snippet by listing many used models.
    spl = " | ".join(f"tstats count from datamodel={m}" for m in csa.CANONICAL_DATAMODELS)
    make_uc("1.1.1", cim_models=["Authentication"], cim_spl=spl)
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    # Find snippet line(s) and verify truncation
    for line in out.splitlines():
        if line.startswith("        snippet:"):
            snippet = line[len("        snippet: ") :]
            assert len(snippet) <= 200


def test_main_finding_with_empty_snippet_omits_snippet_line(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``Finding.snippet == ''`` short-circuits the ``if f.snippet`` guard."""
    # Construct a synthetic finding with empty snippet by patching _check_uc.
    captured: dict[str, str] = {"out": ""}

    def fake_check_uc(uc_id: str, file: str, payload: dict[str, Any]) -> list[csa.Finding]:
        return [
            csa.Finding(
                severity="HIGH",
                kind="cim-spl-datamodel-mismatch",
                uc_id=uc_id,
                file=file,
                message="no snippet",
                snippet="",
            )
        ]

    make_uc("1.1.1", cim_models=["Authentication"])
    import unittest.mock as mock

    with mock.patch.object(csa, "_check_uc", side_effect=fake_check_uc):
        assert csa.main([]) == 0
    out = capsys.readouterr().out
    captured["out"] = out
    # The HIGH finding is in output, but no `snippet:` line.
    assert "[HIGH]" in out
    assert "        snippet:" not in out


def test_main_missing_id_renders_as_unknown(
    fake_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """UC without ``id`` renders as ``UC-<unknown>`` in the FINDINGS block."""
    cat = fake_repo / "content" / "cat-1-test"
    cat.mkdir(exist_ok=True)
    # No "id" key; cimSpl mismatches → HIGH
    (cat / "UC-noid.json").write_text(
        json.dumps(
            {
                "cimModels": ["Authentication"],
                "cimSpl": "| tstats count from datamodel=Network_Traffic",
            }
        ),
        encoding="utf-8",
    )
    assert csa.main([]) == 0
    out = capsys.readouterr().out
    assert "UC-<unknown>" in out


# ----------------------------------------- dispatcher entry-point smoke -----
def test_module_dunder_main_exists() -> None:
    src = pathlib.Path(csa.__file__).read_text()
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
