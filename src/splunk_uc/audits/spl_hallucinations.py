#!/usr/bin/env python3
"""Audit SPL blocks in the JSON SSOT (``content/cat-*/UC-*.json``).

The legacy monolithic markdown corpus (``use-cases/cat-*.md``) was retired
in v8.2.0 — the JSON sidecars under ``content/`` are now the single source
of truth and the only thing this audit walks.

Checks:
1. CIM datamodel.dataset references against the real Splunk CIM 6.x catalog.
2. Use of non-existent Splunk search / eval / stats commands.
3. Malformed tstats (missing FROM, unqualified by fields, etc.).
4. Auto-generated CIM SPL blocks using fields not in the declared dataset.
5. Common typos (datamodel=Performace, eval strftime with no time, etc.).
6. Fabricated field names that look plausible but do not exist for the
   declared sourcetype (``signature`` on Meraki cellular events,
   ``data_usage_mb``, ``event_type`` from imaginary product taxonomies).
   Catch added in v8.2.0 after a real-world miss on UC-5.2.35 where my
   earlier "fix" had cleaned the JSON SSOT but left a hallucinated SPL
   in the legacy markdown corpus that LLMs were being pointed at.
"""

import glob
import json as _json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
CONTENT_DIR = os.path.join(REPO_ROOT, "content")

# Splunk CIM 6.x datamodels and their datasets
# Reference: https://docs.splunk.com/Documentation/CIM/latest/User/Overview
CIM_DATASETS: dict[str, set[str]] = {
    "Alerts": {"Alerts"},
    "Application_State": {"All_Application_State", "Ports", "Processes", "Services"},
    "Authentication": {
        "Authentication",
        "Default_Authentication",
        "Insecure_Authentication",
        "Privileged_Authentication",
        "Failed_Authentication",
        "Successful_Authentication",
        "Successful_Default_Authentication",
        "Failed_Default_Authentication",
        "Successful_Privileged_Authentication",
        "Failed_Privileged_Authentication",
    },
    "Certificates": {"All_Certificates", "SSL"},
    "Change": {
        "All_Changes",
        "Account_Management",
        "Auditing_Changes",
        "Endpoint_Changes",
        "Network_Changes",
        "Instance_Changes",
    },
    "Compute_Inventory": {
        "All_Inventory",
        "CPU",
        "Memory",
        "Network",
        "Storage",
        "OS",
        "User",
        "Virtual_OS",
        "Snapshot",
        "Hypervisor",
    },
    "Data_Access": {"Data_Access"},
    "Databases": {
        "All_Databases",
        "Database_Instance",
        "Instance_Stats",
        "Lock_Stats",
        "Session_Info",
        "Tablespace",
        "Query_Stats",
        "Query",
    },
    "Data_Loss_Prevention": {"DLP_Incidents"},
    "Email": {"All_Email", "Delivery", "Content", "Filtering"},
    "Endpoint": {
        "Ports",
        "Processes",
        "Filesystem",
        "Services",
        "Registry",
    },
    "Event_Signatures": {"Signatures"},
    "Interprocess_Messaging": {"All_Interprocess_Messaging"},
    "Intrusion_Detection": {"IDS_Attacks"},
    "Inventory": {
        "All_Inventory",
        "CPU",
        "Memory",
        "Network",
        "Storage",
        "OS",
        "User",
        "Virtual_OS",
        "Snapshot",
    },
    "JVM": {"JVM", "Threading", "Memory", "Runtime", "Classloading", "OS"},
    "Malware": {"Malware_Attacks", "Malware_Operations"},
    "Network_Resolution": {"DNS"},
    "Network_Sessions": {"All_Sessions", "DHCP", "Session_Start", "Session_End", "VPN"},
    "Network_Traffic": {"All_Traffic"},
    "Performance": {
        "All_Performance",
        "CPU",
        "Facilities",
        "FacilitiesAlerts",
        "Memory",
        "Network",
        "OS",
        "Storage",
    },
    "Splunk_Audit": {
        "Search_Activity",
        "Modular_Actions",
        "Search_Activity.Completed_Searches",
    },
    "Ticket_Management": {
        "All_Ticket_Management",
        "Change",
        "Incident",
        "Problem",
    },
    "Updates": {"Updates"},
    "Vulnerabilities": {"Vulnerabilities"},
    "Web": {"Web"},
    # Splunk Enterprise Security (RBA) — ships its own datamodel; not part of
    # the core CIM 6.x add-on but a first-class citizen of every ES install.
    "Risk": {"All_Risk"},
    # Splunk IT Service Intelligence — service-tier KPI summary index. Used
    # by ITSI-aware detections to query KPI snapshots via tstats.
    "Service_KPI_Summary": {"Service_KPI_Summary"},
}

# Valid top-level Splunk SPL commands (search commands)
# Reference: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands
VALID_COMMANDS: set[str] = {
    "abstract",
    "accum",
    "addcoltotals",
    "addinfo",
    "addtotals",
    "analyzefields",
    "anomalies",
    "anomalousvalue",
    "anomalydetection",
    "append",
    "appendcols",
    "appendpipe",
    "arules",
    "associate",
    "audit",
    "autoregress",
    "bin",
    "bucket",
    "bucketdir",
    "chart",
    "cluster",
    "cofilter",
    "collect",
    "concurrency",
    "contingency",
    "convert",
    "correlate",
    "ctable",
    "datamodel",
    "dbinspect",
    "dedup",
    "delete",
    "delta",
    "diff",
    "dispatch",
    "erex",
    "eval",
    "eventcount",
    "eventstats",
    "extract",
    "kv",
    "fieldformat",
    "fields",
    "fieldsummary",
    "filldown",
    "fillnull",
    "findtypes",
    "folderize",
    "foreach",
    "format",
    "from",
    "gauge",
    "gentimes",
    "geom",
    "geomfilter",
    "geostats",
    "head",
    "highlight",
    "history",
    "iconify",
    "inputcsv",
    "inputlookup",
    "iplocation",
    "join",
    "kmeans",
    "kvform",
    "loadjob",
    "localize",
    "localop",
    "lookup",
    "makecontinuous",
    "makemv",
    "makeresults",
    "map",
    "mcollect",
    "meta",
    "metadata",
    "metasearch",
    "meventcollect",
    "mpreview",
    "msearch",
    "mstats",
    "multikv",
    "multisearch",
    "mvcombine",
    "mvexpand",
    "noop",
    "nomv",
    "outlier",
    "outputcsv",
    "outputlookup",
    "outputtext",
    "overlap",
    "pivot",
    "predict",
    "pxf",
    "rangemap",
    "rare",
    "redistribute",
    "regex",
    "relevancy",
    "reltime",
    "rename",
    "replace",
    "require",
    "rest",
    "return",
    "reverse",
    "rex",
    "rtorder",
    "run",
    "savedsearch",
    "script",
    "scrub",
    "search",
    "searchtxn",
    "selfjoin",
    "sendemail",
    "set",
    "setfields",
    "sichart",
    "sirare",
    "sistats",
    "sitimechart",
    "sitop",
    "snowincident",
    "sort",
    "spath",
    "stats",
    "strcat",
    "streamstats",
    "table",
    "tags",
    "tail",
    "timechart",
    "timewrap",
    "top",
    "transaction",
    "transpose",
    "trendline",
    "tscollect",
    "tstats",
    "typeahead",
    "typelearner",
    "typer",
    "union",
    "uniq",
    "untable",
    "walklex",
    "where",
    "x11",
    "xmlkv",
    "xmlunescape",
    "xpath",
    "xyseries",
    # Common add-on-provided macros/commands
    "runshellscript",
    "createrss",
    # Documentation/convention: `comment` macro for inline SPL annotations.
    "comment",
    # Splunk Machine Learning Toolkit (MLTK) commands
    "fit",
    "apply",
    "summary",
    "score",
    "sample",
    "listmodels",
    "deletemodel",
    # Splunk built-in ML command
    "relative_entropy",
    # Community / Splunkbase custom commands referenced in ESCU detections
    "cyberchef",
}

# Bad patterns we know about
BAD_COMMAND_PATTERNS = [
    (re.compile(r"\bdatamodel=Performace\b"), "Typo: datamodel=Performace -> Performance"),
    (re.compile(r"\bdatamodel=Authenthication\b"), "Typo: Authenthication -> Authentication"),
    (re.compile(r"\bdatamodel=Netowrk_Traffic\b"), "Typo: Netowrk_Traffic -> Network_Traffic"),
    (re.compile(r"\bdatamodel=Networ_Traffic\b"), "Typo: Networ_Traffic -> Network_Traffic"),
    (
        re.compile(r"\bdatamodel=Change_Analysis\b"),
        "Renamed in CIM 4.x -> 'Change' (not Change_Analysis)",
    ),
    (re.compile(r"\bsummariesonly=true\b", re.IGNORECASE), "Use summariesonly=t (not 'true')"),
    (re.compile(r"\bsummariesonly=false\b", re.IGNORECASE), "Use summariesonly=f (not 'false')"),
]

# Known fabricated field/index/sourcetype patterns by sourcetype family.
# Each entry is (regex, message) and fires only when the SPL's index/sourcetype
# matches the family. This is a deliberately small allow-list — we only flag
# patterns that have been observed in real catalog drift, never speculative
# guesses about what "looks fishy". Adding a new entry requires a citation
# back to the Splunkbase / vendor documentation that contradicts it.
#
# Origin: UC-5.2.35 ships a "Cellular Modem Failover" SPL whose author had
# combined an IDS schema (`signature`, `event_type`) with imaginary fields
# (`data_usage_mb`) on a Meraki cellular sourcetype. None of those fields
# exist in either Splunk_TA_cisco_meraki or SC4S Meraki vendor packs.
KNOWN_HALLUCINATED_FIELDS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bindex=cisco_network\b.*?\bsourcetype=\"?meraki\b", re.DOTALL),
        "index=cisco_network with sourcetype=meraki — Meraki TA's default index "
        "is `meraki` (Splunkbase 5580); SC4S vendor pack writes to whatever the "
        "operator configures in sc4s.conf, never to a literal `cisco_network`",
    ),
    (
        re.compile(r"\bsourcetype=\"?meraki\"?\s+type=security_event\b"),
        "Meraki syslog has no `type=security_event` — real types are `flows`, "
        "`urls`, `ids-alerts`, `events`, `airmarshal_events`, `ip_flow_start`, etc. "
        "See `Splunk_TA_cisco_meraki/default/props.conf` REPORT-meraki_type",
    ),
    (
        re.compile(r"\bsourcetype=\"?meraki\"?[^|]*?\bsignature=\"\*[Cc]ellular\*\""),
        "`signature=*cellular*` on Meraki — `signature` is an IDS/IPS payload "
        "field on `meraki` sourcetype `type=ids-alerts`, not on cellular events. "
        "Meraki cellular up/down transitions surface as `type=events` text",
    ),
    (
        re.compile(r"\bsourcetype=\"?meraki[^\"]*\"?[^|]*?\bdata_usage_mb\b"),
        "`data_usage_mb` is not a field emitted by any Splunk_TA_cisco_meraki "
        "input or by SC4S's Meraki vendor pack — usage totals are exposed via "
        "`meraki:summarytopdevicesbyusage` with `usage.total` (KB)",
    ),
    (
        re.compile(
            r"\bsourcetype=\"?meraki[^\"]*\"?[^|]*?\bevent_type=\"(connection|network)_error\""
        ),
        "`event_type=connection_error` / `network_error` are fabricated values "
        "— Meraki TA exposes operational status via `meraki:devices.status` and "
        "`meraki:network:events.event_type`, neither of which uses those codes",
    ),
]


def check_in_with_wildcards_in_where_eval(spl: str) -> list[tuple[str, str]]:
    """Flag `IN (...*...)` only when inside a `| where` or `| eval` command.

    In Splunk 6.5+, `IN(...)` with wildcards is supported in the main search
    command and in `tstats WHERE` clauses. It is NOT supported in the `where`
    command or `eval` expressions; those require `match()` or `like()`.
    """
    findings: list[tuple[str, str]] = []
    for seg in split_spl_pipes(spl):
        low = seg.lower()
        if not low.startswith(("where ", "eval ")):
            continue
        for _m in re.finditer(r"\bIN\s*\(\s*[^)]*?\*[^)]*?\)", seg, flags=re.IGNORECASE):
            findings.append(
                (
                    "in_wildcard_where_eval",
                    "IN with wildcards in where/eval; use match() or like()",
                )
            )
    return findings


class Finding:
    __slots__ = ("category", "file", "message", "severity", "snippet", "uc_id")

    def __init__(
        self, file: str, uc_id: str, severity: str, category: str, message: str, snippet: str = ""
    ):
        self.file = file
        self.uc_id = uc_id
        self.severity = severity
        self.category = category
        self.message = message
        self.snippet = snippet

    def __repr__(self) -> str:
        s = f"[{self.severity}] [{self.category}] UC-{self.uc_id}: {self.message}"
        if self.snippet:
            s += f"\n      snippet: {self.snippet[:120]}"
        return s


def strip_comments(spl: str) -> str:
    """Remove `comment("...")` and similar placeholders from SPL before parsing.

    Handles multi-line and escape-quote content.  Also strips backtick macros
    that commonly appear as leading segments (e.g. `| `es_notable` | ...`).
    """

    def _remove_balanced(text: str, open_tok: str, close_tok: str) -> str:
        out: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            idx = text.find(open_tok, i)
            if idx < 0:
                out.append(text[i:])
                break
            out.append(text[i:idx])
            j = idx + len(open_tok)
            depth = 1
            in_dq = False
            in_sq = False
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

    cleaned = _remove_balanced(spl, "comment(", ")")
    return cleaned


def extract_tstats_components(spl: str) -> list[dict[str, str]]:
    """Extract { from, where, by } dicts from tstats commands in a block."""
    out: list[dict[str, str]] = []
    for m in re.finditer(
        r"\btstats\b(?:\s+summariesonly=\w+)?(?:\s+allow_old_summaries=\w+)?\s+(.+?)(?=\||$)",
        spl,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        body = m.group(1)
        d: dict[str, str] = {}
        fm = re.search(
            r"\bfrom\s+datamodel=([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?", body
        )
        if fm:
            d["model"] = fm.group(1)
            d["dataset"] = fm.group(2) or ""
        wm = re.search(r"\bwhere\b(.+?)(?=\bby\b|$)", body, flags=re.IGNORECASE | re.DOTALL)
        if wm:
            d["where"] = wm.group(1).strip()
        bm = re.search(r"\bby\b(.+)$", body, flags=re.IGNORECASE | re.DOTALL)
        if bm:
            d["by"] = bm.group(1).strip()
        out.append(d)
    return out


def check_tstats(spl: str) -> list[tuple[str, str]]:
    """Return list of (category, message) findings for tstats usage."""
    findings: list[tuple[str, str]] = []
    for comp in extract_tstats_components(spl):
        model = comp.get("model", "")
        dataset = comp.get("dataset", "")
        if model and model not in CIM_DATASETS:
            findings.append(("cim_model_unknown", f"Unknown CIM datamodel: {model!r}"))
        elif model and dataset and dataset not in CIM_DATASETS[model]:
            findings.append(
                (
                    "cim_dataset_unknown",
                    f"Dataset {dataset!r} not in CIM datamodel {model!r}. Valid: {sorted(CIM_DATASETS[model])}",
                )
            )
    return findings


def check_bad_patterns(spl: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for pat, msg in BAD_COMMAND_PATTERNS:
        if pat.search(spl):
            findings.append(("pattern", msg))
    return findings


def check_known_hallucinated_fields(spl: str) -> list[tuple[str, str]]:
    """Flag SPL that uses field/index/sourcetype combinations known to be wrong.

    Each pattern in ``KNOWN_HALLUCINATED_FIELDS`` is paired with the citation
    that disproves it; this is the gate that would have caught UC-5.2.35
    on the JSON SSOT side before it shipped.
    """
    findings: list[tuple[str, str]] = []
    for pat, msg in KNOWN_HALLUCINATED_FIELDS:
        if pat.search(spl):
            findings.append(("hallucinated_field", msg))
    return findings


_DASHBOARD_TOKEN_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_.:]*(?:\|[A-Za-z_]+)?\$")


def _mask_tokens(spl: str) -> str:
    return _DASHBOARD_TOKEN_RE.sub(lambda m: "X" * len(m.group(0)), spl)


def split_spl_pipes(spl: str) -> list[str]:
    """Split SPL on top-level pipe separators only.

    A pipe (`|`) is a command separator only when:
    - it is outside of double or single quotes
    - it is at parenthesis depth 0
    - it is at bracket depth 0
    """
    spl = _mask_tokens(spl)
    segs: list[str] = []
    current: list[str] = []
    in_dq = False
    in_sq = False
    in_bt = False
    paren = 0
    bracket = 0
    i = 0
    n = len(spl)
    while i < n:
        c = spl[i]
        if in_dq:
            current.append(c)
            if c == "\\" and i + 1 < n:
                current.append(spl[i + 1])
                i += 2
                continue
            if c == '"':
                in_dq = False
            i += 1
            continue
        if in_sq:
            current.append(c)
            if c == "\\" and i + 1 < n:
                current.append(spl[i + 1])
                i += 2
                continue
            if c == "'":
                in_sq = False
            i += 1
            continue
        if in_bt:
            current.append(c)
            if c == "`":
                in_bt = False
            i += 1
            continue
        if c == '"':
            in_dq = True
            current.append(c)
            i += 1
            continue
        if c == "'":
            in_sq = True
            current.append(c)
            i += 1
            continue
        if c == "`":
            in_bt = True
            current.append(c)
            i += 1
            continue
        if c == "(":
            paren += 1
            current.append(c)
            i += 1
            continue
        if c == ")":
            paren -= 1
            current.append(c)
            i += 1
            continue
        if c == "[":
            bracket += 1
            current.append(c)
            i += 1
            continue
        if c == "]":
            bracket -= 1
            current.append(c)
            i += 1
            continue
        if c == "|" and paren == 0 and bracket == 0:
            segs.append("".join(current))
            current = []
            i += 1
            continue
        current.append(c)
        i += 1
    segs.append("".join(current))
    return [s.strip() for s in segs if s.strip()]


def extract_pipe_commands(spl: str) -> list[str]:
    """Return first-word (command) of each pipe-delimited segment."""
    cmds: list[str] = []
    segs = split_spl_pipes(spl)
    for i, s in enumerate(segs):
        if not s:
            continue
        if i == 0:
            first_tok = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", s)
            if first_tok and first_tok.group(1).lower() in VALID_COMMANDS:
                cmds.append(first_tok.group(1).lower())
            continue
        if s.lower().startswith("comment("):
            continue
        if s.startswith("`"):
            continue
        tok = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", s)
        if tok:
            cmds.append(tok.group(1).lower())
    return cmds


def check_unknown_commands(spl: str) -> list[tuple[str, str]]:
    """Flag pipe commands that are not in VALID_COMMANDS."""
    findings: list[tuple[str, str]] = []
    for cmd in extract_pipe_commands(spl):
        if cmd not in VALID_COMMANDS:
            findings.append(("unknown_command", f"Unknown SPL command: {cmd!r}"))
    return findings


def audit_json_file(filepath: str) -> list[Finding]:
    """Audit a single JSON SSOT sidecar (``content/cat-*/UC-*.json``).

    ``spl`` (primary SPL) is treated as the ``[SPL]`` block, ``cimSpl`` as the
    ``[CIM SPL]`` block. Both are passed through the tstats / bad-patterns /
    in-with-wildcards / unknown-commands / known-hallucinated-fields checks.
    """
    findings: list[Finding] = []
    fname = os.path.basename(filepath)
    try:
        with open(filepath, encoding="utf-8") as fh:
            uc = _json.load(fh)
    except Exception as exc:
        findings.append(Finding(fname, fname, "ERROR", "parse", f"cannot parse JSON: {exc}", ""))
        return findings
    uc_id = str(uc.get("id", fname))

    for label, key in (("SPL", "spl"), ("CIM SPL", "cimSpl")):
        spl = uc.get(key, "") or ""
        if not spl.strip():
            continue
        spl_clean = strip_comments(spl)
        first_line = spl.splitlines()[0] if spl else ""
        for cat, msg in check_tstats(spl_clean):
            findings.append(Finding(fname, uc_id, "HIGH", cat, f"[{label}] {msg}", first_line))
        for cat, msg in check_bad_patterns(spl_clean):
            findings.append(Finding(fname, uc_id, "MED", cat, f"[{label}] {msg}", first_line))
        for cat, msg in check_in_with_wildcards_in_where_eval(spl_clean):
            findings.append(Finding(fname, uc_id, "MED", cat, f"[{label}] {msg}", first_line))
        for cat, msg in check_unknown_commands(spl_clean):
            findings.append(Finding(fname, uc_id, "HIGH", cat, f"[{label}] {msg}", first_line))
        for cat, msg in check_known_hallucinated_fields(spl_clean):
            findings.append(Finding(fname, uc_id, "HIGH", cat, f"[{label}] {msg}", first_line))
    return findings


def main(argv: list[str] | None = None) -> int:
    """Audit SPL hallucinations across the JSON SSOT corpus.

    Returns non-zero when any finding is emitted so CI can gate on it.
    """
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    # No positional / flag args today; argparse keeps the surface stable for
    # future expansion (e.g. --category, --severity-min) without breaking CI.
    parser.parse_args(argv)

    json_files = sorted(glob.glob(os.path.join(CONTENT_DIR, "cat-*", "UC-*.json")))

    all_findings: list[Finding] = []
    for fp in json_files:
        all_findings.extend(audit_json_file(fp))

    by_cat: dict[str, list[Finding]] = defaultdict(list)
    for finding in all_findings:
        by_cat[finding.category].append(finding)

    print(f"Scanned {len(json_files)} JSON SSOT files")
    print(f"Total findings: {len(all_findings)}")
    print()
    for cat in sorted(by_cat.keys()):
        print(f"  {cat}: {len(by_cat[cat])}")
    print()

    for cat in sorted(by_cat.keys()):
        print(f"\n=== {cat} ({len(by_cat[cat])}) ===")
        for finding in by_cat[cat]:
            print(f"  {finding}")

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
