#!/usr/bin/env python3
"""
Uplift 22.2.x NIS2 UCs from Silver/Bronze to Gold by adding:
1. equipmentModels (derived from equipment + app fields)
2. Product-specific troubleshooting in detailedImplementation
3. equipment field (for Bronze UCs missing it)
4. Fix cimModels ["N/A"] -> []
"""

import json
import glob
import os
import re

EQUIPMENT_MODEL_MAP = {
    "servicenow": [
        "ServiceNow ITSM / Security Incident Response (SIR) module",
    ],
    "m365": [
        "Microsoft 365 Defender (audit log, unified audit)",
        "Microsoft Entra ID (Azure AD sign-in and audit logs)",
    ],
    "okta": [
        "Okta Identity Cloud (System Log API v1)",
    ],
    "tenable": [
        "Tenable.io / Tenable.sc (vulnerability scan exports)",
    ],
    "pagerduty": [
        "PagerDuty (incident notification and escalation)",
    ],
    "azure": [
        "Microsoft Azure (Activity Log, Entra ID sign-in logs)",
    ],
    "itsi": [
        "Splunk IT Service Intelligence (ITSI) 4.x+ (KPI and service monitoring)",
    ],
    "cyberark": [
        "CyberArk Privileged Access Security (vault audit logs)",
    ],
    "cisco": [
        "Cisco network infrastructure (syslog, NetFlow, Firepower)",
    ],
    "qualys": [
        "Qualys Cloud Platform (vulnerability and compliance scan data)",
    ],
    "github": [
        "GitHub Enterprise (audit log API, webhook events)",
    ],
    "hashicorp": [
        "HashiCorp Vault (secret management audit logs)",
    ],
    "syslog": [
        "RFC 5424 syslog sources (network devices, firewalls, servers)",
    ],
    "stream": [
        "Splunk Stream (wire data capture, protocol analysis)",
    ],
    "jira": [
        "Atlassian JIRA (issue tracking, workflow audit)",
    ],
    "paloalto": [
        "Palo Alto Networks (PAN-OS syslog, Cortex Data Lake)",
    ],
    "edge_hub": [
        "Splunk Edge Hub (OT/IoT protocol data collection)",
    ],
    "modbus": [
        "Modbus TCP/RTU (industrial control protocol data)",
    ],
    "exchange": [
        "Microsoft Exchange Online (message tracking logs)",
    ],
    "gitlab": [
        "GitLab (audit events, CI/CD pipeline logs)",
    ],
    "jenkins": [
        "Jenkins (build and deployment audit logs)",
    ],
    "aws": [
        "AWS CloudTrail (API audit logs)",
    ],
    "broadcom_symantec": [
        "Broadcom Symantec Endpoint Protection (SEP event logs)",
    ],
    "zscaler": [
        "Zscaler Internet Access (ZIA web and DNS logs)",
    ],
    "commvault": [
        "Commvault (backup job status and audit logs)",
    ],
    "veeam": [
        "Veeam Backup & Replication (backup job audit logs)",
    ],
    "suricata": [
        "Suricata IDS/IPS (EVE JSON alert and flow logs)",
    ],
    "snmp": [
        "SNMP v2c/v3 (network device polling and traps)",
    ],
    "proofpoint": [
        "Proofpoint Email Protection (TAP API, message trace)",
    ],
    "crowdstrike": [
        "CrowdStrike Falcon (Streaming API, detection events)",
    ],
    "opcua": [
        "OPC UA (industrial automation data)",
    ],
    "itsm": [
        "ITSM platform (change, incident, and problem records)",
    ],
    "dell_emc": [
        "Dell EMC (storage and infrastructure logs)",
    ],
    "infoblox": [
        "Infoblox DDI (DNS, DHCP, IPAM audit logs)",
    ],
    "hecv2": [
        "Splunk HTTP Event Collector v2 (HECv2 data ingestion)",
    ],
    "splunk-es": [
        "Splunk Enterprise Security 7.x (notable framework, correlation rules)",
    ],
    "splunk-soar": [
        "Splunk SOAR 6.x (playbook orchestration and automation)",
    ],
}

TROUBLESHOOTING_TEMPLATES = {
    "splunk-es": (
        '• **Notable macro returns 0 events.** '
        'Verify the correlation rule is enabled and producing notables: '
        '`` `notable` earliest=-24h | stats count by rule_name '
        '| search rule_name="*{rule_hint}*" ``. '
        'If the rule is disabled, re-enable in ES > Configure > Content > Content Management.\n'
        '• **Data model acceleration not running.** '
        'Check: `| rest /services/admin/summarization by_tstats=t '
        '| search datamodel_name=* | where is_inprogress=1 '
        '| table datamodel_name eai:acl.app`. '
        'If the relevant model is missing, enable acceleration in ES > Settings > Data Models.'
    ),
    "servicenow": (
        '• **ServiceNow events missing or stale.** '
        'Check the Splunk Add-on for ServiceNow scripted input: '
        '`index=_internal source=*ta_snow* OR source=*servicenow* '
        '| stats max(_time) as last_poll | eval lag_h=round((now()-last_poll)/3600,1)`. '
        'If `lag_h > 2`, the input may have failed — check ServiceNow API credentials and instance URL.\n'
        '• **Field mapping mismatch.** '
        'ServiceNow field names may differ between instances (e.g. custom prefixes). '
        'Verify key fields with `index=snow OR index=soar sourcetype=servicenow:* earliest=-1h '
        '| fieldsummary | where count>0 | table field count distinct_count`.'
    ),
    "okta": (
        '• **Okta events not appearing.** '
        'Check the Splunk Add-on for Okta input: '
        '`index=_internal source=*okta* '
        '| stats max(_time) as last_poll | eval lag_h=round((now()-last_poll)/3600,1)`. '
        'Common causes: expired API token (Okta tokens expire after 30 days of inactivity), '
        'IP allowlist changes on the Okta org, or System Log API rate limiting (50 req/min).'
    ),
    "m365": (
        '• **Microsoft 365 audit events missing.** '
        'Verify the Splunk Add-on for Microsoft Cloud Services input: '
        '`index=_internal source=*ms_cloud* OR source=*o365* '
        '| stats max(_time) as last_poll | eval lag_h=round((now()-last_poll)/3600,1)`. '
        'Common causes: Azure app registration secret expired (check expiry in Azure Portal > App Registrations), '
        'Microsoft Graph API permissions changed, or tenant admin consent revoked.'
    ),
    "tenable": (
        '• **Vulnerability scan data stale.** '
        'Check: `index=vuln sourcetype=tenable:* | stats max(_time) as last_event '
        '| eval lag_days=round((now()-last_event)/86400,1)`. '
        'If `lag_days > 7`, the Tenable export may have failed — '
        'verify API access key validity and Tenable.io connectivity.'
    ),
    "cyberark": (
        '• **CyberArk vault audit events missing.** '
        'Verify the CyberArk syslog or SIEM integration: '
        '`index=pam sourcetype=cyberark:* | stats max(_time) as last_event '
        '| eval lag_h=round((now()-last_event)/3600,1)`. '
        'Common causes: vault syslog forwarding disabled after upgrade, '
        'or the CyberArk SIEM connector service needs restart.'
    ),
    "paloalto": (
        '• **Palo Alto firewall logs missing.** '
        'Check syslog ingestion: `index=firewall sourcetype=pan:* '
        '| stats max(_time) as last_event | eval lag_min=round((now()-last_event)/60,1)`. '
        'Common causes: syslog server profile changed on the firewall, '
        'or SC4S/syslog-ng container restarted without persistent configuration.'
    ),
    "azure": (
        '• **Azure activity logs not ingesting.** '
        'Check: `index=azure sourcetype=azure:* | stats max(_time) as last_event '
        '| eval lag_h=round((now()-last_event)/3600,1)`. '
        'Common causes: Azure Event Hub consumer group issue, '
        'or the Azure Monitor diagnostic settings were modified.'
    ),
    "qualys": (
        '• **Qualys scan data missing.** '
        'Check: `index=vuln sourcetype=qualys:* | stats max(_time) as last_event '
        '| eval lag_days=round((now()-last_event)/86400,1)`. '
        'Common causes: Qualys API credentials expired, or scan schedule paused in Qualys console.'
    ),
    "crowdstrike": (
        '• **CrowdStrike detection events not appearing.** '
        'Check: `index=edr sourcetype=crowdstrike:* | stats max(_time) as last_event '
        '| eval lag_h=round((now()-last_event)/3600,1)`. '
        'Common causes: Falcon Streaming API OAuth2 token expired, '
        'or the CrowdStrike TA input was disabled during a Splunk restart.'
    ),
    "github": (
        '• **GitHub audit events not ingesting.** '
        'Check: `index=devops sourcetype=github:* | stats max(_time) as last_event '
        '| eval lag_h=round((now()-last_event)/3600,1)`. '
        'Common causes: GitHub Personal Access Token expired, '
        'or the GitHub Enterprise audit log streaming webhook was disabled.'
    ),
    "hashicorp": (
        '• **HashiCorp Vault audit events missing.** '
        'Check: `index=vault sourcetype=hashicorp:vault:audit | stats max(_time) as last_event '
        '| eval lag_h=round((now()-last_event)/3600,1)`. '
        'Common causes: Vault audit device disabled after seal/unseal, '
        'or syslog forwarding target changed.'
    ),
    "itsi": (
        '• **ITSI KPI data not appearing.** '
        'Check: `index=itsi_summary | stats max(_time) as last_event '
        '| eval lag_min=round((now()-last_event)/60,1)`. '
        'Common causes: ITSI service not configured, '
        'KPI base search disabled, or summary index permissions missing.'
    ),
    "stream": (
        '• **Splunk Stream wire data missing.** '
        'Check: `index=netflow OR index=stream sourcetype=stream:* '
        '| stats max(_time) as last_event | eval lag_min=round((now()-last_event)/60,1)`. '
        'Common causes: Stream forwarder (streamfwd) process not running on capture host, '
        'or network tap/mirror port misconfigured.'
    ),
}


def derive_equipment_models(equipment_list, app_str, ds_str):
    models = []
    seen_keys = set()

    for eq in equipment_list:
        eq_lower = eq.lower()
        if eq_lower in EQUIPMENT_MODEL_MAP and eq_lower not in seen_keys:
            models.extend(EQUIPMENT_MODEL_MAP[eq_lower])
            seen_keys.add(eq_lower)

    if "Enterprise Security" in app_str and "splunk-es" not in seen_keys:
        models.extend(EQUIPMENT_MODEL_MAP["splunk-es"])
        seen_keys.add("splunk-es")

    if ("SOAR" in app_str or "Phantom" in app_str) and "splunk-soar" not in seen_keys:
        models.extend(EQUIPMENT_MODEL_MAP["splunk-soar"])
        seen_keys.add("splunk-soar")

    if not models:
        if "Splunk Enterprise" in app_str:
            models.append("Splunk Enterprise 9.x (search platform)")
        else:
            models.append("Splunk Enterprise / Splunk Cloud Platform")

    return models


def derive_equipment_from_app(app_str, ds_str):
    equipment = []
    if "Enterprise Security" in app_str:
        equipment.append("splunk-es")
    if "SOAR" in app_str or "Phantom" in app_str:
        equipment.append("splunk-soar")
    if "ServiceNow" in app_str or "servicenow" in ds_str.lower():
        equipment.append("servicenow")
    if "Stream" in app_str:
        equipment.append("stream")
    return equipment if equipment else ["splunk-es"]


def build_troubleshooting(equipment_list, app_str, title):
    sections = []
    seen = set()

    rule_hint = title.split("—")[-1].strip()[:30] if "—" in title else title[:30]

    if "Enterprise Security" in app_str and "splunk-es" not in seen:
        sections.append(
            TROUBLESHOOTING_TEMPLATES["splunk-es"].format(rule_hint=rule_hint)
        )
        seen.add("splunk-es")

    for eq in equipment_list:
        eq_lower = eq.lower()
        if eq_lower in TROUBLESHOOTING_TEMPLATES and eq_lower not in seen:
            sections.append(
                TROUBLESHOOTING_TEMPLATES[eq_lower].format(rule_hint=rule_hint)
            )
            seen.add(eq_lower)

    if not sections:
        sections.append(
            '• **Search returns 0 results.** '
            'Verify data is being ingested: check `index=_internal sourcetype=splunkd '
            'component=Metrics group=per_index_thruput` for the relevant indexes. '
            'If no throughput, the data input is not running — check inputs.conf and TA configuration.\n'
            '• **Field extractions missing.** '
            'Verify with `| fieldsummary` on a sample of events. '
            'If key fields are not extracted, check props.conf field aliases and transforms.'
        )

    return "\n".join(sections)


def has_troubleshooting(di):
    return bool(re.search(r'(?i)(troubleshoot|step\s*5)', di))


def process_file(filepath):
    with open(filepath) as f:
        data = json.load(f)

    uc_id = data.get("id", "")
    if not uc_id.startswith("22.2."):
        return False

    modified = False
    app_str = data.get("app", "")
    ds_str = data.get("dataSources", "")
    title = data.get("title", "")
    equipment = data.get("equipment", [])

    if data.get("cimModels") == ["N/A"]:
        data["cimModels"] = []
        if data.get("dataModelAcceleration") == "Not applicable":
            data["dataModelAcceleration"] = "Not required for this use case."
        modified = True

    if not equipment:
        equipment = derive_equipment_from_app(app_str, ds_str)
        data["equipment"] = equipment
        modified = True

    if "equipmentModels" not in data or not data["equipmentModels"]:
        models = derive_equipment_models(equipment, app_str, ds_str)
        data["equipmentModels"] = models
        modified = True

    di = data.get("detailedImplementation", "")
    if di and not has_troubleshooting(di):
        trouble = build_troubleshooting(equipment, app_str, title)
        data["detailedImplementation"] = (
            di.rstrip()
            + "\n\nStep 5 — Troubleshooting\n"
            + trouble
        )
        modified = True

    if modified:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return modified


def main():
    files = sorted(glob.glob("content/cat-22-regulatory-compliance/UC-22.2.*.json"))
    modified_count = 0
    for filepath in files:
        try:
            if process_file(filepath):
                modified_count += 1
                print(f"  Updated: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ERROR: {os.path.basename(filepath)}: {e}")

    print(f"\nTotal updated: {modified_count} / {len(files)}")


if __name__ == "__main__":
    main()
