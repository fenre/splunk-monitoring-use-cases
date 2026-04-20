---
id: "6.1.12"
title: "Isilon Capacity and Performance Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.12 · Isilon Capacity and Performance Trending

## Description

Tracks Isilon cluster capacity and throughput (e.g. ops/sec, throughput MB/s) for capacity planning and performance troubleshooting. Matches IT Essentials Learn procedures for Isilon storage.

## Value

Tracks Isilon cluster capacity and throughput (e.g. ops/sec, throughput MB/s) for capacity planning and performance troubleshooting. Matches IT Essentials Learn procedures for Isilon storage.

## Implementation

Poll OneFS stats API or use Isilon TA to collect capacity and performance metrics. Set alerts for pool capacity >85% and for sustained high latency or drop in throughput.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OneFS API or vendor add-on for Isilon metrics.
• Ensure the following data sources are available: OneFS statistics (capacity by pool/node, read/write ops, network throughput).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll OneFS stats API or use Isilon TA to collect capacity and performance metrics. Set alerts for pool capacity >85% and for sustained high latency or drop in throughput.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype=isilon:metrics
| timechart span=1h avg(capacity_used_pct) as pct_used, avg(ops_per_sec) as iops by node
| where pct_used > 80
```

Understanding this SPL

**Isilon Capacity and Performance Trending** — Tracks Isilon cluster capacity and throughput (e.g. ops/sec, throughput MB/s) for capacity planning and performance troubleshooting. Matches IT Essentials Learn procedures for Isilon storage.

Documented **Data sources**: OneFS statistics (capacity by pool/node, read/write ops, network throughput). **App/TA** (typical add-on context): OneFS API or vendor add-on for Isilon metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: isilon:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype=isilon:metrics. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by node** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pct_used > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (capacity and IOPS over time by node/pool), Single value (cluster used %), Table (top consumers).

## SPL

```spl
index=storage sourcetype=isilon:metrics
| timechart span=1h avg(capacity_used_pct) as pct_used, avg(ops_per_sec) as iops by node
| where pct_used > 80
```

## Visualization

Line chart (capacity and IOPS over time by node/pool), Single value (cluster used %), Table (top consumers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
