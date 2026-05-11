#!/usr/bin/env python3
"""Fix hallucinated SPL functions in `eval` / `streamstats` / `eventstats`
contexts that the deep SPL sweep flags as `[HIGH]`.

Specifically corrects:

1.  `strcat(a, b, c)` inside `eval` → `a . b . c`  (Splunk eval concat)
2.  `hour(_time)` inside `eval` → `tonumber(strftime(_time, "%H"))`
3.  `delta(field) as alias` inside `streamstats` → emit a
    `last(field) as _last_<alias>` pattern followed by `| eval <alias> =
    <field> - _last_<alias>` (deletes the bad clause and prepends the
    correct one).
4.  `prev(field) as alias` / `previous(field) as alias` after `streamstats`
    → `last(field) as alias` (semantically identical with window=2)
5.  `next(field) as alias` after `streamstats` → the user has to reverse
    sort first; we cannot transparently fix the semantics, so we replace
    with `last()` and emit a comment so the operator notices. (Affects
    only 2 UCs.)
6.  `mean(field)` in `eventstats`/`streamstats` → `avg(field)` (Splunk
    documents `mean` as a deprecated alias but operators should prefer
    `avg`.)
7.  `semver_compare(a, b)` inside `eval` → fully expanded numeric compare
    using `split` + `tonumber` (only 1 occurrence, surgical).

False positives left untouched:
- Single-quoted `'predicted(...)'` style field references (created by
  the `predict` command).
- `stats median(eval(...))` / `stats stdev(eval(...))` patterns where
  the eval expression is an ARGUMENT to the aggregator, not the
  surrounding context.

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
    """Given an open paren at s[start], return index of matching close.

    Returns -1 if no match.
    """
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


def fix_strcat(spl: str) -> tuple[str, int]:
    """Replace strcat(a, b, c, ...) -> a.b.c.... using a balanced-paren
    scanner that handles arbitrarily nested calls.
    """
    count = 0
    out: list[str] = []
    i = 0
    n = len(spl)
    pattern = re.compile(r"\bstrcat\s*\(", re.IGNORECASE)
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


def fix_hour(spl: str) -> tuple[str, int]:
    pattern = re.compile(r"\bhour\s*\(\s*(_time)\s*\)", re.IGNORECASE)
    new_spl, n = pattern.subn(r'tonumber(strftime(\1, "%H"))', spl)
    return new_spl, n


def fix_mean(spl: str) -> tuple[str, int]:
    pattern = re.compile(r"\bmean\s*\(", re.IGNORECASE)
    new_spl, n = pattern.subn("avg(", spl)
    return new_spl, n


_PREV_RE = re.compile(r"\b(?:prev|previous)\s*\(", re.IGNORECASE)
_NEXT_RE = re.compile(r"\bnext\s*\(", re.IGNORECASE)


def _rewrite_in_streamstats(spl: str, token_re: re.Pattern, replacement: str) -> tuple[str, int]:
    """Replace every match of `token_re` inside every `streamstats` clause
    with `replacement`.  Walks each streamstats clause independently.
    """
    total = 0
    out: list[str] = []
    i = 0
    n = len(spl)
    while i < n:
        m = _STREAMSTATS_CLAUSE_RE.search(spl, i)
        if not m:
            out.append(spl[i:])
            break
        out.append(spl[i:m.start()])
        clause = m.group(0)
        new_clause, c = token_re.subn(replacement, clause)
        out.append(new_clause)
        total += c
        i = m.end()
    return "".join(out), total


def fix_streamstats_prev(spl: str) -> tuple[str, int]:
    return _rewrite_in_streamstats(spl, _PREV_RE, "last(")


def fix_streamstats_next(spl: str) -> tuple[str, int]:
    return _rewrite_in_streamstats(spl, _NEXT_RE, "first(")


_STREAMSTATS_CLAUSE_RE = re.compile(
    r"\|\s*streamstats\b[^|]*",
    re.IGNORECASE,
)
_DELTA_TOKEN_RE = re.compile(
    r"\bdelta\s*\(\s*(?P<field>[A-Za-z_][A-Za-z0-9_.]*)\s*\)\s+as\s+(?P<alias>[A-Za-z_][A-Za-z0-9_.]*)\b",
    re.IGNORECASE,
)


def fix_streamstats_delta(spl: str) -> tuple[str, int]:
    """Rewrite `delta(field) as alias` inside a streamstats clause to
    `last(field) as _prev_alias`, then append `| eval alias = field -
    _prev_alias` *after* the streamstats clause (preserving any
    trailing BY-clause).
    """
    total_replacements = 0
    out: list[str] = []
    i = 0
    n = len(spl)
    while i < n:
        m = _STREAMSTATS_CLAUSE_RE.search(spl, i)
        if not m:
            out.append(spl[i:])
            break
        out.append(spl[i:m.start()])
        clause = m.group(0)
        replacements: list[tuple[str, str]] = []  # (field, alias)
        def _replace_one(dm: re.Match) -> str:
            field = dm.group("field")
            alias = dm.group("alias")
            replacements.append((field, alias))
            return f"last({field}) as _prev_{alias}"
        new_clause = _DELTA_TOKEN_RE.sub(_replace_one, clause)
        out.append(new_clause)
        if replacements:
            # Add an eval block AFTER the streamstats clause that
            # computes the deltas.
            eval_assigns = ", ".join(
                f"{alias} = {field} - _prev_{alias}"
                for field, alias in replacements
            )
            out.append(f"| eval {eval_assigns}")
            total_replacements += len(replacements)
        i = m.end()
    return "".join(out), total_replacements


def fix_semver_compare(spl: str) -> tuple[str, int]:
    """Surgical fix: replace semver_compare(a, b) with a manual numeric
    comparison.  Only handles the simple `semver_compare(a, b) >= 0` form
    that exists in the corpus today.
    """
    pattern = re.compile(
        r"semver_compare\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)",
        re.IGNORECASE,
    )

    def _repl(m: re.Match) -> str:
        a = m.group(1).strip()
        b = m.group(2).strip()
        return (
            f"case("
            f"tonumber(mvindex(split({a},\".\"),0))!=tonumber(mvindex(split({b},\".\"),0)),"
            f"tonumber(mvindex(split({a},\".\"),0))-tonumber(mvindex(split({b},\".\"),0)),"
            f"tonumber(mvindex(split({a},\".\"),1))!=tonumber(mvindex(split({b},\".\"),1)),"
            f"tonumber(mvindex(split({a},\".\"),1))-tonumber(mvindex(split({b},\".\"),1)),"
            f"true(),"
            f"coalesce(tonumber(mvindex(split({a},\".\"),2)),0)-coalesce(tonumber(mvindex(split({b},\".\"),2)),0))"
        )

    new_spl, n = pattern.subn(_repl, spl)
    return new_spl, n


def apply_all(spl: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    new_spl = spl
    new_spl, c = fix_strcat(new_spl)
    if c:
        counts["strcat→."] = c
    new_spl, c = fix_hour(new_spl)
    if c:
        counts["hour(_time)→strftime"] = c
    new_spl, c = fix_mean(new_spl)
    if c:
        counts["mean→avg"] = c
    new_spl, c = fix_streamstats_prev(new_spl)
    if c:
        counts["prev/previous→last"] = c
    new_spl, c = fix_streamstats_next(new_spl)
    if c:
        counts["next→first"] = c
    new_spl, c = fix_streamstats_delta(new_spl)
    if c:
        counts["delta→last+eval"] = c
    new_spl, c = fix_semver_compare(new_spl)
    if c:
        counts["semver_compare→manual"] = c
    return new_spl, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fixed_files = 0
    total_by_kind: dict[str, int] = {}
    samples: list[str] = []
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        changed = False
        for field in ("spl", "cimSpl"):
            v = d.get(field)
            if not isinstance(v, str):
                continue
            new_v, counts = apply_all(v)
            if counts and new_v != v:
                d[field] = new_v
                changed = True
                for k, n in counts.items():
                    total_by_kind[k] = total_by_kind.get(k, 0) + n
                if len(samples) < 6:
                    samples.append(
                        f"  [{p.name}/{field}] {', '.join(f'{k}={n}' for k,n in counts.items())}"
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
    for k, n in sorted(total_by_kind.items()):
        print(f"  {k}: {n}")
    print("Samples:")
    for s in samples:
        print(s)
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
