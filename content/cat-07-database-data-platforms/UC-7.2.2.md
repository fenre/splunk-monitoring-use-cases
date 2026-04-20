---
id: "7.2.2"
title: "Replication Lag / Consistency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.2 · Replication Lag / Consistency

## Description

Replication lag causes stale reads and eventual consistency violations. Monitoring ensures data freshness SLAs are met.

## Value

Replication lag causes stale reads and eventual consistency violations. Monitoring ensures data freshness SLAs are met.

## Implementation

Run scripted input polling replica set status every minute. Parse member states and optime differences. Alert when lag exceeds threshold (e.g., >10 seconds). Track trend for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (rs.status(), nodetool).
• Ensure the following data sources are available: MongoDB `rs.status()`, Cassandra `nodetool status`, Redis `INFO replication`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run scripted input polling replica set status every minute. Parse member states and optime differences. Alert when lag exceeds threshold (e.g., >10 seconds). Track trend for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:rs_status"
| eval lag_sec=optime_primary-optime_secondary
| where lag_sec > 10
| table _time, replica_set, member, state, lag_sec
```

Understanding this SPL

**Replication Lag / Consistency** — Replication lag causes stale reads and eventual consistency violations. Monitoring ensures data freshness SLAs are met.

Documented **Data sources**: MongoDB `rs.status()`, Cassandra `nodetool status`, Redis `INFO replication`. **App/TA** (typical add-on context): Custom scripted input (rs.status(), nodetool). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:rs_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:rs_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where lag_sec > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Replication Lag / Consistency**): table _time, replica_set, member, state, lag_sec


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replication lag over time), Table (replicas with lag), Single value (max current lag).

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
index=database sourcetype="mongodb:rs_status"
| eval lag_sec=optime_primary-optime_secondary
| where lag_sec > 10
| table _time, replica_set, member, state, lag_sec
```

## Visualization

Line chart (replication lag over time), Table (replicas with lag), Single value (max current lag).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
