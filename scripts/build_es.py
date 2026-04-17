#!/usr/bin/env python3
"""Generate Enterprise Security content from the catalog.

Reads ``catalog.json`` and emits correlation searches, governance
mappings (MITRE ATT&CK → UC), and CIM eventtype aliases into
``ta/DA-ESS-monitoring-use-cases/default/``.

Output:
- ``savedsearches.conf``     — correlation searches (action.correlationsearch=1)
- ``governance.conf``        — MITRE ATT&CK mappings per correlation search
- ``eventtypes.conf``        — CIM eventtype shortcuts
- ``tags.conf``              — CIM tags for each eventtype
- ``analytic_stories.conf``  — groups of correlation searches per domain
- ``data/ui/nav/default.xml``

Security categories (per roadmap ``v5.1``):
    9  — Identity & access
    10 — Endpoint security
    14 — Operational Technology / ICS
    17 — Zero Trust
    22 — Compliance & regulatory

Only use cases whose SPL starts with `index=` / `| tstats` and returns
at least one aggregating clause (`| stats`, `| timechart`, `| dedup`,
`| where`) are promoted to correlation searches — this filter guarantees
the search produces per-event rows suitable for notable-event creation.

Re-run:

    python3 scripts/build_es.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, Iterable, List, Set, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CATALOG = os.path.join(REPO_ROOT, "catalog.json")
APP_DIR = os.path.join(REPO_ROOT, "ta", "DA-ESS-monitoring-use-cases")
DEFAULT_DIR = os.path.join(APP_DIR, "default")

# Security categories elected as v5.2 scope.  See the v5.1 MITRE coverage
# push — these categories now have ≥ 80% ATT&CK tagging which qualifies
# them for ES promotion.
SECURITY_CATS: Set[int] = {9, 10, 14, 17, 22}

# Criticality → ES notable event severity (1..10) and schedule.
CRIT_TO_ES: Dict[str, Tuple[int, str, str, str, str]] = {
    # (urgency, severity_label, cron, earliest, latest)
    "critical": (5, "high",     "*/15 * * * *", "-30m@m", "now"),
    "high":     (4, "medium",   "0 * * * *",    "-1h@h",  "now"),
    "medium":   (3, "informational", "0 */2 * * *", "-2h@h", "now"),
    "low":      (2, "informational", "0 */6 * * *", "-6h@h", "now"),
}

# MITRE tactic mapping (technique ID → tactic name).  Used for governance
# and the Analytic Stories that group searches by tactic.  Coverage is
# deliberately coarse — for precise mapping consult STIX CTI JSON.
TACTIC_BY_PREFIX: Dict[str, str] = {
    "T1003": "Credential Access",
    "T1021": "Lateral Movement",
    "T1047": "Execution",
    "T1053": "Persistence",
    "T1055": "Defense Evasion",
    "T1059": "Execution",
    "T1068": "Privilege Escalation",
    "T1071": "Command and Control",
    "T1078": "Initial Access",
    "T1082": "Discovery",
    "T1087": "Discovery",
    "T1098": "Persistence",
    "T1105": "Command and Control",
    "T1110": "Credential Access",
    "T1112": "Defense Evasion",
    "T1134": "Privilege Escalation",
    "T1136": "Persistence",
    "T1189": "Initial Access",
    "T1190": "Initial Access",
    "T1195": "Initial Access",
    "T1197": "Defense Evasion",
    "T1203": "Execution",
    "T1210": "Lateral Movement",
    "T1218": "Defense Evasion",
    "T1219": "Command and Control",
    "T1222": "Defense Evasion",
    "T1484": "Privilege Escalation",
    "T1485": "Impact",
    "T1486": "Impact",
    "T1489": "Impact",
    "T1490": "Impact",
    "T1499": "Impact",
    "T1529": "Impact",
    "T1531": "Impact",
    "T1546": "Privilege Escalation",
    "T1547": "Persistence",
    "T1548": "Privilege Escalation",
    "T1550": "Defense Evasion",
    "T1555": "Credential Access",
    "T1556": "Credential Access",
    "T1558": "Credential Access",
    "T1562": "Defense Evasion",
    "T1566": "Initial Access",
    "T1567": "Exfiltration",
    "T1570": "Lateral Movement",
    "T1570": "Lateral Movement",
    "T1589": "Reconnaissance",
    "T1595": "Reconnaissance",
    "T1657": "Impact",
}


# --------------------------------------------------------------------------
# Catalog helpers (mirror build_ta.py).
# --------------------------------------------------------------------------

def load_catalog() -> dict:
    with open(CATALOG, "r", encoding="utf-8") as f:
        return json.load(f)


def iter_security_ucs(catalog: dict) -> Iterable[dict]:
    for cat in catalog.get("DATA", []):
        if cat.get("i") not in SECURITY_CATS:
            continue
        for sub in cat.get("s", []):
            for uc in sub.get("u", []):
                uc = {**uc, "_cat": cat.get("i")}
                yield uc


def _fits_correlation_search(spl: str) -> bool:
    """Heuristic: correlation searches must be filter-first and aggregate."""
    if not spl:
        return False
    low = spl.strip().lower()
    if not (low.startswith("index=") or low.startswith("| tstats") or low.startswith("search index=")):
        return False
    aggregations = ("| stats", "| tstats", "| timechart", "| where", "| dedup", "| streamstats")
    return any(k in low for k in aggregations)


def _stanza_name(uc: dict) -> str:
    uid = uc.get("i", "?")
    name = uc.get("n", "Untitled").replace("[", "(").replace("]", ")")
    return f"ESCS-{uid} - {name}"


def _escape_conf(val: str) -> str:
    s = val.strip()
    if "\n" not in s:
        return s
    return " \\\n".join(line.rstrip() for line in s.splitlines())


CONF_HEADER = (
    "# ---------------------------------------------------------------------\n"
    "# GENERATED by scripts/build_es.py — DO NOT EDIT BY HAND.\n"
    "# Source of truth: catalog.json + use-cases/*.md.\n"
    "# Re-run `python3 scripts/build_es.py` after updating content.\n"
    "# ---------------------------------------------------------------------\n"
)


# --------------------------------------------------------------------------
# Generators.
# --------------------------------------------------------------------------

def render_savedsearches(ucs: List[dict]) -> str:
    out: List[str] = [CONF_HEADER, ""]
    for uc in ucs:
        uid = uc.get("i", "?")
        crit = (uc.get("c") or "medium").lower()
        urgency, severity, cron, earliest, latest = CRIT_TO_ES.get(crit, CRIT_TO_ES["medium"])
        spl = uc.get("q") or ""
        title = _stanza_name(uc)
        out.append(f"[{title}]")
        out.append(f"description = UC-{uid}: {uc.get('n','')}. {uc.get('v','').strip()}")
        out.append(f"search = {_escape_conf(spl)}")
        out.append(f"cron_schedule = {cron}")
        out.append(f"dispatch.earliest_time = {earliest}")
        out.append(f"dispatch.latest_time = {latest}")
        out.append("enableSched = 0")
        out.append("is_scheduled = 0")
        out.append("disabled = 1")
        out.append("action.correlationsearch = 1")
        out.append(f"action.correlationsearch.label = UC-{uid}: {uc.get('n','')}")
        out.append("action.notable = 1")
        out.append(f"action.notable.param.rule_title = UC-{uid}: {uc.get('n','')}")
        out.append(
            f"action.notable.param.rule_description = {uc.get('v','').strip().splitlines()[0] if uc.get('v') else ''}"
        )
        out.append(f"action.notable.param.severity = {severity}")
        out.append("action.notable.param.drilldown_name = $name$")
        out.append("action.notable.param.drilldown_search = $drilldown_search$")
        # Risk-based alerting hook — empty strings keep RBA disabled until
        # customers set their own risk attribution fields.
        out.append("action.risk = 0")
        out.append("action.risk.param._risk_score = 40")
        out.append("action.risk.param._risk_object = host")
        out.append("action.risk.param._risk_object_type = system")
        if uc.get("mitre"):
            out.append(
                f"action.notable.param.mitre_attack_id = {','.join(uc['mitre'])}"
            )
        if uc.get("kfp"):
            out.append(
                f"action.notable.param.rule_ack_comment = Known false positives: {uc['kfp'].strip()}"
            )
        out.append(
            "# Upstream reference: "
            f"https://github.com/fenre/splunk-monitoring-use-cases#use-case-{uid}"
        )
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_governance(ucs: List[dict]) -> str:
    """Write `governance.conf` — maps correlation searches to MITRE IDs."""
    out: List[str] = [CONF_HEADER, ""]
    for uc in ucs:
        mitre = uc.get("mitre") or []
        if not mitre:
            continue
        out.append(f"[{_stanza_name(uc)}]")
        out.append(f"governance = mitre_attack")
        out.append(f"mitre_attack = {','.join(mitre)}")
        # Derive tactics from technique prefixes.
        tactics = sorted({TACTIC_BY_PREFIX[t.split(".", 1)[0]]
                          for t in mitre if t.split(".", 1)[0] in TACTIC_BY_PREFIX})
        if tactics:
            out.append(f"mitre_attack_tactics = {','.join(tactics)}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_analytic_stories(ucs: List[dict]) -> str:
    """Group correlation searches by first MITRE tactic → Analytic Story.

    The stanzas are named ``analytic_story://<tactic>`` which mirrors the
    `analytic_stories.conf` schema that ES ships with.
    """
    by_tactic: Dict[str, List[str]] = {}
    for uc in ucs:
        for t in uc.get("mitre") or []:
            prefix = t.split(".", 1)[0]
            tac = TACTIC_BY_PREFIX.get(prefix)
            if not tac:
                continue
            by_tactic.setdefault(tac, []).append(_stanza_name(uc))
            break
    out: List[str] = [CONF_HEADER, ""]
    for tactic, names in sorted(by_tactic.items()):
        safe = tactic.replace(" ", "_").lower()
        out.append(f"[analytic_story://mu_{safe}]")
        out.append(f"category = Monitoring Use Cases — {tactic}")
        out.append(f"description = Correlation searches that map to the MITRE ATT&CK ``{tactic}`` tactic.")
        out.append(f"narrative = Curated detections derived from the splunk-monitoring-use-cases catalog.")
        out.append(f"last_updated = 2026-04-16")
        out.append(f"version = 1")
        out.append(f"detections = {', '.join(sorted(set(names)))}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


EVENTTYPES_ES: List[Tuple[str, str, str]] = [
    ("ess_auth_fail", "tag=authentication action=failure", "CIM: failed authentication"),
    ("ess_auth_success", "tag=authentication action=success", "CIM: successful authentication"),
    ("ess_privilege_escalation", "tag=change tag=account tag=modified", "CIM: account privilege changes"),
    ("ess_endpoint_process", "tag=process", "CIM: process execution"),
    ("ess_malware", "tag=malware", "CIM: malware events"),
    ("ess_network_connection", "tag=network tag=communicate", "CIM: network connections"),
    ("ess_dns", "tag=network tag=resolution tag=dns", "CIM: DNS resolutions"),
    ("ess_proxy", "tag=web tag=proxy", "CIM: web proxy traffic"),
    ("ess_ids", "tag=ids tag=attack", "CIM: IDS alerts"),
    ("ess_email", "tag=email tag=delivery", "CIM: email delivery events"),
]


def render_eventtypes() -> str:
    out: List[str] = [CONF_HEADER, ""]
    for name, search, desc in EVENTTYPES_ES:
        out.append(f"[{name}]")
        out.append(f"search = {search}")
        out.append(f"#description = {desc}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_tags() -> str:
    out: List[str] = [CONF_HEADER, ""]
    pairs = [
        ("eventtype=ess_auth_fail", [("authentication", "enabled"), ("failure", "enabled")]),
        ("eventtype=ess_auth_success", [("authentication", "enabled"), ("success", "enabled")]),
        ("eventtype=ess_privilege_escalation", [("account", "enabled"), ("change", "enabled"), ("modified", "enabled")]),
        ("eventtype=ess_endpoint_process", [("process", "enabled")]),
        ("eventtype=ess_malware", [("malware", "enabled")]),
        ("eventtype=ess_network_connection", [("network", "enabled"), ("communicate", "enabled")]),
        ("eventtype=ess_dns", [("network", "enabled"), ("resolution", "enabled"), ("dns", "enabled")]),
        ("eventtype=ess_proxy", [("web", "enabled"), ("proxy", "enabled")]),
        ("eventtype=ess_ids", [("ids", "enabled"), ("attack", "enabled")]),
        ("eventtype=ess_email", [("email", "enabled"), ("delivery", "enabled")]),
    ]
    for stanza, tags in pairs:
        out.append(f"[{stanza}]")
        for k, v in tags:
            out.append(f"{k} = {v}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


NAV_XML = """<nav search_view="search" color="#000000">
    <view name="search" default="true" />
    <collection label="Use cases">
        <a href="https://fenre.github.io/splunk-monitoring-use-cases/">Dashboard</a>
        <a href="https://github.com/fenre/splunk-monitoring-use-cases">Source</a>
    </collection>
</nav>
"""


# We deliberately cap the number of correlation searches shipped in the
# default pack — otherwise a small ES deployment would be buried under
# thousands of disabled searches.  Operators who want the full catalog
# can re-run `build_es.py --include-all` or generate a custom pack.
MAX_CRITICAL = 400
MAX_HIGH = 250


def pick_ucs(include_all: bool = False) -> List[dict]:
    catalog = load_catalog()
    crit_ucs: List[dict] = []
    high_ucs: List[dict] = []
    other_ucs: List[dict] = []
    for uc in iter_security_ucs(catalog):
        if not _fits_correlation_search(uc.get("q") or ""):
            continue
        level = (uc.get("c") or "medium").lower()
        if level == "critical":
            crit_ucs.append(uc)
        elif level == "high":
            high_ucs.append(uc)
        else:
            other_ucs.append(uc)
    if include_all:
        return crit_ucs + high_ucs + other_ucs
    return crit_ucs[:MAX_CRITICAL] + high_ucs[:MAX_HIGH]


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-all", action="store_true",
        help="Include every security UC that fits correlation search semantics "
             "(can produce 1,500+ searches — use sparingly)",
    )
    args = parser.parse_args()

    os.makedirs(DEFAULT_DIR, exist_ok=True)
    os.makedirs(os.path.join(DEFAULT_DIR, "data", "ui", "nav"), exist_ok=True)
    ucs = pick_ucs(include_all=args.include_all)
    print(f"[build_es] correlation searches: {len(ucs)}")

    files = {
        "savedsearches.conf": render_savedsearches(ucs),
        "governance.conf": render_governance(ucs),
        "analytic_stories.conf": render_analytic_stories(ucs),
        "eventtypes.conf": render_eventtypes(),
        "tags.conf": render_tags(),
        "data/ui/nav/default.xml": NAV_XML,
    }
    for rel, contents in files.items():
        path = os.path.join(DEFAULT_DIR, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(contents)
        print(f"  wrote {os.path.relpath(path, REPO_ROOT)}  ({len(contents)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
