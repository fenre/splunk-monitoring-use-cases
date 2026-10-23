"""Starter-pack planner (guided onboarding), Python mirror of the SPA planner.

The algorithm is mirrored line for line from
``src/scripts/07-starter-plan.js``. The shared fixture in
``tests/fixtures/starter-plan-parity.json`` must produce identical output
in both implementations (``mcp/tests/test_starter_plan_parity.py``).
Change both files together.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

LEVELS: dict[str, int] = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}
UNLOCK_RANK: dict[str, int] = {"full": 0, "partial": 1, "none": 2}
MAX_STEPS = 10
NEXT_SOURCES = 3

_NUMBER = re.compile(r"^[\d,.]+$")


def alias_map(groups: Iterable[Sequence[str]] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for group in groups or []:
        if not group:
            continue
        canonical = str(group[0]).strip().lower()
        for name in group:
            out[str(name).strip().lower()] = canonical
    return out


def normalise(name: Any, aliases: Mapping[str, str]) -> str:
    key = str("" if name is None else name).strip().lower()
    return aliases.get(key, key)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({v for v in values if v})


def parse_paste(text: str) -> dict[str, list[str]]:
    """Parse pasted tstats output, a CSV export, or a plain sourcetype list."""
    sourcetypes: list[str] = []
    indexes: list[str] = []
    st_col = -1
    idx_col = -1

    def split(line: str) -> list[str]:
        t = line.strip()
        if "\t" in t:
            return t.split("\t")
        if "," in t:
            return t.split(",")
        return re.split(r"\s+", t)

    def clean(cell: str) -> str:
        return re.sub(r'^"|"$', "", str(cell or "").strip()).strip().lower()

    def is_number(cell: str) -> bool:
        return bool(_NUMBER.match(clean(cell)))

    for line in re.split(r"\r?\n", str(text or "")):
        if not line.strip() or re.match(r"^\s*\|", line):
            continue
        cells = [c for c in (clean(c) for c in split(line)) if c != ""]
        if not cells:
            continue
        if "sourcetype" in cells:
            st_col = cells.index("sourcetype")
            idx_col = cells.index("index") if "index" in cells else -1
            continue
        if st_col != -1:
            if st_col < len(cells) and cells[st_col]:
                sourcetypes.append(cells[st_col])
            if idx_col != -1 and idx_col < len(cells) and cells[idx_col]:
                indexes.append(cells[idx_col])
            continue
        if len(cells) == 3 and is_number(cells[2]):
            indexes.append(cells[0])
            sourcetypes.append(cells[1])
            continue
        if len(cells) == 2 and is_number(cells[1]):
            sourcetypes.append(cells[0])
            continue
        for c in cells:
            if is_number(c):
                continue
            if c.startswith("_") and ":" not in c:
                indexes.append(c)
            else:
                sourcetypes.append(c)

    return {
        "sourcetypes": _sorted_unique(s for s in sourcetypes if not _NUMBER.match(s)),
        "indexes": _sorted_unique(s for s in indexes if not _NUMBER.match(s)),
    }


def _equipment_match(pack_equipment: Iterable[str], user_equipment: Sequence[str]) -> bool:
    return any(
        u == e or u.startswith(e + "_") for e in pack_equipment or [] for u in user_equipment
    )


def plan_rollout(
    index: Mapping[str, Any],
    *,
    goal: str | None = None,
    level: str | None = None,
    sourcetypes: Iterable[str] | None = None,
    indexes: Iterable[str] | None = None,
    equipment: Iterable[str] | None = None,
    include_drafts: bool = False,
    max_steps: int | None = None,
) -> dict[str, Any]:
    aliases = alias_map((index or {}).get("sourcetypeAliases"))
    goal = "security" if goal == "security" else "operations"
    level = level if level in LEVELS else "beginner"
    limit = max_steps if isinstance(max_steps, int) and max_steps > 0 else MAX_STEPS
    user_st = {n for n in (normalise(s, aliases) for s in sourcetypes or []) if n}
    user_idx = {n for n in (str(s).strip().lower() for s in indexes or []) if n}
    user_eq = _sorted_unique(str(e).strip().lower() for e in equipment or [])
    has_data = bool(user_st or user_idx)

    candidates = [
        p
        for p in (index or {}).get("packs") or []
        if p.get("goal") == goal and (p.get("status") == "published" or include_drafts is True)
    ]

    def step_keys(step: Mapping[str, Any]) -> list[str]:
        keys = [normalise(s, aliases) for s in step.get("sourcetypes") or []]
        keys.extend("index:" + str(i).lower() for i in step.get("indexes") or [])
        return keys

    def step_ready(step: Mapping[str, Any]) -> bool:
        for k in step_keys(step):
            if k.startswith("index:"):
                if k[6:] in user_idx:
                    return True
            elif k in user_st:
                return True
        return False

    evaluated: list[dict[str, Any]] = []
    for p in candidates:
        steps = sorted(p.get("steps") or [], key=lambda s: s["order"])
        ready = [step_ready(s) for s in steps]
        ready_count = sum(1 for r in ready if r)
        if ready_count == 0:
            unlock = "none"
        elif ready_count == len(steps):
            unlock = "full"
        else:
            unlock = "partial"
        missing: list[str] = []
        for s, r in zip(steps, ready, strict=True):
            if not r:
                missing.extend(step_keys(s))
        evaluated.append(
            {
                "pack": p,
                "steps": steps,
                "ready": ready,
                "readyCount": ready_count,
                "unlock": unlock,
                "equipmentMatch": _equipment_match(p.get("equipment") or [], user_eq),
                "missingData": _sorted_unique(missing),
            }
        )

    included = [e for e in evaluated if e["readyCount"] > 0 or e["equipmentMatch"]]
    included.sort(
        key=lambda e: (
            0 if e["readyCount"] > 0 else 1,
            0 if e["equipmentMatch"] else 1,
            UNLOCK_RANK[e["unlock"]],
            -e["readyCount"],
            e["pack"]["id"],
        )
    )

    plan_steps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for e in included:
        none_ready = e["readyCount"] == 0
        for s, r in zip(e["steps"], e["ready"], strict=True):
            if len(plan_steps) >= limit or s["ucId"] in seen:
                continue
            if not r and not none_ready:
                continue
            seen.add(s["ucId"])
            diff = str(s.get("difficulty") or "")
            plan_steps.append(
                {
                    "position": len(plan_steps) + 1,
                    "ucId": s["ucId"],
                    "title": s.get("title") or "",
                    "packId": e["pack"]["id"],
                    "order": s["order"],
                    "criticality": s.get("criticality") or "",
                    "difficulty": diff,
                    "wave": s.get("wave") or "",
                    "ready": r,
                    "difficultyWarning": diff in LEVELS and LEVELS[diff] > LEVELS[level],
                }
            )

    unsatisfied: dict[str, list[str]] = {}
    uc_packs: dict[str, set[str]] = {}
    for e in evaluated:
        for s, r in zip(e["steps"], e["ready"], strict=True):
            if r:
                continue
            unsatisfied.setdefault(s["ucId"], step_keys(s))
            uc_packs.setdefault(s["ucId"], set()).add(e["pack"]["id"])

    next_sources: list[dict[str, Any]] = []
    for _round in range(NEXT_SOURCES):
        gain: dict[str, list[str]] = {}
        for uc, keys in unsatisfied.items():
            for k in _sorted_unique(keys):
                gain.setdefault(k, []).append(uc)
        best: str | None = None
        for k in sorted(gain):
            if best is None or len(gain[k]) > len(gain[best]):
                best = k
        if best is None:
            break
        packs: set[str] = set()
        for uc in gain[best]:
            packs.update(uc_packs[uc])
            del unsatisfied[uc]
        is_index = best.startswith("index:")
        next_sources.append(
            {
                "kind": "index" if is_index else "sourcetype",
                "name": best[6:] if is_index else best,
                "unlocks": len(gain[best]),
                "packs": sorted(packs),
            }
        )

    empty_reason: str | None = None
    if not plan_steps:
        empty_reason = "no-input" if (not has_data and not user_eq) else "no-match"

    return {
        "goal": goal,
        "level": level,
        "packs": [
            {
                "id": e["pack"]["id"],
                "title": e["pack"].get("title") or "",
                "status": e["pack"].get("status"),
                "unlock": e["unlock"],
                "readySteps": e["readyCount"],
                "totalSteps": len(e["steps"]),
                "equipmentMatch": e["equipmentMatch"],
                "missingData": e["missingData"],
            }
            for e in included
        ],
        "steps": plan_steps,
        "nextSources": next_sources,
        "emptyReason": empty_reason,
    }
