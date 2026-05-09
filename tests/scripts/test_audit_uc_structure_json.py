"""Unit tests for the JSON backend in ``scripts/audit_uc_structure.py``.

Repo-overhaul plan §P1 step 3 (2026-05-08): the audit gained a JSON
corpus backend. These tests pin the field rules that backend enforces
so future schema-driven changes don't silently weaken the audit.

The tests do not invoke the audit as a subprocess; they import the
function directly so failures are pinpoint and the suite stays under
1 second.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "audit_uc_structure.py"
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture(scope="module")
def audit():
    """Load the audit module under test.

    P6 (scripts taxonomy, 2026-05-09): the audit body now lives at
    src/splunk_uc/audits/uc_structure.py with a thin shim at the
    original scripts/ path. Importing the implementation module
    directly keeps tests aligned with the rest of the migrated
    suite. The legacy spec-loader path is preserved as a fallback
    for an unpacked sdist that lost the src/ tree.
    """
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    try:
        import splunk_uc.audits.uc_structure as impl

        return impl
    except ImportError:
        pass
    spec = importlib.util.spec_from_file_location("audit_uc_structure", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("audit_uc_structure", module)
    spec.loader.exec_module(module)
    return module


def _good_uc():
    return {
        "id": "1.2.3",
        "title": "Detect privilege escalation in Linux audit logs",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoringType": ["Security"],
        "value": "Catches root-elevation events that bypass sudo logging.",
        "app": "Splunk_TA_nix",
        "dataSources": "auditd",
        "spl": "search index=os sourcetype=linux_audit | stats count by user",
        "implementation": "Enable auditd; ingest via Splunk_TA_nix.",
        "visualization": "Single value with sparkline",
        "cimModels": ["Authentication"],
        "grandmaExplanation": (
            "We watch for someone secretly becoming an administrator on the "
            "machine, even if they tried to hide it."
        ),
    }


def test_good_uc_no_issues(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    p.write_text("{}", encoding="utf-8")  # filename matters; payload is the arg
    issues = audit.audit_uc_json(str(p), _good_uc())
    assert issues == [], issues


def test_missing_required_field(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    del payload["cimModels"]
    issues = audit.audit_uc_json(str(p), payload)
    assert any("missing required field 'cimModels'" in i for i in issues), issues


def test_empty_required_field_string(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["spl"] = "   "
    issues = audit.audit_uc_json(str(p), payload)
    assert any("empty required field 'spl'" in i for i in issues), issues


def test_empty_cim_models_list_is_allowed(audit, tmp_path):
    """Repo-overhaul plan §P1 step 5b prep (2026-05-08): empty cimModels
    is a valid curation outcome ("no CIM applies"), not a missing-data
    failure. Other required list fields still fail when empty."""
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["cimModels"] = []
    issues = audit.audit_uc_json(str(p), payload)
    assert not any("'cimModels'" in i for i in issues), issues


def test_empty_monitoring_type_list_is_rejected(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["monitoringType"] = []
    issues = audit.audit_uc_json(str(p), payload)
    assert any("empty required field 'monitoringType'" in i for i in issues), issues


def test_null_cim_models_is_still_rejected(audit, tmp_path):
    """``null`` is sloppy data even where ``[]`` is a valid curation
    outcome — distinguishes "I forgot" from "no CIM applies"."""
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["cimModels"] = None
    issues = audit.audit_uc_json(str(p), payload)
    assert any("null required field 'cimModels'" in i for i in issues), issues


def test_allow_empty_list_set_pins_cim_models(audit):
    """The allow-empty list must contain exactly cimModels today.

    Adding a field requires a deliberate plan entry — the audit is the
    authoritative gate, so widening it silently is a regression."""
    assert audit.JSON_FIELDS_ALLOW_EMPTY_LIST == frozenset({"cimModels"})


def test_id_must_match_filename(audit, tmp_path):
    p = tmp_path / "UC-9.9.9.json"
    payload = _good_uc()
    payload["id"] = "1.2.3"
    issues = audit.audit_uc_json(str(p), payload)
    assert any("does not match filename" in i for i in issues), issues


def test_legacy_emoji_criticality_rejected(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["criticality"] = "🟠 High"
    issues = audit.audit_uc_json(str(p), payload)
    assert any("uses the legacy markdown emoji form" in i for i in issues), issues


def test_invalid_difficulty_rejected(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["difficulty"] = "wizard"
    issues = audit.audit_uc_json(str(p), payload)
    assert any("invalid difficulty 'wizard'" in i for i in issues), issues


def test_spl_must_be_string(audit, tmp_path):
    p = tmp_path / "UC-1.2.3.json"
    payload = _good_uc()
    payload["spl"] = ["not", "a", "string"]
    issues = audit.audit_uc_json(str(p), payload)
    assert any("spl must be a string" in i for i in issues), issues


def test_required_fields_match_agents_md(audit):
    """Pin the AGENTS.md authoring contract to the audit list.

    AGENTS.md says the 13 required JSON fields are id, title, criticality,
    difficulty, monitoringType, value, app, dataSources, spl,
    implementation, visualization, cimModels, grandmaExplanation. Adding
    a field anywhere requires touching both AGENTS.md and this list.
    """
    expected = {
        "id",
        "title",
        "criticality",
        "difficulty",
        "monitoringType",
        "value",
        "app",
        "dataSources",
        "spl",
        "implementation",
        "visualization",
        "cimModels",
        "grandmaExplanation",
    }
    assert set(audit.REQUIRED_JSON_FIELDS) == expected


def test_baseline_filtering(audit, tmp_path):
    """A line in the baseline must filter the matching audit issue."""
    payload = _good_uc()
    del payload["cimModels"]
    p = tmp_path / "UC-1.2.3.json"
    raw = audit.audit_uc_json(str(p), payload)
    assert raw, "audit should produce at least one issue"
    baseline_path = tmp_path / "baseline.txt"
    baseline_path.write_text("\n".join(raw) + "\n", encoding="utf-8")
    loaded = audit._load_baseline(str(baseline_path))
    assert raw[0] in loaded
