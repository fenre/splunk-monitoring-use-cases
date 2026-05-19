#!/usr/bin/env python3
"""Emit SARIF 2.1.0 logs from catalogue audit JSON reports.

Lane D (2026-05-19): DevSecOps reporting surface for Splunk UC catalogue
findings. Converts normalized audit reports under ``dist/audits/`` into
SARIF logs consumable by GitHub Code Scanning, Azure DevOps, GitLab, and
Splunk SOAR ingestion pipelines.

Severity mapping (deterministic)::

    info  → note
    warn  → warning
    fail / high → error

Rule IDs follow ``splunk-uc:<audit>:<finding-kind>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDITS_DIR = REPO_ROOT / "dist" / "audits"
DEFAULT_OUT_DIR = REPO_ROOT / "dist" / "sarif"

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"
TOOL_NAME = "splunk-uc-catalogue-audits"
TOOL_URI = "https://github.com/splunk/splunk-monitoring-use-cases"
INFO_URI = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/"

_UC_ID_RE = re.compile(r"UC-\d+\.\d+\.\d+")
_SIDEcar_PATH_RE = re.compile(r"content/cat-\d+[^/]*/UC-\d+\.\d+\.\d+\.json")

# Audits whose JSON reports are converted to SARIF by default.
DEFAULT_AUDIT_REPORTS: dict[str, str] = {
    "spl-references": "spl-references.json",
    "spl-grammar": "spl-grammar.json",
    "spl-hallucinations": "spl-hallucinations.json",
    "content-quality": "content-quality.json",
    "prerequisites": "prerequisites.json",
    "uc-structure": "uc-structure.json",
}


@dataclass(frozen=True)
class AuditFinding:
    """One normalized finding from any audit report shape."""

    kind: str
    message: str
    severity: str  # info | warn | fail | high | medium | low (normalized downstream)
    file: str = ""
    uc_id: str = ""
    field: str = ""
    line: int = 1


@dataclass
class AuditReport:
    """Normalized in-memory view of one audit JSON report."""

    name: str
    version: str
    findings: list[AuditFinding] = field(default_factory=list)


@dataclass(frozen=True)
class SarifRule:
    rule_id: str
    name: str
    short_description: str
    full_description: str
    default_level: str


@dataclass(frozen=True)
class SarifResult:
    rule_id: str
    level: str
    message: str
    artifact_uri: str
    start_line: int
    properties: dict[str, Any]


@dataclass(frozen=True)
class SarifRun:
    audit_name: str
    tool_version: str
    results: list[SarifResult]
    rules: list[SarifRule]


def _read_version() -> str:
    version_path = REPO_ROOT / "VERSION"
    if version_path.is_file():
        return version_path.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _normalize_severity(raw: str) -> str:
    key = raw.strip().lower()
    if key in {"info", "note", "low"}:
        return "info"
    if key in {"warn", "warning", "medium", "med"}:
        return "warn"
    if key in {"fail", "error", "high", "critical", "serious"}:
        return "fail"
    return "warn"


def _sarif_level(severity: str, *, include_info: bool) -> str | None:
    norm = _normalize_severity(severity)
    if norm == "info":
        if not include_info:
            return None
        return "note"
    if norm == "warn":
        return "warning"
    return "error"


def _synthetic_line(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return 1 + (int(digest[:8], 16) % 999)


def _extract_uc_id(text: str) -> str:
    match = _UC_ID_RE.search(text)
    return match.group(0) if match else ""


def _sidecar_path_for_uc(uc_id: str) -> str:
    if not uc_id.startswith("UC-"):
        uc_id = f"UC-{uc_id}" if uc_id else ""
    if not uc_id:
        return "content/unknown/UC-unknown.json"
    parts = uc_id.removeprefix("UC-").split(".")
    if len(parts) != 3:
        return f"content/unknown/{uc_id}.json"
    cat = parts[0]
    return f"content/cat-{cat}-unknown/UC-{parts[0]}.{parts[1]}.{parts[2]}.json"


def _resolve_artifact_uri(
    *,
    file_hint: str,
    uc_id: str,
    message: str,
) -> str:
    if file_hint:
        path = file_hint.replace("\\", "/")
        if path.startswith(str(REPO_ROOT)):
            path = str(Path(path).relative_to(REPO_ROOT)).replace("\\", "/")
        if _SIDEcar_PATH_RE.search(path) or path.startswith("content/"):
            return path
    match = _SIDEcar_PATH_RE.search(message)
    if match:
        return match.group(0)
    uid = uc_id or _extract_uc_id(message)
    return _sidecar_path_for_uc(uid)


def _finding_from_dict(item: dict[str, Any], *, default_severity: str) -> AuditFinding | None:
    kind = str(
        item.get("category")
        or item.get("issue")
        or item.get("kind")
        or item.get("rule_id")
        or item.get("type")
        or "finding"
    )
    message = str(
        item.get("message")
        or item.get("issue")
        or item.get("description")
        or kind
    )
    if not message.strip():
        return None
    severity = str(item.get("severity") or default_severity)
    file_hint = str(item.get("file") or item.get("path") or item.get("location") or "")
    uc_id = str(item.get("uc_id") or item.get("id") or "")
    if uc_id and not uc_id.startswith("UC-"):
        uc_id = f"UC-{uc_id}"
    field = str(item.get("field") or "")
    line = item.get("line")
    start_line = int(line) if isinstance(line, int) and line > 0 else _synthetic_line(
        f"{file_hint}:{kind}:{message}"
    )
    return AuditFinding(
        kind=kind,
        message=message,
        severity=severity,
        file=file_hint,
        uc_id=uc_id,
        field=field,
        line=start_line,
    )


def _findings_from_prerequisites(payload: dict[str, Any]) -> list[AuditFinding]:
    out: list[AuditFinding] = []
    for msg in payload.get("errors") or []:
        if not isinstance(msg, str):
            continue
        kind = msg.split(":", 1)[0] if ":" in msg else "error"
        out.append(
            AuditFinding(
                kind=kind,
                message=msg,
                severity="fail",
                uc_id=_extract_uc_id(msg),
                line=_synthetic_line(msg),
            )
        )
    for msg in payload.get("warnings") or []:
        if not isinstance(msg, str):
            continue
        kind = msg.split(":", 1)[0] if ":" in msg else "warning"
        out.append(
            AuditFinding(
                kind=kind,
                message=msg,
                severity="warn",
                uc_id=_extract_uc_id(msg),
                line=_synthetic_line(msg),
            )
        )
    cycle = payload.get("cycle")
    if isinstance(cycle, list) and cycle:
        msg = "cycle: " + " -> ".join(str(x) for x in cycle)
        out.append(
            AuditFinding(
                kind="cycle",
                message=msg,
                severity="fail",
                uc_id=str(cycle[0]) if cycle else "",
                line=_synthetic_line(msg),
            )
        )
    return out


def load_audit_report(path: Path, *, audit_name: str | None = None) -> AuditReport:
    """Load any supported ``dist/audits/*.json`` report into ``AuditReport``."""
    name = audit_name or path.stem
    version = _read_version()
    if not path.is_file():
        return AuditReport(name=name, version=version, findings=[])

    raw = json.loads(path.read_text(encoding="utf-8"))
    findings: list[AuditFinding] = []

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                f = _finding_from_dict(item, default_severity="warn")
                if f is not None:
                    findings.append(f)
    elif isinstance(raw, dict):
        if "findings" in raw and isinstance(raw["findings"], list):
            for item in raw["findings"]:
                if isinstance(item, dict):
                    f = _finding_from_dict(item, default_severity="warn")
                    if f is not None:
                        findings.append(f)
        if "violations" in raw and isinstance(raw["violations"], list):
            for item in raw["violations"]:
                if isinstance(item, dict):
                    f = _finding_from_dict(item, default_severity="warn")
                    if f is not None:
                        findings.append(f)
        if "spl_findings" in raw and isinstance(raw["spl_findings"], list):
            for item in raw["spl_findings"]:
                if isinstance(item, dict):
                    f = _finding_from_dict(item, default_severity="fail")
                    if f is not None:
                        findings.append(f)
        if "errors" in raw or "warnings" in raw:
            findings.extend(_findings_from_prerequisites(raw))

    findings.sort(key=lambda f: (f.kind, f.file, f.uc_id, f.message))
    return AuditReport(name=name, version=version, findings=findings)


def _rule_id(audit_name: str, kind: str, *, rule_prefix: str) -> str:
    safe_kind = re.sub(r"[^a-zA-Z0-9._-]+", "-", kind).strip("-").lower() or "finding"
    prefix = rule_prefix.rstrip(":")
    return f"{prefix}:{audit_name}:{safe_kind}"


def audit_to_sarif_results(
    report: AuditReport,
    *,
    rule_prefix: str = "splunk-uc",
    include_info: bool = False,
    limit: int = 0,
) -> tuple[list[SarifResult], list[SarifRule]]:
    """Convert normalized findings to SARIF results + driver rules."""
    results: list[SarifResult] = []
    rules_map: dict[str, SarifRule] = {}

    items = report.findings if limit <= 0 else report.findings[:limit]
    for finding in items:
        level = _sarif_level(finding.severity, include_info=include_info)
        if level is None:
            continue
        rid = _rule_id(report.name, finding.kind, rule_prefix=rule_prefix)
        artifact_uri = _resolve_artifact_uri(
            file_hint=finding.file,
            uc_id=finding.uc_id,
            message=finding.message,
        )
        props: dict[str, Any] = {
            "audit": report.name,
            "kind": finding.kind,
            "severity": _normalize_severity(finding.severity),
        }
        if finding.uc_id:
            props["ucId"] = finding.uc_id
        if finding.field:
            props["field"] = finding.field

        results.append(
            SarifResult(
                rule_id=rid,
                level=level,
                message=finding.message,
                artifact_uri=artifact_uri,
                start_line=finding.line,
                properties=props,
            )
        )
        if rid not in rules_map:
            rules_map[rid] = SarifRule(
                rule_id=rid,
                name=finding.kind,
                short_description=finding.kind.replace("-", " "),
                full_description=f"Catalogue audit finding: {finding.kind}",
                default_level=level,
            )

    results.sort(key=lambda r: (r.rule_id, r.artifact_uri, r.start_line, r.message))
    rules = sorted(rules_map.values(), key=lambda r: r.rule_id)
    return results, rules


def build_sarif_run(
    audit_name: str,
    version: str,
    results: list[SarifResult],
    rules: list[SarifRule],
) -> SarifRun:
    """Wrap results in a single SARIF run with tool driver metadata."""
    return SarifRun(
        audit_name=audit_name,
        tool_version=version,
        results=results,
        rules=rules,
    )


def _run_to_dict(run: SarifRun) -> dict[str, Any]:
    artifacts: dict[str, dict[str, Any]] = {}
    for result in run.results:
        uri = result.artifact_uri
        if uri not in artifacts:
            artifacts[uri] = {"location": {"uri": uri}}

    return {
        "tool": {
            "driver": {
                "name": TOOL_NAME,
                "version": run.tool_version,
                "informationUri": INFO_URI,
                "rules": [
                    {
                        "id": rule.rule_id,
                        "name": rule.name,
                        "shortDescription": {"text": rule.short_description},
                        "fullDescription": {"text": rule.full_description},
                        "defaultConfiguration": {"level": rule.default_level},
                    }
                    for rule in run.rules
                ],
            }
        },
        "artifacts": list(artifacts.values()),
        "results": [
            {
                "ruleId": result.rule_id,
                "level": result.level,
                "message": {"text": result.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": result.artifact_uri},
                            "region": {"startLine": result.start_line},
                        }
                    }
                ],
                "properties": result.properties,
            }
            for result in run.results
        ],
        "invocations": [
            {
                "executionSuccessful": True,
                "commandLine": f"python -m splunk_uc generate-sarif --audit {run.audit_name}",
                "toolExecutionNotifications": [],
            }
        ],
    }


def build_sarif_log(runs: list[SarifRun]) -> dict[str, Any]:
    """Build the top-level SARIF log object."""
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [_run_to_dict(run) for run in runs],
    }


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def emit_sarif(
    audit_reports: dict[str, Path],
    out: Path,
    *,
    rule_prefix: str = "splunk-uc",
    include_info: bool = False,
    limit: int = 0,
) -> None:
    """Write combined + per-audit SARIF files under ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    runs: list[SarifRun] = []
    version = _read_version()

    for audit_name in sorted(audit_reports.keys()):
        report = load_audit_report(audit_reports[audit_name], audit_name=audit_name)
        results, rules = audit_to_sarif_results(
            report,
            rule_prefix=rule_prefix,
            include_info=include_info,
            limit=limit,
        )
        run = build_sarif_run(audit_name, version, results, rules)
        runs.append(run)
        per_audit_path = out / f"{audit_name}.sarif"
        per_payload = build_sarif_log([run])
        per_audit_path.write_text(_canonical_json(per_payload), encoding="utf-8")

    combined = build_sarif_log(runs)
    (out / "catalogue.sarif").write_text(_canonical_json(combined), encoding="utf-8")


def _discover_reports(audits_dir: Path) -> dict[str, Path]:
    reports: dict[str, Path] = {}
    for name, filename in DEFAULT_AUDIT_REPORTS.items():
        path = audits_dir / filename
        if path.is_file():
            reports[name] = path
    if not reports and audits_dir.is_dir():
        for path in sorted(audits_dir.glob("*.json")):
            reports[path.stem] = path
    return reports


def _check_outputs(out_dir: Path, expected: dict[str, Path]) -> int:
    version = _read_version()
    runs: list[SarifRun] = []
    for audit_name, report_path in sorted(expected.items()):
        report = load_audit_report(report_path, audit_name=audit_name)
        results, rules = audit_to_sarif_results(report)
        runs.append(build_sarif_run(audit_name, version, results, rules))

    combined_path = out_dir / "catalogue.sarif"
    if not combined_path.is_file():
        print(f"FATAL: missing {combined_path}", file=sys.stderr)
        return 1

    on_disk = combined_path.read_text(encoding="utf-8")
    expected_text = _canonical_json(build_sarif_log(runs))
    if on_disk != expected_text:
        print(f"FATAL: SARIF drift detected at {combined_path}", file=sys.stderr)
        return 1

    for audit_name in expected:
        per_path = out_dir / f"{audit_name}.sarif"
        if not per_path.is_file():
            print(f"FATAL: missing {per_path}", file=sys.stderr)
            return 1

    print(f"OK: SARIF outputs at {out_dir} match audit reports ({len(expected)} audit(s)).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--audits-dir",
        type=Path,
        default=DEFAULT_AUDITS_DIR,
        help=f"Directory of audit JSON reports (default: {DEFAULT_AUDITS_DIR.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--audit",
        action="append",
        dest="audits",
        metavar="AUDIT_NAME",
        help="Restrict to one audit (repeatable).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify on-disk SARIF matches current audit reports (no write).",
    )
    parser.add_argument(
        "--include-info",
        action="store_true",
        help="Include info/low findings as SARIF level note (default: warnings+errors only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cap findings per audit (0 = no cap).",
    )
    parser.add_argument(
        "--rule-prefix",
        default="splunk-uc",
        help="Prefix for SARIF ruleId values (default: splunk-uc).",
    )
    parser.add_argument(
        "--report",
        type=str,
        action="append",
        dest="reports",
        metavar="AUDIT=PATH",
        help="Explicit audit report mapping (e.g. spl-grammar=dist/audits/spl-grammar.json).",
    )
    args = parser.parse_args(argv)

    if args.reports:
        audit_reports: dict[str, Path] = {}
        for spec in args.reports:
            if "=" not in spec:
                print(f"FATAL: --report must be AUDIT=PATH, got {spec!r}", file=sys.stderr)
                return 2
            name, raw_path = spec.split("=", 1)
            audit_reports[name.strip()] = Path(raw_path.strip())
    else:
        audit_reports = _discover_reports(args.audits_dir)

    if args.audits:
        wanted = set(args.audits)
        audit_reports = {k: v for k, v in audit_reports.items() if k in wanted}

    if not audit_reports:
        print(
            f"WARN: no audit reports found under {args.audits_dir}; emitting empty SARIF.",
            file=sys.stderr,
        )

    if args.check:
        return _check_outputs(args.out, audit_reports)

    emit_sarif(
        audit_reports,
        args.out,
        rule_prefix=args.rule_prefix,
        include_info=args.include_info,
        limit=args.limit,
    )
    combined = args.out / "catalogue.sarif"
    n_results = sum(
        len(load_audit_report(p, audit_name=n).findings) for n, p in audit_reports.items()
    )
    print(
        f"Wrote {combined} (+ {len(audit_reports)} per-audit file(s), "
        f"{n_results} finding(s) from {len(audit_reports)} audit(s))."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
