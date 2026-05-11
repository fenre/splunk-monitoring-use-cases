#!/usr/bin/env python3
"""audit_doc_spl.py — SPL / CIM hallucination sweep across prose docs.

Why this script exists
----------------------

The existing audits in ``src/splunk_uc/audits/spl_hallucinations.py`` and
``scripts/deep_spl_hallucination_sweep.py`` validate SPL inside the JSON
SSOT (``content/cat-*/UC-*.json``).  They do *not* read the prose
documentation under ``docs/`` and at the repo root, even though those
files contain hundreds of fenced SPL code blocks and frequent
inline mentions of CIM data-model names — both of which are prime
candidates for LLM-generated hallucinations.

This audit closes that gap by:

1. **Fenced SPL blocks** — collecting every ```` ```spl ```` block plus
   every bare ```` ``` ```` block that looks like SPL (starts with
   ``|``, ``index=``, ``search ``, ``tstats``, ``mstats``,
   ``from datamodel``, or contains a ``| stats``/``| eval`` segment).
   Each block is run through the same checks as the canonical SPL
   audits:

      • Unknown top-level commands (``VALID_COMMANDS``)
      • Unknown eval / where / fieldformat functions (``VALID_EVAL_FUNCS``)
      • Unknown stats-family aggregators (``VALID_AGGREGATE_FUNCS``)
      • Aggregator-in-eval misuse (``EVAL_ONLY_AGGREGATORS``)
      • Bad command patterns / typos (``BAD_COMMAND_PATTERNS``)
      • ``tstats`` ``datamodel=`` references against ``CIM_DATASETS``

2. **Prose CIM mentions** — finding phrases like ``the Authentication
   data model``, ``CIM datamodel Foo_Bar``, or ``datamodel=Web`` *outside*
   of fenced blocks, and verifying the name against ``CIM_DATASETS``.

The script is **report-only**: it writes ``data/doc-spl-mentions.json``
and prints a human summary to stdout.  Fixes belong in a separate
curated pass once human review has tagged the truly bad mentions.

Stdlib-only.  Imports the canonical SPL/CIM tables from the existing
audits — no duplication of the allowlists.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATUS_PATH = REPO / "data" / "doc-spl-mentions.json"

# Reuse the canonical SPL / CIM tables from the existing audits.
sys.path.insert(0, str(REPO / "src"))
from splunk_uc.audits.spl_hallucinations import (  # noqa: E402
    BAD_COMMAND_PATTERNS,
    CIM_DATASETS as _CORE_CIM_DATASETS,
    VALID_COMMANDS,
    check_bad_patterns,
    check_tstats as _check_tstats_core,
    check_unknown_commands,
)
sys.path.insert(0, str(REPO / "scripts"))
from deep_spl_hallucination_sweep import (  # noqa: E402
    EVAL_ONLY_AGGREGATORS,
    FUNC_CALL_RE,
    VALID_AGGREGATE_FUNCS,
    VALID_EVAL_FUNCS,
    _strip_comments,
    _strip_strings,
    split_pipes,
)

# Custom data models that this repo defines on top of Splunk CIM 6.x.
# Documented in `docs/guides/iot-ot.md` (Operational_Telemetry).  These
# are NOT in the upstream Splunk_SA_CIM datamodel set, so the core
# `_CORE_CIM_DATASETS` table does not list them — extend the lookup
# locally so the audit doesn't false-positive on them.
LOCAL_CIM_EXTENSIONS: dict[str, set[str]] = {
    "Operational_Telemetry": {
        "All_Operational_Telemetry",
        "Metrics",
        "Events",
        "States",
        "Production",
        "OEE",
        "Quality",
        "Maintenance",
        "Security",
        "Location",
    },
}
CIM_DATASETS: dict[str, set[str]] = {
    **_CORE_CIM_DATASETS,
    **LOCAL_CIM_EXTENSIONS,
}


def check_tstats(spl: str) -> list[tuple[str, str]]:
    """Replicate the core `check_tstats` but against our extended
    `CIM_DATASETS` (which knows about `Operational_Telemetry`).

    The core implementation closes over `_CORE_CIM_DATASETS` at import
    time, so we cannot just monkey-patch it.
    """
    # Reuse the core extractor for the parsed components, then re-check.
    from splunk_uc.audits.spl_hallucinations import (
        extract_tstats_components,
    )
    findings: list[tuple[str, str]] = []
    for comp in extract_tstats_components(spl):
        model = comp.get("model", "")
        dataset = comp.get("dataset", "")
        if model and model not in CIM_DATASETS:
            findings.append(("cim_model_unknown", f"Unknown CIM datamodel: {model!r}"))
        elif model and dataset and dataset not in CIM_DATASETS[model]:
            findings.append((
                "cim_dataset_unknown",
                f"Dataset {dataset!r} not in CIM datamodel {model!r}. "
                f"Valid: {sorted(CIM_DATASETS[model])}",
            ))
    return findings


# Backtick-enclosed macros are opaque to SPL scanning — their bodies are
# expanded at search time, so any function-looking call inside them
# (e.g. `entropy(query)` from URL Toolbox) is NOT a Splunk eval call.
# Mask them with spaces before scanning so `FUNC_CALL_RE` can't find
# their internals.
_BACKTICK_RE = re.compile(r"`[^`]*`")


def _mask_backticks(spl: str) -> str:
    return _BACKTICK_RE.sub(lambda m: " " * (m.end() - m.start()), spl)

# ---------------------------------------------------------------- corpus
DOCS_DIR = REPO / "docs"
DEFAULT_EXTRA = [
    "AGENTS.md",
    "AGENTS-EXAMPLES.md",
    "CHANGELOG.md",
    "CODEBASE-DIAGRAM.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "README.md",
    "LEGAL.md",
    "api/README.md",
]


def collect_docs() -> list[Path]:
    out: list[Path] = []
    if DOCS_DIR.is_dir():
        for p in DOCS_DIR.rglob("*.md"):
            if p.is_file():
                out.append(p)
    for rel in DEFAULT_EXTRA:
        p = REPO / rel
        if p.is_file():
            out.append(p)
    return sorted({p.resolve() for p in out})


# ---------------------------------------------------------------- block extraction
# Three-backtick fence with optional language tag and optional info string.
# We strip surrounding indentation so blockquoted code blocks still parse.
FENCE_RE = re.compile(r"^([ \t]{0,3})```([^\n`]*)\n(.*?)\n\1```", re.S | re.M)

# Treat these tags as definitely SPL.
SPL_TAGS = {"spl", "splunk"}

# Heuristics — bare blocks that look like SPL.
SPL_OPEN_PATTERNS = [
    re.compile(r"^\s*\|\s*(?:tstats|mstats|inputlookup|metasearch|datamodel|from|search|rest)\b", re.I),
    re.compile(r"^\s*index\s*=", re.I),
    re.compile(r"^\s*search\s+index\s*=", re.I),
    re.compile(r"^\s*\|\s*makeresults\b", re.I),
    re.compile(r"^\s*tstats\b", re.I),
    re.compile(r"^\s*mstats\b", re.I),
]
SPL_INNER_PATTERNS = [
    re.compile(r"\|\s*stats\s+", re.I),
    re.compile(r"\|\s*eval\s+\w", re.I),
    re.compile(r"\|\s*timechart\b", re.I),
    re.compile(r"\|\s*tstats\b", re.I),
    re.compile(r"\|\s*where\s+\w", re.I),
    re.compile(r"\|\s*streamstats\b", re.I),
    re.compile(r"\|\s*eventstats\b", re.I),
]


def looks_like_spl(tag: str, block: str) -> bool:
    if tag.lower() in SPL_TAGS:
        return True
    if not block.strip():
        return False
    # A bare block is SPL if its first non-blank line opens with an SPL
    # cue OR if the body contains two or more SPL-style pipe segments.
    first = block.lstrip().splitlines()[0] if block.strip() else ""
    if any(p.search(first) for p in SPL_OPEN_PATTERNS):
        return True
    inner_hits = sum(bool(p.search(block)) for p in SPL_INNER_PATTERNS)
    return inner_hits >= 2


def extract_spl_blocks(text: str) -> list[tuple[int, str, str]]:
    """Return (line_number, tag, body) for every fenced block that
    we classify as SPL."""
    out: list[tuple[int, str, str]] = []
    for m in FENCE_RE.finditer(text):
        info = m.group(2).strip()
        tag = info.split()[0].lower() if info else ""
        body = m.group(3)
        if not looks_like_spl(tag, body):
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        out.append((line_no, tag or "<bare>", body))
    return out


# ---------------------------------------------------------------- prose CIM detection

# Capture phrases like:
#   the Authentication data model
#   CIM datamodel Network_Traffic
#   datamodel=Foo
#   datamodel:Foo.Bar
#
# We only emit findings for prose mentions OUTSIDE code blocks.  The
# code-block extractor above is the path for in-block validation.
# Only one prose pattern.  We previously tried a second pattern that
# matched "<Name> data model" / "<Name> CIM model" but the surrounding
# prose ("the Operational Telemetry data model", "Common Information
# Model", "validate the CIM_Alerts data model" …) generated more noise
# than signal:
#   • "Common Information Model" *is* CIM — the long form, not a typo.
#   • Multi-word names like "Operational Telemetry" got swallowed up
#     together with the preceding verb ("Run_Splunk_SA_CIM", "Validate_Web").
#   • The real hallucinations of interest already appear inside fenced
#     SPL blocks, where `check_tstats` flags them via `datamodel=`.
# A single-pattern audit keeps the signal-to-noise ratio sane.
CIM_PROSE_PATTERNS = [
    # "datamodel=Foo" / "datamodel = Foo" / "datamodel:Foo.Bar" —
    # most common in tstats prose snippets outside a fenced block.
    re.compile(
        r"\bdatamodel\s*[:=]\s*([A-Za-z_][A-Za-z0-9_]*)"
        r"(?:\.([A-Za-z_][A-Za-z0-9_]*))?",
    ),
]


# Inline `code spans` — single, double, or triple backticks around a
# non-backtick body.  We strip these too because authors frequently
# paste mini-SPL snippets like "`| tstats from datamodel=Foo`" into
# prose paragraphs; without stripping them, the prose pattern would
# fire on every `datamodel=` inside an inline code span.
#
# CommonMark permits inline code spans to wrap newlines (so long as
# they do not contain a stray backtick), which we honour with
# `re.DOTALL`.  Single-line snippets remain the common case.
_INLINE_CODE_RE = re.compile(r"`{1,3}[^`]+`{1,3}", re.S)


def strip_code_blocks(text: str) -> str:
    """Replace fenced and inline code with whitespace so prose
    patterns can match against the remainder without colliding with
    code samples."""
    text = FENCE_RE.sub(lambda m: " " * (m.end() - m.start()), text)
    text = _INLINE_CODE_RE.sub(lambda m: " " * (m.end() - m.start()), text)
    return text


# Words we do NOT want flagged from the second prose pattern.  These
# show up in writing about data models in general, not specific CIM
# datamodel names.
NON_CIM_PROSE_NOUNS = {
    "the",
    "a",
    "an",
    "any",
    "every",
    "splunk",
    "core",
    "custom",
    "common",
    "data",
    "datamodel",
    "datamodels",
    "model",
    "information",
    "cim",
    "ecs",
    "this",
    "that",
    "each",
    "shared",
    "above",
    "below",
    "internal",
    "official",
    "first",
    "second",
    "third",
    "key",
    "primary",
    "secondary",
    "main",
    "another",
    "other",
    # Brand / product names that are descriptive, not CIM data model names.
    "elastic",
    "elasticsearch",
    "amazon",
    "microsoft",
    "google",
    "cisco",
    "ibm",
    "broadcom",
    # Splunk app / TA names that show up next to "data model" but are
    # not themselves data model names.
    "splunk_sa_cim",
    "splunk_ta_cisco",
    "splunk_ta_cim",
    # Network / industrial protocol modelling languages that share the
    # phrase "data model" — these are RFC / IEC concepts, not Splunk
    # CIM datamodels.
    "yang",   # RFC 7950 / NETCONF schema language
    "openconfig",
    "smi",    # SNMP Management Information Base modelling
    "yang/openconfig",
}


def extract_cim_mentions(prose: str) -> list[tuple[str, str | None]]:
    """Return [(model, dataset_or_None)] mentions found in prose."""
    out: list[tuple[str, str | None]] = []
    for m in CIM_PROSE_PATTERNS[0].finditer(prose):
        model = m.group(1)
        dataset = m.group(2)
        if model.lower() in NON_CIM_PROSE_NOUNS:
            continue
        out.append((model, dataset))
    return out


# ---------------------------------------------------------------- main audit
@dataclass
class Finding:
    path: str
    line: int
    category: str
    severity: str
    message: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet[:240],
        }


def _check_eval_functions(spl: str) -> list[tuple[str, str, str]]:
    """Mirror of deep_spl_hallucination_sweep.check_eval_functions, but
    returns (category, message, snippet) tuples for our Finding shape."""
    out: list[tuple[str, str, str]] = []
    scrubbed = _mask_backticks(_strip_strings(_strip_comments(spl)))
    for seg in split_pipes(scrubbed):
        seg_l = seg.lstrip().lower()
        if not seg_l.startswith(("eval ", "where ", "fieldformat ")):
            continue
        cmd, _, body = seg.lstrip().partition(" ")
        for m in FUNC_CALL_RE.finditer(body):
            name = m.group(1)
            lower = name.lower()
            if lower in {"and", "or", "not", "xor", "as", "by"}:
                continue
            if lower in VALID_EVAL_FUNCS:
                continue
            start = max(0, m.start() - 60)
            end = min(len(body), m.end() + 60)
            snip = body[start:end]
            if lower in EVAL_ONLY_AGGREGATORS:
                out.append((
                    "aggregator-in-eval",
                    f"Aggregator `{name}()` used inside `{cmd}` — "
                    "`median`/`stdev`/`var` are only valid in "
                    "stats/timechart/chart/streamstats/eventstats",
                    snip,
                ))
                continue
            out.append((
                "unknown-eval-func",
                f"Unknown eval-context function: {name}() "
                "(not in documented eval-function set)",
                snip,
            ))
    return out


# These keywords appear directly after stats-family commands but are
# *clauses* / argument names, not aggregator function calls.  Skip them.
AGG_HOST_COMMANDS = (
    "stats", "timechart", "chart", "streamstats", "eventstats",
    "geostats", "mstats", "tstats", "sistats", "sitimechart", "sichart",
)
AGG_KEYWORD_PASS_THROUGH = {
    "and", "or", "not", "xor", "as", "by", "where", "from",
    "groupby", "span", "earliest", "latest", "limit",
    "useother", "usenull", "summariesonly", "fillnull",
    "true", "false", "allnum", "allownull", "nullstr",
    "global", "window", "current", "reset_on_change",
    "reset_before", "reset_after", "time_field",
    # Predict-output field references generated by `| predict`.
    "predicted", "outlier", "residual",
}
PREDICT_FIELDS = re.compile(
    r"^(predicted|upper\d{1,3}|lower\d{1,3}|outlier|residual)$"
)


def _check_aggregate_functions(spl: str) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    scrubbed = _mask_backticks(_strip_strings(_strip_comments(spl)))
    for seg in split_pipes(scrubbed):
        seg_l = seg.lstrip().lower()
        if not seg_l:
            continue
        first_word = seg_l.split(None, 1)[0]
        if first_word not in AGG_HOST_COMMANDS:
            continue
        body = seg.lstrip()[len(first_word):]
        for m in FUNC_CALL_RE.finditer(body):
            name = m.group(1).lower()
            if name in VALID_AGGREGATE_FUNCS:
                continue
            if re.match(r"^(perc|exactperc|upperperc)\d+$", name):
                continue
            if re.match(r"^p\d+$", name):
                continue
            if name == "eval":
                continue
            if name in AGG_KEYWORD_PASS_THROUGH:
                continue
            if name in VALID_EVAL_FUNCS:
                continue
            if PREDICT_FIELDS.match(name):
                continue
            start = max(0, m.start() - 60)
            end = min(len(body), m.end() + 60)
            out.append((
                "unknown-aggregate-func",
                f"Unknown stats-family aggregator function: {name}() "
                f"after `{first_word}` command",
                body[start:end],
            ))
    return out


def audit_block(path: Path, line: int, body: str) -> list[Finding]:
    findings: list[Finding] = []
    rel = path.relative_to(REPO).as_posix()
    snippet_head = (body.splitlines() or [""])[0][:160]
    # tstats / CIM dataset checks
    for cat, msg in check_tstats(body):
        findings.append(Finding(rel, line, cat, "HIGH", msg, snippet_head))
    for cat, msg in check_bad_patterns(body):
        findings.append(Finding(rel, line, cat, "MED", msg, snippet_head))
    for cat, msg in check_unknown_commands(body):
        findings.append(Finding(rel, line, cat, "HIGH", msg, snippet_head))
    for cat, msg, snip in _check_eval_functions(body):
        findings.append(Finding(rel, line, cat, "HIGH", msg, snip))
    for cat, msg, snip in _check_aggregate_functions(body):
        findings.append(Finding(rel, line, cat, "HIGH", msg, snip))
    return findings


def audit_prose_cim(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    rel = path.relative_to(REPO).as_posix()
    prose = strip_code_blocks(text)
    seen: set[tuple[int, str, str | None]] = set()
    for model, dataset in extract_cim_mentions(prose):
        if model in CIM_DATASETS:
            if dataset and dataset not in CIM_DATASETS[model]:
                idx = prose.find(model)
                line = text.count("\n", 0, idx) + 1 if idx >= 0 else 0
                key = (line, model, dataset)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(Finding(
                    rel, line,
                    "cim_dataset_unknown",
                    "MED",
                    f"Prose mentions `{model}.{dataset}` but `{dataset}` "
                    f"is not a documented dataset of `{model}`. "
                    f"Valid: {sorted(CIM_DATASETS[model])}",
                    "",
                ))
            continue
        # Model name unknown — only flag the first occurrence per file
        idx = prose.find(model)
        line = text.count("\n", 0, idx) + 1 if idx >= 0 else 0
        key = (line, model, dataset)
        if key in seen:
            continue
        seen.add(key)
        findings.append(Finding(
            rel, line,
            "cim_model_unknown",
            "MED",
            f"Prose mentions `{model}` as a CIM/datamodel name but it "
            "is not in the documented CIM 6.x catalogue or the two "
            "Splunk add-on extensions (`Risk`, `Service_KPI_Summary`).",
            "",
        ))
    return findings


def audit(docs: list[Path]) -> tuple[list[Finding], dict[str, int], dict[str, int]]:
    findings: list[Finding] = []
    block_counts: dict[str, int] = defaultdict(int)
    cim_counts: dict[str, int] = defaultdict(int)
    for p in docs:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for line, tag, body in extract_spl_blocks(text):
            block_counts[tag] += 1
            findings.extend(audit_block(p, line, body))
        for f in audit_prose_cim(p, text):
            cim_counts[f.category] += 1
            findings.append(f)
    return findings, dict(block_counts), dict(cim_counts)


def write_status(
    findings: list[Finding],
    block_counts: dict[str, int],
    cim_counts: dict[str, int],
) -> None:
    by_cat: dict[str, int] = defaultdict(int)
    for f in findings:
        by_cat[f.category] += 1
    payload = {
        "_meta": {
            "tool": "scripts/audit_doc_spl.py",
            "schema": 1,
            "findings": len(findings),
            "blocks_scanned": block_counts,
            "prose_findings": cim_counts,
            "category_counts": dict(by_cat),
        },
        "findings": [f.to_dict() for f in findings],
    }
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def summarise(findings: list[Finding], block_counts: dict[str, int]) -> None:
    print(f"Scanned {sum(block_counts.values())} SPL blocks "
          f"({', '.join(f'{n} {tag}' for tag, n in sorted(block_counts.items(), key=lambda kv: -kv[1]))})")
    print()
    if not findings:
        print("No SPL or CIM prose issues found.")
        return
    by_cat: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_cat[f.category].append(f)
    print(f"{len(findings)} findings across {len(by_cat)} categories:\n")
    for cat in sorted(by_cat.keys()):
        items = by_cat[cat]
        print(f"  {cat:24s} {len(items):4d}")
    print()
    for cat in sorted(by_cat.keys()):
        items = by_cat[cat][:20]
        print(f"=== {cat} ({len(by_cat[cat])}) — first 20 ===")
        for f in items:
            print(f"  {f.path}:{f.line}  {f.message}")
            if f.snippet:
                print(f"      {f.snippet}")
        print()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true",
                   help="Print the JSON payload to stdout in addition to "
                        "writing data/doc-spl-mentions.json.")
    args = p.parse_args(argv)
    docs = collect_docs()
    print(f"Scanning {len(docs)} markdown files ...\n")
    findings, block_counts, cim_counts = audit(docs)
    write_status(findings, block_counts, cim_counts)
    summarise(findings, block_counts)
    if args.json:
        json.dump([f.to_dict() for f in findings], sys.stdout, indent=2)
        print()
    print(f"Status written → {STATUS_PATH.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
