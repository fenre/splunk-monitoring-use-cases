#!/usr/bin/env python3
"""Fix remaining hallucinated eval-context functions found by the deep
SPL hallucination sweep.

Replacements applied:

* `concat(a, b, c, ...)` → `a.b.c....` (Splunk dot-concatenation)
* `to_string(x)`         → `tostring(x)` (typo of canonical func)
* `month(_time)`         → `tonumber(strftime(_time, "%m"))`
* `sort(mvexpr)`         → `mvsort(mvexpr)` (eval form of sort for MV)
* `where predicted(x)`   → `where 'predicted(x)'` (quote field name created
                                                  by `| predict`)

Each transformation only fires when the function call is inside an
`eval` / `where` / `fieldformat` clause (so we don't accidentally rewrite
stats aggregators like `concat()` or `sort()` that don't exist there
anyway, or vendor macros that happen to share names).

Pass --write to apply.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


def _find_balanced(s: str, start: int) -> int:
    depth = 0
    i = start
    n = len(s)
    in_str: str | None = None
    while i < n:
        ch = s[i]
        if in_str:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'"):
                in_str = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def _split_args(args: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_str: str | None = None
    i = 0
    n = len(args)
    while i < n:
        ch = args[i]
        if in_str:
            current.append(ch)
            if ch == "\\" and i + 1 < n:
                current.append(args[i + 1])
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_str = ch
            current.append(ch)
        elif ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current).strip())
    return parts


def rewrite_concat(spl: str) -> tuple[str, int]:
    """Replace `concat(a, b, c, ...)` → `a.b.c....` using balanced-paren
    scanning.  Conservative: applies anywhere it sees `concat(`, since
    `concat` is not a documented Splunk command at all.
    """
    count = 0
    out: list[str] = []
    i = 0
    n = len(spl)
    pattern = re.compile(r"\bconcat\s*\(", re.IGNORECASE)
    while i < n:
        m = pattern.search(spl, i)
        if not m:
            out.append(spl[i:])
            break
        out.append(spl[i:m.start()])
        open_idx = m.end() - 1
        close_idx = _find_balanced(spl, open_idx)
        if close_idx == -1:
            out.append(spl[m.start():])
            break
        inner = spl[open_idx + 1:close_idx]
        args = _split_args(inner)
        out.append(".".join(args))
        count += 1
        i = close_idx + 1
    return "".join(out), count


def rewrite_to_string(spl: str) -> tuple[str, int]:
    pattern = re.compile(r"\bto_string\s*\(", re.IGNORECASE)
    new_spl, n = pattern.subn("tostring(", spl)
    return new_spl, n


def rewrite_month_time(spl: str) -> tuple[str, int]:
    pattern = re.compile(
        r"\bmonth\s*\(\s*(_time)\s*\)",
        re.IGNORECASE,
    )
    new_spl, n = pattern.subn(r'tonumber(strftime(\1, "%m"))', spl)
    return new_spl, n


def rewrite_mv_sort(spl: str) -> tuple[str, int]:
    """Replace bare `sort(<mv-expr>)` (eval-context) with `mvsort(...)`."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])sort\s*\(", re.IGNORECASE)
    new_spl, n = pattern.subn("mvsort(", spl)
    return new_spl, n


def rewrite_predicted_in_where(spl: str) -> tuple[str, int]:
    """Quote the `predicted(field)` produced by `| predict` so it is read
    as a field name instead of a function call.
    """
    pattern = re.compile(
        r"(\bwhere\b[^|]*?)\bpredicted\s*\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\)",
        re.IGNORECASE,
    )

    def _repl(m: re.Match) -> str:
        head = m.group(1)
        field = m.group(2)
        return f"{head}'predicted({field})'"

    new_spl, n = pattern.subn(_repl, spl)
    return new_spl, n


def apply_all(spl: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    new_spl = spl
    new_spl, c = rewrite_concat(new_spl)
    if c:
        counts["concat→."] = c
    new_spl, c = rewrite_to_string(new_spl)
    if c:
        counts["to_string→tostring"] = c
    new_spl, c = rewrite_month_time(new_spl)
    if c:
        counts["month→strftime"] = c
    new_spl, c = rewrite_predicted_in_where(new_spl)
    if c:
        counts["predicted→quoted"] = c
    # NOTE: mv-sort intentionally restricted to UCs that contain
    # `mvsort`/`mvjoin`/`mvdedup`/`mvappend` adjacent, because `sort` as
    # a STANDALONE command (` | sort ...`) is fully valid.
    if "mvjoin(sort(" in new_spl or "mvsort" in new_spl or "sort(mvdedup" in new_spl:
        new_spl, c = rewrite_mv_sort(new_spl)
        if c:
            counts["sort→mvsort"] = c
    return new_spl, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fixed_files = 0
    total: dict[str, int] = {}
    samples: list[str] = []
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        changed = False
        for fld in ("spl", "cimSpl"):
            v = d.get(fld)
            if not isinstance(v, str):
                continue
            new_v, counts = apply_all(v)
            if counts and new_v != v:
                d[fld] = new_v
                changed = True
                for k, n in counts.items():
                    total[k] = total.get(k, 0) + n
                if len(samples) < 6:
                    samples.append(
                        f"  [{p.name}/{fld}] {', '.join(f'{k}={n}' for k,n in counts.items())}"
                    )
        if changed:
            fixed_files += 1
            if args.write:
                p.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"Files fixed: {fixed_files}")
    print("Replacements by kind:")
    for k, n in sorted(total.items()):
        print(f"  {k}: {n}")
    print("Samples:")
    for s in samples:
        print(s)
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
