"""The published rollup stamp keeps dist/ stable when the body does not change."""

from __future__ import annotations

import pytest

from splunk_uc.published_rollup_stamp import frozen_published_stamp


def test_frozen_stamp_is_reused_when_the_clock_is_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert frozen_published_stamp("equipment-app-map") == "2026-11-05T21:59:04Z"
    assert frozen_published_stamp("compliance-coverage") == "2026-11-05T20:47:57Z"
    assert frozen_published_stamp("recommender-app") == "2026-11-05T22:25:18Z"


def test_source_date_epoch_replaces_the_frozen_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert frozen_published_stamp("equipment-app-map") is None
