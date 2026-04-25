<!-- AUTO-GENERATED from UC-5.4.35.json — DO NOT EDIT -->

---
id: "5.4.35"
title: "Aruba Air Monitor — WIDS/WIPS Events (HPE Aruba)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.35 · Aruba Air Monitor — WIDS/WIPS Events (HPE Aruba)

## Description

Aruba's Wireless Intrusion Detection and Prevention System (WIDS/WIPS) detects rogue APs, evil twin attacks, ad-hoc networks, unauthorized bridges, and DoS attacks (deauthentication floods, association floods). Air Monitor (AM) mode APs or hybrid APs provide dedicated RF security scanning.

## Value

Aruba's Wireless Intrusion Detection and Prevention System (WIDS/WIPS) detects rogue APs, evil twin attacks, ad-hoc networks, unauthorized bridges, and DoS attacks (deauthentication floods, association floods). Air Monitor (AM) mode APs or hybrid APs provide dedicated RF security scanning.

## Implementation

Enable WIDS/WIPS and AM-capable APs per Aruba design guide; ensure security-class syslog messages are forwarded with TA parsing for threat category and severity. Tune alerts for critical classes (rogue AP, evil twin, deauth flood). Correlate with physical site/AP layout for containment workflows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Aruba Networks Add-on for Splunk` (Splunkbase 4668).
• Ensure the following data sources are available: `sourcetype=aruba:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable WIDS/WIPS and AM-capable APs per Aruba design guide; ensure security-class syslog messages are forwarded with TA parsing for threat category and severity. Tune alerts for critical classes (rogue AP, evil twin, deauth flood). Correlate with physical site/AP layout for containment workflows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids" OR subsystem="WIDS" OR match(_raw, "(?i)(rogue|evil.twin|ad-hoc|deauth|disassoc).*(flood|detected|attack|alert)"))
| eval threat_type=coalesce(wids_classification, threat_name, intrusion_type, ids_signature, alert_type)
| eval sev=coalesce(severity, threat_severity, priority)
| stats count by threat_type, sev, ap_name, channel, detecting_ap, bssid
| sort -count
```

Understanding this SPL

**Aruba Air Monitor — WIDS/WIPS Events (HPE Aruba)** — Aruba's Wireless Intrusion Detection and Prevention System (WIDS/WIPS) detects rogue APs, evil twin attacks, ad-hoc networks, unauthorized bridges, and DoS attacks (deauthentication floods, association floods). Air Monitor (AM) mode APs or hybrid APs provide dedicated RF security scanning.

Documented **Data sources**: `sourcetype=aruba:syslog`. **App/TA** (typical add-on context): `Aruba Networks Add-on for Splunk` (Splunkbase 4668). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: aruba:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="aruba:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **threat_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **sev** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by threat_type, sev, ap_name, channel, detecting_ap, bssid** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Aruba Central, the mobility controller UI, or ClearPass Policy Manager (Access Tracker / policy views), compare authentication and health events with the search for the same timeframe.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (threat type, severity, channel, detecting AP), Bar chart (threats by type), Timeline (WIDS event rate), Map or floor plan overlay when location fields exist.

## SPL

```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids" OR subsystem="WIDS" OR match(_raw, "(?i)(rogue|evil.twin|ad-hoc|deauth|disassoc).*(flood|detected|attack|alert)"))
| eval threat_type=coalesce(wids_classification, threat_name, intrusion_type, ids_signature, alert_type)
| eval sev=coalesce(severity, threat_severity, priority)
| stats count by threat_type, sev, ap_name, channel, detecting_ap, bssid
| sort -count
```

## Visualization

Table (threat type, severity, channel, detecting AP), Bar chart (threats by type), Timeline (WIDS event rate), Map or floor plan overlay when location fields exist.

## References

- [Splunkbase app 4668](https://splunkbase.splunk.com/app/4668)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
