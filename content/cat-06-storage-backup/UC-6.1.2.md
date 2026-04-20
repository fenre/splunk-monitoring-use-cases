---
id: "6.1.2"
title: "Storage Latency Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.1.2 · Storage Latency Monitoring

## Description

High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.

## Value

High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.

## Implementation

Poll latency metrics via REST or SNMP every 5 minutes. Set tiered alerts: warning >10ms, critical >20ms for production volumes. Correlate with IOPS spikes to distinguish overload from hardware issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA or SNMP polling.
• Ensure the following data sources are available: Array performance metrics (avg_latency, read_latency, write_latency).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll latency metrics via REST or SNMP every 5 minutes. Set tiered alerts: warning >10ms, critical >20ms for production volumes. Correlate with IOPS spikes to distinguish overload from hardware issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| stats avg(avg_latency) as latency_ms by volume_name
| where latency_ms > 20
| sort -latency_ms
```

Understanding this SPL

**Storage Latency Monitoring** — High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.

Documented **Data sources**: Array performance metrics (avg_latency, read_latency, write_latency). **App/TA** (typical add-on context): Vendor TA or SNMP polling. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:volume_perf. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:volume_perf". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by volume_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where latency_ms > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency over time by volume), Heatmap (volume × time), Single value (current avg latency).

## SPL

```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| stats avg(avg_latency) as latency_ms by volume_name
| where latency_ms > 20
| sort -latency_ms
```

## Visualization

Line chart (latency over time by volume), Heatmap (volume × time), Single value (current avg latency).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
