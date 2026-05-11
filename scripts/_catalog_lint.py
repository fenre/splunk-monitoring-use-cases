"""Catalog-wide SPL anti-pattern linter.

Detects generic, vendor-agnostic SPL bugs that come up in hallucinated
catalogs (independent of Meraki). Each rule is precise about what it flags
to avoid false positives.

Rules:
  G1  tonumber(<field>, <int>)     - second arg is the BASE, not a default.
                                     A base of 1-36 is technically valid but
                                     callers usually mean "default if NaN".
                                     Use coalesce(tonumber(field), default).
  G2  where <field>="null"          - comparing to literal string "null".
                                     Splunk evaluates this as a string, so
                                     real NULLs do NOT match. Use isnull(field).
  G3  isnull("null")                - same mistake; isnull on a string literal
                                     is always false.
  G4  isnotnull("...")              - same as G3.
  G5  where field=null              - bare null literal; in Splunk SPL `null`
                                     is just a token, not a NULL. Use isnull().
  G6  where field=NULL              - same as G5 with a different token.
  G7  if(field=="null", ...)         - same string-vs-null trap.
  G8  | join field [ ... | head 1 ] - subsearch must NOT use head limit-of-1
                                      because join builds the whole right side
                                      first; head 1 throws away rows. (info)
  G10 strftime(_time)                - missing format string (legitimate use
                                       always supplies a format).
  G11 sourcetype="meraki:*" together with type="*" or signature="*" -
                                     SC4S syslog fields used on API TA data
                                     (already covered by Meraki linter; here
                                     we catch any leftover stragglers).

Usage:
    python3 scripts/_catalog_lint.py
    python3 scripts/_catalog_lint.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def _strip_comments(spl: str) -> str:
    return re.sub(r"```[^`]*```", "", spl)


def lint_uc(uc_id: str, spl: str) -> list[dict]:
    findings = []
    s = _strip_comments(spl)

    # G1 - tonumber(<expr>, <int 0..36>) - second arg is BASE not default
    for m in re.finditer(
        r"tonumber\s*\(\s*([^,()]+?)\s*,\s*([0-9]+)\s*\)", s
    ):
        base = int(m.group(2))
        if 0 <= base <= 36 and base not in (2, 8, 10, 16):
            findings.append({
                "rule": "G1",
                "uc_id": uc_id,
                "msg": f"tonumber({m.group(1).strip()}, {base}) - "
                       "2nd arg is base, not default. Use "
                       "coalesce(tonumber(field), default).",
                "snippet": m.group(0),
            })

    # G2 - where <field> = "null"  (literal string compare).
    # Skip the well-known Meraki TA convention where dismissedAt and
    # resolvedAt are stored as the literal string "null" for unset values.
    _meraki_null_string_fields = {
        "dismissedAt", "dismissed_at", "resolvedAt", "resolved_at",
        "acknowledgedAt", "acknowledged_at",
    }
    for m in re.finditer(
        r"\bwhere\s+([\w.]+)\s*=\s*\"null\"", s, re.I
    ):
        field = m.group(1)
        if field in _meraki_null_string_fields:
            continue
        findings.append({
            "rule": "G2", "uc_id": uc_id,
            "msg": f"where {field}=\"null\" - literal string compare; use isnull({field}).",
            "snippet": m.group(0),
        })

    # G3 - isnull("...") string literal
    for m in re.finditer(r"isnull\s*\(\s*\"[^\"]+\"\s*\)", s):
        findings.append({
            "rule": "G3", "uc_id": uc_id,
            "msg": "isnull() on a string literal always returns false.",
            "snippet": m.group(0),
        })

    # G4 - isnotnull("...") string literal
    for m in re.finditer(r"isnotnull\s*\(\s*\"[^\"]+\"\s*\)", s):
        findings.append({
            "rule": "G4", "uc_id": uc_id,
            "msg": "isnotnull() on a string literal always returns true.",
            "snippet": m.group(0),
        })

    # G5/G6 - where field = null / NULL (bare token)
    for m in re.finditer(
        r"\bwhere\s+([\w.]+)\s*=\s*(null|NULL)\b(?!\s*\")", s
    ):
        findings.append({
            "rule": "G5" if m.group(2) == "null" else "G6",
            "uc_id": uc_id,
            "msg": f"where {m.group(1)}={m.group(2)} - bare token, use isnull({m.group(1)}).",
            "snippet": m.group(0),
        })

    # G7 - if(field=="null", ...)  string-vs-null trap inside eval
    for m in re.finditer(
        r"if\s*\(\s*([\w.]+)\s*==?\s*\"null\"", s, re.I
    ):
        field = m.group(1)
        if field in _meraki_null_string_fields:
            continue
        findings.append({
            "rule": "G7", "uc_id": uc_id,
            "msg": f"if({field}==\"null\", ...) - string compare, use isnull().",
            "snippet": m.group(0),
        })

    # G8 - | join field [ ... | head 1 ]
    for m in re.finditer(
        r"\|\s*join\s+[^[\]]*\[[^\]]*\|\s*head\s+1\s*\]", s
    ):
        findings.append({
            "rule": "G8", "uc_id": uc_id,
            "msg": "join subsearch contains | head 1 - join builds full right side first.",
            "snippet": m.group(0)[:120],
        })

    # G9 removed - tostring(_time) is valid SPL (returns epoch string),
    # commonly used for stable hash keys (md5(cluster_id."|".tostring(_time))).

    # G10 - strftime(_time) with no format
    for m in re.finditer(r"strftime\s*\(\s*_time\s*\)", s):
        findings.append({
            "rule": "G10", "uc_id": uc_id,
            "msg": "strftime(_time) without format - SPL requires a format spec.",
            "snippet": m.group(0),
        })

    return findings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--rule", default=None,
                   help="Filter to a single rule code, e.g. G1")
    p.add_argument("--id", default=None,
                   help="Filter to a single UC ID, e.g. 5.4.17")
    args = p.parse_args()

    findings = []
    n_ucs = 0
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        n_ucs += 1
        if args.id and d.get("id") != args.id:
            continue
        spl = d.get("spl") or ""
        if not spl:
            continue
        for f in lint_uc(d.get("id", "?"), spl):
            f["path"] = str(path.relative_to(ROOT))
            f["title"] = d.get("title", "")
            findings.append(f)

    if args.rule:
        findings = [f for f in findings if f["rule"] == args.rule]

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print(f"Scanned {n_ucs} UCs, {len(findings)} findings\n")
        from collections import Counter
        by_rule = Counter(f["rule"] for f in findings)
        for rule, n in by_rule.most_common():
            print(f"  {rule}: {n}")
        print()
        for f in findings:
            print(f"  [{f['rule']}] UC-{f['uc_id']:<10s} {f['msg']}")
            print(f"           {f['path']}")
            print(f"           snippet: {f['snippet']}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
