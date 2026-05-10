"""Splunk fortune cookie -- pick a random monitoring use case from catalog.json.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/splunk_fortune.py to src/splunk_uc/tools/splunk_fortune.py.
parents[3] resolves: splunk_fortune.py -> tools/ -> splunk_uc/ ->
src/ -> repo root. The legacy ``parent.parent`` chain assumed depth
one and is now wrong by two levels. The legacy shim re-exports
``main`` so any direct CLI invocation still works during the soak
period.

Run from repo root::

    python -m splunk_uc splunk-fortune
    python -m splunk_uc splunk-fortune --count 3
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

COOKIE = r"""
     .--------.
    /  Your   /\
   /  SPLunk  /  \
  /  fortune  /   \
 '-----------'    '
  \  \  \  \  \  \  \
"""

FALLBACK: list[dict[str, Any]] = [
    {
        "n": "Emergency SPL",
        "c": "high",
        "v": "When in doubt, index=* | head 100",
        "q": "index=* | head 100",
    }
]


def load_catalog(path: Path) -> list[dict[str, Any]]:
    """Flatten ``catalog.json`` into a list of UC dicts annotated with ``_category``."""
    if not path.is_file():
        return FALLBACK
    with path.open(encoding="utf-8") as f:
        root = json.load(f)
    flat: list[dict[str, Any]] = []
    for block in root.get("DATA", []):
        for cat in block.get("s", []):
            cat_name = cat.get("n", "?")
            for uc in cat.get("u", []):
                uc["_category"] = cat_name
                flat.append(uc)
    return flat or FALLBACK


def fortune_line(uc: dict[str, Any]) -> str:
    """Render the headline line for one fortune (criticality emoji + path)."""
    crit = uc.get("c", "?")
    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(crit, "⚪")
    return f"{emoji} [{crit}] {uc.get('_category', '')} → {uc.get('n', 'Untitled')}"


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` is consumed via argparse."""
    ap = argparse.ArgumentParser(description="Random Splunk monitoring fortune from catalog.json")
    ap.add_argument("--count", "-n", type=int, default=1, help="How many fortunes (default 1)")
    ap.add_argument(
        "--catalog",
        type=Path,
        default=REPO_ROOT / "catalog.json",
        help="Path to catalog.json",
    )
    args = ap.parse_args(argv)

    use_cases = load_catalog(args.catalog)
    # ``random.sample`` here is non-CSPRNG by design: this is a
    # decorative fortune-cookie picker, not a security control. See
    # codeguard-1-crypto-algorithms (allowed for non-cryptographic use).
    picks = random.sample(use_cases, min(args.count, len(use_cases)))

    print(COOKIE)
    for uc in picks:
        print()
        print(fortune_line(uc))
        value = uc.get("v", "").strip()
        truncated = value[:200]
        ellipsis = "…" if len(uc.get("v", "")) > 200 else ""
        print(f"   {truncated}{ellipsis}")
        q = uc.get("q", "").strip()
        if q:
            print()
            print("   ── sample SPL ──")
            for line in q.split("\n")[:8]:
                print(f"   {line}")
            if q.count("\n") > 7:
                print("   …")
        print()

    print("  May your pipelines be fast and your _raw never truncated. 🥠\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
