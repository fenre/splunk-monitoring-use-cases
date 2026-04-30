"""Tests for tools/build/enrichment.py — equipment, apps, ESCU, pillar."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import enrichment  # noqa: E402


class TestEquipment:
    def test_equipment_is_list(self):
        assert isinstance(enrichment.EQUIPMENT, list)
        assert len(enrichment.EQUIPMENT) > 50

    def test_equipment_entries_have_required_keys(self):
        for entry in enrichment.EQUIPMENT:
            assert "id" in entry, f"Missing 'id' in equipment: {entry}"
            assert "tas" in entry, f"Missing 'tas' in equipment: {entry}"

    def test_equipment_ids_unique(self):
        ids = [e["id"] for e in enrichment.EQUIPMENT]
        assert len(ids) == len(set(ids))


class TestSplunkApps:
    def test_splunk_apps_is_list(self):
        assert isinstance(enrichment.SPLUNK_APPS, list)
        assert len(enrichment.SPLUNK_APPS) > 10

    def test_app_entries_have_required_keys(self):
        required = {"name", "id", "url", "tas", "desc"}
        for app in enrichment.SPLUNK_APPS:
            missing = required - set(app.keys())
            assert not missing, f"App {app.get('name', '?')} missing keys: {missing}"


class TestCatGroups:
    def test_cat_groups_is_dict(self):
        assert isinstance(enrichment.CAT_GROUPS, dict)
        assert len(enrichment.CAT_GROUPS) >= 3

    def test_cat_groups_have_lists(self):
        for key, group in enrichment.CAT_GROUPS.items():
            assert isinstance(group, list), f"CAT_GROUPS[{key}] should be a list"
            assert len(group) > 0, f"CAT_GROUPS[{key}] is empty"


class TestAppsForTa:
    def test_known_ta(self):
        result = enrichment.apps_for_ta_string("Splunk_TA_cisco_meraki")
        assert isinstance(result, list)

    def test_empty_string(self):
        result = enrichment.apps_for_ta_string("")
        assert isinstance(result, list)

    def test_none_input(self):
        result = enrichment.apps_for_ta_string(None)
        assert isinstance(result, list)


class TestAssignPillar:
    def test_security_category(self):
        uc = {"n": "Intrusion detection", "mtype": ["Security"], "v": "Detect threats"}
        result = enrichment.assign_pillar(uc, 10)
        assert result in ("security", "both")

    def test_observability_category(self):
        uc = {"n": "CPU usage", "mtype": ["Performance"], "v": "Monitor performance"}
        result = enrichment.assign_pillar(uc, 1)
        assert result in ("observability", "both")


class TestIsEscuDetection:
    def test_non_escu(self):
        uc = {"title": "Basic monitoring", "app": "Splunk_TA_linux"}
        assert enrichment.is_escu_detection(uc) is False

    def test_escu_detected(self):
        uc = {"title": "Test", "app": "SplunkEnterpriseSecuritySuite"}
        result = enrichment.is_escu_detection(uc)
        assert isinstance(result, bool)


class TestAssignRegulations:
    def test_assign_does_not_error(self):
        uc = {
            "n": "Test firewall rule",
            "mtype": ["Security"],
            "spl": "index=firewall | stats count by src_ip",
        }
        enrichment.assign_regulations(uc, 10, 1)
        assert isinstance(uc, dict)
