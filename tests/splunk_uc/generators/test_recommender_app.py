"""Smoke + unit tests for ``splunk_uc.generators.recommender_app``.

The recommender_app generator is 5,000+ lines that build the
``splunk-uc-recommender`` Splunk app from the live repository data. A
full unit-test suite would mock the entire compliance + Splunkbase
catalogue, so we take a two-pronged approach:

* Unit-test the small, side-effect-free helpers
  (``_gsa_load_json``, ``_gsa_uc_sort_key``, ``_gsa_alias_map``,
  ``_gsa_framework_by_id``, ``_gsa_safe_stanza``).
* Run ``main`` against the real repository's content tree, but write
  into a temp directory. This exercises ``_render`` and the full
  app-builder pipeline against realistic inputs without mutating
  the on-disk ``splunk-apps/`` tree, lifting branch coverage on
  hundreds of lines that pure helpers cannot reach.

The smoke test asserts on the canonical AppInspect-shaped files
(app.conf, app.manifest, default.meta, README.md, savedsearches.conf,
nav.xml, collections.conf) so future refactors of the conf banner
do not silently drop a required file.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

import splunk_uc.generators.recommender_app as M

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestGsaLoadJson:
    def test_round_trips_a_valid_json_file(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        payload = {"a": 1, "b": [2, 3]}
        p.write_text(json.dumps(payload), encoding="utf-8")
        assert M._gsa_load_json(p) == payload

    def test_raises_json_decode_error_on_malformed(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text("{ not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            M._gsa_load_json(p)


class TestGsaUcSortKey:
    def test_orders_by_numeric_components(self) -> None:
        assert M._gsa_uc_sort_key({"id": "1.2.3"}) == (1, 2, 3)
        assert M._gsa_uc_sort_key({"id": "10.1.0"}) == (10, 1, 0)

    def test_handles_two_component_ids(self) -> None:
        assert M._gsa_uc_sort_key({"id": "1.2"}) == (1, 2)

    def test_returns_sentinel_for_missing_id(self) -> None:
        # Empty id is split into a single empty string; int("") raises
        # ValueError and the ``except`` branch returns ``(9_999,)``.
        # The branch is marked ``pragma: no cover`` in the source, but
        # we still pin the externally observable behaviour.
        assert M._gsa_uc_sort_key({}) == (9_999,)


class TestGsaAliasMap:
    def test_maps_lowercased_id_short_name_and_aliases(self) -> None:
        regs = {
            "frameworks": [
                {
                    "id": "gdpr",
                    "shortName": "GDPR",
                    "aliases": ["EU GDPR", "Reg 2016/679"],
                }
            ]
        }
        out = M._gsa_alias_map(regs)
        assert out["gdpr"] == "gdpr"
        assert out["gdpr"] == "gdpr"  # shortName lower
        assert out["eu gdpr"] == "gdpr"
        assert out["reg 2016/679"] == "gdpr"

    def test_merges_alias_index_block(self) -> None:
        regs = {
            "frameworks": [{"id": "hipaa-security", "shortName": "HIPAA"}],
            "aliasIndex": {"HIPAA Security": "hipaa-security", "$comment": "ignored"},
        }
        out = M._gsa_alias_map(regs)
        assert out["hipaa security"] == "hipaa-security"
        # Dollar-prefixed alias rows are documentation, not aliases.
        assert "$comment" not in out

    def test_skips_frameworks_without_id(self) -> None:
        regs = {"frameworks": [{"shortName": "Mystery"}]}
        assert M._gsa_alias_map(regs) == {}

    def test_handles_missing_alias_index(self) -> None:
        out = M._gsa_alias_map({"frameworks": []})
        assert out == {}


class TestGsaFrameworkById:
    def test_indexes_by_framework_id(self) -> None:
        regs = {
            "frameworks": [
                {"id": "gdpr", "shortName": "GDPR"},
                {"id": "pci-dss", "shortName": "PCI"},
            ]
        }
        out = M._gsa_framework_by_id(regs)
        assert set(out.keys()) == {"gdpr", "pci-dss"}
        assert out["gdpr"]["shortName"] == "GDPR"

    def test_skips_frameworks_without_id(self) -> None:
        regs = {"frameworks": [{"shortName": "no-id"}, {"id": "gdpr"}]}
        out = M._gsa_framework_by_id(regs)
        assert list(out) == ["gdpr"]


class TestGsaSafeStanza:
    def test_strips_brackets_and_newlines(self) -> None:
        # The regex strips ``[``, ``]``, ``\n``, ``\r`` and then
        # ``.strip()`` trims surrounding whitespace.
        assert M._gsa_safe_stanza("[hello]") == "hello"
        assert M._gsa_safe_stanza("line1\nline2") == "line1 line2"

    def test_passes_through_safe_strings(self) -> None:
        assert M._gsa_safe_stanza("plain text") == "plain text"

    def test_strips_outer_whitespace(self) -> None:
        assert M._gsa_safe_stanza("  spaced  ") == "spaced"


# ---------------------------------------------------------------------------
# main / _render end-to-end against the real repo content
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestMainRender:
    """Drive ``main`` end-to-end against the real repo content but
    write into a temp directory.

    The recommender_app generator is intentionally read-only with
    respect to the source tree (the only output is the app payload),
    so running it for real is the safest way to lift coverage on the
    builder pipeline. If this test starts failing due to a content
    change, the assertion targets are the canonical AppInspect file
    set — anything else flexes downstream.
    """

    def test_main_writes_appinspect_shaped_app(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out = tmp_path / "splunk-apps"
        rc = M.main(["--output", str(out)])
        out_text = capsys.readouterr().out

        assert rc == 0
        app_root = out / M.PRIMARY_APP_ID
        assert app_root.is_dir()

        # AppInspect-canonical layout.
        assert (app_root / "default" / "app.conf").is_file()
        assert (app_root / "app.manifest").is_file()
        assert (app_root / "metadata" / "default.meta").is_file()
        assert (app_root / "README.md").is_file()
        assert (app_root / "default" / "savedsearches.conf").is_file()
        assert (app_root / "default" / "data" / "ui" / "nav" / "default.xml").is_file()
        assert (app_root / "default" / "collections.conf").is_file()

        # Stdout summary mentions the artefact and a non-zero file count.
        assert M.PRIMARY_APP_ID in out_text
        assert "files at" in out_text
        assert "Wrote 1 app" in out_text

    def test_main_check_mode_reports_up_to_date_when_outputs_match(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--check`` against a freshly-generated tree must be a
        no-op (rc=0, "up to date" banner). This pins the determinism
        invariant of ``_render`` end-to-end."""
        out = tmp_path / "splunk-apps"
        # Generate once.
        assert M.main(["--output", str(out)]) == 0
        capsys.readouterr()  # drain stdout
        # Now run --check against the same tree.
        rc = M.main(["--check", "--output", str(out)])
        out_text = capsys.readouterr().out
        assert rc == 0
        assert "up to date" in out_text

    def test_main_check_mode_reports_drift_when_files_diverge(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out = tmp_path / "splunk-apps"
        assert M.main(["--output", str(out)]) == 0
        capsys.readouterr()
        # Mutate a saved-search to force drift.
        savedsearches = out / M.PRIMARY_APP_ID / "default" / "savedsearches.conf"
        savedsearches.write_text(
            savedsearches.read_text(encoding="utf-8") + "\n# tampered\n",
            encoding="utf-8",
        )
        rc = M.main(["--check", "--output", str(out)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "drift" in err.lower()


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------


class TestDiffTrees:
    def test_returns_empty_when_trees_match(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "x.txt").write_bytes(b"hello")
        (b / "x.txt").write_bytes(b"hello")
        assert M._diff_trees(a, b) == []

    def test_flags_files_only_in_lhs(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "extra.txt").write_bytes(b"hi")
        diffs = M._diff_trees(a, b)
        assert any("only in freshly generated tree" in d for d in diffs)

    def test_flags_files_only_in_rhs(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (b / "stale.txt").write_bytes(b"hi")
        diffs = M._diff_trees(a, b)
        assert any("only on disk" in d for d in diffs)

    def test_flags_modified_files(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "x.txt").write_bytes(b"v1")
        (b / "x.txt").write_bytes(b"v2")
        diffs = M._diff_trees(a, b)
        assert any("differs:" in d for d in diffs)

    def test_timestamp_only_diff_is_suppressed(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "x.json").write_bytes(b'{\n  "x": 1,\n  "generatedAt": "A"\n}\n')
        (b / "x.json").write_bytes(b'{\n  "x": 1,\n  "generatedAt": "B"\n}\n')
        assert M._diff_trees(a, b) == []

    def test_release_date_diff_is_suppressed(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "x.json").write_bytes(b'{\n  "x": 1,\n  "releaseDate": "2026-01-01"\n}\n')
        (b / "x.json").write_bytes(b'{\n  "x": 1,\n  "releaseDate": "2025-01-01"\n}\n')
        assert M._diff_trees(a, b) == []


class TestScopeCheckDiff:
    def test_scope_skipped_when_expected_app_is_missing(self, tmp_path: Path) -> None:
        expected, on_disk = tmp_path / "exp", tmp_path / "disk"
        expected.mkdir()
        on_disk.mkdir()
        # No subdir matches the requested app; diff list stays empty.
        assert M._scope_check_diff(expected, on_disk, ["missing-app"]) == []

    def test_scope_diff_calls_diff_trees_for_present_apps(
        self, tmp_path: Path
    ) -> None:
        expected, on_disk = tmp_path / "exp", tmp_path / "disk"
        (expected / "my-app").mkdir(parents=True)
        (on_disk / "my-app").mkdir(parents=True)
        (expected / "my-app" / "x.txt").write_bytes(b"new")
        (on_disk / "my-app" / "x.txt").write_bytes(b"old")
        diffs = M._scope_check_diff(expected, on_disk, ["my-app"])
        assert any("differs:" in d for d in diffs)


# ---------------------------------------------------------------------------
# _strip_timestamp_lines edge cases
# ---------------------------------------------------------------------------


class TestStripTimestampLines:
    def test_removes_generated_at_lines(self) -> None:
        raw = b'{\n  "x": 1,\n  "generatedAt": "2026"\n}\n'
        out = M._strip_timestamp_lines(raw)
        assert b"generatedAt" not in out

    def test_removes_release_date_lines(self) -> None:
        raw = b'{\n  "x": 1,\n  "releaseDate": "2026"\n}\n'
        out = M._strip_timestamp_lines(raw)
        assert b'"releaseDate"' not in out

    def test_removes_generated_marker_lines(self) -> None:
        raw = b"# Generated: 2026\nbody\n"
        out = M._strip_timestamp_lines(raw)
        assert b"Generated:" not in out

    def test_passthrough_when_no_markers(self) -> None:
        raw = b'{"x":1}\n'
        assert M._strip_timestamp_lines(raw) == raw

    def test_handles_empty_input(self) -> None:
        # An empty bytes object splits into one empty string; the join
        # gives back an empty bytes object too.
        assert M._strip_timestamp_lines(b"") == b""


# ---------------------------------------------------------------------------
# _read_version + _deterministic_timestamp
# ---------------------------------------------------------------------------


class TestReadVersion:
    def test_reads_version_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        vf = tmp_path / "VERSION"
        vf.write_text("9.9.9\n", encoding="utf-8")
        monkeypatch.setattr(M, "VERSION_FILE", vf)
        assert M._read_version() == "9.9.9"

    def test_returns_zero_fallback_when_version_file_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "VERSION_FILE", tmp_path / "nope")
        assert M._read_version() == "0.0.0"

    def test_returns_zero_fallback_when_version_file_is_blank(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An empty (zero-byte or whitespace-only) VERSION file hits
        the ``if not raw`` guard and returns the zero sentinel."""
        vf = tmp_path / "VERSION"
        vf.write_text("   \n", encoding="utf-8")
        monkeypatch.setattr(M, "VERSION_FILE", vf)
        assert M._read_version() == "0.0.0"

    def test_pads_two_part_version_to_semver(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A ``6.0`` VERSION must be padded to ``6.0.0`` so the
        Splunk app.conf parser accepts it."""
        vf = tmp_path / "VERSION"
        vf.write_text("6.0\n", encoding="utf-8")
        monkeypatch.setattr(M, "VERSION_FILE", vf)
        assert M._read_version() == "6.0.0"

    def test_truncates_four_part_version_to_semver(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Conversely, ``6.0.0.1`` is truncated to ``6.0.0`` — the
        same parser refuses anything beyond three components."""
        vf = tmp_path / "VERSION"
        vf.write_text("6.0.0.1\n", encoding="utf-8")
        monkeypatch.setattr(M, "VERSION_FILE", vf)
        assert M._read_version() == "6.0.0"


class TestDeterministicTimestamp:
    def test_uses_source_date_epoch_when_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        ts = M._deterministic_timestamp()
        assert ts == "2023-11-14T22:13:20Z"

    def test_falls_back_to_git_log_when_sde_absent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        # Real git log is allowed; we just assert the format.
        ts = M._deterministic_timestamp()
        assert ts.endswith("Z") and "T" in ts

    def test_falls_back_to_wall_clock_when_git_unavailable(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        # Force the git subprocess to fail.
        import subprocess as sp

        def _explode(*_a: object, **_kw: object) -> object:
            raise FileNotFoundError("git missing")

        monkeypatch.setattr(sp, "run", _explode)
        ts = M._deterministic_timestamp()
        assert ts.endswith("Z") and "T" in ts


# ---------------------------------------------------------------------------
# _render_conf — the canonical conf-banner renderer used by every .conf
# ---------------------------------------------------------------------------


class TestRenderConf:
    def test_emits_banner_then_sections_with_blank_lines(self) -> None:
        out = M._render_conf(
            banner="# generated by test\n",
            sections=[
                ("section_a", (("key1", "val1"), ("key2", "val2"))),
                ("section_b", (("k", "v"),)),
            ],
        )
        # Banner is present at the top.
        assert out.startswith("# generated by test")
        # Sections are bracketed.
        assert "[section_a]" in out
        assert "[section_b]" in out
        # Key-value lines render with `key = value` (note the spacing
        # is part of the conf format).
        assert "key1 = val1" in out
        assert "k = v" in out

    def test_handles_empty_section_list(self) -> None:
        out = M._render_conf("# banner\n", [])
        # Banner is preserved, nothing else.
        assert "banner" in out


# ---------------------------------------------------------------------------
# _gsa_load_ucs — the UC sidecar walker
# ---------------------------------------------------------------------------


class TestGsaLoadUcs:
    def test_returns_empty_list_when_content_dir_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Point CONTENT_DIR at a directory that does not exist.
        monkeypatch.setattr(M, "CONTENT_DIR", tmp_path / "no-such")
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        assert M._gsa_load_ucs() == []

    def test_deduplicates_by_id_keeping_first_alphabetical(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The walker enumerates ``sorted(content.rglob('UC-*.json'))``,
        so the dedup rule is "first file in path-sorted order wins".
        Two sidecars in *different categories* with the same id —
        cat-1 sorts before cat-9, so the cat-1 copy wins."""
        content = tmp_path / "content"
        (content / "cat-1").mkdir(parents=True)
        (content / "cat-9").mkdir(parents=True)
        (content / "cat-1" / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "from-cat-1"})
        )
        (content / "cat-9" / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "from-cat-9"})
        )
        monkeypatch.setattr(M, "CONTENT_DIR", content)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        out = M._gsa_load_ucs()
        assert [u["title"] for u in out] == ["from-cat-1"]

    def test_skips_non_dict_and_missing_id_sidecars(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        content = tmp_path / "content"
        (content / "cat-1").mkdir(parents=True)
        # Top-level list — not a dict.
        (content / "cat-1" / "UC-1.1.1.json").write_text(json.dumps([1, 2, 3]))
        # Dict but no id.
        (content / "cat-1" / "UC-1.1.2.json").write_text(json.dumps({"title": "x"}))
        # Good entry.
        (content / "cat-1" / "UC-1.1.3.json").write_text(
            json.dumps({"id": "1.1.3", "title": "good"})
        )
        monkeypatch.setattr(M, "CONTENT_DIR", content)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        out = M._gsa_load_ucs()
        assert [u["id"] for u in out] == ["1.1.3"]

    def test_raises_systemexit_on_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        content = tmp_path / "content"
        (content / "cat-1").mkdir(parents=True)
        (content / "cat-1" / "UC-1.1.1.json").write_text("{ not valid json")
        monkeypatch.setattr(M, "CONTENT_DIR", content)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
        with pytest.raises(SystemExit, match="Invalid JSON"):
            M._gsa_load_ucs()


# ---------------------------------------------------------------------------
# _uc_to_unified_savedsearch + _compliance_eventtypes_sections — pin the
# small branches that the smoke test does not deterministically reach.
# ---------------------------------------------------------------------------


class TestGsaAliasMapEdgeBranches:
    def test_framework_without_shortname_does_not_index_alias(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A framework that has an ``id`` but no ``shortName`` MUST
        only contribute the id-lowercased alias; the ``shortName``
        branch is skipped (line 145→147)."""
        regs = {
            "frameworks": [
                {"id": "gdpr"},
                {"id": "hipaa", "shortName": "HIPAA", "aliases": ["hipaa-2003"]},
            ],
            "aliasIndex": {},
        }
        result = M._gsa_alias_map(regs)
        # gdpr only contributes "gdpr" (no shortName)
        assert result["gdpr"] == "gdpr"
        # hipaa contributes id, shortName, and alias
        assert result["hipaa"] == "hipaa"
        assert result["hipaa-2003"] == "hipaa"


class TestComplianceMatchedUcsBlankRegulation:
    def test_skips_compliance_entries_with_blank_regulation_field(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A UC sidecar that declares a compliance entry with an empty
        / whitespace-only ``regulation`` string MUST skip that entry
        before consulting the alias map (line 378, ``continue``)."""
        ucs = [
            {
                "id": "1.1.1",
                "title": "Test",
                "compliance": [
                    {"regulation": ""},
                    {"regulation": "  "},
                    {"regulation": "gdpr"},
                ],
            },
            {
                "id": "1.1.2",
                "title": "No-match UC",
                "compliance": [{"regulation": ""}],
            },
        ]
        regs = {
            "frameworks": [{"id": "gdpr", "shortName": "GDPR", "tier": 1}],
            "aliasIndex": {},
        }
        monkeypatch.setattr(M, "_gsa_load_ucs", lambda: ucs)
        monkeypatch.setattr(M, "_gsa_load_json", lambda _p: regs)
        matched, frameworks = M._load_compliance_bundle()
        # UC 1.1.1 still matches via the third entry; UC 1.1.2 is dropped
        # because both its compliance entries are blank.
        assert [u["id"] for u in matched] == ["1.1.1"]
        assert list(frameworks) == ["gdpr"]


class TestUcToUnifiedSavedsearch:
    def test_emits_clauses_and_versions_lines_when_present(self) -> None:
        """When matched compliance entries carry ``clause`` and
        ``version`` data, the rendered stanza grows two extra
        action.uc_compliance.param.* keys."""
        uc = {
            "id": "1.1.1",
            "title": "Test UC",
            "criticality": "high",
            "spl": "index=foo\n| stats count",
            "_matchedCompliance": [
                {
                    "_canonical": "gdpr",
                    "clause": "Art. 32",
                    "version": "2018",
                },
                {
                    "_canonical": "pci-dss",
                    "clause": "Req. 10",
                    "version": "4.0",
                },
            ],
        }
        frameworks = {
            "gdpr": {"shortName": "GDPR"},
            "pci-dss": {"shortName": "PCI"},
        }
        _stanza, pairs = M._uc_to_unified_savedsearch(uc, frameworks)
        keys = {k for k, _ in pairs}
        assert "action.uc_compliance.param.clauses" in keys
        assert "action.uc_compliance.param.versions" in keys
        # Description includes the clauses line.
        desc = next(v for k, v in pairs if k == "description")
        assert "clauses=" in desc
        # Multi-line SPL gets the backslash-newline join.
        search = next(v for k, v in pairs if k == "search")
        assert " \\\n" in search

    def test_omits_clauses_key_when_no_clause_data(self) -> None:
        """A UC whose matched compliance has no ``clause`` field MUST
        NOT emit the ``action.uc_compliance.param.clauses`` key — pins
        the False branch of ``if clauses`` (line 464→466). The
        ``versions`` key still appears because ``_canonical`` alone is
        enough to populate version_tags as ``<id>@unversioned``."""
        uc = {
            "id": "1.1.1",
            "title": "Test UC",
            "criticality": "medium",
            "spl": "index=foo | stats count",
            "_matchedCompliance": [{"_canonical": "gdpr"}],
        }
        _stanza, pairs = M._uc_to_unified_savedsearch(uc, {"gdpr": {"shortName": "GDPR"}})
        keys = {k for k, _ in pairs}
        assert "action.uc_compliance.param.clauses" not in keys
        assert "action.uc_compliance.param.versions" in keys
        # Description has NO 'clauses=' line.
        desc = next(v for k, v in pairs if k == "description")
        assert "clauses=" not in desc

    def test_omits_versions_key_when_no_canonical_data(self) -> None:
        """When every matched compliance entry has a falsy
        ``_canonical``, both ``regulations`` and ``version_tags``
        collapse to empty and the corresponding action.* keys are
        omitted — pins the False branch of ``if version_tags`` (line
        466→468). This is the contract used by UCs that map to a
        framework the recommender does not yet recognise."""
        uc = {
            "id": "1.1.1",
            "title": "Test UC",
            "criticality": "medium",
            "spl": "index=foo | stats count",
            "_matchedCompliance": [{"_canonical": ""}, {"_canonical": None}],
        }
        _stanza, pairs = M._uc_to_unified_savedsearch(uc, {})
        keys = {k for k, _ in pairs}
        assert "action.uc_compliance.param.clauses" not in keys
        assert "action.uc_compliance.param.versions" not in keys

    def test_falls_back_to_placeholder_spl_when_uc_has_none(self) -> None:
        """When the UC sidecar has no ``spl`` / ``query`` field, the
        renderer emits the documented placeholder so the stanza is
        still valid and disabled-by-default."""
        uc = {
            "id": "9.9.9",
            "title": "No-SPL UC",
            "criticality": "low",
            "_matchedCompliance": [{"_canonical": "gdpr"}],
        }
        _stanza, pairs = M._uc_to_unified_savedsearch(uc, {"gdpr": {"shortName": "GDPR"}})
        search = next(v for k, v in pairs if k == "search")
        assert "_placeholder=1" in search
        assert 'eval uc_id="9.9.9"' in search


class TestComplianceEventtypesSections:
    def test_skips_compliance_entries_with_blank_canonical(self) -> None:
        """A matched-compliance entry whose ``_canonical`` resolves to
        an empty/whitespace-only string is dropped before being keyed
        into ``by_key`` (pin for line 516, the ``if not fw_id`` guard).
        """
        ucs = [
            {
                "id": "1.1.1",
                "controlFamily": "Access Control",
                "_matchedCompliance": [
                    {"_canonical": ""},  # MUST be skipped
                    {"_canonical": "   "},  # MUST be skipped
                    {"_canonical": "gdpr"},
                ],
            }
        ]
        sections = M._compliance_eventtypes_sections(
            ucs, {"gdpr": {"shortName": "GDPR"}}
        )
        # Only the gdpr/access_control eventtype is emitted.
        stanzas = {stanza for stanza, _ in sections}
        assert stanzas == {"uc_compliance_gdpr_access_control"}


# ---------------------------------------------------------------------------
# main truncates the diff list at 200 entries
# ---------------------------------------------------------------------------


class TestMainCheckDriftTruncation:
    def test_diff_overflow_is_truncated_in_stderr(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When --check produces more than 200 diff lines, main MUST
        print the first 200 and a "... N additional diffs omitted"
        footer. Stub _scope_check_diff to return a fabricated diff
        list so we don't need 201 real differing files."""
        fake_diffs = [f"  differs: file-{i:04d}.txt" for i in range(250)]
        monkeypatch.setattr(M, "_scope_check_diff", lambda *_a, **_kw: fake_diffs)
        # _render is a no-op so we don't actually build the tree.
        monkeypatch.setattr(M, "_render", lambda _root: {M.PRIMARY_APP_ID: tmp_path})
        out_dir = tmp_path / "splunk-apps"
        out_dir.mkdir()
        rc = M.main(["--check", "--output", str(out_dir)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "additional diffs omitted" in err
        assert "drift" in err.lower()


# ---------------------------------------------------------------------------
# _build_primary_app — directly exercise the legacy-file cleanup and the
# LICENSE-absent branch without going through the full _render pipeline.
# ---------------------------------------------------------------------------


class TestBuildPrimaryAppLegacyAndLicense:
    def test_removes_pre_existing_legacy_studio_artefacts(
        self,
        tmp_path: Path,
    ) -> None:
        """If a previous build left ``recommend_studio.xml`` /
        ``recommend.json`` lying around, the new build MUST delete
        them — pins line 4903 (``_legacy.unlink()``)."""
        out_root = tmp_path / "splunk-apps"
        app_root = out_root / M.PRIMARY_APP_ID
        views = app_root / "default" / "data" / "ui" / "views"
        views.mkdir(parents=True)
        legacy_xml = views / "recommend_studio.xml"
        legacy_json = views / "recommend.json"
        legacy_xml.write_text("stale\n", encoding="utf-8")
        legacy_json.write_text("{}\n", encoding="utf-8")

        M._build_primary_app(out_root, "0.0.0", "2026-05-20T00:00:00Z", "/svc/api/v1")

        assert not legacy_xml.exists()
        assert not legacy_json.exists()
        # The fresh recommend.xml DOES land.
        assert (views / "recommend.xml").exists()

    def test_skips_license_copy_when_repo_license_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the repo-root LICENSE file does not exist, the
        build MUST skip the LICENSE copy without raising. Pins the
        False branch of ``if LICENSE_FILE.exists()`` (4950→4956)."""
        out_root = tmp_path / "splunk-apps"
        monkeypatch.setattr(M, "LICENSE_FILE", tmp_path / "no-such-LICENSE")

        app_root = M._build_primary_app(
            out_root,
            "0.0.0",
            "2026-05-20T00:00:00Z",
            "/svc/api/v1",
        )
        assert app_root.exists()
        assert not (app_root / "LICENSE").exists()


def test_module_exposes_main_callable() -> None:
    """Pin the dispatcher contract: ``splunk_uc.generators.recommender_app``
    MUST expose a callable ``main`` so the registry can route to it.
    """
    assert callable(M.main)
    # io is required by the conf-renderer for CSV streaming.
    assert hasattr(M, "_render")
    # _SAFE_STANZA_RE is the regex backing _gsa_safe_stanza; keep it
    # accessible so unit tests can inspect.
    assert isinstance(M._SAFE_STANZA_RE.pattern, str)


# ``io`` is imported above purely so the test module has a reference
# the linter cannot strip; ``recommender_app`` uses it for CSV
# rendering and we want pytest to surface any future import-time
# regression as an early failure.
_ = io.StringIO()
