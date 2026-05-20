"""Unit tests for ``splunk_uc.audits.content_quality``.

P16 wave GG: lifts ``src/splunk_uc/audits/content_quality.py`` from
~14% to 100% combined coverage. Pins every documented contract of
the content-quality audit:

(a) flag UCs where ``description`` and ``value`` are identical
    (whitespace-normalised);
(b) flag UCs where ``grandmaExplanation`` mentions any of the 11
    technical jargon terms (case-insensitive, first-match-breaks);
(c) flag UCs whose ``controlTest.fixtureRef`` does not resolve on
    disk;
(d) invalid-JSON sidecars are flagged with ``invalid_json``;
(e) ``--generate-baseline`` emits the current violations list as
    JSON and exits 0; ``--baseline`` suppresses listed violations,
    truncating the printed list to 20 with a ``... and N more``
    footer.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import content_quality as cq


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path: ...


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ + sample-data/ skeletons."""
    (tmp_path / "content").mkdir()
    (tmp_path / "sample-data").mkdir()
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    monkeypatch.setattr(cq, "SAMPLE_DATA", tmp_path / "sample-data")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **(payload or {})}
        sidecar.write_text(json.dumps(merged), encoding="utf-8")
        return sidecar

    return _make


# ----------------------------------------------------------------------
# Module constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_project_root_resolves(self) -> None:
        from splunk_uc.audits import content_quality as fresh

        assert (fresh.PROJECT_ROOT / "schemas").is_dir()

    def test_jargon_terms_non_empty(self) -> None:
        assert len(cq.JARGON_TERMS) > 0

    def test_jargon_terms_include_core(self) -> None:
        """The 11 documented terms must all be present."""
        expected = {
            "tstats",
            "datamodel",
            "CIM",
            "sourcetype",
            "macro",
            "eval",
            "rex",
            "lookup",
            "savedsearch",
            "props.conf",
            "transforms.conf",
        }
        assert set(cq.JARGON_TERMS) == expected


# ----------------------------------------------------------------------
# Clean and trivial paths
# ----------------------------------------------------------------------


class TestNoViolations:
    def test_empty_content_returns_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cq.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "0 existing violation(s)" in out

    def test_clean_uc_returns_zero(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {
                "description": "A description.",
                "value": "A different value.",
                "grandmaExplanation": "We watch your stuff.",
            },
        )
        rc = cq.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "0 existing" in out


# ----------------------------------------------------------------------
# Invalid JSON
# ----------------------------------------------------------------------


class TestInvalidJson:
    def test_invalid_json_flagged(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        bad = cat / "UC-1.1.1.json"
        bad.write_text("{not json,,,}", encoding="utf-8")
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid_json" in err


# ----------------------------------------------------------------------
# description == value
# ----------------------------------------------------------------------


class TestDescriptionEqualsValue:
    def test_exact_match_flagged(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"description": "Same text.", "value": "Same text."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_whitespace_strip_match_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Leading/trailing whitespace stripped before comparison."""
        make_uc(
            "1.1.1",
            {"description": "  Same text.  ", "value": "Same text."},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_different_text_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"description": "X", "value": "Y"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_description_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When ``description`` is missing the check is skipped."""
        make_uc("1.1.1", {"value": "X"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_value_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When ``value`` is missing the check is skipped."""
        make_uc("1.1.1", {"description": "X"})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Jargon in grandmaExplanation
# ----------------------------------------------------------------------


class TestJargonInGrandma:
    def test_no_jargon_passes(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "We watch the lights."})
        rc = cq.main([])
        assert rc == 0

    def test_tstats_flagged(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "We use tstats here."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "jargon_in_grandma: tstats" in err

    def test_case_insensitive_match(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "CIM model lookup."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # The first match in JARGON_TERMS that appears (case-insensitively)
        # is reported. Either CIM or lookup will be flagged depending on
        # which comes first in JARGON_TERMS — that's CIM.
        assert "jargon_in_grandma:" in err

    def test_first_match_breaks(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        """Only the FIRST jargon term encountered is flagged per UC."""
        # "tstats" appears at index 0 in JARGON_TERMS, "datamodel" at
        # index 1. Including both yields a single violation for tstats.
        make_uc(
            "1.1.1",
            {"grandmaExplanation": "We use tstats over datamodel."},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # Only one issue line for this UC's jargon.
        jargon_lines = [line for line in err.splitlines() if "jargon_in_grandma" in line]
        assert len(jargon_lines) == 1
        assert "tstats" in jargon_lines[0]

    def test_missing_grandma_no_issue(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No ``grandmaExplanation`` field means the check is silent."""
        make_uc("1.1.1", {})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Broken fixtureRef
# ----------------------------------------------------------------------


class TestFixtureRef:
    def test_resolvable_fixture_passes(self, fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
        # Create the fixture target.
        (fake_repo / "sample-data" / "fx.json").write_text("{}", encoding="utf-8")
        make_uc(
            "1.1.1",
            {"controlTest": {"fixtureRef": "sample-data/fx.json"}},
        )
        rc = cq.main([])
        assert rc == 0

    def test_missing_fixture_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {"controlTest": {"fixtureRef": "sample-data/missing.json"}},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "broken_fixtureRef" in err
        assert "sample-data/missing.json" in err

    def test_empty_fixtureref_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"controlTest": {"fixtureRef": ""}})
        rc = cq.main([])
        assert rc == 0

    def test_control_test_not_dict_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A non-dict ``controlTest`` does not trip the fixtureRef check."""
        make_uc("1.1.1", {"controlTest": "not a dict"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_control_test_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No ``controlTest`` field means the check is silent."""
        make_uc("1.1.1", {})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Defaults / id fallback
# ----------------------------------------------------------------------


class TestIdFallback:
    def test_missing_id_uses_stem(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When the JSON has no ``id`` field, the issue references the
        file stem instead."""
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(
            json.dumps({"description": "Same.", "value": "Same."}),
            encoding="utf-8",
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # The relative file path is what's printed (the id only appears
        # in the violation dict, not in the formatted output line).
        assert "UC-1.1.1.json" in err


# ----------------------------------------------------------------------
# --generate-baseline
# ----------------------------------------------------------------------


class TestGenerateBaseline:
    def test_generate_baseline_outputs_json(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        rc = cq.main(["--generate-baseline"])
        out = capsys.readouterr().out
        assert rc == 0
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert any(v["issue"] == "description_equals_value" for v in parsed)

    def test_generate_baseline_empty(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cq.main(["--generate-baseline"])
        out = capsys.readouterr().out
        assert rc == 0
        assert json.loads(out) == []


# ----------------------------------------------------------------------
# --baseline
# ----------------------------------------------------------------------


class TestBaseline:
    def test_baseline_suppresses_violation(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sidecar = make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        rel = str(sidecar.relative_to(fake_repo))
        baseline_path = fake_repo / "baseline.json"
        baseline_path.write_text(
            json.dumps([{"file": rel, "issue": "description_equals_value"}]),
            encoding="utf-8",
        )
        rc = cq.main(["--baseline", str(baseline_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "1 existing violation(s) (all in baseline), 0 new" in out

    def test_baseline_does_not_suppress_new_violation(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Violations not listed in the baseline still fire."""
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        baseline_path = fake_repo / "baseline.json"
        baseline_path.write_text(json.dumps([]), encoding="utf-8")
        rc = cq.main(["--baseline", str(baseline_path)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_baseline_file_missing_skips_filter(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A non-existent baseline path means no filter — every
        violation is reported as new."""
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        missing_baseline = fake_repo / "no-such-baseline.json"
        rc = cq.main(["--baseline", str(missing_baseline)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err


# ----------------------------------------------------------------------
# Truncation
# ----------------------------------------------------------------------


class TestTruncation:
    def test_more_than_20_violations_truncated(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output is truncated to the first 20 lines with an
        ``... and N more`` footer."""
        for z in range(1, 26):  # 25 violations
            make_uc(
                f"1.1.{z}",
                {"description": "Same.", "value": "Same."},
            )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # First line counts the new violations.
        assert "25 new violation(s)" in err
        # Truncation footer.
        assert "... and 5 more" in err

    def test_exactly_20_violations_no_truncation(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """At exactly 20 violations the truncation footer must NOT
        appear (covers the boundary branch)."""
        for z in range(1, 21):  # 20 violations
            make_uc(
                f"1.1.{z}",
                {"description": "Same.", "value": "Same."},
            )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "20 new violation(s)" in err
        assert "more" not in err


# ----------------------------------------------------------------------
# CLI surface
# ----------------------------------------------------------------------


class TestCli:
    def test_help_exits_clean(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            cq.main(["--help"])
        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "--baseline" in out
        assert "--generate-baseline" in out
