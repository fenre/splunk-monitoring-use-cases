"""Dedupe rules for cat-21 expansion vs existing catalog and cat-10.12."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .taxonomy import TaxonomyEntry

REPO = Path(__file__).resolve().parents[2]
CAT21 = REPO / "content" / "cat-21-industry-verticals"
CAT1012 = REPO / "content" / "cat-10-security-infrastructure"


def _normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\s]", "", t)
    return t


def _load_titles(directory: Path, pattern: str) -> set[str]:
    out: set[str] = set()
    for p in directory.glob(pattern):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.add(_normalize_title(data["title"]))
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def existing_cat21_titles() -> set[str]:
    return _load_titles(CAT21, "UC-*.json")


def existing_cat1012_titles() -> set[str]:
    return _load_titles(CAT1012, "UC-10.12.*.json")


def title_overlap(a: str, b: str) -> bool:
    """Fuzzy overlap: exact normalized match or high token overlap."""
    na, nb = _normalize_title(a), _normalize_title(b)
    if na == nb:
        return True
    ta, tb = set(na.split()), set(nb.split())
    if len(ta) < 3 or len(tb) < 3:
        return False
    overlap = len(ta & tb) / min(len(ta), len(tb))
    return overlap >= 0.85


# Manifest items explicitly marked [C] — do not generate in cat-21
CAT1012_SKIP_PATTERNS: tuple[str, ...] = (
    "hipaa minimum necessary",
    "pacs dicom c-store",
    "medical device network segmentation",
    "fix protocol session",
    "algorithmic trading circuit breaker",
    "market data feed latency",
    "order execution anomaly",
    "swift message unauthorized",
    "ach origination anomaly",
    "mortgage application velocity",
    "salesforce permission escalation",
    "sox access control audit",
    "fedramp continuous monitoring",
    "cmmc compliance assessment",
    "fisma reporting automation",
    "cjis audit log",
    "cac/piv authentication",
    "government cloud authorization boundary",
    "nist sp 800-53 control family",
    "kyc customer due diligence",
    "pci compliance app audit",
    "atm fraud",
    "wire transfer fraud",
    "account takeover",
    "money laundering",
    "account abuse",
    "zipf's law fraud",
    "benford's law journal",
)


def should_skip_title(title: str, *, skip_cat1012: bool = True) -> bool:
    nt = _normalize_title(title)
    for pat in CAT1012_SKIP_PATTERNS:
        if pat.replace("'", "") in nt or pat in nt:
            return True
    if skip_cat1012:
        for existing in existing_cat1012_titles():
            if title_overlap(title, existing):
                return True
    return False


def dedupe_entries(entries: list[TaxonomyEntry]) -> list[TaxonomyEntry]:
    """Remove duplicates against existing cat-21, cat-10.12, and within batch."""
    existing21 = existing_cat21_titles()
    seen_titles: set[str] = set()
    out: list[TaxonomyEntry] = []

    for entry in entries:
        nt = _normalize_title(entry.title)
        if nt in seen_titles:
            continue
        if any(title_overlap(entry.title, e) for e in existing21):
            continue
        if should_skip_title(entry.title):
            continue
        seen_titles.add(nt)
        out.append(entry)

    return out


def dedupe_report(entries: list[TaxonomyEntry]) -> dict[str, int]:
    before = len(entries)
    after = len(dedupe_entries(entries))
    return {
        "before": before,
        "after": after,
        "removed": before - after,
        "existing_cat21": len(existing_cat21_titles()),
        "existing_cat1012": len(existing_cat1012_titles()),
    }
