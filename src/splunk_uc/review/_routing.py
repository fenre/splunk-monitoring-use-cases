"""Triage-driven deep-review routing, shared by the runner and calibration scoring."""

from __future__ import annotations

from typing import Any

CORRECTNESS_SCORE_ROUTE_MAX = 3
CONFIDENCE_ROUTE_BELOW = 0.6


def triage_routing_reasons(triage: dict[str, Any] | None) -> list[str]:
    """Reasons a triage record sends its UC to deep review (empty when it does not)."""
    if not triage:
        return []
    reasons: list[str] = []
    if any(
        f.get("dimension") == "correctness" and f.get("severity") in ("blocker", "major")
        for f in triage.get("findings", [])
    ):
        reasons.append("triage correctness finding")
    if any(
        f.get("severity") in ("blocker", "major") for f in triage.get("firewalled_field_flags", [])
    ):
        reasons.append("triage firewalled blocker/major")
    score = (triage.get("scores") or {}).get("correctness")
    if isinstance(score, int) and score <= CORRECTNESS_SCORE_ROUTE_MAX:
        reasons.append(f"triage correctness score <= {CORRECTNESS_SCORE_ROUTE_MAX}")
    confidence = triage.get("confidence")
    if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_ROUTE_BELOW:
        reasons.append(f"triage confidence < {CONFIDENCE_ROUTE_BELOW}")
    return reasons
