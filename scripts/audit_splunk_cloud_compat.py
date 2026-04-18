#!/usr/bin/env python3
"""Audit SPL and content packs for Splunk Cloud (Victoria / Classic) compatibility.

The audit surfaces patterns known to fail `splunk-appinspect --mode=pre-cert`
or Splunk Cloud vetting:

1.  **SPL-level** patterns scanned across every UC ``q`` / ``qs`` field in
    ``catalog.json``. These are usually warnings; SPL can often be
    rewritten, but sometimes represents an intentional on-prem pattern.

2.  **Pack-level** patterns scanned across every ``.conf`` / manifest file
    in ``ta/``. These are hard failures for Splunk Cloud — custom search
    commands, modular inputs, REST endpoints, and bundled binaries are not
    permitted in the ``cloudvet`` gate.

Exit status
-----------
- 0 — no issues at any level
- 0 — SPL warnings only (unless ``--strict``)
- 1 — pack-level incompatibility detected, or ``--strict`` + any warning
- 2 — unexpected error

Output
------
Always writes ``docs/splunk-cloud-compat.md`` with tables per category and
per pack. CI can also upload ``test-results/splunk-cloud-compat.json`` as a
machine-readable artefact.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
TA_DIR = REPO_ROOT / "ta"
# Phase 1.8 of the gold-standard plan adds regulation-scoped apps generated
# by scripts/generate_splunk_app.py under splunk-apps/.  They must also
# pass Splunk Cloud vetting, so the audit scans both trees.
APP_DIRS = (
    REPO_ROOT / "ta",
    REPO_ROOT / "splunk-apps",
)
DOC_OUT = REPO_ROOT / "docs" / "splunk-cloud-compat.md"
JSON_OUT = REPO_ROOT / "test-results" / "splunk-cloud-compat.json"


# ---------------------------------------------------------------------- SPL rules
@dataclass(frozen=True)
class SplRule:
    id: str
    severity: str  # "fail" | "warn" | "info"
    pattern: re.Pattern[str]
    description: str
    remediation: str


SPL_RULES: list[SplRule] = [
    SplRule(
        id="CLOUD-SPL-001",
        severity="fail",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*runshellscript\b"),
        description="`| runshellscript` is an internal command not allowed in Splunk Cloud.",
        remediation="Move shell logic to a scripted input or an alert action.",
    ),
    SplRule(
        id="CLOUD-SPL-002",
        severity="fail",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*script\b"),
        description="`| script` invokes scripted lookups; Cloud requires the lookup to be allow-listed.",
        remediation="Replace with a KV-store lookup or a vendor-provided TA that ships the scripted lookup.",
    ),
    SplRule(
        id="CLOUD-SPL-003",
        severity="fail",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*crawl\b"),
        description="`| crawl` has been removed from Splunk Enterprise and is not available in Cloud.",
        remediation="Enumerate sources via ``| metadata type=sourcetypes`` / ``type=hosts`` instead.",
    ),
    SplRule(
        id="CLOUD-SPL-004",
        severity="warn",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*dbxquery\b"),
        description="`| dbxquery` requires Splunk DB Connect, which may not be present in every Cloud tenant.",
        remediation="Gate with a feature check, or pre-index the data via DB Connect inputs.",
    ),
    SplRule(
        id="CLOUD-SPL-005",
        severity="warn",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*sendemail\b"),
        description="`| sendemail` is deprecated; Cloud admins should use the built-in email alert action instead.",
        remediation="Configure the email action in `alert_actions.conf` (or the UI) rather than in SPL.",
    ),
    SplRule(
        id="CLOUD-SPL-006",
        severity="warn",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*rest\s+[^|]*(?:http|splunk_server_group)"),
        description="`| rest` to external URIs or non-standard server groups can be blocked by Cloud egress controls.",
        remediation="Query only local REST endpoints (no `http*` arg) or use a federated search head.",
    ),
    SplRule(
        id="CLOUD-SPL-007",
        severity="info",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*collect\b"),
        description="`| collect` writes to a summary index. Cloud allows it, but the target index must be provisioned.",
        remediation="Ensure the summary index referenced by `index=` is created in the tenant.",
    ),
    SplRule(
        id="CLOUD-SPL-008",
        severity="warn",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*loadjob\b"),
        description="`| loadjob` with a hardcoded sid is not portable across Cloud shards.",
        remediation="Use saved-search scheduling + `| loadjob savedsearch=\"app:user:name\"` or summary indexing.",
    ),
    SplRule(
        id="CLOUD-SPL-009",
        severity="warn",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*map\b(?![^|]*\bmaxsearches\s*=)"),
        description="`| map` fans out subsearches without a `maxsearches=` cap; Cloud enforces tight subsearch quotas.",
        remediation="Rewrite using `stats` or `mvexpand` when possible, or add `maxsearches=N` to the map command.",
    ),
    SplRule(
        id="CLOUD-SPL-010",
        severity="info",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*multisearch\b"),
        description="`| multisearch` is supported but can be rewritten to `| union` for clarity.",
        remediation="Prefer `| union` unless you specifically need the multisearch scheduler behaviour.",
    ),
    SplRule(
        id="CLOUD-SPL-011",
        severity="fail",
        pattern=re.compile(r"(?i)(?<![a-z_])\|\s*outputcsv\s+[^|]*\.\./"),
        description="`| outputcsv` pointing outside the app's lookups/ directory is blocked in Cloud.",
        remediation="Write only to plain filenames; Splunk resolves them under `$SPLUNK_HOME/etc/apps/<app>/lookups/`.",
    ),
]


# --------------------------------------------------------------------- pack rules
@dataclass(frozen=True)
class PackRule:
    id: str
    severity: str  # "fail" | "warn"
    filename_glob: str  # glob pattern the rule applies to
    pattern: re.Pattern[str]
    description: str
    remediation: str


PACK_RULES: list[PackRule] = [
    PackRule(
        id="CLOUD-PACK-001",
        severity="fail",
        filename_glob="**/commands.conf",
        pattern=re.compile(r"^\s*\[[^\]]+\]", re.MULTILINE),
        description="Custom search commands are not permitted in Splunk Cloud.",
        remediation="Remove commands.conf or refactor logic into SPL macros / saved searches.",
    ),
    PackRule(
        id="CLOUD-PACK-002",
        severity="fail",
        filename_glob="**/restmap.conf",
        pattern=re.compile(r"^\s*\[[^\]]+\]", re.MULTILINE),
        description="Custom REST endpoints are not permitted in Splunk Cloud.",
        remediation="Remove restmap.conf; drive automation from saved searches + alert actions.",
    ),
    PackRule(
        id="CLOUD-PACK-003",
        severity="fail",
        filename_glob="**/web.conf",
        pattern=re.compile(r"^\s*\[expose:[^\]]+\]", re.MULTILINE),
        description="`[expose:*]` stanzas in web.conf expose custom handlers; Cloud disallows.",
        remediation="Remove the [expose:*] stanza.",
    ),
    PackRule(
        id="CLOUD-PACK-004",
        severity="fail",
        filename_glob="**/inputs.conf",
        pattern=re.compile(r"^\s*\[script://", re.MULTILINE),
        description="`[script://]` scripted inputs are disallowed in Cloud Classic and require ACS vetting in Victoria.",
        remediation="Use Splunk Connect for Syslog / HEC / modular inputs shipped in vendor TAs.",
    ),
    PackRule(
        id="CLOUD-PACK-005",
        severity="fail",
        filename_glob="**/inputs.conf",
        pattern=re.compile(r"^\s*\[monitor://.*/var/log/\s*\]", re.MULTILINE),
        description="Absolute `/var/log/*` monitor stanzas imply local host access; not applicable in Cloud search head apps.",
        remediation="Remove monitor://* stanzas from the TA meant to run on search heads.",
    ),
    PackRule(
        id="CLOUD-PACK-006",
        severity="fail",
        filename_glob="**/authentication.conf",
        pattern=re.compile(r"^\s*\[authentication\]", re.MULTILINE),
        description="authentication.conf changes require Splunk Cloud Support ticket, not app install.",
        remediation="Remove authentication.conf.",
    ),
    PackRule(
        id="CLOUD-PACK-007",
        severity="fail",
        filename_glob="**/*.conf",
        pattern=re.compile(r"^\s*python\.version\s*=\s*python2", re.MULTILINE | re.IGNORECASE),
        description="`python.version = python2` is not allowed; Cloud supports python3 only.",
        remediation="Set `python.version = python3` (or remove the directive).",
    ),
    PackRule(
        id="CLOUD-PACK-008",
        severity="warn",
        filename_glob="**/transforms.conf",
        pattern=re.compile(r"^\s*external_cmd\s*=", re.MULTILINE),
        description="External lookup commands require the external script to be allow-listed.",
        remediation="Convert to CSV or KV Store lookup when possible.",
    ),
]


# ---------------------------------------------------------------------- findings
@dataclass
class Finding:
    rule_id: str
    severity: str
    location: str  # "UC-1.1.1" or "ta/TA-foo/default/inputs.conf:14"
    context: str
    message: str
    remediation: str


# ---------------------------------------------------------------------- SPL scan
def audit_spl() -> tuple[list[Finding], int]:
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        cat = json.load(fh)
    findings: list[Finding] = []
    total_ucs = 0
    for cat_entry in cat.get("DATA", []):
        for sc in cat_entry.get("s", []):
            for uc in sc.get("u", []):
                total_ucs += 1
                uc_id = uc.get("i") or ""
                for field in ("q", "qs"):
                    spl = uc.get(field) or ""
                    if not spl:
                        continue
                    for rule in SPL_RULES:
                        for m in rule.pattern.finditer(spl):
                            ctx = spl[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
                            findings.append(Finding(
                                rule_id=rule.id,
                                severity=rule.severity,
                                location=f"UC-{uc_id} ({field})",
                                context=ctx.strip(),
                                message=rule.description,
                                remediation=rule.remediation,
                            ))
    return findings, total_ucs


# ---------------------------------------------------------------------- pack scan
def audit_packs() -> list[Finding]:
    findings: list[Finding] = []
    for root in APP_DIRS:
        if not root.exists():
            continue
        for rule in PACK_RULES:
            for path in sorted(root.glob(rule.filename_glob)):
                if not path.is_file():
                    continue
                try:
                    text = path.read_text("utf-8", errors="replace")
                except Exception:
                    continue
                for m in rule.pattern.finditer(text):
                    line_no = text.count("\n", 0, m.start()) + 1
                    lines = text.splitlines()
                    ctx = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
                    findings.append(Finding(
                        rule_id=rule.id,
                        severity=rule.severity,
                        location=f"{path.relative_to(REPO_ROOT)}:{line_no}",
                        context=ctx,
                        message=rule.description,
                        remediation=rule.remediation,
                    ))
    return findings


# ---------------------------------------------------------------------- report
def render_report(spl_findings: list[Finding], pack_findings: list[Finding], total_ucs: int) -> str:
    def count_by_sev(findings: list[Finding]) -> dict[str, int]:
        out = {"fail": 0, "warn": 0, "info": 0}
        for f in findings:
            out[f.severity] = out.get(f.severity, 0) + 1
        return out

    spl_by_sev = count_by_sev(spl_findings)
    pack_by_sev = count_by_sev(pack_findings)
    uc_with_any = len({f.location.split(" ")[0] for f in spl_findings})

    lines = [
        "# Splunk Cloud compatibility audit",
        "",
        "Auto-generated by `scripts/audit_splunk_cloud_compat.py`. Do not edit by hand.",
        "",
        "## Summary",
        "",
        f"- UCs audited: **{total_ucs:,}**",
        f"- UCs with at least one finding: **{uc_with_any}**  "
        f"(fail={spl_by_sev['fail']}, warn={spl_by_sev['warn']}, info={spl_by_sev['info']})",
        f"- Pack-level findings: **{len(pack_findings)}**  "
        f"(fail={pack_by_sev['fail']}, warn={pack_by_sev['warn']})",
        "",
        "## Severity legend",
        "",
        "| Severity | Meaning |",
        "| -------- | ------- |",
        "| **fail** | Will be rejected by AppInspect / Splunk Cloud vetting. Must be fixed before ship. |",
        "| **warn** | May be rejected depending on tenant policy; likely needs remediation. |",
        "| **info** | Works in Cloud but has operational caveats (e.g. requires pre-provisioned index). |",
        "",
        "## Rule catalog",
        "",
        "### SPL rules",
        "",
        "| Rule | Severity | Description |",
        "| ---- | -------- | ----------- |",
    ]
    for r in SPL_RULES:
        lines.append(f"| {r.id} | {r.severity} | {r.description} |")
    lines.extend([
        "",
        "### Pack rules",
        "",
        "| Rule | Severity | Applies to | Description |",
        "| ---- | -------- | ---------- | ----------- |",
    ])
    for r in PACK_RULES:
        lines.append(f"| {r.id} | {r.severity} | `{r.filename_glob}` | {r.description} |")
    def _fmt_ctx(s: str) -> str:
        # GitHub-flavoured markdown: inside a table cell, literal `|` must be
        # escaped even when wrapped in backticks. `&#124;` renders cleanly.
        return s.replace("|", "&#124;")[:80]

    if pack_findings:
        lines.extend([
            "",
            "## Pack findings",
            "",
            "| Location | Rule | Severity | Context |",
            "| -------- | ---- | -------- | ------- |",
        ])
        for f in pack_findings:
            lines.append(f"| `{f.location}` | {f.rule_id} | {f.severity} | `{_fmt_ctx(f.context)}` |")
    else:
        lines.append("\n_No pack-level findings — packs are Splunk Cloud clean._\n")
    if spl_findings:
        lines.extend([
            "",
            "## SPL findings (top 50 by UC ID)",
            "",
            "| UC | Rule | Severity | Context |",
            "| -- | ---- | -------- | ------- |",
        ])
        shown = sorted(spl_findings, key=lambda f: f.location)[:50]
        for f in shown:
            lines.append(f"| {f.location} | {f.rule_id} | {f.severity} | `{_fmt_ctx(f.context)}` |")
        if len(spl_findings) > 50:
            lines.append(
                f"\n_…and {len(spl_findings) - 50} more. See `test-results/splunk-cloud-compat.json` for the full set._"
            )
    else:
        lines.append("\n_No SPL-level findings._\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------- cli
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on warnings (fail-level always fails).")
    parser.add_argument("--no-write", action="store_true",
                        help="Do not write the markdown/json outputs (CI dry-run).")
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print("catalog.json missing — run build.py first.", file=sys.stderr)
        return 2

    spl_findings, total_ucs = audit_spl()
    pack_findings = audit_packs()

    if not args.no_write:
        DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
        DOC_OUT.write_text(render_report(spl_findings, pack_findings, total_ucs), "utf-8")
        print(f"Wrote {DOC_OUT}")

        JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
        with JSON_OUT.open("w", encoding="utf-8") as fh:
            json.dump({
                "total_ucs": total_ucs,
                "spl_findings": [f.__dict__ for f in spl_findings],
                "pack_findings": [f.__dict__ for f in pack_findings],
            }, fh, indent=2)
        print(f"Wrote {JSON_OUT}")

    fails = sum(1 for f in spl_findings + pack_findings if f.severity == "fail")
    warns = sum(1 for f in spl_findings + pack_findings if f.severity == "warn")
    infos = sum(1 for f in spl_findings + pack_findings if f.severity == "info")
    print(f"Findings: fail={fails}, warn={warns}, info={infos}")

    if fails > 0:
        return 1
    if args.strict and warns > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
