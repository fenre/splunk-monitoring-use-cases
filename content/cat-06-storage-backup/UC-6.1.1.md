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
• `stats` rolls up events into metrics; results are split **by volume_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where pct_used > 85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).

## SPL

```spl
index=storage sourcetype="netapp:ontap:volume"
| stats latest(size_used_percent) as pct_used by volume_name
| where pct_used > 85
| sort -pct_used
```

## Visualization

Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).

## Known False Positives

Temporary spikes during snapshots or replication; use rolling average or exclude known maintenance windows.

## References

- [Splunk Add-on for NetApp](https://splunkbase.splunk.com/app/1664)
