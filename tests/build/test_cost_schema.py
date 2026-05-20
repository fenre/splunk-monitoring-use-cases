"""Schema validation tests for the optional ``cost`` field group (v1.8.0)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"
CONTENT_ROOT = REPO_ROOT / "content"


@pytest.fixture(scope="module")
def uc_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture(scope="module")
def cost_tier_enum() -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    tier = schema["properties"]["cost"]["properties"]["tier"]
    return list(tier["enum"])


@pytest.fixture(scope="module")
def estimated_by_enum() -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prop = schema["properties"]["cost"]["properties"]["estimated_by"]
    return list(prop["enum"])


def test_schema_is_draft_2020_12(uc_validator: jsonschema.Draft202012Validator) -> None:
    assert uc_validator.schema.get("$schema", "").endswith("/draft/2020-12/schema")


def test_cost_tier_enum_exact(cost_tier_enum: list[str]) -> None:
    assert cost_tier_enum == ["low", "medium", "high", "extreme"]


def test_cost_estimated_by_closed_enum(estimated_by_enum: list[str]) -> None:
    assert estimated_by_enum == [
        "maintainer",
        "ai-advisory",
        "vendor",
        "customer-report",
    ]


def test_uc_without_cost_validates(uc_validator: jsonschema.Draft202012Validator) -> None:
    minimal = {
        "id": "1.1.1",
        "title": "Example use case title here",
    }
    uc_validator.validate(minimal)


def test_uc_with_full_cost_block_validates(
    uc_validator: jsonschema.Draft202012Validator,
) -> None:
    payload = {
        "id": "1.1.1",
        "title": "Example use case title here",
        "cost": {
            "tier": "medium",
            "ingest_gb_per_day": 5.0,
            "search_load": "moderate",
            "search_load_notes": "Hourly scheduled stats.",
            "tstats_eligible": True,
            "storage_class": "warm",
            "retention_days": 90,
            "sources": ["index volume"],
            "last_estimated": "2026-05-19",
            "estimated_by": "maintainer",
        },
    }
    uc_validator.validate(payload)


def test_invalid_cost_tier_fails(uc_validator: jsonschema.Draft202012Validator) -> None:
    payload = {
        "id": "1.1.1",
        "title": "Example use case title here",
        "cost": {"tier": " astronomical "},
    }
    with pytest.raises(jsonschema.ValidationError):
        uc_validator.validate(payload)


def test_all_real_uc_sidecars_still_validate(
    uc_validator: jsonschema.Draft202012Validator,
) -> None:
    paths = sorted(CONTENT_ROOT.glob("cat-*/UC-*.json"))
    assert len(paths) >= 7000, f"expected large UC corpus, found {len(paths)}"
    errors: list[str] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        try:
            uc_validator.validate(payload)
        except jsonschema.ValidationError as exc:
            errors.append(f"{path}: {exc.message}")
    assert not errors, f"{len(errors)} UC(s) failed validation:\n" + "\n".join(
        errors[:5]
    )
