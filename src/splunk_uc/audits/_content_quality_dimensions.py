"""Heuristic evaluators for description and value field quality.

Pure functions consumed by ``content_quality.py``. These tighten beyond
``schemas/uc.schema.json`` minLength bounds — they surface a maintainer
queue, they do not auto-edit sidecars.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any, Literal

Severity = Literal["info", "warn", "fail"]

DESCRIPTION_ACTION_VERBS = (
    "detects",
    "identifies",
    "alerts",
    "monitors",
    "finds",
    "tracks",
    "surfaces",
    "flags",
    "measures",
    "reports",
    "watches",
    "correlates",
    "highlights",
)

DESCRIPTION_BOILERPLATE_PHRASES = (
    "this use case",
    "this rule",
    "this detection",
    "this uc",
    "this search",
)

DESCRIPTION_TEMPLATE_STEMS = (
    "monitors the ",
    "detects when ",
    "use case for ",
    "alert when ",
)

VALUE_OUTCOME_KEYWORDS = (
    "reduce",
    "detect",
    "prevent",
    "shorten",
    "comply",
    "ensure",
    "minimize",
    "minimise",
    "improve",
    "avoid",
    "satisfy",
    "lower",
    "accelerate",
    "eliminate",
    "contain",
    "recover",
)

VALUE_GENERIC_PHRASES = (
    "best practice",
    "industry standard",
    "improve security",
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class DescriptionFinding:
    uc_id: str
    category_id: int
    criticality: str
    dimension: str
    excerpt: str
    severity: Severity

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValueFinding:
    uc_id: str
    category_id: int
    criticality: str
    dimension: str
    excerpt: str
    severity: Severity

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _uc_id(payload: dict[str, Any], fallback: str) -> str:
    raw = payload.get("id", fallback)
    return str(raw)


def _category_id(uc_id: str) -> int:
    head = uc_id.split(".", 1)[0]
    try:
        return int(head)
    except ValueError:
        return 0


def _criticality(payload: dict[str, Any]) -> str:
    crit = payload.get("criticality", "unknown")
    return str(crit) if crit else "unknown"


def _excerpt(text: str, limit: int = 120) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def _sentence_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    parts = [p for p in _SENTENCE_SPLIT.split(stripped) if p.strip()]
    return max(1, len(parts))


def _starts_with_action_verb(description: str) -> bool:
    lowered = description.lstrip().lower()
    for verb in DESCRIPTION_ACTION_VERBS:
        if lowered.startswith(verb):
            return True
    return False


def _is_boilerplate_description(description: str, title: str) -> bool:
    lowered = description.strip().lower()
    if not lowered:
        return False
    if lowered == title.strip().lower():
        return True
    head = lowered[:80]
    if any(phrase in head for phrase in DESCRIPTION_BOILERPLATE_PHRASES):
        return True
    return any(lowered.startswith(stem) for stem in DESCRIPTION_TEMPLATE_STEMS)


def _overlap_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.casefold(), b.casefold()).ratio()


def _is_generic_only_value(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return False
    for phrase in VALUE_GENERIC_PHRASES:
        if phrase not in lowered:
            continue
        remainder = lowered.replace(phrase, "").strip(" .,-—")
        if len(remainder) < 25:
            return True
    return False


def _has_outcome_keyword(value: str) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in VALUE_OUTCOME_KEYWORDS)


def evaluate_description_quality(uc: dict[str, Any], *, uc_id: str) -> list[DescriptionFinding]:
    """Return heuristic findings for the UC ``description`` field."""
    description = uc.get("description")
    if not isinstance(description, str) or not description.strip():
        return []

    title = uc.get("title", "")
    title_str = title if isinstance(title, str) else ""
    cat = _category_id(uc_id)
    crit = _criticality(uc)
    excerpt = _excerpt(description)
    findings: list[DescriptionFinding] = []

    if len(description) < 120:
        findings.append(
            DescriptionFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="description.too_short",
                severity="fail",
            )
        )

    if _is_boilerplate_description(description, title_str):
        findings.append(
            DescriptionFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="description.boilerplate",
                severity="warn",
            )
        )

    if _sentence_count(description) == 1 and len(description) < 200:
        findings.append(
            DescriptionFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="description.too_thin",
                severity="warn",
            )
        )

    if not _starts_with_action_verb(description):
        findings.append(
            DescriptionFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="description.no_action_verb",
                severity="info",
            )
        )

    return findings


def evaluate_value_quality(uc: dict[str, Any], *, uc_id: str) -> list[ValueFinding]:
    """Return heuristic findings for the UC ``value`` field."""
    value = uc.get("value")
    if not isinstance(value, str) or not value.strip():
        return []

    description = uc.get("description", "")
    description_str = description if isinstance(description, str) else ""
    cat = _category_id(uc_id)
    crit = _criticality(uc)
    excerpt = _excerpt(value)
    findings: list[ValueFinding] = []

    if len(value) < 80:
        findings.append(
            ValueFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="value.too_short",
                severity="fail",
            )
        )

    if not _has_outcome_keyword(value):
        findings.append(
            ValueFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="value.no_outcome",
                severity="warn",
            )
        )

    if _is_generic_only_value(value):
        findings.append(
            ValueFinding(
                uc_id=uc_id,
                category_id=cat,
                criticality=crit,
                excerpt=excerpt,
                dimension="value.too_generic",
                severity="warn",
            )
        )

    if description_str.strip():
        if value.strip().casefold() == description_str.strip().casefold():
            findings.append(
                ValueFinding(
                    uc_id=uc_id,
                    category_id=cat,
                    criticality=crit,
                    excerpt=excerpt,
                    dimension="value.duplicates_description",
                    severity="warn",
                )
            )
        elif _overlap_ratio(value, description_str) >= 0.9:
            findings.append(
                ValueFinding(
                    uc_id=uc_id,
                    category_id=cat,
                    criticality=crit,
                    excerpt=excerpt,
                    dimension="value.duplicates_description",
                    severity="warn",
                )
            )

    return findings
