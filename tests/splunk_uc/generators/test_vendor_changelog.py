"""Tests for ``splunk_uc.generators.vendor_changelog`` (Lane J-5)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from splunk_uc.audits.vendor_changelog import VendorChangelogError
from splunk_uc.generators import vendor_changelog as gen


REQUIRED_BASE_ARGS = [
    "--product",
    "asa",
    "--release",
    "9.20.1",
    "--release-date",
    "2026-04-15",
    "--change-kind",
    "field-renamed",
    "--summary",
    "Test summary describing the change for unit-test purposes only.",
    "--details",
    "Test details describing the change for unit-test coverage; safe to ignore.",
    "--spl-impact",
    "Test SPL impact narrative for unit-test coverage; safe to ignore.",
    "--source-url",
    "https://example.com/vendor/release-notes",
    "--categories",
    "3",
]


def _seed_vendor_file(tmp_path: Path, *, entries: list[dict[str, Any]] | None = None) -> Path:
    payload = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "generated": "2026-04-01",
        "vendor": "cisco",
        "vendor_display": "Cisco Systems",
        "entries": entries or [],
    }
    path = tmp_path / "cisco.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def seeded_vendor_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _seed_vendor_file(tmp_path)
    monkeypatch.setattr(gen, "VENDOR_CHANGELOG_DIR", tmp_path)
    # REPO_ROOT is only used for pretty-printing the success message;
    # rebind to the tmp_path's parent so relative_to() doesn't blow up.
    monkeypatch.setattr(gen, "REPO_ROOT", tmp_path.parent)
    return tmp_path


def test_next_entry_id_starts_at_001() -> None:
    assert gen._next_entry_id("cisco", [], 2026) == "CISCO-2026-001"


def test_next_entry_id_increments_per_year() -> None:
    entries = [{"id": "CISCO-2026-001"}, {"id": "CISCO-2026-007"}, {"id": "CISCO-2025-099"}]
    assert gen._next_entry_id("cisco", entries, 2026) == "CISCO-2026-008"
    assert gen._next_entry_id("cisco", entries, 2027) == "CISCO-2027-001"


def test_next_entry_id_ignores_malformed_ids() -> None:
    entries = [{"id": "not-an-id"}, {"id": "CISCO-2026-002"}]
    assert gen._next_entry_id("cisco", entries, 2026) == "CISCO-2026-003"


def test_sort_entries_orders_newest_first_with_id_tiebreak() -> None:
    entries = [
        {"id": "CISCO-2026-001", "release_date": "2026-01-15"},
        {"id": "CISCO-2026-002", "release_date": "2026-03-10"},
        {"id": "CISCO-2026-003", "release_date": "2026-03-10"},
    ]
    sorted_entries = gen._sort_entries(entries)
    assert [item["id"] for item in sorted_entries] == [
        "CISCO-2026-002",
        "CISCO-2026-003",
        "CISCO-2026-001",
    ]


def test_sort_entries_handles_bad_release_date() -> None:
    entries = [
        {"id": "CISCO-2026-001", "release_date": "not-a-date"},
        {"id": "CISCO-2026-002", "release_date": "2026-01-01"},
    ]
    sorted_entries = gen._sort_entries(entries)
    # Bad date is treated as ordinal 0 → comes last.
    assert sorted_entries[-1]["id"] == "CISCO-2026-001"


def test_build_entry_from_args_round_trip() -> None:
    args = mock.Mock(spec=[])
    args.product = "asa"
    args.product_display = ""
    args.release = "9.20.1"
    args.release_date = "2026-04-15"
    args.change_kind = "field-rename"
    args.summary = "Summary"
    args.details = "Details"
    args.fields_added = []
    args.fields_removed = []
    args.fields_deprecated = ["old_field"]
    args.rename_from = "src"
    args.rename_to = "dest"
    args.spl_impact = "spl impact"
    args.categories = ["3"]
    args.source_url = "https://example.com"
    args.source_kind = "release-notes"
    args.severity = "minor"
    args.added_by = "maintainer"
    entry = gen._build_entry_from_args(args, "CISCO-2026-001")
    assert entry["id"] == "CISCO-2026-001"
    assert entry["product_display"] == "asa"
    assert entry["fields_renamed"] == [{"from": "src", "to": "dest"}]
    assert entry["added_date"] == date.today().isoformat()


def _valid_entry(entry_id: str = "CISCO-2026-001") -> dict[str, Any]:
    return {
        "id": entry_id,
        "product": "asa",
        "product_display": "Cisco ASA",
        "release": "9.20",
        "release_date": "2026-04-15",
        "change_kind": "field-added",
        "summary": "Test summary describing the change for unit-test purposes only.",
        "details": "Test details describing the change for unit-test coverage; safe to ignore.",
        "fields_added": ["new_field"],
        "fields_removed": [],
        "fields_renamed": [],
        "fields_deprecated": [],
        "spl_impact": "Update SPL to include new_field for ASA visibility.",
        "affected_uc_categories": ["3"],
        "source_url": "https://example.com/release-notes",
        "source_kind": "release-notes",
        "severity": "minor",
        "added_by": "maintainer",
        "added_date": "2026-04-20",
    }


def test_add_entry_writes_payload(seeded_vendor_dir: Path) -> None:
    path = gen.add_entry("cisco", _valid_entry())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert any(item["id"] == "CISCO-2026-001" for item in payload["entries"])
    assert payload["generated"] == date.today().isoformat()


def test_add_entry_rejects_duplicate_id(seeded_vendor_dir: Path) -> None:
    gen.add_entry("cisco", _valid_entry())
    with pytest.raises(VendorChangelogError, match="already exists"):
        gen.add_entry("cisco", _valid_entry())


def test_add_entry_dry_run_does_not_modify_file(
    seeded_vendor_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = (seeded_vendor_dir / "cisco.json").read_text(encoding="utf-8")
    gen.add_entry("cisco", _valid_entry(), dry_run=True)
    after = (seeded_vendor_dir / "cisco.json").read_text(encoding="utf-8")
    assert before == after
    captured = capsys.readouterr()
    assert "CISCO-2026-001" in captured.out


def test_add_entry_missing_vendor_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gen, "VENDOR_CHANGELOG_DIR", tmp_path)
    entry = {"id": "X-2026-001"}
    with pytest.raises(VendorChangelogError, match="vendor file not found"):
        gen.add_entry("does-not-exist", entry)


def test_main_dry_run_succeeds(
    seeded_vendor_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = gen.main(["--vendor", "cisco", "--dry-run", *REQUIRED_BASE_ARGS])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Dry run OK" in captured.out


def test_main_writes_real_entry(
    seeded_vendor_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = gen.main(["--vendor", "cisco", *REQUIRED_BASE_ARGS])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Added CISCO-2026-001" in captured.out


def test_main_returns_2_when_vendor_file_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gen, "VENDOR_CHANGELOG_DIR", tmp_path)
    rc = gen.main(["--vendor", "missing", *REQUIRED_BASE_ARGS])
    assert rc == 2
    captured = capsys.readouterr()
    assert "ERROR" in captured.err


def test_main_returns_1_on_duplicate_entry_id(
    seeded_vendor_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc1 = gen.main(["--vendor", "cisco", *REQUIRED_BASE_ARGS])
    assert rc1 == 0
    rc2 = gen.main(
        ["--vendor", "cisco", "--entry-id", "CISCO-2026-001", *REQUIRED_BASE_ARGS]
    )
    assert rc2 == 1
    captured = capsys.readouterr()
    assert "already exists" in captured.err


def test_main_returns_2_when_entries_not_array(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gen, "VENDOR_CHANGELOG_DIR", tmp_path)
    path = tmp_path / "cisco.json"
    path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "generated": "2026-04-01",
                "vendor": "cisco",
                "vendor_display": "Cisco Systems",
                "entries": [],
            }
        ),
        encoding="utf-8",
    )
    # Mutate after schema-load so we hit the gen.main runtime check.
    with mock.patch.object(gen, "load_vendor_changelog", return_value=None):
        path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "schema_version": "1.0.0",
                    "generated": "2026-04-01",
                    "vendor": "cisco",
                    "vendor_display": "Cisco Systems",
                    "entries": "not-an-array",
                }
            ),
            encoding="utf-8",
        )
        rc = gen.main(["--vendor", "cisco", *REQUIRED_BASE_ARGS])
    assert rc == 2
    captured = capsys.readouterr()
    assert "entries must be an array" in captured.err
