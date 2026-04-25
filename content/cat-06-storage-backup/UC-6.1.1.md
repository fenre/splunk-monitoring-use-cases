<!-- AUTO-GENERATED from UC-6.1.1.json — DO NOT EDIT -->

---
id: "6.1.1"
title: "Volume Capacity Trending"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.1 · Volume Capacity Trending

## Description

Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.

## Value

Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.

## Implementation

Deploy vendor TA on a heavy forwarder. Configure REST API polling (every 15 min) for volume metrics. Create alert for >85% and >95% thresholds. Build capacity forecast using `predict` command.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA (e.g., `TA-netapp_ontap`) or scripted API input.
• Ensure the following data sources are available: Storage array REST API metrics, SNMP hrStorageTable.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy vendor TA on a heavy forwarder. Configure REST API polling (every 15 min) for volume metrics. Create alert for >85% and >95% thresholds. Build capacity forecast using `predict` command.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:volume"
| stats latest(size_used_percent) as pct_used by volume_name
| where pct_used > 85
| sort -pct_used
```

Understanding this SPL

**Volume Capacity Trending** — Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.

Documented **Data sources**: Storage array REST API metrics, SNMP hrStorageTable. **App/TA** (typical add-on context): Vendor TA (e.g., `TA-netapp_ontap`) or scripted API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:volume. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:volume". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by volume_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where pct_used > 85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare per-volume used space and thresholds with NetApp ONTAP System Manager, the ONTAP CLI, or NetApp Active IQ Unified Manager for the same SVM, volume, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).

## SPL

```spl
index=storage sourcetype="netapp:ontap:volume"
| stats latest(size_used_percent) as pct_used by volume_name
| where pct_used > 85
| sort -pct_used
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).

## References

- [Splunk Add-on for NetApp](https://splunkbase.splunk.com/app/1664)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
