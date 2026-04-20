---
id: "7.2.22"
title: "CouchDB View Build Times"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.2.22 · CouchDB View Build Times

## Description

Long-running view index builds block compaction and increase disk I/O. Tracks `_active_tasks` indexer progress and failures.

## Value

Long-running view index builds block compaction and increase disk I/O. Tracks `_active_tasks` indexer progress and failures.

## Implementation

Poll `_active_tasks` every minute. Alert when indexer runs >1h with low progress or task errors. Correlate with data volume growth.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CouchDB `_active_tasks`, log ingestion.
• Ensure the following data sources are available: Indexer task type, `progress`, `total_changes`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `_active_tasks` every minute. Alert when indexer runs >1h with low progress or task errors. Correlate with data volume growth.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="couchdb:active_tasks" type=indexer
| eval pct=round(progress/total_changes*100,1)
| where pct < 100 AND updated_in_sec > 3600
| table database_name design_doc pct updated_in_sec
```

Understanding this SPL

**CouchDB View Build Times** — Long-running view index builds block compaction and increase disk I/O. Tracks `_active_tasks` indexer progress and failures.

Documented **Data sources**: Indexer task type, `progress`, `total_changes`. **App/TA** (typical add-on context): CouchDB `_active_tasks`, log ingestion. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: couchdb:active_tasks. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="couchdb:active_tasks". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct < 100 AND updated_in_sec > 3600` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **CouchDB View Build Times**): table database_name design_doc pct updated_in_sec


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (design doc, % complete), Line chart (indexer duration), Single value (stuck indexers).

## SPL

```spl
index=database sourcetype="couchdb:active_tasks" type=indexer
| eval pct=round(progress/total_changes*100,1)
| where pct < 100 AND updated_in_sec > 3600
| table database_name design_doc pct updated_in_sec
```

## Visualization

Table (design doc, % complete), Line chart (indexer duration), Single value (stuck indexers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
