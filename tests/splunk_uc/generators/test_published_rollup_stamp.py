"""Commit clock for generated rollups, with a fixed fallback without git."""

from __future__ import annotations

import pytest

from splunk_uc.published_rollup_stamp import (
    frozen_published_stamp,
    head_commit_epoch,
    resolve_published_stamp,
)


def test_source_date_epoch_replaces_git_and_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    monkeypatch.setattr(
        "splunk_uc.published_rollup_stamp.head_commit_epoch", lambda: "1700000000"
    )
    assert frozen_published_stamp("equipment-app-map") is None
    assert resolve_published_stamp("equipment-app-map") == "1970-01-01T00:00:00Z"


def test_head_commit_time_replaces_the_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(
        "splunk_uc.published_rollup_stamp.head_commit_epoch", lambda: "1700000000"
    )
    assert frozen_published_stamp("scorecard") is None
    assert resolve_published_stamp("provenance") == "2023-11-14T22:13:20Z"


def test_fixed_fallback_only_without_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr("splunk_uc.published_rollup_stamp.head_commit_epoch", lambda: None)
    assert frozen_published_stamp("equipment-app-map") == "2026-11-05T21:59:04Z"
    assert frozen_published_stamp("compliance-coverage") == "2026-11-05T20:47:57Z"
    assert frozen_published_stamp("recommender-app") == "2026-11-05T22:25:18Z"
    assert resolve_published_stamp("scorecard") == "2026-11-06T12:04:37Z"


def test_head_commit_epoch_reads_git() -> None:
    epoch = head_commit_epoch()
    assert epoch is not None and epoch.isdigit()
