<!-- AUTO-GENERATED from UC-5.2.21.json — DO NOT EDIT -->

---
id: "5.2.21"
title: "IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.21 · IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)

## Description

Identifies and prioritizes intrusion detection alerts for investigation and threat response.

## Value

Identifies and prioritizes intrusion detection alerts for investigation and threat response.

## Implementation

Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=ids_alert`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src, dest
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
```

Understanding this SPL

**IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)** — Identifies and prioritizes intrusion detection alerts for investigation and threat response.

Documented **Data sources**: `sourcetype=meraki type=ids_alert`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by signature, priority, src, dest** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where priority <= 2` — typically the threshold or rule expression for this monitoring goal.
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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert timeline; severity breakdown pie chart; alert detail table; threat map.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src, dest
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
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

Alert timeline; severity breakdown pie chart; alert detail table; threat map.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
