---
id: "7.2.3"
title: "Read/Write Latency Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.3 · Read/Write Latency Trending

## Description

Latency trending detects performance degradation before it impacts users. Enables proactive tuning and scaling decisions.

## Value

Latency trending detects performance degradation before it impacts users. Enables proactive tuning and scaling decisions.

## Implementation

Poll database metrics every 5 minutes via scripted input or API. Track read/write latency percentiles (p50, p95, p99). Baseline normal patterns and alert on sustained deviation. Correlate with workload changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom metrics input, database stats API.
• Ensure the following data sources are available: MongoDB `serverStatus()`, Cassandra JMX, Elasticsearch `_nodes/stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll database metrics every 5 minutes via scripted input or API. Track read/write latency percentiles (p50, p95, p99). Baseline normal patterns and alert on sustained deviation. Correlate with workload changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:server_status"
| timechart span=5m avg(opcounters.query) as reads, avg(opcounters.insert) as writes, avg(opLatencies.reads.latency) as read_lat
```

Understanding this SPL

**Read/Write Latency Trending** — Latency trending detects performance degradation before it impacts users. Enables proactive tuning and scaling decisions.

Documented **Data sources**: MongoDB `serverStatus()`, Cassandra JMX, Elasticsearch `_nodes/stats`. **App/TA** (typical add-on context): Custom metrics input, database stats API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:server_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:server_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency percentiles over time), Dual-axis chart (latency + throughput), Table (current latency by operation).

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
index=database sourcetype="mongodb:server_status"
| timechart span=5m avg(opcounters.query) as reads, avg(opcounters.insert) as writes, avg(opLatencies.reads.latency) as read_lat
```

## Visualization

Line chart (latency percentiles over time), Dual-axis chart (latency + throughput), Table (current latency by operation).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
