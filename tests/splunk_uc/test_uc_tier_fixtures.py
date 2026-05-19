"""Tests for the UC quality-tier fixture corpus (Lane B Task B-1)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from splunk_uc.audits.gold_profile import GOLD_REQUIRED

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "uc-tiers"
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"
MANIFEST_PATH = FIXTURES_DIR / "MANIFEST.json"

_MANIFEST_ENTRY_KEYS = ("consumers", "criticality", "tier")


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _fixture_paths() -> list[Path]:
    return sorted(
        p
        for p in FIXTURES_DIR.glob("*.json")
        if p.name != "MANIFEST.json"
    )


def _canonical_manifest_bytes(manifest: dict) -> bytes:
    """Re-emit manifest with stable top-level and nested key ordering."""
    ordered: dict[str, dict[str, object]] = {}
    for filename in sorted(manifest):
        entry = manifest[filename]
        ordered[filename] = {key: entry[key] for key in _MANIFEST_ENTRY_KEYS}
    return (json.dumps(ordered, indent=2, sort_keys=False) + "\n").encode("utf-8")


@pytest.fixture(scope="module")
def schema_validator() -> jsonschema.Draft202012Validator:
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator(_load_schema())


@pytest.mark.parametrize("fixture_path", _fixture_paths(), ids=lambda p: p.name)
def test_fixture_validates_against_uc_schema(
    fixture_path: Path,
    schema_validator: jsonschema.Draft202012Validator,
) -> None:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    schema_validator.validate(payload)


def test_manifest_and_fixtures_are_in_bijection() -> None:
    manifest = _load_manifest()
    manifest_names = set(manifest)
    fixture_names = {p.name for p in _fixture_paths()}

    assert manifest_names == fixture_names, (
        f"manifest/fixture mismatch: "
        f"only in manifest={sorted(manifest_names - fixture_names)!r}, "
        f"only on disk={sorted(fixture_names - manifest_names)!r}"
    )


@pytest.mark.parametrize("fixture_path", _fixture_paths(), ids=lambda p: p.name)
def test_manifest_tier_and_criticality_match_sidecar(
    fixture_path: Path,
) -> None:
    manifest = _load_manifest()
    entry = manifest[fixture_path.name]
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert payload.get("criticality") == entry["criticality"], (
        f"{fixture_path.name}: sidecar criticality {payload.get('criticality')!r} "
        f"!= manifest {entry['criticality']!r}"
    )


def _has_field(payload: dict, key: str) -> bool:
    value = payload.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, list):
        return True
    return True


@pytest.mark.parametrize(
    "fixture_path",
    [p for p in _fixture_paths() if p.name.startswith("gold-")],
    ids=lambda p: p.name,
)
def test_gold_fixtures_carry_gold_required_fields(fixture_path: Path) -> None:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    missing = sorted(field for field in GOLD_REQUIRED if not _has_field(payload, field))
    assert not missing, f"{fixture_path.name} missing gold-required fields: {missing}"


def test_manifest_is_valid_json_with_stable_key_ordering() -> None:
    raw = MANIFEST_PATH.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))

    assert isinstance(manifest, dict)
    assert list(manifest) == sorted(manifest), "manifest top-level keys must be sorted"

    for filename, entry in manifest.items():
        assert list(entry) == list(_MANIFEST_ENTRY_KEYS), (
            f"{filename}: nested keys must be ordered {_MANIFEST_ENTRY_KEYS}, "
            f"got {list(entry)}"
        )
        assert isinstance(entry["consumers"], list)
        assert entry["tier"] in {"bronze", "silver", "gold"}
        assert entry["criticality"] in {"high", "medium", "low"}

    assert raw == _canonical_manifest_bytes(manifest), (
        "MANIFEST.json is not byte-stable under canonical re-emission"
    )


def test_manifest_tier_labels_match_filename_prefix() -> None:
    manifest = _load_manifest()
    for filename, entry in manifest.items():
        prefix = filename.split("-", 1)[0]
        assert entry["tier"] == prefix, (
            f"{filename}: tier {entry['tier']!r} != filename prefix {prefix!r}"
        )
