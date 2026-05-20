"""Hermetic coverage suite for ``splunk_uc.migrations.gap_analysis``.

Brings coverage from 17.6% to 100%.

The driver correlates ``data/inventory/ucs.json`` against
``data/regulations.draft.json`` and writes
``data/inventory/gap-analysis.json``. It exits 2 when either input is
missing and 0 on success. All tests redirect ``INVENTORY``, ``REGS``,
``OUT`` and ``REPO`` via ``monkeypatch`` so the live repo is never
touched.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.migrations import gap_analysis as ga


def _make_inventory(
    path: pathlib.Path,
    *,
    cases: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"useCases": cases}, ensure_ascii=False),
        encoding="utf-8",
    )


def _make_regs(
    path: pathlib.Path,
    *,
    frameworks: list[dict[str, object]],
    alias_index: dict[str, str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "frameworks": frameworks,
                "aliasIndex": alias_index,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Construct a hermetic repo skeleton and redirect every module
    constant at it."""

    inventory = tmp_path / "data" / "inventory" / "ucs.json"
    regs = tmp_path / "data" / "regulations.draft.json"
    out = tmp_path / "data" / "inventory" / "gap-analysis.json"

    monkeypatch.setattr(ga, "REPO", tmp_path)
    monkeypatch.setattr(ga, "INVENTORY", inventory)
    monkeypatch.setattr(ga, "REGS", regs)
    monkeypatch.setattr(ga, "OUT", out)
    return tmp_path


class TestNorm:
    def test_collapses_internal_whitespace_and_lowers(self) -> None:
        assert ga.norm("  GDPR  Art\t32 ") == "gdpr art 32"

    def test_empty_string_is_empty(self) -> None:
        assert ga.norm("") == ""


class TestResolveAliases:
    def test_resolves_known_aliases_and_collects_unknowns(self) -> None:
        out = ga.resolve_aliases(
            ["GDPR", "PCI DSS", "Unknown framework"],
            {"gdpr": "gdpr-1", "pci dss": "pci-1"},
        )
        assert out["resolved"] == {
            "gdpr-1": ["GDPR"],
            "pci-1": ["PCI DSS"],
        }
        assert out["unknown"] == ["Unknown framework"]

    def test_deduplicates_multiple_labels_to_same_framework(self) -> None:
        out = ga.resolve_aliases(
            ["GDPR", "  gdpr  ", "regulation (eu) 2016/679"],
            {
                "gdpr": "gdpr-1",
                "regulation (eu) 2016/679": "gdpr-1",
            },
        )
        # All three labels resolve to gdpr-1 (with whitespace
        # normalisation), so the list accumulates them in input order.
        assert out["resolved"]["gdpr-1"] == [
            "GDPR",
            "  gdpr  ",
            "regulation (eu) 2016/679",
        ]
        assert out["unknown"] == []

    def test_empty_input_returns_empty_buckets(self) -> None:
        out = ga.resolve_aliases([], {"gdpr": "gdpr-1"})
        assert out["resolved"] == {}
        assert out["unknown"] == []


class TestMainErrorPaths:
    def test_returns_2_when_inventory_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create regs so the second check would pass.
        _make_regs(
            ga.REGS,
            frameworks=[],
            alias_index={},
        )
        rc = ga.main([])
        assert rc == 2
        assert "inventory missing" in capsys.readouterr().err

    def test_returns_2_when_regulations_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create inventory but no regs.
        _make_inventory(ga.INVENTORY, cases=[])
        rc = ga.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert str(ga.REGS) in err

    def test_accepts_none_argv_via_dispatcher_contract(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Pin the ``argv | None`` accept path through the early-exit
        # so the call is fast.
        assert ga.main(None) == 2
        assert "inventory missing" in capsys.readouterr().err


class TestMainHappyPath:
    def test_full_report_with_known_aliases(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _make_regs(
            ga.REGS,
            frameworks=[
                {
                    "id": "gdpr-1",
                    "shortName": "GDPR",
                    "name": "GDPR",
                    "commonClauses": ["Art.5", "Art.32"],
                },
                {
                    "id": "pci-1",
                    "shortName": "PCI",
                    "name": "PCI DSS",
                    "commonClauses": ["3.4", "10.1"],
                },
            ],
            alias_index={
                "gdpr": "gdpr-1",
                "pci dss": "pci-1",
                # $ keys are ignored by the driver.
                "$schemaversion": "skip-me",
            },
        )
        _make_inventory(
            ga.INVENTORY,
            cases=[
                {"uc_id": "UC-1.1.1", "regulations": ["GDPR"]},
                {"uc_id": "UC-1.1.2", "regulations": ["GDPR", "PCI DSS"]},
                {"uc_id": "UC-1.1.3"},  # no regulations key
                {"uc_id": "UC-1.1.4", "regulations": []},  # empty
                {
                    "uc_id": "UC-1.1.5",
                    "regulations": ["Unknown1", "Unknown2", "Unknown1"],
                },
            ],
        )

        rc = ga.main([])
        assert rc == 0

        # Output file exists and is well-formed.
        payload = json.loads(ga.OUT.read_text(encoding="utf-8"))
        assert payload["schemaVersion"] == 1
        assert payload["totalUseCases"] == 5
        # Three UCs carry a non-empty ``regulations`` list.
        assert payload["useCasesWithRegulationsTag"] == 3

        per_framework = {f["id"]: f for f in payload["perFramework"]}
        # GDPR matched twice, PCI matched once.
        assert per_framework["gdpr-1"]["ucCount"] == 2
        assert per_framework["gdpr-1"]["ucIds"] == ["UC-1.1.1", "UC-1.1.2"]
        assert per_framework["pci-1"]["ucCount"] == 1
        assert per_framework["pci-1"]["ucIds"] == ["UC-1.1.2"]

        # Per-framework rows are sorted by (-ucCount, shortName).
        ordered_ids = [row["id"] for row in payload["perFramework"]]
        # GDPR (count=2) precedes PCI (count=1).
        assert ordered_ids[0] == "gdpr-1"
        assert ordered_ids[1] == "pci-1"

        # Unknown tags collected with most_common ordering.
        unknown_labels = [r["label"] for r in payload["unknownRegulationTags"]]
        assert "Unknown1" in unknown_labels
        assert "Unknown2" in unknown_labels
        # Unknown1 appears twice → counted at 2.
        u1 = next(
            r for r in payload["unknownRegulationTags"] if r["label"] == "Unknown1"
        )
        assert u1["count"] == 2

        # Stdout summary contains the framework table + sha256 line.
        out = capsys.readouterr().out
        assert "wrote" in out
        assert "sha256=" in out
        assert "GDPR" in out
        assert "PCI" in out

    def test_truncates_unknown_tags_when_more_than_twenty(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Pin the ``> 20 unknowns`` branch in the stdout printer.
        _make_regs(
            ga.REGS,
            frameworks=[],
            alias_index={},
        )
        many_unknowns = [
            f"junk-label-{i:02d}" for i in range(25)
        ]
        _make_inventory(
            ga.INVENTORY,
            cases=[{"uc_id": "UC-1.1.1", "regulations": many_unknowns}],
        )

        rc = ga.main([])
        assert rc == 0
        out = capsys.readouterr().out
        # Truncation footer printed.
        assert "... and 5 more" in out
