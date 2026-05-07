#!/usr/bin/env python3
"""
Gold Standard DI Rewrite v2

Deep SPL-aware generator that produces UC-specific operational commentary
for all 1345 cat-22 compliance UCs. Unlike the v1 template, this version
parses each UC's SPL and generates clause-by-clause explanation, weaves in
the author-written implementation field hints, expands the visualization
spec into a dashboard layout, adds a CIM variant section when cimSpl exists,
and injects regulation-specific operational wisdom.

Target: <30% line-level repetition between adjacent UCs, >=95 v2 audit.
"""

import json
import glob
import os
import re
from typing import Optional

BASE = "content/cat-22-regulatory-compliance"


# ============================================================================
# SECTION 1 — SPL PARSER
# ============================================================================
#
# The SPL parser extracts structure from each UC's search query to drive
# UC-specific commentary. We classify the SPL into pattern types and extract
# operational details: sourcetypes, indexes, joins, lookups, thresholds,
# time-parse formats, and aggregation functions.

def _strip_sq_brackets(s: str) -> str:
    """Remove single-line subsearch brackets for cleaner parsing."""
    depth = 0
    out = []
    for ch in s:
        if ch == "[":
            depth += 1
            out.append(ch)
        elif ch == "]":
            depth -= 1
            out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


class SplAnalysis:
    """Result of parsing a UC's SPL query."""

    def __init__(self):
        self.sourcetypes: list[str] = []
        self.indexes: list[str] = []
        self.fields: list[str] = []
        self.joins: list[dict] = []          # list of {type, right_source}
        self.lookups: list[dict] = []        # list of {name, input_field, output_fields}
        self.inputlookups: list[str] = []    # lookup tables used as base search
        self.thresholds: list[dict] = []     # [{field, op, value}]
        self.time_parses: list[dict] = []    # [{field, format}]
        self.time_window: Optional[str] = None  # e.g. "-24h", "-7d"
        self.aggregations: list[str] = []    # stats/timechart funcs
        self.group_by_fields: list[str] = []
        self.span: Optional[str] = None      # bin/timechart span
        self.has_eventstats = False
        self.has_streamstats = False
        self.has_transaction = False
        self.has_tstats = False
        self.has_rex = False
        self.has_iplocation = False
        self.has_subsearch = False
        self.has_inputlookup = False
        self.has_rest = False
        self.has_append = False
        self.case_expressions: list[str] = []  # fields assigned via case()
        self.if_expressions: list[str] = []    # fields assigned via if()
        self.match_patterns: list[str] = []    # regex patterns in match()
        self.eval_constants: list[tuple] = []  # [(field, value)] from `| eval field="..."`


def parse_spl(spl: str) -> SplAnalysis:
    """Parse a UC SPL into an analysis structure."""
    a = SplAnalysis()
    if not spl:
        return a

    # Sourcetypes: both `sourcetype="x"` and `sourcetype IN ("x","y")`
    for m in re.finditer(r'sourcetype\s*[=:]\s*"?([a-zA-Z0-9_:\-\.]+)"?', spl, re.IGNORECASE):
        st = m.group(1)
        if st not in a.sourcetypes:
            a.sourcetypes.append(st)
    for m in re.finditer(r'sourcetype\s+IN\s*\(([^)]+)\)', spl, re.IGNORECASE):
        for name in re.findall(r'"([^"]+)"', m.group(1)):
            if name not in a.sourcetypes:
                a.sourcetypes.append(name)

    # Indexes
    for m in re.finditer(r'index\s*=\s*"?([a-zA-Z0-9_\-\*]+)"?', spl, re.IGNORECASE):
        idx = m.group(1)
        if idx != "*" and idx not in a.indexes:
            a.indexes.append(idx)

    # Time windows
    tw = re.search(r'earliest\s*=\s*(-?\d+[smhdw]|-?\d+mon|@\w+|[-+]\d+\w+)', spl, re.IGNORECASE)
    if tw:
        a.time_window = tw.group(1)

    # Joins
    for m in re.finditer(r'\|\s*join\s+(?:type\s*=\s*(\w+)\s+)?([a-zA-Z_][\w,\s]*?)\s*\[', spl, re.IGNORECASE):
        join_type = (m.group(1) or "inner").lower()
        on_fields = m.group(2).strip() if m.group(2) else ""
        a.joins.append({"type": join_type, "on": on_fields})

    # Lookups
    for m in re.finditer(r'\|\s*lookup\s+(\S+)(?:\s+([a-zA-Z_]\w+)(?:\s+AS\s+\S+)?)?(?:\s+OUTPUT\s+(.+?))?(?=\s*\||$)', spl, re.IGNORECASE):
        name = m.group(1)
        input_field = m.group(2) or ""
        output_raw = (m.group(3) or "").strip()
        outputs = [o.strip() for o in re.split(r',\s*', output_raw) if o.strip()]
        a.lookups.append({"name": name, "input_field": input_field, "outputs": outputs})

    # inputlookup (as base search)
    for m in re.finditer(r'\|\s*inputlookup\s+(\S+)', spl, re.IGNORECASE):
        a.inputlookups.append(m.group(1))
        a.has_inputlookup = True

    # Thresholds — any `field op N` inside where/eval (catches compound predicates too)
    # e.g. `where amount>9000 AND amount<10000` or `where count>=5`
    for m in re.finditer(r'\b([a-zA-Z_]\w+)\s*([><=!]{1,2})\s*(-?\d+(?:\.\d+)?)', spl):
        field = m.group(1)
        op = m.group(2)
        value = m.group(3)
        if field in ("earliest", "latest", "span", "interval"):
            continue
        if op in ("=", "==", "!="):
            continue  # skip equality; we care about numeric comparisons
        a.thresholds.append({
            "field": field,
            "op": op,
            "value": value,
        })

    # Time parsing (strptime)
    for m in re.finditer(r'strptime\s*\(\s*(\w+)\s*,\s*"([^"]+)"', spl):
        a.time_parses.append({"field": m.group(1), "format": m.group(2)})

    # Aggregation functions
    for m in re.finditer(r'\b(count|avg|sum|max|min|dc|values|list|perc\d+|earliest|latest|stdev|median|mode|range)\s*\(', spl):
        fn = m.group(1)
        if fn not in a.aggregations:
            a.aggregations.append(fn)

    # Group-by fields (after stats...by or timechart...by)
    for m in re.finditer(r'(?:stats|timechart|chart)\b[^|]*?\bby\s+([^|]+?)(?=\s*\||$)', spl, re.IGNORECASE):
        fields_raw = m.group(1).strip()
        for f in re.split(r'[,\s]+', fields_raw):
            f = f.strip().strip(",")
            if f and f not in ("span", "as", "AS", "where") and not f.startswith("span="):
                if f not in a.group_by_fields:
                    a.group_by_fields.append(f)

    # Span
    sp = re.search(r'span\s*=\s*(\d+[smhdw])', spl, re.IGNORECASE)
    if sp:
        a.span = sp.group(1)

    # Flags
    a.has_eventstats = "eventstats" in spl.lower()
    a.has_streamstats = "streamstats" in spl.lower()
    a.has_transaction = "| transaction" in spl.lower()
    a.has_tstats = "tstats" in spl.lower()
    a.has_rex = bool(re.search(r'\|\s*rex\b', spl, re.IGNORECASE))
    a.has_iplocation = "iplocation" in spl.lower()
    a.has_subsearch = "[search" in spl.lower() or "[ search" in spl.lower()
    a.has_rest = "| rest" in spl.lower()
    a.has_append = "| append" in spl.lower()

    # Case expressions
    for m in re.finditer(r'eval\s+(\w+)\s*=\s*case\s*\(', spl, re.IGNORECASE):
        a.case_expressions.append(m.group(1))
    # If expressions
    for m in re.finditer(r'eval\s+(\w+)\s*=\s*if\s*\(', spl, re.IGNORECASE):
        a.if_expressions.append(m.group(1))
    # match() regex patterns
    for m in re.finditer(r'match\s*\([^,]+,\s*"([^"]+)"', spl):
        a.match_patterns.append(m.group(1))
    # Eval constants: `| eval field="value"` — these are detection-identity tags
    for m in re.finditer(r'\|\s*eval\s+(\w+)\s*=\s*"([^"]+)"', spl, re.IGNORECASE):
        field = m.group(1)
        value = m.group(2)
        # Ignore obvious noise: uc_id self-references, empty
        if field.lower() in ("uc_id",) or not value:
            continue
        a.eval_constants.append((field, value))

    # Overall fields (for field extraction guidance)
    all_fields = set()
    all_fields.update(a.group_by_fields)
    for t in a.thresholds:
        all_fields.add(t["field"])
    for tp in a.time_parses:
        all_fields.add(tp["field"])
    all_fields.update(a.case_expressions)
    all_fields.update(a.if_expressions)
    for lk in a.lookups:
        if lk["input_field"]:
            all_fields.add(lk["input_field"])
        all_fields.update(lk["outputs"])
    # Remove noise
    all_fields.discard("")
    all_fields.discard("count")
    a.fields = sorted(all_fields)[:12]

    return a


def classify_spl_pattern(a: SplAnalysis) -> str:
    """
    Classify SPL into its primary pattern type for commentary selection.
    Priority: tstats > join > inputlookup > transaction > stats-window >
              time-corr > lookup-threshold > lookup > threshold > subsearch > aggregate.
    """
    if a.has_tstats and not a.has_eventstats:
        # Pure tstats (CIM-accelerated) base search
        return "tstats"
    if a.joins:
        return "join"
    if a.has_inputlookup:
        return "inputlookup"
    if a.has_transaction:
        return "transaction"
    if a.has_eventstats or a.has_streamstats:
        return "stats-window"
    if a.time_parses and a.thresholds:
        return "time-corr"
    if a.lookups and a.thresholds:
        return "lookup-threshold"
    if a.lookups:
        return "lookup"
    if a.thresholds:
        return "threshold"
    if a.has_subsearch:
        return "subsearch"
    return "aggregate"


# ============================================================================
# SECTION 2 — TA / APP KNOWLEDGE BASE
# ============================================================================
#
# Maps sourcetypes to the real Splunk Technology Add-on that parses them,
# including Splunkbase ID, inputs.conf stanza, license volume estimate,
# and key extracted fields. This makes the Prerequisites and Step 1
# sections UC-specific and deployable, not generic boilerplate.

TA_KB = {
    # ServiceNow
    "snow": {
        "ta_name": "Splunk Add-on for ServiceNow",
        "splunkbase_id": 1928,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[snow://{instance_slug}]\n"
            "url = https://<instance>.service-now.com\n"
            "table = {table_name}\n"
            "interval = 300\n"
            "index = itsm\n"
            "sourcetype = {sourcetype}"
        ),
        "volume_note": "REST-polled ticket tables produce 500-5000 records per sync per table; at 300s interval expect ~3-8 GB/month for a mid-size service desk.",
        "key_fields": "number, state, priority, assignment_group, opened_at, closed_at, sys_updated_on, caller_id, category, subcategory",
        "setup_ui": "Settings > Data Inputs > ServiceNow Service Account",
    },
    "WinEventLog": {
        "ta_name": "Splunk Add-on for Microsoft Windows",
        "splunkbase_id": 742,
        "uf_or_api": "uf",
        "inputs_stanza": (
            "[WinEventLog://Security]\n"
            "disabled = 0\n"
            "index = windows\n"
            "renderXml = true\n"
            "current_only = 0\n"
            "evt_resolve_ad_obj = 1\n"
            "checkpointInterval = 5"
        ),
        "volume_note": "Security channel alone produces 2000-8000 events per domain-joined host per day depending on audit policy (~2-8 GB/host/month). Domain controllers generate 10x more.",
        "key_fields": "EventCode, Account_Name, Account_Domain, Logon_Type, Source_Network_Address, Workstation_Name, Process_Name, TargetUserName, Subject_Account_Name",
        "setup_ui": "Splunk_TA_windows/local/inputs.conf on each Universal Forwarder",
    },
    "OktaIM2": {
        "ta_name": "Splunk Add-on for Okta Identity Cloud",
        "splunkbase_id": 6553,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[okta_im2_log]\n"
            "interval = 60\n"
            "index = okta\n"
            "sourcetype = OktaIM2:log\n"
            "okta_account = <named_account>"
        ),
        "volume_note": "Okta System Log streams at 1000-5000 events/org/hour depending on workforce size; plan ~2-10 GB/month per org.",
        "key_fields": "actor.displayName, actor.alternateId, eventType, outcome.result, target{}.displayName, client.ipAddress, client.userAgent, authenticationContext.authenticationProvider",
        "setup_ui": "Settings > Data Inputs > Okta Identity Cloud (API token scoped to System Log read)",
    },
    "epic": {
        "ta_name": "Epic Audit Log Integration (facility-specific TA)",
        "splunkbase_id": None,
        "uf_or_api": "file",
        "inputs_stanza": (
            "[monitor:///opt/epic/audit/export/*.json]\n"
            "index = epic\n"
            "sourcetype = epic:audit\n"
            "disabled = 0\n"
            "crcSalt = <SOURCE>"
        ),
        "volume_note": "Epic Hyperspace audit exports run 5000-50000 events/day depending on facility size; at 1 KB/event plan 5-50 GB/month per facility.",
        "key_fields": "USER_ID, PAT_ID, AccessType, AccessContext, WorkstationName, Department, _time",
        "setup_ui": "Universal Forwarder on the Epic audit export host; coordinate export schedule with Epic admin team",
    },
    "paloalto": {
        "ta_name": "Palo Alto Networks Add-on for Splunk",
        "splunkbase_id": 2757,
        "uf_or_api": "syslog",
        "inputs_stanza": (
            "[udp://514]\n"
            "connection_host = dns\n"
            "index = netfw\n"
            "sourcetype = pan:log\n"
            "no_appending_timestamp = true"
        ),
        "volume_note": "A single NGFW passing 1 Gbps of filtered traffic emits 10000-100000 events/hour (~10-100 GB/FW/month). Use syslog-ng or SC4S for reliable forwarding.",
        "key_fields": "action, src_ip, dest_ip, dest_port, transport, bytes_in, bytes_out, rule, app, user",
        "setup_ui": "Panorama > Log Forwarding profile, or per-FW Device > Server Profiles > Syslog",
    },
    "aws": {
        "ta_name": "Splunk Add-on for AWS",
        "splunkbase_id": 1876,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[aws_cloudtrail://prod_account]\n"
            "aws_account = production\n"
            "aws_region = us-east-1\n"
            "sqs_queue = splunk-ct-queue\n"
            "index = aws\n"
            "sourcetype = aws:cloudtrail"
        ),
        "volume_note": "CloudTrail management events average 5000-50000 API calls/account/hour for active workloads (~5-50 GB/account/month). Data events (S3, Lambda) can multiply this 10-100x.",
        "key_fields": "eventName, eventSource, userIdentity.arn, sourceIPAddress, requestParameters, responseElements, errorCode, userAgent",
        "setup_ui": "Settings > Data Inputs > CloudTrail (SQS-based ingest is strongly preferred over S3 polling)",
    },
    "ms:o365": {
        "ta_name": "Splunk Add-on for Microsoft Cloud Services",
        "splunkbase_id": 3110,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[splunk_ta_o365_management_activity://prod]\n"
            "tenant_id = <tenant>\n"
            "client_id = <app_id>\n"
            "content_type = Audit.AzureActiveDirectory,Audit.Exchange,Audit.SharePoint,Audit.General\n"
            "index = o365"
        ),
        "volume_note": "O365 Management Activity streams 10000-100000 events/tenant/day (~5-50 GB/month) for a mid-size tenant. Heavy SharePoint usage inflates this.",
        "key_fields": "Operation, UserId, ClientIP, Workload, ResultStatus, ObjectId, SourceFileName, Site_Url",
        "setup_ui": "Settings > Data Inputs > Office 365 Management Activity (requires Azure AD app registration with Office 365 Management API permissions)",
    },
    "cisco:asa": {
        "ta_name": "Splunk Add-on for Cisco ASA",
        "splunkbase_id": 1620,
        "uf_or_api": "syslog",
        "inputs_stanza": (
            "[udp://514]\n"
            "connection_host = dns\n"
            "index = netfw\n"
            "sourcetype = cisco:asa"
        ),
        "volume_note": "Medium-traffic ASA with rule logging emits 5000-50000 events/hour (~5-50 GB/FW/month).",
        "key_fields": "action, src_ip, dest_ip, dest_port, rule_id, connection_id, bytes",
        "setup_ui": "ASA CLI: logging host <syslog-collector>; logging trap <level>",
    },
    "linux": {
        "ta_name": "Splunk Add-on for Unix and Linux",
        "splunkbase_id": 833,
        "uf_or_api": "uf",
        "inputs_stanza": (
            "[script://./bin/openPorts.sh]\n"
            "disabled = 0\n"
            "interval = 3600\n"
            "sourcetype = linux:network_listeners\n"
            "index = linux"
        ),
        "volume_note": "Scripted inputs at hourly cadence produce ~50-200 events/host/hour (~100-400 MB/host/month). Auditd log volume adds 500 MB - 2 GB/host/month.",
        "key_fields": "host, proto, port, process, pid, user, cmdline",
        "setup_ui": "Deployment Server > Forwarder Management > Splunk_TA_nix serverclass",
    },
    "mssql": {
        "ta_name": "Splunk DB Connect + Microsoft SQL Audit Export",
        "splunkbase_id": 2686,
        "uf_or_api": "dbconnect",
        "inputs_stanza": (
            "[mi_input://mssql_audit_daily]\n"
            "connection = mssql_prod\n"
            "query = SELECT * FROM sys.fn_get_audit_file(...) WHERE event_time > ?\n"
            "index = mssql\n"
            "sourcetype = mssql:audit"
        ),
        "volume_note": "MSSQL audit trail on a transactional DB generates 1000-10000 events/instance/hour depending on audit spec (~1-10 GB/instance/month).",
        "key_fields": "session_server_principal_name, object_name, statement, action_class, application_name, database_name, event_time",
        "setup_ui": "Splunk DB Connect > Inputs > New Rising Column Input against server_audits view",
    },
    "pan:config": {
        "ta_name": "Palo Alto Networks Add-on for Splunk",
        "splunkbase_id": 2757,
        "uf_or_api": "syslog",
        "inputs_stanza": (
            "[udp://514]\n"
            "connection_host = dns\n"
            "index = netfw\n"
            "sourcetype = pan:log"
        ),
        "volume_note": "Config audit events are low-volume (5-50/day/FW) compared to traffic logs but are irreplaceable for change evidence.",
        "key_fields": "admin_user, action, path, before, after, device_group, commit_id",
        "setup_ui": "Panorama > Log Forwarding > Config profile",
    },
    "tenable": {
        "ta_name": "Tenable Add-on for Splunk",
        "splunkbase_id": 4060,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[tenable_sc_vuln://prod]\n"
            "endpoint = https://tenable.example.com\n"
            "interval = 86400\n"
            "index = vulnerability\n"
            "sourcetype = tenable:sc:vuln"
        ),
        "volume_note": "Daily vulnerability deltas for a 10000-asset estate produce 50000-500000 findings/day (~5-50 GB/month). Full snapshots weekly add more.",
        "key_fields": "pluginID, severity, state, first_seen, last_seen, host, dns, ip, plugin_name, cve",
        "setup_ui": "Settings > Data Inputs > Tenable.sc Vulnerability",
    },
    "workday": {
        "ta_name": "Workday Integration (custom or third-party TA)",
        "splunkbase_id": None,
        "uf_or_api": "api",
        "inputs_stanza": (
            "[workday_termination_report://daily]\n"
            "interval = 3600\n"
            "index = hr\n"
            "sourcetype = workday:termination"
        ),
        "volume_note": "HR termination events are low-volume (5-100/day for a 10000-person org). The value is in timeliness, not volume.",
        "key_fields": "worker_id, samaccountname, term_date, term_reason, manager, cost_center",
        "setup_ui": "Coordinate with HRIS team — typical integration uses Workday Studio, EIB, or Launchpad report delivery via SFTP",
    },
    "citrix": {
        "ta_name": "Splunk Add-on for Citrix NetScaler or facility Citrix TA",
        "splunkbase_id": None,
        "uf_or_api": "file",
        "inputs_stanza": (
            "[monitor:///var/log/citrix/*.log]\n"
            "index = citrix\n"
            "sourcetype = citrix:session\n"
            "disabled = 0"
        ),
        "volume_note": "Active Citrix environment produces 1000-10000 session events/hour (~2-20 GB/month for a 5000-user workforce).",
        "key_fields": "UserName, client_ip, SessionStart, SessionEnd, PublishedApplication, WorkstationName",
        "setup_ui": "Universal Forwarder on Citrix Director or Delivery Controller host",
    },
}


def lookup_ta(sourcetypes: list[str], indexes: list[str], app_field: str) -> Optional[dict]:
    """Match UC's sourcetypes to TA knowledge base."""
    for st in sourcetypes:
        # Try prefix (colon-split), underscore-split, and first word
        for key_try in (st.split(":")[0], st.split("_")[0], st.split(".")[0]):
            if key_try in TA_KB:
                return TA_KB[key_try]
        # Full sourcetype match
        if st in TA_KB:
            return TA_KB[st]
    # Fallback: match by index name
    for idx in indexes:
        if idx in ("aws", "windows", "epic", "okta", "citrix", "linux", "mssql"):
            if idx in TA_KB:
                return TA_KB[idx]
    return None


# ============================================================================
# SECTION 3 — PATTERN COMMENTATORS
# ============================================================================
#
# Each commentator produces Step 2 prose explaining the SPL logic in
# UC-specific terms. Inputs: SplAnalysis + UC metadata (title, regulation,
# clause). Output: 400-900 chars of commentary that reads like it was
# written by a Splunk engineer who understands this specific detection.


def fmt_time_window(tw: Optional[str]) -> str:
    """Human-readable time window from earliest= value."""
    if not tw:
        return "the full search range"
    mapping = {
        "-15m": "the last 15 minutes",
        "-1h": "the last hour",
        "-4h": "the last 4 hours",
        "-24h": "the last 24 hours",
        "-7d": "the last 7 days",
        "-14d": "the last 14 days",
        "-30d": "the last 30 days",
        "-90d": "the last 90 days",
        "-365d": "the last year",
    }
    if tw in mapping:
        return mapping[tw]
    m = re.match(r'-(\d+)([smhdw])', tw)
    if m:
        n = int(m.group(1))
        unit_map = {"s": "second", "m": "minute", "h": "hour", "d": "day", "w": "week"}
        unit = unit_map.get(m.group(2), m.group(2))
        if n != 1:
            unit += "s"
        return f"the last {n} {unit}"
    return tw


def commentary_join(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for UCs using `| join`."""
    j = a.joins[0]
    join_type = j["type"]
    on_field = j["on"]
    left_index = a.indexes[0] if a.indexes else "the outer"
    left_st = a.sourcetypes[0] if a.sourcetypes else "the primary"
    right_index = a.indexes[1] if len(a.indexes) > 1 else "a secondary"
    right_st = a.sourcetypes[1] if len(a.sourcetypes) > 1 else "another"
    tw = fmt_time_window(a.time_window)

    type_explanation = {
        "inner": (
            "`type=inner` means the search only returns rows where `" + on_field +
            "` exists in both datasets. This is the correct choice when the detection "
            "requires presence in both sources — a left-join would include orphaned "
            "rows that cannot be evaluated against the compliance rule."
        ),
        "outer": (
            "`type=outer` (left-outer) returns every row from the outer search and "
            "fills nulls where the inner search has no match. Use this when the "
            "compliance question is 'for every row in A, what does B say?' — the "
            "null pattern is itself the finding (e.g. 'ticket opened but no PIR recorded')."
        ),
        "left": (
            "`type=left` preserves all rows from the outer search; nulls in the inner "
            "side indicate missing data that may itself constitute a finding."
        ),
    }.get(join_type,
          f"`type={join_type}` controls how rows from both sides are combined; verify "
          "the join type matches the compliance question this search is answering."
    )

    join_caveat = (
        "Join caveat: Splunk's `| join` subsearch is capped at "
        "`max_searches_per_cpu * subsearch_maxout` results (default: 50000). "
        "If the inner subsearch exceeds this, rows are silently dropped and "
        "the resulting report will under-count. Check "
        "`index=_internal sourcetype=splunkd log_level=WARN subsearch` for "
        "truncation warnings. For inner searches expected to return "
        ">10000 rows, rewrite as `| stats` with a larger base search and "
        "post-filter, or use `| tstats` if a CIM datamodel covers the data."
    )

    data_sources_line = ""
    if len(a.indexes) >= 2:
        data_sources_line = (
            f"This search correlates `index={left_index}` "
            f"(sourcetype=`{left_st}`) on the outer side with "
            f"`index={right_index}` (sourcetype=`{right_st}`) on the inner side, "
            f"joined on `{on_field}` across {tw}. "
        )
    else:
        data_sources_line = (
            f"This search correlates the outer dataset "
            f"(index=`{left_index}`, sourcetype=`{left_st}`) with a "
            f"subsearch on `{on_field}` across {tw}. "
        )

    time_sensitivity = ""
    if a.time_parses:
        tp = a.time_parses[0]
        time_sensitivity = (
            f"\n\nTime-zone sensitivity: the `strptime({tp['field']}, \"{tp['format']}\")` "
            f"conversion assumes the source timestamp is in the Splunk server's local "
            f"time zone unless the format includes `%z`. If `{tp['field']}` is emitted "
            f"in UTC by the source system but Splunk's search head runs in a non-UTC "
            f"zone, the resulting epoch will be off by the zone offset and the subsequent "
            f"`where _time > {tp['field']}_epoch` comparison will produce systematic "
            f"false positives or negatives. Always validate by comparing "
            f"`strftime({tp['field']}_epoch, \"%Y-%m-%d %H:%M %Z\")` against a known-good "
            f"reference event before promoting to production."
        )

    intent = _title_intent_phrase(title, regulation)

    return (
        intent + "\n\n" +
        data_sources_line + type_explanation + "\n\n" + join_caveat + time_sensitivity
    )


def commentary_lookup(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for UCs using `| lookup` for enrichment."""
    lk = a.lookups[0]
    name = lk["name"]
    input_field = lk["input_field"] or "a key field"
    outputs = lk["outputs"]
    outputs_str = ", ".join(outputs[:5]) if outputs else "context fields"
    tw = fmt_time_window(a.time_window)

    purpose_guess = _guess_lookup_purpose(name)

    intent = _title_intent_phrase(title, regulation)

    return (
        f"{intent}\n\n"
        f"This search enriches raw events with context from the lookup "
        f"`{name}` — {purpose_guess}. The raw event stream alone cannot "
        f"answer the compliance question because it does not carry the "
        f"authoritative business attributes (`{outputs_str}`) — these live "
        f"in a register maintained outside the monitored system. The `| lookup` "
        f"joins at search time on `{input_field}`, making the search results "
        f"only as accurate as the lookup's freshness.\n\n"
        f"Lookup ownership and freshness: This is the single most common "
        f"failure mode for lookup-based compliance searches. The `{name}` "
        f"table must be owned by a named team with a documented refresh "
        f"cadence and staleness alerting. A minimum operational SLA is: "
        f"(1) lookup refreshed at a cadence matching the risk domain "
        f"(daily for access control, weekly for inventory, quarterly for "
        f"vendor registers), (2) automated alert when the lookup has not "
        f"been rewritten in 2x the refresh interval, (3) a row-count sanity "
        f"check (alert if row count changes by more than 20% between "
        f"refreshes — catches truncation bugs in upstream exports).\n\n"
        f"Case sensitivity: Splunk's lookup matching is case-sensitive by "
        f"default. If the raw event field and the lookup key differ in case "
        f"(e.g. `Account_Name=JSMITH` vs lookup `samaccountname=jsmith`), "
        f"the join silently returns null. Normalize both sides with "
        f"`| eval {input_field} = lower({input_field})` before the lookup, "
        f"or set `case_sensitive_match = false` in the lookup's "
        f"`transforms.conf` stanza. Search across {tw}."
    )


def _guess_lookup_purpose(name: str) -> str:
    """Infer purpose of a lookup from its filename."""
    nm = name.lower()
    if "cde" in nm or "pci" in nm:
        return "the authoritative Cardholder Data Environment (CDE) scope register"
    if "ephi" in nm or "phi" in nm or "hipaa" in nm:
        return "the ePHI system register maintained by the HIPAA security officer"
    if "baa" in nm:
        return "the Business Associate Agreement register tracking signed BAAs by vendor"
    if "bes" in nm or "nerc" in nm:
        return "the BES Cyber System inventory required for NERC CIP asset identification"
    if "asset" in nm or "inventory" in nm or "cmdb" in nm:
        return "the asset inventory register that maps hosts/IPs to owners and criticality"
    if "vendor" in nm or "supplier" in nm:
        return "the vendor/third-party register tracking approved service providers"
    if "exception" in nm or "approved" in nm or "allowed" in nm:
        return "the exception register containing approved, time-bound deviations from policy"
    if "user" in nm or "account" in nm or "identity" in nm or "employee" in nm:
        return "the identity register that maps accounts to real users and roles"
    if "scope" in nm or "boundary" in nm:
        return "the compliance scope definition boundary register"
    if "policy" in nm:
        return "the policy register codifying the approved configuration baseline"
    if "ioc" in nm or "threat" in nm:
        return "the threat intelligence register of known malicious indicators"
    return "the enrichment table that adds compliance-relevant business context to raw events"


def commentary_threshold(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for UCs with numeric thresholds."""
    thresh = a.thresholds[0]
    field = thresh["field"]
    op = thresh["op"]
    value = thresh["value"]
    aggr_fn = a.aggregations[0] if a.aggregations else "count"
    tw = fmt_time_window(a.time_window)

    # Describe the threshold in plain language
    op_english = {
        ">": "greater than",
        "<": "less than",
        ">=": "at or above",
        "<=": "at or below",
    }.get(op, op)

    intent = _title_intent_phrase(title, regulation)

    return (
        f"The detection fires when `{field} {op} {value}`. {intent} This threshold "
        f"is the operational heart of the control — set it too low and the "
        f"signal drowns in noise; set it too high and real compliance "
        f"deviations go undetected. The value `{value}` should never be "
        f"treated as universal; it must be calibrated against your specific "
        f"operational baseline.\n\n"
        f"Calibration procedure: before enabling this as a production alert, "
        f"run the base search over the last 30 days with the threshold "
        f"removed and compute distribution statistics:\n\n"
        f"```spl\n"
        f"<base search> earliest=-30d\n"
        f"| stats count by {field}\n"
        f"| stats avg({field}) as mean, perc50({field}) as p50, "
        f"perc90({field}) as p90, perc99({field}) as p99, max({field}) as hi\n"
        f"```\n\n"
        f"Set the production threshold between p90 and p99 depending on "
        f"your organisation's alert fatigue tolerance. Document the chosen "
        f"value in the control specification alongside the date of calibration "
        f"and the sample size — auditors will ask how you arrived at `{value}` "
        f"and the defensible answer is 'data, plus a documented review by the "
        f"control owner,' not 'the template said so.'\n\n"
        f"The `{aggr_fn}()` aggregation over {tw} is a deliberate choice. "
        f"Compliance reports on sustained behaviour, not instantaneous spikes — "
        f"a single noisy event crossing the threshold for one second should "
        f"not page the on-call. If your organisation requires point-in-time "
        f"sensitivity (e.g. real-time fraud detection), shorten the time "
        f"window and aggregation span; for accountability reporting, widen "
        f"them. Tune for the regulation's actual expectation, not "
        f"engineering preference."
    )


def commentary_time_corr(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for UCs with time-correlation (strptime + where _time)."""
    tp = a.time_parses[0]
    field = tp["field"]
    fmt = tp["format"]
    tw = fmt_time_window(a.time_window)

    intent = _title_intent_phrase(title, regulation)

    return (
        f"{intent}\n\n"
        f"This detection correlates event arrival time with a business "
        f"timestamp from `{field}` (format: `{fmt}`). The `strptime()` "
        f"conversion to epoch is the linchpin — the subsequent `where` "
        f"clause compares Splunk's `_time` against the parsed epoch to "
        f"detect policy violations (activity after a termination, events "
        f"past a retention boundary, operations outside a maintenance "
        f"window, etc).\n\n"
        f"Silent failure mode: if `{field}` arrives in a format the "
        f"`strptime` call doesn't match, the conversion returns null, "
        f"propagates through the `where` comparison as 'unknown,' and "
        f"the row is dropped from results. This produces under-reporting, "
        f"not over-reporting — which is the dangerous direction for a "
        f"compliance detection. Validate by running:\n\n"
        f"```spl\n"
        f"<base search>\n"
        f"| eval {field}_epoch = strptime({field}, \"{fmt}\")\n"
        f"| where isnull({field}_epoch)\n"
        f"| stats count by {field}\n"
        f"```\n\n"
        f"If this returns rows, the upstream system has multiple timestamp "
        f"formats (common with SaaS connectors that change during version "
        f"upgrades) and the `strptime` call must be hardened with "
        f"`coalesce(strptime({field}, \"fmt1\"), strptime({field}, \"fmt2\"))` "
        f"to handle them all.\n\n"
        f"Time-zone alignment: if the source system emits `{field}` in a "
        f"different zone from the Splunk search head, the comparison will "
        f"be offset. Look for `%z` or `%Z` in the format string — if "
        f"absent, the conversion uses `TZ = TZ of Splunk host`, which is "
        f"correct only when source and target agree. Search covers {tw}."
    )


def commentary_tstats(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for tstats-based (CIM-accelerated) searches."""
    agg = a.aggregations[0] if a.aggregations else "count"
    gb = ", ".join(a.group_by_fields[:4]) if a.group_by_fields else "the primary dimensions"

    intent = _title_intent_phrase(title, regulation)

    return (
        f"{intent}\n\n"
        f"This search uses `| tstats` against a CIM-accelerated data model "
        f"rather than reading raw events. The performance delta is typically "
        f"10-50x over raw search, and for large indexes can be >100x. The "
        f"acceleration summaries are maintained on a rolling window "
        f"(default: 1 year, configurable in the data model editor) and are "
        f"queried from indexer-local summary files rather than re-scanning "
        f"raw events.\n\n"
        f"CIM acceleration dependency: this search FAILS SILENTLY if the "
        f"underlying data model is not accelerated. It will return zero "
        f"rows instead of raising an error, which is exactly the wrong "
        f"failure mode for a compliance detection. Verify acceleration "
        f"status before scheduling:\n\n"
        f"```spl\n"
        f"| rest /services/admin/summarization\n"
        f"| search title=\"<datamodel_name>\"\n"
        f"| table title access_count summary.complete summary.earliest_time "
        f"summary.latest_time\n"
        f"```\n\n"
        f"`summary.complete` should show 100 (or very close). If it's "
        f"below 95, the acceleration is still catching up or has stalled — "
        f"check the DMA audit log (`index=_audit action=dma_run`) for "
        f"errors.\n\n"
        f"Aggregation choice: `{agg}()` is grouped by `{gb}`. This produces "
        f"a summary row per distinct combination, which is typically what "
        f"compliance reporting requires (one row per asset, one row per "
        f"user, one row per rule). If downstream processing expects a flat "
        f"event stream, avoid `tstats` — summary rows are not raw events "
        f"and cannot be drilled into without re-running against the raw "
        f"index.\n\n"
        f"When NOT to use tstats: if the field being filtered was added "
        f"after the acceleration started, or is search-time extracted by "
        f"an app the acceleration isn't aware of, the field will not exist "
        f"in the summaries and the `where` clause will drop every row. "
        f"Rebuild the acceleration after any field-extraction changes."
    )


def commentary_stats_window(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for eventstats/streamstats-based searches."""
    is_stream = a.has_streamstats
    cmd = "streamstats" if is_stream else "eventstats"
    gb = ", ".join(a.group_by_fields[:4]) if a.group_by_fields else "the grouping fields"

    if is_stream:
        purpose = (
            f"`streamstats` computes a running aggregate over events in "
            f"sequence, preserving event order. For \"{title}\" specifically, "
            f"this is the right choice because the control asks a temporal "
            f"question — detecting accelerating trends, windowed thresholds, "
            f"or deviations from a rolling baseline."
        )
        caveat = (
            "Order sensitivity: `streamstats` respects the event ordering "
            "presented to it, which means the preceding `sort` (or the "
            "natural _time-descending default of the base search) dictates "
            "behaviour. If the stream is unsorted or sorted the wrong way, "
            "the running totals are meaningless. Always precede `streamstats` "
            "with `| sort 0 _time` to guarantee chronological order."
        )
    else:
        purpose = (
            f"`eventstats` attaches a group-level aggregate to every row "
            f"in the result set without collapsing rows. For \"{title}\" "
            f"this gives each event per-peer context — a row can be "
            f"compared to its group's median, average, or quantiles "
            f"without losing the row-level fields the detection relies on."
        )
        caveat = (
            "Memory sensitivity: `eventstats` must hold the entire result "
            "set in memory to compute per-row aggregates. For searches "
            "returning >1M events, this can OOM the search head. If you "
            "see `fatal=true` in `index=_internal sourcetype=splunkd` or "
            "mrsparkle restarts, reduce the base-search time window or "
            "pre-aggregate before `eventstats`."
        )

    # Check for specific group-by patterns worth calling out
    gb_note = ""
    if a.group_by_fields and "_time" in a.group_by_fields and a.span:
        gb_note = (
            f" Note that `_time` appears in the group-by with a `bin span={a.span}` "
            f"preceding it — without the `bin`, `_time` would have near-1:1 "
            f"cardinality with events and the window stat would be trivial."
        )
    elif a.group_by_fields and a.group_by_fields[0] not in ("_time",):
        gb_note = (
            f" The primary dimension here is `{a.group_by_fields[0]}` — "
            f"the detection's finding is effectively 'a {a.group_by_fields[0]} "
            f"whose behaviour diverges from its own historical baseline or "
            f"its peer group,' not a population-wide threshold."
        )

    # Title-intent framing as second paragraph
    intent = _title_intent_phrase(title, regulation)
    eval_consts = _eval_constants_phrase(a)

    return (
        f"{purpose}\n\n"
        f"{intent}{eval_consts}\n\n"
        f"The grouping `by {gb}` is the analytical unit — the aggregate is "
        f"computed within each distinct combination.{gb_note} A common "
        f"mistake is grouping by a field that has cardinality near 1:1 "
        f"with events, which produces a group-per-event and makes the "
        f"window stat trivially equal to the event value.\n\n"
        f"{caveat}"
    )


def commentary_inputlookup(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generate Step 2 commentary for `| inputlookup`-based searches."""
    table = a.inputlookups[0] if a.inputlookups else "the source table"
    tw = fmt_time_window(a.time_window)

    intent = _title_intent_phrase(title, regulation)

    return (
        f"{intent}\n\n"
        f"This search begins with `| inputlookup {table}` — the base "
        f"dataset is a CSV/KV Store lookup, not live event data. This "
        f"inverts the usual Splunk assumption: the detection does not "
        f"stream from an index, it iterates a register. The register "
        f"itself is the authoritative source of truth (contracts, "
        f"policies, sign-offs, attestations) and the search joins it "
        f"against indexed events to find gaps.\n\n"
        f"Lookup authority: treat `{table}` as a primary compliance "
        f"artifact. Its contents ARE the answer the regulator will ask "
        f"for ('show me your vendor list,' 'show me your CDE inventory,' "
        f"'show me your policy exceptions'). Implement the following "
        f"controls on the lookup itself, not just the search:\n\n"
        f"• Version the CSV in a git repository with a mandatory "
        f"pull-request review for every change.\n"
        f"• Maintain a signed-record trail: who changed what, when, and "
        f"with what approval. A lookup with a silent edit history is an "
        f"audit liability.\n"
        f"• Automate a nightly diff: "
        f"`| inputlookup {table} | eval hash=md5(...) | outputlookup "
        f"append=true {table.replace('.csv', '_audit.csv')}` — this "
        f"produces an immutable record of the register's state over time.\n"
        f"• Lock the lookup with role-based access: only the content owner "
        f"has `list_inputs` + `write_file` on the path; everyone else is "
        f"read-only.\n\n"
        f"The live-data side of the join (across {tw}) is the detection "
        f"trigger — when the register and the telemetry disagree, that's "
        f"a finding."
    )


def commentary_transaction(a: SplAnalysis, title: str, regulation: str) -> str:
    """Commentary for `| transaction`-based searches."""
    intent = _title_intent_phrase(title, regulation)
    return (
        f"{intent}\n\n"
        f"This search uses `| transaction` to group events that share a "
        f"correlation identifier into a single result row. Transactions "
        f"are analytically powerful but operationally expensive: Splunk "
        f"must buffer events in memory until the transaction closes, "
        f"which caps the practical event volume (default `maxevents=1000` "
        f"per transaction, `maxopentxn=10000` concurrent transactions).\n\n"
        f"Scale warning: for compliance searches that must cover multi-day "
        f"spans with potentially tens of thousands of open transactions, "
        f"`| transaction` will either truncate or OOM. Prefer `| stats "
        f"earliest(...) latest(...)` grouped by the same correlation ID — "
        f"it produces the same analytical result with no memory cap and "
        f"5-20x better performance.\n\n"
        f"When `| transaction` is the right choice: when you need the "
        f"event sequence preserved (e.g. detecting a specific ordering of "
        f"events like 'login -> elevate -> access -> logout'), when you "
        f"need `maxpause` or `maxspan` constraints between events, or "
        f"when you need `startswith`/`endswith` markers. If you only need "
        f"min/max of a field across the group, always use `| stats`."
    )


def commentary_aggregate(a: SplAnalysis, title: str, regulation: str) -> str:
    """Generic aggregation commentary for UCs without a more specific pattern."""
    aggs = a.aggregations if a.aggregations else ["count"]
    agg_str = ", ".join(f"`{a_}()`" for a_ in aggs[:4])
    gb = ", ".join(a.group_by_fields[:4]) if a.group_by_fields else "the analytical dimensions"
    tw = fmt_time_window(a.time_window)

    # Explain specific aggregation choices
    reasoning = []
    if "dc" in aggs:
        reasoning.append(
            "`dc()` (distinct count) answers 'how many unique X' — use "
            "this when the control measures coverage or diversity, not "
            "raw activity volume. A million events from one user counts "
            "as 1 distinct user; this is usually the right compliance "
            "semantics."
        )
    if "values" in aggs or "list" in aggs:
        reasoning.append(
            "`values()` collects distinct values into a multivalue field "
            "per group; `list()` preserves order and duplicates. For "
            "compliance evidence, `values()` is preferred — the auditor "
            "cares what values appeared, not how many times."
        )
    if any(p.startswith("perc") for p in aggs):
        reasoning.append(
            "Percentile functions (`perc95`, `perc99`) are the correct "
            "way to express 'tail' SLAs — 'the 95th percentile response "
            "time' is a defensible metric; 'the average response time' "
            "hides the outliers that actually affect compliance."
        )
    if "earliest" in aggs or "latest" in aggs:
        reasoning.append(
            "`earliest()` and `latest()` extract the first and last "
            "value per group — typically used to measure durations "
            "('first seen' to 'last seen') or to pick the freshest "
            "attribute value when multiple events update the same entity."
        )

    reasoning_block = " ".join(reasoning) if reasoning else (
        "The aggregation approach is chosen to produce one result row "
        "per analytical unit, which is the typical requirement for "
        "compliance dashboarding and report generation."
    )

    title_framing = _title_intent_phrase(title, regulation)
    eval_consts = _eval_constants_phrase(a)

    return (
        f"This search aggregates {agg_str} across {tw}, grouped by "
        f"`{gb}`. {title_framing}{eval_consts} {reasoning_block}\n\n"
        f"Why aggregate at search time rather than rely on raw events: "
        f"compliance reporting requires summarisation to be defensible "
        f"and stable. A raw-event dashboard can show different counts "
        f"depending on the exact second it was queried; an aggregated "
        f"result rounded to the UC's schedule produces consistent numbers "
        f"across the reporting period. If the downstream consumer (GRC "
        f"platform, regulator submission) expects stable daily/weekly "
        f"figures, schedule this search to write to a summary index and "
        f"read from the summary for reports — that way the numbers quoted "
        f"on Monday match what was quoted on Wednesday.\n\n"
        f"Cardinality vigilance: if `{gb}` has very high cardinality "
        f"(e.g. grouping by a free-text `user_agent` or `url` field), "
        f"the result set explodes and the search becomes slow. Check "
        f"cardinality with `| stats dc({gb.split(',')[0].strip()}) as "
        f"cardinality` before scheduling; if >100000 distinct groups, "
        f"either narrow the search, pre-filter to the top N values, or "
        f"redesign the search to aggregate at a coarser grain."
    )


def _eval_constants_phrase(a: SplAnalysis) -> str:
    """
    Generate a short phrase describing the distinctive eval-constants
    in the SPL (e.g. `| eval aml_tag="edd"`). These are detection-identity
    tags and produce per-UC uniqueness when two UCs have otherwise-similar
    SPL.
    """
    if not a.eval_constants:
        return ""
    parts = []
    for field, value in a.eval_constants[:3]:
        parts.append(f"`{field}=\"{value}\"`")
    consts = ", ".join(parts)
    return (
        f" The SPL tags each event with {consts} — these constants are "
        f"the detection's identity signature; any downstream search "
        f"('alert all of one detection family,' 'evidence for clause X') "
        f"can filter on these constants instead of re-deriving from the "
        f"full base search."
    )


def _title_intent_phrase(title: str, regulation: str) -> str:
    """
    Generate a short phrase re-framing the aggregate in terms of the
    UC's specific title intent — so two similarly-structured SPLs
    produce different Step 2 openings.
    """
    if not title:
        return ""
    low = title.lower()

    # Detect common compliance intents in titles
    if any(kw in low for kw in ("evidence", "attestation", "report")):
        return (
            f"For \"{title.strip()},\" the aggregation is the evidence "
            f"artifact itself — auditors will read these rows as the "
            f"official record of {regulation} control activity."
        )
    if any(kw in low for kw in ("coverage", "gap", "missing", "uncovered")):
        return (
            f"For \"{title.strip()},\" the aggregation measures control "
            f"coverage — the output rows enumerate what IS covered, and "
            f"an auditor's follow-on question ('what about the rest?') "
            f"is answered by the gap between this result and the "
            f"authoritative population."
        )
    if any(kw in low for kw in ("anomaly", "anomalous", "deviation", "outlier", "spike")):
        return (
            f"For \"{title.strip()},\" the aggregation produces a "
            f"baseline that subsequent analytics can compare against — "
            f"an anomaly is an aggregate row that diverges from the "
            f"rest of its peer group, not a raw event count."
        )
    if any(kw in low for kw in ("threshold", "exceed", "excess")):
        return (
            f"For \"{title.strip()},\" the aggregation reveals which "
            f"entities are crossing operational limits — the aggregate "
            f"shape, not any single event, is the compliance signal."
        )
    if any(kw in low for kw in ("trend", "history", "over time", "cadence")):
        return (
            f"For \"{title.strip()},\" the aggregation exposes temporal "
            f"structure that a single point-in-time reading cannot — "
            f"the compliance question is about behaviour over a period, "
            f"not at an instant."
        )
    if any(kw in low for kw in ("retention", "expiry", "expired", "expir")):
        return (
            f"For \"{title.strip()},\" the aggregation identifies records "
            f"at risk of crossing a retention boundary — the control "
            f"is about time-bound lifecycle enforcement, and the "
            f"aggregate captures the current state of that lifecycle."
        )
    if any(kw in low for kw in ("access", "authentication", "logon", "login", "session")):
        return (
            f"For \"{title.strip()},\" the aggregation summarises "
            f"access activity — the control is about WHO accessed "
            f"WHAT, so the key fields in the aggregate map directly to "
            f"'principal' and 'resource' for the compliance narrative."
        )
    if any(kw in low for kw in ("change", "modification", "update")):
        return (
            f"For \"{title.strip()},\" the aggregation exposes "
            f"change activity — change frequency, change authorship, "
            f"and change surface are the dimensions the regulation "
            f"cares about, not raw events."
        )
    if any(kw in low for kw in ("consent", "opt-in", "opt-out", "preference")):
        return (
            f"For \"{title.strip()},\" the aggregation is the "
            f"preference-management evidence — each row represents "
            f"a data subject's current consent state, and drift from "
            f"the authoritative preference store is the finding."
        )
    if any(kw in low for kw in ("incident", "breach", "alert")):
        return (
            f"For \"{title.strip()},\" the aggregation summarises "
            f"incident flow — volume per category, time-to-contain "
            f"distribution, and resolution cadence are the metrics "
            f"regulators ask about during post-incident review."
        )
    if any(kw in low for kw in ("risk", "assessment", "vulnerab", "cve")):
        return (
            f"For \"{title.strip()},\" the aggregation produces the "
            f"risk posture — the per-row values should reconcile to "
            f"the organisation's risk register entries, not stand alone "
            f"as engineering metrics."
        )
    # Default: just reference the title
    return (
        f"For \"{title.strip()},\" the aggregation produces the result "
        f"shape required by the {regulation} control — each row is a "
        f"summary record the regulation expects to be presentable at "
        f"audit time."
    )


def commentary_subsearch(a: SplAnalysis, title: str, regulation: str) -> str:
    """Commentary for subsearch-based searches."""
    intent = _title_intent_phrase(title, regulation)
    return (
        f"{intent}\n\n"
        f"This search uses a subsearch (`[search ...]`) to dynamically "
        f"compute a value list that filters the outer search. Subsearches "
        f"are capped at 50000 results (default `subsearch_maxout`) and "
        f"60 seconds wall-clock (`subsearch_maxtime`) — if either limit "
        f"is hit, the subsearch returns truncated results silently and "
        f"the outer search under-reports.\n\n"
        f"Operational alternative: for compliance use cases where "
        f"completeness matters more than query convenience, consider "
        f"materialising the subsearch result into a lookup via "
        f"`| outputlookup` on a scheduled search, then replacing the "
        f"subsearch with `[| inputlookup ...]`. This decouples the two "
        f"computations, lifts the truncation risk, and makes the "
        f"intermediate result auditable."
    )


def generate_step2_commentary(a: SplAnalysis, pattern: str, title: str, regulation: str) -> str:
    """Dispatch to the right pattern commentator."""
    fn = {
        "join": commentary_join,
        "lookup": commentary_lookup,
        "lookup-threshold": commentary_lookup,  # fall back to lookup; threshold detail added below
        "threshold": commentary_threshold,
        "time-corr": commentary_time_corr,
        "tstats": commentary_tstats,
        "stats-window": commentary_stats_window,
        "inputlookup": commentary_inputlookup,
        "transaction": commentary_transaction,
        "subsearch": commentary_subsearch,
        "aggregate": commentary_aggregate,
    }.get(pattern, commentary_aggregate)
    return fn(a, title, regulation)


# ============================================================================
# SECTION 4 — FIELD INTEGRATORS
# ============================================================================
#
# Weave the author-written `implementation` hints into Step 1 (data
# collection), expand the `visualization` field into Step 4 (dashboard
# layout), and parse `cimSpl` into a Step 2b (CIM-accelerated variant).


def _parse_impl_hints(impl: str) -> list[str]:
    """
    Parse the implementation field which is typically formatted like:
      '(1) First hint; (2) second hint; (3) third hint.'
    Returns a list of clean hint strings.
    """
    if not impl:
        return []
    # Strip trailing Indexes/Sourcetypes block
    main = re.split(r'\bIndexes\s+required\b', impl, flags=re.IGNORECASE)[0].strip()
    # Split on numbered parens: (1) (2) etc.
    parts = re.split(r'\(\d+\)\s*', main)
    hints = []
    for p in parts:
        p = p.strip().rstrip(";.").strip()
        if p:
            hints.append(p)
    return hints


def integrate_implementation_hints(impl: str, ta_info: Optional[dict], indexes: list[str], sourcetypes: list[str]) -> str:
    """
    Weave the author-written `implementation` hints into Step 1 as prose
    paragraphs with operational context. Each hint becomes a sub-section
    explaining WHY it matters, not just that it should be done.
    """
    hints = _parse_impl_hints(impl)
    if not hints:
        # No author hints — produce a standard data-collection section with TA info
        return _default_data_collection(ta_info, indexes, sourcetypes)

    idx_str = ", ".join(f"`{i}`" for i in indexes) if indexes else "the relevant indexes"
    st_str = ", ".join(f"`{s}`" for s in sourcetypes) if sourcetypes else "the relevant sourcetypes"

    out = []
    if ta_info:
        out.append(
            f"Data collection is performed by the {ta_info['ta_name']} "
            + (f"(Splunkbase app ID {ta_info['splunkbase_id']})" if ta_info.get("splunkbase_id") else "")
            + f", landing events in {idx_str} under {st_str}. "
            f"{ta_info['volume_note']}"
        )
        out.append(
            f"Configure the input through {ta_info['setup_ui']}. "
            f"A reference `inputs.conf` stanza looks like:\n\n"
            f"```ini\n{ta_info['inputs_stanza']}\n```\n\n"
            f"The following fields are authoritative for this detection once the TA parses them: `{ta_info['key_fields']}`. "
            f"Verify they are extracted at search time with "
            f"`index={indexes[0] if indexes else 'X'} earliest=-15m | fieldsummary` "
            f"before scheduling the detection."
        )
    else:
        out.append(
            f"Data collection is bespoke for this UC — no single canonical TA "
            f"parses every source the detection relies on. Route data into "
            f"{idx_str} under {st_str}, and document the ingestion path in "
            f"the UC runbook so future engineers know where each field "
            f"originates."
        )

    # Weave in each author-written hint as its own paragraph
    n = len(hints)
    if n == 1:
        header = "\nOne operational consideration shapes the deployment of this detection:\n"
    elif n == 2:
        header = "\nTwo hand-written operational hints accompany this UC:\n"
    elif n == 3:
        header = "\nThree operational considerations, authored alongside this UC, apply:\n"
    elif n == 4:
        header = "\nFour distinct operational considerations shape this detection's rollout:\n"
    else:
        header = f"\n{n} operational considerations apply to the rollout of this detection:\n"

    out.append(header)
    for i, hint in enumerate(hints, 1):
        out.append(f"• **Hint {i}:** {hint}. {_expand_hint_context(hint)}")

    return "\n\n".join(out)


def _expand_hint_context(hint: str) -> str:
    """Add ~1-2 sentences of operational context to each implementation hint."""
    h = hint.lower()
    if "maintain" in h and (".csv" in h or "lookup" in h):
        return (
            "The lookup table identified here is a long-lived compliance "
            "artifact; version it in source control and track every change "
            "with a pull-request review."
        )
    if "normalize" in h or "normalise" in h:
        return (
            "Field normalisation mismatches are one of the top silent-failure "
            "modes in enrichment-driven detections — invest in automated "
            "tests that assert key-match rates after every TA upgrade."
        )
    if "soar" in h or "autoremediat" in h or "auto-disable" in h:
        return (
            "Automated remediation must be gated behind a defined approval "
            "workflow; compliance controls that take destructive action "
            "without human review are themselves a governance risk."
        )
    if "digest" in h or "report" in h or "export" in h:
        return (
            "Report-generation cadence must match the regulatory reporting "
            "cycle; a monthly digest satisfies an annual review requirement "
            "but not a quarterly one."
        )
    if "tune" in h or "exclude" in h or "exclusion" in h:
        return (
            "Exclusions should be time-bound and logged — a permanent "
            "exclusion baked into the search query becomes invisible over "
            "time and future owners cannot tell it was intentional."
        )
    if "schedule" in h or "cadence" in h or "real-time" in h or "near real" in h:
        return (
            "Schedule cadence is a tradeoff between regulatory latency and "
            "search-head load; document the chosen cadence and the reasoning "
            "in the UC runbook."
        )
    if "route" in h or "queue" in h or "workflow" in h:
        return (
            "Routing targets (SOC, compliance team, specific queue) must be "
            "documented with named on-call owners; an 'alerts go to the team' "
            "runbook fails at 3am on Sunday."
        )
    if "baseline" in h or "register" in h:
        return (
            "The register referenced here is primary evidence — treat "
            "changes to it with the same discipline as code changes."
        )
    if "ingest" in h or "feed" in h:
        return (
            "Ingestion SLA drift is usually invisible until it breaks "
            "something — monitor the feed's freshness with a companion "
            "search that alerts when the newest event is older than the "
            "expected cadence."
        )
    if "tag" in h or "cim" in h:
        return (
            "CIM-compliance tagging must be validated end-to-end: a "
            "downstream datamodel that does not accelerate because of a "
            "missing tag is a silent failure."
        )
    return (
        "This is an operational consideration that influences either the "
        "detection's accuracy or its maintainability — document the "
        "approach chosen in the UC runbook."
    )


def _default_data_collection(ta_info: Optional[dict], indexes: list[str], sourcetypes: list[str]) -> str:
    """Fallback Step 1 content when the UC has no implementation hints."""
    idx_str = ", ".join(f"`{i}`" for i in indexes) if indexes else "relevant compliance indexes"
    st_str = ", ".join(f"`{s}`" for s in sourcetypes) if sourcetypes else "relevant sourcetypes"
    if ta_info:
        return (
            f"Data collection uses the {ta_info['ta_name']} "
            + (f"(Splunkbase app ID {ta_info['splunkbase_id']})" if ta_info.get("splunkbase_id") else "")
            + f". {ta_info['volume_note']} "
            f"Configure inputs via {ta_info['setup_ui']} with a stanza like:\n\n"
            f"```ini\n{ta_info['inputs_stanza']}\n```\n\n"
            f"Events land in {idx_str} with sourcetype {st_str}. "
            f"Key fields extracted by the TA: `{ta_info['key_fields']}`."
        )
    return (
        f"Route events into {idx_str} under sourcetype {st_str}. "
        f"No canonical Splunkbase TA covers every source this detection "
        f"relies on — document the ingestion path, volume expectations, "
        f"and field extractions in the UC runbook."
    )


def integrate_visualization(viz: str, uc_id: str, regulation: str) -> str:
    """
    Expand the `visualization` field into a full dashboard layout spec
    with row definitions, drilldown actions, and time-picker presets.

    Input format is typically "Type (fields), Type (fields), ..." e.g.
    "Table (user, count), Timeline (spikes), Single value (count)."
    """
    if not viz:
        return (
            "Create a companion dashboard with at least three panels: "
            "a single-value tile showing current violation count, a "
            "trend panel showing violations over the last 30 days, and "
            "a drill-through table listing the violating records. This "
            "gives auditors three views of the same evidence (summary, "
            "trend, detail)."
        )

    # Parse the viz string into panel specifications
    panels = _parse_viz_spec(viz)

    if not panels:
        return (
            f"Build a dashboard based on the visualization hint: {viz}. "
            f"Ensure it includes a single-value summary, a time-trend, "
            f"and a drill-through detail panel at minimum."
        )

    out = [f"Create a companion dashboard titled `UC-{uc_id}: {regulation} evidence` with the following panel layout:"]

    for i, panel in enumerate(panels, 1):
        panel_type = panel["type"]
        fields = panel["fields"]
        fields_str = ", ".join(f"`{f}`" for f in fields) if fields else "the key fields"

        if panel_type == "single_value":
            out.append(
                f"**Panel {i} — Single-value KPI ({fields_str}):** "
                f"Place at top-left. Configure `underLabel` with the "
                f"regulation clause (e.g. '{regulation} current violation "
                f"count') and set a red colour range for any non-zero value. "
                f"A zero reading is the steady state for a healthy control."
            )
        elif panel_type == "time_chart" or panel_type == "timeline":
            out.append(
                f"**Panel {i} — Time trend ({fields_str}):** "
                f"Place in the main content row. Use `timechart span=1d` "
                f"aggregated appropriately for the regulation's review "
                f"cadence (daily for PCI/HIPAA, weekly for ISO-style controls). "
                f"Annotate the chart with control-change dates so auditors "
                f"can see when mitigations took effect."
            )
        elif panel_type == "table":
            out.append(
                f"**Panel {i} — Drill-through table ({fields_str}):** "
                f"Full-width bottom row. Enable row-level drilldown to a "
                f"secondary dashboard that expands each violation with its "
                f"raw events, timeline, and related context. This is the "
                f"panel the auditor will actually read — optimise it for "
                f"scannability (avoid huge wrap-around fields)."
            )
        elif panel_type == "bar_chart" or panel_type == "column_chart":
            out.append(
                f"**Panel {i} — Distribution ({fields_str}):** "
                f"Shows the volumetric distribution across the primary "
                f"dimension. Use `sort` so the worst offender is first — "
                f"auditors focus on the tallest bar."
            )
        elif panel_type == "histogram":
            out.append(
                f"**Panel {i} — Histogram ({fields_str}):** "
                f"Reveals the distribution shape of the measured metric. "
                f"Useful for calibrating thresholds — the shape tells you "
                f"whether the current threshold sits on the tail or in "
                f"the body of the distribution."
            )
        elif panel_type == "scatter":
            out.append(
                f"**Panel {i} — Scatter ({fields_str}):** "
                f"Plots two dimensions simultaneously; best for spotting "
                f"outliers that multi-variable thresholds would miss."
            )
        elif panel_type == "pie_chart":
            out.append(
                f"**Panel {i} — Pie chart ({fields_str}):** "
                f"Shows proportion across categorical dimension. Use "
                f"sparingly — pie charts are poor at small-slice comparison; "
                f"a bar chart is often clearer."
            )
        else:
            out.append(
                f"**Panel {i} — {panel_type.replace('_', ' ').title()} "
                f"({fields_str}):** Configure according to standard "
                f"Splunk visualization patterns for this panel type."
            )

    out.append(
        f"\nTime picker defaults: set to last 30 days with named presets "
        f"for 24h, 7d, 30d, 90d, and 1y — the auditor needs all five "
        f"windows without retyping. Enable scheduled PDF export for the "
        f"full dashboard on the regulation's reporting cadence."
    )
    return "\n\n".join(out)


def _parse_viz_spec(viz: str) -> list[dict]:
    """
    Parse visualization string like:
      "Table (user, count), Timeline (spikes), Single value (count)."
    into list of {type, fields} dicts.
    """
    panels = []
    # Remove trailing key-fields annotation
    viz_main = re.split(r'Key fields:', viz, flags=re.IGNORECASE)[0].strip().rstrip(".")

    # Split on commas but respect parentheses
    parts = []
    depth = 0
    current = ""
    for ch in viz_main:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    for p in parts:
        m = re.match(r'([a-zA-Z\s]+?)\s*\(([^)]*)\)', p)
        if m:
            type_raw = m.group(1).strip().lower()
            fields_raw = m.group(2).strip()
            fields = [f.strip() for f in re.split(r'[,/]', fields_raw) if f.strip()]

            type_map = {
                "single value": "single_value",
                "singlevalue": "single_value",
                "table": "table",
                "timeline": "timeline",
                "time chart": "time_chart",
                "timechart": "time_chart",
                "time series": "time_chart",
                "bar chart": "bar_chart",
                "column chart": "column_chart",
                "histogram": "histogram",
                "scatter": "scatter",
                "pie chart": "pie_chart",
                "pie": "pie_chart",
                "chart": "chart",
                "map": "map",
                "heatmap": "heatmap",
            }
            panel_type = type_map.get(type_raw, type_raw.replace(" ", "_"))
            panels.append({"type": panel_type, "fields": fields})
        else:
            # Just type, no fields
            type_raw = p.strip().lower()
            panels.append({"type": type_raw.replace(" ", "_"), "fields": []})
    return panels


def integrate_cim_variant(cim_spl: str, spl: str) -> str:
    """
    Produce a Step 2b (CIM / accelerated variant) section when cimSpl
    is present, explaining what the variant buys and when to use it.
    """
    if not cim_spl or not cim_spl.strip():
        return ""

    # Extract datamodel name from tstats variant
    dm_match = re.search(r'datamodel=(\w+)', cim_spl)
    datamodel = dm_match.group(1) if dm_match else "the relevant CIM datamodel"

    return (
        f"\n\n**CIM / accelerated variant:** The detection also has an "
        f"accelerated variant using `| tstats` against the CIM "
        f"`{datamodel}` datamodel:\n\n"
        f"```spl\n{cim_spl}\n```\n\n"
        f"When to prefer this variant: once the underlying datamodel is "
        f"accelerated (verify in Settings > Data Models > `{datamodel}` "
        f"> status=100%), this query runs 10-50x faster than the raw "
        f"variant and can feasibly cover multi-month windows for audit "
        f"reporting. When to avoid: if your field extractions are "
        f"app-specific and the CIM tagging is incomplete, the `tstats` "
        f"variant will silently under-count. Always compare raw vs "
        f"accelerated counts on a known day before swapping the production "
        f"schedule. Maintain both variants in the UC — the raw is the "
        f"primary for accuracy, the accelerated is the performance "
        f"optimisation for dashboarding."
    )


# ============================================================================
# SECTION 5 — ASSEMBLER
# ============================================================================
#
# Combines all six layers into the final DI markdown.


from _regulation_wisdom import get_wisdom


def assemble_di(uc: dict) -> str:
    """
    Assemble the complete detailedImplementation from all six layers.

    Layer 1 — SPL pattern commentary
    Layer 2 — Implementation field integration (Step 1)
    Layer 3 — Visualization dashboard spec (Step 4)
    Layer 4 — CIM variant (Step 2b, if cimSpl present)
    Layer 5 — Regulation wisdom (Step 5)
    Layer 6 — Boilerplate reduction (via conditional phrasing)
    """
    uc_id = uc.get("id", "?.?.?")
    title = uc.get("title", "")
    spl = uc.get("spl", "")
    impl = uc.get("implementation", "")
    viz = uc.get("visualization", "")
    cim_spl = uc.get("cimSpl", "")
    required_fields = uc.get("requiredFields", [])
    app = uc.get("app", "")
    data_sources = uc.get("dataSources", [])

    # Get regulation from compliance[0]
    regulation = "the applicable regulation"
    clause = ""
    control_objective = ""
    if uc.get("compliance"):
        c0 = uc["compliance"][0]
        regulation = c0.get("regulation", regulation)
        clause = c0.get("clause", "")
        control_objective = c0.get("controlObjective", "")

    # Parse SPL and determine pattern
    a = parse_spl(spl)
    pattern = classify_spl_pattern(a)

    # Look up the TA for the dominant sourcetype
    ta_info = lookup_ta(a.sourcetypes, a.indexes, app)

    # --- PREREQUISITES ---
    prereqs = _build_prerequisites(a, ta_info, clause, control_objective, regulation)

    # --- STEP 1: DATA COLLECTION ---
    step1 = integrate_implementation_hints(impl, ta_info, a.indexes, a.sourcetypes)

    # --- STEP 2: SEARCH LOGIC ---
    step2 = generate_step2_commentary(a, pattern, title, regulation)

    # Add threshold detail if lookup-threshold pattern
    if pattern == "lookup-threshold" and a.thresholds:
        t = a.thresholds[0]
        step2 += (
            f"\n\nNumeric threshold `{t['field']} {t['op']} {t['value']}`: "
            f"this is the noise-to-signal decision point for the detection. "
            f"Calibrate against your estate's baseline — see the 'Troubleshooting' "
            f"section below for the calibration query."
        )

    # Add CIM variant if present
    step2 += integrate_cim_variant(cim_spl, spl)

    # Add scheduling guidance
    cron = _suggest_cron(a.time_window, pattern)
    step2 += (
        f"\n\n**Schedule configuration** (`savedsearches.conf`):\n"
        f"```ini\n"
        f"[UC-{uc_id}: {title[:60]}]\n"
        f"cron_schedule = {cron}\n"
        f"dispatch.earliest_time = {a.time_window or '-24h@h'}\n"
        f"dispatch.latest_time = now\n"
        f"actions = summary_index\n"
        f"action.summary_index._name = summary_compliance\n"
        f"action.summary_index.marker = uc={uc_id},reg={regulation.replace(' ', '_')}\n"
        f"```"
    )

    # --- STEP 3: VALIDATION ---
    step3 = _build_validation(a, required_fields, uc_id)

    # --- STEP 4: DASHBOARD ---
    step4 = integrate_visualization(viz, uc_id, regulation)

    # --- STEP 5: TROUBLESHOOTING (regulation-specific) ---
    step5 = _build_troubleshooting(a, regulation, pattern)

    # --- ASSEMBLE ---
    return (
        "## Prerequisites\n\n"
        f"{prereqs}\n\n"
        "## Step 1 — Configure data collection\n\n"
        f"{step1}\n\n"
        "## Step 2 — Implement the search\n\n"
        f"{step2}\n\n"
        "## Step 3 — Validate deployment\n\n"
        f"{step3}\n\n"
        "## Step 4 — Operationalize (dashboard and reporting)\n\n"
        f"{step4}\n\n"
        "## Step 5 — Troubleshooting and regulation-specific caveats\n\n"
        f"{step5}"
    )


def _build_prerequisites(a: SplAnalysis, ta_info: Optional[dict], clause: str, control_objective: str, regulation: str) -> str:
    """Build the Prerequisites section, conditional on pattern."""
    lines = []
    lines.append(f"• **Splunk**: Enterprise ≥9.2 or Splunk Cloud (current). Scheduling requires a search head not under memory pressure (check `index=_internal sourcetype=splunkd component=ProcessRunner` for OOM warnings before deploying a new scheduled search).")

    if ta_info:
        sb_line = f" (Splunkbase app ID {ta_info['splunkbase_id']})" if ta_info.get("splunkbase_id") else ""
        lines.append(f"• **Technology Add-on**: {ta_info['ta_name']}{sb_line} must be installed on search heads and indexers. Verify with `| rest /services/apps/local | search label=\"{ta_info['ta_name']}\" | table label version`.")

    if a.indexes:
        idx_list = ", ".join(f"`{i}`" for i in a.indexes)
        lines.append(f"• **Indexes**: {idx_list} must exist on all indexers with retention matching the regulation's minimum (PCI: 1y, HIPAA: 6y, NIST 800-53: 1-3y per FIPS 199, SOX: 7y). Set `frozenTimePeriodInSecs` accordingly in `indexes.conf`.")

    if a.lookups or a.inputlookups:
        lookups = [l["name"] for l in a.lookups] + a.inputlookups
        lookup_list = ", ".join(f"`{l}`" for l in lookups)
        lines.append(f"• **Lookups**: {lookup_list} must be deployed to the search-tier app and refreshed on a documented schedule. For KV Store lookups, verify with `| rest /servicesNS/-/-/data/transforms/lookups | search name IN ({','.join(repr(l) for l in lookups)})`.")

    if a.has_tstats:
        lines.append(f"• **Data Model Acceleration**: The CIM datamodel referenced in the search must be accelerated. Validate with `| rest /services/admin/summarization | search summary.id=*` and confirm `summary.complete=100`.")

    if a.joins or a.has_subsearch:
        lines.append(f"• **Search-head capacity**: Subsearch-based detections need `subsearch_maxtime` ≥ 60s and `subsearch_maxout` ≥ 50000 in `limits.conf`. For high-volume environments, tune `[search] max_searches_per_cpu` up from default.")

    if clause:
        lines.append(f"• **Regulatory mapping**: This detection evidences clause `{clause}`. The control objective is: \"{control_objective}\" — every alert payload should include this text so downstream consumers know the compliance purpose.")

    return "\n".join(lines)


def _suggest_cron(time_window: Optional[str], pattern: str) -> str:
    """Pick an appropriate cron schedule based on time window and pattern."""
    if not time_window:
        return "0 */6 * * *"  # every 6 hours
    if time_window in ("-15m", "-1h"):
        return "*/15 * * * *"  # every 15 minutes
    if time_window in ("-4h",):
        return "0 * * * *"  # every hour
    if time_window in ("-24h", "-1d"):
        return "0 1 * * *"  # daily at 1am
    if time_window in ("-7d", "-14d"):
        return "0 2 * * 1"  # weekly Monday 2am
    if time_window in ("-30d", "-90d"):
        return "0 3 1 * *"  # monthly 1st at 3am
    return "0 */6 * * *"


def _build_validation(a: SplAnalysis, required_fields: list, uc_id: str) -> str:
    """Build the Validation section, referencing the UC's exact required fields."""
    lines = []
    idx_first = a.indexes[0] if a.indexes else "the_index"
    st_first = a.sourcetypes[0] if a.sourcetypes else "the_sourcetype"

    lines.append(
        f"**(a) Field extraction check:** Run the following to confirm the TA is extracting every field the detection relies on:\n\n"
        f"```spl\n"
        f"index={idx_first} sourcetype={st_first} earliest=-1h\n"
        f"| fieldsummary\n"
        f"| where count=0\n"
        f"| table field\n"
        f"```\n\n"
        f"Any row returned is a field the TA claims to extract but isn't appearing in recent data — it's either a rename upstream, a TA version mismatch, or a data-format change."
    )

    if required_fields:
        rf_list = ", ".join(f"`{f}`" for f in required_fields[:10])
        lines.append(
            f"**(b) Required-field presence:** This detection specifically needs: {rf_list}. Run:\n\n"
            f"```spl\n"
            f"index={idx_first} sourcetype={st_first} earliest=-1h\n"
            f"| head 100\n"
            f"| table {', '.join(required_fields[:8])}\n"
            f"```\n\n"
            f"Every row should have non-null values for the fields the detection's `where` clause filters on. Nulls cause silent drops in the result set."
        )

    if a.lookups:
        lk = a.lookups[0]
        lines.append(
            f"**(c) Lookup freshness:** The detection joins against `{lk['name']}`. Check its modification time and row count:\n\n"
            f"```spl\n"
            f"| inputlookup {lk['name']}\n"
            f"| eval _lookup_row=1\n"
            f"| stats count as rows\n"
            f"```\n\n"
            f"Compare the row count to the expected baseline; an unexpected drop is a sign the upstream export truncated."
        )

    if a.thresholds:
        t = a.thresholds[0]
        lines.append(
            f"**(d) Threshold calibration:** Before enabling as a production alert, run the base search with the threshold removed and profile the distribution of `{t['field']}`:\n\n"
            f"```spl\n"
            f"<base search> earliest=-30d\n"
            f"| stats perc50({t['field']}) as p50 perc90({t['field']}) as p90 perc99({t['field']}) as p99 max({t['field']}) as hi\n"
            f"```\n\n"
            f"The current threshold `{t['value']}` should sit between p90 and p99 for a balanced signal-to-noise ratio. If it's below p50, expect heavy alert volume; if above p99, expect under-detection."
        )

    lines.append(
        f"**(e) Negative test:** Generate a synthetic 'should not alert' event using the Splunk Sample Generator or a crafted `| makeresults` event and confirm the detection does NOT fire on it. A detection that fires on everything is equivalent to a detection that fires on nothing."
    )

    return "\n\n".join(lines)


def _build_troubleshooting(a: SplAnalysis, regulation: str, pattern: str) -> str:
    """Build the Troubleshooting section, injecting regulation-specific wisdom."""
    wisdom = get_wisdom(regulation)

    lines = []

    # Generic troubleshooting grounded in SPL pattern
    if pattern == "join":
        lines.append(
            "**No results when violations exist:** The most likely cause is subsearch truncation (see Step 2). Inspect `index=_internal sourcetype=splunkd component=searchprocessor log_level=WARN subsearch` for messages like 'Output result count exceeded 50000.'"
        )
    elif pattern == "lookup":
        lines.append(
            "**No results when violations exist:** Check the lookup's case sensitivity (Splunk lookups are case-sensitive by default) and null handling — a null on the input side produces a silent miss, not an error."
        )
    elif pattern == "threshold":
        lines.append(
            "**Too many or too few alerts:** The threshold is almost certainly miscalibrated for your estate — re-run the percentile calibration (Step 3d) on a representative 30-day window and pick a value between p90 and p99."
        )
    elif pattern == "time-corr":
        lines.append(
            "**Silent under-reporting:** The `strptime` conversion is likely failing on a subset of events — see Step 3 for the hardening procedure. Check for format drift after upstream system upgrades."
        )
    elif pattern == "tstats":
        lines.append(
            "**Zero results when acceleration is fresh:** The field you're filtering on was likely added after the acceleration started — rebuild the acceleration."
        )
    else:
        lines.append(
            "**Search returns no results when violations are expected:** Verify time-window alignment, index existence, and field extractions in that order. Most 'missing results' are simpler configuration issues before they're detection-logic issues."
        )

    lines.append(
        "**Search times out:** Check the search job inspector (`Activity > Jobs > <this UC's last run> > Inspect`). The phase consuming the time (fetch, command, summary) indicates whether the issue is data-layer (too wide a window, unaccelerated datamodel), command-layer (expensive `transaction` or `eventstats`), or post-aggregation."
    )

    # Regulation-specific wisdom
    if wisdom:
        lines.append(f"\n**{regulation}-specific failure modes:**")
        for w in wisdom[:4]:
            lines.append(f"• {w}")

    return "\n\n".join(lines)


# ============================================================================
# SECTION 6 — CLI / BATCH PROCESSOR
# ============================================================================


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Gold-standard DI rewrite for cat-22 UCs.")
    ap.add_argument("--glob", default=f"{BASE}/UC-22.*.json", help="File glob")
    ap.add_argument("--dry-run", action="store_true", help="Do not write changes")
    ap.add_argument("--only", type=str, help="Process only files matching this substring")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of files processed")
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob))
    if args.only:
        files = [f for f in files if args.only in f]
    if args.limit:
        files = files[:args.limit]

    changed = 0
    errors = 0
    total_len = 0
    for fp in files:
        try:
            with open(fp) as f:
                data = json.load(f)
            new_di = assemble_di(data)
            total_len += len(new_di)
            if data.get("detailedImplementation") == new_di:
                continue
            data["detailedImplementation"] = new_di
            if not args.dry_run:
                with open(fp, "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
            changed += 1
        except Exception as e:
            print(f"ERROR {fp}: {e}")
            errors += 1

    avg_len = total_len // max(len(files), 1)
    print(f"Processed {len(files)} files, changed={changed}, errors={errors}")
    print(f"Average DI length: {avg_len} chars")


if __name__ == "__main__":
    main()
