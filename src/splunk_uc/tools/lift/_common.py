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
    failing_fields: dict[str, list[str]] = field(default_factory=dict)
    # field_name -> human-readable rubric violations (one entry per gap)

    def to_json(self) -> dict[str, Any]:
        return {
            "uc_id": self.uc_id,
            "sidecar_path": str(self.sidecar_path),
            "target_tier": self.target_tier.value,
            "current_score": self.current_score,
            "failing_fields": {k: list(v) for k, v in self.failing_fields.items()},
        }


def resolve_sidecar_path(
    uc_id: str,
    content_root: Path | None = None,
) -> Path:
    """Locate the sidecar JSON for a given UC-X.Y.Z identifier.

    Searches ``content_root/cat-*/UC-<id>.json``. Raises
    ``FileNotFoundError`` if no match is found, or ``RuntimeError`` if
    more than one match is found (a healthy catalogue never has two
    ``cat-*`` dirs containing the same UC ID).
    """
    root = content_root if content_root is not None else DEFAULT_CONTENT_ROOT
    bare_id = uc_id.removeprefix("UC-")
    matches = sorted(root.glob(f"cat-*/UC-{bare_id}.json"))
    if not matches:
        raise FileNotFoundError(f"no sidecar found for {uc_id} under {root}")
    if len(matches) > 1:
        rendered = ", ".join(str(path.relative_to(root)) for path in matches)
        raise RuntimeError(f"multiple sidecars found for {uc_id} under {root}: {rendered}")
    return matches[0]


def load_sidecar(path: Path) -> dict[str, Any]:
    """Parse a UC sidecar JSON file. Raises ValueError for non-object JSON."""
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"sidecar {path} must be a JSON object; got {type(data).__name__}")
    return cast(dict[str, Any], data)


def score_uc(
    sidecar_path: Path,
    target_tier: TargetTier,
) -> GapReport:
    """Score a UC against the depth rubric and return a gap report.

    Delegates to ``gold_profile.score_sidecar``, which scores a parsed
    UC dict against the Bronze/Silver/Gold gradient defined in
    ``src/splunk_uc/audits/gold_profile.py``. The ``target_tier``
    argument is recorded on the returned ``GapReport`` for downstream
    consumers (``lift-prompt`` etc.) but does not change the score —
    the audit always returns the highest tier reached.

    Gold-v2 (``schemas/uc-profile-gold.json`` v2) is not consulted
    here; callers requesting Gold-v2 thresholds should additionally
    invoke ``gold_profile_v2`` themselves.
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
