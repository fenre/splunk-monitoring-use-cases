#!/usr/bin/env python3
"""Audit SPL reference identifiers against a known-good vocabulary.

Where ``audit-spl-grammar`` catches structural bugs and
``audit-spl-hallucinations`` catches unknown commands + invalid CIM
paths, this audit catches the harder failure mode: **plausible-looking
SPL with hallucinated identifiers** — fake macro names, misspelled
sourcetypes, eval functions that look right but aren't, datamodel paths
that don't exist.

Sources of truth (in order of preference):

1. **Splunk-core baseline** (``_spl_baseline.py``) — Splunk's published
   command + eval + stats vocabulary. Always available.
2. **CIM 6.x catalogue** (``spl_hallucinations.CIM_DATASETS``) — the
   real Splunk Common Information Model datamodel/dataset map.
3. **Local reference corpus** (``data/spl-reference.local.json``) —
   optional fingerprints from third-party Splunk apps. Built by
   ``tools/research/build_spl_reference.py``.
4. **The UC's own declarations** — ``splunkbaseApps[].id`` /
   ``dataSources`` strings. A sourcetype that appears in the UC's own
   ``dataSources`` field is by definition expected.

Severity tiers:

- **HIGH** — unknown SPL command, invalid datamodel.dataset (these
  break SPL execution).
- **MEDIUM** — unknown macro, unknown sourcetype (likely typo or
  hallucination).
- **LOW** — unknown eval / stats function (may be a custom UDF or a
  Splunk feature newer than our baseline).

Usage::

    python -m splunk_uc audit-spl-references           # human report
    python -m splunk_uc audit-spl-references --check   # CI-grade (fail on HIGH)
    python -m splunk_uc audit-spl-references --json    # machine-readable
    python -m splunk_uc audit-spl-references --severity MEDIUM
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from splunk_uc.audits import _spl_parse as parse
from splunk_uc.audits._spl_baseline import (
    BUILTIN_FIELD_TOKENS,
    CIM_DATASETS,
    VALID_COMMANDS,
    VALID_EVAL_FUNCTIONS,
    VALID_STATS_FUNCTIONS,
    is_perc_function,
)
from splunk_uc.audits._spl_well_known import (
    WELL_KNOWN_INDEXES,
    WELL_KNOWN_MACROS,
    WELL_KNOWN_SOURCETYPES,
)
from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO = Path(__file__).resolve().parents[3]
REFERENCE_PATH = REPO / "data" / "spl-reference.local.json"

_SPL_FIELDS = ("spl", "cimSpl", "rbaSpl", "mvSpl")

_SEV_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    field: str
    identifier: str
    message: str
    suggestion: str = ""

    def human(self) -> str:
        loc = f"UC-{self.uc_id} ({self.file}:{self.field})"
        line = f"[{self.severity}] [{self.category}] {loc}: {self.message}"
        if self.suggestion:
            line += f" -- did you mean: {self.suggestion}?"
        return line


# ---------------------------------------------------------------------------
# Reference vocabulary plumbing
# ---------------------------------------------------------------------------


@dataclass
class Vocabulary:
    """The union of every identifier we accept as known-good."""

    commands: set[str]
    macros: set[str]
    sourcetypes: set[str]
    sourcetype_glob_patterns: set[str]  # e.g. ``*365:cas:api``, ``cisco:ise:*``
    indexes: set[str]
    datamodel_paths: set[str]
    lookups: set[str]
    eval_functions: set[str]
    stats_functions: set[str]
    cim_models: set[str]  # just the model names, used for partial datamodel refs
    sources: list[dict[str, Any]]  # provenance of the loaded reference corpus

    # Cached compiled glob regex; built lazily on first access so the
    # cost is paid once per process rather than per-UC.
    _glob_re: "re.Pattern[str] | None" = None

    def matches_sourcetype(self, value: str) -> bool:
        """True if ``value`` is a known literal or matches a known glob.

        We use ``fnmatch.translate`` to compile each glob into a Python
        regex and then ``|``-combine them into a single pattern, so a
        membership test is one regex search regardless of corpus size.
        """
        if value in self.sourcetypes:
            return True
        if not self.sourcetype_glob_patterns:
            return False
        if self._glob_re is None:
            # ``fnmatch.translate`` returns ``(?s:<pattern>)\Z`` already
            # anchored; just join with ``|`` for the union.
            joined = "|".join(
                fnmatch.translate(g) for g in sorted(self.sourcetype_glob_patterns)
            )
            self._glob_re = re.compile(joined)
        return self._glob_re.match(value) is not None


def _load_reference(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            data: Any = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def build_vocabulary() -> Vocabulary:
    """Merge baseline + reference corpus into one immutable vocabulary."""
    ref = _load_reference(REFERENCE_PATH)
    cim_paths = set()
    for model, datasets in CIM_DATASETS.items():
        cim_paths.add(model)
        for ds in datasets:
            cim_paths.add(f"{model}.{ds}")
    return Vocabulary(
        commands=set(VALID_COMMANDS) | set(ref.get("commands", [])),
        macros=set(WELL_KNOWN_MACROS) | set(ref.get("macros", [])),
        sourcetypes=set(WELL_KNOWN_SOURCETYPES) | set(ref.get("sourcetypes", [])),
        sourcetype_glob_patterns=set(ref.get("sourcetype_glob_patterns", [])),
        indexes=set(BUILTIN_FIELD_TOKENS) | set(WELL_KNOWN_INDEXES) | set(ref.get("indexes", [])),
        datamodel_paths=cim_paths | set(ref.get("datamodel_paths", [])),
        lookups=set(ref.get("lookups", [])),
        eval_functions=set(VALID_EVAL_FUNCTIONS) | set(ref.get("eval_functions", [])),
        stats_functions=set(VALID_STATS_FUNCTIONS)
        | set(VALID_EVAL_FUNCTIONS)  # eval funcs are valid inside stats(eval(...))
        | set(ref.get("stats_functions", [])),
        cim_models=set(CIM_DATASETS.keys()) | set(ref.get("cim_models", [])),
        sources=ref.get("sources", []),
    )


# ---------------------------------------------------------------------------
# Per-UC declared vocabulary
# ---------------------------------------------------------------------------


def declared_sourcetypes_for(payload: dict[str, Any]) -> set[str]:
    """Pull every sourcetype string out of ``dataSources``/``spl`` declarations.

    The catalogue stores ``dataSources`` as a free-text string in most
    UCs but a structured array in others. We pull strings of the form
    ``sourcetype="..."`` / ``sourcetype=...`` from whatever is there
    so a UC's own declared inputs always count as "known".
    """
    candidates: list[str] = []
    ds = payload.get("dataSources")
    if isinstance(ds, str):
        candidates.append(ds)
    elif isinstance(ds, list):
        for item in ds:
            if isinstance(item, str):
                candidates.append(item)
            elif isinstance(item, dict):
                for v in item.values():
                    if isinstance(v, str):
                        candidates.append(v)
    out: set[str] = set()
    for blob in candidates:
        for sref in parse.extract_sourcetypes(blob):
            if not sref.is_wildcard and sref.value:
                out.add(sref.value)
    return out


def declared_indexes_for(payload: dict[str, Any]) -> set[str]:
    """Same idea for declared indexes (rare, but a few UCs name them)."""
    blobs: list[str] = []
    ds = payload.get("dataSources")
    if isinstance(ds, str):
        blobs.append(ds)
    elif isinstance(ds, list):
        for item in ds:
            if isinstance(item, str):
                blobs.append(item)
    out: set[str] = set()
    for blob in blobs:
        for iref in parse.extract_indexes(blob):
            if not iref.is_wildcard and iref.value and not iref.value.startswith("<"):
                out.add(iref.value)
    return out


# ---------------------------------------------------------------------------
# Per-UC checks
# ---------------------------------------------------------------------------


def _looks_like_token(value: str) -> bool:
    """Return True if a value is a Simple-XML / catalog placeholder."""
    return value.startswith(("$", "<<", "{")) or value.endswith(("}", ">>", "$"))


def _suggest(name: str, candidates: set[str]) -> str:
    if not name or not candidates:
        return ""
    matches = get_close_matches(name, candidates, n=1, cutoff=0.85)
    if matches:
        return matches[0]
    # Try case-insensitive
    lc = name.lower()
    lower_map = {c.lower(): c for c in candidates}
    if lc in lower_map and lower_map[lc] != name:
        return lower_map[lc]
    return ""


def check_one_spl_field(
    uc_id: str,
    file_label: str,
    field: str,
    spl: str,
    vocab: Vocabulary,
    declared_sourcetypes: set[str],
    declared_indexes: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    extracted = parse.extract_all(spl)

    # --- Commands (HIGH) -----------------------------------------------------
    for cmd in extracted.commands:
        if cmd in vocab.commands:
            continue
        sug = _suggest(cmd, vocab.commands)
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="HIGH",
                category="unknown-command",
                field=field,
                identifier=cmd,
                message=f"unknown SPL command `{cmd}`",
                suggestion=sug,
            )
        )

    # --- Macros (MEDIUM) -----------------------------------------------------
    for mref in extracted.macros:
        if not mref.name or _looks_like_token(mref.name):
            continue
        if mref.name in vocab.macros:
            continue
        # ESCU convention: every detection ships a per-detection "exclusion
        # filter" macro named ``<detection_name>_filter`` that the customer
        # overrides locally. They are by definition not in any global
        # vocabulary; treat the suffix as known-good.
        if mref.name.endswith("_filter"):
            continue
        # Backtick-wrapped names containing ``.`` are JSON field paths,
        # not real macros. Splunk macro names are alphanumeric + ``_``
        # by convention — none of the 2,381 macros in the curated
        # ``data/spl-reference.local.json`` vocabulary carry a dot. A
        # dotted candidate is therefore a UC-content bug (a field path
        # mistakenly wrapped in backticks, e.g.
        # ``coalesce(field, \`involvedObject.kind\`)``) and not an
        # unknown-macro finding. Skipping these here keeps the audit
        # report focused on true vocabulary gaps; the content-bug class
        # can be picked up by a dedicated audit if a maintainer wants
        # to track it separately.
        if "." in mref.name:
            continue
        sug = _suggest(mref.name, vocab.macros)
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="MEDIUM",
                category="unknown-macro",
                field=field,
                identifier=mref.name,
                message=f"macro `{mref.name}` not in known-good vocabulary",
                suggestion=sug,
            )
        )

    # --- Sourcetypes (MEDIUM) -----------------------------------------------
    known_sourcetypes = vocab.sourcetypes | declared_sourcetypes
    for sref in extracted.sourcetypes:
        if sref.is_wildcard:
            continue
        v = sref.value
        if not v or _looks_like_token(v):
            continue
        if v in known_sourcetypes:
            continue
        # Splunk add-ons frequently ship sourcetypes as glob patterns
        # (e.g. ``cisco:ise:*``, ``*365:cas:api``) rather than enumerating
        # every concrete value. The local reference corpus collects those
        # globs separately so we can match them after the literal lookup
        # fails.
        if vocab.matches_sourcetype(v):
            continue
        # Tolerate sourcetypes the UC declared with wildcards: a search
        # for sourcetype="aws:cloudtrail" is fine if the UC declared
        # sourcetype=aws:* etc. We don't currently parse wildcard
        # declarations -- keeping that as a future refinement.
        sug = _suggest(v, known_sourcetypes)
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="MEDIUM",
                category="unknown-sourcetype",
                field=field,
                identifier=v,
                message=f"sourcetype `{v}` not declared by UC and not in reference corpus",
                suggestion=sug,
            )
        )

    # --- Indexes (LOW) — informational; many indexes are tenant-specific ----
    known_indexes = vocab.indexes | declared_indexes
    for iref in extracted.indexes:
        if iref.is_wildcard:
            continue
        v = iref.value
        if not v or _looks_like_token(v):
            continue
        if v in known_indexes:
            continue
        # Indexes are deployment-specific; flag only obvious oddities.
        # Rule of thumb: a custom index name that includes whitespace or
        # punctuation other than `_-` is suspect.
        if not all(c.isalnum() or c in "_-" for c in v):
            findings.append(
                Finding(
                    file=file_label,
                    uc_id=uc_id,
                    severity="LOW",
                    category="suspicious-index-name",
                    field=field,
                    identifier=v,
                    message=f"index `{v}` contains unusual characters",
                )
            )

    # --- Datamodel paths (HIGH for invalid model, MEDIUM for unknown dataset) -
    for dref in extracted.datamodels:
        if dref.dataset is None:
            # Just a model name. HIGH if not in CIM and not in reference corpus.
            if dref.model in vocab.datamodel_paths:
                continue
            sug = _suggest(dref.model, vocab.cim_models)
            findings.append(
                Finding(
                    file=file_label,
                    uc_id=uc_id,
                    severity="HIGH",
                    category="unknown-datamodel",
                    field=field,
                    identifier=dref.model,
                    message=f"unknown datamodel `{dref.model}`",
                    suggestion=sug,
                )
            )
            continue
        path = f"{dref.model}.{dref.dataset}"
        if path in vocab.datamodel_paths:
            continue
        # If the model exists but dataset doesn't, that's MEDIUM (could be
        # a custom add-on datamodel extension).
        if dref.model in vocab.cim_models:
            datasets = CIM_DATASETS.get(dref.model, set())
            sug = _suggest(dref.dataset, datasets)
            findings.append(
                Finding(
                    file=file_label,
                    uc_id=uc_id,
                    severity="MEDIUM",
                    category="unknown-datamodel-dataset",
                    field=field,
                    identifier=path,
                    message=f"dataset `{dref.dataset}` not in CIM model `{dref.model}`",
                    suggestion=f"{dref.model}.{sug}" if sug else "",
                )
            )
            continue
        # Otherwise HIGH: completely unknown model + dataset combo.
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="HIGH",
                category="unknown-datamodel",
                field=field,
                identifier=path,
                message=f"unknown datamodel path `{path}`",
                suggestion=_suggest(dref.model, vocab.cim_models),
            )
        )

    # --- Eval functions (LOW) -----------------------------------------------
    for fref in extracted.eval_functions:
        name = fref.name
        if name in vocab.eval_functions:
            continue
        if name in vocab.commands:
            # `lookup(...)` and similar — fine.
            continue
        if is_perc_function(name):
            continue
        # Skip names that are clearly fields/aliases (lowercase + digit/underscore-only
        # patterns are common as field names appearing as `count(field)` etc, but
        # those are caught by the *stats* path — so for `eval` context we lean
        # in: anything not in the vocabulary is suspect.
        sug = _suggest(name, vocab.eval_functions)
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="LOW",
                category="unknown-eval-function",
                field=field,
                identifier=name,
                message=f"unknown eval function `{name}` in `{fref.context}` context",
                suggestion=sug,
            )
        )

    # --- Stats functions (LOW) ----------------------------------------------
    for fref in extracted.stats_functions:
        name = fref.name
        if name in vocab.stats_functions:
            continue
        if name in vocab.commands:
            continue
        if is_perc_function(name):
            continue
        sug = _suggest(name, vocab.stats_functions)
        findings.append(
            Finding(
                file=file_label,
                uc_id=uc_id,
                severity="LOW",
                category="unknown-stats-function",
                field=field,
                identifier=name,
                message=f"unknown stats function `{name}` in `{fref.context}` context",
                suggestion=sug,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run_audit(
    min_severity: str = "LOW",
    vocab: Vocabulary | None = None,
) -> list[Finding]:
    """Run the audit across every UC sidecar and return all findings >= severity.

    The ``vocab`` parameter lets callers (CLI, tests) build the
    vocabulary once and reuse it for both the audit run and any
    follow-up reporting (provenance, sizes), avoiding the cost of a
    second build on warm caches.
    """
    if vocab is None:
        vocab = build_vocabulary()
    threshold = _SEV_RANK[min_severity]
    out: list[Finding] = []
    for path, payload in iter_uc_sidecars():
        uc_id = str(payload.get("id", "<unknown>"))
        rel = path.relative_to(REPO)
        declared_st = declared_sourcetypes_for(payload)
        declared_ix = declared_indexes_for(payload)
        for field in _SPL_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            for finding in check_one_spl_field(
                uc_id=uc_id,
                file_label=str(rel),
                field=field,
                spl=value,
                vocab=vocab,
                declared_sourcetypes=declared_st,
                declared_indexes=declared_ix,
            ):
                if _SEV_RANK[finding.severity] >= threshold:
                    out.append(finding)
    return out


def _summarise(findings: list[Finding]) -> dict[str, Any]:
    by_sev: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_cat: dict[str, int] = {}
    by_uc: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        by_uc[f.uc_id] = by_uc.get(f.uc_id, 0) + 1
    return {
        "total": len(findings),
        "by_severity": by_sev,
        "by_category": by_cat,
        "ucs_with_findings": len(by_uc),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0] if __doc__ else "")
    p.add_argument(
        "--severity",
        default="LOW",
        choices=["HIGH", "MEDIUM", "LOW"],
        help="Minimum severity to report.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any HIGH-severity finding is present (CI gate).",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit human output to first N findings (0 = no limit).",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary (suppress per-finding detail).",
    )
    args = p.parse_args(argv)

    # Build the vocabulary once and pass it through so we don't pay the
    # CIM-paths build twice (once in run_audit, once for provenance).
    vocab = build_vocabulary()
    findings = run_audit(min_severity=args.severity, vocab=vocab)
    summary = _summarise(findings)

    if args.json:
        out = {
            "summary": summary,
            "sources": vocab.sources,
            "vocabulary": {
                "commands": len(vocab.commands),
                "macros": len(vocab.macros),
                "sourcetypes": len(vocab.sourcetypes),
                "indexes": len(vocab.indexes),
                "datamodel_paths": len(vocab.datamodel_paths),
                "eval_functions": len(vocab.eval_functions),
                "stats_functions": len(vocab.stats_functions),
            },
            "findings": [asdict(f) for f in findings],
        }
        json.dump(out, sys.stdout, indent=2, sort_keys=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write("audit-spl-references summary\n")
        sys.stdout.write("=" * 60 + "\n")
        if vocab.sources:
            for src in vocab.sources:
                sys.stdout.write(f"  reference corpus: {src.get('name', '?')}\n")
        else:
            sys.stdout.write(
                "  reference corpus: <none>  (Splunk-core baseline only --\n"
                "    run `python -m tools.research.build_spl_reference` to enrich)\n"
            )
        sys.stdout.write(f"  vocab sizes: commands={len(vocab.commands)}, ")
        sys.stdout.write(f"macros={len(vocab.macros)}, ")
        sys.stdout.write(f"sourcetypes={len(vocab.sourcetypes)}, ")
        sys.stdout.write(f"datamodels={len(vocab.datamodel_paths)}\n")
        sys.stdout.write("\n")
        sys.stdout.write(f"  findings: total={summary['total']}\n")
        for sev in ("HIGH", "MEDIUM", "LOW"):
            sys.stdout.write(f"    {sev:7s} {summary['by_severity'].get(sev, 0)}\n")
        sys.stdout.write(f"  unique UCs with findings: {summary['ucs_with_findings']}\n")
        sys.stdout.write("\n")
        sys.stdout.write("  by category:\n")
        for cat, n in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
            sys.stdout.write(f"    {cat:35s} {n}\n")
        if not args.summary_only and findings:
            sys.stdout.write("\n  findings detail:\n")
            shown = findings if args.limit <= 0 else findings[: args.limit]
            for f in shown:
                sys.stdout.write("    " + f.human() + "\n")
            if args.limit and len(findings) > args.limit:
                sys.stdout.write(
                    f"    ... ({len(findings) - args.limit} more, use --limit 0 to see all)\n"
                )

    if args.check and summary["by_severity"].get("HIGH", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
