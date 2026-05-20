"""Tests for vendor changelog audit and generator."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from splunk_uc.audits import vendor_changelog as vc
from splunk_uc.generators import vendor_changelog as gen_vc

REPO = Path(__file__).resolve().parents[3]
CISCO_PATH = REPO / "data" / "vendor-changelog" / "cisco.json"


def test_cisco_json_loads_and_validates() -> None:
    changelog = vc.load_vendor_changelog(CISCO_PATH)
    assert changelog.vendor == "cisco"
    assert len(changelog.entries) >= 15


def test_all_seed_entries_pass_schema() -> None:
    changelog = vc.load_vendor_changelog(CISCO_PATH)
    for entry in changelog.entries:
        assert entry.id.startswith("CISCO-")
        assert entry.change_kind in vc.CHANGE_KINDS
        assert entry.affected_uc_categories


def test_deterministic_sort_order_on_read() -> None:
    changelog = vc.load_vendor_changelog(CISCO_PATH)
    release_dates = [entry.release_date for entry in changelog.entries]
    assert release_dates == sorted(release_dates, reverse=True)
    for left, right in zip(changelog.entries, changelog.entries[1:], strict=False):
        if left.release_date == right.release_date:
            assert left.id <= right.id


def test_generator_resorts_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    payload = {
        "version": "1.0.0",
        "generated": "2026-05-19",
        "schema_version": "1.0",
        "vendor": "cisco",
        "vendor_display": "Cisco Systems",
        "entries": [
            {
                "id": "CISCO-2024-099",
                "product": "asa",
                "product_display": "Cisco ASA",
                "release": "9.19",
                "release_date": "2024-01-01",
                "change_kind": "other",
                "summary": "Older placeholder entry for sort test.",
                "details": "Details long enough for schema validation in generator sort test.",
                "fields_added": [],
                "fields_removed": [],
                "fields_renamed": [],
                "fields_deprecated": [],
                "spl_impact": "No SPL impact for generator sort test entry.",
                "affected_uc_categories": ["13"],
                "source_url": "https://www.cisco.com/",
                "source_kind": "maintainer-note",
                "severity": "info",
                "added_by": "test",
                "added_date": "2026-05-19",
            }
        ],
    }
    path = vendor_dir / "cisco.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)
    monkeypatch.setattr(gen_vc, "VENDOR_CHANGELOG_DIR", vendor_dir)

    gen_vc.add_entry(
        "cisco",
        {
            **payload["entries"][0],
            "id": "CISCO-2025-999",
            "release_date": "2025-12-31",
            "summary": "Newest entry for sort order test in generator.",
        },
    )
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    dates = [item["release_date"] for item in reloaded["entries"]]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.parametrize(
    ("generated", "fail_days", "expected"),
    [
        (date.today(), 180, vc.FreshnessLevel.OK),
        (date.today() - timedelta(days=91), 180, vc.FreshnessLevel.WARN),
        (date.today() - timedelta(days=181), 180, vc.FreshnessLevel.FAIL),
    ],
)
def test_evaluate_freshness_levels(
    generated: date,
    fail_days: int,
    expected: vc.FreshnessLevel,
) -> None:
    changelog = vc.VendorChangelog(
        path=CISCO_PATH,
        version="1.0.0",
        generated=generated,
        schema_version="1.0",
        vendor="cisco",
        vendor_display="Cisco Systems",
        entries=(),
    )
    report = vc.evaluate_freshness(
        changelog,
        date.today(),
        warn_days=90,
        fail_days=fail_days,
    )
    assert report.level is expected


def test_evaluate_uc_impact_flags_renamed_field() -> None:
    changelog = vc.load_vendor_changelog(CISCO_PATH)
    fixture_uc = {
        "id": "13.1.99",
        "spl": 'index=firewall sourcetype=cisco:asa\n| stats count by dst_port, src_ip',
        "dataSources": "Cisco ASA syslog",
    }
    impacts = vc.evaluate_uc_impact(fixture_uc, {"cisco": changelog})
    matched = [item for item in impacts if item.entry_id == "CISCO-2024-003"]
    assert matched, "expected ASA dst_port rename entry to match fixture UC"
    assert any("dst_port" in reason for reason in matched[0].reasons)


def test_check_exit_code_fresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    shutil_copy = CISCO_PATH.read_text(encoding="utf-8")
    (vendor_dir / "cisco.json").write_text(shutil_copy, encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)
    monkeypatch.setattr(vc, "DEFAULT_OUT_DIR", tmp_path / "out")
    assert vc.main(["--check", "--max-age-days", "180", "--out", str(tmp_path / "out")]) == 0


def test_check_exit_code_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    payload = json.loads(CISCO_PATH.read_text(encoding="utf-8"))
    payload["generated"] = "2020-01-01"
    (vendor_dir / "cisco.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)
    assert vc.main(["--check", "--max-age-days", "180", "--out", str(tmp_path / "out")]) == 1


def test_vendor_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    (vendor_dir / "cisco.json").write_text(CISCO_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)
    assert vc.main(["--vendor", "cisco", "--out", str(tmp_path / "out")]) == 0


def test_max_age_days_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    payload = json.loads(CISCO_PATH.read_text(encoding="utf-8"))
    payload["generated"] = (date.today() - timedelta(days=100)).isoformat()
    (vendor_dir / "cisco.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)
    assert vc.main(["--check", "--max-age-days", "180", "--out", str(tmp_path / "out")]) == 0
    assert vc.main(["--check", "--max-age-days", "30", "--out", str(tmp_path / "out")]) == 1


def test_output_json_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    (vendor_dir / "cisco.json").write_text(CISCO_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(vc, "VENDOR_CHANGELOG_DIR", vendor_dir)

    out_dir = tmp_path / "out"
    vc.main(["--out", str(out_dir), "--show-impact"])
    first = json.loads((out_dir / "vendor-changelog.json").read_text(encoding="utf-8"))
    first.pop("generated_at", None)
    (out_dir / "vendor-changelog.json").unlink()
    vc.main(["--out", str(out_dir), "--show-impact"])
    second = json.loads((out_dir / "vendor-changelog.json").read_text(encoding="utf-8"))
    second.pop("generated_at", None)
    assert first == second


def test_change_kind_closed_enum() -> None:
    schema = json.loads((REPO / "schemas" / "vendor-changelog.schema.json").read_text(encoding="utf-8"))
    enum_values = schema["$defs"]["entry"]["properties"]["change_kind"]["enum"]
    assert set(enum_values) == set(vc.CHANGE_KINDS)


def test_unknown_vendor_raises_clear_error(tmp_path: Path) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    payload = json.loads(CISCO_PATH.read_text(encoding="utf-8"))
    payload["vendor"] = "aws"
    path = vendor_dir / "aws.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(vc.VendorChangelogError, match="not registered in KNOWN_VENDORS"):
        vc.load_vendor_changelog(path)


def test_per_vendor_schema_versions_coexist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_dir = tmp_path / "vendor-changelog"
    vendor_dir.mkdir()
    (vendor_dir / "cisco.json").write_text(CISCO_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    synthetic = json.loads(CISCO_PATH.read_text(encoding="utf-8"))
    synthetic["vendor"] = "testvendor"
    synthetic["vendor_display"] = "Test Vendor"
    synthetic["entries"] = synthetic["entries"][:1]
    synthetic["entries"][0]["id"] = "TESTVENDOR-2024-001"
    (vendor_dir / "testvendor.json").write_text(json.dumps(synthetic, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setitem(vc.KNOWN_VENDORS, "testvendor", frozenset({"1.0"}))
    loaded = vc.load_all_vendor_changelogs(vendor_dir)
    assert set(loaded) == {"cisco", "testvendor"}
    assert loaded["testvendor"].schema_version == "1.0"


def test_cli_dispatcher_smoke() -> None:
    import os

    proc = subprocess.run(
        [sys.executable, "-m", "splunk_uc", "audit-vendor-changelog", "--help"],
        cwd=REPO,
        env={**os.environ, "PYTHONPATH": str(REPO / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "max-age-days" in proc.stdout
