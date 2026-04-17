#!/usr/bin/env python3
"""Audit SPL blocks in use-cases/cat-*.md for likely hallucinations.

Checks:
1. CIM datamodel.dataset references against the real Splunk CIM 6.x catalog.
2. Use of non-existent Splunk search / eval / stats commands.
3. Malformed tstats (missing FROM, unqualified by fields, etc.).
4. Invalid MITRE ATT&CK technique IDs (basic shape check).
5. Auto-generated CIM SPL blocks using fields not in the declared dataset.
6. Common typos (datamodel=Performace, eval strftime with no time, etc.).
"""

import glob
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES_DIR = os.path.join(REPO_ROOT, "use-cases")

UC_HEADER = re.compile(r"^### UC-(\d+\.\d+\.\d+)\b.*$", re.MULTILINE)
SPL_FENCE = re.compile(r"```spl\n(.*?)\n```", re.DOTALL)
CIM_SPL_MARKER = re.compile(r"^- \*\*CIM SPL[^*]*\*\*\s*$", re.MULTILINE)

# Splunk CIM 6.x datamodels and their datasets
# Reference: https://docs.splunk.com/Documentation/CIM/latest/User/Overview
CIM_DATASETS: Dict[str, Set[str]] = {
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
        # Windows-specific additions
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
}

# Valid top-level Splunk SPL commands (search commands)
# Reference: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands
VALID_COMMANDS: Set[str] = {
    "abstract", "accum", "addcoltotals", "addinfo", "addtotals", "analyzefields",
    "anomalies", "anomalousvalue", "anomalydetection", "append", "appendcols",
    "appendpipe", "arules", "associate", "audit", "autoregress", "bin", "bucket",
    "bucketdir", "chart", "cluster", "cofilter", "collect", "concurrency",
    "contingency", "convert", "correlate", "ctable", "datamodel", "dbinspect",
    "dedup", "delete", "delta", "diff", "dispatch", "erex", "eval", "eventcount",
    "eventstats", "extract", "kv", "fieldformat", "fields", "fieldsummary",
    "filldown", "fillnull", "findtypes", "folderize", "foreach", "format",
    "from", "gauge", "gentimes", "geom", "geomfilter", "geostats", "head",
    "highlight", "history", "iconify", "inputcsv", "inputlookup", "iplocation",
    "join", "kmeans", "kvform", "loadjob", "localize", "localop", "lookup",
    "makecontinuous", "makemv", "makeresults", "map", "mcollect", "meta",
    "metadata", "metasearch", "meventcollect", "mpreview", "msearch", "mstats",
    "multikv", "multisearch", "mvcombine", "mvexpand", "noop", "nomv", "outlier",
    "outputcsv", "outputlookup", "outputtext", "overlap", "pivot", "predict",
    "pxf", "rangemap", "rare", "redistribute", "regex", "relevancy", "reltime",
    "rename", "replace", "require", "rest", "return", "reverse", "rex", "rtorder",
    "run", "savedsearch", "script", "scrub", "search", "searchtxn", "selfjoin",
    "sendemail", "set", "setfields", "sichart", "sirare", "sistats", "sitimechart",
    "sitop", "snowincident", "sort", "spath", "stats", "strcat", "streamstats",
    "table", "tags", "tail", "timechart", "timewrap", "top", "transaction",
    "transpose", "trendline", "tscollect", "tstats", "typeahead", "typelearner",
    "typer", "union", "uniq", "untable", "walklex", "where", "x11", "xmlkv",
    "xmlunescape", "xpath", "xyseries",
    # Common add-on-provided macros/commands
    "sendemail", "runshellscript", "createrss",
    # ES-specific
    "savedsearch",
    # Documentation/convention: `comment` macro for inline SPL annotations.
    "comment",
    # Splunk Machine Learning Toolkit (MLTK) commands
    "fit", "apply", "summary", "score", "sample", "listmodels", "deletemodel",
    # Splunk built-in ML command
    "relative_entropy",
    # Community / Splunkbase custom commands referenced in ESCU detections
    "cyberchef",
}

# Valid eval function names (partial - common ones)
# Reference: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/EvalFunctions
VALID_EVAL_FUNCS: Set[str] = {
    "abs", "acos", "acosh", "asin", "asinh", "atan", "atan2", "atanh", "case",
    "ceiling", "ceil", "cidrmatch", "coalesce", "commands", "cos", "cosh",
    "exact", "exp", "floor", "hypot", "if", "in", "isbool", "isint", "isnotnull",
    "isnull", "isnum", "isstr", "json_array", "json_array_to_mv", "json_extract",
    "json_extract_exact", "json_keys", "json_object", "json_valid", "len",
    "like", "ln", "log", "lookup", "lower", "ltrim", "match", "max", "md5",
    "min", "mvappend", "mvcount", "mvdedup", "mvfilter", "mvfind", "mvindex",
    "mvjoin", "mvmap", "mvrange", "mvsort", "mvzip", "now", "null", "nullif",
    "pi", "pow", "printf", "random", "relative_time", "replace", "round",
    "rtrim", "searchmatch", "sha1", "sha256", "sha512", "sigfig", "sin", "sinh",
    "spath", "split", "sqrt", "strftime", "strptime", "substr", "tan", "tanh",
    "time", "tonumber", "tostring", "trim", "typeof", "upper", "urldecode",
    "urlencode", "validate", "cluster", "true", "false",
    # Custom but common
    "relative_time",
}

# Valid stats functions
VALID_STATS_FUNCS: Set[str] = {
    "avg", "mean", "count", "dc", "distinct_count", "earliest", "eval",
    "estdc", "estdc_error", "exactperc", "first", "last", "latest", "list",
    "max", "median", "min", "mode", "p", "perc", "percentile", "range", "rate",
    "stdev", "stdevp", "sum", "sumsq", "upperperc", "values", "var", "varp",
    "per_day", "per_hour", "per_minute", "per_second",
    # tstats-specific
    "prestats",
}

# Bad patterns we know about
BAD_COMMAND_PATTERNS = [
    (re.compile(r"\bdatamodel=Performace\b"), "Typo: datamodel=Performace -> Performance"),
    (re.compile(r"\bdatamodel=Authenthication\b"), "Typo: Authenthication -> Authentication"),
    (re.compile(r"\bdatamodel=Netowrk_Traffic\b"), "Typo: Netowrk_Traffic -> Network_Traffic"),
    (re.compile(r"\bdatamodel=Networ_Traffic\b"), "Typo: Networ_Traffic -> Network_Traffic"),
    (re.compile(r"\bdatamodel=Change_Analysis\b"), "Renamed in CIM 4.x -> 'Change' (not Change_Analysis)"),
    (re.compile(r"\bsummariesonly=true\b", re.IGNORECASE), "Use summariesonly=t (not 'true')"),
    (re.compile(r"\bsummariesonly=false\b", re.IGNORECASE), "Use summariesonly=f (not 'false')"),
]


def check_in_with_wildcards_in_where_eval(spl: str) -> List[Tuple[str, str]]:
    """Flag `IN (...*...)` only when inside a `| where` or `| eval` command.

    In Splunk 6.5+, `IN(...)` with wildcards is supported in the main search
    command and in `tstats WHERE` clauses. It is NOT supported in the `where`
    command or `eval` expressions; those require `match()` or `like()`.
    """
    findings: List[Tuple[str, str]] = []
    for seg in split_spl_pipes(spl):
        low = seg.lower()
        if not (low.startswith("where ") or low.startswith("eval ")):
            continue
        for m in re.finditer(r"\bIN\s*\(\s*[^)]*?\*[^)]*?\)", seg, flags=re.IGNORECASE):
            findings.append((
                "in_wildcard_where_eval",
                "IN with wildcards in where/eval; use match() or like()",
            ))
    return findings

# MITRE T-code pattern (T1234 or T1234.001)
MITRE_PATTERN = re.compile(r"\bT(\d{4})(?:\.(\d{3}))?\b")
# Known invalid patterns: T with wrong digit count, missing dot, etc.
MITRE_INVALID_PATTERNS = [
    re.compile(r"\bT\d{1,3}\b(?!\.)"),  # T123 (too few)
    re.compile(r"\bT\d{5,}\b"),  # T12345+ (too many)
]


class Finding:
    __slots__ = ("file", "uc_id", "severity", "category", "message", "snippet")

    def __init__(self, file: str, uc_id: str, severity: str, category: str, message: str, snippet: str = ""):
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
    # Iteratively remove `comment(...)` with balanced quotes
    def _remove_balanced(text: str, open_tok: str, close_tok: str) -> str:
        out: List[str] = []
        i = 0
        n = len(text)
        while i < n:
            idx = text.find(open_tok, i)
            if idx < 0:
                out.append(text[i:])
                break
            out.append(text[i:idx])
            # Scan for matching close, respecting quotes
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


def extract_tstats_components(spl: str) -> List[Dict[str, str]]:
    """Extract { from, where, by } dicts from tstats commands in a block."""
    out: List[Dict[str, str]] = []
    for m in re.finditer(
        r"\btstats\b(?:\s+summariesonly=\w+)?(?:\s+allow_old_summaries=\w+)?\s+(.+?)(?=\||$)",
        spl,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        body = m.group(1)
        d: Dict[str, str] = {}
        fm = re.search(r"\bfrom\s+datamodel=([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?", body)
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


def check_tstats(spl: str) -> List[Tuple[str, str]]:
    """Return list of (category, message) findings for tstats usage."""
    findings: List[Tuple[str, str]] = []
    for comp in extract_tstats_components(spl):
        model = comp.get("model", "")
        dataset = comp.get("dataset", "")
        if model and model not in CIM_DATASETS:
            findings.append(("cim_model_unknown", f"Unknown CIM datamodel: {model!r}"))
        elif model and dataset and dataset not in CIM_DATASETS[model]:
            findings.append((
                "cim_dataset_unknown",
                f"Dataset {dataset!r} not in CIM datamodel {model!r}. Valid: {sorted(CIM_DATASETS[model])}",
            ))
    return findings


def check_bad_patterns(spl: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    for pat, msg in BAD_COMMAND_PATTERNS:
        if pat.search(spl):
            findings.append(("pattern", msg))
    return findings


_DASHBOARD_TOKEN_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_.:]*(?:\|[A-Za-z_]+)?\$")


def _mask_tokens(spl: str) -> str:
    """Replace dashboard tokens `$foo|mod$` with a placeholder so splitters
    don't treat the internal `|` as a pipe separator.
    """
    return _DASHBOARD_TOKEN_RE.sub(lambda m: "X" * len(m.group(0)), spl)


def split_spl_pipes(spl: str) -> List[str]:
    """Split SPL on top-level pipe separators only.

    A pipe (`|`) is a command separator only when:
    - it is outside of double or single quotes
    - it is at parenthesis depth 0
    - it is at bracket depth 0

    Back-tick strings (macros like `comment(...)` via `macro`) are treated as
    atomic and never split internally.  Dashboard tokens like `$foo|s$` are
    masked out beforehand so their internal `|` is ignored.
    """
    spl = _mask_tokens(spl)
    segs: List[str] = []
    current: List[str] = []
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


def extract_pipe_commands(spl: str) -> List[str]:
    """Return first-word (command) of each pipe-delimited segment."""
    cmds: List[str] = []
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


def check_unknown_commands(spl: str) -> List[Tuple[str, str]]:
    """Flag pipe commands that are not in VALID_COMMANDS."""
    findings: List[Tuple[str, str]] = []
    for cmd in extract_pipe_commands(spl):
        if cmd not in VALID_COMMANDS:
            findings.append(("unknown_command", f"Unknown SPL command: {cmd!r}"))
    return findings


def extract_eval_funcs_used(spl: str) -> List[str]:
    """Return lowercase eval-ish function names invoked in the SPL (best-effort).

    Matches patterns like `eval x=foo(...)`, `where foo(...)`, or inline func
    calls following `,` or `=` in eval/where clauses.
    """
    funcs: List[str] = []
    # Scan eval/where segments only to avoid picking up stats functions.
    segs = re.split(r"\n?\|\s*", spl)
    for seg in segs:
        s = seg.strip()
        low = s.lower()
        if not (low.startswith("eval ") or low.startswith("where ") or low.startswith("foreach ")):
            continue
        for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", s):
            name = m.group(1).lower()
            # Skip Splunk SPL commands that can legitimately appear in eval args
            if name in {"if", "case", "match", "coalesce", "in"}:
                funcs.append(name)
                continue
            funcs.append(name)
    return funcs


def check_mitre_ids(mitre_line: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    for pat in MITRE_INVALID_PATTERNS:
        for m in pat.finditer(mitre_line):
            findings.append(("mitre", f"Malformed MITRE ID: {m.group(0)!r}"))
    return findings


def split_uc_blocks(text: str) -> List[Tuple[str, str]]:
    """Split markdown into (uc_id, body) tuples."""
    parts: List[Tuple[str, str]] = []
    matches = list(UC_HEADER.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts.append((uc_id, text[start:end]))
    return parts


def extract_spl_blocks_with_labels(body: str) -> List[Tuple[str, str]]:
    """Return list of (label, spl_text). Label is 'SPL' or 'CIM SPL' based on preceding marker."""
    out: List[Tuple[str, str]] = []
    # Find all ```spl blocks and figure out which marker precedes them.
    for m in SPL_FENCE.finditer(body):
        start = m.start()
        pre = body[:start]
        # Find last "- **SPL...**:" or "- **CIM SPL:**" before this block
        labels = list(re.finditer(r"^- \*\*(CIM SPL[^*]*|SPL[^*]*)\*\*", pre, flags=re.MULTILINE))
        if labels:
            lab = labels[-1].group(1).strip()
            if lab.upper().startswith("CIM SPL"):
                out.append(("CIM SPL", m.group(1)))
            else:
                out.append(("SPL", m.group(1)))
        else:
            out.append(("UNKNOWN", m.group(1)))
    return out


def audit_file(filepath: str) -> List[Finding]:
    findings: List[Finding] = []
    text = open(filepath, encoding="utf-8").read()
    fname = os.path.basename(filepath)

    for uc_id, body in split_uc_blocks(text):
        # Check MITRE line
        for mm in re.finditer(r"^- \*\*MITRE ATT&CK:\*\*\s*(.*)$", body, flags=re.MULTILINE):
            for cat, msg in check_mitre_ids(mm.group(1)):
                findings.append(Finding(fname, uc_id, "LOW", cat, msg, mm.group(1)))

        # Check each SPL block
        for label, spl in extract_spl_blocks_with_labels(body):
            spl_clean = strip_comments(spl)
            for cat, msg in check_tstats(spl_clean):
                findings.append(Finding(fname, uc_id, "HIGH", cat, f"[{label}] {msg}", spl.splitlines()[0] if spl else ""))
            for cat, msg in check_bad_patterns(spl_clean):
                findings.append(Finding(fname, uc_id, "MED", cat, f"[{label}] {msg}", spl.splitlines()[0] if spl else ""))
            for cat, msg in check_in_with_wildcards_in_where_eval(spl_clean):
                findings.append(Finding(fname, uc_id, "MED", cat, f"[{label}] {msg}", spl.splitlines()[0] if spl else ""))
            for cat, msg in check_unknown_commands(spl_clean):
                findings.append(Finding(fname, uc_id, "HIGH", cat, f"[{label}] {msg}", spl.splitlines()[0] if spl else ""))

    return findings


def main() -> int:
    files = sorted(glob.glob(os.path.join(USE_CASES_DIR, "cat-*.md")))
    all_findings: List[Finding] = []
    for f in files:
        all_findings.extend(audit_file(f))

    by_cat: Dict[str, List[Finding]] = defaultdict(list)
    for f in all_findings:
        by_cat[f.category].append(f)

    print(f"Scanned {len(files)} files")
    print(f"Total findings: {len(all_findings)}")
    print()
    for cat in sorted(by_cat.keys()):
        print(f"  {cat}: {len(by_cat[cat])}")
    print()

    # Print detailed findings grouped by category
    for cat in sorted(by_cat.keys()):
        print(f"\n=== {cat} ({len(by_cat[cat])}) ===")
        for f in by_cat[cat]:
            print(f"  {f}")

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
