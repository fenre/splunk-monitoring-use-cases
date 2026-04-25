<!-- AUTO-GENERATED from UC-5.2.22.json — DO NOT EDIT -->

---
id: "5.2.22"
title: "Malware Detection and AMP File Reputation Events (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.22 · Malware Detection and AMP File Reputation Events (Meraki MX)

## Description

Detects and tracks file-based threats to respond quickly to potential malware infections.

## Value

Detects and tracks file-based threats to respond quickly to potential malware infections.

## Implementation

Enable AMP on MX appliance. Ingest malware detection events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*malware*" OR signature="*AMP*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AMP on MX appliance. Ingest malware detection events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src, threat_name, file_name
| where malware_count > 0
| sort - malware_count
```

Understanding this SPL

**Malware Detection and AMP File Reputation Events (Meraki MX)** — Detects and tracks file-based threats to respond quickly to potential malware infections.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*malware*" OR signature="*AMP*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, threat_name, file_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where malware_count > 0` — typically the threshold or rule expression for this monitoring goal.
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
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Threat timeline; infected hosts table; file reputation detail; incident dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src, threat_name, file_name
| where malware_count > 0
| sort - malware_count
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

Threat timeline; infected hosts table; file reputation detail; incident dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
