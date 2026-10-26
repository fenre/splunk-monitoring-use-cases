"""Calibration set selection and triage-model scoring.

The calibration set is a stratified sample (category x criticality, with a
floor of ``status=verified`` UCs). The deep model reviews every UC in it to
produce the reference; a maintainer spot-checks a subset and records
corrections in ``human-labels.json``. A triage candidate passes when, against
that reference, it reaches the recall and false-blocker thresholds in
``docs/uc-text-review-rubric.md``.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from splunk_uc.review._ledger import (
    REVIEW_ROOT,
    category_of,
    iter_tier_records,
    rel_file,
    uc_id_of,
)
from splunk_uc.review._routing import triage_routing_reasons

CALIBRATION_ROOT = REVIEW_ROOT / "calibration"
SET_PATH = CALIBRATION_ROOT / "set.json"
HUMAN_LABELS_PATH = CALIBRATION_ROOT / "human-labels.json"
RECALL_MIN = 0.90
FALSE_BLOCKER_MAX = 0.10
GATED_SEVERITIES = ("blocker", "major")

FindingKey = tuple[str, str, str]


def select_calibration_set(
    entries: Iterable[tuple[Path, dict[str, Any]]],
    *,
    size: int = 150,
    min_verified: int = 15,
    human_sample: int = 40,
    seed: int = 20261026,
) -> dict[str, Any]:
    """Round-robin across shuffled (category, criticality) strata, with a verified floor."""
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    verified: list[tuple[Path, dict[str, Any]]] = []
    for path, uc in entries:
        strata[(category_of(path), str(uc.get("criticality", "unknown")))].append((path, uc))
        if uc.get("status") == "verified":
            verified.append((path, uc))
    for members in strata.values():
        rng.shuffle(members)
    rng.shuffle(verified)

    chosen: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, uc in verified[:min_verified]:
        chosen[uc_id_of(uc)] = (path, uc)
    keys = sorted(strata)
    rng.shuffle(keys)
    cursor = dict.fromkeys(keys, 0)
    while len(chosen) < size and any(cursor[k] < len(strata[k]) for k in keys):
        for key in keys:
            if len(chosen) >= size:
                break
            members = strata[key]
            while cursor[key] < len(members):
                path, uc = members[cursor[key]]
                cursor[key] += 1
                if uc_id_of(uc) not in chosen:
                    chosen[uc_id_of(uc)] = (path, uc)
                    break

    rows = sorted(
        (
            {
                "uc_id": uid,
                "file": rel_file(path),
                "category": category_of(path),
                "criticality": uc.get("criticality"),
                "status": uc.get("status"),
            }
            for uid, (path, uc) in chosen.items()
        ),
        key=lambda r: [int(x) for x in r["uc_id"].removeprefix("UC-").split(".")],
    )
    step = max(1, len(rows) // max(1, human_sample))
    human = [r["uc_id"] for r in rows[::step]][:human_sample]
    return {
        "$comment": "UC review calibration set (scripts/uc_review_runner.py calibrate select).",
        "seed": seed,
        "size": len(rows),
        "ucs": rows,
        "human_spot_check": human,
    }


def human_labels_template(calibration_set: dict[str, Any]) -> dict[str, Any]:
    return {
        "$comment": (
            "Maintainer spot-check of the deep-model reference. For each UC in "
            "human_spot_check: list reference findings that are wrong under 'reject' "
            "(match on field + dimension) and findings the reference missed under 'add'. "
            "Set 'checked' to true once the UC has been reviewed."
        ),
        "labels": {
            uc_id: {"checked": False, "reject": [], "add": []}
            for uc_id in calibration_set.get("human_spot_check", [])
        },
    }


def _keys(record: dict[str, Any], severities: Iterable[str]) -> set[FindingKey]:
    wanted = set(severities)
    keys = {
        (record["uc_id"], str(f.get("field")), str(f.get("dimension")))
        for f in record.get("findings", [])
        if f.get("severity") in wanted
    }
    keys |= {
        (record["uc_id"], str(f.get("field")), "firewalled")
        for f in record.get("firewalled_field_flags", [])
        if f.get("severity") in wanted
    }
    return keys


def _label_keys(uc_id: str, items: Iterable[dict[str, Any]]) -> set[FindingKey]:
    return {(uc_id, str(i.get("field")), str(i.get("dimension", "firewalled"))) for i in items}


def score_candidate(
    *,
    reference_root: Path,
    candidate_root: Path,
    reference_tier: str = "deep",
    candidate_tier: str = "triage",
    uc_ids: Iterable[str] | None = None,
    human_labels: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recall of reference blocker/major findings and the candidate's false-blocker rate."""
    allowed = set(uc_ids) if uc_ids is not None else None
    reference = {
        r["uc_id"]: r
        for r in iter_tier_records(reference_tier, root=reference_root)
        if allowed is None or r["uc_id"] in allowed
    }
    candidate = {
        r["uc_id"]: r
        for r in iter_tier_records(candidate_tier, root=candidate_root)
        if allowed is None or r["uc_id"] in allowed
    }
    common = sorted(set(reference) & set(candidate))

    labels = (human_labels or {}).get("labels", {})
    ref_gated: set[FindingKey] = set()
    ref_any: set[FindingKey] = set()
    cand_gated: set[FindingKey] = set()
    cand_blockers: set[FindingKey] = set()
    for uc_id in common:
        ref = reference[uc_id]
        gated = _keys(ref, GATED_SEVERITIES)
        label = labels.get(uc_id) or {}
        if label.get("checked"):
            gated -= _label_keys(uc_id, label.get("reject", []))
            gated |= _label_keys(uc_id, label.get("add", []))
        ref_gated |= gated
        ref_any |= _keys(ref, ("blocker", "major", "minor", "needs_verification")) | gated
        cand_gated |= _keys(candidate[uc_id], GATED_SEVERITIES)
        cand_blockers |= _keys(candidate[uc_id], ("blocker",))

    needs_deep = {
        uc_id
        for uc_id in common
        if any(
            f.get("dimension") == "correctness" and f.get("severity") in GATED_SEVERITIES
            for f in reference[uc_id].get("findings", [])
        )
        or any(
            f.get("severity") == "blocker"
            for f in reference[uc_id].get("firewalled_field_flags", [])
        )
    }
    routed = {uc_id for uc_id in common if _routes_to_deep(candidate[uc_id])}
    verdict_agreement = (
        sum(1 for u in common if reference[u].get("verdict") == candidate[u].get("verdict"))
        / len(common)
        if common
        else 0.0
    )

    matched = ref_gated & cand_gated
    recall = len(matched) / len(ref_gated) if ref_gated else 1.0
    false_blockers = {k for k in cand_blockers if k not in ref_gated}
    false_blocker_rate = len(false_blockers) / len(cand_blockers) if cand_blockers else 0.0
    passed = recall >= RECALL_MIN and false_blocker_rate <= FALSE_BLOCKER_MAX
    return {
        "ucs_scored": len(common),
        "missing_reference": sorted(set(candidate) - set(reference)),
        "missing_candidate": sorted(set(reference) - set(candidate)),
        "reference_gated_findings": len(ref_gated),
        "candidate_gated_findings": len(cand_gated),
        "matched": len(matched),
        "recall": round(recall, 4),
        "candidate_blockers": len(cand_blockers),
        "false_blockers": len(false_blockers),
        "false_blocker_rate": round(false_blocker_rate, 4),
        "thresholds": {"recall_min": RECALL_MIN, "false_blocker_max": FALSE_BLOCKER_MAX},
        "human_labels_applied": sum(1 for v in labels.values() if v.get("checked")),
        "passed": passed,
        "routing_recall": round(len(needs_deep & routed) / len(needs_deep), 4)
        if needs_deep
        else 1.0,
        "ucs_needing_deep": len(needs_deep),
        "ucs_routed_by_candidate": len(routed),
        "verdict_agreement": round(verdict_agreement, 4),
        "missed_examples": [list(k) for k in sorted(ref_gated - cand_gated)[:25]],
        "false_blocker_examples": [list(k) for k in sorted(false_blockers)[:25]],
    }


def _routes_to_deep(triage: dict[str, Any]) -> bool:
    return bool(triage_routing_reasons(triage))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
