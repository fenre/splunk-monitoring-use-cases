#!/usr/bin/env python3
"""Audit SPL grammar in use-cases/cat-*.md for patterns that don't parse or execute.

Covers patterns that `audit_spl_hallucinations.py` misses because they are
syntactically well-formed by command name but semantically or contextually broken:

1. `stats ... span=...`  — `span=` is only valid on `bin`/`timechart`/`tstats` context,
   not on `stats`.  Detects it even when embedded deep in a pipeline.
2. Leading `|` at the very start of a code fence (not valid as a standalone
   search — must have a generating command or be inside a subsearch).
3. Multiple top-level `index=` / `search index=` commands glued together with
   `| comment("...")` — these are multi-search artefacts, not one search.
4. `case(<literal-with-asterisk>, ...)` where the asterisk is being treated as
   a literal string but the author clearly intended a wildcard match (use
   `match()`/`like()` instead).
5. Invalid `streamstats current=` / `streamstats reset_after=` flags — Splunk
   supports `current=t/f`, `reset_after=<predicate>` but common errors include
   `current=` with a duration value.

Each finding includes severity, UC id, pattern category, and a short snippet.

Usage:
    python scripts/audit_spl_grammar.py            # human report
    python scripts/audit_spl_grammar.py --check    # non-zero exit on any HIGH finding
    python scripts/audit_spl_grammar.py --json     # machine-readable

Intended to be wired into .github/workflows/validate.yml.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES = os.path.join(REPO_ROOT, "use-cases", "cat-*.md")

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE)
RE_SPL_FENCE = re.compile(r"```spl\n(.*?)\n```", re.DOTALL)


@dataclass
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    message: str
    snippet: str = ""

    def human(self) -> str:
        s = f"[{self.severity}] [{self.category}] {self.uc_id} ({os.path.basename(self.file)}): {self.message}"
        if self.snippet:
            s += f"\n        snippet: {self.snippet.strip()[:140]}"
        return s


def _iter_uc_blocks(text: str) -> Iterable[Tuple[str, str, int, int]]:
    matches = list(RE_UC_HEAD.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield uc_id, text[start:end], start, end


def _iter_spl_blocks(body: str) -> Iterable[str]:
    for m in RE_SPL_FENCE.finditer(body):
        yield m.group(1)


def _strip_comments(spl: str) -> str:
    """Remove `comment("...")` segments for parsing-only purposes."""
    def remove_balanced(text: str, open_tok: str) -> str:
        out: list[str] = []
        i, n = 0, len(text)
        while i < n:
            idx = text.find(open_tok, i)
            if idx < 0:
                out.append(text[i:])
                break
            out.append(text[i:idx])
            j = idx + len(open_tok)
            depth = 1
            in_dq = in_sq = False
            while j < n and depth > 0:
                c = text[j]
                if in_dq:
                    if c == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if c == '"':
                        in_dq = False
                elif in_sq:
                    if c == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if c == "'":
                        in_sq = False
                else:
                    if c == '"':
                        in_dq = True
                    elif c == "'":
                        in_sq = True
                    elif c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                j += 1
            i = j
        return "".join(out)

    return remove_balanced(spl, "comment(")


_TOKEN_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_.:]*(?:\|[A-Za-z_]+)?\$")


def _split_pipes(spl: str) -> List[str]:
    """Split on unquoted, untokenised `|` at segment boundaries."""
    masked = _TOKEN_RE.sub(lambda m: "\x00" * len(m.group(0)), spl)
    segments: list[str] = []
    buf: list[str] = []
    in_dq = in_sq = False
    depth = 0
    for c in masked:
        if c == "\x00":
            buf.append("X")
            continue
        if in_dq:
            if c == '"':
                in_dq = False
            buf.append(c)
            continue
        if in_sq:
            if c == "'":
                in_sq = False
            buf.append(c)
            continue
        if c == '"':
            in_dq = True
            buf.append(c)
            continue
        if c == "'":
            in_sq = True
            buf.append(c)
            continue
        if c == "(":
            depth += 1
            buf.append(c)
            continue
        if c == ")":
            depth -= 1
            buf.append(c)
            continue
        if c == "|" and depth == 0:
            segments.append("".join(buf).strip())
            buf = []
            continue
        buf.append(c)
    if buf:
        segments.append("".join(buf).strip())
    return segments


# ------- Individual checks --------------------------------------------------

_RE_STATS_CMD = re.compile(r"^(?:si)?stats\b", re.IGNORECASE)
_RE_SPAN_KW = re.compile(r"\bspan\s*=", re.IGNORECASE)
_RE_EVENTSTATS = re.compile(r"^eventstats\b", re.IGNORECASE)
_RE_STREAMSTATS = re.compile(r"^streamstats\b", re.IGNORECASE)


def check_stats_span(uc_id: str, file: str, spl: str) -> List[Finding]:
    """Flag `stats ... span=` (invalid — span belongs on bin/timechart/tstats)."""
    cleaned = _strip_comments(spl)
    findings: List[Finding] = []
    for seg in _split_pipes(cleaned):
        if _RE_STATS_CMD.match(seg) and _RE_SPAN_KW.search(seg):
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="HIGH",
                    category="stats-span-invalid",
                    message=(
                        "`stats ... span=` is invalid. `span=` belongs on `bin`, "
                        "`timechart`, or inside `tstats`. Rewrite as "
                        "`| bin _time span=<N> | stats ... by ... _time` or use `timechart span=...`."
                    ),
                    snippet=seg[:160],
                )
            )
        # Same bug appears on eventstats/streamstats
        elif _RE_EVENTSTATS.match(seg) and _RE_SPAN_KW.search(seg):
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="HIGH",
                    category="stats-span-invalid",
                    message="`eventstats ... span=` is invalid (same as stats).",
                    snippet=seg[:160],
                )
            )
        elif _RE_STREAMSTATS.match(seg) and _RE_SPAN_KW.search(seg):
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="HIGH",
                    category="stats-span-invalid",
                    message=(
                        "`streamstats ... span=` is not valid Splunk. Use `window=<N>` "
                        "or pre-bin with `| bin _time span=<N>` and use `by _time`."
                    ),
                    snippet=seg[:160],
                )
            )
    return findings


_GENERATING_COMMANDS = frozenset({
    # Core Splunk generating commands
    "tstats", "mstats", "metadata", "metasearch", "rest", "inputlookup",
    "datamodel", "from", "dbinspect", "loadjob", "makeresults", "savedsearch",
    "mcollect", "search", "mcatalog", "pivot", "gentimes", "typeahead",
    "dbinspect", "folderize", "walklex", "geomfilter", "multisearch",
    # ES-specific
    "es_notable", "`es_notable`",
    # Splunk DB Connect (dbxquery generates rows from an external DB)
    "dbxquery",
    # MLTK
    "sample",
    # Splunkbase custom / widely-used generators
    "snowincident", "snowevent", "snowrequest",
    # `| comment "..."` is decorative — valid leading only if followed by
    # a real search segment.  We treat it separately.
})


def check_leading_pipe(uc_id: str, file: str, spl: str) -> List[Finding]:
    """Flag a leading `|` at the very start of the block unless the first segment is
    a known generating command that is *supposed* to start with `|`."""
    cleaned = spl.lstrip()
    if not cleaned.startswith("|"):
        return []
    segs = _split_pipes(cleaned.lstrip("|").strip())
    if not segs:
        return []
    # Skip leading `| comment "..."` decorative segments
    idx = 0
    while idx < len(segs) and segs[idx].strip().lower().startswith("comment"):
        idx += 1
    if idx >= len(segs):
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="HIGH",
                category="leading-pipe-invalid",
                message="Block contains only `| comment` segments — no actual search.",
                snippet=cleaned[:160],
            )
        ]
    first_seg = segs[idx].strip()
    # `| index=...` and `| sourcetype=...` behave like an implicit search
    if re.match(r"^(?:index|sourcetype|source|host)\s*=", first_seg, re.IGNORECASE):
        return []
    first = first_seg.split()[0].lower() if first_seg else ""
    # Allow `| <macro>` (macros are backtick-quoted)
    if first in _GENERATING_COMMANDS or first.startswith("`"):
        return []
    return [
        Finding(
            file=file,
            uc_id=uc_id,
            severity="HIGH",
            category="leading-pipe-invalid",
            message=(
                f"Block begins with `|` followed by `{first or '(empty)'}` which "
                "is not a generating command. Either drop the leading `|` or "
                "prefix with a valid generating command (`tstats`, `mstats`, "
                "`inputlookup`, `search`, `rest`, `makeresults`, `dbxquery`, ...)."
            ),
            snippet=cleaned[:160],
        )
    ]


_RE_MULTI_SEARCH_GLUE = re.compile(
    r"^\s*index\s*=.+?\s*\|\s*comment\(.+?\)\s*\|?\s*index\s*=",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)


def check_multi_search_glue(uc_id: str, file: str, spl: str) -> List[Finding]:
    """Flag `index=... | comment("...") | index=...` patterns — two searches
    glued together, not a single pipeline.  Treat as HIGH."""
    if _RE_MULTI_SEARCH_GLUE.search(spl):
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="HIGH",
                category="multi-search-glue",
                message=(
                    "Multiple `index=` searches glued with `| comment(...)` are "
                    "not a single pipeline. Split into separate UCs or combine "
                    "with `| multisearch`/`| union` if a combined view is required."
                ),
                snippet=spl.strip()[:200],
            )
        ]
    return []


_RE_CASE_WILDCARD = re.compile(
    r"\bcase\s*\(\s*([^,)]*\*[^,)]*)\s*,",
    re.IGNORECASE,
)


def check_case_wildcard(uc_id: str, file: str, spl: str) -> List[Finding]:
    """Flag `case(<literal-with-*>, ...)` where the `*` will be a literal string.

    Only fire when the first predicate contains `*` inside a quoted string OR
    in the `<field>="*"` style, which are common mistakes.
    """
    findings: List[Finding] = []
    for m in _RE_CASE_WILDCARD.finditer(spl):
        predicate = m.group(1)
        # If the `*` is inside quotes on either side of `=` or in a string literal,
        # that's the bug.
        if re.search(r'"[^"]*\*[^"]*"', predicate):
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="MED",
                    category="case-wildcard-literal",
                    message=(
                        "`case()` predicate contains a quoted `*` which is a "
                        "literal string, not a wildcard. Use `like()` or "
                        "`match()` for pattern matching inside `case`."
                    ),
                    snippet=predicate[:120],
                )
            )
    return findings


_RE_POSTCHART_WHERE = re.compile(
    r"\btimechart\b[^|]*(?:\|\s*[^|]*)*?\|\s*where\b",
    re.IGNORECASE | re.DOTALL,
)


_AS_ALIAS_RE = re.compile(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_EVAL_ASSIGN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", re.IGNORECASE)
_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

_WHERE_KEYWORDS = {
    # SPL boolean/keywords
    "and", "or", "not", "in", "like", "true", "false", "null",
    # SPL test functions
    "isnull", "isnotnull", "if", "case", "match", "searchmatch",
    "like", "cidrmatch", "coalesce",
    # eval casts and math
    "len", "eval", "where", "tonumber", "tostring", "abs", "min", "max",
    "round", "floor", "ceiling", "ceil", "log", "ln", "exp", "sqrt",
    "strftime", "strptime", "now", "relative_time", "typeof",
    "upper", "lower", "substr", "replace", "split", "mvindex", "mvcount",
    "mvappend", "mvfilter", "spath", "json_extract", "pi",
    # common field idiom
    "_time", "count",
}


def check_where_after_timechart(uc_id: str, file: str, spl: str) -> List[Finding]:
    """Flag `timechart ... | where <field>` where <field> is clearly a raw event
    field that the timechart aggregation dropped.

    We build a running set of "produced" fields as the pipeline progresses
    (timechart aliases, streamstats/eventstats aliases, eval assignments,
    lookup OUTPUT field names) and only flag the `where` when it references
    identifiers that are NOT in the produced set AND also don't look like
    constants/thresholds.  Heuristic — tuned to minimise false positives.

    Skip entirely when the SPL contains `| comment` (multi-search glue — those
    get flagged by a different check).
    """
    cleaned = _strip_comments(spl)
    if "comment(" in spl or "| comment" in spl:
        return []
    segs = _split_pipes(cleaned)
    findings: List[Finding] = []
    saw_timechart = False
    produced: set[str] = set()
    for seg in segs:
        low = seg.lower().lstrip()
        if low.startswith("timechart"):
            saw_timechart = True
            produced = set()
            for am in _AS_ALIAS_RE.finditer(seg):
                produced.add(am.group(1).lower())
            if re.search(r"\bcount\b", seg, flags=re.IGNORECASE) and "as " not in low[:80]:
                produced.add("count")
            # `by <fields>` produces the split-by dimensions
            bm = re.search(r"\bby\s+([A-Za-z_,\s]+)$", seg, flags=re.IGNORECASE)
            if bm:
                for f in bm.group(1).split(","):
                    f = f.strip()
                    if f:
                        produced.add(f.lower())
            produced.add("_time")
            continue
        if not saw_timechart:
            continue
        # Track fields produced by subsequent commands
        if low.startswith("eval "):
            for em in _EVAL_ASSIGN_RE.finditer(seg[len("eval "):]):
                produced.add(em.group(1).lower())
            continue
        if low.startswith(("streamstats ", "eventstats ", "stats ")):
            for am in _AS_ALIAS_RE.finditer(seg):
                produced.add(am.group(1).lower())
            continue
        if low.startswith("lookup "):
            # grab fields after OUTPUT/OUTPUTNEW
            om = re.search(r"\bOUTPUT(?:NEW)?\s+(.*)$", seg, flags=re.IGNORECASE)
            if om:
                for tok in re.split(r"[\s,]+", om.group(1).strip()):
                    if tok and _IDENT_RE.fullmatch(tok):
                        produced.add(tok.lower())
            continue
        if low.startswith("rename "):
            for rm in re.finditer(
                r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)", seg, flags=re.IGNORECASE
            ):
                produced.add(rm.group(1).lower())
            continue
        if low.startswith("predict") and (low == "predict" or low.startswith("predict ")):
            # `predict X as Y` aliases emit `Y`, `lower95(Y)`, `upper95(Y)`
            # Also unaliased `predict X` emits `prediction(X)` but any ident used
            # in a downstream where must have been aliased.
            for am in _AS_ALIAS_RE.finditer(seg):
                produced.add(am.group(1).lower())
            continue
        if low.startswith("addtotals") and (low == "addtotals" or not low[len("addtotals")].isalnum()):
            # `addtotals [fieldname=<X>]` defaults to `Total`
            fm = re.search(r"\bfieldname\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", seg, flags=re.IGNORECASE)
            produced.add(fm.group(1).lower() if fm else "total")
            continue
        if low.startswith("untable "):
            # `untable <x-field> <col-field> <val-field>` emits the two named fields
            parts = re.split(r"\s+", seg.strip(), maxsplit=4)
            if len(parts) >= 4:
                produced.add(parts[2].lower())
                produced.add(parts[3].lower())
            continue
        if low.startswith("xyseries "):
            parts = re.split(r"\s+", seg.strip(), maxsplit=4)
            if len(parts) >= 4:
                produced.add(parts[1].lower())
            continue
        if low.startswith(("fit ", "apply ")):
            # MLTK: DensityFunction emits `IsOutlier(<x>)`, OneClassSVM emits `isNormal`,
            # LocalOutlierFactor emits `isOutlier`/`outlier`.  Track common names.
            produced.update({"isoutlier", "isnormal", "outlier", "predicted", "probability"})
            for am in _AS_ALIAS_RE.finditer(seg):
                produced.add(am.group(1).lower())
            continue
        if low.startswith("anomalydetection ") or low.startswith("anomalies "):
            produced.update({"probable_cause", "outlier", "anomalyscore"})
            continue
        if low.startswith("accum "):
            am = re.search(r"\baccum\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?", seg, flags=re.IGNORECASE)
            if am:
                produced.add((am.group(2) or am.group(1)).lower())
            continue
        if not low.startswith("where "):
            continue
        # Collect identifiers on the *left-hand side* of comparison operators
        # to reduce false positives (don't flag comparison constants).
        body = seg[len("where "):]
        # Pull bareword idents that are the subject of comparisons (appear to the
        # left of >, <, =, !=, etc.)
        lhs = re.findall(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:==|=|!=|<>|>=|<=|>|<)",
            body,
        )
        KEYWORDS = _WHERE_KEYWORDS
        suspicious = [
            f for f in lhs
            if f.lower() not in KEYWORDS
            and f.lower() not in produced
            and len(f) > 2
        ]
        if suspicious and produced:
            first = suspicious[0]
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="MED",
                    category="where-after-timechart-unknown-field",
                    message=(
                        f"`where` after `timechart` references `{first}` on the "
                        "LHS of a comparison, but it is not produced by the "
                        f"timechart or any downstream command (produced: "
                        f"{sorted(produced)[:8]}...). The filter likely drops all rows."
                    ),
                    snippet=seg[:160],
                )
            )
            break
    return findings


def audit_spl_block(uc_id: str, file: str, spl: str) -> List[Finding]:
    out: List[Finding] = []
    out.extend(check_stats_span(uc_id, file, spl))
    out.extend(check_leading_pipe(uc_id, file, spl))
    out.extend(check_multi_search_glue(uc_id, file, spl))
    out.extend(check_case_wildcard(uc_id, file, spl))
    out.extend(check_where_after_timechart(uc_id, file, spl))
    return out


def audit_file(path: str) -> List[Finding]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    findings: List[Finding] = []
    for uc_id, body, _s, _e in _iter_uc_blocks(text):
        for spl in _iter_spl_blocks(body):
            findings.extend(audit_spl_block(uc_id, path, spl))
    return findings


# ----- Auto-fixers ---------------------------------------------------------

_FIX_STATS_SPAN_RE = re.compile(
    r"(\|\s*(?:si)?stats\b[^|\n]*?\bby\b[^|\n]*?)\b_time\s+span\s*=\s*([A-Za-z0-9]+)\b",
    re.IGNORECASE,
)


def fix_stats_span_in_spl(spl: str) -> Tuple[str, int]:
    """Rewrite `| stats ... by ... _time span=X` to `| bin _time span=X | stats ... by ... _time`.

    Handles:
      * inline `_time span=1h`
      * trailing `_time span=1h` (as last token of `by` clause)

    Leaves the order of other `by` fields intact.  Returns (new_spl, n_fixed).
    """
    fixes = 0
    def _replace(m: re.Match) -> str:
        nonlocal fixes
        fixes += 1
        pre = m.group(1).rstrip()
        span_val = m.group(2)
        # Ensure the `by` clause still includes `_time` at the end with no span.
        if pre.endswith(","):
            pre = pre[:-1].rstrip()
        new_pre = pre + ", _time" if not pre.endswith("_time") else pre
        # Re-order so `bin` runs BEFORE the stats
        # Strip the opening `| ` so we can re-prefix it
        no_leading_pipe = new_pre.lstrip().lstrip("|").lstrip()
        return f"| bin _time span={span_val}\n| {no_leading_pipe}"

    new = _FIX_STATS_SPAN_RE.sub(_replace, spl)
    return new, fixes


_FIX_STATS_SPAN_INLINE_RE = re.compile(
    # `by field1, field2, _time span=X` where `_time` appears somewhere in the middle
    r"(\|\s*(?:si)?stats\b[^|\n]*?\bby\b[^|\n]*?)_time\s+span\s*=\s*([A-Za-z0-9]+)",
    re.IGNORECASE,
)


def fix_spl_block(spl: str) -> Tuple[str, int]:
    """Apply all in-place SPL fixes; return (new_spl, total_fixes)."""
    total = 0
    new, n = fix_stats_span_in_spl(spl)
    total += n
    return new, total


def fix_file(path: str, dry_run: bool = False) -> Tuple[int, List[str]]:
    """Apply fixes to a file.  Returns (n_fixed, summary_lines)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_text = text
    n_fixed = 0
    summary: List[str] = []
    # Walk through code fences and apply fixes to each SPL block
    pos = 0
    out_parts: List[str] = []
    for m in RE_SPL_FENCE.finditer(text):
        pre = text[pos:m.start()]
        inner = m.group(1)
        new_inner, n = fix_spl_block(inner)
        out_parts.append(pre)
        out_parts.append("```spl\n" + new_inner + "\n```")
        if n > 0:
            n_fixed += n
        pos = m.end()
    out_parts.append(text[pos:])
    new_text = "".join(out_parts)
    if n_fixed > 0 and not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        summary.append(f"  {os.path.basename(path):60s}  +{n_fixed} fixes")
    elif n_fixed > 0 and dry_run:
        summary.append(f"  {os.path.basename(path):60s}  would fix {n_fixed}")
    return n_fixed, summary


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Exit 1 if any HIGH finding")
    ap.add_argument("--json", action="store_true", help="JSON output for tooling")
    ap.add_argument(
        "--severity",
        choices=["HIGH", "MED", "LOW"],
        default="MED",
        help="Minimum severity to surface in the exit code (default: MED)",
    )
    ap.add_argument(
        "--fix",
        action="store_true",
        help="Apply mechanical fixes (stats-span-invalid). Writes files in place.",
    )
    ap.add_argument(
        "--fix-dry-run",
        action="store_true",
        help="Report what --fix would change but do not write files",
    )
    args = ap.parse_args(argv)

    paths = sorted(glob.glob(USE_CASES))

    if args.fix or args.fix_dry_run:
        print("Applying mechanical fixes (stats-span-invalid)...")
        total = 0
        summaries: List[str] = []
        for p in paths:
            n, s = fix_file(p, dry_run=args.fix_dry_run)
            total += n
            summaries.extend(s)
        if summaries:
            print("\n".join(summaries))
        action = "WOULD FIX" if args.fix_dry_run else "FIXED"
        print(f"\n{action} {total} stats-span issues across {len(summaries)} files")
        return 0

    all_findings: List[Finding] = []
    for p in paths:
        all_findings.extend(audit_file(p))

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], indent=2))
    else:
        print("=" * 72)
        print("SPL grammar audit (use-cases/cat-*.md)")
        print("=" * 72)
        print(f"Files scanned: {len(paths)}")
        counts: dict[str, int] = {}
        for f in all_findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        print(
            "Findings by severity: "
            + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        )
        print()
        by_cat: dict[str, int] = {}
        for f in all_findings:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        print("Findings by category:")
        for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            print(f"  {v:4d}  {k}")
        print()
        if all_findings:
            print("FINDINGS:")
            print("-" * 72)
            for f in all_findings:
                print(f.human())

    if not args.check:
        return 0

    severity_order = {"HIGH": 3, "MED": 2, "LOW": 1}
    thresh = severity_order[args.severity]
    n_fail = sum(1 for f in all_findings if severity_order[f.severity] >= thresh)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
