"""Shared helpers for the content-quality lift loop verbs.

See ``docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md``
for the architectural contract. This module is pure-function: no AI
calls, no subprocess dispatch, no network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONTENT_ROOT = REPO_ROOT / "content"


class TargetTier(Enum):
    """Quality tier the lift loop is authoring toward."""

    SILVER = "silver"
    GOLD = "gold"
    GOLD_V2 = "gold-v2"

    @classmethod
    def from_str(cls, value: str) -> TargetTier:
        normalised = value.strip().lower()
        for tier in cls:
            if tier.value == normalised:
                return tier
        raise ValueError(f"unknown tier {value!r}; choose from {[t.value for t in cls]}")


@dataclass(frozen=True)
class GapReport:
    """Per-UC gap analysis against a target tier's depth rubric."""

    uc_id: str
    sidecar_path: Path
    target_tier: TargetTier
    current_score: int
    failing_fields: dict[str, str] = field(default_factory=dict)
    # field_name -> human-readable rubric violation

    def to_json(self) -> dict[str, Any]:
        return {
            "uc_id": self.uc_id,
            "sidecar_path": str(self.sidecar_path),
            "target_tier": self.target_tier.value,
            "current_score": self.current_score,
            "failing_fields": dict(self.failing_fields),
        }


def resolve_sidecar_path(
    uc_id: str,
    content_root: Path | None = None,
) -> Path:
    """Locate the sidecar JSON for a given UC-X.Y.Z identifier.

    Searches ``content_root/cat-*/UC-<id>.json``. Raises
    ``FileNotFoundError`` if no match is found.
    """
    root = content_root if content_root is not None else DEFAULT_CONTENT_ROOT
    bare_id = uc_id.removeprefix("UC-")
    for sidecar in root.glob(f"cat-*/UC-{bare_id}.json"):
        return sidecar
    raise FileNotFoundError(f"no sidecar found for {uc_id} under {root}")


def load_sidecar(path: Path) -> dict[str, Any]:
    """Parse a UC sidecar JSON file."""
    with path.open(encoding="utf-8") as handle:
        return cast(dict[str, Any], json.load(handle))


def score_uc(
    sidecar_path: Path,
    target_tier: TargetTier,
) -> GapReport:
    """Score a UC against the target tier's rubric and return a gap report.

    Delegates the actual scoring to the existing ``audit-gold-profile``
    audit, parsing its summary output. For Silver/Gold the v1 audit is
    sufficient; for Gold-v2 the v2 audit is also consulted.
    """
    from splunk_uc.audits import gold_profile  # local import: lazy

    data = load_sidecar(sidecar_path)
    uc_id = str(data.get("id", sidecar_path.stem.removeprefix("UC-")))

    current_score, failures = gold_profile.score_sidecar(
        data,
        tier=target_tier.value,
    )

    return GapReport(
        uc_id=uc_id,
        sidecar_path=sidecar_path,
        target_tier=target_tier,
        current_score=current_score,
        failing_fields=failures,
    )
