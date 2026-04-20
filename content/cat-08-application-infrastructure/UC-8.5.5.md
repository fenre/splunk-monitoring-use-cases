---
id: "8.5.5"
title: "Replication Lag (Redis)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.5 · Replication Lag (Redis)

## Description

Redis replication lag affects read consistency for apps reading from replicas. Monitoring ensures data freshness.

## Value

Redis replication lag affects read consistency for apps reading from replicas. Monitoring ensures data freshness.

## Implementation

Poll Redis INFO replication from replicas every minute. Calculate byte offset lag. Alert when lag exceeds threshold (e.g., >1MB or growing). Monitor replication link status (master_link_status).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: Redis INFO replication (`master_repl_offset`, `slave_repl_offset`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Redis INFO replication from replicas every minute. Calculate byte offset lag. Alert when lag exceeds threshold (e.g., >1MB or growing). Monitor replication link status (master_link_status).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info" role="slave"
| eval lag_bytes=master_repl_offset-slave_repl_offset
| timechart span=1m max(lag_bytes) as repl_lag by host
| where repl_lag > 1000000
```

Understanding this SPL

**Replication Lag (Redis)** — Redis replication lag affects read consistency for apps reading from replicas. Monitoring ensures data freshness.

Documented **Data sources**: Redis INFO replication (`master_repl_offset`, `slave_repl_offset`). **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where repl_lag > 1000000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replication lag over time), Single value (current lag), Table (replica status).

## SPL

```spl
index=cache sourcetype="redis:info" role="slave"
| eval lag_bytes=master_repl_offset-slave_repl_offset
| timechart span=1m max(lag_bytes) as repl_lag by host
| where repl_lag > 1000000
```

## Visualization

Line chart (replication lag over time), Single value (current lag), Table (replica status).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
