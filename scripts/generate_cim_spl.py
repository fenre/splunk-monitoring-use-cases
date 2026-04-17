#!/usr/bin/env python3
"""
Insert **CIM SPL:** fenced blocks for use cases that declare **CIM Models:**
but have no **CIM SPL:** block.

Run: python3 scripts/generate_cim_spl.py [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES_GLOB = os.path.join(REPO_ROOT, "use-cases", "cat-*.md")

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·", re.MULTILINE)
RE_CIM_MODELS = re.compile(r"^-\s+\*\*CIM Models:\*\*\s*(.*)$", re.MULTILINE)
RE_CIM_SPL_MARKER = re.compile(r"^-\s+\*\*CIM SPL:\*\*\s*$", re.MULTILINE)
RE_SPL_MARKER = re.compile(r"-\s+\*\*SPL(?:\s*\([^)]*\))?:\*\*")

NA_VALUES = frozenset(
    {"n/a", "na", "none", ""}
)

# Aliases / normalizations for common CIM model misspellings or shorthand
CIM_MODEL_ALIASES: Dict[str, str] = {
    "DLP": "Data_Loss_Prevention",
    "IDS": "Intrusion_Detection",
    "IPS": "Intrusion_Detection",
    "AV": "Malware",
    "Auth": "Authentication",
    "Change_Analysis": "Change",
    "Changes": "Change",
    "Netflow": "Network_Traffic",
    "NetFlow": "Network_Traffic",
}

CIM_MAP: Dict[str, Dict[str, object]] = {
    "Authentication": {
        "dataset": "Authentication",
        "fields": ["action", "app", "user", "src", "dest", "signature"],
        "default_by": ["action", "user", "src"],
    },
    "Change": {
        "dataset": "All_Changes",
        "fields": ["action", "object_category", "user", "dest", "object", "status"],
        "default_by": ["action", "object_category", "user"],
    },
    "Endpoint": {
        "dataset": "Processes",
        "fields": ["process_name", "user", "dest", "parent_process_name", "action"],
        "default_by": ["process_name", "user", "dest"],
    },
    "Network_Traffic": {
        "dataset": "All_Traffic",
        "fields": [
            "action",
            "src",
            "dest",
            "dest_port",
            "transport",
            "app",
            "bytes_in",
            "bytes_out",
        ],
        "default_by": ["action", "src", "dest", "dest_port"],
    },
    "Network_Resolution": {
        "dataset": "DNS",
        "fields": ["query", "query_type", "reply_code", "src", "dest", "answer"],
        "default_by": ["query", "reply_code", "src"],
    },
    "Web": {
        "dataset": "Web",
        "fields": ["url", "status", "http_method", "src", "dest", "action", "http_user_agent"],
        "default_by": ["status", "http_method", "dest"],
    },
    "Intrusion_Detection": {
        "dataset": "IDS_Attacks",
        "fields": ["action", "signature", "severity", "src", "dest", "category"],
        "default_by": ["action", "signature", "src", "dest"],
    },
    "Malware": {
        "dataset": "Malware_Attacks",
        "fields": ["action", "signature", "file_name", "dest", "user"],
        "default_by": ["action", "signature", "dest"],
    },
    "Alerts": {
        "dataset": "Alerts",
        "fields": ["severity", "signature", "src", "dest", "type", "app"],
        "default_by": ["severity", "signature", "app"],
    },
    "Email": {
        "dataset": "All_Email",
        "fields": ["action", "src_user", "recipient", "subject", "file_name"],
        "default_by": ["action", "src_user"],
    },
    "Performance": {
        "dataset": "CPU|Memory|Storage|Network",
        "fields": ["host", "cpu_load_percent", "mem_used", "storage_used_percent"],
        "default_by": ["host"],
    },
    "Vulnerabilities": {
        "dataset": "Vulnerabilities",
        "fields": ["severity", "signature", "dest", "category", "cvss"],
        "default_by": ["severity", "signature", "dest"],
    },
    "Data_Access": {
        "dataset": "Data_Access",
        "fields": ["action", "object", "user", "src"],
        "default_by": ["action", "object", "user"],
    },
    "Databases": {
        "dataset": "Database_Instance|Instance_Stats|Query|Query_Stats|Session_Info|Tablespace|Lock_Stats",
        "fields": ["host", "dest", "action", "query_type"],
        "default_by": ["host", "action"],
    },
    "Network_Sessions": {
        "dataset": "All_Sessions",
        "fields": ["action", "src", "dest", "user", "session_id"],
        "default_by": ["action", "src", "user"],
    },
    "Certificates": {
        "dataset": "All_Certificates",
        "fields": ["ssl_issuer", "ssl_subject_common_name", "ssl_end_time", "dest"],
        "default_by": ["ssl_subject_common_name", "dest"],
    },
    "Updates": {
        "dataset": "Updates",
        "fields": ["status", "signature", "dest", "vendor_product"],
        "default_by": ["status", "dest"],
    },
    "Inventory": {
        "dataset": "All_Inventory",
        "fields": ["dest", "category", "vendor_product", "os"],
        "default_by": ["dest", "category"],
    },
    "JVM": {
        "dataset": "Threading|Memory|Runtime|Classloading|OS",
        "fields": ["host", "jvm_description"],
        "default_by": ["host"],
    },
    "Ticket_Management": {
        "dataset": "All_Ticket_Management",
        "fields": ["status", "priority", "user", "category"],
        "default_by": ["status", "priority", "category"],
    },
    "Compute_Inventory": {
        "dataset": "Virtual_OS|Hypervisor|Snapshot|CPU|Memory|Network|Storage|OS",
        "fields": ["dest", "hypervisor", "status", "cpu_count", "mem"],
        "default_by": ["dest", "status"],
    },
    "Data_Loss_Prevention": {
        "dataset": "DLP_Incidents",
        "fields": ["action", "src", "dest", "user", "category", "signature"],
        "default_by": ["action", "src", "user"],
    },
}


# SPL token (field name) -> canonical CIM-ish name used in CIM_MAP fields lists
FIELD_ALIASES: Dict[str, str] = {
    "src_ip": "src",
    "source_ip": "src",
    "sourceipaddress": "src",
    "sourceaddress": "src",
    "client_ip": "src",
    "dst_ip": "dest",
    "dest_ip": "dest",
    "destination_ip": "dest",
    "dvc": "dest",
    "dvc_ip": "dest",
    "hostname": "dest",
    "src_user": "user",
    "src_user_id": "user",
    "user_id": "user",
    "user_name": "user",
    "username": "user",
    "account": "user",
    "process": "process_name",
    "proc": "process_name",
    "parent_process": "parent_process_name",
    "parent_proc": "parent_process_name",
    "url_domain": "dest",
    "domain": "dest",
    "dns_query": "query",
    "answer": "answer",
    "http_status": "status",
    "status_code": "status",
    "method": "http_method",
    "http_method": "http_method",
    "vendor_product": "vendor_product",
    "signature_id": "signature",
    "rule_name": "signature",
    "threat_name": "signature",
    "file_path": "file_name",
    "file": "file_name",
    "bucketname": "object",
    "bucket_name": "object",
    "object_name": "object",
    "arn": "user",
}


def normalize_cim_model_name(raw: str) -> str:
    """Extract the first CIM model name from a free-form string.

    Handles cases like:
    - "Authentication" -> "Authentication"
    - "Web (for access_combined when CIM-tagged)" -> "Web"
    - "DLP" -> "Data_Loss_Prevention"
    - "Network_Traffic when joined to firewall" -> "Network_Traffic"
    - "N/A (O365) + Network_Traffic for firewall side" -> "Network_Traffic"
      (skips leading N/A, picks first real model)
    - "Operational Telemetry (Metrics) where tagged; otherwise N/A" -> ""
      (not a real CIM model, returns empty)
    """
    s = raw.strip()
    if not s:
        return ""
    # Strip parenthetical annotations
    s = re.sub(r"\([^)]*\)", " ", s)
    # Split on common separators and iterate for first valid-looking token
    # Accept tokens that look like CIM model names: Word(_Word)* with known models
    parts = re.split(r"[,;/+]", s)
    candidates: List[str] = []
    for part in parts:
        # Further split on whitespace; take leading token-run of CIM-name shape
        part = part.strip()
        if not part:
            continue
        # Skip "N/A" tokens
        if part.lower() in ("n/a", "na", "none"):
            continue
        # Take only leading ModelName pattern (letters/underscores, stops at non-CIM words)
        m = re.match(r"^([A-Za-z][A-Za-z_]*(?:\s+[A-Z][A-Za-z_]*)*)", part)
        if not m:
            continue
        token = m.group(1).strip()
        # Convert spaces to underscores for multi-word models like "Network Traffic"
        token_under = re.sub(r"\s+", "_", token)
        # Apply aliases
        if token_under in CIM_MODEL_ALIASES:
            token_under = CIM_MODEL_ALIASES[token_under]
        candidates.append(token_under)
    # Pick first candidate that's in our CIM_MAP, else first candidate
    for c in candidates:
        if c in CIM_MAP:
            return c
    return candidates[0] if candidates else ""


def is_na_cim_value(val: str) -> bool:
    return val.strip().lower() in NA_VALUES


def split_uc_spans(text: str) -> List[Tuple[str, int, int]]:
    matches = list(RE_UC_HEAD.finditer(text))
    out: List[Tuple[str, int, int]] = []
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((uc_id, start, end))
    return out


def extract_spl_fenced(body: str) -> Optional[str]:
    m = RE_SPL_MARKER.search(body)
    if m is None:
        return None
    rest = body[m.end() :]
    lines = rest.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return None
    if not lines[i].strip().startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or not lines[i].strip().startswith("```"):
            return None
    i += 1
    inner: List[str] = []
    while i < len(lines):
        if lines[i].strip() == "```":
            return "\n".join(inner)
        inner.append(lines[i])
        i += 1
    return None


def _norm_token(t: str) -> str:
    t = t.strip()
    if not t:
        return ""
    # strip surrounding quotes
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        t = t[1:-1]
    # drop AS alias: "field as alias" -> field
    if re.search(r"\s+as\s+", t, re.I):
        t = re.split(r"\s+as\s+", t, maxsplit=1, flags=re.I)[0].strip()
    return t.strip()


def extract_by_field_tokens(spl: str) -> List[str]:
    """Collect likely split-by fields from SPL (best-effort)."""
    found: List[str] = []
    for m in re.finditer(r"(?i)\bby\s+(.+)$", spl, re.MULTILINE):
        chunk = m.group(1)
        # stop at pipe starting a new command (not inside parens — best effort)
        pipe = chunk.find("|")
        if pipe != -1:
            chunk = chunk[:pipe]
        for part in chunk.split(","):
            tok = _norm_token(part)
            if not tok or tok == "_time":
                continue
            # skip eval expressions
            if "(" in tok and ")" in tok:
                continue
            # dotted field: keep last segment for some mappings
            base = tok.split(".")[-1]
            if base:
                found.append(base)
    return found


def extract_stats_funcs(spl: str) -> List[Tuple[str, str]]:
    """Return list of (func_lower, inner_field) from stats/timechart/chart."""
    out: List[Tuple[str, str]] = []
    for m in re.finditer(
        r"(?i)\b(stats|timechart|chart|eventstats|sistats)\s+([^|]+)",
        spl,
    ):
        segment = m.group(2)
        for fn, inner in re.findall(
            r"(?i)\b(count|dc|distinct_count|sum|avg|mean|max|min|values|latest)\s*\(\s*([^)]+?)\s*\)",
            segment,
        ):
            inner_clean = inner.strip().strip("`").split(".")[-1]
            out.append((fn.lower(), inner_clean))
    return out


def detect_time_span(spl: str) -> Optional[str]:
    m = re.search(r"(?i)\btimechart\b[^|\n]*\bspan\s*=\s*(\S+)", spl)
    if m:
        return m.group(1).strip("\"'")
    m = re.search(r"(?i)\bbin\s+_time\b[^|\n]*\bspan\s*=\s*(\S+)", spl)
    if m:
        return m.group(1).strip("\"'")
    return None


def uses_time_aggregation(spl: str) -> bool:
    return bool(
        re.search(r"(?i)\btimechart\b", spl)
        or re.search(r"(?i)\bbin\s+_time\b", spl)
        or re.search(r"(?i)\bstreamstats\b.*\btime_window\b", spl)
    )


def canonical_field_token(tok: str, model: str) -> str:
    t = tok.strip().strip("`")
    tl = t.lower().replace("-", "_")
    if tl == "host":
        if model == "Performance":
            return "host"
        return "dest"
    if model == "Email" and tl in ("user", "sender", "from", "src"):
        return "src_user"
    return FIELD_ALIASES.get(tl, tl)


def performance_subdataset(spl: str) -> str:
    s = spl.lower()
    if any(k in s for k in ("vmstat", "memused", "swap", "memory", "oom")):
        return "Memory"
    if any(
        k in s
        for k in (
            "df",
            "inode",
            "iostat",
            "storage",
            "disk",
            "filesystem",
            "mount",
        )
    ):
        return "Storage"
    if any(k in s for k in ("network", "bytes", "nic", "interface", "tcp", "udp")):
        return "Network"
    return "CPU"


def databases_subdataset(spl: str) -> str:
    s = spl.lower()
    if "query" in s or "statement" in s or "sql" in s:
        return "Query"
    if "lock" in s or "deadlock" in s:
        return "Lock_Stats"
    if "tablespace" in s or "table_space" in s:
        return "Tablespace"
    if "session" in s or "connection" in s:
        return "Session_Info"
    if "instance" in s or "db2" in s or "sid" in s:
        return "Database_Instance"
    return "Instance_Stats"


def jvm_subdataset(spl: str) -> str:
    s = spl.lower()
    if "thread" in s or "deadlock" in s:
        return "Threading"
    if "gc" in s or "heap" in s or "memory" in s:
        return "Memory"
    if "class" in s or "classload" in s:
        return "Classloading"
    if "os" in s and ("cpu" in s or "load" in s):
        return "OS"
    return "Runtime"


def compute_inventory_subdataset(spl: str) -> str:
    s = spl.lower()
    if "snapshot" in s or "snap" in s:
        return "Snapshot"
    if "hypervisor" in s or "esxi" in s or "kvm" in s:
        return "Hypervisor"
    if "storage" in s or "disk" in s or "volume" in s:
        return "Storage"
    if "network" in s or "interface" in s or "nic" in s:
        return "Network"
    return "Virtual_OS"


def resolve_dataset(model: str, spl: str, spec: Dict[str, object]) -> str:
    raw_ds = str(spec["dataset"])
    if "|" not in raw_ds:
        return raw_ds
    if model == "Performance":
        return performance_subdataset(spl)
    if model == "Databases":
        return databases_subdataset(spl)
    if model == "JVM":
        return jvm_subdataset(spl)
    if model == "Compute_Inventory":
        return compute_inventory_subdataset(spl)
    return raw_ds.split("|")[0]


def qualify_field(model: str, dataset_obj: str, cim_field: str) -> str:
    if model == "Performance":
        return f"Performance.{cim_field}"
    return f"{dataset_obj}.{cim_field}"


def map_tokens_to_cim_fields(
    model: str,
    allowed: Sequence[str],
    tokens: Sequence[str],
) -> List[str]:
    allowed_set = set(allowed)
    out: List[str] = []
    for tok in tokens:
        c = canonical_field_token(tok, model)
        if c in allowed_set and c not in out:
            out.append(c)
    return out


def pick_numeric_cim_field(model: str, dataset_obj: str, spl: str, allowed: Sequence[str]) -> Optional[str]:
    """Pick a field for avg/sum tstats when SPL hints at a metric."""
    for _fn, inner in extract_stats_funcs(spl):
        mapped = map_tokens_to_cim_fields(model, allowed, [inner])
        if mapped:
            f = mapped[0]
            if f in ("bytes_in", "bytes_out", "cpu_load_percent", "mem_used", "storage_used_percent", "cvss"):
                return f
        c = canonical_field_token(inner, model)
        if model == "Performance":
            low = inner.lower()
            if "cpu" in low or "idle" in low or "load" in low:
                return "cpu_load_percent"
            if "mem" in low or "swap" in low:
                return "mem_used"
            if "disk" in low or "usepct" in low or "storage" in low or "inode" in low:
                return "storage_used_percent"
        if c in allowed and c not in ("action", "user", "src", "dest"):
            return c
    for name in allowed:
        if name.endswith("_percent") or name in ("bytes_in", "bytes_out", "cvss", "mem", "cpu_count"):
            return name
    return None


def choose_aggregation(
    model: str, dataset_obj: str, spl: str, allowed: Sequence[str]
) -> str:
    """
    Return tstats aggregation expression (without leading pipe), e.g.
    'count', 'dc(All_Traffic.src) as agg_value', 'avg(Performance.cpu_load_percent) as agg_value'
    """
    funcs = extract_stats_funcs(spl)
    uses_time = uses_time_aggregation(spl)

    if not funcs:
        return "count"

    primary_fn, primary_inner = funcs[-1]

    if primary_fn in ("dc", "distinct_count"):
        mapped = map_tokens_to_cim_fields(model, allowed, [primary_inner])
        if mapped:
            qf = qualify_field(model, dataset_obj, mapped[0])
            return f"dc({qf}) as agg_value"
        return "count"

    if primary_fn in ("sum", "avg", "mean") or (uses_time and primary_fn in ("avg", "mean")):
        hint = pick_numeric_cim_field(model, dataset_obj, spl, allowed)
        if hint:
            qf = qualify_field(model, dataset_obj, hint)
            fn = "sum" if primary_fn == "sum" else "avg"
            return f"{fn}({qf}) as agg_value"
        if primary_fn == "sum":
            for cand in ("bytes_in", "bytes_out"):
                if cand in allowed:
                    qf = qualify_field(model, dataset_obj, cand)
                    return f"sum({qf}) as agg_value"

    if primary_fn == "latest" and model == "Change":
        if "status" in allowed:
            qf = qualify_field(model, dataset_obj, "status")
            return f"latest({qf}) as agg_value"

    return "count"


def build_by_clause(
    model: str,
    dataset_obj: str,
    by_fields: Sequence[str],
    span: Optional[str],
) -> str:
    parts = [qualify_field(model, dataset_obj, f) for f in by_fields]
    clause = ", ".join(parts)
    if span:
        clause = f"{clause} span={span}"
    return clause


def generate_tstats_line(
    model: str,
    spl: Optional[str],
) -> str:
    spl_l = (spl or "").strip()
    if model not in CIM_MAP:
        return (
            "| tstats summariesonly=t count from datamodel="
            f"{model} by _time span=1h | sort - count"
        )

    spec = CIM_MAP[model]
    allowed = list(spec["fields"])
    default_by = list(spec["default_by"])
    dataset_obj = resolve_dataset(model, spl_l, spec)

    by_from_spl = extract_by_field_tokens(spl_l) if spl_l else []
    mapped_by = map_tokens_to_cim_fields(model, allowed, by_from_spl)
    if not mapped_by:
        mapped_by = list(default_by)

    span: Optional[str] = None
    if uses_time_aggregation(spl_l):
        span = detect_time_span(spl_l) or "1h"

    agg = choose_aggregation(model, dataset_obj, spl_l, allowed)
    dm = f"{model}.{dataset_obj}"

    by_clause = build_by_clause(model, dataset_obj, mapped_by, span)

    if agg == "count":
        line = f"| tstats summariesonly=t count from datamodel={dm} by {by_clause} | sort - count"
    else:
        line = (
            f"| tstats summariesonly=t {agg} from datamodel={dm} by {by_clause} | sort - agg_value"
        )

    return line


def format_cim_spl_block(spl_line: str) -> str:
    body = spl_line.rstrip()
    return (
        "- **CIM SPL:**\n"
        "```spl\n"
        f"{body}\n"
        "```"
    )


def insert_after_cim_models(uc_body: str, insertion: str) -> Optional[str]:
    m = RE_CIM_MODELS.search(uc_body)
    if not m:
        return None
    if RE_CIM_SPL_MARKER.search(uc_body):
        return None
    insert_at = m.end()
    return uc_body[:insert_at] + "\n" + insertion + uc_body[insert_at:]


def process_file(path: str, dry_run: bool) -> int:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    spans = split_uc_spans(text)
    if not spans:
        return 0

    new_parts: List[str] = []
    pos = 0
    added = 0

    for uc_id, start, end in spans:
        new_parts.append(text[pos:start])
        body = text[start:end]
        m_models = RE_CIM_MODELS.search(body)
        if m_models and not RE_CIM_SPL_MARKER.search(body):
            val = m_models.group(1).strip()
            if not is_na_cim_value(val):
                model = normalize_cim_model_name(val)
                # Only generate if model is known to CIM; otherwise skip rather
                # than emit an invalid tstats referencing an unknown datamodel.
                if model and model in CIM_MAP:
                    spl = extract_spl_fenced(body)
                    tstats_line = generate_tstats_line(model, spl)
                    block = format_cim_spl_block(tstats_line)
                    updated = insert_after_cim_models(body, block)
                    if updated is not None:
                        print(f"  {uc_id} ({model}): {tstats_line}")
                        body = updated
                        added += 1
                elif model:
                    print(f"  SKIP {uc_id}: unknown CIM model {model!r} (raw: {val!r})", file=sys.stderr)
        new_parts.append(body)
        pos = end
    new_parts.append(text[pos:])
    new_text = "".join(new_parts)

    if added and not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate **CIM SPL:** blocks for use cases.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned inserts without modifying files.",
    )
    args = ap.parse_args()

    files = sorted(glob.glob(USE_CASES_GLOB))
    if not files:
        print(f"No files matched {USE_CASES_GLOB}", file=sys.stderr)
        return 1

    per_file: Dict[str, int] = {}
    total = 0
    for path in files:
        n = process_file(path, args.dry_run)
        if n:
            per_file[path] = n
            total += n

    print()
    print("Summary — CIM SPL blocks added per file:")
    if not per_file:
        print("  (none)")
    else:
        for path, n in per_file.items():
            print(f"  {os.path.basename(path)}: {n}")
    print(f"Total: {total}")
    if args.dry_run and total:
        print("\nDry-run: no files were modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
