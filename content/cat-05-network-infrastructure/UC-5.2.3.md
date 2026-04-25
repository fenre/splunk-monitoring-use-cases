<!-- AUTO-GENERATED from UC-5.2.3.json — DO NOT EDIT -->

---
id: "5.2.3"
title: "Threat Detection Events"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.3 · Threat Detection Events

## Description

IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.

## Value

IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.

## Implementation

Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:threat`, `sourcetype=cisco:firepower:alert`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src, dest, threat_name, severity, action | sort -count
```

Understanding this SPL

**Threat Detection Events** — IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.

Documented **Data sources**: `sourcetype=pan:threat`, `sourcetype=cisco:firepower:alert`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:threat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:threat". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest, threat_name, severity, action** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, dest, threat, action), Bar chart by threat type, Map.

## SPL

```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src, dest, threat_name, severity, action | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Table (source, dest, threat, action), Bar chart by threat type, Map.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
