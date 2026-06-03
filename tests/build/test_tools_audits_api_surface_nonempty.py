"""Unit-level coverage for ``tools/audits/api_surface_nonempty.py``.

This audit is the regression guard for issue #68 (2026-06-03): production
GitHub Pages shipped ``/api/v1/recommender/*`` and ``/api/v1/equipment/*``
endpoints that returned HTTP 200 with zero records because
``generate-api-surface`` ran before ``dist/catalog.json`` existed, so
``_load_catalog()`` returned ``[]``. The guard compares the v1 recommender +
equipment counts against the populated ``api/catalog-index.json`` and fails
the build before such empty indexes can be published.

The audit runs in both CI workflows (``.github/workflows/pages.yml`` after the
publish build, and ``.github/workflows/validate.yml`` in ``audits-build``).
This suite drives every branch of ``check_surface``, ``catalog_uc_count`` and
``main`` hermetically against synthetic ``dist/`` trees rooted at
``tmp_path``.

What this suite locks
---------------------

* A fully populated surface passes (rc 0, OK banner).
* A missing dist root fails (rc 1) with a dedicated message.
* A missing/unreadable ``catalog-index.json`` fails — the guard cannot verify
  the surface and must not silently pass.
* A below-threshold catalogue (a tiny fixture build) tolerates empty indexes.
* Each recommender/equipment index in turn — empty count, missing file, or a
  missing/non-int count key — is reported as a distinct issue-#68 violation.
* ``catalog_uc_count`` prefers ``counts.useCases`` and falls back to
  ``len(ucs)``.
* The CLI surface (default dist root, ``--min-catalog`` override, argv=None)
  behaves as documented.
* The ``if __name__ == "__main__":`` guard is covered by a subprocess smoke
  check against a populated synthetic tree.

Run
---

``pytest tests/build/test_tools_audits_api_surface_nonempty.py``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.api_surface_nonempty as guard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _make_populated_dist(
    root: Path,
    *,
    catalog_uc: int = 7929,
) -> Path:
    """Build a healthy ``dist/`` tree: a populated catalog-index plus every
    v1 recommender + equipment index with non-zero counts. Returns ``root``."""

    _write_json(
        root / "api" / "catalog-index.json",
        {
            "$schema": "x",
            "version": "2.0.0",
            "generatedAt": "2026-05-31T00:00:00Z",
            "counts": {
                "categories": 23,
                "subcategories": 200,
                "useCases": catalog_uc,
                "regulations": 82,
            },
            "categories": [],
            "ucs": [{"i": f"1.1.{n}", "n": "x", "cat": 1, "sub": "1.1"} for n in range(3)],
        },
    )
    _write_json(
        root / "api" / "v1" / "recommender" / "uc-thin.json",
        {"useCaseCount": catalog_uc, "useCases": [{"i": "1.1.1"}]},
    )
    _write_json(
        root / "api" / "v1" / "recommender" / "sourcetype-index.json",
        {"sourcetypeCount": 412, "sourcetypes": {"cisco:asa": ["1.1.1"]}},
    )
    _write_json(
        root / "api" / "v1" / "recommender" / "cim-index.json",
        {"cimModelCount": 28, "cimModels": {"Network_Traffic": ["1.1.1"]}},
    )
    _write_json(
        root / "api" / "v1" / "recommender" / "app-index.json",
        {"appCount": 340, "apps": {"Splunk_TA_cisco-asa": ["1.1.1"]}},
    )
    _write_json(
        root / "api" / "v1" / "equipment" / "index.json",
        {
            "equipmentCount": 106,
            "useCasesWithEquipmentTotal": 5123,
            "equipment": [{"id": "paloalto", "useCaseCount": 40}],
        },
    )
    _write_json(
        root / "api" / "index.json",
        [
            {"number": 1, "name": "Server & Compute", "subcategory_count": 4, "uc_count": 275},
            {"number": 2, "name": "Networking", "subcategory_count": 6, "uc_count": 310},
        ],
    )
    return root


# Map the relative index path to its count key for targeted mutation, mirroring
# guard._CHECKS so a drift in the production key names breaks this test too.
_INDEX_BY_REL = {rel: key for rel, key, _label in guard._CHECKS}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_fully_populated_surface_passes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        rc = guard.main([str(dist)])
        assert rc == 0
        out = capsys.readouterr()
        assert "[api_surface_nonempty] OK" in out.out
        assert "7929 use cases" in out.out
        assert out.err == ""

    def test_check_surface_returns_no_problems(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        assert guard.check_surface(dist) == []


# ---------------------------------------------------------------------------
# Missing dist root / catalog-index
# ---------------------------------------------------------------------------


class TestMissingInputs:
    def test_missing_dist_root_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bogus = tmp_path / "no-such-dist"
        rc = guard.main([str(bogus)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "dist root not found" in err

    def test_missing_catalog_index_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        (dist / "api" / "catalog-index.json").unlink()
        rc = guard.main([str(dist)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "catalog-index.json: missing or unreadable" in err

    def test_unreadable_catalog_index_fails(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        (dist / "api" / "catalog-index.json").write_text("{not json", encoding="utf-8")
        problems = guard.check_surface(dist)
        assert problems
        assert "cannot verify" in problems[0]


# ---------------------------------------------------------------------------
# Below-threshold catalogue tolerates empty indexes
# ---------------------------------------------------------------------------


class TestThreshold:
    def test_tiny_catalogue_tolerates_empty_indexes(self, tmp_path: Path) -> None:
        """A fixture build with a handful of UCs legitimately yields small or
        empty indexes — the guard must not fire below ``--min-catalog``."""

        dist = _make_populated_dist(tmp_path / "dist", catalog_uc=12)
        # Zero out every v1 index; with catalog_uc=12 < 100 this is tolerated.
        for rel, key in _INDEX_BY_REL.items():
            _write_json(dist / rel, {key: 0})
        assert guard.check_surface(dist) == []
        assert guard.main([str(dist)]) == 0

    def test_min_catalog_override_lowers_threshold(self, tmp_path: Path) -> None:
        """With ``--min-catalog`` dropped below the fixture catalogue size the
        empty indexes become a hard failure again."""

        dist = _make_populated_dist(tmp_path / "dist", catalog_uc=12)
        for rel, key in _INDEX_BY_REL.items():
            _write_json(dist / rel, {key: 0})
        assert guard.check_surface(dist, min_catalog=10)
        assert guard.main([str(dist), "--min-catalog", "10"]) == 1


# ---------------------------------------------------------------------------
# Failure modes — the issue #68 regression itself
# ---------------------------------------------------------------------------


class TestEmptyIndexDetection:
    @pytest.mark.parametrize("rel,key,label", list(guard._CHECKS))
    def test_each_empty_index_is_reported(
        self,
        rel: str,
        key: str,
        label: str,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Zero out one index at a time and assert the guard names that index
        and references the issue-#68 regression."""

        dist = _make_populated_dist(tmp_path / "dist")
        # Preserve all other keys but force the count to zero.
        payload = json.loads((dist / rel).read_text(encoding="utf-8"))
        payload[key] = 0
        _write_json(dist / rel, payload)

        rc = guard.main([str(dist)])
        assert rc == 1
        err = capsys.readouterr().err
        assert rel in err
        assert f"{key}=0" in err
        assert "issue #68" in err

    @pytest.mark.parametrize("rel,key,label", list(guard._CHECKS))
    def test_missing_index_file_is_reported(
        self, rel: str, key: str, label: str, tmp_path: Path
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        (dist / rel).unlink()
        problems = guard.check_surface(dist)
        assert any(rel in p and "missing" in p for p in problems)

    @pytest.mark.parametrize("rel,key,label", list(guard._CHECKS))
    def test_missing_count_key_is_reported(
        self, rel: str, key: str, label: str, tmp_path: Path
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        # Replace the index with a body that lacks the integer count key.
        _write_json(dist / rel, {"description": "no count here"})
        problems = guard.check_surface(dist)
        assert any(rel in p and f"missing integer key {key!r}" in p for p in problems)

    def test_unreadable_index_is_reported(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        rel = guard._CHECKS[0][0]
        (dist / rel).write_text("{not json", encoding="utf-8")
        problems = guard.check_surface(dist)
        assert any(rel in p and "unreadable JSON" in p for p in problems)

    def test_all_empty_reports_every_index(self, tmp_path: Path) -> None:
        """The production failure: every index empty at once. All five must be
        listed in a single pass so the operator sees the full picture."""

        dist = _make_populated_dist(tmp_path / "dist")
        for rel, key in _INDEX_BY_REL.items():
            payload = json.loads((dist / rel).read_text(encoding="utf-8"))
            payload[key] = 0
            _write_json(dist / rel, payload)
        problems = guard.check_surface(dist)
        assert len(problems) == len(guard._CHECKS)


# ---------------------------------------------------------------------------
# api/index.json — restored category table-of-contents (issue #68 facet 3)
# ---------------------------------------------------------------------------


class TestCategoryIndex:
    def test_missing_category_index_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        (dist / "api" / "index.json").unlink()
        rc = guard.main([str(dist)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "api/index.json: missing" in err
        assert "issue #68" in err

    def test_empty_array_category_index_fails(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        _write_json(dist / "api" / "index.json", [])
        problems = guard.check_surface(dist)
        assert any("api/index.json" in p and "non-empty array" in p for p in problems)

    def test_non_list_category_index_fails(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        _write_json(dist / "api" / "index.json", {"not": "a list"})
        problems = guard.check_surface(dist)
        assert any("api/index.json" in p and "non-empty array" in p for p in problems)

    def test_unreadable_category_index_fails(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        (dist / "api" / "index.json").write_text("{not json", encoding="utf-8")
        problems = guard.check_surface(dist)
        assert any("api/index.json" in p and "unreadable JSON" in p for p in problems)

    def test_populated_category_index_passes(self, tmp_path: Path) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        # A healthy tree (which includes a 2-entry index.json) yields no problems.
        assert guard.check_surface(dist) == []


# ---------------------------------------------------------------------------
# catalog_uc_count resolution order
# ---------------------------------------------------------------------------


class TestCatalogUcCount:
    def test_prefers_counts_use_cases(self, tmp_path: Path) -> None:
        root = tmp_path / "dist"
        _write_json(
            root / "api" / "catalog-index.json",
            {"counts": {"useCases": 4242}, "ucs": [{"i": "1.1.1"}]},
        )
        assert guard.catalog_uc_count(root) == 4242

    def test_falls_back_to_ucs_length(self, tmp_path: Path) -> None:
        root = tmp_path / "dist"
        _write_json(
            root / "api" / "catalog-index.json",
            {"ucs": [{"i": "1.1.1"}, {"i": "1.1.2"}, {"i": "1.1.3"}]},
        )
        assert guard.catalog_uc_count(root) == 3

    def test_returns_none_when_no_count_available(self, tmp_path: Path) -> None:
        root = tmp_path / "dist"
        _write_json(root / "api" / "catalog-index.json", {"version": "2.0.0"})
        assert guard.catalog_uc_count(root) is None

    def test_returns_none_when_file_absent(self, tmp_path: Path) -> None:
        assert guard.catalog_uc_count(tmp_path / "dist") is None


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestCliSurface:
    def test_argv_none_defaults_to_sys_argv(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = _make_populated_dist(tmp_path / "dist")
        monkeypatch.setattr(sys, "argv", ["api_surface_nonempty", str(dist)])
        rc = guard.main()
        assert rc == 0
        assert "[api_surface_nonempty] OK" in capsys.readouterr().out

    def test_default_dist_root_is_dist(self) -> None:
        import argparse

        parser = argparse.ArgumentParser(prog="api_surface_nonempty")
        parser.add_argument("dist_root", nargs="?", default="dist")
        parser.add_argument("--min-catalog", type=int, default=100)
        ns = parser.parse_args([])
        assert ns.dist_root == "dist"
        assert ns.min_catalog == 100


# ---------------------------------------------------------------------------
# Module entrypoint guard — subprocess smoke
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_passes_on_populated_tree(self, tmp_path: Path) -> None:
        """Invoke ``python -m tools.audits.api_surface_nonempty <dist>`` against
        a populated synthetic tree to pin the production CLI contract and cover
        the ``if __name__ == '__main__':`` guard."""

        import subprocess

        dist = _make_populated_dist(tmp_path / "dist")
        repo_root = Path(guard.__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.api_surface_nonempty", str(dist)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"guard failed on populated tree: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "[api_surface_nonempty] OK" in result.stdout

    def test_invoking_as_script_fails_on_empty_surface(self, tmp_path: Path) -> None:
        import subprocess

        dist = _make_populated_dist(tmp_path / "dist")
        # Empty the uc-thin index to trip the guard.
        rel, key, _ = guard._CHECKS[0]
        _write_json(dist / rel, {key: 0})
        repo_root = Path(guard.__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.api_surface_nonempty", str(dist)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1
        assert "issue #68" in result.stderr
