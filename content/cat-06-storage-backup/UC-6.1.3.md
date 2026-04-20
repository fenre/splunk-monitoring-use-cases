---
id: "6.1.3"
title: "IOPS Trending per Volume"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.3 · IOPS Trending per Volume

## Description

Identifies workload hotspots and enables data placement optimization. Supports capacity planning for storage refreshes.

## Value

Identifies workload hotspots and enables data placement optimization. Supports capacity planning for storage refreshes.

## Implementation

Collect IOPS metrics per volume/LUN at 5-15 min intervals. Baseline normal patterns and alert on deviations exceeding 2× baseline. Correlate with application deployment events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA or SNMP.
• Ensure the following data sources are available: Array performance metrics (read_ops, write_ops, other_ops).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect IOPS metrics per volume/LUN at 5-15 min intervals. Baseline normal patterns and alert on deviations exceeding 2× baseline. Correlate with application deployment events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=15m sum(total_ops) as iops by volume_name
| sort -iops
```

Understanding this SPL

**IOPS Trending per Volume** — Identifies workload hotspots and enables data placement optimization. Supports capacity planning for storage refreshes.

Documented **Data sources**: Array performance metrics (read_ops, write_ops, other_ops). **App/TA** (typical add-on context): Vendor TA or SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:volume_perf. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:volume_perf". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by volume_name** — ideal for trending and alerting on this use case.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (IOPS trend by volume), Stacked bar (read vs write IOPS), Table (top IOPS consumers).

## SPL

```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=15m sum(total_ops) as iops by volume_name
| sort -iops
```

## Visualization

Line chart (IOPS trend by volume), Stacked bar (read vs write IOPS), Table (top IOPS consumers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
