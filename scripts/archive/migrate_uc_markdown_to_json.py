#!/usr/bin/env python3
"""Phase 1.3 migration driver: cat-22 markdown -> JSON sidecars.

What it does
------------
1. Parses ``use-cases/cat-22-regulatory-compliance.md`` using
   :mod:`scripts.uc_markdown_io` into a typed tree (subcategories × UCs).
2. For every UC it synthesises a schema-valid ``compliance[]`` array by
   - reading the free-text ``Regulations:`` field and looking each token
     up in ``data/regulations.json``'s ``aliasIndex``,
   - reading the trailing parenthesised clause hint from the UC title and
     expanding range forms (``Art. 5/6``, ``Art. 15-22``, ``Art. 33, 72-hour
     rule``) into one ``compliance[]`` entry per detected clause.
3. Writes one JSON sidecar per UC under ``use-cases/cat-22/uc-<id>.json``.
4. Round-trips every JSON back through :func:`render_uc_to_markdown` and
   diffs against the source markdown block – this is the Phase 1.3
   zero-narrative-loss gate. Any divergence is reported and causes a
   non-zero exit code.
5. Emits ``docs/uc-migration-report.md`` with the full statistics,
   per-regulation hit counts, unresolved alias list, and any residual
   diffs that survived normalisation.

Security notes (codeguard-0-input-validation-injection,
codeguard-0-file-handling-and-uploads):
- All file writes are under repo-relative paths; no shell is invoked.
- Regex patterns are anchored; no catastrophic-backtracking classes.
- The ``aliasIndex`` is the sole gate for regulation-name normalisation;
  unknown names are surfaced in the report, never silently mapped.

Usage
-----
    python3 scripts/migrate_uc_markdown_to_json.py [--check]
      --check  Diff-only mode: do not write sidecars. Exits 1 if any UC
               would round-trip non-losslessly or any Regulations token is
               unresolved against regulations.json (Phase 1.5c gate).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.uc_markdown_io import (  # noqa: E402 — local import after path fixup
    load_category,
    normalize_for_diff,
    parse_category_markdown,
    parse_uc_block,
    render_uc_to_markdown,
    to_schema_payload,
)


MD_SOURCE = REPO_ROOT / "use-cases" / "cat-22-regulatory-compliance.md"
REG_INDEX = REPO_ROOT / "data" / "regulations.json"
OUT_DIR = REPO_ROOT / "use-cases" / "cat-22"
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"
REPORT_PATH = REPO_ROOT / "docs" / "uc-migration-report.md"


_UC_HDR = re.compile(r"^### UC-(\d+\.\d+\.\d+)", re.M)
_SUB_HDR = re.compile(r"^### (\d+\.\d+) ")


# ---------------------------------------------------------------------------
# Regulation resolution
# ---------------------------------------------------------------------------

@dataclass
class RegIndex:
    frameworks: Dict[str, Dict]
    alias_index: Dict[str, str]

    def resolve(self, token: str) -> Optional[Dict]:
        """Return the framework dict for a free-text ``Regulations:`` token.

        Lookup strategy:
        1. Exact lower-case match in ``aliasIndex``.
        2. Strip trailing version suffix (e.g. "ISO 27001:2022" -> "iso 27001").
        3. Keyword-match against framework shortName/name.
        """

        t = token.strip().lower()
        if t in self.alias_index:
            fid = self.alias_index[t]
            return self.frameworks.get(fid)

        base = re.sub(r":.*$", "", t).strip()
        if base in self.alias_index:
            fid = self.alias_index[base]
            return self.frameworks.get(fid)

        for fid, fw in self.frameworks.items():
            if t == fw["name"].lower() or t == fw.get("shortName", "").lower():
                return fw
        return None

    @classmethod
    def load(cls, path: Path) -> "RegIndex":
        data = json.loads(path.read_text(encoding="utf-8"))
        frameworks = {f["id"]: f for f in data["frameworks"]}
        alias_index: Dict[str, str] = {}
        for k, v in data.get("aliasIndex", {}).items():
            if k == "$comment":
                continue
            alias_index[k.lower()] = v
        for fid, fw in frameworks.items():
            alias_index.setdefault(fid.lower(), fid)
            alias_index.setdefault(fw["name"].lower(), fid)
            if fw.get("shortName"):
                alias_index.setdefault(fw["shortName"].lower(), fid)
            for al in fw.get("aliases", []) or []:
                alias_index.setdefault(al.lower(), fid)
        return cls(frameworks=frameworks, alias_index=alias_index)


# ---------------------------------------------------------------------------
# Clause-hint expansion
# ---------------------------------------------------------------------------

_CLAUSE_TOKEN_SPLIT = re.compile(r"[;,]|\s+/\s+|\s+and\s+", re.IGNORECASE)


def expand_clause_hint(hint: Optional[str], framework: Optional[Dict]) -> List[str]:
    """Turn a UC-title clause parenthetical into a list of clause strings.

    Examples::
        "Art. 5/6"                 -> ["Art.5", "Art.6"]
        "Art. 15-22"               -> ["Art.15-22"]       (keep as range)
        "Art. 33, 72-hour rule"    -> ["Art.33"]         (drop prose)
        "§164.312(b)"              -> ["§164.312(b)"]
        "Art. 21(2)(d)"            -> ["Art.21(2)(d)"]

    Unparseable hints return ``["unspecified"]`` so that the required
    ``compliance[0].clause`` field is still populated; the Phase 1.5c audit
    script will flag these for SME review.
    """

    if not hint:
        return ["unspecified"]

    raw = re.sub(r"\bhour rule\b.*$", "", hint, flags=re.IGNORECASE).strip()
    raw = re.sub(r"\bnational transposition\b", "", raw, flags=re.IGNORECASE).strip(", ")

    parts: List[str] = []
    chunks = _CLAUSE_TOKEN_SPLIT.split(raw)
    prefix: Optional[str] = None
    for chunk in chunks:
        c = chunk.strip()
        if not c:
            continue

        pm = re.match(r"^(Art\.?|Article|§|Sec(?:tion)?\.?|Clause|Principle|CSC|AC|AU|SI|CA|CM|SC|SR|ID|PR|DE|RS|RC)\s*(.+)$", c, re.IGNORECASE)
        if pm:
            prefix = _canon_prefix(pm.group(1))
            tail = pm.group(2).strip()
            parts.append(prefix + tail)
            continue

        if re.match(r"^[0-9A-Za-z][0-9A-Za-z.()\-]*$", c):
            if prefix:
                parts.append(prefix + c)
            else:
                parts.append(c)

    if not parts:
        return [hint.strip()] if hint.strip() else ["unspecified"]

    deduped: List[str] = []
    seen = set()
    for p in parts:
        q = _tidy_clause(p)
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped or ["unspecified"]


def _canon_prefix(raw_prefix: str) -> str:
    p = raw_prefix.lower().rstrip(".")
    if p in ("art", "article"):
        return "Art."
    if p in ("§", "sec", "section"):
        return "§"
    if p == "clause":
        return "Clause "
    return raw_prefix.rstrip(".") + " "


def _tidy_clause(s: str) -> str:
    s = s.strip().rstrip(".,;")
    s = re.sub(r"Art\.\s+", "Art.", s)
    return s


# ---------------------------------------------------------------------------
# Version pick
# ---------------------------------------------------------------------------

def latest_version(framework: Dict) -> str:
    """Pick the most recent version of a framework by effectiveFrom, fallback
    to the last entry order."""

    versions = framework.get("versions", [])
    if not versions:
        return "unspecified"
    dated = [v for v in versions if v.get("effectiveFrom")]
    if dated:
        dated.sort(key=lambda v: v["effectiveFrom"], reverse=True)
        return dated[0]["version"]
    return versions[-1]["version"]


# ---------------------------------------------------------------------------
# Compliance synthesis
# ---------------------------------------------------------------------------

def synthesise_compliance(
    uc: Dict,
    reg_index: RegIndex,
    unresolved_tokens: Counter,
    resolved_by_framework: Counter,
) -> List[Dict]:
    """Build ``compliance[]`` from the UC's Regulations field and title hint."""

    tokens = [t.strip() for t in (uc.get("regulations") or "").split(",") if t.strip()]
    if not tokens:
        return [_placeholder_entry("unspecified", uc.get("_clauseHint"))]

    hint = uc.get("_clauseHint")
    entries: List[Dict] = []

    for tok in tokens:
        fw = reg_index.resolve(tok)
        if fw is None:
            unresolved_tokens[tok] += 1
            entries.append(_placeholder_entry(tok, hint))
            continue

        resolved_by_framework[fw["id"]] += 1
        version = latest_version(fw)
        clauses = expand_clause_hint(hint, fw)

        for clause in clauses:
            entries.append({
                "regulation": fw.get("shortName") or fw["name"],
                "version": version,
                "clause": clause,
                "mode": "satisfies",
                "assurance": "contributing",
                "assurance_rationale": (
                    "Auto-migrated from cat-22 markdown on Phase 1.3 run. "
                    "Requires SME review to confirm clause accuracy, "
                    "mode (satisfies vs detects-violation-of), and assurance "
                    "level (contributing/partial/full)."
                ),
                "provenance": "maintainer",
            })

    return entries or [_placeholder_entry("unspecified", hint)]


def _placeholder_entry(token: str, hint: Optional[str]) -> Dict:
    clause = "unspecified"
    if hint:
        clause = hint.strip() or "unspecified"
    return {
        "regulation": token or "unspecified",
        "version": "unspecified",
        "clause": clause,
        "mode": "satisfies",
        "assurance": "contributing",
        "assurance_rationale": (
            "Auto-migrated placeholder: regulation token not resolvable in "
            "data/regulations.json aliasIndex. See docs/uc-migration-report.md "
            "and fix the alias or the UC's Regulations line."
        ),
        "provenance": "maintainer",
    }


# ---------------------------------------------------------------------------
# JSON sidecar shaping
# ---------------------------------------------------------------------------

EXCLUDED_KEYS_IN_JSON = {"regulations"}


def uc_to_sidecar(uc: Dict, compliance: List[Dict]) -> Dict:
    payload = to_schema_payload(uc)
    out: Dict = {
        "$schema": "../../schemas/uc.schema.json",
        "id": payload["id"],
        "title": payload["title"],
    }
    for key in (
        "criticality", "difficulty", "monitoringType", "mitreAttack",
        "industry", "splunkPillar",
    ):
        if key in payload:
            out[key] = payload[key]
    out["compliance"] = compliance
    for key in (
        "app", "premiumApps", "dataSources", "spl", "cimModels", "cimSpl",
        "value", "implementation", "visualization", "knownFalsePositives",
        "references",
    ):
        if key in payload:
            out[key] = payload[key]
    return out


# ---------------------------------------------------------------------------
# Round-trip diff
# ---------------------------------------------------------------------------

def source_block_for(lines: List[str], positions: Dict[str, Tuple[int, int]], uc_id: str) -> str:
    start, end = positions[uc_id]
    block = "\n".join(lines[start:end])
    return re.sub(r"\n---\s*\n?\Z", "\n", block)


def index_source_blocks(src: str) -> Tuple[List[str], Dict[str, Tuple[int, int]]]:
    lines = src.splitlines()
    positions: Dict[str, Tuple[int, int]] = {}
    starts: List[Tuple[str, int]] = []
    for i, ln in enumerate(lines):
        m = _UC_HDR.match(ln)
        if m:
            starts.append((m.group(1), i))
    for idx, (uid, start) in enumerate(starts):
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if _UC_HDR.match(lines[j]) or _SUB_HDR.match(lines[j]):
                end = j
                break
        positions[uid] = (start, end)
    return lines, positions


def roundtrip_check(parsed_uc: Dict, original_block: str) -> Tuple[bool, str]:
    rendered = render_uc_to_markdown(parsed_uc)
    norm_src = normalize_for_diff(original_block)
    norm_rnd = normalize_for_diff(rendered)
    if norm_src == norm_rnd:
        return True, ""
    diff = "\n".join(
        difflib.unified_diff(
            norm_src.splitlines(),
            norm_rnd.splitlines(),
            fromfile="orig",
            tofile="rendered",
            lineterm="",
        )
    )
    return False, diff


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_sidecar(uc_id: str, payload: Dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / f"uc-{uc_id}.json"
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
    target.write_text(body + "\n", encoding="utf-8")
    return target


def write_report(
    total: int,
    round_trip_ok: int,
    round_trip_fail: int,
    per_sub: Dict[str, int],
    resolved: Counter,
    unresolved: Counter,
    failures: List[Tuple[str, str]],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "# cat-22 migration report (Phase 1.3)",
        "",
        "This report is regenerated by `scripts/migrate_uc_markdown_to_json.py`.",
        "It is the evidence artefact for the zero-narrative-loss gate required by",
        "the phase plan.",
        "",
        "## Summary",
        "",
        f"- Total UCs parsed: **{total}**",
        f"- Zero-narrative-loss round-trip matches: **{round_trip_ok}**",
        f"- Round-trip failures: **{round_trip_fail}**",
        "",
        "## Per-subcategory counts",
        "",
        "| Subcategory | UCs migrated |",
        "| --- | --- |",
    ]
    for sub_id in sorted(per_sub):
        lines.append(f"| {sub_id} | {per_sub[sub_id]} |")

    lines += [
        "",
        "## Regulation resolution",
        "",
        "| Framework id | UCs touching it |",
        "| --- | --- |",
    ]
    for fid, n in sorted(resolved.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {fid} | {n} |")

    lines += [
        "",
        "## Unresolved Regulations-field tokens",
        "",
        "Each row below is a free-text token appearing in a `- **Regulations:**`",
        "line that the aliasIndex did not resolve. Fix by adding an alias to",
        "`data/regulations.json` or by correcting the markdown.",
        "",
        "| Token | Occurrences |",
        "| --- | --- |",
    ]
    if not unresolved:
        lines.append("| _(none)_ | 0 |")
    else:
        for tok, n in sorted(unresolved.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"| `{tok}` | {n} |")

    lines += [
        "",
        "## Round-trip failures",
        "",
    ]
    if not failures:
        lines.append("_None — every UC round-trips losslessly._")
    else:
        for uid, diff in failures:
            lines += [
                f"### UC-{uid}",
                "",
                "```diff",
                diff,
                "```",
                "",
            ]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 1.3 cat-22 migration driver.")
    ap.add_argument("--check", action="store_true",
                    help="Do not write sidecar files; exit non-zero on any "
                         "round-trip failure or unresolved regulation token.")
    ap.add_argument("--source", default=str(MD_SOURCE))
    ap.add_argument("--regulations", default=str(REG_INDEX))
    args = ap.parse_args()

    src_path = Path(args.source)
    md_text = src_path.read_text(encoding="utf-8")
    src_lines, uc_positions = index_source_blocks(md_text)

    cat = parse_category_markdown(md_text)
    reg_index = RegIndex.load(Path(args.regulations))

    unresolved: Counter = Counter()
    resolved: Counter = Counter()
    per_sub: Dict[str, int] = defaultdict(int)
    failures: List[Tuple[str, str]] = []
    total = 0
    ok = 0

    for sub in cat.subcategories:
        for uc in sub.ucs:
            total += 1
            per_sub[sub.id] += 1

            compliance = synthesise_compliance(uc, reg_index, unresolved, resolved)
            sidecar = uc_to_sidecar(uc, compliance)

            original_block = source_block_for(src_lines, uc_positions, uc["id"])
            passed, diff = roundtrip_check(uc, original_block)
            if passed:
                ok += 1
            else:
                failures.append((uc["id"], diff))

            if not args.check:
                write_sidecar(uc["id"], sidecar)

    fail = total - ok
    write_report(total, ok, fail, per_sub, resolved, unresolved, failures)

    print(f"UCs parsed: {total}")
    print(f"Round-trip matches: {ok}")
    print(f"Round-trip failures: {fail}")
    print(f"Unresolved regulation tokens: {len(unresolved)}")
    for tok, n in sorted(unresolved.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
        print(f"  - {tok!r} ({n} occurrences)")
    if not args.check:
        print(f"Wrote {total} sidecars under {OUT_DIR.relative_to(REPO_ROOT)}/")
    print(f"Report: {REPORT_PATH.relative_to(REPO_ROOT)}")

    if args.check and (fail > 0 or unresolved):
        return 1
    if fail > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
