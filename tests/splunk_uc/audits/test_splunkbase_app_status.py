"""The live Splunkbase app-status audit fails closed on a cited id.

A cited id is a problem when the Splunkbase API returns 404, the app is
archived, or the add-on name beside the id shares no word with the live
title. ``data/splunkbase-app-status-backlog.json`` may only shrink.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import _uc_walk
from splunk_uc.audits import splunkbase_app_status as audit


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(audit, "REPO", tmp_path)
    monkeypatch.setattr(audit, "BACKLOG", tmp_path / "data" / "splunkbase-app-status-backlog.json")
    return tmp_path


def _write_uc(repo: Path, uc_id: str, **fields: object) -> None:
    folder = repo / "content" / "cat-01-test"
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"id": uc_id, **fields}
    (folder / f"UC-{uc_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_backlog(repo: Path, entries: list[dict[str, object]]) -> None:
    path = repo / "data" / "splunkbase-app-status-backlog.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"useCases": entries}), encoding="utf-8")


def test_missing_id_is_a_violation(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.1", app="Universal Forwarder (Splunkbase 617)")
    facts = {"617": {"httpStatus": 404}}
    violations = audit.classify(audit.collect_citations(), facts)
    assert [(v["id"], v["appId"], v["reason"]) for v in violations] == [
        ("UC-1.0.1", 617, "missing")
    ]


def test_archived_app_is_a_violation(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.2", app="EMC XtremIO (Splunkbase 2812)")
    facts = {
        "2812": {
            "httpStatus": 200,
            "title": "EMC XtremIO App for Splunk Enterprise",
            "isArchived": True,
        }
    }
    violations = audit.classify(audit.collect_citations(), facts)
    assert violations[0]["reason"] == "archived"


def test_unrelated_live_title_is_a_violation(fake_repo: Path) -> None:
    _write_uc(
        fake_repo,
        "1.0.3",
        app="Splunk Add-on for Cisco Cyber Vision (Splunkbase 6071)",
    )
    facts = {"6071": {"httpStatus": 200, "title": "Twitter", "isArchived": False}}
    violations = audit.classify(audit.collect_citations(), facts)
    assert violations[0]["reason"] == "title_mismatch"


def test_shared_title_word_is_not_a_violation(fake_repo: Path) -> None:
    _write_uc(
        fake_repo,
        "1.0.4",
        app="Splunk Add-on for Cisco IOS (Splunkbase 7538)",
    )
    facts = {
        "7538": {
            "httpStatus": 200,
            "title": "Cisco Enterprise Networking Add-on for Splunk",
            "isArchived": False,
        }
    }
    assert audit.classify(audit.collect_citations(), facts) == []


def test_download_page_is_not_a_splunkbase_id(fake_repo: Path) -> None:
    _write_uc(
        fake_repo,
        "1.0.5",
        app="Universal Forwarder (https://www.splunk.com/en_us/download/universal-forwarder.html)",
    )
    assert audit.collect_citations() == []


def test_check_fails_on_a_new_violation(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.6", references=[{"title": "Meraki", "url": "https://splunkbase.splunk.com/app/5631"}])
    _write_backlog(fake_repo, [])
    facts = {"5631": {"httpStatus": 404}}

    def fetcher(ids: set[str]) -> dict[str, dict[str, object]]:
        assert ids == {"5631"}
        return facts

    assert audit.main(["--check"], fetcher=fetcher) == 1


def test_check_fails_on_a_stale_backlog_entry(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.7", app="Cisco Meraki Add-on for Splunk (Splunkbase 5580)")
    _write_backlog(fake_repo, [{"id": "UC-1.0.7", "appId": 5580, "reason": "missing"}])

    def fetcher(ids: set[str]) -> dict[str, dict[str, object]]:
        return {"5580": {"httpStatus": 200, "title": "Cisco Meraki Add-on for Splunk", "isArchived": False}}

    assert audit.main(["--check"], fetcher=fetcher) == 1


def test_check_passes_when_the_backlog_matches(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.8", app="do not cite Splunkbase 617")
    _write_backlog(fake_repo, [{"id": "UC-1.0.8", "appId": 617, "reason": "missing"}])

    def fetcher(ids: set[str]) -> dict[str, dict[str, object]]:
        return {"617": {"httpStatus": 404}}

    assert audit.main(["--check"], fetcher=fetcher) == 0


def test_only_scans_the_named_sidecar(fake_repo: Path) -> None:
    _write_uc(fake_repo, "1.0.9", app="do not cite Splunkbase 617")
    _write_uc(fake_repo, "1.0.10", app="do not cite Splunkbase 618")
    _write_backlog(fake_repo, [{"id": "UC-9.9.9", "appId": 1, "reason": "missing"}])
    target = fake_repo / "content" / "cat-01-test" / "UC-1.0.9.json"
    seen: set[str] = set()

    def fetcher(ids: set[str]) -> dict[str, dict[str, object]]:
        seen.update(ids)
        return {app_id: {"httpStatus": 404} for app_id in ids}

    assert audit.main(["--check", "--only", str(target)], fetcher=fetcher) == 1
    assert seen == {"617"}
