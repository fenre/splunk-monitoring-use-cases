"""Unit tests for ``splunk_uc.generators.equipment_tags``.

P16 wave V: lifts ``src/splunk_uc/generators/equipment_tags.py``
from 15.6% to ~100% combined coverage. Pins every documented
contract of the Phase 5.5 structured equipment-tagging generator:
``_iter_sidecar_paths``, ``_read_sidecar``, ``_compute_tags``,
``_reorder_sidecar``, ``_apply_tags``, ``_serialise``,
``_process_sidecars``, ``_print_report``, and the full ``main()``
CLI matrix.

Equipment tag computation depends on the ``equipment_lib`` patterns
loaded from ``tools/build/enrichment.py``. To stay hermetic, tests
either:
  * monkey-patch ``_CONTENT_UC_ROOT`` and ``_REPO_ROOT`` to a
    fixture tree, OR
  * monkey-patch ``compile_patterns`` / ``load_equipment`` /
    ``match_equipment`` at the module level.
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

import pytest

from splunk_uc.generators import equipment_tags as et


def _compile_patterns() -> list[tuple[str, str, str | None]]:
    """Indirection to ``et.compile_patterns()``.

    ``equipment_tags`` re-exports ``compile_patterns`` from
    ``equipment_lib`` via a top-level ``from ... import`` statement
    but does not declare an ``__all__``, so mypy under ``--strict``
    rejects ``et.compile_patterns`` as an undeclared export.
    Resolving the attribute lazily on every call also lets the
    ``fake_patterns`` fixture's ``monkeypatch.setattr(et, ...)`` take
    effect — the binding has to be late-resolved against the module
    attribute, not snapshot at import time.
    """
    return et.compile_patterns()  # type: ignore[attr-defined,no-any-return]


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic content tree with a couple of UC sidecars."""
    content = tmp_path / "content"
    cat1 = content / "cat-01-fake"
    cat1.mkdir(parents=True)
    cat2 = content / "cat-22-compliance"
    cat2.mkdir(parents=True)

    sidecar_a = {
        "id": "1.1.1",
        "title": "Test UC A",
        "app": "Splunk Add-on for AWS",
        "spl": "search index=aws | stats count",
        "dataSources": "AWS CloudTrail logs",
        "implementation": "Use AWS CloudTrail.",
        "description": "Detect anomalies in AWS",
    }
    sidecar_b = {
        "id": "22.1.1",
        "title": "Test UC B",
        "app": "Microsoft Azure",
        "spl": "search index=azure",
        "dataSources": "Azure logs",
        "implementation": "Use Azure connector.",
        "description": "Detect Azure issues",
    }
    (cat1 / "UC-1.1.1.json").write_text(
        json.dumps(sidecar_a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (cat2 / "UC-22.1.1.json").write_text(
        json.dumps(sidecar_b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    monkeypatch.setattr(et, "_CONTENT_UC_ROOT", content)
    monkeypatch.setattr(et, "_REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def fake_patterns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace equipment_lib calls with deterministic fakes."""

    def fake_compile_patterns(equipment: object = None) -> list[tuple[str, str, str | None]]:
        return [
            ("aws", "aws", None),
            ("cloudtrail", "aws", "cloudtrail"),
            ("azure", "azure", None),
            ("microsoft azure", "azure", None),
        ]

    def fake_load_equipment() -> list[dict[str, object]]:
        return []

    def fake_match_equipment(
        text: str,
        patterns: list[tuple[str, str, str | None]],
        *,
        min_pattern_len: int = 1,
    ) -> tuple[set[str], set[str]]:
        text_l = text.lower()
        eq_ids: set[str] = set()
        compounds: set[str] = set()
        for pat, eid, mid in patterns:
            if len(pat) < min_pattern_len:
                continue
            if pat in text_l:
                eq_ids.add(eid)
                if mid:
                    compounds.add(f"{eid}_{mid}")
        return eq_ids, compounds

    monkeypatch.setattr(et, "compile_patterns", fake_compile_patterns)
    monkeypatch.setattr(et, "load_equipment", fake_load_equipment)
    monkeypatch.setattr(et, "match_equipment", fake_match_equipment)


class TestIterSidecarPaths:
    def test_yields_sorted_uc_files(self, fake_repo: pathlib.Path) -> None:
        paths = list(et._iter_sidecar_paths())
        assert len(paths) == 2
        # rglob produces them in arbitrary order; the impl sorts them.
        assert paths == sorted(paths)
        assert all(p.suffix == ".json" for p in paths)
        assert all(p.name.startswith("UC-") for p in paths)

    def test_returns_empty_when_no_files(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        empty = tmp_path / "empty-content"
        empty.mkdir()
        monkeypatch.setattr(et, "_CONTENT_UC_ROOT", empty)
        assert list(et._iter_sidecar_paths()) == []


class TestReadSidecar:
    def test_reads_valid_sidecar(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        path = fake_repo / "content" / "cat-01-fake" / "UC-1.1.1.json"
        data = et._read_sidecar(path)
        assert data is not None
        assert data["id"] == "1.1.1"
        assert data["title"] == "Test UC A"

    def test_warns_and_returns_none_on_invalid_json(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = fake_repo / "content" / "cat-01-fake" / "broken.json"
        path.write_text("{ this is not valid", encoding="utf-8")
        result = et._read_sidecar(path)
        assert result is None
        err = capsys.readouterr().err
        assert "WARN: could not parse" in err
        assert "broken.json" in err

    def test_returns_none_on_non_dict(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        path = fake_repo / "content" / "cat-01-fake" / "list.json"
        path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        assert et._read_sidecar(path) is None

    def test_returns_none_on_missing_id(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        path = fake_repo / "content" / "cat-01-fake" / "no-id.json"
        path.write_text(json.dumps({"title": "no id"}), encoding="utf-8")
        assert et._read_sidecar(path) is None


class TestComputeTags:
    def test_app_only_match(self, fake_patterns: None) -> None:
        sidecar = {
            "app": "AWS Add-on",
            "spl": "search foo",
            "dataSources": "logs",
            "implementation": "",
            "description": "",
        }
        patterns = _compile_patterns()
        eq, _models = et._compute_tags(sidecar, patterns)
        assert "aws" in eq

    def test_narrative_match_with_min_length(self, fake_patterns: None) -> None:
        sidecar = {
            "app": "Generic",
            "spl": "search index=cloudtrail",
            "dataSources": "CloudTrail logs",
            "implementation": "Use CloudTrail.",
            "description": "Tracks CloudTrail events",
        }
        patterns = _compile_patterns()
        eq, models = et._compute_tags(sidecar, patterns)
        # ``cloudtrail`` (>= 4 chars) should match the narrative.
        assert "aws" in eq
        assert "aws_cloudtrail" in models

    def test_returns_sorted_lists(self, fake_patterns: None) -> None:
        sidecar = {
            "app": "Microsoft Azure and AWS",
            "spl": "",
            "dataSources": "",
            "implementation": "",
            "description": "",
        }
        patterns = _compile_patterns()
        eq, models = et._compute_tags(sidecar, patterns)
        assert eq == sorted(eq)
        assert models == sorted(models)
        assert "aws" in eq
        assert "azure" in eq

    def test_strips_backticks_from_text(self, fake_patterns: None) -> None:
        sidecar = {
            "app": "`AWS`",
            "spl": "`search index=cloudtrail`",
            "dataSources": "",
            "implementation": "",
            "description": "",
        }
        patterns = _compile_patterns()
        eq, _models = et._compute_tags(sidecar, patterns)
        assert "aws" in eq

    def test_handles_missing_fields(self, fake_patterns: None) -> None:
        # Missing keys must default to empty without raising.
        sidecar: dict[str, object] = {"id": "1.1.1"}
        patterns = _compile_patterns()
        eq, models = et._compute_tags(sidecar, patterns)
        assert eq == []
        assert models == []

    def test_handles_none_fields(self, fake_patterns: None) -> None:
        # Explicit ``None`` values for narrative fields are common
        # in the SSOT — the impl uses ``or ""`` to coerce them.
        sidecar = {
            "app": None,
            "spl": None,
            "dataSources": None,
            "implementation": None,
            "description": None,
        }
        patterns = _compile_patterns()
        eq, models = et._compute_tags(sidecar, patterns)
        assert eq == []
        assert models == []


class TestReorderSidecar:
    def test_known_keys_ordered_canonically(self) -> None:
        sidecar = {
            "implementation": "x",
            "id": "1.1.1",
            "title": "t",
            "criticality": "high",
            "spl": "search",
            "app": "AWS",
        }
        out = et._reorder_sidecar(sidecar)
        keys = list(out.keys())
        # canonical order: id, title, criticality, ..., app, spl, implementation
        assert keys.index("id") < keys.index("title")
        assert keys.index("title") < keys.index("criticality")
        assert keys.index("app") < keys.index("spl")
        assert keys.index("spl") < keys.index("implementation")

    def test_unknown_keys_alphabetical_at_end(self) -> None:
        sidecar = {
            "id": "1.1.1",
            "zeta_unknown": 1,
            "alpha_unknown": 2,
        }
        out = et._reorder_sidecar(sidecar)
        keys = list(out.keys())
        assert keys[0] == "id"
        # alphabetical: alpha < zeta
        assert keys.index("alpha_unknown") < keys.index("zeta_unknown")

    def test_preserves_values(self) -> None:
        sidecar = {"id": "1.1.1", "app": "AWS", "spl": "search"}
        out = et._reorder_sidecar(sidecar)
        assert out["app"] == "AWS"
        assert out["spl"] == "search"

    def test_returns_new_dict_not_alias(self) -> None:
        sidecar = {"id": "1.1.1", "app": "AWS"}
        out = et._reorder_sidecar(sidecar)
        assert out is not sidecar


class TestApplyTags:
    def test_sets_equipment_and_models(self) -> None:
        sidecar = {"id": "1.1.1", "app": "AWS"}
        out = et._apply_tags(sidecar, ["aws"], ["aws_cloudtrail"])
        assert out["equipment"] == ["aws"]
        assert out["equipmentModels"] == ["aws_cloudtrail"]

    def test_merges_with_existing_tags(self) -> None:
        sidecar = {
            "id": "1.1.1",
            "equipment": ["azure"],
            "equipmentModels": ["azure_foo"],
        }
        out = et._apply_tags(sidecar, ["aws"], ["aws_cloudtrail"])
        assert out["equipment"] == ["aws", "azure"]
        assert out["equipmentModels"] == ["aws_cloudtrail", "azure_foo"]

    def test_drops_empty_arrays(self) -> None:
        sidecar = {
            "id": "1.1.1",
            "equipment": [],
            "equipmentModels": [],
        }
        out = et._apply_tags(sidecar, [], [])
        assert "equipment" not in out
        assert "equipmentModels" not in out

    def test_drops_arrays_if_become_empty_via_merge(self) -> None:
        # If existing was empty and computed was empty, both must be popped.
        sidecar = {"id": "1.1.1"}
        out = et._apply_tags(sidecar, [], [])
        assert "equipment" not in out
        assert "equipmentModels" not in out

    def test_returns_reordered_keys(self) -> None:
        sidecar = {
            "implementation": "x",
            "id": "1.1.1",
            "app": "AWS",
        }
        out = et._apply_tags(sidecar, ["aws"], [])
        keys = list(out.keys())
        assert keys.index("id") < keys.index("app")
        assert keys.index("app") < keys.index("implementation")

    def test_does_not_mutate_input(self) -> None:
        sidecar = {"id": "1.1.1", "app": "AWS"}
        original = dict(sidecar)
        out = et._apply_tags(sidecar, ["aws"], [])
        assert sidecar == original
        assert out is not sidecar

    def test_handles_none_existing_values(self) -> None:
        sidecar = {"id": "1.1.1", "equipment": None, "equipmentModels": None}
        out = et._apply_tags(sidecar, ["aws"], ["aws_cloudtrail"])
        assert out["equipment"] == ["aws"]
        assert out["equipmentModels"] == ["aws_cloudtrail"]


class TestSerialise:
    def test_returns_indent_2_with_trailing_newline(self) -> None:
        sidecar = {"id": "1.1.1", "title": "x"}
        out = et._serialise(sidecar)
        assert out.endswith("\n")
        assert "  " in out  # 2-space indent
        assert out.count("\n") >= 3  # opening { + 2 keys + closing }

    def test_preserves_unicode(self) -> None:
        sidecar = {"id": "1.1.1", "title": "café"}
        out = et._serialise(sidecar)
        # ensure_ascii=False means café stays literal.
        assert "café" in out


class TestProcessSidecars:
    def test_processes_all_sidecars(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
    ) -> None:
        processed, changed, paths, _eq, _mod = et._process_sidecars(check=False)
        assert processed == 2
        # Both sidecars should pick up tags they didn't have.
        assert changed == 2
        # And in --check=False mode, the files on disk are now updated.
        for p in paths:
            content = p.read_text(encoding="utf-8")
            assert '"equipment"' in content or '"equipmentModels"' in content

    def test_check_mode_does_not_write(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
    ) -> None:
        before = {p.name: p.read_text(encoding="utf-8") for p in et._iter_sidecar_paths()}
        processed, changed, _paths, _eq, _mod = et._process_sidecars(check=True)
        assert processed == 2
        assert changed == 2
        # Files unchanged on disk because of ``--check``.
        for p in et._iter_sidecar_paths():
            assert p.read_text(encoding="utf-8") == before[p.name]

    def test_idempotent_when_already_up_to_date(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
    ) -> None:
        # First pass writes the tags.
        et._process_sidecars(check=False)
        # Second pass should be a no-op.
        processed, changed, paths, _eq, _mod = et._process_sidecars(check=False)
        assert processed == 2
        assert changed == 0
        assert paths == []

    def test_counts_per_equipment_id(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
    ) -> None:
        _proc, _ch, _paths, eq_counts, model_counts = et._process_sidecars(check=False)
        assert isinstance(eq_counts, Counter)
        assert eq_counts["aws"] >= 1
        assert eq_counts["azure"] >= 1
        assert isinstance(model_counts, Counter)
        assert model_counts["aws_cloudtrail"] >= 1

    def test_skips_unparseable_sidecar(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
    ) -> None:
        bad = fake_repo / "content" / "cat-01-fake" / "UC-broken.json"
        bad.write_text("{ broken", encoding="utf-8")
        processed, _changed, _paths, _eq, _mod = et._process_sidecars(check=False)
        # The broken sidecar contributes 0 to ``processed``.
        assert processed == 2  # the two real sidecars only


class TestPrintReport:
    def test_renders_all_sections(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        eq = Counter({"aws": 3, "azure": 2})
        models = Counter({"aws_cloudtrail": 1})
        et._print_report(processed=10, changed=5, eq_counts=eq, model_counts=models)
        out = capsys.readouterr().out
        assert "Processed sidecars:        10" in out
        assert "Sidecars with changed tags: 5" in out
        assert "Equipment coverage (2 distinct ids):" in out
        assert "aws" in out
        assert "azure" in out
        assert "Equipment-model coverage (1 distinct compounds):" in out
        assert "aws_cloudtrail" in out

    def test_omits_models_section_when_empty(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        et._print_report(
            processed=5,
            changed=0,
            eq_counts=Counter({"aws": 1}),
            model_counts=Counter(),
        )
        out = capsys.readouterr().out
        assert "Equipment coverage" in out
        assert "Equipment-model coverage" not in out

    def test_renders_empty_when_no_counts(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        et._print_report(0, 0, Counter(), Counter())
        out = capsys.readouterr().out
        assert "Processed sidecars:        0" in out
        assert "Equipment coverage (0 distinct ids):" in out


class TestMainCli:
    def test_default_writes_and_summary(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = et.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Processed 2 sidecars" in out
        assert "updated 2" in out

    def test_check_mode_drift_returns_1(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = et.main(["--check"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "FATAL: 2/2 UC sidecars have stale" in captured.err
        assert "Re-run" in captured.err
        # Affected file list rendered (≤25 entries).
        assert "UC-1.1.1.json" in captured.err

    def test_check_mode_clean_returns_0(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # First sync the tags so a subsequent --check is clean.
        et.main([])
        capsys.readouterr()
        rc = et.main(["--check"])
        assert rc == 0
        assert "OK: 2 UC sidecars have up-to-date equipment tags." in capsys.readouterr().out

    def test_check_mode_truncates_affected_list_at_25(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        fake_patterns: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        content = tmp_path / "content"
        cat = content / "cat-01-fake"
        cat.mkdir(parents=True)
        # 30 sidecars, all needing updates.
        for i in range(30):
            (cat / f"UC-1.1.{i + 1}.json").write_text(
                json.dumps(
                    {
                        "id": f"1.1.{i + 1}",
                        "title": f"UC {i + 1}",
                        "app": "AWS",
                        "spl": "search",
                        "dataSources": "",
                        "implementation": "",
                        "description": "",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        monkeypatch.setattr(et, "_CONTENT_UC_ROOT", content)
        monkeypatch.setattr(et, "_REPO_ROOT", tmp_path)
        rc = et.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        # Should mention "and 5 more" (30 - 25 = 5).
        assert "and 5 more" in err

    def test_report_mode_prints_breakdown(
        self,
        fake_repo: pathlib.Path,
        fake_patterns: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = et.main(["--report"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Processed sidecars:" in out
        assert "Equipment coverage" in out

    def test_help_lists_flags(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            et.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        for flag in ("--check", "--report"):
            assert flag in out

    def test_main_is_callable(self) -> None:
        # The ``if __name__ == "__main__":`` block at the bottom of
        # the module calls ``sys.exit(main())``; ensure ``main`` is
        # importable.
        assert callable(et.main)


# ----------------------------------------------------------------------
# Module-import side effect: ``sys.path`` membership of ``scripts/``
# ----------------------------------------------------------------------


class TestLegacyScriptsDirSysPathBootstrap:
    """Pin both branches of the module-level
    ``if str(_LEGACY_SCRIPTS_DIR) not in sys.path:`` guard (lines 57-58).

    The True branch (skipping when ``_LEGACY_SCRIPTS_DIR`` is already
    present) is already covered by every test in this file because the
    initial module import has already populated ``sys.path``. The False
    branch (the actual ``sys.path.insert`` call on line 58) is only
    reached during the *first* import of the module; subsequent reloads
    short-circuit at the guard. Removing the entry from ``sys.path``,
    reloading the module, and re-asserting that the insertion happened
    pins the line.
    """

    def test_reimport_when_scripts_dir_missing_re_inserts(self) -> None:
        import importlib
        import sys

        scripts_dir = str(et._LEGACY_SCRIPTS_DIR)
        original = list(sys.path)
        try:
            while scripts_dir in sys.path:
                sys.path.remove(scripts_dir)
            assert scripts_dir not in sys.path
            importlib.reload(et)
            assert scripts_dir in sys.path, (
                "module-level guard must re-insert _LEGACY_SCRIPTS_DIR "
                "when it is absent from sys.path at import time"
            )
        finally:
            sys.path[:] = original

    def test_reimport_when_scripts_dir_already_present_is_a_noop(self) -> None:
        import importlib
        import sys

        scripts_dir = str(et._LEGACY_SCRIPTS_DIR)
        assert scripts_dir in sys.path, (
            "preconditioned to pin the False branch: the module's "
            "initial import already populated sys.path"
        )
        path_before = list(sys.path)
        importlib.reload(et)
        assert sys.path.count(scripts_dir) == path_before.count(scripts_dir), (
            "reload must not append a duplicate scripts_dir entry"
        )


def test_module_constants_resolve_under_real_repo() -> None:
    # These constants must resolve to real on-disk paths at the repo
    # root so the live generator can actually load the corpus.
    assert et._REPO_ROOT.is_dir()
    assert (et._REPO_ROOT / "content").is_dir()
    assert et._CONTENT_UC_ROOT.name == "content"


def test_min_length_constants_are_sane() -> None:
    # Documented contract: app field is curated (min=1), narrative is
    # broader and noisier (min=4 to suppress false positives).
    assert et._MIN_LEN_APP == 1
    assert et._MIN_LEN_NARRATIVE == 4
    assert et._MIN_LEN_APP < et._MIN_LEN_NARRATIVE


def test_sidecar_field_order_matches_schema_anchors() -> None:
    # The first six and last few anchors should be exactly these (any
    # drift here breaks the generator's byte-stable output contract).
    expected_head = (
        "$schema",
        "id",
        "title",
        "criticality",
        "difficulty",
        "monitoringType",
    )
    assert et._SIDECAR_FIELD_ORDER[: len(expected_head)] == expected_head
    # ``equipment`` and ``equipmentModels`` must appear in the field
    # order because the generator writes them.
    assert "equipment" in et._SIDECAR_FIELD_ORDER
    assert "equipmentModels" in et._SIDECAR_FIELD_ORDER
    # And `equipment` comes before `equipmentModels`.
    eq_idx = et._SIDECAR_FIELD_ORDER.index("equipment")
    eqm_idx = et._SIDECAR_FIELD_ORDER.index("equipmentModels")
    assert eq_idx < eqm_idx
