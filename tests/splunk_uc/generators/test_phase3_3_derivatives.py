"""Unit tests for ``splunk_uc.generators.phase3_3_derivatives``.

P16 wave Y: lifts ``src/splunk_uc/generators/phase3_3_derivatives.py``
from 0% to ~99% combined coverage. Pins every documented contract of
the Phase 3.3 derivative-regulation propagation generator, the module
that walks the ``derivesFrom`` graph declared in
``data/regulations.json`` and materialises inherited ``compliance[]``
entries on every UC sidecar that maps to a parent regulation.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.generators import phase3_3_derivatives as p33

MakeSidecar = Callable[[str, str, dict[str, Any]], pathlib.Path]
MakeRegulations = Callable[[dict[str, Any]], pathlib.Path]


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic repo with content/ and data/regulations.json."""
    content = tmp_path / "content"
    content.mkdir()
    (content / "cat-09-identity-access-management").mkdir()
    (content / "cat-22-regulatory-compliance").mkdir()
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(p33, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(p33, "CONTENT_DIR", content)
    monkeypatch.setattr(p33, "REGULATIONS_PATH", tmp_path / "data" / "regulations.json")
    return tmp_path


@pytest.fixture
def make_sidecar(fake_repo: pathlib.Path) -> MakeSidecar:
    def _make(category: str, uc_id: str, payload: dict[str, Any]) -> pathlib.Path:
        cat_dir = p33.CONTENT_DIR / category
        cat_dir.mkdir(exist_ok=True)
        path = cat_dir / f"UC-{uc_id}.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    return _make


@pytest.fixture
def make_regulations(fake_repo: pathlib.Path) -> MakeRegulations:
    def _make(data: dict[str, Any]) -> pathlib.Path:
        p33.REGULATIONS_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return p33.REGULATIONS_PATH

    return _make


@pytest.fixture
def stub_synth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the migration synth helpers with deterministic stubs."""
    import splunk_uc.migrations.migrate_compliance_phase4 as p4

    monkeypatch.setattr(
        p4,
        "synthesise_control_objective",
        lambda sidecar, entry, prov: f"OBJ for {entry.get('regulation')} {entry.get('clause')}",
    )
    monkeypatch.setattr(
        p4,
        "synthesise_evidence_artifact",
        lambda sidecar, entry: f"EVI for {entry.get('regulation')} {entry.get('clause')}",
    )


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_repo_root_resolves_to_real_repo(self) -> None:
        # Real (not monkey-patched) constants point at the real repo.
        import importlib

        fresh = importlib.reload(p33)
        assert (fresh.REPO_ROOT / "data" / "regulations.json").is_file()
        assert (fresh.REPO_ROOT / "content").is_dir()

    def test_sidecar_field_order_has_compliance_after_evidence(self) -> None:
        idx_evidence = p33.SIDECAR_FIELD_ORDER.index("evidence")
        idx_compliance = p33.SIDECAR_FIELD_ORDER.index("compliance")
        assert idx_evidence < idx_compliance

    def test_entry_field_order_starts_with_regulation_version_clause(self) -> None:
        assert p33.ENTRY_FIELD_ORDER[:3] == ("regulation", "version", "clause")

    def test_entry_field_order_ends_with_derivation_source(self) -> None:
        assert p33.ENTRY_FIELD_ORDER[-1] == "derivationSource"

    def test_derivation_source_field_order_has_parent_then_inheritance(self) -> None:
        assert p33.DERIVATION_SOURCE_FIELD_ORDER[0] == "parentRegulation"
        assert "inheritanceMode" in p33.DERIVATION_SOURCE_FIELD_ORDER

    def test_assurance_degradation_full_to_partial(self) -> None:
        assert p33.ASSURANCE_DEGRADATION == {"full": "partial", "partial": "contributing"}

    def test_curated_derived_fields_contains_assurance_and_audit_text(self) -> None:
        assert "controlObjective" in p33._CURATED_DERIVED_FIELDS
        assert "evidenceArtifact" in p33._CURATED_DERIVED_FIELDS
        assert "assurance" in p33._CURATED_DERIVED_FIELDS
        assert "assurance_rationale" in p33._CURATED_DERIVED_FIELDS


# ---------------------------------------------------------------------------
# _read_json
# ---------------------------------------------------------------------------


class TestReadJson:
    def test_happy_path(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "file.json"
        path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        assert p33._read_json(path) == {"key": "value"}

    def test_missing_file_raises_file_not_found(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(FileNotFoundError):
            p33._read_json(tmp_path / "nope.json")

    def test_invalid_json_raises_decode_error(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            p33._read_json(path)

    def test_preserves_unicode(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "unicode.json"
        path.write_text(json.dumps({"name": "café"}, ensure_ascii=False), encoding="utf-8")
        assert p33._read_json(path) == {"name": "café"}


# ---------------------------------------------------------------------------
# FrameworkIndex
# ---------------------------------------------------------------------------


class TestFrameworkIndex:
    def test_basic_construction_indexes_by_id(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [
                    {"id": "gdpr", "shortName": "GDPR", "name": "General Data Protection"},
                    {"id": "uk-gdpr", "shortName": "UK GDPR", "name": "UK General Data Protection"},
                ]
            }
        )
        assert idx.framework("gdpr") is not None
        assert idx.framework("uk-gdpr") is not None
        assert idx.framework("missing") is None

    def test_alias_index_lowercases_keys(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [{"id": "gdpr"}],
                "aliasIndex": {"GDPR": "gdpr", "Gdpr": "gdpr"},
            }
        )
        assert idx.resolve_id("gdpr") == "gdpr"
        assert idx.resolve_id("GDPR") == "gdpr"
        assert idx.resolve_id("  gDpR  ") == "gdpr"

    def test_alias_skips_underscore_dollar_metadata_keys(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [{"id": "gdpr"}],
                "aliasIndex": {"GDPR": "gdpr", "$schema": "ignored"},
            }
        )
        assert idx.resolve_id("$schema") is None
        assert idx.resolve_id("gdpr") == "gdpr"

    def test_self_aliases_registered_for_id_short_name_name(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [
                    {
                        "id": "gdpr",
                        "shortName": "GDPR",
                        "name": "General Data Protection Regulation",
                    }
                ]
            }
        )
        assert idx.resolve_id("gdpr") == "gdpr"
        assert idx.resolve_id("GDPR") == "gdpr"
        assert idx.resolve_id("general data protection regulation") == "gdpr"

    def test_self_alias_does_not_override_explicit_alias(self) -> None:
        # If aliasIndex already maps "x" -> "y", FrameworkIndex must not
        # silently clobber it via the framework's own shortName.
        idx = p33.FrameworkIndex(
            {
                "frameworks": [
                    {"id": "gdpr", "shortName": "GDPR"},
                    {"id": "uk-gdpr", "shortName": "GDPR"},  # would collide
                ],
                "aliasIndex": {"GDPR": "gdpr"},
            }
        )
        assert idx.resolve_id("GDPR") == "gdpr"

    def test_self_alias_skips_blank_short_name(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "shortName": "", "name": "GDPR"}]})
        assert idx.resolve_id("gdpr") == "gdpr"

    def test_alias_index_missing_yields_empty_alias(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr"}]})
        # No aliasIndex means only self-aliases populate.
        assert idx.resolve_id("gdpr") == "gdpr"
        assert idx.resolve_id("unknown") is None

    def test_alias_index_null_treated_as_empty(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr"}], "aliasIndex": None})
        assert idx.resolve_id("gdpr") == "gdpr"

    def test_derives_from_skips_dollar_keys(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [{"id": "gdpr"}],
                "derivesFrom": {"$schema": "ignored", "uk-gdpr": {"parent": "gdpr"}},
            }
        )
        derived = idx.derives_from
        assert "uk-gdpr" in derived
        assert "$schema" not in derived

    def test_derives_from_missing_returns_empty(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": []})
        assert idx.derives_from == {}

    def test_derives_from_null_treated_as_empty(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [], "derivesFrom": None})
        assert idx.derives_from == {}

    def test_short_name_prefers_short_name(self) -> None:
        idx = p33.FrameworkIndex(
            {"frameworks": [{"id": "gdpr", "shortName": "GDPR", "name": "General"}]}
        )
        assert idx.short_name("gdpr") == "GDPR"

    def test_short_name_falls_back_to_name(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "name": "General"}]})
        assert idx.short_name("gdpr") == "General"

    def test_short_name_falls_back_to_id_for_unknown_framework(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": []})
        assert idx.short_name("unknown") == "unknown"

    def test_short_name_falls_back_to_id_when_short_name_and_name_missing(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr"}]})
        assert idx.short_name("gdpr") == "gdpr"

    def test_first_version_extracts_from_versions_zero_dot_version(self) -> None:
        idx = p33.FrameworkIndex(
            {
                "frameworks": [
                    {"id": "gdpr", "versions": [{"version": "2016/679"}, {"version": "next"}]}
                ]
            }
        )
        assert idx.first_version("gdpr") == "2016/679"

    def test_first_version_returns_none_for_unknown_framework(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": []})
        assert idx.first_version("unknown") is None

    def test_first_version_returns_none_for_empty_versions(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "versions": []}]})
        assert idx.first_version("gdpr") is None

    def test_first_version_returns_none_for_missing_versions_field(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr"}]})
        assert idx.first_version("gdpr") is None

    def test_first_version_returns_none_for_null_versions(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "versions": None}]})
        assert idx.first_version("gdpr") is None

    def test_first_version_returns_none_when_first_is_not_dict(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "versions": ["bad"]}]})
        assert idx.first_version("gdpr") is None

    def test_first_version_returns_none_when_version_is_not_str(self) -> None:
        idx = p33.FrameworkIndex({"frameworks": [{"id": "gdpr", "versions": [{"version": 42}]}]})
        assert idx.first_version("gdpr") is None


# ---------------------------------------------------------------------------
# PropagationPlan
# ---------------------------------------------------------------------------


def _make_plan(
    derives_from: dict[str, Any], extra_frameworks: list[dict[str, Any]] | None = None
) -> tuple[p33.FrameworkIndex, p33.PropagationPlan]:
    frameworks: list[dict[str, Any]] = [
        {"id": "gdpr", "shortName": "GDPR", "versions": [{"version": "2016/679"}]},
        {"id": "uk-gdpr", "shortName": "UK GDPR", "versions": [{"version": "2018"}]},
        {"id": "lgpd", "shortName": "LGPD", "versions": [{"version": "2018"}]},
        {"id": "ccpa", "shortName": "CCPA", "versions": [{"version": "2018"}]},
    ]
    if extra_frameworks:
        frameworks.extend(extra_frameworks)
    idx = p33.FrameworkIndex({"frameworks": frameworks, "derivesFrom": derives_from})
    plan = p33.PropagationPlan(idx)
    return idx, plan


class TestPropagationPlanConstruction:
    def test_basic_identity_mode(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        assert len(targets) == 1
        assert targets[0]["derivative_id"] == "uk-gdpr"
        assert targets[0]["target_clause"] == "Art.32"
        assert targets[0]["inheritance_mode"] == "identity"

    def test_mapped_mode_uses_clause_mapping(self) -> None:
        _, plan = _make_plan(
            {
                "lgpd": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "mapped",
                    "clauseMapping": {"Art.32": "Art.46"},
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        assert targets[0]["target_clause"] == "Art.46"
        assert targets[0]["inheritance_mode"] == "mapped"

    def test_mapped_mode_skips_unmapped_clauses(self) -> None:
        _, plan = _make_plan(
            {
                "lgpd": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "mapped",
                    "clauseMapping": {"Art.32": "Art.46"},
                }
            }
        )
        assert plan.targets_for_parent_clause("gdpr", "2016/679", "Art.99") == []

    def test_clause_mapping_skips_dollar_keys(self) -> None:
        # $schema-style metadata keys in clauseMapping must be filtered out.
        _, plan = _make_plan(
            {
                "lgpd": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "mapped",
                    "clauseMapping": {"$schema": "ignored", "Art.32": "Art.46"},
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        assert targets[0]["target_clause"] == "Art.46"

    def test_clause_mapping_null_treated_as_empty(self) -> None:
        with pytest.raises(SystemExit, match="clauseMapping is empty"):
            _make_plan(
                {
                    "lgpd": {
                        "parent": "gdpr",
                        "parentVersion": "2016/679",
                        "inheritanceMode": "mapped",
                        "clauseMapping": None,
                    }
                }
            )

    def test_divergences_captured_on_targets(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                    "divergences": [{"clause": "Art.32", "note": "UK scope differs"}],
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        assert targets[0]["divergence_note"] == "UK scope differs"

    def test_divergences_skip_entries_without_clause(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                    "divergences": [
                        {"note": "no clause"},
                        {"clause": "Art.32", "note": "x"},
                    ],
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        # First entry silently ignored (no clause key); the second one
        # populates the note for Art.32.
        assert targets[0]["divergence_note"] == "x"

    def test_divergences_default_to_empty_when_null(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                    "divergences": None,
                }
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        assert targets[0]["divergence_note"] is None

    def test_no_match_returns_empty_targets(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                }
            }
        )
        assert plan.targets_for_parent_clause("unknown", "v1", "Art.1") == []

    def test_systemexit_on_missing_parent(self) -> None:
        with pytest.raises(SystemExit, match="missing parent or parentVersion"):
            _make_plan({"uk-gdpr": {"parentVersion": "2016/679", "inheritanceMode": "identity"}})

    def test_systemexit_on_missing_parent_version(self) -> None:
        with pytest.raises(SystemExit, match="missing parent or parentVersion"):
            _make_plan({"uk-gdpr": {"parent": "gdpr", "inheritanceMode": "identity"}})

    def test_systemexit_on_invalid_inheritance_mode(self) -> None:
        with pytest.raises(SystemExit, match="invalid inheritanceMode"):
            _make_plan(
                {
                    "uk-gdpr": {
                        "parent": "gdpr",
                        "parentVersion": "2016/679",
                        "inheritanceMode": "weird",
                    }
                }
            )

    def test_systemexit_on_missing_inheritance_mode(self) -> None:
        with pytest.raises(SystemExit, match="invalid inheritanceMode"):
            _make_plan({"uk-gdpr": {"parent": "gdpr", "parentVersion": "2016/679"}})

    def test_systemexit_on_mapped_with_empty_clause_mapping(self) -> None:
        with pytest.raises(SystemExit, match="clauseMapping is empty"):
            _make_plan(
                {
                    "lgpd": {
                        "parent": "gdpr",
                        "parentVersion": "2016/679",
                        "inheritanceMode": "mapped",
                        "clauseMapping": {},
                    }
                }
            )

    def test_systemexit_on_mapped_with_missing_clause_mapping(self) -> None:
        with pytest.raises(SystemExit, match="clauseMapping is empty"):
            _make_plan(
                {
                    "lgpd": {
                        "parent": "gdpr",
                        "parentVersion": "2016/679",
                        "inheritanceMode": "mapped",
                    }
                }
            )

    def test_targets_systemexit_when_derivative_lacks_version(self) -> None:
        # A derivative whose framework has no version declared.
        with pytest.raises(SystemExit, match="no version declared"):
            _, plan = _make_plan(
                {
                    "no-version": {
                        "parent": "gdpr",
                        "parentVersion": "2016/679",
                        "inheritanceMode": "identity",
                    }
                },
                extra_frameworks=[{"id": "no-version", "shortName": "X"}],
            )
            plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")

    def test_multiple_derivatives_for_same_parent_clause(self) -> None:
        _, plan = _make_plan(
            {
                "uk-gdpr": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "identity",
                },
                "lgpd": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "mapped",
                    "clauseMapping": {"Art.32": "Art.46"},
                },
            }
        )
        targets = plan.targets_for_parent_clause("gdpr", "2016/679", "Art.32")
        # Sorted by deriv_id at construction → lgpd before uk-gdpr.
        assert [t["derivative_id"] for t in targets] == ["lgpd", "uk-gdpr"]


# ---------------------------------------------------------------------------
# _is_derived
# ---------------------------------------------------------------------------


class TestIsDerived:
    def test_provenance_derived_from_parent(self) -> None:
        assert p33._is_derived({"provenance": "derived-from-parent"}) is True

    def test_other_provenance_returns_false(self) -> None:
        assert p33._is_derived({"provenance": "hand-authored"}) is False

    def test_no_provenance_with_derivation_source_dict(self) -> None:
        assert p33._is_derived({"derivationSource": {"parent": "x"}}) is True

    def test_no_provenance_without_derivation_source(self) -> None:
        assert p33._is_derived({}) is False

    def test_derivation_source_not_a_dict(self) -> None:
        assert p33._is_derived({"derivationSource": "not a dict"}) is False


# ---------------------------------------------------------------------------
# _entry_key
# ---------------------------------------------------------------------------


class TestEntryKey:
    def test_lowercases_regulation(self) -> None:
        key = p33._entry_key({"regulation": "GDPR", "version": "2016/679", "clause": "Art.32"})
        assert key == ("gdpr", "2016/679", "Art.32")

    def test_strips_whitespace(self) -> None:
        key = p33._entry_key(
            {"regulation": "  GDPR  ", "version": "  2016/679  ", "clause": "  Art.32  "}
        )
        assert key == ("gdpr", "2016/679", "Art.32")

    def test_missing_fields_default_empty(self) -> None:
        assert p33._entry_key({}) == ("", "", "")

    def test_non_str_values_coerced(self) -> None:
        key = p33._entry_key({"regulation": "GDPR", "version": 2016, "clause": 32})
        assert key == ("gdpr", "2016", "32")


# ---------------------------------------------------------------------------
# _canonical_entry
# ---------------------------------------------------------------------------


class TestCanonicalEntry:
    def test_known_keys_get_canonical_order(self) -> None:
        entry = {
            "provenance": "derived-from-parent",
            "regulation": "UK GDPR",
            "clause": "Art.32",
            "version": "2018",
            "assurance": "partial",
            "mode": "satisfies",
        }
        result = p33._canonical_entry(entry)
        keys = list(result.keys())
        assert keys[:6] == ["regulation", "version", "clause", "mode", "assurance", "provenance"]

    def test_unknown_keys_preserved_at_tail(self) -> None:
        entry = {
            "regulation": "UK GDPR",
            "version": "2018",
            "clause": "Art.32",
            "extra_zebra": "tail",
            "extra_apple": "also-tail",
        }
        result = p33._canonical_entry(entry)
        keys = list(result.keys())
        # Insertion order preserved for unknowns.
        assert keys[-2:] == ["extra_zebra", "extra_apple"]

    def test_does_not_mutate_input(self) -> None:
        entry = {"regulation": "UK GDPR", "version": "2018", "clause": "Art.32"}
        original = dict(entry)
        p33._canonical_entry(entry)
        assert entry == original

    def test_derivation_source_sub_canonicalised(self) -> None:
        entry = {
            "regulation": "UK GDPR",
            "version": "2018",
            "clause": "Art.32",
            "derivationSource": {
                "divergenceNote": "x",
                "parentRegulation": "gdpr",
                "parentVersion": "2016/679",
                "parentClause": "Art.32",
            },
        }
        result = p33._canonical_entry(entry)
        ds_keys = list(result["derivationSource"].keys())
        assert ds_keys[:3] == ["parentRegulation", "parentVersion", "parentClause"]
        assert ds_keys[-1] == "divergenceNote"

    def test_derivation_source_not_dict_left_unchanged(self) -> None:
        entry = {
            "regulation": "UK GDPR",
            "version": "2018",
            "clause": "Art.32",
            "derivationSource": "not a dict",
        }
        result = p33._canonical_entry(entry)
        assert result["derivationSource"] == "not a dict"


class TestCanonicalDerivationSource:
    def test_known_keys_ordered(self) -> None:
        ds = {
            "divergenceNote": "x",
            "parentClause": "Art.32",
            "parentRegulation": "gdpr",
        }
        result = p33._canonical_derivation_source(ds)
        assert list(result.keys())[:2] == ["parentRegulation", "parentClause"]

    def test_unknown_keys_preserved_at_tail(self) -> None:
        ds = {"parentRegulation": "gdpr", "custom": "x"}
        result = p33._canonical_derivation_source(ds)
        assert list(result.keys())[-1] == "custom"


class TestCanonicalSidecar:
    def test_known_keys_ordered(self) -> None:
        sidecar = {"app": "Splunk", "id": "9.1.1", "title": "T", "$schema": "s"}
        result = p33._canonical_sidecar(sidecar)
        keys = list(result.keys())
        assert keys[:3] == ["$schema", "id", "title"]
        # "app" appears in SIDECAR_FIELD_ORDER (position 15).
        assert "app" in keys

    def test_unknown_keys_preserved_at_tail(self) -> None:
        sidecar = {"id": "9.1.1", "title": "T", "customField": "x"}
        result = p33._canonical_sidecar(sidecar)
        assert list(result.keys())[-1] == "customField"


# ---------------------------------------------------------------------------
# _encode_sidecar
# ---------------------------------------------------------------------------


class TestEncodeSidecar:
    def test_two_space_indent_with_trailing_newline(self) -> None:
        text = p33._encode_sidecar({"id": "9.1.1", "title": "T"})
        assert text.endswith("\n")
        assert '  "id"' in text

    def test_unicode_preserved(self) -> None:
        text = p33._encode_sidecar({"id": "9.1.1", "title": "café"})
        assert "café" in text


# ---------------------------------------------------------------------------
# _build_inherited_entry
# ---------------------------------------------------------------------------


class TestBuildInheritedEntry:
    def test_full_assurance_degrades_to_partial(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["assurance"] == "partial"

    def test_partial_assurance_degrades_to_contributing(self) -> None:
        parent = {"clause": "Art.32", "assurance": "partial", "mode": "satisfies"}
        target = {
            "derivative_id": "lgpd",
            "derivative_name": "LGPD",
            "derivative_version": "2018",
            "target_clause": "Art.46",
            "inheritance_mode": "mapped",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["assurance"] == "contributing"

    def test_contributing_does_not_propagate(self) -> None:
        parent = {"clause": "Art.32", "assurance": "contributing", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        assert p33._build_inherited_entry(parent, "gdpr", "2016/679", target) is None

    def test_non_str_assurance_returns_none(self) -> None:
        parent = {"clause": "Art.32", "assurance": 42, "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        assert p33._build_inherited_entry(parent, "gdpr", "2016/679", target) is None

    def test_unknown_assurance_returns_none(self) -> None:
        parent = {"clause": "Art.32", "assurance": "novel", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        assert p33._build_inherited_entry(parent, "gdpr", "2016/679", target) is None

    def test_rationale_identity_mode_mentions_preservation(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert "preserves parent clause numbering" in entry["assurance_rationale"]

    def test_rationale_mapped_mode_mentions_clause_mapping(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "lgpd",
            "derivative_name": "LGPD",
            "derivative_version": "2018",
            "target_clause": "Art.46",
            "inheritance_mode": "mapped",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert "Clause mapped per data/regulations.json" in entry["assurance_rationale"]

    def test_divergence_note_appended_to_rationale(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": "Scope mismatch",
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert "Divergence recorded" in entry["assurance_rationale"]

    def test_divergence_note_attached_to_derivation_source(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": "Scope mismatch",
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["derivationSource"]["divergenceNote"] == "Scope mismatch"

    def test_no_divergence_note_omits_field_from_derivation_source(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert "divergenceNote" not in entry["derivationSource"]

    def test_parent_id_uppercased_in_rationale(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert "GDPR@2016/679" in entry["assurance_rationale"]

    def test_default_mode_satisfies_when_missing(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full"}  # no mode
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["mode"] == "satisfies"

    def test_mode_copied_from_parent(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "contributing"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["mode"] == "contributing"

    def test_provenance_always_derived(self) -> None:
        parent = {"clause": "Art.32", "assurance": "full", "mode": "satisfies"}
        target = {
            "derivative_id": "uk-gdpr",
            "derivative_name": "UK GDPR",
            "derivative_version": "2018",
            "target_clause": "Art.32",
            "inheritance_mode": "identity",
            "divergence_note": None,
        }
        entry = p33._build_inherited_entry(parent, "gdpr", "2016/679", target)
        assert entry is not None
        assert entry["provenance"] == "derived-from-parent"


# ---------------------------------------------------------------------------
# _merge_curated_fields
# ---------------------------------------------------------------------------


class TestMergeCuratedFields:
    def test_none_curated_returns_inherited(self) -> None:
        inherited = {"regulation": "UK GDPR", "version": "2018", "clause": "Art.32"}
        assert p33._merge_curated_fields(inherited, None) == inherited

    def test_non_dict_curated_returns_inherited(self) -> None:
        inherited = {"regulation": "UK GDPR", "version": "2018", "clause": "Art.32"}
        result = p33._merge_curated_fields(inherited, "not a dict")  # type: ignore[arg-type]
        assert result == inherited

    def test_sme_curated_control_objective_overlays_inherited(self) -> None:
        inherited = {
            "regulation": "UK GDPR",
            "controlObjective": "Auto-drafted — SME review required.",
        }
        curated = {"controlObjective": "SME-refined text."}
        result = p33._merge_curated_fields(inherited, curated)
        assert result["controlObjective"] == "SME-refined text."

    def test_sme_curated_assurance_overlays_inherited(self) -> None:
        inherited = {"regulation": "UK GDPR", "assurance": "contributing"}
        curated = {"assurance": "partial"}  # SME-upgraded
        result = p33._merge_curated_fields(inherited, curated)
        assert result["assurance"] == "partial"

    def test_structural_fields_not_overridden(self) -> None:
        # "regulation" / "version" / "clause" / "provenance" / "derivationSource" / "mode"
        # are NOT in _CURATED_DERIVED_FIELDS so they should be preserved from
        # the inherited (freshly-built) entry.
        inherited = {
            "regulation": "UK GDPR",
            "version": "2018",
            "clause": "Art.32",
            "mode": "satisfies",
            "provenance": "derived-from-parent",
            "derivationSource": {"parentRegulation": "gdpr"},
        }
        curated = {
            "regulation": "STALE",
            "version": "STALE",
            "clause": "STALE",
            "mode": "STALE",
            "provenance": "STALE",
            "derivationSource": "STALE",
        }
        result = p33._merge_curated_fields(inherited, curated)
        assert result["regulation"] == "UK GDPR"
        assert result["version"] == "2018"
        assert result["clause"] == "Art.32"
        assert result["mode"] == "satisfies"
        assert result["provenance"] == "derived-from-parent"
        assert result["derivationSource"] == {"parentRegulation": "gdpr"}

    def test_all_curated_fields_merged_when_present(self) -> None:
        inherited = {"regulation": "UK GDPR"}
        curated = {
            "controlObjective": "x",
            "evidenceArtifact": "y",
            "obligationRef": "z",
            "requires_sme_review": True,
            "assurance": "partial",
            "assurance_rationale": "rat",
        }
        result = p33._merge_curated_fields(inherited, curated)
        for field in p33._CURATED_DERIVED_FIELDS:
            assert result[field] == curated[field]

    def test_does_not_mutate_inherited(self) -> None:
        inherited = {"regulation": "UK GDPR"}
        original = dict(inherited)
        p33._merge_curated_fields(inherited, {"controlObjective": "x"})
        assert inherited == original


# ---------------------------------------------------------------------------
# _autodraft_audit_fields
# ---------------------------------------------------------------------------


class TestAutodraftAuditFields:
    def test_drafts_both_fields_when_missing(self, stub_synth: None) -> None:
        entry = {"regulation": "UK GDPR", "clause": "Art.32"}
        result = p33._autodraft_audit_fields({"id": "9.1.1"}, entry)
        assert result["controlObjective"] == "OBJ for UK GDPR Art.32"
        assert result["evidenceArtifact"] == "EVI for UK GDPR Art.32"

    def test_preserves_existing_control_objective(self, stub_synth: None) -> None:
        entry = {"regulation": "UK GDPR", "controlObjective": "SME-curated."}
        result = p33._autodraft_audit_fields({"id": "9.1.1"}, entry)
        assert result["controlObjective"] == "SME-curated."

    def test_preserves_existing_evidence_artifact(self, stub_synth: None) -> None:
        entry = {"regulation": "UK GDPR", "evidenceArtifact": "SME-curated."}
        result = p33._autodraft_audit_fields({"id": "9.1.1"}, entry)
        assert result["evidenceArtifact"] == "SME-curated."

    def test_mutates_and_returns_same_dict(self, stub_synth: None) -> None:
        entry: dict[str, Any] = {"regulation": "UK GDPR", "clause": "Art.32"}
        result = p33._autodraft_audit_fields({"id": "9.1.1"}, entry)
        assert result is entry


# ---------------------------------------------------------------------------
# _rewrite_sidecar
# ---------------------------------------------------------------------------


def _build_basic_plan_for_rewrite() -> tuple[p33.FrameworkIndex, p33.PropagationPlan]:
    return _make_plan(
        {
            "uk-gdpr": {
                "parent": "gdpr",
                "parentVersion": "2016/679",
                "inheritanceMode": "identity",
            },
            "lgpd": {
                "parent": "gdpr",
                "parentVersion": "2016/679",
                "inheritanceMode": "mapped",
                "clauseMapping": {"Art.32": "Art.46"},
            },
        }
    )


class TestRewriteSidecar:
    def test_native_entry_propagates_to_uk_gdpr_and_lgpd(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "full",
                    "provenance": "hand-authored",
                }
            ]
        }
        changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert changed is True
        assert derived_count == 2
        regs = [e["regulation"] for e in sidecar["compliance"] if isinstance(e, dict)]
        assert "UK GDPR" in regs
        assert "LGPD" in regs

    def test_native_wins_over_derivative(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "full",
                    "provenance": "hand-authored",
                },
                # Hand-authored UK GDPR entry — must NOT be replaced.
                {
                    "regulation": "UK GDPR",
                    "version": "2018",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "full",  # stronger than the would-be partial
                    "provenance": "hand-authored",
                },
            ]
        }
        p33._rewrite_sidecar(sidecar, plan, idx)
        uk = [e for e in sidecar["compliance"] if e.get("regulation") == "UK GDPR"]
        assert len(uk) == 1
        assert uk[0]["provenance"] == "hand-authored"
        assert uk[0]["assurance"] == "full"

    def test_two_parents_producing_same_target_clause_dedup(self, stub_synth: None) -> None:
        # Both Art.33 and Art.34 → LGPD Art.48 — should produce one derived entry.
        idx, plan = _make_plan(
            {
                "lgpd": {
                    "parent": "gdpr",
                    "parentVersion": "2016/679",
                    "inheritanceMode": "mapped",
                    "clauseMapping": {"Art.33": "Art.48", "Art.34": "Art.48"},
                }
            }
        )
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.33",
                    "mode": "satisfies",
                    "assurance": "full",
                },
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.34",
                    "mode": "satisfies",
                    "assurance": "full",
                },
            ]
        }
        p33._rewrite_sidecar(sidecar, plan, idx)
        lgpd = [e for e in sidecar["compliance"] if e.get("regulation") == "LGPD"]
        assert len(lgpd) == 1

    def test_contributing_parent_does_not_propagate(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "contributing",
                }
            ]
        }
        changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert changed is False
        assert derived_count == 0

    def test_non_dict_entries_preserved_in_native(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {"compliance": ["not a dict"]}
        changed, _ = p33._rewrite_sidecar(sidecar, plan, idx)
        assert changed is False
        assert sidecar["compliance"] == ["not a dict"]

    def test_entry_with_no_regulation_skipped(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [{"version": "2016/679", "clause": "Art.32", "assurance": "full"}]
        }
        _changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert derived_count == 0

    def test_entry_with_no_version_skipped(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [{"regulation": "GDPR", "clause": "Art.32", "assurance": "full"}]
        }
        _changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert derived_count == 0

    def test_entry_with_no_clause_skipped(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [{"regulation": "GDPR", "version": "2016/679", "assurance": "full"}]
        }
        _changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert derived_count == 0

    def test_unknown_regulation_skipped(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "Unknown",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "assurance": "full",
                }
            ]
        }
        _changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert derived_count == 0

    def test_existing_derived_entry_curated_fields_preserved(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "full",
                    "provenance": "hand-authored",
                },
                {
                    "regulation": "UK GDPR",
                    "version": "2018",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "partial",
                    "controlObjective": "SME-refined CO.",
                    "evidenceArtifact": "SME-refined EA.",
                    "provenance": "derived-from-parent",
                    "derivationSource": {"parentRegulation": "gdpr"},
                },
            ]
        }
        p33._rewrite_sidecar(sidecar, plan, idx)
        uk = next(e for e in sidecar["compliance"] if e.get("regulation") == "UK GDPR")
        assert uk["controlObjective"] == "SME-refined CO."
        assert uk["evidenceArtifact"] == "SME-refined EA."

    def test_no_compliance_field_treated_as_empty(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        sidecar: dict[str, Any] = {"id": "9.1.1"}
        changed, derived_count = p33._rewrite_sidecar(sidecar, plan, idx)
        assert changed is False
        assert derived_count == 0
        assert sidecar["compliance"] == []

    def test_returns_unchanged_when_already_canonical(self, stub_synth: None) -> None:
        idx, plan = _build_basic_plan_for_rewrite()
        # Build a sidecar that, after _rewrite_sidecar, matches the input byte-for-byte.
        # Pre-canonicalised entry mirrors what _rewrite_sidecar would produce.
        seed: dict[str, Any] = {
            "compliance": [
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "assurance": "full",
                    "provenance": "hand-authored",
                }
            ]
        }
        # First call seeds; second call should be a no-op (changed=False).
        p33._rewrite_sidecar(seed, plan, idx)
        snapshot = json.loads(json.dumps(seed))
        changed, _ = p33._rewrite_sidecar(seed, plan, idx)
        assert changed is False
        assert seed == snapshot


# ---------------------------------------------------------------------------
# _uc_sort_key
# ---------------------------------------------------------------------------


class TestUcSortKey:
    def test_extracts_three_tuple_from_lowercase_uc_stem(self, tmp_path: pathlib.Path) -> None:
        # _uc_sort_key only recognises the lowercase ``uc-`` prefix; this is
        # the actual on-disk pattern the production glob feeds it
        # (``CONTENT_DIR.glob("cat-*/UC-*.json")`` returns capitalised stems,
        # which hit the defensive ``ValueError`` branch — pinned separately).
        assert p33._uc_sort_key(tmp_path / "uc-9.1.1.json") == (9, 1, 1)

    def test_uppercase_uc_prefix_hits_unparseable_branch(self, tmp_path: pathlib.Path) -> None:
        # Capitalised ``UC-`` is NOT stripped by _uc_sort_key — the resulting
        # ``UC-9`` segment fails int() conversion and the function returns
        # the defensive ``(10**9,)*3`` fallback. This pins the latent
        # case-sensitivity behaviour; the production paths flow through this
        # branch on every run.
        result = p33._uc_sort_key(tmp_path / "UC-9.1.1.json")
        assert result == (10**9, 10**9, 10**9)

    def test_unparseable_stem_sorts_last(self, tmp_path: pathlib.Path) -> None:
        result = p33._uc_sort_key(tmp_path / "uc-bad.json")
        assert result == (10**9, 10**9, 10**9)

    def test_multi_digit_sorts_numerically(self, tmp_path: pathlib.Path) -> None:
        # Lowercase variant exercises the int-parsing branch and proves
        # multi-digit segments sort numerically rather than lexically.
        assert p33._uc_sort_key(tmp_path / "uc-9.10.1.json") > p33._uc_sort_key(
            tmp_path / "uc-9.2.1.json"
        )

    def test_lowercase_prefix_is_stripped(self, tmp_path: pathlib.Path) -> None:
        assert p33._uc_sort_key(tmp_path / "uc-1.2.3.json") == (1, 2, 3)


# ---------------------------------------------------------------------------
# _process — the heart of the generator
# ---------------------------------------------------------------------------


def _build_basic_regulations() -> dict[str, Any]:
    return {
        "frameworks": [
            {"id": "gdpr", "shortName": "GDPR", "versions": [{"version": "2016/679"}]},
            {"id": "uk-gdpr", "shortName": "UK GDPR", "versions": [{"version": "2018"}]},
            {"id": "lgpd", "shortName": "LGPD", "versions": [{"version": "2018"}]},
        ],
        "derivesFrom": {
            "uk-gdpr": {
                "parent": "gdpr",
                "parentVersion": "2016/679",
                "inheritanceMode": "identity",
            },
            "lgpd": {
                "parent": "gdpr",
                "parentVersion": "2016/679",
                "inheritanceMode": "mapped",
                "clauseMapping": {"Art.32": "Art.46"},
            },
        },
        "aliasIndex": {"GDPR": "gdpr"},
    }


class TestProcessWrite:
    def test_write_mode_summary(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        rc = p33._process(check_only=False)
        out = capsys.readouterr().out
        assert rc == 0
        assert "Phase 3.3 derivatives:" in out
        assert "wrote" in out
        assert "inherited entries" in out

    def test_write_mode_persists_derived_entries(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        p33._process(check_only=False)
        result = json.loads(path.read_text(encoding="utf-8"))
        regs = [e["regulation"] for e in result["compliance"]]
        assert "UK GDPR" in regs
        assert "LGPD" in regs

    def test_write_mode_idempotent_second_run(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        p33._process(check_only=False)
        first = path.read_text(encoding="utf-8")
        p33._process(check_only=False)
        second = path.read_text(encoding="utf-8")
        assert first == second

    def test_no_native_entries_no_writes_no_drift(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {"id": "9.1.1", "title": "T", "compliance": []},
        )
        before = path.read_text(encoding="utf-8")
        rc = p33._process(check_only=False)
        assert rc == 0
        assert path.read_text(encoding="utf-8") == before


class TestProcessCheck:
    def test_check_clean_returns_zero_with_ok_summary(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        # Seed in write-mode first so the tree is at steady state.
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        p33._process(check_only=False)
        capsys.readouterr()  # discard write-mode output
        rc = p33._process(check_only=True)
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out
        assert "no drift" in out

    def test_check_detects_drift_exit_one(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        # Drop a UC with only the native parent entry — derived entries
        # are missing from disk → drift.
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        rc = p33._process(check_only=True)
        err = capsys.readouterr().err
        assert rc == 1
        assert "drift detected" in err
        assert "would-update" in err

    def test_check_mode_does_not_write(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        before = path.read_text(encoding="utf-8")
        p33._process(check_only=True)
        assert path.read_text(encoding="utf-8") == before


class TestProcessErrors:
    def test_unparseable_sidecar_returns_two(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = make_sidecar("cat-09-identity-access-management", "9.1.1", {"id": "9.1.1"})
        path.write_text("not json", encoding="utf-8")
        rc = p33._process(check_only=False)
        err = capsys.readouterr().err
        assert rc == 2
        assert "cannot parse JSON" in err

    def test_non_dict_sidecar_returns_two(
        self,
        make_regulations: MakeRegulations,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        path = p33.CONTENT_DIR / "cat-09-identity-access-management" / "UC-9.1.1.json"
        path.write_text("[]", encoding="utf-8")
        rc = p33._process(check_only=False)
        err = capsys.readouterr().err
        assert rc == 2
        assert "not a JSON object" in err

    def test_empty_content_tree_is_ok(
        self,
        make_regulations: MakeRegulations,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        rc = p33._process(check_only=False)
        assert rc == 0


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_help_lists_check_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            p33.main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr().out
        assert "--check" in captured

    def test_default_invocation_runs_in_write_mode(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {"id": "9.1.1", "title": "T", "compliance": []},
        )
        rc = p33.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "wrote" in out

    def test_check_flag_propagates_to_process(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {"id": "9.1.1", "title": "T", "compliance": []},
        )
        rc = p33.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_check_exits_one_on_drift(
        self,
        make_sidecar: MakeSidecar,
        make_regulations: MakeRegulations,
        stub_synth: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_regulations(_build_basic_regulations())
        make_sidecar(
            "cat-09-identity-access-management",
            "9.1.1",
            {
                "id": "9.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                        "provenance": "hand-authored",
                    }
                ],
            },
        )
        rc = p33.main(["--check"])
        assert rc == 1
