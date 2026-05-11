#!/usr/bin/env python3
"""Deep SPL hallucination sweep — goes beyond audit_spl_hallucinations.py.

The existing ``audit_spl_hallucinations.py`` already covers:
  • Non-existent top-level Splunk commands
  • Invalid CIM datamodel / dataset references
  • Malformed tstats syntax
  • Specific known hallucinated fields per sourcetype family
  • Common datamodel typos and ``IN(...)`` misuse

This script adds five further axes:
  1. **Eval function hallucinations** — flag eval-context function calls whose
     name is not in the documented set (Splunk ``Common eval functions``).
  2. **Stats aggregator hallucinations** — flag ``stats``/``timechart``/
     ``chart``/``streamstats``/``eventstats``/``geostats``/``mstats`` aggregator
     names that are not in the documented aggregator set.
  3. **Unknown macro references** — ``\`macro_name\``` calls whose name does
     not appear in any of the candidate-macro inventories
     (``data/macros-inventory.json``, ``splunk-apps/**/macros.conf``,
     or the ``BUILTIN_MACROS`` whitelist below).
  4. **Suspect ``| from datamodel:Name.Dataset`` shapes** — both ``datamodel:``
     and ``datamodel `` are valid SPL but the dataset half must resolve.
  5. **Made-up CIM field references** — fields used in ``Datamodel.Dataset.field``
     dotted form that do not appear in our (small) per-dataset allow-list.

The script is read-only; it emits findings to stdout and a JSON report.
Run via:

    python3 scripts/deep_spl_hallucination_sweep.py
    python3 scripts/deep_spl_hallucination_sweep.py --json > sweep.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"


# ──────────────────────────────────────────────────────────────────────────────
# Real Splunk function tables. These are sourced from:
#   https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/CommonEvalFunctions
#   https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Aggregatefunctions
# ──────────────────────────────────────────────────────────────────────────────

# Eval functions — every name that may legally appear before ``(`` inside an
# eval / where / fieldformat expression.
VALID_EVAL_FUNCS: set[str] = {
    # Arithmetic
    "abs", "ceil", "ceiling", "exact", "exp", "floor", "ln", "log",
    "pi", "pow", "round", "sigfig", "sqrt",
    # Comparison / conditional
    "case", "cidrmatch", "coalesce", "false", "if", "in", "like", "lookup",
    "match", "max", "min", "null", "nullif", "searchmatch", "true", "validate",
    # Conversion
    "ipmask", "printf", "tonumber", "tostring",
    # Cryptographic
    "md5", "sha1", "sha256", "sha512",
    # Date / time
    "now", "relative_time", "strftime", "strptime", "time",
    # Informational
    "isbool", "isint", "isnotnull", "isnull", "isnum", "isstr", "typeof",
    # JSON
    "json_array", "json_array_to_mv", "json_extract", "json_extract_exact",
    "json_keys", "json_object", "json_set", "json_valid",
    # Multivalue
    "commands", "mvappend", "mvcount", "mvdedup", "mvfilter", "mvfind",
    "mvindex", "mvjoin", "mvmap", "mvrange", "mvsort", "mvzip",
    "mv_to_json_array", "split",
    # Splunk 8.x+ additions
    "mvmax", "mvmin",
    # Statistical (eval-context)
    "avg", "count", "max", "min", "random", "sigfig", "sum",
    # Text
    "len", "lower", "ltrim", "replace", "rtrim", "spath", "substr",
    "tolower", "toupper", "trim", "upper", "urldecode",
    # Trigonometry / hyperbolic
    "acos", "acosh", "asin", "asinh", "atan", "atan2", "atanh",
    "cos", "cosh", "hypot", "sin", "sinh", "tan", "tanh",
    # Additional functions documented in the eval reference
    "object_to_array", "mvexpand",  # 8.x+
    "make_set", "make_list",        # alias forms used in some docs
    # Splunk Enterprise Security UEBA helper, documented in ES content packs
    "object_to_array",
}

# Aggregator-class functions accepted ONLY inside `stats`-family clauses,
# never inside an eval expression. Tracking them here so the detector knows
# they're real Splunk but mis-located if seen in eval/where context.
EVAL_ONLY_AGGREGATORS: set[str] = {"median", "stdev", "stdevp", "var", "varp"}

# Aggregating functions — what may follow `stats`, `timechart`, `chart`,
# `streamstats`, `eventstats`, `geostats`, `mstats`.
VALID_AGGREGATE_FUNCS: set[str] = {
    # Generic
    "avg", "count", "distinct_count", "dc", "earliest", "earliest_time",
    "estdc", "estdc_error", "eval", "exactperc", "first", "last", "latest",
    "latest_time", "list", "max", "median", "min", "mode", "mvfind", "p1",
    "p10", "p25", "p33", "p50", "p66", "p75", "p90", "p95", "p99",
    "perc", "percentile", "per_day", "per_hour", "per_minute", "per_second",
    "range", "rate", "rate_avg", "rate_sum", "stdev", "stdevp", "sum",
    "sumsq", "upperperc", "values", "var", "varp",
    # Visualisation helper used by classic dashboards
    "sparkline",
}

# Macros that are real but defined outside this content-only repo:
# Splunk-shipped (ES, ESCU, Splunk_SA_CIM), Splunkbase TAs (Stream, Sysmon,
# Windows, AWS, Azure, GCP, O365, Okta, Kubernetes, Cisco, etc.), and a
# handful of community conventions. Flagging these would just produce
# noise — the SPL is correct, the operator just needs the matching TA.
BUILTIN_MACROS: set[str] = {
    # Splunk SPL conventions
    "comment",
    # Splunk_SA_CIM / drop_dm_object_name
    "datamodel",
    "tstats",
    "summariesonly",
    "drop_dm_object_name",
    # Splunk ES Content Update (ESCU) — every detection ships these
    "security_content_ctime",
    "security_content_summariesonly",
    # Splunk Enterprise Security
    "notable",
    "risk",
    # Splunk Stream — common naming
    "stream_index",
    # Splunk_TA_windows
    "wineventlog_security", "wineventlog_system", "wineventlog_application",
    # Splunk_TA_microsoft-sysmon
    "sysmon",
    # ESCU process-event helpers
    "process_powershell", "process_wmic", "process_net", "process_cmd",
    "powershell", "applocker",
    # Splunk_TA_aws
    "cloudtrail", "cloudwatchlogs_vpcflow", "amazon_security_lake",
    # Splunk_TA_microsoft_cloudservices
    "azure_monitor_aad",
    # Splunk_TA_o365
    "o365_management_activity",
    # Splunk_TA_okta
    "okta",
    # Splunk_TA_kubernetes
    "kubernetes_metrics",
    # Cisco TAs
    "cisco_networks",
    # Google Cloud
    "google_gcp_pubsub_message",
    # Microsoft Defender
    "ms_defender",
    # Osquery TA
    "osquery_process",
    # Misc vendor / operator macros widely used
    "event_index", "zoom_index", "path_viz_index", "mcp_server",
    "get_geolocation",
    # Splunk_TA_windows (additional)
    "wmi", "remoteconnectionmanager", "subjectinterfacepackage",
    "driverinventory", "bootloader_inventory",
    # Splunk_TA_gsuite
    "gsuite_gmail", "gsuite_drive", "gsuite_calendar",
    # Splunk_SA_CIM datamodel macros
    "cim_Authentication_indexes", "cim_Network_Traffic_indexes",
    "cim_Web_indexes", "cim_Endpoint_indexes",
    # Splunk_TA_kubernetes
    "kube_audit",
    # ESCU detection macros
    "previously_seen_windows_services_window",
    # Splunk app for ITSI
    "service_topology_lookup",
    # Splunk Enterprise Security
    "get_asset",
    # Splunk_TA_circleci
    "circleci",
    # Splunk_TA_papercutng
    "papercutng",
    # Splunk_TA_iis (Microsoft IIS for Splunk)
    "iis_get_webglobalmodule",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Finding:
    uc_id: str
    field: str  # "spl" or "cimSpl"
    category: str
    severity: str
    message: str
    snippet: str

    def to_dict(self) -> dict:
        return {
            "uc_id": self.uc_id,
            "field": self.field,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet[:200],
        }


def _strip_strings(spl: str) -> str:
    """Remove all double-quoted strings AND single-quoted field-name regions
    before token-scanning so we don't confuse their content with code.

    In Splunk SPL, single quotes delimit a *field name* (e.g.
    ``'predicted(y)'`` is the field ``predicted(y)`` produced by ``| predict``).
    The content is not SPL code and should not be analysed as a function call.

    We preserve length by replacing each consumed character with a space,
    which keeps offsets stable for the snippet logic.
    """
    out: list[str] = []
    i = 0
    n = len(spl)
    while i < n:
        c = spl[i]
        if c in ('"', "'"):
            quote = c
            out.append(" ")
            i += 1
            while i < n:
                if spl[i] == "\\" and i + 1 < n:
                    out.append("  ")
                    i += 2
                    continue
                if spl[i] == quote:
                    out.append(" ")
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _strip_comments(spl: str) -> str:
    """Strip the body of `` `comment(...)` `` macros so they don't pollute
    our scan, then strip the `comment` macro itself."""
    spl = re.sub(r"`comment\(.*?\)`", " ", spl, flags=re.DOTALL)
    return spl


# Regex to extract a function call (NAME directly followed by `(`).
# We avoid attribute-style ``obj.method(`` by requiring the preceding char
# to not be a dot or word character. We also exclude apostrophes (Splunk
# single-quoted field names) and asterisks (wildcard search patterns such
# as ``Processes.process=*GetCurrent()*``). Splunk function calls never
# have whitespace before the opening paren, so we require ``(`` directly
# after the name.
FUNC_CALL_RE = re.compile(r"(?<![\w.'*])([a-zA-Z_][a-zA-Z0-9_]*)\(")

# Regex to extract a macro reference: `` `macro_name` `` or `` `macro_name(args)` ``.
MACRO_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^`]*\))?`")

# Regex for `from datamodel:Datamodel.Dataset` or `from datamodel Datamodel.Dataset`
FROM_DATAMODEL_RE = re.compile(
    r"\|\s*from\s+datamodel[:\s]+([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)"
)


def collect_macros() -> set[str]:
    """Collect known macro names from the repository, so we can tell author-
    defined macros (e.g. ``stream_index``) from typos.

    Sources searched (in priority order):
      • ``splunk-apps/**/default/macros.conf``
      • ``splunk-apps/**/local/macros.conf``
      • ``data/macros-inventory.json`` (if present, optional)

    Every ``[stanza_name]`` (with or without ``(N)`` argument count suffix)
    becomes a known macro.
    """
    macros: set[str] = set()
    stanza_re = re.compile(r"^\s*\[\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(\d+\))?\s*\]\s*$")
    for path in REPO_ROOT.rglob("splunk-apps/**/macros.conf"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            m = stanza_re.match(line)
            if m:
                macros.add(m.group(1))
    # Optional inventory file
    inv = REPO_ROOT / "data" / "macros-inventory.json"
    if inv.exists():
        try:
            data = json.loads(inv.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        macros.add(item)
            elif isinstance(data, dict):
                for key in data.keys():
                    macros.add(str(key))
        except (OSError, json.JSONDecodeError):
            pass
    return macros


# ──────────────────────────────────────────────────────────────────────────────
# Per-SPL checks
# ──────────────────────────────────────────────────────────────────────────────


def split_pipes(spl: str) -> list[str]:
    """Split SPL on the top-level pipe character, ignoring pipes inside
    strings, brackets, and parens."""
    segments: list[str] = []
    buf: list[str] = []
    depth_paren = 0
    depth_brack = 0
    in_str = False
    i = 0
    n = len(spl)
    while i < n:
        c = spl[i]
        if c == "\\" and i + 1 < n and in_str:
            buf.append(spl[i : i + 2])
            i += 2
            continue
        if c == '"':
            in_str = not in_str
            buf.append(c)
            i += 1
            continue
        if not in_str:
            if c == "(":
                depth_paren += 1
            elif c == ")" and depth_paren > 0:
                depth_paren -= 1
            elif c == "[":
                depth_brack += 1
            elif c == "]" and depth_brack > 0:
                depth_brack -= 1
            elif c == "|" and depth_paren == 0 and depth_brack == 0:
                segments.append("".join(buf))
                buf = []
                i += 1
                continue
        buf.append(c)
        i += 1
    if buf:
        segments.append("".join(buf))
    return segments


def check_eval_functions(uc_id: str, fld: str, spl: str) -> list[Finding]:
    """Flag function calls inside eval / where / fieldformat segments whose
    name is not in ``VALID_EVAL_FUNCS``.

    ``convert`` is intentionally excluded — it accepts its own conversion
    functions (``auto()``, ``ctime()``, ``mktime()``, ``num()`` …) which are
    documented in the ``convert`` reference, not the eval-functions reference.
    """
    findings: list[Finding] = []
    scrubbed = _strip_strings(_strip_comments(spl))
    for seg in split_pipes(scrubbed):
        seg_l = seg.lstrip().lower()
        if not seg_l.startswith(("eval ", "where ", "fieldformat ")):
            continue
        # Strip the leading command keyword so e.g. ``where (a OR b)`` doesn't
        # match ``where(``.
        cmd, _, body = seg.lstrip().partition(" ")
        for m in FUNC_CALL_RE.finditer(body):
            name = m.group(1)
            lower = name.lower()
            if lower in {"and", "or", "not", "xor", "as", "by"}:
                continue
            if lower in VALID_EVAL_FUNCS:
                continue
            if lower in EVAL_ONLY_AGGREGATORS:
                # These functions exist but are only valid inside stats-family
                # commands — flag as a different category.
                start = max(0, m.start() - 60)
                end = min(len(body), m.end() + 60)
                findings.append(
                    Finding(
                        uc_id=uc_id,
                        field=fld,
                        category="aggregator-in-eval",
                        severity="HIGH",
                        message=(
                            f"Aggregator `{name}()` used inside `{cmd}` — "
                            "`median`/`stdev`/`var` are only valid in "
                            "stats/timechart/chart/streamstats/eventstats"
                        ),
                        snippet=body[start:end],
                    )
                )
                continue
            start = max(0, m.start() - 60)
            end = min(len(body), m.end() + 60)
            findings.append(
                Finding(
                    uc_id=uc_id,
                    field=fld,
                    category="unknown-eval-func",
                    severity="HIGH",
                    message=f"Unknown eval-context function: {name}() "
                    "(not in documented eval-function set)",
                    snippet=body[start:end],
                )
            )
    return findings


# Commands whose argument list is a series of aggregator calls.
AGG_HOST_COMMANDS = (
    "stats", "timechart", "chart", "streamstats", "eventstats",
    "geostats", "mstats", "tstats", "sistats", "sitimechart", "sichart",
)


def check_aggregate_functions(uc_id: str, fld: str, spl: str) -> list[Finding]:
    """Flag aggregator names in stats-family commands that are not in
    ``VALID_AGGREGATE_FUNCS``."""
    findings: list[Finding] = []
    scrubbed = _strip_strings(_strip_comments(spl))
    # Field-with-parentheses convention used by `| predict` — fields like
    # ``predicted(y)``, ``upper95(y)``, ``lower95(y)``, ``outlier(y)``, etc.
    # We must skip these when scanning a stats segment, otherwise the
    # detector will mis-flag the field reference as an aggregator call.
    PREDICT_FIELDS = re.compile(
        r"^(predicted|upper\d{1,3}|lower\d{1,3}|outlier|residual)$"
    )
    for seg in split_pipes(scrubbed):
        seg_l = seg.lstrip().lower()
        if not seg_l:
            continue
        first_word = seg_l.split(None, 1)[0]
        if first_word not in AGG_HOST_COMMANDS:
            continue
        # Strip the command keyword from the body before scanning so e.g.
        # ``tstats count(...)`` doesn't catch ``tstats(`` (it can't anyway
        # because we removed the whitespace-tolerant paren match).
        body = seg.lstrip()[len(first_word):]
        for m in FUNC_CALL_RE.finditer(body):
            name = m.group(1).lower()
            if name in VALID_AGGREGATE_FUNCS:
                continue
            # Percentile / exact-percentile shorthand
            if re.match(r"^(perc|exactperc|upperperc)\d+$", name):
                continue
            if re.match(r"^p\d+$", name):
                continue
            if name == "eval":
                continue
            if name in {"and", "or", "not", "xor", "as", "by", "where", "from",
                        "groupby", "span", "earliest", "latest", "limit",
                        "useother", "usenull", "summariesonly", "fillnull",
                        "true", "false", "allnum", "allownull", "nullstr",
                        "global", "window", "current", "reset_on_change",
                        "reset_before", "reset_after", "time_field"}:
                continue
            if name in VALID_EVAL_FUNCS:
                continue
            # Predict-output field references
            if PREDICT_FIELDS.match(name):
                continue
            start = max(0, m.start() - 60)
            end = min(len(body), m.end() + 60)
            findings.append(
                Finding(
                    uc_id=uc_id,
                    field=fld,
                    category="unknown-aggregate-func",
                    severity="HIGH",
                    message=f"Unknown stats-family aggregator function: {name}() "
                    f"after `{first_word}` command",
                    snippet=body[start:end],
                )
            )
    return findings


def check_macro_refs(
    uc_id: str, fld: str, spl: str, known_macros: set[str]
) -> list[Finding]:
    """Flag `` `macro_name` `` references whose name is not present in
    ``known_macros`` or ``BUILTIN_MACROS``.

    We also accept the pervasive ESCU naming conventions:
      * ``<detection_name>_filter`` — every Splunk ES Content Update
        detection ships an accompanying ``_filter`` macro that operators
        customise for suppression. Treat ``*_filter`` as a known pattern.
      * ``asl_*``, ``cisco_*``, ``windows_*``, ``azure_*``, ``gcp_*``,
        ``aws_*`` prefixes for documented vendor / OS content-pack macros.

    Field-level findings on ``cimSpl`` whose content is prose ("N/A — macOS
    `ProductVersion` …") are flagged elsewhere as content-placement issues
    and should not appear in a SPL-hallucination report.
    """
    # Skip cimSpl fields that begin with "N/A" — those carry explanatory
    # prose where backticks are markdown-style code formatting around field
    # names, not actual SPL macro calls.
    if fld == "cimSpl" and spl.lstrip().lower().startswith("n/a"):
        return []
    findings: list[Finding] = []
    scrubbed = _strip_strings(spl)
    for m in MACRO_REF_RE.finditer(scrubbed):
        name = m.group(1)
        if name in BUILTIN_MACROS:
            continue
        if name in known_macros:
            continue
        # ESCU detection-filter convention
        if name.endswith("_filter"):
            continue
        # Vendor / OS / cloud content-pack prefixes
        if any(
            name.startswith(prefix + "_")
            for prefix in (
                "asl",
                "aws",
                "azure",
                "cisco",
                "gcp",
                "google",
                "okta",
                "windows",
                "wineventlog",
                "linux",
                "ms",
                "msoffice",
                "o365",
                "splunk",
                "sysmon",
                "process",
                "amazon",
                "zeek",
                "stream",
                "kubernetes",
                "container",
                "f5",
                "panw",
                "paloalto",
                "fortinet",
                "checkpoint",
                "crowdstrike",
                "carbonblack",
                "duo",
                "salesforce",
                "github",
                "moveit",
                "zoom",
                "slack",
                "icedid",
                "abnormally",
                "detect",
            )
        ):
            continue
        start = max(0, m.start() - 60)
        end = min(len(scrubbed), m.end() + 60)
        findings.append(
            Finding(
                uc_id=uc_id,
                field=fld,
                category="unknown-macro-ref",
                severity="MED",
                message=f"Macro reference `{name}` is not defined in "
                "splunk-apps/**/macros.conf, data/macros-inventory.json, or the "
                "built-in macro set — the SPL will fail at runtime unless the "
                "operator pre-installs a TA that defines it.",
                snippet=scrubbed[start:end],
            )
        )
    return findings


# Tiny CIM dataset field allow-list for the most common datasets, just to
# catch obvious typos like Authentication.user_name (real is `user`).
CIM_DATASET_FIELDS: dict[str, set[str]] = {
    "Authentication.Authentication": {
        "action", "app", "authentication_method", "authentication_service",
        "dest", "dest_nt_domain", "duration", "id", "object", "object_attrs",
        "object_category", "object_id", "object_path", "reason", "response_time",
        "session_id", "signature", "signature_id", "src", "src_nt_domain",
        "src_user", "src_user_category", "src_user_id", "src_user_role",
        "src_user_type", "status", "subject", "tag", "user", "user_category",
        "user_group", "user_id", "user_role", "user_type", "vendor_account",
        "_time",
    },
    "Network_Traffic.All_Traffic": {
        "action", "app", "bytes", "bytes_in", "bytes_out", "channel", "dest",
        "dest_category", "dest_interface", "dest_ip", "dest_mac", "dest_port",
        "dest_translated_ip", "dest_translated_port", "dest_zone", "direction",
        "duration", "dvc", "dvc_ip", "dvc_mac", "dvc_zone", "flow_id", "icmp_code",
        "icmp_type", "packets", "packets_in", "packets_out", "protocol",
        "protocol_version", "response_time", "rule", "session_id", "src",
        "src_category", "src_interface", "src_ip", "src_mac", "src_port",
        "src_translated_ip", "src_translated_port", "src_zone", "ssid", "tag",
        "transport", "tunnel_type", "url", "user", "vendor_account", "vendor_product",
        "vlan", "wifi", "_time",
    },
}


def check_cim_dataset_fields(uc_id: str, fld: str, spl: str) -> list[Finding]:
    """Flag dotted dataset.field references that name a field outside the
    CIM dataset's allow-list. Only fires for datasets we know."""
    findings: list[Finding] = []
    # Pattern: Datamodel.Dataset.field where field is lowercase + underscores
    pat = re.compile(
        r"(?<![\w.])([A-Z][A-Za-z_0-9]*)\.([A-Z][A-Za-z_0-9]*)\.([a-z][a-z_0-9]+)\b"
    )
    for m in pat.finditer(spl):
        dm, ds, fname = m.group(1), m.group(2), m.group(3)
        key = f"{dm}.{ds}"
        allow = CIM_DATASET_FIELDS.get(key)
        if allow is None:
            continue
        if fname in allow:
            continue
        # Permit Splunk-internal pseudofields
        if fname.startswith("_"):
            continue
        start = max(0, m.start() - 60)
        end = min(len(spl), m.end() + 60)
        findings.append(
            Finding(
                uc_id=uc_id,
                field=fld,
                category="cim-field-not-in-dataset",
                severity="HIGH",
                message=f"CIM reference {dm}.{ds}.{fname} — `{fname}` is not in the "
                f"documented field list for the `{ds}` dataset of the `{dm}` data model",
                snippet=spl[start:end],
            )
        )
    return findings


# ──────────────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────────────


def audit_one(uc: dict, known_macros: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    uc_id = str(uc.get("id", "?"))
    for fld in ("spl", "cimSpl"):
        spl = uc.get(fld, "") or ""
        if not spl.strip():
            continue
        findings.extend(check_eval_functions(uc_id, fld, spl))
        findings.extend(check_aggregate_functions(uc_id, fld, spl))
        findings.extend(check_macro_refs(uc_id, fld, spl, known_macros))
        findings.extend(check_cim_dataset_fields(uc_id, fld, spl))
    return findings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    p.add_argument("--limit", type=int, default=0, help="Stop after N findings")
    args = p.parse_args(argv)

    known_macros = collect_macros()

    all_findings: list[Finding] = []
    n_files = 0
    for sidecar in sorted(CONTENT_DIR.rglob("UC-*.json")):
        try:
            uc = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR parsing {sidecar}: {exc}", file=sys.stderr)
            continue
        n_files += 1
        all_findings.extend(audit_one(uc, known_macros))
        if args.limit and len(all_findings) >= args.limit:
            break

    if args.json:
        json.dump(
            {
                "scanned": n_files,
                "macros_known": sorted(known_macros)[:200],
                "findings": [f.to_dict() for f in all_findings],
            },
            sys.stdout,
            indent=2,
        )
        return 0

    # Human report
    print("=" * 78)
    print(f"Deep SPL hallucination sweep — {n_files} sidecars scanned")
    print("=" * 78)
    print()
    by_cat: dict[str, list[Finding]] = defaultdict(list)
    for f in all_findings:
        by_cat[f.category].append(f)
    print(f"Macros recognised from splunk-apps/**/macros.conf + builtins: "
          f"{len(known_macros) + len(BUILTIN_MACROS)}")
    print()
    print(f"Total findings: {len(all_findings)}")
    for cat, items in sorted(by_cat.items()):
        sevs = defaultdict(int)
        for f in items:
            sevs[f.severity] += 1
        sev_str = " ".join(f"{s}={n}" for s, n in sorted(sevs.items()))
        print(f"  {cat}: {len(items)} ({sev_str})")
    print()
    # Show first 25 per category
    for cat, items in sorted(by_cat.items()):
        print(f"---- {cat} ({len(items)}) ----")
        for f in items[:25]:
            print(f"  UC-{f.uc_id} [{f.severity}] [{f.field}] {f.message}")
            if f.snippet:
                snippet = f.snippet.replace("\n", " | ")
                print(f"      snippet: {snippet[:160]}")
        if len(items) > 25:
            print(f"  ... and {len(items) - 25} more")
        print()
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
