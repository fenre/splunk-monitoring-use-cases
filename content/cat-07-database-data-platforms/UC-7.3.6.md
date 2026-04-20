---
id: "7.3.6"
title: "Redis Memory Fragmentation Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.6 · Redis Memory Fragmentation Ratio

## Description

Fragmentation ratio > 1.5 indicating memory inefficiency. High fragmentation wastes RAM and can trigger OOM or evictions under memory pressure.

## Value

Fragmentation ratio > 1.5 indicating memory inefficiency. High fragmentation wastes RAM and can trigger OOM or evictions under memory pressure.

## Implementation

Create scripted input running `redis-cli INFO memory` every 15 minutes. Parse `mem_fragmentation_ratio` (used_memory_rss/used_memory). Alert when ratio exceeds 1.5. Track `used_memory_rss` and `used_memory` for trend analysis. Consider `MEMORY PURGE` (Redis 4+) or restart for severe fragmentation. Correlate with eviction rate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (redis-cli INFO memory).
• Ensure the following data sources are available: redis-cli INFO memory (mem_fragmentation_ratio).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input running `redis-cli INFO memory` every 15 minutes. Parse `mem_fragmentation_ratio` (used_memory_rss/used_memory). Alert when ratio exceeds 1.5. Track `used_memory_rss` and `used_memory` for trend analysis. Consider `MEMORY PURGE` (Redis 4+) or restart for severe fragmentation. Correlate with eviction rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="redis:info"
| where mem_fragmentation_ratio > 1.5
| timechart span=15m avg(mem_fragmentation_ratio) as frag_ratio by host
| where frag_ratio > 1.5
```

Understanding this SPL

**Redis Memory Fragmentation Ratio** — Fragmentation ratio > 1.5 indicating memory inefficiency. High fragmentation wastes RAM and can trigger OOM or evictions under memory pressure.

Documented **Data sources**: redis-cli INFO memory (mem_fragmentation_ratio). **App/TA** (typical add-on context): Custom scripted input (redis-cli INFO memory). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where mem_fragmentation_ratio > 1.5` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where frag_ratio > 1.5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (fragmentation ratio over time), Gauge (current ratio), Table (hosts with high fragmentation).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=database sourcetype="redis:info"
| where mem_fragmentation_ratio > 1.5
| timechart span=15m avg(mem_fragmentation_ratio) as frag_ratio by host
| where frag_ratio > 1.5
```

## Visualization

Line chart (fragmentation ratio over time), Gauge (current ratio), Table (hosts with high fragmentation).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
