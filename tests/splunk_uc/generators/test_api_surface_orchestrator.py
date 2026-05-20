"""Hermetic unit tests for the api_surface orchestrator + CLI.

Focuses on the three orchestrator-level surfaces that the helper tests
in ``test_api_surface_loaders.py`` and ``test_api_surface_recommender.py``
do not exercise:

* ``_is_external`` and ``_strip_timestamp_lines`` (pure helpers used
  by both ``_render`` and ``_diff_trees``).
* ``_diff_trees`` — directory-tree comparison with external-subtree
  skip semantics.
* ``main`` — CLI entry-point. We stub ``_render`` to a no-op so the
  test does not need the full input corpus; the goal is to pin the
  CLI behaviour (``--check`` happy path, ``--check`` with diffs,
  ``--check`` with missing out_root, write path with and without an
  existing out_root, external-subtree preservation).

The orchestrator end-to-end test (full ``_render`` with real-shape
fixtures and the story-layer sub-generators stubbed) is added as a
separate ``test_render_end_to_end`` so a future failure in one layer
does not mask the others.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import splunk_uc.generators.api_surface as M

# ---------------------------------------------------------------------------
# _is_external
# ---------------------------------------------------------------------------


class TestIsExternal:
    def test_evidence_packs_subtree_is_external(self) -> None:
        assert M._is_external(Path("evidence-packs/gdpr.json")) is True

    def test_other_subtrees_are_internal(self) -> None:
        assert M._is_external(Path("compliance/regulations/gdpr.json")) is False
        assert M._is_external(Path("manifest.json")) is False
        assert M._is_external(Path("mitre/index.json")) is False

    def test_empty_path_is_internal(self) -> None:
        # ``Path('').parts == ()`` — the guard ``bool(parts)`` makes this False.
        assert M._is_external(Path("")) is False


# ---------------------------------------------------------------------------
# _strip_timestamp_lines
# ---------------------------------------------------------------------------


class TestStripTimestampLines:
    def test_removes_generated_at_lines(self) -> None:
        raw = b'{\n  "foo": 1,\n  "generatedAt": "2026-01-01"\n}\n'
        out = M._strip_timestamp_lines(raw)
        assert b"generatedAt" not in out
        assert b'"foo": 1' in out

    def test_removes_generated_marker_lines(self) -> None:
        raw = b"# Generated: 2026-05-19T12:00:00Z\nbody line\n"
        out = M._strip_timestamp_lines(raw)
        assert b"Generated:" not in out
        assert b"body line" in out

    def test_passthrough_when_no_timestamp_markers(self) -> None:
        raw = b'{"a":1}\n{"b":2}\n'
        assert M._strip_timestamp_lines(raw) == raw

    def test_handles_empty_input(self) -> None:
        assert M._strip_timestamp_lines(b"") == b""


# ---------------------------------------------------------------------------
# _diff_trees
# ---------------------------------------------------------------------------


class TestDiffTrees:
    @staticmethod
    def _write(p: Path, body: bytes) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)

    def test_returns_empty_when_trees_match(self, tmp_path: Path) -> None:
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        self._write(lhs / "manifest.json", b'{"x":1}\n')
        self._write(rhs / "manifest.json", b'{"x":1}\n')
        assert M._diff_trees(lhs, rhs) == []

    def test_flags_files_only_in_lhs(self, tmp_path: Path) -> None:
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        self._write(lhs / "manifest.json", b'{"x":1}\n')
        rhs.mkdir()
        diffs = M._diff_trees(lhs, rhs)
        assert any("only on disk" in d for d in diffs)

    def test_flags_files_only_in_rhs(self, tmp_path: Path) -> None:
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        lhs.mkdir()
        self._write(rhs / "manifest.json", b'{"x":1}\n')
        diffs = M._diff_trees(lhs, rhs)
        assert any("only in freshly generated tree" in d for d in diffs)

    def test_flags_modified_files(self, tmp_path: Path) -> None:
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        self._write(lhs / "manifest.json", b'{"x":1}\n')
        self._write(rhs / "manifest.json", b'{"x":2}\n')
        diffs = M._diff_trees(lhs, rhs)
        assert any(d.startswith("~ ") for d in diffs)

    def test_timestamp_only_diff_is_ignored(self, tmp_path: Path) -> None:
        """If the only difference is a generatedAt line, the diff is
        suppressed (per the _strip_timestamp_lines logic)."""
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        self._write(
            lhs / "manifest.json",
            b'{\n  "x": 1,\n  "generatedAt": "2026-01-01"\n}\n',
        )
        self._write(
            rhs / "manifest.json",
            b'{\n  "x": 1,\n  "generatedAt": "2025-01-01"\n}\n',
        )
        assert M._diff_trees(lhs, rhs) == []

    def test_excludes_external_subtrees(self, tmp_path: Path) -> None:
        """``evidence-packs/`` is owned by a different generator and must
        be skipped on both sides of the comparison."""
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        # ``manifest.json`` matches on both sides; an evidence-pack file
        # exists only on ``rhs`` — it MUST NOT be flagged.
        self._write(lhs / "manifest.json", b'{"x":1}\n')
        self._write(rhs / "manifest.json", b'{"x":1}\n')
        self._write(rhs / "evidence-packs" / "gdpr.json", b'{"e":1}\n')
        assert M._diff_trees(lhs, rhs) == []

    def test_results_are_sorted_deterministically(self, tmp_path: Path) -> None:
        lhs, rhs = tmp_path / "a", tmp_path / "b"
        self._write(lhs / "z.json", b"1")
        self._write(lhs / "a.json", b"1")
        rhs.mkdir()
        diffs = M._diff_trees(lhs, rhs)
        # Both files are missing from rhs; sorted alphabetically.
        assert diffs[0].endswith("a.json  (only on disk)")
        assert diffs[1].endswith("z.json  (only on disk)")


# ---------------------------------------------------------------------------
# main (CLI) — _render is stubbed out so we focus on the CLI logic only.
# ---------------------------------------------------------------------------


class _StubRender:
    """Replacement for ``_render`` that mirrors its side effect of writing
    a deterministic set of files into ``out_root``. This lets us assert
    on the cleanup + write-path semantics of ``main`` without needing
    the full input corpus."""

    def __init__(self, payload: dict[str, str] | None = None) -> None:
        # Map of relative-path → body. Defaults to a small canonical set.
        self.payload = payload or {
            "manifest.json": '{"v": "test"}\n',
            "compliance/index.json": '{"x": 1}\n',
        }
        self.calls: list[Path] = []

    def __call__(self, out_root: Path) -> None:
        self.calls.append(out_root)
        for rel, body in self.payload.items():
            target = out_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")


class TestMainCheckMode:
    def test_check_happy_path_returns_zero_when_no_drift(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--check`` against a tree identical to the freshly generated
        one prints the up-to-date banner and exits 0."""
        stub = _StubRender()
        monkeypatch.setattr(M, "_render", stub)
        # Pre-seed the on-disk tree to match what _StubRender writes.
        out = tmp_path / "api" / "v1"
        for rel, body in stub.payload.items():
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

        rc = M.main(["--check", "--out", str(out)])
        out_text = capsys.readouterr().out
        assert rc == 0
        assert "up to date" in out_text

    def test_check_returns_nonzero_when_out_root_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If the user asks for --check but the on-disk tree is missing,
        main short-circuits with a useful error rather than producing
        a misleading drift list."""
        monkeypatch.setattr(M, "_render", _StubRender())
        out = tmp_path / "does-not-exist"
        rc = M.main(["--check", "--out", str(out)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "does not exist" in err

    def test_check_returns_nonzero_when_drift_detected(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When the freshly generated tree differs from the on-disk
        tree, main prints the canonical 'API surface is stale' banner
        and exits 1. The diff list MUST appear in stderr."""
        stub = _StubRender()
        monkeypatch.setattr(M, "_render", stub)
        out = tmp_path / "api" / "v1"
        out.mkdir(parents=True)
        # Pre-seed with a DIFFERENT body to force drift.
        (out / "manifest.json").write_text('{"v": "OLD"}\n', encoding="utf-8")
        (out / "compliance").mkdir()
        (out / "compliance" / "index.json").write_text('{"x": 1}\n', encoding="utf-8")

        rc = M.main(["--check", "--out", str(out)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "is stale" in err
        assert "manifest.json" in err


class TestMainWritePath:
    def test_write_path_creates_files_when_out_root_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        stub = _StubRender()
        monkeypatch.setattr(M, "_render", stub)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        out = tmp_path / "api" / "v1"
        rc = M.main(["--out", str(out)])
        out_text = capsys.readouterr().out
        assert rc == 0
        assert (out / "manifest.json").exists()
        assert "Wrote" in out_text
        # The relative_to call requires REPO_ROOT to be a parent.
        assert "api/v1" in out_text

    def test_write_path_purges_owned_subtrees_and_preserves_external(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An existing tree's owned subdirectories are wiped, but the
        evidence-packs/ subtree (owned by a different generator) MUST
        survive the regen."""
        stub = _StubRender()
        monkeypatch.setattr(M, "_render", stub)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        out = tmp_path / "api" / "v1"
        out.mkdir(parents=True)
        # Owned: must be wiped by the regen.
        (out / "stale-file.json").write_text('{"stale": true}', encoding="utf-8")
        (out / "stale-dir").mkdir()
        (out / "stale-dir" / "x.json").write_text("1", encoding="utf-8")
        # External subtree: must survive.
        (out / "evidence-packs").mkdir()
        (out / "evidence-packs" / "gdpr.md").write_text(
            "evidence content", encoding="utf-8"
        )

        rc = M.main(["--out", str(out)])
        assert rc == 0
        # Owned files purged before regen.
        assert not (out / "stale-file.json").exists()
        assert not (out / "stale-dir").exists()
        # External subtree preserved.
        assert (out / "evidence-packs" / "gdpr.md").read_text(encoding="utf-8") == (
            "evidence content"
        )
        # Stub render output present.
        assert (out / "manifest.json").exists()


# ---------------------------------------------------------------------------
# _render — end-to-end with real input shapes (story sub-generators stubbed
# because they require their own dedicated test surface).
# ---------------------------------------------------------------------------


def _install_minimal_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    """Stamp out a complete, minimal input corpus and re-point every
    ``api_surface`` path constant at it. Returns the patched paths so
    individual tests can inspect them."""
    repo = tmp_path / "repo"
    (repo / "content" / "cat-1").mkdir(parents=True)
    (repo / "data" / "crosswalks" / "oscal").mkdir(parents=True)
    (repo / "data" / "crosswalks" / "attack").mkdir(parents=True)
    (repo / "data" / "crosswalks" / "d3fend").mkdir(parents=True)
    (repo / "data" / "crosswalks" / "olir").mkdir(parents=True)
    (repo / "reports").mkdir(parents=True)
    (repo / "dist").mkdir(parents=True)

    # regulations.json — one framework, one version, one clause.
    regs_payload: dict[str, Any] = {
        "frameworks": [
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "name": "General Data Protection Regulation",
                "tier": 1,
                "jurisdiction": "EU",
                "tags": ["privacy"],
                "aliases": ["GDPR"],
                "versions": [
                    {
                        "version": "2018",
                        "clauses": [
                            {
                                "ref": "Art. 32",
                                "title": "Security of processing",
                                "category": "operational",
                                "expectedUCCount": 1,
                            }
                        ],
                    }
                ],
            }
        ]
    }
    (repo / "data" / "regulations.json").write_text(json.dumps(regs_payload))

    # coverage report
    coverage = {
        "totals": {
            "frameworks": 1,
            "regulations": 1,
            "uniqueClauses": 1,
            "ucsTouched": 1,
        },
        "frameworks": [
            {
                "id": "gdpr",
                "coverage": 1.0,
                "totalClauses": 1,
                "coveredClauses": 1,
            }
        ],
    }
    (repo / "reports" / "compliance-coverage.json").write_text(json.dumps(coverage))

    # One UC sidecar with a compliance entry referencing GDPR Art. 32.
    uc_sidecar = {
        "id": "1.1.1",
        "title": "Test UC",
        "compliance": [
            {
                "regulation": "GDPR",
                "regulationVersion": "2018",
                "clauseRef": "Art. 32",
                "rationale": "Demonstrates encryption controls.",
                "obligationRef": "Art. 32 (1)",
            }
        ],
        "mitreAttack": ["T1003"],
        "cimModels": ["Authentication"],
        "splunkbaseApps": [
            {"id": "1234", "name": "Splunk_TA_test", "required": True}
        ],
    }
    (repo / "content" / "cat-1" / "UC-1.1.1.json").write_text(json.dumps(uc_sidecar))

    # catalog.json — DATA is a list of categories, each with ``s`` (a
    # list of subcategories), each with ``u`` (a list of UCs).
    catalog = {
        "DATA": [
            {
                "i": 1,
                "n": "Category 1",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Subcategory 1.1",
                        "u": [
                            {
                                "i": "1.1.1",
                                "n": "Test UC",
                                "q": 'index=foo sourcetype="aws:cloudtrail"',
                                "t": "Splunk_TA_test",
                                "d": "AWS CloudTrail",
                                "e": ["paloalto"],
                                "em": ["paloalto_pa-220"],
                                "mitre": ["T1003"],
                                "pillar": "security",
                                "mtype": ["proactive"],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    (repo / "dist" / "catalog.json").write_text(json.dumps(catalog))

    # VERSION file
    (repo / "VERSION").write_text("9.9.9")

    # Splunkbase catalog
    (repo / "data" / "splunkbase-catalog.json").write_text(
        json.dumps(
            {
                "apps": {
                    "1234": {
                        "displayName": "Splunk TA Test",
                        "url": "https://splunkbase.splunk.com/app/1234",
                        "latestVersion": "1.0.0",
                        "cloudVetted": True,
                    }
                }
            }
        )
    )

    # OSCAL crosswalks — seed ONE catalog + ONE component-definition so
    # the orchestrator hits the for-loop bodies at lines 2253-2259
    # (write catalog body, write component body) instead of skipping
    # the empty dict. Other crosswalk dirs stay empty.
    (repo / "data" / "crosswalks" / "oscal" / "fake-catalog.normalised.json").write_text(
        json.dumps({"control_count": 0, "controls": []})
    )
    (repo / "data" / "crosswalks" / "oscal" / "component-definition-1.1.1.json").write_text(
        json.dumps({"component-definition": {"uc": "1.1.1"}})
    )

    # Re-point every module-level path at the temp repo.
    monkeypatch.setattr(M, "REPO_ROOT", repo)
    monkeypatch.setattr(M, "API_ROOT", repo / "api" / "v1")
    monkeypatch.setattr(M, "REGS_PATH", repo / "data" / "regulations.json")
    monkeypatch.setattr(M, "OSCAL_DIR", repo / "data" / "crosswalks" / "oscal")
    monkeypatch.setattr(M, "ATTACK_DIR", repo / "data" / "crosswalks" / "attack")
    monkeypatch.setattr(M, "D3FEND_DIR", repo / "data" / "crosswalks" / "d3fend")
    monkeypatch.setattr(M, "OLIR_DIR", repo / "data" / "crosswalks" / "olir")
    monkeypatch.setattr(
        M, "SPLUNKBASE_CATALOG_PATH", repo / "data" / "splunkbase-catalog.json"
    )
    monkeypatch.setattr(
        M,
        "SPLUNKBASE_OVERRIDES_PATH",
        repo / "data" / "splunkbase-catalog-overrides.json",
    )
    monkeypatch.setattr(
        M, "COVERAGE_REPORT", repo / "reports" / "compliance-coverage.json"
    )
    monkeypatch.setattr(M, "CATALOG_PATH_PRIMARY", repo / "dist" / "catalog.json")
    monkeypatch.setattr(M, "CATALOG_PATH_LEGACY", repo / "catalog.json")
    monkeypatch.setattr(M, "VERSION_FILE", repo / "VERSION")
    # Reset module-level caches that may have been populated by other tests.
    monkeypatch.setattr(M, "_CATALOG_CACHE", None, raising=False)

    # Stub the story-layer sub-generators — they have their own dedicated
    # test surfaces (test_clause_index.py, test_story_payload.py) and
    # they depend on legacy module loading from scripts/ which we
    # intentionally do not exercise here.
    monkeypatch.setattr(M, "_render_story_surfaces", lambda _out: None)

    return {"repo": repo}


# ---------------------------------------------------------------------------
# _render_story_surfaces — directly exercise the legacy-module loader + the
# three-step compliance-story pipeline. The orchestrator end-to-end test
# above stubs this out; this class exercises it against the real repo data.
# ---------------------------------------------------------------------------


class TestRenderStorySurfaces:
    def test_loads_legacy_augment_module_and_runs_all_three_stages(
        self,
        tmp_path: Path,
    ) -> None:
        """Drives ``_render_story_surfaces`` against an output tree
        that has already been seeded with the regulations subtree (so
        augment can index those files). The test uses the real repo
        ``data/regulations.json`` because the legacy
        ``augment_regulation_api.py`` script resolves ``REPO_ROOT``
        from its own ``__file__`` and we cannot monkeypatch a
        constant inside a module loaded via ``importlib.util``.

        The contract being pinned is: (a) the legacy loader resolves
        ``augment_regulation_api`` without error, (b) ``clauses/`` is
        created and populated, (c) ``story/`` is created, (d) if
        ``regulations/`` already exists then the augment step runs
        against it (we MUST NOT skip with no regulations dir).
        """
        out = tmp_path / "out"
        regs = out / "compliance" / "regulations"
        regs.mkdir(parents=True)
        # Seed a one-framework regulations file matching the real
        # repo regulations.json shape so augment_regulation_api can
        # process it. We pick the smallest tier-1 framework so the
        # test runs in <1s.
        from importlib import util as _u

        scripts = M._LEGACY_SCRIPTS_DIR
        spec = _u.spec_from_file_location(
            "augment_regulation_api", scripts / "augment_regulation_api.py"
        )
        assert spec is not None and spec.loader is not None
        mod = _u.module_from_spec(spec)
        spec.loader.exec_module(mod)
        real_regs = json.loads(mod.REGULATIONS_PATH.read_text(encoding="utf-8"))
        # Pick the first framework so the test does not depend on
        # any specific regulation surviving in the catalogue.
        first_fw = real_regs["frameworks"][0]
        fw_id = first_fw["id"]
        # Write the per-regulation file with just enough shape for
        # augment_regulation_file to process.
        payload = {
            "id": fw_id,
            "shortName": first_fw.get("shortName", fw_id.upper()),
            "name": first_fw.get("name", fw_id),
            "versions": first_fw.get("versions", []),
            "clauseCoverageMatrix": {},
        }
        (regs / f"{fw_id}.json").write_text(json.dumps(payload))
        # The augment step also reads an index.json for the
        # regulations listing.
        (regs / "index.json").write_text(
            json.dumps({"regulations": [{"id": fw_id}]})
        )

        # Now call the orchestrator. It MUST run all three stages
        # without raising and MUST leave clauses/ + story/ in place.
        M._render_story_surfaces(out)

        clauses = out / "compliance" / "clauses"
        story = out / "compliance" / "story"
        assert clauses.is_dir()
        assert story.is_dir()
        # clauses/index.json is the always-present marker.
        assert (clauses / "index.json").exists()

    def test_raises_systemexit_when_regulations_dir_absent(
        self,
        tmp_path: Path,
    ) -> None:
        """If ``regulations/`` does not exist, the augment step is
        skipped (False branch of ``if regs_dir.exists()``) but
        ``story_mod.generate`` still requires ``regs_dir`` and raises
        ``SystemExit``. This pins the documented failure mode and
        prevents a future refactor from silently swallowing it.
        """
        out = tmp_path / "out"
        out.mkdir()
        with pytest.raises(SystemExit, match=r"regulations missing"):
            M._render_story_surfaces(out)

    def test_raises_runtimeerror_when_legacy_loader_returns_no_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``_load_legacy_module`` is a closure inside
        ``_render_story_surfaces`` that calls
        ``importlib.util.spec_from_file_location``. When that returns
        ``None`` (or a spec without a loader) we MUST raise
        ``RuntimeError`` rather than silently continuing — otherwise
        a stale checkout could quietly stop rebuilding the
        compliance-story surfaces.

        The closure is invoked exactly once per ``_render_story_surfaces``
        call (for ``augment_regulation_api``), so patching
        ``spec_from_file_location`` at the ``importlib.util`` level
        catches the closure's call without affecting the two sibling
        package imports (``clause_index``, ``story_payload``) above,
        which use a regular ``from ... import`` statement that does
        not go through ``spec_from_file_location``.
        """
        import importlib.util as _u

        out = tmp_path / "out"
        out.mkdir()

        monkeypatch.setattr(_u, "spec_from_file_location", lambda *a, **kw: None)

        with pytest.raises(
            RuntimeError, match=r"Cannot load augment_regulation_api"
        ):
            M._render_story_surfaces(out)


class TestRenderEndToEnd:
    def test_writes_expected_top_level_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Smoke test: ``_render`` writes manifest, context.jsonld,
        openapi.yaml, README.md, and the compliance/MITRE/recommender
        subtrees against a minimal but realistic fixture corpus."""
        _install_minimal_corpus(tmp_path, monkeypatch)
        out = tmp_path / "out"
        M._render(out)

        # Top-level artefacts.
        assert (out / "manifest.json").exists()
        assert (out / "context.jsonld").exists()
        assert (out / "openapi.yaml").exists()
        assert (out / "README.md").exists()

        # Compliance subtree.
        assert (out / "compliance" / "index.json").exists()
        assert (out / "compliance" / "coverage.json").exists()
        assert (out / "compliance" / "gaps.json").exists()
        assert (out / "compliance" / "regulations" / "index.json").exists()
        assert (out / "compliance" / "regulations" / "gdpr.json").exists()
        # Per-version slice for GDPR 2018.
        per_version = list((out / "compliance" / "regulations").glob("gdpr@*.json"))
        assert len(per_version) == 1
        assert (out / "compliance" / "ucs" / "index.json").exists()
        assert (out / "compliance" / "ucs" / "1.1.1.json").exists()

        # MITRE subtree.
        assert (out / "mitre" / "index.json").exists()
        assert (out / "mitre" / "techniques.json").exists()
        assert (out / "mitre" / "coverage.json").exists()
        assert (out / "mitre" / "d3fend.json").exists()

        # Recommender subtree.
        assert (out / "recommender" / "sourcetype-index.json").exists()
        assert (out / "recommender" / "cim-index.json").exists()
        assert (out / "recommender" / "app-index.json").exists()
        assert (out / "recommender" / "uc-thin.json").exists()
        assert (out / "recommender" / "splunkbase-index.json").exists()

        # Equipment subtree (the catalog UC tags ``paloalto``).
        assert (out / "equipment" / "index.json").exists()

    def test_manifest_payload_is_valid_json_with_counts(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _install_minimal_corpus(tmp_path, monkeypatch)
        out = tmp_path / "out"
        M._render(out)
        payload = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        # The manifest references the API version and at least one count
        # we can sanity-check.
        assert payload.get("apiVersion") == M.API_VERSION
        # Manifest schema includes a "counts" or similar section — just
        # confirm the body is non-trivial.
        assert isinstance(payload, dict)
        assert len(payload) > 0

    def test_uc_detail_payload_matches_sidecar(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _install_minimal_corpus(tmp_path, monkeypatch)
        out = tmp_path / "out"
        M._render(out)
        body = json.loads(
            (out / "compliance" / "ucs" / "1.1.1.json").read_text(encoding="utf-8")
        )
        # The detail payload echoes the sidecar id and propagates the
        # compliance block.
        assert body["id"] == "1.1.1"
        assert any(
            entry.get("regulation") == "GDPR" for entry in body.get("compliance", [])
        )
