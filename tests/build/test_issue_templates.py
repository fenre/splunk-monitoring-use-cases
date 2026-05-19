"""Structural invariants for ``.github/ISSUE_TEMPLATE/`` issue forms.

Lane G Task G-3 adds a crowd-sourced false-positive report template.
These tests pin the YAML shape so a typo cannot drop required fields
or labels that triage automation relies on.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ISSUE_TEMPLATE_DIR = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
FP_TEMPLATE = ISSUE_TEMPLATE_DIR / "false-positive-report.yml"


@pytest.fixture(scope="module")
def fp_template() -> dict[str, Any]:
    assert FP_TEMPLATE.is_file(), (
        f"missing {FP_TEMPLATE.relative_to(REPO_ROOT)} — "
        "the false-positive report form must exist for operational FP intake"
    )
    loaded = yaml.safe_load(FP_TEMPLATE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), "false-positive-report.yml must parse to a mapping"
    return loaded


def test_fp_template_parses_as_yaml() -> None:
    """Every issue template under ISSUE_TEMPLATE/ must be valid YAML."""
    assert ISSUE_TEMPLATE_DIR.is_dir()
    yml_files = sorted(ISSUE_TEMPLATE_DIR.glob("*.yml"))
    assert yml_files, "expected at least one issue template"
    for path in yml_files:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert loaded is not None, f"{path.name} parsed to null"
        assert isinstance(loaded, dict), f"{path.name} must be a mapping at top level"


def test_fp_template_required_top_level_keys(fp_template: dict[str, Any]) -> None:
    for key in ("name", "description", "labels", "body"):
        assert key in fp_template, f"false-positive-report.yml missing top-level key {key!r}"


def test_fp_template_labels(fp_template: dict[str, Any]) -> None:
    labels = fp_template["labels"]
    assert isinstance(labels, list)
    assert "false-positive" in labels
    assert "needs-triage" in labels


def test_fp_template_body_has_input_and_textarea(fp_template: dict[str, Any]) -> None:
    body = fp_template["body"]
    assert isinstance(body, list)
    block_types = {block.get("type") for block in body if isinstance(block, dict)}
    assert "input" in block_types, "template must include at least one input block"
    assert "textarea" in block_types, "template must include at least one textarea block"


def test_fp_template_uc_id_input_with_pattern(fp_template: dict[str, Any]) -> None:
    """UC ID field must be a required input with UC-X.Y.Z pattern validation."""
    uc_blocks = [
        block
        for block in fp_template["body"]
        if isinstance(block, dict)
        and block.get("type") == "input"
        and block.get("id") == "uc-id"
    ]
    assert len(uc_blocks) == 1
    validations = uc_blocks[0].get("validations") or {}
    assert validations.get("required") is True
    assert validations.get("pattern") == r"^UC-\d+\.\d+\.\d+$"
