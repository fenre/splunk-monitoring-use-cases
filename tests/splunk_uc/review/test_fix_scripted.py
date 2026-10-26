"""Tests for review-fix-scripted (mechanical UC review fixes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.audits._template_fingerprints import detect_template_flags_v2  # noqa: E402
from splunk_uc.review import fix_scripted as fx  # noqa: E402


def test_controltest_variant() -> None:
    uc = {
        "id": "2.1.46",
        "controlTest": {
            "positiveScenario": "Ingest one event above threshold.",
            "negativeScenario": "Benign events. Variant 2 confirms zero alert rows for 'vCenter Alarm'.",
        },
    }
    new, field = fx.fix_controltest_variant(uc)
    assert field == "controlTest"
    assert (
        new["controlTest"]["negativeScenario"]
        == "Benign events. Confirm zero alert rows for 'vCenter Alarm'."
    )
    assert "v2_controlTest_variant" not in detect_template_flags_v2(new)
    assert uc["controlTest"]["negativeScenario"].startswith("Benign events. Variant 2")
    assert fx.fix_controltest_variant(new) == (new, None)


def test_purpose_built_handles_apostrophes_and_floor() -> None:
    long_prefix = "Detects certificate renewal failures from certbot logs and alerts per host. " * 2
    uc = {
        "title": "Let's Encrypt Renewal Errors",
        "description": long_prefix
        + "Purpose-built for 'Let's Encrypt Renewal Errors' in Operations workflows.",
    }
    new, field = fx.fix_purpose_built(uc)
    assert field == "description"
    assert new["description"] == long_prefix.strip()

    short = {
        "title": "X",
        "description": "Short text. Purpose-built for 'X' in Operations workflows.",
    }
    assert fx.fix_purpose_built(short) == (short, None)


@pytest.mark.parametrize(
    ("entry", "spl", "pillar", "removed"),
    [
        (
            {"name": "Splunk User Behavior Analytics", "note": "UBA"},
            "index=network",
            "Observability",
            True,
        ),
        ("Splunk Enterprise Security", "index=network", "Observability", True),
        (
            {
                "name": "Splunk Enterprise Security",
                "note": "optional — raise risk notables on repeats",
            },
            "index=x",
            "Observability",
            False,
        ),
        ("Splunk Enterprise Security", "index=notable | stats count", "Observability", False),
        ("Splunk Enterprise Security", "index=network", "Security", False),
        ("Splunk ITSI", "index=network", "Observability", False),
    ],
)
def test_premium_app_mismatch(entry: object, spl: str, pillar: str, removed: bool) -> None:
    uc = {"splunkPillar": pillar, "spl": spl, "premiumApps": [entry]}
    new, field = fx.fix_premium_app_mismatch(uc)
    if removed:
        assert field == "premiumApps"
        assert "premiumApps" not in new
    else:
        assert field is None


@pytest.mark.parametrize(("indent", "ensure_ascii"), fx.SERIALISATIONS)
def test_serialise_like_preserves_format(indent: int, ensure_ascii: bool) -> None:
    kwargs = {"indent": indent, "ensure_ascii": ensure_ascii}
    data = {"id": "1.1.1", "description": "a — b", "z": 1, "a": [1, 2]}
    raw = json.dumps(data, **kwargs) + "\n"
    out = fx.serialise_like(raw, {**data, "description": "c — d"})
    assert out == json.dumps({**data, "description": "c — d"}, **kwargs) + "\n"
    assert list(json.loads(out)) == ["id", "description", "z", "a"]


def test_run_dry_run_and_apply(tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-99-test"
    cat.mkdir(parents=True)
    path = cat / "UC-99.1.1.json"
    uc = {
        "id": "99.1.1",
        "controlTest": {
            "positiveScenario": "p",
            "negativeScenario": "n. Variant 3 confirms zero alert rows for 'T'.",
        },
    }
    path.write_text(json.dumps(uc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    dry = fx.run("controltest-variant", files=[str(path)], category=None, apply=False, samples=1)
    assert dry["changed"] == 1
    assert "Confirm zero alert rows" in dry["sample_diffs"][0]
    assert path.read_text(encoding="utf-8") == before

    applied = fx.run("controltest-variant", files=[str(path)], category=None, apply=True, samples=0)
    assert applied["applied"] is True
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["controlTest"]["negativeScenario"] == "n. Confirm zero alert rows for 'T'."


def test_family_checks_match_report_lane() -> None:
    from splunk_uc.review import report

    assert set(fx.FAMILY_CHECKS.values()) == set(report.SCRIPTED_CHECKS)
