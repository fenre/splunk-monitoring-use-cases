---
id: "8.3.16"
title: "Kafka Connect Task Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.16 · Kafka Connect Task Failures

## Description

Connector `FAILED` state, task failures, and `offset_commit` errors stop data pipelines. Distinct from broker-only monitoring.

## Value

Connector `FAILED` state, task failures, and `offset_commit` errors stop data pipelines. Distinct from broker-only monitoring.

## Implementation

Poll `/connectors/*/status` every 2m. Alert on any FAILED. Include stack trace first line only for indexing size.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Connect worker logs, Connect REST `/status`.
• Ensure the following data sources are available: `kafka_connect:connector_status`, worker log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `/connectors/*/status` every 2m. Alert on any FAILED. Include stack trace first line only for indexing size.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka_connect:status"
| where connector_state="FAILED" OR task_state="FAILED"
| stats latest(trace) as err by connector, task_id
| table connector task_id connector_state task_state err
```

Understanding this SPL

**Kafka Connect Task Failures** — Connector `FAILED` state, task failures, and `offset_commit` errors stop data pipelines. Distinct from broker-only monitoring.

Documented **Data sources**: `kafka_connect:connector_status`, worker log. **App/TA** (typical add-on context): Connect worker logs, Connect REST `/status`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka_connect:status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka_connect:status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where connector_state="FAILED" OR task_state="FAILED"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by connector, task_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Kafka Connect Task Failures**): table connector task_id connector_state task_state err


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed connectors/tasks), Timeline (state changes), Single value (open failures).

## SPL

```spl
index=kafka sourcetype="kafka_connect:status"
| where connector_state="FAILED" OR task_state="FAILED"
| stats latest(trace) as err by connector, task_id
| table connector task_id connector_state task_state err
```

## Visualization

Table (failed connectors/tasks), Timeline (state changes), Single value (open failures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
