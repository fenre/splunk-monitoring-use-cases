#!/usr/bin/env python3
"""Audit UC sidecar SPL for documented style and risk anti-patterns.

Complements ``audit-spl-grammar`` (structural bugs) and
``audit-spl-references`` (unknown identifiers) by flagging SPL that is
syntactically valid but violates catalogue quality standards: join,
makeresults, random(), hardcoded coalesce fallbacks, unbounded
transaction/streamstats, missing index discipline, and pipe-per-line
formatting.

The pattern catalogue lives in ``data/spl-anti-patterns.json``. The
audit emits a machine-readable offender queue under ``dist/audits/`` for
Lane N maintainers to burn down by hand.

Usage::

    python -m splunk_uc audit-spl-anti-patterns
    python -m splunk_uc audit-spl-anti-patterns --check --severity high
    python -m splunk_uc audit-spl-anti-patterns --out dist/audits
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from splunk_uc.audits.spl_grammar import _strip_comments

REPO = Path(__file__).resolve().parents[3]
DEFAULT_PATTERNS_PATH = REPO / "data" / "spl-anti-patterns.json"
DEFAULT_OUT_DIR = REPO / "dist" / "audits"

_SEV_RANK = {"high": 3, "medium": 2, "low": 1}

# Inline JSON Schema for data/spl-anti-patterns.json (no separate file).
_DATA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["version", "generated", "schema_version", "entries"],
    "additionalProperties": False,
    "properties": {
        "version": {"type": "string"},
        "generated": {"type": "string"},
        "schema_version": {"type": "string"},
        "entries": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "name",
                    "pattern",
                    "pattern_kind",
                    "severity",
                    "category",
                    "description",
                    "remediation",
                    "doc_anchor",
                ],
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string", "pattern": r"^ANTIPAT-\d{3}$"},
                    "name": {"type": "string", "minLength": 1},
                    "pattern": {"type": "string"},
                    "pattern_kind": {"type": "string", "enum": ["regex", "semantic", "ast"]},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "category": {"type": "string", "minLength": 1},
                    "description": {"type": "string", "minLength": 1},
                    "remediation": {"type": "string", "minLength": 1},
                    "doc_anchor": {"type": "string", "minLength": 1},
                },
            },
        },
    },
}

# Inline JSON Schema for dist/audits/spl-anti-patterns.json output.
_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["schema_version", "generated_at", "patterns_version", "matches", "summary"],
    "properties": {
        "schema_version": {"type": "string"},
        "generated_at": {"type": "string"},
        "patterns_version": {"type": "string"},
        "matches": {"type": "array"},
        "summary": {
            "type": "object",
            "required": [
                "total_ucs_scanned",
                "total_matches",
                "by_severity",
                "by_pattern",
                "top_offenders",
            ],
        },
    },
}

_SPL_FENCE_RE = re.compile(r"```spl\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class AntiPattern:
    id: str
    name: str
    pattern: str
    pattern_kind: str
    severity: str
    category: str
    description: str
    remediation: str
    doc_anchor: str
    _compiled: re.Pattern[str] | None = None


@dataclass(frozen=True)
class Match:
    entry_id: str
    pattern_name: str
    severity: str
    category: str
    uc_id: str
    field: str
    file: str
    line: int
    excerpt: str
    remediation: str
    doc_anchor: str


def _validate_schema(payload: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    """Minimal JSON Schema validator (no external dependency)."""
    errors = _validate_node(payload, schema, "$")
    if errors:
        raise ValueError(f"{label} schema validation failed:\n  " + "\n  ".join(errors))


def _validate_node(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object, got {type(value).__name__}"]
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required key {key!r}")
        allowed = schema.get("properties", {})
        for key, sub in allowed.items():
            if key in value:
                errors.extend(_validate_node(value[key], sub, f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in allowed:
                    errors.append(f"{path}: unexpected key {key!r}")
    elif expected == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array, got {type(value).__name__}"]
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} items")
        item_schema = schema.get("items", {})
        for idx, item in enumerate(value):
            errors.extend(_validate_node(item, item_schema, f"{path}[{idx}]"))
    elif expected == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string, got {type(value).__name__}")
        else:
            min_len = schema.get("minLength")
            if min_len is not None and len(value) < min_len:
                errors.append(f"{path}: string shorter than minLength {min_len}")
            pattern = schema.get("pattern")
            if pattern and not re.fullmatch(pattern, value):
                errors.append(f"{path}: does not match pattern {pattern!r}")
            enum = schema.get("enum")
            if enum is not None and value not in enum:
                errors.append(f"{path}: value {value!r} not in enum")
    return errors


def load_anti_patterns(path: Path) -> list[AntiPattern]:
    """Load and validate the anti-pattern catalogue."""
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    _validate_schema(payload, _DATA_SCHEMA, str(path))

    entries = payload["entries"]
    out: list[AntiPattern] = []
    for raw in entries:
        compiled: re.Pattern[str] | None = None
        if raw["pattern_kind"] == "regex" and raw["pattern"]:
            compiled = re.compile(raw["pattern"], re.IGNORECASE | re.MULTILINE | re.DOTALL)
        out.append(
            AntiPattern(
                id=raw["id"],
                name=raw["name"],
                pattern=raw["pattern"],
                pattern_kind=raw["pattern_kind"],
                severity=raw["severity"],
                category=raw["category"],
                description=raw["description"],
                remediation=raw["remediation"],
                doc_anchor=raw["doc_anchor"],
                _compiled=compiled,
            )
        )
    return out


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _excerpt(text: str, index: int, width: int = 120) -> str:
    start = max(0, index - 40)
    end = min(len(text), index + width)
    snippet = text[start:end].replace("\n", "\\n")
    return snippet.strip()


def _count_unquoted_pipes(line: str) -> int:
    """Return pipe count on a physical line outside quotes/backticks."""
    count = 0
    in_dq = in_sq = in_bt = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_dq:
            if c == "\\" and i + 1 < len(line):
                i += 2
                continue
            if c == '"':
                in_dq = False
        elif in_sq:
            if c == "\\" and i + 1 < len(line):
                i += 2
                continue
            if c == "'":
                in_sq = False
        elif in_bt:
            if c == "`":
                in_bt = False
        else:
            if c == '"':
                in_dq = True
            elif c == "'":
                in_sq = True
            elif c == "`":
                in_bt = True
            elif c == "|":
                count += 1
        i += 1
    return count


def _check_missing_index(spl: str) -> bool:
    cleaned = _strip_comments(spl)
    if re.search(r"(?i)\bindex\s*=", cleaned):
        return False
    if re.search(r"(?i)\bfrom\s+datamodel\s*=", cleaned):
        return False
    if re.search(r"(?i)\|\s*(?:tstats|inputlookup|makeresults|savedsearch)\b", cleaned):
        return False
    if cleaned.lstrip().startswith("|"):
        return False
    return bool(cleaned.strip())


def _check_missing_sourcetype(spl: str) -> bool:
    cleaned = _strip_comments(spl)
    if not re.search(r"(?i)\bindex\s*=", cleaned):
        return False
    if re.search(r"(?i)\bsourcetype\s*=", cleaned):
        return False
    if re.search(r"(?i)\bfrom\s+datamodel\s*=", cleaned):
        return False
    return True


def _check_multi_pipe_line(spl: str) -> list[int]:
    """Return 1-based line numbers with more than one unquoted pipe."""
    bad: list[int] = []
    for lineno, line in enumerate(spl.splitlines(), start=1):
        if _count_unquoted_pipes(line) > 1:
            bad.append(lineno)
    return bad


def _semantic_matches(pattern: AntiPattern, spl: str) -> list[tuple[int, str]]:
    """Run semantic detectors keyed by anti-pattern id."""
    if pattern.id == "ANTIPAT-008" and _check_missing_index(spl):
        return [(1, spl.splitlines()[0][:120] if spl.splitlines() else spl[:120])]
    if pattern.id == "ANTIPAT-009" and _check_missing_sourcetype(spl):
        first = spl.splitlines()[0] if spl.splitlines() else spl
        return [(1, first[:120])]
    if pattern.id == "ANTIPAT-010":
        return [
            (ln, line.strip()[:120])
            for ln, line in enumerate(spl.splitlines(), start=1)
            if _count_unquoted_pipes(line) > 1
        ]
    return []


def scan_spl(spl_text: str, patterns: list[AntiPattern]) -> list[Match]:
    """Scan one SPL string against all patterns; returns raw matches (no uc context)."""
    if not spl_text or not spl_text.strip():
        return []

    out: list[Match] = []
    for pattern in patterns:
        if pattern.pattern_kind == "semantic":
            for line, excerpt in _semantic_matches(pattern, spl_text):
                out.append(
                    Match(
                        entry_id=pattern.id,
                        pattern_name=pattern.name,
                        severity=pattern.severity,
                        category=pattern.category,
                        uc_id="",
                        field="",
                        file="",
                        line=line,
                        excerpt=excerpt,
                        remediation=pattern.remediation,
                        doc_anchor=pattern.doc_anchor,
                    )
                )
            continue

        if pattern._compiled is None:
            continue

        for m in pattern._compiled.finditer(spl_text):
            out.append(
                Match(
                    entry_id=pattern.id,
                    pattern_name=pattern.name,
                    severity=pattern.severity,
                    category=pattern.category,
                    uc_id="",
                    field="",
                    file="",
                    line=_line_number(spl_text, m.start()),
                    excerpt=_excerpt(spl_text, m.start()),
                    remediation=pattern.remediation,
                    doc_anchor=pattern.doc_anchor,
                )
            )
    return out


def _extract_spl_blocks(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (field_label, spl_text) pairs from a UC sidecar."""
    blocks: list[tuple[str, str]] = []
    for key in ("spl", "qs"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            blocks.append((key, value))

    di = payload.get("detailedImplementation")
    if isinstance(di, dict):
        nested = di.get("spl")
        if isinstance(nested, str) and nested.strip():
            blocks.append(("detailedImplementation.spl", nested))
    elif isinstance(di, str) and di.strip():
        for idx, block in enumerate(_SPL_FENCE_RE.findall(di)):
            if block.strip():
                blocks.append((f"detailedImplementation[spl#{idx + 1}]", block.strip()))

    return blocks


def scan_uc(
    uc_path: Path,
    patterns: list[AntiPattern],
) -> list[Match]:
    """Extract SPL from a UC sidecar and scan each block."""
    try:
        with uc_path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []

    uc_id = str(payload.get("id", uc_path.stem.removeprefix("UC-")))
    try:
        rel = str(uc_path.relative_to(REPO))
    except ValueError:
        rel = str(uc_path)

    out: list[Match] = []
    for field, spl_text in _extract_spl_blocks(payload):
        for raw in scan_spl(spl_text, patterns):
            out.append(
                Match(
                    entry_id=raw.entry_id,
                    pattern_name=raw.pattern_name,
                    severity=raw.severity,
                    category=raw.category,
                    uc_id=uc_id,
                    field=field,
                    file=rel,
                    line=raw.line,
                    excerpt=raw.excerpt,
                    remediation=raw.remediation,
                    doc_anchor=raw.doc_anchor,
                )
            )
    return out


def _sort_key(match: Match) -> tuple[int, str, str, str, int]:
    return (-_SEV_RANK.get(match.severity, 0), match.uc_id, match.entry_id, match.field, match.line)


def _build_summary(matches: list[Match], total_ucs: int) -> dict[str, Any]:
    by_sev = Counter(m.severity for m in matches)
    by_pattern = Counter(m.entry_id for m in matches)
    by_uc = Counter(m.uc_id for m in matches)
    top_offenders = [
        {"uc_id": uc_id, "match_count": count}
        for uc_id, count in by_uc.most_common(10)
    ]
    return {
        "total_ucs_scanned": total_ucs,
        "total_matches": len(matches),
        "by_severity": dict(sorted(by_sev.items(), key=lambda x: -_SEV_RANK.get(x[0], 0))),
        "by_pattern": dict(by_pattern.most_common()),
        "top_offenders": top_offenders,
    }


def evaluate_corpus(content_root: Path, patterns_path: Path) -> dict[str, Any]:
    """Walk content/cat-*/UC-*.json and build the offender queue."""
    patterns = load_anti_patterns(patterns_path)
    matches: list[Match] = []
    total_ucs = 0

    for path in sorted(content_root.glob("cat-*/UC-*.json")):
        total_ucs += 1
        matches.extend(scan_uc(path, patterns))

    matches.sort(key=_sort_key)
    patterns_meta: dict[str, Any] = {}
    with patterns_path.open(encoding="utf-8") as fh:
        meta = json.load(fh)
        patterns_meta["version"] = meta.get("version", "unknown")

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
        "patterns_version": patterns_meta["version"],
        "matches": [asdict(m) for m in matches],
        "summary": _build_summary(matches, total_ucs),
    }
    _validate_schema(report, _OUTPUT_SCHEMA, "output")
    return report


def render_markdown(report: dict[str, Any], patterns_path: Path) -> str:
    """Human-readable summary for maintainers."""
    summary = report["summary"]
    lines = [
        "# SPL anti-pattern audit",
        "",
        f"Generated: {report['generated_at']}",
        f"Patterns catalogue: `{patterns_path.relative_to(REPO)}` (v{report['patterns_version']})",
        "",
        "## Summary",
        "",
        f"- UCs scanned: **{summary['total_ucs_scanned']}**",
        f"- Total matches: **{summary['total_matches']}**",
        "",
        "### Severity histogram",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for sev in ("high", "medium", "low"):
        lines.append(f"| {sev} | {summary['by_severity'].get(sev, 0)} |")

    lines.extend(["", "### Pattern frequency", "", "| Pattern | Count |", "| --- | ---: |"])
    for pattern_id, count in summary["by_pattern"].items():
        lines.append(f"| {pattern_id} | {count} |")

    lines.extend(["", "## Top offenders", ""])
    if summary["top_offenders"]:
        lines.extend(["| UC ID | Matches |", "| --- | ---: |"])
        for row in summary["top_offenders"]:
            lines.append(f"| {row['uc_id']} | {row['match_count']} |")
    else:
        lines.append("_No offenders._")

    lines.extend(["", "## Remediation anchors", ""])
    seen: set[str] = set()
    for m in report["matches"][:50]:
        anchor = m["doc_anchor"]
        if anchor not in seen:
            seen.add(anchor)
            lines.append(f"- `{anchor}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], out_dir: Path, patterns_path: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "spl-anti-patterns.json"
    md_path = out_dir / "spl-anti-patterns.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report, patterns_path), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit UC SPL for documented anti-patterns.")
    p.add_argument(
        "--patterns",
        type=Path,
        default=DEFAULT_PATTERNS_PATH,
        help="Path to data/spl-anti-patterns.json",
    )
    p.add_argument(
        "--content",
        type=Path,
        default=REPO / "content",
        help="Root of the UC sidecar tree (default: content/)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (writes spl-anti-patterns.json + .md)",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when matches exceed --limit at or above --severity",
    )
    p.add_argument(
        "--severity",
        default="high",
        choices=["low", "medium", "high"],
        help="Minimum severity that counts toward --check failure (default: high)",
    )
    p.add_argument(
        "--include-pattern",
        action="append",
        default=[],
        metavar="ID",
        help="Only report matches for this ANTIPAT-xxx id (repeatable)",
    )
    p.add_argument(
        "--exclude-pattern",
        action="append",
        default=[],
        metavar="ID",
        help="Suppress matches for this ANTIPAT-xxx id (repeatable)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Allow up to N matches before --check fails (0 = zero tolerance)",
    )
    args = p.parse_args(argv)

    report = evaluate_corpus(args.content, args.patterns)
    threshold = _SEV_RANK[args.severity]
    filtered = [
        m
        for m in report["matches"]
        if _SEV_RANK.get(m["severity"], 0) >= threshold
        and (not args.include_pattern or m["entry_id"] in args.include_pattern)
        and m["entry_id"] not in args.exclude_pattern
    ]

    out_dir = args.out or DEFAULT_OUT_DIR
    if args.out is not None or not args.check:
        write_outputs(report, out_dir, args.patterns)
        if not args.check:
            sys.stdout.write(
                f"Wrote {out_dir / 'spl-anti-patterns.json'} "
                f"({report['summary']['total_matches']} matches)\n"
            )

    if args.check:
        actionable = len(filtered)
        if actionable > args.limit:
            sys.stderr.write(
                f"SPL anti-pattern audit: {actionable} match(es) at severity>={args.severity} "
                f"(limit={args.limit})\n"
            )
            shown = filtered[:20]
            for m in shown:
                sys.stderr.write(
                    f"  [{m['severity']}] UC-{m['uc_id']} ({m['file']}:{m['field']}:"
                    f"{m['line']}) {m['entry_id']} — {m['excerpt'][:80]}\n"
                )
            if len(filtered) > 20:
                sys.stderr.write(f"  ... ({len(filtered) - 20} more)\n")
            return 1
        sys.stdout.write(
            f"SPL anti-pattern audit: OK ({actionable} matches at severity>={args.severity}, "
            f"limit={args.limit})\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
