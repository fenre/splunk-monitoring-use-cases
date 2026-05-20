"""Unit tests for ``splunk_uc.generators.phase3_2_cross_cutting``.

P16 wave X: lifts ``src/splunk_uc/generators/phase3_2_cross_cutting.py``
from 12.1% to ~99% combined coverage. Pins every documented contract
of the Phase 3.2 cross-cutting compliance generator that idempotently
merges clause-level regulatory tags into existing non-cat-22 UC sidecars
under ``content/cat-NN-<slug>/UC-<id>.json``.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.generators import phase3_2_cross_cutting as p32

MakeSidecar = Callable[[str, str, dict[str, Any]], pathlib.Path]
MakeManifest = Callable[[Any], pathlib.Path]


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic repo with ``content/cat-NN-<slug>/`` and a manifest dir."""
    content = tmp_path / "content"
    content.mkdir()
    (content / "cat-01-server-compute").mkdir()
    (content / "cat-09-identity-access-management").mkdir()
    (content / "cat-22-regulatory-compliance").mkdir()
    (tmp_path / "data" / "per-regulation").mkdir(parents=True)
    monkeypatch.setattr(p32, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(p32, "CONTENT_DIR", content)
    monkeypatch.setattr(
        p32, "MANIFEST_PATH", tmp_path / "data" / "per-regulation" / "phase3.2.json"
    )
    return tmp_path


@pytest.fixture
def make_sidecar(fake_repo: pathlib.Path) -> MakeSidecar:
    def _make(category: str, uc_id: str, payload: dict[str, Any]) -> pathlib.Path:
        cat_dir = p32.CONTENT_DIR / category
        cat_dir.mkdir(exist_ok=True)
        path = cat_dir / f"UC-{uc_id}.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    return _make


@pytest.fixture
def make_manifest(fake_repo: pathlib.Path) -> MakeManifest:
    def _make(manifest: Any) -> pathlib.Path:
        p32.MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return p32.MANIFEST_PATH

    return _make


@pytest.fixture
def stub_synth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the migration synth helpers with deterministic stubs."""
    monkeypatch.setattr(
        p32,
        "synthesise_control_objective",
        lambda sidecar, entry, prov: f"OBJ for {entry.get('regulation')} {entry.get('clause')}",
    )
    monkeypatch.setattr(
        p32,
        "synthesise_evidence_artifact",
        lambda sidecar, entry: f"EVI for {entry.get('regulation')} {entry.get('clause')}",
    )


class TestReadJson:
    def test_reads_valid(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "x.json"
        path.write_text(json.dumps({"a": 1}), encoding="utf-8")
        assert p32._read_json(path) == {"a": 1}

    def test_raises_on_missing(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(FileNotFoundError):
            p32._read_json(tmp_path / "missing.json")

    def test_raises_on_invalid(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{ bad", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            p32._read_json(path)


class TestEncodeSidecar:
    def test_uses_canonical_order_and_trailing_newline(self) -> None:
        out = p32._encode_sidecar({"app": "X", "id": "1.1.1"})
        # ``id`` comes before ``app`` per SIDECAR_FIELD_ORDER.
        assert out.index('"id"') < out.index('"app"')
        assert out.endswith("\n")
        assert "  " in out


class TestCanonicalSidecar:
    def test_known_keys_canonical_order(self) -> None:
        out = p32._canonical_sidecar({"app": "X", "id": "1.1.1", "title": "t"})
        keys = list(out.keys())
        assert keys.index("id") < keys.index("title")
        assert keys.index("title") < keys.index("app")

    def test_unknown_keys_appended(self) -> None:
        out = p32._canonical_sidecar({"id": "1.1.1", "zzz_unknown": 1})
        keys = list(out.keys())
        assert keys[0] == "id"
        assert keys[-1] == "zzz_unknown"

    def test_returns_new_dict(self) -> None:
        sidecar = {"id": "1.1.1"}
        out = p32._canonical_sidecar(sidecar)
        assert out is not sidecar


class TestCanonicalEntry:
    def test_orders_entry_fields(self) -> None:
        entry = {
            "assurance_rationale": "x",
            "regulation": "ISO",
            "version": "2013",
            "clause": "A.5.1",
            "mode": "primary",
            "assurance": "high",
        }
        out = p32._canonical_entry(entry)
        assert list(out.keys()) == [
            "regulation",
            "version",
            "clause",
            "mode",
            "assurance",
            "assurance_rationale",
        ]

    def test_drops_extra_keys(self) -> None:
        # The function only emits keys in _ENTRY_FIELD_ORDER. Unknown
        # keys are silently dropped — the schema validator upstream
        # catches them.
        entry = {"regulation": "ISO", "version": "1", "clause": "x", "extra": "junk"}
        out = p32._canonical_entry(entry)
        assert "extra" not in out


class TestLoadManifest:
    def test_loads_valid(self, fake_repo: pathlib.Path, make_manifest: MakeManifest) -> None:
        make_manifest({"ucs": [{"uc_id": "1.1.1", "title": "t", "mappings": []}]})
        loaded = p32._load_manifest()
        assert loaded["ucs"][0]["uc_id"] == "1.1.1"

    def test_raises_when_not_dict(
        self,
        fake_repo: pathlib.Path,
        make_manifest: MakeManifest,
    ) -> None:
        make_manifest(["not a dict"])
        with pytest.raises(SystemExit) as excinfo:
            p32._load_manifest()
        assert "object containing a 'ucs' array" in str(excinfo.value)

    def test_raises_when_ucs_missing(
        self,
        fake_repo: pathlib.Path,
        make_manifest: MakeManifest,
    ) -> None:
        make_manifest({"other": []})
        with pytest.raises(SystemExit):
            p32._load_manifest()

    def test_raises_when_ucs_not_list(
        self,
        fake_repo: pathlib.Path,
        make_manifest: MakeManifest,
    ) -> None:
        make_manifest({"ucs": "not a list"})
        with pytest.raises(SystemExit):
            p32._load_manifest()

    def test_raises_when_ucs_empty(
        self,
        fake_repo: pathlib.Path,
        make_manifest: MakeManifest,
    ) -> None:
        make_manifest({"ucs": []})
        with pytest.raises(SystemExit) as excinfo:
            p32._load_manifest()
        assert "'ucs' array is empty" in str(excinfo.value)


class TestCategoryPadded:
    def test_single_digit(self) -> None:
        assert p32._category_padded("1.1.1") == "01"

    def test_two_digit(self) -> None:
        assert p32._category_padded("22.1.1") == "22"

    def test_uses_first_segment(self) -> None:
        assert p32._category_padded("9.1.1") == "09"


class TestCategoryDirIndex:
    def test_indexes_matching_dirs(self, fake_repo: pathlib.Path) -> None:
        index = p32._category_dir_index()
        assert "01" in index
        assert "09" in index
        assert "22" in index
        assert index["01"].name == "cat-01-server-compute"

    def test_skips_non_directories(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Drop a file named cat-99-fake.txt to verify it's skipped.
        (p32.CONTENT_DIR / "cat-99-fake.txt").write_text("not a dir", encoding="utf-8")
        # And a directory with wrong name shape.
        (p32.CONTENT_DIR / "cat-XX-not-numeric").mkdir()
        index = p32._category_dir_index()
        assert "99" not in index
        assert "XX" not in index


class TestSidecarPath:
    def test_resolves_when_category_exists(self, fake_repo: pathlib.Path) -> None:
        cat_index = p32._category_dir_index()
        path = p32._sidecar_path("1.1.1", cat_index)
        assert path is not None
        assert path.name == "UC-1.1.1.json"
        assert path.parent.name == "cat-01-server-compute"

    def test_returns_none_when_category_missing(self, fake_repo: pathlib.Path) -> None:
        cat_index = p32._category_dir_index()
        assert p32._sidecar_path("99.1.1", cat_index) is None


class TestBuildSSotTitleIndex:
    def test_indexes_non_cat22(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A"},
        )
        make_sidecar(
            "cat-22-regulatory-compliance",
            "22.1.1",
            {"id": "22.1.1", "title": "UC Reg"},
        )
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        assert "1.1.1" in ssot
        assert ssot["1.1.1"][0] == "UC A"
        # cat-22 is excluded.
        assert "22.1.1" not in ssot

    def test_skips_invalid_json(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        (p32.CONTENT_DIR / "cat-01-server-compute" / "UC-broken.json").write_text(
            "{ broken", encoding="utf-8"
        )
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        # Broken sidecar is silently skipped.
        assert "broken" not in ssot

    def test_skips_non_dict_top_level(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        (p32.CONTENT_DIR / "cat-01-server-compute" / "UC-list.json").write_text(
            json.dumps(["array"]), encoding="utf-8"
        )
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        # Confirms no exception; list payload simply skipped.
        assert ssot == {}

    def test_falls_back_to_stem_when_id_missing(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        (p32.CONTENT_DIR / "cat-01-server-compute" / "UC-1.1.99.json").write_text(
            json.dumps({"title": "no id"}), encoding="utf-8"
        )
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        assert "1.1.99" in ssot
        assert ssot["1.1.99"][0] == "no id"

    def test_first_match_wins(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # If two sidecars share an id (shouldn't happen but defensively
        # handled by setdefault), the alphabetically-first wins.
        cat1 = p32.CONTENT_DIR / "cat-01-server-compute"
        (cat1 / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "First"}), encoding="utf-8"
        )
        # Same id, different category folder.
        (p32.CONTENT_DIR / "cat-09-identity-access-management" / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "Second"}), encoding="utf-8"
        )
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        # cat-01 is processed first (sorted glob) so "First" wins.
        assert ssot["1.1.1"][0] == "First"


class TestValidateTargets:
    def test_passes_when_manifest_matches_ssot(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
    ) -> None:
        make_sidecar("cat-01-server-compute", "1.1.1", {"id": "1.1.1", "title": "UC A"})
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        manifest = {"ucs": [{"uc_id": "1.1.1", "title": "UC A", "mappings": []}]}
        p32._validate_targets(manifest, ssot)  # no raise

    def test_fails_on_cat22_uc(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = {"ucs": [{"uc_id": "22.1.1", "title": "X", "mappings": []}]}
        with pytest.raises(SystemExit) as excinfo:
            p32._validate_targets(manifest, {})
        assert excinfo.value.code == 2
        err = capsys.readouterr().err
        assert "cat-22 UCs are owned by Phase 1.3/2.2/2.3/3.1 generators" in err

    def test_fails_on_missing_uc_id(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = {"ucs": [{"title": "X", "mappings": []}]}
        with pytest.raises(SystemExit):
            p32._validate_targets(manifest, {})
        assert "missing uc_id/title" in capsys.readouterr().err

    def test_fails_on_missing_title(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = {"ucs": [{"uc_id": "1.1.1", "mappings": []}]}
        with pytest.raises(SystemExit):
            p32._validate_targets(manifest, {})
        assert "missing uc_id/title" in capsys.readouterr().err

    def test_fails_when_uc_not_in_ssot(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = {"ucs": [{"uc_id": "1.1.99", "title": "Ghost", "mappings": []}]}
        with pytest.raises(SystemExit):
            p32._validate_targets(manifest, {})
        assert "no matching UC sidecar found" in capsys.readouterr().err

    def test_fails_on_title_mismatch(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_sidecar("cat-01-server-compute", "1.1.1", {"id": "1.1.1", "title": "Real"})
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        manifest = {"ucs": [{"uc_id": "1.1.1", "title": "Wrong", "mappings": []}]}
        with pytest.raises(SystemExit):
            p32._validate_targets(manifest, ssot)
        err = capsys.readouterr().err
        assert "differs from SSOT title" in err

    def test_accumulates_multiple_errors(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = {
            "ucs": [
                {"uc_id": "22.1.1", "title": "x", "mappings": []},
                {"uc_id": "1.1.99", "title": "y", "mappings": []},
            ]
        }
        with pytest.raises(SystemExit):
            p32._validate_targets(manifest, {})
        err = capsys.readouterr().err
        assert "cat-22 UCs" in err
        assert "no matching UC sidecar" in err


class TestNormaliseRegulation:
    def test_strips_and_lowercases(self) -> None:
        assert p32._normalise_regulation("  ISO 27001  ") == "iso 27001"

    def test_none_treated_as_empty(self) -> None:
        assert p32._normalise_regulation(None) == ""

    def test_empty(self) -> None:
        assert p32._normalise_regulation("") == ""


class TestEntryKey:
    def test_normalised_triple(self) -> None:
        entry = {"regulation": "ISO 27001", "version": "2013", "clause": "A.5.1"}
        assert p32._entry_key(entry) == ("iso 27001", "2013", "A.5.1")

    def test_missing_fields(self) -> None:
        assert p32._entry_key({}) == ("", "", "")

    def test_version_int_coerced(self) -> None:
        assert p32._entry_key({"regulation": "x", "version": 2013, "clause": "y"}) == (
            "x",
            "2013",
            "y",
        )


class TestBuildNewEntry:
    def test_projects_canonical_keys_in_order(self) -> None:
        mapping = {
            "uc_id": "1.1.1",
            "title": "x",
            "regulation": "ISO 27001",
            "version": "2013",
            "clause": "A.5.1",
            "clauseUrl": "https://example.com",
            "mode": "primary",
            "assurance": "high",
            "assurance_rationale": "x",
        }
        entry = p32._build_new_entry(mapping)
        assert list(entry.keys()) == [
            "regulation",
            "version",
            "clause",
            "clauseUrl",
            "mode",
            "assurance",
            "assurance_rationale",
        ]

    def test_drops_unknown_keys(self) -> None:
        mapping = {
            "regulation": "ISO",
            "version": "1",
            "clause": "x",
            "junk": "drop me",
        }
        entry = p32._build_new_entry(mapping)
        assert "junk" not in entry

    def test_partial_mapping(self) -> None:
        mapping = {"regulation": "ISO"}
        entry = p32._build_new_entry(mapping)
        assert entry == {"regulation": "ISO"}


class TestApplyMappings:
    def test_appends_new_entry_and_drafts_objective_evidence(
        self,
        stub_synth: None,
    ) -> None:
        sidecar: dict[str, Any] = {"id": "1.1.1", "compliance": []}
        mappings = [
            {
                "regulation": "ISO 27001",
                "version": "2013",
                "clause": "A.5.1",
                "mode": "primary",
                "assurance": "high",
                "assurance_rationale": "x",
            }
        ]
        assert p32._apply_mappings(sidecar, mappings) is True
        compliance = sidecar["compliance"]
        assert len(compliance) == 1
        e = compliance[0]
        assert e["controlObjective"] == "OBJ for ISO 27001 A.5.1"
        assert e["evidenceArtifact"] == "EVI for ISO 27001 A.5.1"
        # And the entry's keys are canonically ordered.
        assert next(iter(e.keys())) == "regulation"

    def test_idempotent_on_duplicate(self, stub_synth: None) -> None:
        sidecar: dict[str, Any] = {
            "id": "1.1.1",
            "compliance": [
                {
                    "regulation": "ISO 27001",
                    "version": "2013",
                    "clause": "A.5.1",
                    "mode": "primary",
                    "assurance": "high",
                    "assurance_rationale": "existing",
                }
            ],
        }
        mappings = [
            {
                "regulation": "ISO 27001",
                "version": "2013",
                "clause": "A.5.1",
                "mode": "primary",
                "assurance": "high",
                "assurance_rationale": "would-overwrite",
            }
        ]
        assert p32._apply_mappings(sidecar, mappings) is False
        # SME-curated rationale is preserved.
        assert sidecar["compliance"][0]["assurance_rationale"] == "existing"

    def test_respects_provided_control_objective_and_evidence(
        self,
        stub_synth: None,
    ) -> None:
        sidecar: dict[str, Any] = {"id": "1.1.1", "compliance": []}
        mappings = [
            {
                "regulation": "ISO 27001",
                "version": "2013",
                "clause": "A.5.1",
                "mode": "primary",
                "assurance": "high",
                "assurance_rationale": "x",
                "controlObjective": "Pre-supplied OBJ",
                "evidenceArtifact": "Pre-supplied EVI",
            }
        ]
        p32._apply_mappings(sidecar, mappings)
        e = sidecar["compliance"][0]
        # Manifest-provided values are NOT overwritten.
        assert e["controlObjective"] == "Pre-supplied OBJ"
        assert e["evidenceArtifact"] == "Pre-supplied EVI"

    def test_existing_compliance_array_preserved_when_no_changes(
        self,
        stub_synth: None,
    ) -> None:
        # When ``touched=False``, the sidecar.compliance is NOT
        # rewritten (its prior key ordering is preserved).
        original = [
            {
                "evidenceArtifact": "x",  # non-canonical order
                "regulation": "ISO 27001",
                "version": "2013",
                "clause": "A.5.1",
                "mode": "primary",
                "assurance": "high",
                "assurance_rationale": "x",
            }
        ]
        sidecar: dict[str, Any] = {"id": "1.1.1", "compliance": original}
        # Empty mappings → touched=False → no rewrite.
        assert p32._apply_mappings(sidecar, []) is False
        # The original entry is still there in its non-canonical order.
        assert next(iter(sidecar["compliance"][0].keys())) == "evidenceArtifact"


class TestUcSortKey:
    def test_returns_int_list(self) -> None:
        assert p32._uc_sort_key("22.1.1") == [22, 1, 1]

    def test_multi_digit_segments(self) -> None:
        assert p32._uc_sort_key("22.10.1") == [22, 10, 1]
        assert p32._uc_sort_key("22.2.1") == [22, 2, 1]
        # And numerical sort is correct.
        assert p32._uc_sort_key("22.2.1") < p32._uc_sort_key("22.10.1")


class TestProcess:
    def _make_minimal_target(
        self,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO 27001",
                                "version": "2013",
                                "clause": "A.5.1",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )

    def test_write_mode_updates_sidecar(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._make_minimal_target(make_sidecar, make_manifest)
        rc = p32._process(check_only=False)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Phase 3.2 cross-cutting: updated 1 sidecar(s)" in out

    def test_check_mode_drift_returns_1(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._make_minimal_target(make_sidecar, make_manifest)
        rc = p32._process(check_only=True)
        assert rc == 1
        err = capsys.readouterr().err
        assert "Phase 3.2 cross-cutting drift detected" in err
        assert "would-update:" in err

    def test_check_mode_drift_skips_unresolved_uc_id(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pin the False arm of ``if resolved is not None:`` (branch
        ``483→481``) inside the check-mode drift reporter.

        In production every ``uc_id`` in ``updated`` resolves to a
        sidecar path because the same ``cat_index`` is used for
        discovery and update. To force the False arm we monkey-patch
        ``_sidecar_path`` to return ``None`` so the loop skips the
        ``would-update: ...`` print and falls through to the next
        iteration. The drift header is still emitted and ``rc == 1``,
        proving the loop continues without crashing on missing path
        resolution."""
        self._make_minimal_target(make_sidecar, make_manifest)
        original_sidecar_path = p32._sidecar_path
        call_counter = {"count": 0}

        def _intermittent_sidecar_path(
            uc_id: str, cat_index: dict[str, pathlib.Path]
        ) -> pathlib.Path | None:
            call_counter["count"] += 1
            if call_counter["count"] > 1:
                return None
            return original_sidecar_path(uc_id, cat_index)

        monkeypatch.setattr(p32, "_sidecar_path", _intermittent_sidecar_path)
        rc = p32._process(check_only=True)
        assert rc == 1
        captured = capsys.readouterr()
        assert "Phase 3.2 cross-cutting drift detected" in captured.err
        assert "would-update:" not in captured.err

    def test_check_mode_clean_returns_0(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Pre-populate the sidecar with the mapping already applied
        # in canonical form.
        existing_entry = {
            "regulation": "ISO 27001",
            "version": "2013",
            "clause": "A.5.1",
            "mode": "primary",
            "assurance": "high",
            "assurance_rationale": "x",
        }
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": [existing_entry]},
        )
        # And canonical-encode that file so byte equality holds.
        path = p32.CONTENT_DIR / "cat-01-server-compute" / "UC-1.1.1.json"
        canonical = p32._canonical_sidecar(
            {"id": "1.1.1", "title": "UC A", "compliance": [existing_entry]}
        )
        path.write_text(
            json.dumps(canonical, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [existing_entry],
                    }
                ]
            }
        )
        rc = p32._process(check_only=True)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Phase 3.2 cross-cutting: OK" in out
        assert "1 UCs" in out
        assert "1 mappings" in out
        assert "no drift" in out

    def test_uc_with_no_mappings_returns_2(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest({"ucs": [{"uc_id": "1.1.1", "title": "UC A", "mappings": []}]})
        rc = p32._process(check_only=False)
        assert rc == 2
        assert "has no mappings" in capsys.readouterr().err

    def test_uc_with_non_list_mappings_returns_2(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest({"ucs": [{"uc_id": "1.1.1", "title": "UC A", "mappings": "not a list"}]})
        rc = p32._process(check_only=False)
        assert rc == 2

    def test_missing_sidecar_returns_2(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Create a sidecar in the SSOT index so _validate_targets passes,
        # then delete it before _process tries to read it.
        path = make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO",
                                "version": "2013",
                                "clause": "A.5.1",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )
        # Pre-validate target succeeded; now remove path so _process's
        # second exists() check fails.
        original_exists = pathlib.Path.exists

        def custom_exists(self: pathlib.Path) -> bool:
            if self == path:
                return False
            return original_exists(self)

        monkeypatch.setattr(pathlib.Path, "exists", custom_exists)
        rc = p32._process(check_only=False)
        assert rc == 2
        assert "SSOT sidecar missing for 1.1.1" in capsys.readouterr().err

    def test_sidecar_not_object_returns_2(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Write a target sidecar that loads as a list rather than dict.
        make_sidecar("cat-01-server-compute", "1.1.1", {"id": "1.1.1", "title": "UC A"})
        # Pre-validate will populate the SSOT index normally, then
        # overwrite the file with a non-dict payload to trip the
        # ``not isinstance(sidecar, dict)`` check in _process.
        path = p32.CONTENT_DIR / "cat-01-server-compute" / "UC-1.1.1.json"
        # _validate_targets reads via _build_ssot_title_index which uses
        # the dict shape; then _process reads it again, and the second
        # read can be made to return a list. The simplest path is to
        # overwrite the file between the two reads via a custom hook.
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO",
                                "version": "2013",
                                "clause": "A.5.1",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )
        # Patch _read_json to return a list once we hit the target path
        # during _process (not during validation).
        original_read = p32._read_json
        seen: dict[str, int] = {"count": 0}

        def fake_read(p: pathlib.Path) -> Any:
            if p == path:
                seen["count"] += 1
                # First read (in validate) → real dict; second (in
                # process loop) → list.
                if seen["count"] >= 2:
                    return ["not", "a", "dict"]
            return original_read(p)

        # patch via monkeypatch
        import unittest.mock as mock

        with mock.patch.object(p32, "_read_json", side_effect=fake_read):
            rc = p32._process(check_only=False)
        assert rc == 2
        assert "sidecar is not a JSON object" in capsys.readouterr().err

    def test_id_mismatch_returns_2(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Write a target sidecar whose internal id differs from filename.
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "9.9.9", "title": "UC A", "compliance": []},
        )
        # _validate_targets walks `_build_ssot_title_index` which keys
        # by the file's internal `id`, so it'd see `id=9.9.9`, not the
        # filename `1.1.1`. We need to make the manifest reference
        # `9.9.9` (so validation passes) but file location is
        # cat-01/UC-1.1.1.json — which means _sidecar_path resolves
        # under cat-09 (the padded "09" of "9.9.9"), pointing at a
        # non-existent file.
        # Simpler: just trip the id-mismatch by having two files with
        # the same UC id but different filenames. Skip this complex
        # path; assert by patching _sidecar_path to return the wrong
        # path.
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "9.9.9",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO",
                                "version": "2013",
                                "clause": "A.5.1",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )
        # Add cat-09 dir so _validate_targets finds 9.9.9 with title
        # "UC A". But the file is in cat-01! That requires _sidecar_path
        # to find cat-09 with a file named UC-9.9.9.json.
        # The cleanest construct: put a UC-9.9.9.json file under
        # cat-09 with the WRONG `id` set inside.
        (p32.CONTENT_DIR / "cat-09-identity-access-management" / "UC-9.9.9.json").write_text(
            json.dumps({"id": "9.9.8", "title": "UC A"}, indent=2),
            encoding="utf-8",
        )
        # But that breaks the SSOT title index (id=9.9.8 stored, not 9.9.9).
        # Make validate_targets pass: patch _build_ssot_title_index to
        # return the right shape, then _process will hit the id-mismatch.
        cat_index = p32._category_dir_index()
        ssot = p32._build_ssot_title_index(cat_index)
        # 9.9.9 maps to title "UC A" in ssot via the index's get-id fallback
        # if there's no `id` key — but with `id=9.9.8`, ssot["9.9.8"] = ...
        # Let's craft the situation manually.
        ssot["9.9.9"] = (
            "UC A",
            p32.CONTENT_DIR / "cat-09-identity-access-management" / "UC-9.9.9.json",
        )
        # Bypass real _build_ssot_title_index in _process via monkeypatch.
        import unittest.mock as mock

        with mock.patch.object(p32, "_build_ssot_title_index", return_value=ssot):
            rc = p32._process(check_only=False)
        assert rc == 2
        assert "does not match manifest uc_id" in capsys.readouterr().err

    def test_no_drift_when_apply_returns_false(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Sidecar already has the entry; _apply_mappings returns False.
        existing_entry = {
            "regulation": "ISO",
            "version": "1",
            "clause": "x",
            "mode": "primary",
            "assurance": "high",
            "assurance_rationale": "x",
        }
        canonical = p32._canonical_sidecar(
            {
                "id": "1.1.1",
                "title": "UC A",
                "compliance": [existing_entry],
            }
        )
        path = p32.CONTENT_DIR / "cat-01-server-compute" / "UC-1.1.1.json"
        path.write_text(
            json.dumps(canonical, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [existing_entry],
                    }
                ]
            }
        )
        rc = p32._process(check_only=False)
        assert rc == 0


class TestMainCli:
    def test_default_runs(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO",
                                "version": "1",
                                "clause": "x",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )
        rc = p32.main([])
        assert rc == 0

    def test_check_flag(
        self,
        fake_repo: pathlib.Path,
        make_sidecar: MakeSidecar,
        make_manifest: MakeManifest,
        stub_synth: None,
    ) -> None:
        make_sidecar(
            "cat-01-server-compute",
            "1.1.1",
            {"id": "1.1.1", "title": "UC A", "compliance": []},
        )
        make_manifest(
            {
                "ucs": [
                    {
                        "uc_id": "1.1.1",
                        "title": "UC A",
                        "mappings": [
                            {
                                "regulation": "ISO",
                                "version": "1",
                                "clause": "x",
                                "mode": "primary",
                                "assurance": "high",
                                "assurance_rationale": "x",
                            }
                        ],
                    }
                ]
            }
        )
        rc = p32.main(["--check"])
        assert rc == 1

    def test_help_lists_check(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as excinfo:
            p32.main(["--help"])
        assert excinfo.value.code == 0
        assert "--check" in capsys.readouterr().out


def test_module_constants_resolve_under_real_repo() -> None:
    assert p32.REPO_ROOT.is_dir()
    assert (p32.REPO_ROOT / "content").is_dir()
    assert p32.MANIFEST_PATH.name == "phase3.2.json"


def test_sidecar_field_order_shape() -> None:
    head = (
        "$schema",
        "id",
        "title",
        "criticality",
        "difficulty",
        "monitoringType",
    )
    assert p32.SIDECAR_FIELD_ORDER[: len(head)] == head
    assert "compliance" in p32.SIDECAR_FIELD_ORDER


def test_entry_field_order_subset_of_allowed() -> None:
    for key in p32._ENTRY_FIELD_ORDER:
        assert key in p32._ALLOWED_ENTRY_KEYS


def test_cat_dir_re_matches_canonical_shape() -> None:
    assert p32._CAT_DIR_RE.match("cat-01-server-compute") is not None
    assert p32._CAT_DIR_RE.match("cat-22-regulatory-compliance") is not None
    assert p32._CAT_DIR_RE.match("cat-XX-invalid") is None
    assert p32._CAT_DIR_RE.match("not-a-cat-dir") is None
