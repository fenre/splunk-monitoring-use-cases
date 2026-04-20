---
id: "3.4.6"
title: "Registry Replication Lag and Consistency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.4.6 · Registry Replication Lag and Consistency

## Description

Replication lag between registry replicas can cause inconsistent image availability and failed pulls. Monitoring supports HA and DR assurance.

## Value

Replication lag between registry replicas can cause inconsistent image availability and failed pulls. Monitoring supports HA and DR assurance.

## Implementation

Poll replication status from registry (e.g. Harbor replication jobs). Ingest lag and status. Alert when lag exceeds 5 minutes or status is failed.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (registry replication status).
• Ensure the following data sources are available: Registry replication API or admin metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll replication status from registry (e.g. Harbor replication jobs). Ingest lag and status. Alert when lag exceeds 5 minutes or status is failed.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:replication"
| stats latest(lag_seconds) as lag, latest(status) as status by source_registry, target_registry
| where lag > 300 OR status != "success"
| table source_registry target_registry lag status _time
```

Understanding this SPL

**Registry Replication Lag and Consistency** — Replication lag between registry replicas can cause inconsistent image availability and failed pulls. Monitoring supports HA and DR assurance.

Documented **Data sources**: Registry replication API or admin metrics. **App/TA** (typical add-on context): Custom API input (registry replication status). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:replication. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:replication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by source_registry, target_registry** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where lag > 300 OR status != "success"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Registry Replication Lag and Consistency**): table source_registry target_registry lag status _time


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (lag over time), Table (source, target, lag, status), Single value (max lag).

## SPL

```spl
index=containers sourcetype="registry:replication"
| stats latest(lag_seconds) as lag, latest(status) as status by source_registry, target_registry
| where lag > 300 OR status != "success"
| table source_registry target_registry lag status _time
```

## Visualization

Line chart (lag over time), Table (source, target, lag, status), Single value (max lag).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
