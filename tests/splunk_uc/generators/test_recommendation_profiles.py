"""Recommendation profile generator contracts."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.generators import recommendation_profiles as rp

ROOT = Path(__file__).resolve().parents[3]


def test_every_core_uc_exists() -> None:
    profiles = rp.load_profiles()
    ids = rp._load_uc_ids()
    missing = []
    for profile in profiles:
        for item in profile["corePack"]:
            if item["ucId"] not in ids:
                missing.append(f"{profile['slug']}:{item['ucId']}")
    assert missing == []


def test_compact_payload_is_sorted_and_deterministic() -> None:
    payload = rp.compact_payload(rp.load_profiles())
    a = rp._dumps(payload)
    b = rp._dumps(payload)
    assert a == b
    slugs = list(payload["profiles"])
    assert slugs == sorted(slugs)


def test_schema_file_exists() -> None:
    assert (ROOT / "schemas" / "recommendation-profile.schema.json").is_file()
    assert (ROOT / "data" / "recommendation-profiles" / "cisco_ise.json").is_file()
