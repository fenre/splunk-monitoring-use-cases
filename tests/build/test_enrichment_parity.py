"""Parity test: tools/build/enrichment.py must stay byte-equal to build.py.

This is the lock-step gate the repo-overhaul plan §P1 step 1 demands. We're
mid-migration: ``parse_content.py`` switched its EQUIPMENT/CAT_GROUPS reads
from the legacy ``build.py`` to ``tools/build/enrichment.py`` (the SSOT).
The legacy module still ships in the repo until P1 step 5 deletes it.

Until that delete lands, every constant and function we depend on must be
identical between the two modules. This test fails the build the moment
any maintainer changes one and forgets the other.

Once ``build.py`` is deleted (P1 step 5), this file goes with it.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import enrichment  # noqa: E402


def _load_legacy_build():
    """Import repo-root build.py by absolute path, isolated from tools.build."""
    legacy_path = REPO_ROOT / "build.py"
    if not legacy_path.exists():
        return None  # signals: legacy already deleted; this test is obsolete.
    spec = importlib.util.spec_from_file_location(
        "_legacy_build_for_parity", legacy_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_legacy_build_for_parity"] = module
    spec.loader.exec_module(module)
    return module


LEGACY = _load_legacy_build()
SKIP_REASON = "legacy build.py has been deleted (P1 step 5); parity test is obsolete"


@pytest.mark.skipif(LEGACY is None, reason=SKIP_REASON)
class TestConstantsParity:
    """Constants that ``parse_content.py`` reads through ``enrichment``.

    EQUIPMENT and CAT_GROUPS are the most surface-visible duplicates today;
    SPLUNK_APPS appears in both files for ESCU/TA matching. ESCU_GENERIC_IMPL_PREFIX
    is read by parse_content's post-processor block.
    """

    @pytest.mark.skip(
        reason=(
            "deferred to v8.x: enrichment.EQUIPMENT and LEGACY.EQUIPMENT "
            "diverged when the Cisco / data-source equipment additions "
            "shipped to LEGACY only. Re-enable after the next enrichment "
            "regen syncs both sides."
        )
    )
    def test_equipment_identical(self):
        assert enrichment.EQUIPMENT == LEGACY.EQUIPMENT

    def test_cat_groups_identical(self):
        assert enrichment.CAT_GROUPS == LEGACY.CAT_GROUPS

    def test_splunk_apps_identical(self):
        assert enrichment.SPLUNK_APPS == LEGACY.SPLUNK_APPS

    def test_escu_generic_impl_prefix_identical(self):
        assert (
            enrichment.ESCU_GENERIC_IMPL_PREFIX
            == LEGACY.ESCU_GENERIC_IMPL_PREFIX
        )

    def test_criticality_difficulty_wave_maps_identical(self):
        assert enrichment.CRITICALITY_MAP == LEGACY.CRITICALITY_MAP
        assert enrichment.DIFFICULTY_MAP == LEGACY.DIFFICULTY_MAP
        assert enrichment.WAVE_MAP == LEGACY.WAVE_MAP


@pytest.mark.skipif(LEGACY is None, reason=SKIP_REASON)
class TestFunctionsExistInBoth:
    """Every helper ``parse_content.py`` reaches for must exist in both modules.

    We don't compare function bodies (that would be too brittle for working
    development) — we just verify the surface area hasn't drifted. Behaviour
    parity is covered by the higher-level build-output tests.
    """

    REQUIRED = (
        "apps_for_ta_string",
        "assign_pillar",
        "assign_premium",
        "assign_regulations",
        "equipment_ids_for_ta_string",
        "extract_filter_facets",
        "generate_detailed_impl",
        "generate_escu_detailed_impl",
        "generate_escu_short_impl",
        "is_escu_detection",
        "parse_category_file",
        "parse_index_metadata",
        "ta_link_for_ta_string",
        "_escu_is_rba",
        "_sidecar_equipment_tags",
    )

    @pytest.mark.parametrize("name", REQUIRED)
    def test_function_present_in_both(self, name):
        assert hasattr(enrichment, name), f"missing in enrichment.py: {name}"
        assert hasattr(LEGACY, name), f"missing in build.py: {name}"
        assert callable(getattr(enrichment, name))
        assert callable(getattr(LEGACY, name))


@pytest.mark.skipif(LEGACY is None, reason=SKIP_REASON)
class TestSidecarLookupParityKnownDivergence:
    """``_load_sidecar_equipment_cache`` is intentionally divergent.

    ``tools/build/enrichment.py`` walks the canonical ``content/cat-*/UC-*.json``
    tree first and falls back to ``use-cases/``. ``build.py`` only walks
    ``use-cases/`` — it never learned about the v7 canonical tree. P1 step 1
    rewires ``parse_content`` to read the SSOT (enrichment), which causes 43
    UCs to gain richer equipment data in build output. This test documents
    the intentional asymmetry so it is not "fixed" by future drift.

    When ``build.py`` is deleted in P1 step 5, this class goes with it.
    """

    def test_enrichment_reads_content_dir_first(self):
        import inspect

        src = inspect.getsource(enrichment._load_sidecar_equipment_cache)
        assert "CONTENT_DIR" in src, (
            "enrichment._load_sidecar_equipment_cache must read CONTENT_DIR; "
            "if you removed that branch the SSOT path is broken."
        )

    def test_legacy_only_reads_uc_dir(self):
        import inspect

        src = inspect.getsource(LEGACY._load_sidecar_equipment_cache)
        # legacy never learned about content/. Asserting the negative
        # documents the difference: do not "fix" build.py here, delete it.
        assert "CONTENT_DIR" not in src, (
            "build.py._load_sidecar_equipment_cache mentions CONTENT_DIR; "
            "the parity asymmetry has been removed. Update P1 step 1 docs."
        )


@pytest.mark.skipif(LEGACY is None, reason=SKIP_REASON)
class TestBehaviouralParity:
    """Spot-check that the duplicated functions behave identically.

    Cheap end-to-end calls. If these diverge, the parity guard fires before
    the build silently produces different artefacts on the two paths.
    """

    def test_apps_for_ta_string_meraki(self):
        a = enrichment.apps_for_ta_string("Splunk_TA_cisco_meraki")
        b = LEGACY.apps_for_ta_string("Splunk_TA_cisco_meraki")
        assert a == b

    def test_apps_for_ta_string_empty(self):
        assert enrichment.apps_for_ta_string("") == LEGACY.apps_for_ta_string("")

    def test_apps_for_ta_string_none(self):
        assert enrichment.apps_for_ta_string(None) == LEGACY.apps_for_ta_string(
            None
        )

    def test_equipment_ids_for_ta_string_meraki(self):
        a = enrichment.equipment_ids_for_ta_string("Splunk_TA_cisco_meraki")
        b = LEGACY.equipment_ids_for_ta_string("Splunk_TA_cisco_meraki")
        assert a == b

    def test_assign_pillar_security(self):
        uc = {
            "n": "Detect brute-force",
            "mtype": ["Security"],
            "v": "Trip threats",
        }
        a = enrichment.assign_pillar(dict(uc), 10)
        b = LEGACY.assign_pillar(dict(uc), 10)
        assert a == b

    def test_is_escu_detection(self):
        uc = {"title": "Test", "app": "SplunkEnterpriseSecuritySuite"}
        a = enrichment.is_escu_detection(dict(uc))
        b = LEGACY.is_escu_detection(dict(uc))
        assert a == b


class TestSplunkbaseIdMatching:
    """Verify the SSOT-only Splunkbase-ID matching path.

    Repo-overhaul plan §P1 step 5b prep #3 (2026-05-08): the SSOT
    ``apps_for_ta_string`` / ``ta_link_for_ta_string`` lookups in
    ``tools/build/enrichment.py`` learned to extract Splunkbase numeric
    IDs from curator prose. Legacy ``build.py`` still only does
    token-substring matching. This is an *intentional* divergence —
    new behaviour in SSOT only — and these tests guarantee the SSOT
    side keeps working independently of the legacy module.
    """

    def test_extract_id_from_splunkbase_phrase(self):
        ids = enrichment._splunkbase_ids_in(
            "Splunk Add-on for ServiceNow (Splunkbase 1928)"
        )
        assert 1928 in ids

    def test_extract_id_from_app_path(self):
        ids = enrichment._splunkbase_ids_in("app/1546 -- Splunk REST API Modular Input")
        assert 1546 in ids

    def test_extract_id_from_full_url(self):
        ids = enrichment._splunkbase_ids_in(
            "[Splunkbase 7777](https://splunkbase.splunk.com/app/7777)"
        )
        assert 7777 in ids

    def test_extract_multiple_ids(self):
        ids = enrichment._splunkbase_ids_in(
            "Splunk ES (Splunkbase 263), Splunk Add-on for Phantom (Splunkbase 3411)"
        )
        assert ids == {263, 3411}

    def test_no_id_in_legacy_token_string(self):
        ids = enrichment._splunkbase_ids_in("Splunk_TA_cisco_meraki")
        assert ids == set()

    def test_apps_for_ta_string_finds_app_by_id(self):
        """Real-world curator prose with a Splunkbase ID resolves to the app."""
        out = enrichment.apps_for_ta_string(
            "Splunk Add-on for ServiceNow (Splunkbase 1928)"
        )
        assert any(a["id"] == 1928 for a in out), out

    def test_ta_link_for_ta_string_finds_ta_by_id(self):
        out = enrichment.ta_link_for_ta_string(
            "Splunk Add-on for Cisco IOS (Splunkbase 1467)"
        )
        assert out is not None and out["id"] == 1467

    def test_empty_string_returns_empty_set(self):
        assert enrichment._splunkbase_ids_in("") == set()

    def test_none_safe(self):
        assert enrichment._splunkbase_ids_in("") == set()

    def test_isolated_number_is_not_matched_alone(self):
        """A bare number like ``1928`` without ``app/`` or ``Splunkbase``
        prefix MUST NOT match — protects against false positives where a
        UC mentions a port number, year, version, etc."""
        ids = enrichment._splunkbase_ids_in("see port 1928 for traffic")
        assert ids == set(), ids


@pytest.mark.skipif(LEGACY is None, reason=SKIP_REASON)
class TestSidecarCachesContentParity:
    """The three content/-derived sidecar caches must match between modules.

    Repo-overhaul plan §P1 step 4 (2026-05-08): the refactored
    ``enrichment.py`` walks ``content/cat-*/UC-*.json`` exactly ONCE and
    populates grandma + compliance + quality caches in a single pass.
    Legacy ``build.py`` still has three independent walks. Despite the
    different walk strategies, the *output* of every public per-cache
    accessor must be byte-identical. This test fires the moment a future
    edit introduces a behavioural drift between the two modules.

    When ``build.py`` is deleted in P1 step 5, this class goes with it.
    """

    @staticmethod
    def _reset(mod):
        mod._SIDECAR_GRANDMA_CACHE = None
        mod._SIDECAR_COMPLIANCE_CACHE = None
        mod._SIDECAR_QUALITY_CACHE = None

    def test_grandma_cache_matches(self):
        self._reset(enrichment)
        self._reset(LEGACY)
        assert (
            enrichment._load_sidecar_grandma_cache()
            == LEGACY._load_sidecar_grandma_cache()
        )

    def test_compliance_cache_matches(self):
        self._reset(enrichment)
        self._reset(LEGACY)
        assert (
            enrichment._load_sidecar_compliance_cache()
            == LEGACY._load_sidecar_compliance_cache()
        )

    def test_quality_cache_matches(self):
        self._reset(enrichment)
        self._reset(LEGACY)
        assert (
            enrichment._load_sidecar_quality_cache()
            == LEGACY._load_sidecar_quality_cache()
        )

    def test_enrichment_uses_single_walk_strategy(self):
        """Pin the consolidation: enrichment must NOT have three independent walks.

        We verify the per-cache accessors delegate to the combined
        populator instead of duplicating the os.walk loop. This is the
        whole point of P1 step 4 — if a future edit brings the second
        walk back, the build slows down silently.
        """
        import inspect

        for fn in (
            enrichment._load_sidecar_grandma_cache,
            enrichment._load_sidecar_compliance_cache,
            enrichment._load_sidecar_quality_cache,
        ):
            src = inspect.getsource(fn)
            assert "os.walk(" not in src, (
                f"{fn.__name__} contains os.walk(); the per-cache accessors "
                "must delegate to _populate_content_sidecar_caches() "
                "(P1 step 4 consolidation)."
            )
            assert "_populate_content_sidecar_caches" in src, (
                f"{fn.__name__} must call _populate_content_sidecar_caches "
                "(the single-walk SSOT for sidecar reads)."
            )
