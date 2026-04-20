---
id: "7.5.15"
title: "Elasticsearch Snapshot Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.15 · Elasticsearch Snapshot Failures

## Description

Failed snapshots mean no viable backup for disaster recovery. Partial snapshots may leave indices unrecoverable. Monitoring ensures RPO commitments are met.

## Value

Failed snapshots mean no viable backup for disaster recovery. Partial snapshots may leave indices unrecoverable. Monitoring ensures RPO commitments are met.

## Implementation

Poll `GET _snapshot/_all/_all` or `GET _snapshot/<repo>/_current` to track snapshot state. Alert on any snapshot with state FAILED or PARTIAL. Also monitor time since last successful snapshot — alert when it exceeds RPO threshold (e.g., 24 hours). Check `_snapshot/<repo>/_status` for in-progress snapshot progress.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_snapshot`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:snapshot_status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _snapshot/_all/_all` or `GET _snapshot/<repo>/_current` to track snapshot state. Alert on any snapshot with state FAILED or PARTIAL. Also monitor time since last successful snapshot — alert when it exceeds RPO threshold (e.g., 24 hours). Check `_snapshot/<repo>/_status` for in-progress snapshot progress.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:snapshot_status"
| where state IN ("FAILED","PARTIAL","INCOMPATIBLE")
| stats count by snapshot, repository, state, reason
| sort -count
```

Understanding this SPL

**Elasticsearch Snapshot Failures** — Failed snapshots mean no viable backup for disaster recovery. Partial snapshots may leave indices unrecoverable. Monitoring ensures RPO commitments are met.

Documented **Data sources**: `sourcetype=elasticsearch:snapshot_status`. **App/TA** (typical add-on context): Custom REST scripted input (`_snapshot`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:snapshot_status. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:snapshot_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state IN ("FAILED","PARTIAL","INCOMPATIBLE")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by snapshot, repository, state, reason** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (recent snapshots with state), Single value (hours since last successful), Line chart (snapshot duration trend).

## SPL

```spl
index=database sourcetype="elasticsearch:snapshot_status"
| where state IN ("FAILED","PARTIAL","INCOMPATIBLE")
| stats count by snapshot, repository, state, reason
| sort -count
```

## Visualization

Table (recent snapshots with state), Single value (hours since last successful), Line chart (snapshot duration trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
