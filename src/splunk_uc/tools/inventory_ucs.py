"""Inventory every use case from the JSON SSOT (``content/cat-*/UC-*.json``).

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/inventory_ucs.py to src/splunk_uc/tools/inventory_ucs.py.
parents[3] resolves: inventory_ucs.py -> tools/ -> splunk_uc/ ->
src/ -> repo root. The legacy ``parents[1]`` chain assumed depth one
and is now wrong by two levels. The legacy shim re-exports ``main``
so any direct CLI invocation still works during the soak period.

The ``generatedAtComment`` in the emitted ``ucs.json`` deliberately
continues to point at the legacy ``scripts/inventory_ucs.py`` path so
the file stays byte-stable for downstream consumers (audit baselines,
release diffs). We will refresh that comment in a separate PR
together with the rest of the soaked-shim retirement work.

Walks each UC sidecar, captures the curator-authored metadata
(title, criticality, monitoring type, Splunk pillar, regulations, MITRE
ATT&CK IDs), and writes two artefacts:

* ``data/inventory/ucs.json`` -- machine-readable, sorted, deterministic
* ``data/inventory/ucs.csv`` -- auditor-friendly tabular projection

The JSON is authoritative; the CSV is a convenience projection of the same
records so auditors and regulators can sort/filter in a spreadsheet
without touching tooling.

Run::

    python -m splunk_uc inventory-ucs
    python -m splunk_uc inventory-ucs --stats          # also print counters

Exit 0 on success, 2 if the inventory is internally inconsistent
(duplicate UC IDs).
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO / "content"
OUT_DIR = REPO / "data" / "inventory"


@dataclass(frozen=True)
class UseCase:
    """One UC sidecar projected onto auditor-relevant inventory fields."""

    uc_id: str  # e.g. "UC-22.1.1"
    category: int
    subcategory: int
    index: int
    title: str
    source_file: str
    source_line: int = 1  # JSON sidecars don't carry line numbers; default to 1
    criticality: str = ""
    difficulty: str = ""
    monitoring_type: list[str] = field(default_factory=list)
    splunk_pillar: str = ""
    regulations: list[str] = field(default_factory=list)
    mitre_attack: list[str] = field(default_factory=list)

    @property
    def sort_key(self) -> tuple[int, int, int]:
        """Return a (category, subcategory, index) tuple for stable ordering."""
        return (self.category, self.subcategory, self.index)


def _normalise_list(raw: Any) -> list[str]:
    """Coerce a JSON value to a clean list[str], preserving order."""
    if raw in (None, ""):
        return []
    if isinstance(raw, str):
        cleaned = raw.strip().strip(".")
        if not cleaned or cleaned.lower() in {"-", "n/a", "none"}:
            return []
        parts = [p.strip() for p in re.split(r"[,;/]\s*|\s+and\s+", cleaned) if p.strip()]
        return parts
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if item is None:
                continue
            text = str(item).strip()
            if text and text.lower() not in {"-", "n/a", "none"}:
                out.append(text)
        return out
    return []


def parse_sidecar(path: pathlib.Path, category_number: int) -> UseCase | None:
    """Parse one ``UC-X.Y.Z.json`` sidecar into a :class:`UseCase`."""
    try:
        with path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN: skipping unreadable sidecar {path}: {exc}", file=sys.stderr)
        return None

    uc_id_tail = payload.get("id") or path.stem.removeprefix("UC-")
    try:
        cat_str, sub_str, idx_str = uc_id_tail.split(".")
        cat, sub, idx = int(cat_str), int(sub_str), int(idx_str)
    except (ValueError, AttributeError):
        print(
            f"WARN: skipping sidecar {path} with malformed id '{uc_id_tail}'",
            file=sys.stderr,
        )
        return None

    if cat != category_number:
        print(
            f"WARN: sidecar {path} declares id {uc_id_tail} but lives under "
            f"cat-{category_number:02d}",
            file=sys.stderr,
        )

    return UseCase(
        uc_id=f"UC-{uc_id_tail}",
        category=cat,
        subcategory=sub,
        index=idx,
        title=str(payload.get("title", "")).strip(),
        source_file=str(path.relative_to(REPO)),
        source_line=1,
        criticality=str(payload.get("criticality", "")).strip(),
        difficulty=str(payload.get("difficulty", "")).strip(),
        monitoring_type=_normalise_list(payload.get("monitoringType", [])),
        splunk_pillar=str(payload.get("splunkPillar", "")).strip(),
        regulations=_normalise_list(payload.get("regulations", [])),
        mitre_attack=_normalise_list(payload.get("mitreAttack", [])),
    )


def discover_category_dirs() -> list[tuple[int, pathlib.Path]]:
    """Return (category_number, dir) pairs for ``content/cat-NN-*`` folders."""
    pairs: list[tuple[int, pathlib.Path]] = []
    for path in CONTENT_DIR.glob("cat-*"):
        if not path.is_dir():
            continue
        m = re.match(r"cat-(\d+)-", path.name)
        if not m:
            continue
        pairs.append((int(m.group(1)), path))
    pairs.sort(key=lambda pair: pair[0])
    return pairs


def parse_category(cat_dir: pathlib.Path, cat_num: int) -> Iterable[UseCase]:
    """Yield each UC parsed from ``cat_dir/UC-*.json`` sorted by filename."""
    for sidecar in sorted(cat_dir.glob("UC-*.json")):
        uc = parse_sidecar(sidecar, cat_num)
        if uc is not None:
            yield uc


def validate(ucs: list[UseCase]) -> list[str]:
    """Return a list of duplicate-UC error messages (empty when clean)."""
    errors: list[str] = []
    seen: dict[str, UseCase] = {}
    for uc in ucs:
        if uc.uc_id in seen:
            other = seen[uc.uc_id]
            errors.append(f"duplicate UC id {uc.uc_id}: {uc.source_file} vs {other.source_file}")
            continue
        seen[uc.uc_id] = uc
    return errors


def write_json(ucs: list[UseCase], path: pathlib.Path) -> None:
    """Write the canonical inventory JSON to ``path`` with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        # Keep the legacy regenerate hint in the emitted JSON for byte-stability;
        # the shim under scripts/inventory_ucs.py still works during the soak.
        "generatedAtComment": "Regenerate with python3 scripts/inventory_ucs.py",
        "schemaVersion": 1,
        "totalUseCases": len(ucs),
        "useCases": [asdict(uc) for uc in ucs],
    }
    with path.open("w", encoding="utf-8") as h:
        json.dump(payload, h, indent=2, ensure_ascii=False)
        h.write("\n")


def write_csv(ucs: list[UseCase], path: pathlib.Path) -> None:
    """Write the auditor-friendly CSV projection of the inventory to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(
            [
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
            ]
        )
        for uc in ucs:
            w.writerow(
                [
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
                ]
            )


def print_stats(ucs: list[UseCase]) -> None:
    """Print human-readable counters: per-category counts, top regulations."""
    by_cat: dict[int, int] = defaultdict(int)
    reg_counter: Counter[str] = Counter()
    with_regs = 0
    for uc in ucs:
        by_cat[uc.category] += 1
        if uc.regulations:
            with_regs += 1
            for r in uc.regulations:
                reg_counter[r] += 1
    total = max(len(ucs), 1)
    print(f"\nTotal UCs: {len(ucs)}")
    print(f"UCs with Regulations: tag: {with_regs} ({with_regs * 100 / total:.1f}% of {len(ucs)})")
    print("\nUCs per category:")
    for cat in sorted(by_cat):
        print(f"  cat-{cat:02d}: {by_cat[cat]}")
    print("\nTop regulation tags:")
    for reg, n in reg_counter.most_common(25):
        print(f"  {reg:40s}  {n}")


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` is consumed via argparse."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", action="store_true", help="print summary counters")
    ap.add_argument(
        "--out-dir",
        default=str(OUT_DIR),
        help="output directory (default: data/inventory/)",
    )
    args = ap.parse_args(argv)

    ucs: list[UseCase] = []
    for cat_num, cat_dir in discover_category_dirs():
        ucs.extend(parse_category(cat_dir, cat_num))
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
