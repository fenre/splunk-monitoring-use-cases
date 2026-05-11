"""Auto-fix sourcetype hallucinations in catalog UCs.

Reads the same hallucination map as scripts/_catalog_st_audit.py and
performs whole-token replacements in `spl`, `dataSources`, and the
Configure-data-collection / Create-the-search portions of
`detailedImplementation`.

Whole-token only (boundary on character class) so we never touch parts
of unrelated identifiers.

Usage:
    python3 scripts/_catalog_st_fix.py            # dry run
    python3 scripts/_catalog_st_fix.py --apply    # write changes
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _catalog_st_audit import HALLUCINATIONS  # noqa: E402

CONTENT = ROOT / "content"


def replace_token(text: str, wrong: str, canonical: str) -> tuple[str, int]:
    """Replace `wrong` with `canonical` only when not embedded in a longer
    identifier. Token boundary = anything other than [\\w:.\\-]."""
    pat = re.compile(
        r'(?<![\w:.\-])' + re.escape(wrong) + r'(?![\w:.\-])',
        re.I,
    )
    new_text, n = pat.subn(canonical, text)
    return new_text, n


SKIP = {
    "ms:o365:dlp",  # Needs additional Workload=Dlp filter; handled manually.
}


def fix_uc(d: dict) -> tuple[dict, list[tuple[str, str, int]]]:
    fixes = []
    for wrong, (canonical, _ta, _why) in HALLUCINATIONS.items():
        if wrong in SKIP:
            continue
        for fld in ("spl", "dataSources", "implementation",
                    "detailedImplementation"):
            v = d.get(fld)
            if not isinstance(v, str) or not v:
                continue
            new_v, n = replace_token(v, wrong, canonical)
            if n > 0:
                d[fld] = new_v
                fixes.append((wrong, canonical, n))
    return d, fixes


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true",
                    help="Write changes back to disk")
    p.add_argument("--id", default=None,
                    help="Restrict to a single UC ID")
    args = p.parse_args()

    n_files = 0
    n_changed = 0
    n_total = 0
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        n_files += 1
        if args.id and d.get("id") != args.id:
            continue
        before = json.dumps(d, sort_keys=True)
        new_d, fixes = fix_uc(d)
        after = json.dumps(new_d, sort_keys=True)
        if not fixes:
            continue
        n_changed += 1
        n_total += sum(n for _, _, n in fixes)
        print(f"UC-{d.get('id', '?')}  {path.relative_to(ROOT)}")
        for wrong, canonical, n in fixes:
            print(f"    {n}x  {wrong}  ->  {canonical}")
        if args.apply and before != after:
            with open(path, "w") as f:
                json.dump(new_d, f, indent=2, ensure_ascii=False)
                f.write("\n")
    print()
    print(f"Files scanned : {n_files}")
    print(f"Files changed : {n_changed}")
    print(f"Total token replacements: {n_total}")
    if not args.apply:
        print("\n(dry run - re-run with --apply to write changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
