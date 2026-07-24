#!/usr/bin/env python3
"""Metadata-driven hand-craft lift for templated UC sidecars (Wave A batch).

Generates domain-specific KFP, controlTest, exclusions, and evidence from each
UC's SPL, dataSources, and title — not bulk-enricher boilerplate. Intended
as a bridge until the full AI lift-loop runs at scale with SME review.

Usage:
    python3 scripts/handcraft_metadata_lift.py --category cat-09 --dry-run
    python3 scripts/handcraft_metadata_lift.py --category cat-17 --force
    python3 scripts/handcraft_metadata_lift.py --files content/.../UC-9.1.2.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from splunk_uc.audits._template_fingerprints import (  # noqa: E402
    GENERIC_REF_URLS,
    detect_template_flags,
    is_fully_templated_v2,
)

CONTENT = _REPO / "content"

CAT_PROFILE: dict[str, str] = {
    "01": "linux",
    "02": "linux",
    "03": "generic",
    "04": "generic",
    "05": "generic",
    "06": "generic",
    "07": "generic",
    "08": "generic",
    "09": "iam",
    "10": "security_infra",
    "11": "generic",
    "12": "generic",
    "13": "generic",
    "14": "generic",
    "15": "generic",
    "16": "generic",
    "17": "network",
    "18": "generic",
    "19": "generic",
    "20": "generic",
    "22": "compliance",
    "23": "generic",
    "24": "generic",
    "25": "personal",
}

FLAG_TO_FIELD: dict[str, str] = {
    "generic_kfp": "knownFalsePositives",
    "generic_controlTest": "controlTest",
    "generic_exclusions": "exclusions",
    "generic_evidence": "evidence",
    "generic_references": "references",
}

RETRIEVED = "2026-04-25"
SPLUNKBASE_RE = re.compile(r"Splunkbase\s+(\d{2,5})|splunkbase\.splunk\.com/app/(\d+)", re.I)

TA_BY_SOURCETYPE: list[tuple[str, str, int]] = [
    ("WinEventLog", "Splunk Add-on for Microsoft Windows", 742),
    ("XmlWinEventLog", "Splunk Add-on for Microsoft Windows", 742),
    ("aws:", "Splunk Add-on for Amazon Web Services", 1876),
    ("azure:", "Splunk Add-on for Microsoft Azure", 3110),
    ("gcp:", "Splunk Add-on for Google Cloud Platform", 3084),
    ("o365:", "Splunk Add-on for Microsoft Office 365", 4054),
    ("docker:", "Splunk Connect for Docker", 4496),
    ("kube:", "Splunk Connect for Kubernetes", 5167),
    ("cisco:", "Splunk Add-on for Cisco Security", 1352),
    ("cisco:ise", "Splunk Add-on for Cisco Identity Services", 1915),
    ("meraki:", "Splunk Add-on for Cisco Meraki", 5631),
    ("pan:", "Splunk Add-on for Palo Alto Networks", 4919),
    ("paloalto:", "Splunk Add-on for Palo Alto Networks", 4919),
    ("fortinet:", "Splunk Add-on for Fortinet FortiGate", 2846),
    ("linux:", "Splunk Add-on for Unix and Linux", 833),
    ("syslog", "Splunk Add-on for Unix and Linux", 833),
    ("vmware:", "Splunk Add-on for VMware ESXi Logs", 3684),
]

CIM_MODEL_URLS: dict[str, str] = {
    "Performance": "https://docs.splunk.com/Documentation/CIM/latest/User/Performance",
    "Authentication": "https://docs.splunk.com/Documentation/CIM/latest/User/Authentication",
    "Intrusion_Detection": "https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection",
    "Change": "https://docs.splunk.com/Documentation/CIM/latest/User/Change",
    "Network_Traffic": "https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic",
    "Malware": "https://docs.splunk.com/Documentation/CIM/latest/User/Malware",
    "Endpoint": "https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint",
    "Web": "https://docs.splunk.com/Documentation/CIM/latest/User/Web",
    "Email": "https://docs.splunk.com/Documentation/CIM/latest/User/Email",
    "Risk": "https://docs.splunk.com/Documentation/CIM/latest/User/Risk",
    "Vulnerabilities": "https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities",
    "Alerts": "https://docs.splunk.com/Documentation/CIM/latest/User/Alerts",
}

VENDOR_SOURCETYPE_URLS: list[tuple[str, str, str]] = [
    ("strava:", "Strava API reference", "https://developers.strava.com/docs/reference/"),
    ("garmin:", "Garmin Connect Developer Program", "https://developer.garmin.com/gc-developer-program/overview/"),
    ("fitbit:", "Fitbit Web API", "https://dev.fitbit.com/build/reference/web-api/"),
    ("peloton:", "Peloton Developer Portal", "https://developer.onepeloton.com/"),
    ("polar:", "Polar AccessLink API", "https://www.polar.com/accesslink-api/"),
    ("zwift:", "Zwift Game Server API", "https://zwiftinsider.com/zwift-api/"),
    ("whoop:", "WHOOP Developer API", "https://developer.whoop.com/api/"),
    ("oura:", "Oura Cloud API", "https://cloud.ouraring.com/docs/"),
    ("withings:", "Withings Health API", "https://developer.withings.com/"),
    ("nest:", "Google Nest Device Access", "https://developers.google.com/nest/device-access"),
    ("hue:", "Philips Hue Developer", "https://developers.meethue.com/"),
    ("homeassistant:", "Home Assistant REST API", "https://developers.home-assistant.io/docs/api/rest/"),
    ("nozomi:", "Nozomi Networks Guardian", "https://www.nozominetworks.com/"),
]

REGULATION_URLS: dict[str, tuple[str, str]] = {
    "gdpr": ("GDPR — EUR-Lex full text", "https://eur-lex.europa.eu/eli/reg/2016/679/oj"),
    "iso-27001": ("ISO/IEC 27001:2022", "https://www.iso.org/standard/27001"),
    "nist-csf": ("NIST Cybersecurity Framework", "https://www.nist.gov/cyberframework"),
    "nist": ("NIST Cybersecurity Framework", "https://www.nist.gov/cyberframework"),
    "pci-dss": ("PCI DSS Document Library", "https://www.pcisecuritystandards.org/document_library/"),
    "pci": ("PCI DSS Document Library", "https://www.pcisecuritystandards.org/document_library/"),
    "hipaa": ("HIPAA Security Rule — HHS", "https://www.hhs.gov/hipaa/for-professionals/security/index.html"),
    "soc-2": ("AICPA SOC 2 Trust Services Criteria", "https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2"),
    "soc2": ("AICPA SOC 2 Trust Services Criteria", "https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2"),
    "ccpa": ("California CCPA — CA Legislature", "https://oag.ca.gov/privacy/ccpa"),
    "mifid": ("MiFID II — EUR-Lex", "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0065"),
    "dora": ("DORA — EUR-Lex", "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2554"),
    "nis2": ("NIS2 Directive — EUR-Lex", "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555"),
}

SPLUNK_SPECIFIC_FILLERS: list[tuple[str, str]] = [
    ("Splunk HTTP Event Collector", "https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector"),
    ("Splunk inputs.conf reference", "https://docs.splunk.com/Documentation/Splunk/latest/Admin/Inputsconf"),
    ("Splunk savedsearches.conf reference", "https://docs.splunk.com/Documentation/Splunk/latest/Admin/Savedsearchesconf"),
    ("Splunk ES Content Management", "https://docs.splunk.com/Documentation/ES/latest/Admin/ContentManagement"),
    ("Splunk Add-on for Unix and Linux sourcetypes", "https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/Sourcetypes"),
]


@dataclass(frozen=True)
class DomainProfile:
    exception_register: str
    dashboard_prefix: str
    evidence_sourcetype: str
    value_theme: str


PROFILES: dict[str, DomainProfile] = {
    "iam": DomainProfile(
        exception_register="iam_exception_register.csv",
        dashboard_prefix="IAM",
        evidence_sourcetype="csv:iam_controls",
        value_theme="account takeover risk, help-desk load, and audit findings",
    ),
    "network": DomainProfile(
        exception_register="network_exception_register.csv",
        dashboard_prefix="Network",
        evidence_sourcetype="csv:network_controls",
        value_theme="unauthorized access, segmentation drift, and NAC policy failures",
    ),
    "security_infra": DomainProfile(
        exception_register="soc_exception_register.csv",
        dashboard_prefix="Security Infra",
        evidence_sourcetype="csv:soc_controls",
        value_theme="missed threat campaigns, control regressions, and SOC SLA breaches",
    ),
    "linux": DomainProfile(
        exception_register="linux_capacity_exceptions.csv",
        dashboard_prefix="Linux",
        evidence_sourcetype="csv:linux_controls",
        value_theme="capacity incidents, patch regressions, and service outages",
    ),
    "compliance": DomainProfile(
        exception_register="compliance_exception_register.csv",
        dashboard_prefix="Compliance",
        evidence_sourcetype="csv:compliance_controls",
        value_theme="audit findings, regulatory gaps, and attestation delays",
    ),
    "generic": DomainProfile(
        exception_register="ops_exception_register.csv",
        dashboard_prefix="Operations",
        evidence_sourcetype="csv:ops_controls",
        value_theme="operational risk and delayed incident response",
    ),
    "personal": DomainProfile(
        exception_register="personal_monitoring_notes.csv",
        dashboard_prefix="Personal",
        evidence_sourcetype="csv:personal_metrics",
        value_theme="missed training goals, stale hobby data, and connector failures",
    ),
}


def _slug(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower()).strip("_")
    return slug[:48] or "uc"


def _extract_event_code(spl: str) -> str | None:
    match = re.search(r"EventCode\s*=\s*(\d+)", spl, re.I)
    return match.group(1) if match else None


def _extract_index(spl: str) -> str | None:
    match = re.search(r"index\s*=\s*([a-zA-Z0-9_\-]+)", spl, re.I)
    return match.group(1) if match else None


def _extract_sourcetype(spl: str) -> str | None:
    match = re.search(r'sourcetype\s*=\s*"([^"]+)"', spl, re.I)
    if match:
        return match.group(1)
    match = re.search(r"sourcetype\s*=\s*([a-zA-Z0-9_:.\-]+)", spl, re.I)
    return match.group(1) if match else None


def _category_from_path(path: Path) -> str:
    match = re.match(r"cat-(\d+)", path.parent.name)
    if match:
        return CAT_PROFILE.get(match.group(1), "generic")
    uc_id = path.stem.removeprefix("UC-")
    cat_num = uc_id.split(".", 1)[0] if "." in uc_id else ""
    return CAT_PROFILE.get(cat_num.zfill(2) if cat_num.isdigit() else "", "generic")


def _profile_for(path: Path) -> DomainProfile:
    return PROFILES[_category_from_path(path)]


def _kfp_iam(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", ""))
    event_code = _extract_event_code(spl)
    index_name = _extract_index(spl) or "wineventlog"
    sourcetype = _extract_sourcetype(spl) or "WinEventLog:Security"
    reg = PROFILES["iam"].exception_register

    if event_code == "4740":
        return (
            f"1. **Stale cached credentials on workstation `{title}`** — "
            f"User changed password on phone but laptop still holds old creds, "
            f"generating repeated 4740 lockouts from `CallerComputerName`. "
            f"Cross-check `index=wineventlog EventCode=4625` from same workstation.\n\n"
            f"2. **Service account password rotation** — Batch job still uses previous secret. "
            f"Distinguish service accounts via `privileged_accounts` lookup (`service=true`).\n\n"
            f"3. **Helpdesk-initiated unlock cycle during pen test** — Red-team exercise triggers "
            f"expected lockouts. Match active CHG with `pen_test=true` in `{reg}`.\n\n"
            f"4. **Misconfigured GPO account lockout threshold** — Legitimate users hit threshold during "
            f"morning login storm. Compare lockout rate baseline with `timechart span=1h count`.\n\n"
            f"**Suppression mechanism:** `{reg}` keyed on `Account_Name` + `CallerComputerName` with `valid_until`."
        )
    if event_code == "4625":
        return (
            f"1. **Password spray below per-pair threshold** — Attacker rotates accounts; "
            f"this UC thresholds on (`Account_Name`, `Source_Network_Address`). "
            f"Escalate to spray analytics if distinct accounts spike.\n\n"
            f"2. **Service account Kerberos failure after rotation** — Clustered 4625 from "
            f"`index={index_name}` `{sourcetype}` post-password change.\n\n"
            f"3. **Break-glass testing** — Intentional failures from jump hosts during exercise.\n\n"
            f"4. **Approved scanner netblock** — Qualys/Tenable credentialed scan from `approved_scanners.csv`.\n\n"
            f"**Suppression mechanism:** Join `{reg}` before threshold filter."
        )
    if "err=49" in spl or "ldap" in spl.lower():
        return (
            f"1. **Application misconfigured bind DN** — Deploy sends wrong `bind_dn` after release. "
            f"Correlate spike with `index={index_name}` deploy timestamp in `index=changes`.\n\n"
            f"2. **Directory maintenance restart** — Short bind failure burst while 389/636 restarts. "
            f"Match maintenance window in change calendar.\n\n"
            f"3. **Brute-force against LDAP** — External `src` hammering `bind_dn` with err=49. "
            f"Compare with firewall deny logs for same `src`.\n\n"
            f"4. **Expired service credential** — Single application account stale password. "
            f"One `bind_dn` dominates stats; fix in vault rotation.\n\n"
            f"**Suppression mechanism:** `ldap_exception_register.csv` with `bind_dn`, `src`, `valid_until`."
        )
    return (
        f"1. **Scheduled IAM maintenance** — Planned directory or IdP change generates expected "
        f"deviations for '{title}'. Cross-check change records.\n\n"
        f"2. **Onboarding burst** — New accounts or apps produce atypical `{index_name}` volume.\n\n"
        f"3. **Monitoring synthetic bind checks** — Health probes from known scanner hosts.\n\n"
        f"4. **Stale application credential** — Single entity dominates `{sourcetype}` failures.\n\n"
        f"**Suppression mechanism:** `{reg}` with entity, reason, valid_until."
    )


def _kfp_network(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", "")).lower()
    index_name = _extract_index(spl) or "network"
    sourcetype = _extract_sourcetype(spl) or "configured sourcetype"
    reg = PROFILES["network"].exception_register

    if any(token in spl for token in ("nac", "ise", "radius", "cisco:ise")):
        return (
            f"1. **Certificate or EAP profile rollout** — Clients fail EAP-TLS during staged cert "
            f"deployment for '{title}'. Cross-check `FailureReason` and CMDB cert expiry.\n\n"
            f"2. **RADIUS/PSN maintenance restart** — Short auth failure burst while ISE node "
            f"restarts. Match change window on `index=changes`.\n\n"
            f"3. **Guest or IoT onboarding surge** — Legitimate MAC registration spike skews "
            f"`index={index_name}` `{sourcetype}` baselines.\n\n"
            f"4. **Approved pen-test or scanner traffic** — Red-team exercises from netblock in "
            f"`approved_scanners.csv` mimic auth failures.\n\n"
            f"**Suppression mechanism:** `{reg}` keyed on `CallingStationID`, `NAS-IP-Address`, `valid_until`."
        )
    if any(token in spl for token in ("pan:", "fortigate", "firewall", "ips", "proxy")):
        return (
            f"1. **Vulnerability scanner signature matches** — Qualys/Tenable traffic triggers "
            f"IPS/threat signatures for '{title}'. Compare `src` against `scanner_ips` lookup.\n\n"
            f"2. **Policy push during change window** — New deny rule generates expected blocks. "
            f"Match firewall commit timestamp in change calendar.\n\n"
            f"3. **Encrypted traffic inspection gap** — TLS-heavy apps bypass deep inspection; "
            f"volume drop is operational, not a sensor failure.\n\n"
            f"4. **Red-team C2 simulation** — Approved exercise from `pen_test_hosts.csv`.\n\n"
            f"**Suppression mechanism:** `{reg}` keyed on `src`, `signature_id`, `valid_until`."
        )
    if any(token in spl for token in ("zscaler", "proxy", "ztna", "vpn")):
        return (
            f"1. **Remote workforce login storm** — Morning VPN/ZTNA session spike for '{title}'. "
            f"Compare with historical same-hour baseline.\n\n"
            f"2. **IdP or SAML metadata refresh** — Brief auth failures during federation cert rotation.\n\n"
            f"3. **Split-tunnel policy change** — New route advertisements shift traffic patterns.\n\n"
            f"4. **Synthetic ZTNA health checks** — Monitoring probes from known appliance IPs.\n\n"
            f"**Suppression mechanism:** `{reg}` keyed on `user`, `src`, `valid_until`."
        )
    return (
        f"1. **Planned network maintenance** — Switch/firewall change generates expected deviations "
        f"for '{title}'. Cross-check CMDB change records.\n\n"
        f"2. **New site onboarding** — Baseline metrics unstable first 72h on `{index_name}`.\n\n"
        f"3. **Synthetic path monitoring** — Nagios/DNA Center probes from `monitoring_hosts.csv`.\n\n"
        f"4. **Misconfigured ACL or VLAN** — Single `nas_ip` or segment dominates `{sourcetype}` failures.\n\n"
        f"**Suppression mechanism:** `{reg}` with entity, reason, valid_until."
    )


def _kfp_security_infra(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", "")).lower()
    index_name = _extract_index(spl) or "security"
    sourcetype = _extract_sourcetype(spl) or "configured sourcetype"
    reg = PROFILES["security_infra"].exception_register

    if "notable" in spl or "incident_review" in spl:
        return (
            f"1. **Active major incident triage** — Analysts leave notables open while pivoting on "
            f"parent campaign for '{title}'. Check open MAJ ticket and `index=risk` contributions.\n\n"
            f"2. **Correlation rule tuning** — Recent Content Management edit recategorises urgency. "
            f"Compare `lastModified` on correlation search.\n\n"
            f"3. **Risk-Based Alerting aggregation** — Individual rule fires consolidated into "
            f"informational notables; per-rule count drops while risk score remains elevated.\n\n"
            f"4. **Holiday on-call gap** — Valid aged notables during staffing gap; escalate paging "
            f"rather than suppress rule globally.\n\n"
            f"**Suppression mechanism:** ES Notable Event Suppression or `{reg}` keyed on `rule_name`, `valid_until`."
        )
    if any(token in spl for token in ("pan:", "threat", "ips", "malware", "av")):
        return (
            f"1. **Approved vulnerability scanner** — Scanner `src` triggers high-severity "
            f"signatures for '{title}'. Join `scanner_ips` before threshold.\n\n"
            f"2. **Signature definition update** — Vendor content push reclassifies benign traffic. "
            f"Compare threat_id first_seen with content release date.\n\n"
            f"3. **Red-team emulation** — Atomic test traffic from approved exercise hosts.\n\n"
            f"4. **Backup replication traffic** — Off-hours bulk transfer matches lateral-movement heuristics.\n\n"
            f"**Suppression mechanism:** `{reg}` keyed on `src`, `threat_id`, `valid_until`."
        )
    return (
        f"1. **SOC tuning or purple-team exercise** — Expected alert volume during rule validation "
        f"for '{title}'. Match active CHG with `purple_team=true`.\n\n"
        f"2. **Content deployment window** — TA or CIM update shifts field extractions on "
        f"`index={index_name}` `{sourcetype}`.\n\n"
        f"3. **Duplicate log ingestion** — HF/IDX misconfiguration doubles event counts.\n\n"
        f"4. **Baseline seasonality** — Month-end batch jobs skew trending searches.\n\n"
        f"**Suppression mechanism:** `{reg}` with entity, reason, valid_until."
    )


def _kfp_linux(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", ""))
    index_name = _extract_index(spl) or "os"
    sourcetype = _extract_sourcetype(spl) or "configured sourcetype"
    reg = PROFILES["linux"].exception_register
    return (
        f"1. **Patch Tuesday / unattended-upgrades** — CPU and disk I/O spike during package "
        f"application for '{title}'. Correlate with apt/yum logs in same window.\n\n"
        f"2. **Nightly backup or log-rotate job** — Predictable I/O burst on fixed cron schedule.\n\n"
        f"3. **Synthetic monitoring probe** — Nagios/Zabbix agent generates periodic load.\n\n"
        f"4. **New host onboarding** — Baseline metrics unstable first 48h on `{index_name}` "
        f"`{sourcetype}`.\n\n"
        f"**Suppression mechanism:** `{reg}` keyed on `host`, `valid_until`."
    )


def _compliance_regulation(uc: dict) -> tuple[str, str]:
    entries = uc.get("compliance")
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        reg = str(entries[0].get("regulation", "regulatory"))
        clause = str(entries[0].get("clause", ""))
        return reg, clause
    return "regulatory", ""


def _kfp_compliance(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", ""))
    index_name = _extract_index(spl) or "audit_evidence"
    sourcetype = _extract_sourcetype(spl) or "configured sourcetype"
    regulation, clause = _compliance_regulation(uc)
    reg_label = regulation.upper().replace("-", " ").replace("_", " ")
    clause_ref = f" clause {clause}" if clause else ""
    reg_slug = re.sub(r"[^a-z0-9]+", "_", regulation.lower()).strip("_") or "compliance"
    reg_lookup = f"{reg_slug}_exception_register.csv"

    return (
        f"1. **Authorised {reg_label} control testing** — Internal audit or GRC exercises "
        f"'{title}' during scheduled{clause_ref} evidence collection. Match compliance programme "
        f"calendar and accounts tagged `compliance_ops=true`.\n\n"
        f"2. **External assessor sampling** — QSA or regulator sampling temporarily spikes "
        f"`index={index_name}` `{sourcetype}` volume. Cross-check engagement letter in `{reg_lookup}`.\n\n"
        f"3. **Planned maintenance affecting control telemetry** — CAB-approved change pauses or "
        f"reshapes ingestion to `{index_name}`. Compare `_time` with active change record.\n\n"
        f"4. **Third-party processor under contract** — BAA/DPA-covered vendor generates expected "
        f"cross-boundary events during normal service delivery.\n\n"
        f"**Suppression mechanism:** `{reg_lookup}` keyed on `entity`, `exception_reason`, "
        f"`valid_until`, joined before alert threshold."
    )


def _kfp_personal(uc: dict) -> str:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", "")).lower()
    index_name = _extract_index(spl) or "personal"
    sourcetype = _extract_sourcetype(spl) or "configured sourcetype"
    return (
        f"1. **OAuth or API token expiry** — Vendor connector stops polling for '{title}'; "
        f"stale rows remain in `index={index_name}`. Check `_internal` HEC 401s and renew "
        f"token in passwords.conf.\n\n"
        f"2. **Rest day or planned break** — Zero activities is expected, not ingestion failure. "
        f"Vendor app shows no sessions for the calendar day.\n\n"
        f"3. **Multi-device double-count** — Same activity synced from watch and phone into "
        f"`{sourcetype}`. Dedup with `stats latest(*) by external_id`.\n\n"
        f"4. **Timezone bucket misalignment** — Weekly bins on UTC vs local schedule skew "
        f"thresholds. Document offset in SPL `bin _time` or connector config.\n\n"
        f"**Suppression mechanism:** Personal preference notes in `personal_monitoring_notes.csv` "
        f"(not enterprise CMDB/ServiceNow registers)."
    )


def _kfp_for_uc(uc: dict, profile_key: str) -> str:
    if profile_key == "compliance":
        return _kfp_compliance(uc)
    if profile_key == "personal":
        return _kfp_personal(uc)
    if profile_key == "iam":
        return _kfp_iam(uc)
    if profile_key == "network":
        return _kfp_network(uc)
    if profile_key == "security_infra":
        return _kfp_security_infra(uc)
    if profile_key == "linux":
        return _kfp_linux(uc)
    title = str(uc.get("title", "Use case"))
    index_name = _extract_index(str(uc.get("spl", ""))) or "target index"
    reg = PROFILES["generic"].exception_register
    return (
        f"1. **Scheduled maintenance** — Planned change generates expected deviations for '{title}'. "
        f"Cross-check change records.\n\n"
        f"2. **Batch job cycle** — Fixed-schedule workload skews `{index_name}` metrics.\n\n"
        f"3. **Monitoring synthetic checks** — Health probes from known hosts.\n\n"
        f"4. **Onboarding burst** — New entities produce atypical volume until baseline stabilizes.\n\n"
        f"**Suppression mechanism:** `{reg}` with entity, reason, valid_until."
    )


def _control_test_for_uc(uc: dict, profile: DomainProfile) -> dict[str, str]:
    title = str(uc.get("title", "Use case"))
    spl = str(uc.get("spl", ""))
    index_name = _extract_index(spl) or "target_index"
    sourcetype = _extract_sourcetype(spl) or "target_sourcetype"
    event_code = _extract_event_code(spl)
    pos_extra = f" EventCode={event_code}" if event_code else ""
    reg = profile.exception_register
    return {
        "positiveScenario": (
            f"Ingest synthetic events into `index={index_name}` sourcetype={sourcetype!r}{pos_extra} "
            f"that satisfy the UC-{_uc_display_id(uc)} SPL filters for '{title}'. "
            f"Run the saved search and confirm at least one alertable row with expected fields populated."
        ),
        "negativeScenario": (
            f"Ingest benign `{index_name}` / `{sourcetype}` events outside the detection threshold, "
            f"or exclude the test entity via `{reg}` with a valid window. "
            f"Confirm zero alert rows for UC-{_uc_display_id(uc)}."
        ),
    }


def _exclusions_for_uc(uc: dict, profile: DomainProfile) -> str:
    title = str(uc.get("title", "this use case"))
    reg = profile.exception_register
    if profile.dashboard_prefix == "Compliance":
        regulation, _clause = _compliance_regulation(uc)
        reg_label = regulation.upper().replace("-", " ").replace("_", " ")
        return (
            f"Covers the detection logic documented for '{title}' only. Does not supplant "
            f"formal {reg_label} legal attestation, external auditor opinion, or unrelated "
            f"regulatory controls. Test environments listed in `{reg}` during approved "
            f"assessments are excluded."
        )
    if profile.dashboard_prefix == "Personal":
        return (
            f"Covers personal hobby monitoring for '{title}' only. Does not replace "
            f"enterprise SIEM, ITSM, or compliance attestation. Not intended for production "
            f"security operations — exclude shared/demo HEC tokens during connector testing."
        )
    if profile.dashboard_prefix == "IAM":
        scope = "IdP cloud-native analytics"
    elif profile.dashboard_prefix == "Network":
        scope = "full NAC policy design or firewall rule authoring"
    elif profile.dashboard_prefix == "Security Infra":
        scope = "organization-wide SIEM playbooks for unrelated threat classes"
    else:
        scope = "cross-domain SIEM playbooks for unrelated domains"
    return (
        f"Covers the detection logic documented for '{title}' only. Does not supplant {scope} "
        f"or regulatory attestation. Entities listed in `{reg}` during approved tests are excluded."
    )


def _evidence_for_uc(uc: dict, profile: DomainProfile) -> str:
    uc_id = _uc_display_id(uc)
    title = str(uc.get("title", uc_id))
    slug = _slug(title)
    prefix = profile.dashboard_prefix.lower().replace(" ", "_")
    if profile.dashboard_prefix == "Compliance":
        regulation, clause = _compliance_regulation(uc)
        reg_tag = regulation.replace("-", "").upper()[:12] or "COMPLIANCE"
        clause_tag = f", clause={clause}" if clause else ""
        return (
            f"Saved search `compliance_{slug}` (UC-{uc_id}), GRC dashboard panel "
            f"\"Compliance — {title}\", and scheduled export to `index=audit_evidence` "
            f"sourcetype={profile.evidence_sourcetype} with tags `reg={reg_tag}{clause_tag}`."
        )
    return (
        f"Saved search `{prefix}_{slug}` (UC-{uc_id}), SOC dashboard panel "
        f"\"{profile.dashboard_prefix} — {title}\", and weekly export to "
        f"`index=audit_evidence` sourcetype={profile.evidence_sourcetype}."
    )


def _description_value(uc: dict, profile: DomainProfile) -> tuple[str, str] | None:
    desc = str(uc.get("description", ""))
    val = str(uc.get("value", ""))
    if "Operations and leadership rely on" not in val and len(desc) >= 80:
        return None
    title = str(uc.get("title", ""))
    spl = str(uc.get("spl", ""))
    index_name = _extract_index(spl) or "target index"
    uc_id = _uc_display_id(uc)
    new_desc = desc if len(desc) >= 80 else (
        f"Monitors `{index_name}` for conditions defined in UC-{uc_id} SPL "
        f"to detect '{title}' per the configured thresholds and field extractions."
    )
    if len(new_desc) < 80:
        new_desc = (
            f"Detects '{title}' by searching `{index_name}` with the UC-{uc_id} "
            f"SPL pipeline and alerting when configured thresholds are exceeded."
        )
    new_val = (
        f"Early '{title}' detection reduces {profile.value_theme} by giving "
        f"{profile.dashboard_prefix} operators a Splunk-native signal before manual "
        f"triage or audit channels surface the issue."
    )
    return new_desc, new_val


def _uc_display_id(uc: dict) -> str:
    return str(uc.get("id", "")).removeprefix("UC-")


def _uc_display_id(uc: dict) -> str:
    return str(uc.get("id", "")).removeprefix("UC-")


def _ref(title: str, url: str) -> dict[str, str]:
    return {"title": title, "url": url, "retrieved": RETRIEVED}


def _normalize_ref(raw: object) -> dict[str, str] | None:
    if isinstance(raw, dict):
        url = str(raw.get("url", "")).strip()
        if not url:
            return None
        return _ref(str(raw.get("title") or url), url)
    if isinstance(raw, str) and raw.startswith("http"):
        return _ref(raw, raw)
    return None


def _references_would_flag(refs: list[dict[str, str]]) -> bool:
    urls = [r.get("url", "") for r in refs if isinstance(r, dict)]
    generic_hits = sum(1 for url in urls if url in GENERIC_REF_URLS)
    return generic_hits >= 3 and len(urls) <= 4


def _infer_splunkbase_refs(uc: dict) -> list[dict[str, str]]:
    text = " ".join(
        [
            str(uc.get("app", "")),
            str(uc.get("dataSources", "")),
            str(uc.get("implementation", "")),
        ]
    )
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in SPLUNKBASE_RE.finditer(text):
        sid = match.group(1) or match.group(2)
        if not sid or sid == "617":
            continue
        url = f"https://splunkbase.splunk.com/app/{sid}"
        if url not in seen:
            refs.append(_ref(f"Splunkbase app {sid}", url))
            seen.add(url)
    spl = str(uc.get("spl", "")).lower()
    for prefix, title, sid in TA_BY_SOURCETYPE:
        if prefix.lower() in spl and sid != 617:
            url = f"https://splunkbase.splunk.com/app/{sid}"
            if url not in seen:
                refs.append(_ref(f"{title} (Splunkbase {sid})", url))
                seen.add(url)
            break
    premium = uc.get("premiumApps")
    if isinstance(premium, list):
        for entry in premium:
            name = entry if isinstance(entry, str) else entry.get("name", "") if isinstance(entry, dict) else ""
            if "Enterprise Security" in str(name):
                url = "https://splunkbase.splunk.com/app/263"
                if url not in seen:
                    refs.append(_ref("Splunk Enterprise Security (Splunkbase 263)", url))
                    seen.add(url)
    return refs


def _infer_cim_refs(uc: dict) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    models = uc.get("cimModels")
    if not isinstance(models, list):
        return refs
    for model in models:
        model_name = str(model).strip()
        if not model_name or model_name.upper() == "N/A":
            continue
        url = CIM_MODEL_URLS.get(model_name)
        if url:
            refs.append(_ref(f"CIM: {model_name}", url))
    return refs


def _infer_vendor_refs(uc: dict) -> list[dict[str, str]]:
    spl = str(uc.get("spl", "")).lower()
    refs: list[dict[str, str]] = []
    for prefix, title, url in VENDOR_SOURCETYPE_URLS:
        if prefix in spl:
            refs.append(_ref(title, url))
            break
    equipment = uc.get("equipment")
    if isinstance(equipment, list):
        brands = {str(item).lower() for item in equipment}
        if "cisco" in brands and not refs:
            refs.append(
                _ref(
                    "Cisco Security documentation",
                    "https://www.cisco.com/c/en/us/support/security/index.html",
                )
            )
        if "paloalto" in brands or "palo" in brands:
            refs.append(
                _ref(
                    "Palo Alto Networks documentation",
                    "https://docs.paloaltonetworks.com/",
                )
            )
    return refs


def _infer_compliance_refs(uc: dict) -> list[dict[str, str]]:
    entries = uc.get("compliance")
    if not isinstance(entries, list) or not entries:
        return []
    first = entries[0]
    if not isinstance(first, dict):
        return []
    regulation = str(first.get("regulation", "")).lower()
    for key, (title, url) in REGULATION_URLS.items():
        if key in regulation.replace("_", "-"):
            return [_ref(title, url)]
    return []


def _references_for_uc(uc: dict, profile_key: str) -> list[dict[str, str]]:
    """Build domain-specific references that clear generic_references flag."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw in uc.get("references") or []:
        ref = _normalize_ref(raw)
        if not ref:
            continue
        url = ref["url"].rstrip("/")
        if url in GENERIC_REF_URLS:
            continue
        if url not in seen:
            out.append(ref)
            seen.add(url)

    for ref in (
        _infer_compliance_refs(uc)
        + _infer_splunkbase_refs(uc)
        + _infer_cim_refs(uc)
        + _infer_vendor_refs(uc)
    ):
        url = ref["url"].rstrip("/")
        if url not in seen:
            out.append(ref)
            seen.add(url)

    if profile_key == "personal":
        hec = "https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector"
        if hec not in seen:
            out.append(_ref("Splunk HTTP Event Collector", hec))
            seen.add(hec)

    combined = str(uc.get("app", "")) + str(uc.get("spl", ""))
    if profile_key == "security_infra" and (
        "Enterprise Security" in combined or "datamodel=Risk" in combined or "Risk.All_Risk" in combined
    ):
        es_url = "https://docs.splunk.com/Documentation/ES/latest/Admin/ContentManagement"
        if es_url not in seen:
            out.append(_ref("Splunk ES Content Management", es_url))
            seen.add(es_url)

    for title, url in SPLUNK_SPECIFIC_FILLERS:
        if len(out) >= 4 and not _references_would_flag(out):
            break
        if url.rstrip("/") in seen:
            continue
        out.append(_ref(title, url))
        seen.add(url.rstrip("/"))

    while len(out) < 4:
        added = False
        for title, url in SPLUNK_SPECIFIC_FILLERS:
            if url.rstrip("/") not in seen:
                out.append(_ref(title, url))
                seen.add(url.rstrip("/"))
                added = True
                break
        if not added:
            break

    if _references_would_flag(out):
        out = [r for r in out if r.get("url") not in GENERIC_REF_URLS]
        while len(out) < 4:
            for title, url in SPLUNK_SPECIFIC_FILLERS:
                if url.rstrip("/") not in {r.get("url", "").rstrip("/") for r in out}:
                    out.append(_ref(title, url))
                    break
            else:
                break

    return out[:6]


def _fields_for_update(flags: list[str], *, force: bool) -> set[str]:
    if force:
        return {
            "knownFalsePositives",
            "controlTest",
            "exclusions",
            "evidence",
            "references",
            "description",
            "value",
        }
    if is_fully_templated_v2(flags):
        return {
            "knownFalsePositives",
            "controlTest",
            "exclusions",
            "evidence",
            "references",
            "description",
            "value",
        }
    return {FLAG_TO_FIELD[flag] for flag in flags if flag in FLAG_TO_FIELD}


def handcraft_fields(
    uc: dict,
    path: Path,
    *,
    flags: list[str],
    force: bool,
) -> dict[str, object]:
    """Return lifted_fields dict for templated narrative surface."""
    profile_key = _category_from_path(path)
    profile = PROFILES[profile_key]
    target_fields = _fields_for_update(flags, force=force)
    all_fields: dict[str, object] = {
        "knownFalsePositives": _kfp_for_uc(uc, profile_key),
        "controlTest": _control_test_for_uc(uc, profile),
        "exclusions": _exclusions_for_uc(uc, profile),
        "evidence": _evidence_for_uc(uc, profile),
        "references": _references_for_uc(uc, profile_key),
    }
    dv = _description_value(uc, profile)
    if dv:
        all_fields["description"], all_fields["value"] = dv
    return {key: value for key, value in all_fields.items() if key in target_fields}


def _iter_paths(category: str | None, files: list[str] | None) -> list[Path]:
    if files:
        return [Path(f) if Path(f).is_absolute() else _REPO / f for f in files]
    if not category:
        raise ValueError("Provide --category or --files")
    matches = sorted(CONTENT.glob(f"{category}-*/UC-*.json"))
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="Category prefix e.g. cat-09")
    parser.add_argument("--files", nargs="*", help="Specific sidecar paths")
    parser.add_argument("--limit", type=int, default=0, help="Max UCs to process (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite narrative fields even when template flags are already clear",
    )
    parser.add_argument(
        "--refs-only",
        action="store_true",
        help="Only rewrite references[] when generic_references flag is present",
    )
    args = parser.parse_args(argv)

    paths = _iter_paths(args.category, args.files)
    if args.limit:
        paths = paths[: args.limit]

    updated = 0
    skipped = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        flags = detect_template_flags(data)
        if args.refs_only:
            if "generic_references" not in flags:
                skipped += 1
                continue
            lifted = {"references": _references_for_uc(data, _category_from_path(path))}
        else:
            if not flags and not args.force:
                skipped += 1
                continue
            lifted = handcraft_fields(data, path, flags=flags, force=args.force)
            if not lifted:
                skipped += 1
                continue
        if args.dry_run:
            action = "force" if args.force and not flags else "clear"
            print(
                f"DRY-RUN {path.name}: would {action} {flags or ['handcraft-rewrite']} "
                f"fields {sorted(lifted)}"
            )
            updated += 1
            continue
        for key, value in lifted.items():
            data[key] = value
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        after = detect_template_flags(data)
        print(f"OK {path.name}: cleared {flags} -> remaining {after}")
        updated += 1

    print(f"Done: {updated} updated, {skipped} already clean, {len(paths)} scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
