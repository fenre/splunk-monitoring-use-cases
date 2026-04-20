---
id: "7.2.17"
title: "CouchDB Replication Conflicts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.17 · CouchDB Replication Conflicts

## Description

Growing `_conflicts` document count indicates divergent replicas and data quality issues. Early detection prevents silent wrong reads.

## Value

Growing `_conflicts` document count indicates divergent replicas and data quality issues. Early detection prevents silent wrong reads.

## Implementation

Ingest replication task status from `_active_tasks` and periodic conflict counts from a map view. Alert on replication errors or conflict_count increase week-over-week.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CouchDB `_stats`, `_active_tasks` API.
• Ensure the following data sources are available: Replication task errors, document conflict counts (custom view or `_changes` sampling).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest replication task status from `_active_tasks` and periodic conflict counts from a map view. Alert on replication errors or conflict_count increase week-over-week.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="couchdb:replication"
| where conflict_count > 0 OR error IS NOT NULL
| stats sum(conflict_count) as conflicts, latest(error) as err by database_name, source, target
| sort -conflicts
```

Understanding this SPL

**CouchDB Replication Conflicts** — Growing `_conflicts` document count indicates divergent replicas and data quality issues. Early detection prevents silent wrong reads.

Documented **Data sources**: Replication task errors, document conflict counts (custom view or `_changes` sampling). **App/TA** (typical add-on context): CouchDB `_stats`, `_active_tasks` API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: couchdb:replication. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="couchdb:replication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where conflict_count > 0 OR error IS NOT NULL` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by database_name, source, target** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DB, conflicts, error), Line chart (conflict trend), Single value (total conflicts).

## SPL

```spl
index=database sourcetype="couchdb:replication"
| where conflict_count > 0 OR error IS NOT NULL
| stats sum(conflict_count) as conflicts, latest(error) as err by database_name, source, target
| sort -conflicts
```

## Visualization

Table (DB, conflicts, error), Line chart (conflict trend), Single value (total conflicts).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
