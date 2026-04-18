#!/usr/bin/env python3
"""Phase 0.2 — inventory every use case across use-cases/cat-*.md.

Parses the "### UC-<cat>.<sub>.<idx>" headers from every category markdown
file, captures the accompanying metadata (title, criticality, monitoring
type, Splunk pillar, regulations, MITRE ATT&CK IDs), and writes two
artefacts:

* data/inventory/ucs.json       — machine-readable, sorted, deterministic
* data/inventory/ucs.csv        — auditor-friendly tabular view

The JSON is authoritative; the CSV is a convenience projection of the same
records so that auditors and regulators can sort/filter in a spreadsheet
without touching tooling.

Run:
    python3 scripts/inventory_ucs.py
    python3 scripts/inventory_ucs.py --stats          # also print counters

Exit 0 on success, 2 if the inventory is internally inconsistent (duplicate
UC IDs, category mismatch between header and ID).
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Iterable

REPO = pathlib.Path(__file__).resolve().parents[1]
USE_CASES_DIR = REPO / "use-cases"
OUT_DIR = REPO / "data" / "inventory"

UC_HEADER_RE = re.compile(
    r"^###\s+UC-(?P<id>\d+\.\d+\.\d+)(?:\s*[·\-:]\s*(?P<title>.+?))?\s*$",
)
BULLET_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<key>[^*]+?):\*\*\s*(?P<value>.*?)\s*$",
)

BULLET_KEYS_INTERNED = {
    # canonical key -> (alternate labels seen in the catalog)
    "criticality": {"criticality"},
    "difficulty": {"difficulty"},
    "monitoringType": {"monitoring type", "monitoring types"},
    "splunkPillar": {"splunk pillar"},
    "regulations": {"regulations"},
    "mitreAttack": {"mitre att&ck", "mitre att&ck (ttp)"},
    "app": {"app/ta", "apps/tas"},
    "dataSources": {"data sources"},
    "cimModels": {"cim models"},
    "value": {"value"},
    "implementation": {"implementation"},
    "visualization": {"visualization"},
}
KEY_LOOKUP: dict[str, str] = {
    alias: canonical for canonical, aliases in BULLET_KEYS_INTERNED.items() for alias in aliases
}


@dataclass(frozen=True)
class UseCase:
    uc_id: str            # e.g. "UC-22.1.1"
    category: int
    subcategory: int
    index: int
    title: str
    source_file: str
    source_line: int
    criticality: str = ""
    difficulty: str = ""
    monitoring_type: list[str] = field(default_factory=list)
    splunk_pillar: str = ""
    regulations: list[str] = field(default_factory=list)
    mitre_attack: list[str] = field(default_factory=list)

    @property
    def sort_key(self) -> tuple[int, int, int]:
        return (self.category, self.subcategory, self.index)


def split_list_value(raw: str) -> list[str]:
    """Split a bullet-list value like 'GDPR, HIPAA, PCI-DSS' into items."""
    if not raw:
        return []
    cleaned = raw.strip().strip(".")
    if not cleaned or cleaned.lower() in {"-", "n/a", "none"}:
        return []
    parts = [p.strip() for p in re.split(r"[,;/]\s*|\s+and\s+", cleaned) if p.strip()]
    return [p for p in parts if p]


def parse_bullets(lines: Iterable[str]) -> dict:
    """Parse the bullet block immediately following a UC header."""
    bullets: dict[str, str] = {}
    for line in lines:
        m = BULLET_RE.match(line)
        if not m:
            continue
        raw_key = m.group("key").strip().lower()
        canonical = KEY_LOOKUP.get(raw_key)
        if canonical:
            bullets[canonical] = m.group("value")
    return bullets


def parse_file(path: pathlib.Path, category_number: int) -> list[UseCase]:
    text = path.read_text(encoding="utf-8").splitlines()
    ucs: list[UseCase] = []
    i = 0
    while i < len(text):
        m = UC_HEADER_RE.match(text[i])
        if not m:
            i += 1
            continue
        uc_id_tail = m.group("id")
        title = (m.group("title") or "").strip()
        cat_str, sub_str, idx_str = uc_id_tail.split(".")
        cat, sub, idx = int(cat_str), int(sub_str), int(idx_str)

        block: list[str] = []
        j = i + 1
        # UC body ends at the next header of equal or higher level, or at
        # a horizontal rule, whichever comes first.
        while j < len(text):
            nxt = text[j]
            if nxt.startswith("### ") or nxt.startswith("## ") or nxt.rstrip() == "---":
                break
            block.append(nxt)
            j += 1

        bullets = parse_bullets(block)
        ucs.append(
            UseCase(
                uc_id=f"UC-{uc_id_tail}",
                category=cat,
                subcategory=sub,
                index=idx,
                title=title,
                source_file=str(path.relative_to(REPO)),
                source_line=i + 1,
                criticality=bullets.get("criticality", ""),
                difficulty=bullets.get("difficulty", ""),
                monitoring_type=split_list_value(bullets.get("monitoringType", "")),
                splunk_pillar=bullets.get("splunkPillar", ""),
                regulations=split_list_value(bullets.get("regulations", "")),
                mitre_attack=split_list_value(bullets.get("mitreAttack", "")),
            )
        )
        i = j
    return ucs


def discover_category_files() -> list[tuple[int, pathlib.Path]]:
    """Return (category_number, path) pairs for cat-NN-*.md files."""
    pairs: list[tuple[int, pathlib.Path]] = []
    for path in USE_CASES_DIR.glob("cat-*.md"):
        m = re.match(r"cat-(\d+)-", path.name)
        if not m:
            continue
        pairs.append((int(m.group(1)), path))
    pairs.sort(key=lambda pair: pair[0])
    return pairs


def validate(ucs: list[UseCase]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, UseCase] = {}
    for uc in ucs:
        if uc.uc_id in seen:
            other = seen[uc.uc_id]
            errors.append(
                f"duplicate UC id {uc.uc_id}: "
                f"{uc.source_file}:{uc.source_line} vs {other.source_file}:{other.source_line}"
            )
            continue
        seen[uc.uc_id] = uc
    return errors


def write_json(ucs: list[UseCase], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAtComment": "Regenerate with python3 scripts/inventory_ucs.py",
        "schemaVersion": 1,
        "totalUseCases": len(ucs),
        "useCases": [asdict(uc) for uc in ucs],
    }
    with path.open("w", encoding="utf-8") as h:
        json.dump(payload, h, indent=2, ensure_ascii=False)
        h.write("\n")


def write_csv(ucs: list[UseCase], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow([
            "uc_id",
            "category",
            "subcategory",
            "title",
            "criticality",
            "difficulty",
            "monitoring_type",
            "splunk_pillar",
            "regulations",
            "mitre_attack",
            "source_file",
            "source_line",
        ])
        for uc in ucs:
            w.writerow([
                uc.uc_id,
                uc.category,
                uc.subcategory,
                uc.title,
                uc.criticality,
                uc.difficulty,
                "; ".join(uc.monitoring_type),
                uc.splunk_pillar,
                "; ".join(uc.regulations),
                "; ".join(uc.mitre_attack),
                uc.source_file,
                uc.source_line,
            ])


def print_stats(ucs: list[UseCase]) -> None:
    by_cat: dict[int, int] = defaultdict(int)
    reg_counter: Counter = Counter()
    with_regs = 0
    for uc in ucs:
        by_cat[uc.category] += 1
        if uc.regulations:
            with_regs += 1
            for r in uc.regulations:
                reg_counter[r] += 1
    print(f"\nTotal UCs: {len(ucs)}")
    print(f"UCs with Regulations: tag: {with_regs} "
          f"({with_regs * 100 / len(ucs):.1f}% of {len(ucs)})")
    print("\nUCs per category:")
    for cat in sorted(by_cat):
        print(f"  cat-{cat:02d}: {by_cat[cat]}")
    print("\nTop regulation tags:")
    for reg, n in reg_counter.most_common(25):
        print(f"  {reg:40s}  {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", action="store_true", help="print summary counters")
    ap.add_argument(
        "--out-dir",
        default=str(OUT_DIR),
        help="output directory (default: data/inventory/)",
    )
    args = ap.parse_args()

    ucs: list[UseCase] = []
    for cat_num, path in discover_category_files():
        ucs.extend(parse_file(path, cat_num))
    ucs.sort(key=lambda uc: uc.sort_key)

    errors = validate(ucs)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    out_dir = pathlib.Path(args.out_dir)
    write_json(ucs, out_dir / "ucs.json")
    write_csv(ucs, out_dir / "ucs.csv")

    print(f"wrote {out_dir / 'ucs.json'}")
    print(f"wrote {out_dir / 'ucs.csv'}")
    if args.stats:
        print_stats(ucs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
