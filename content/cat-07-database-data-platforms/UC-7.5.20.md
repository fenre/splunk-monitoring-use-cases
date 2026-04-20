---
id: "7.5.20"
title: "Solr Core Admin Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.20 · Solr Core Admin Health

## Description

Core-level errors (recovery failures, corrupt index flags, leader election issues) degrade search for specific collections; admin health checks catch per-core problems early.

## Value

Core-level errors (recovery failures, corrupt index flags, leader election issues) degrade search for specific collections; admin health checks catch per-core problems early.

## Implementation

Poll `STATUS` for all cores on a schedule; capture `instanceDir`, `dataDir`, `uptime`, replication/Cloud role fields. Ingest ERROR lines from `solr.log`. Alert when core state is not active, recovery fails, or leader/replica roles mismatch expectations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`/admin/cores?action=STATUS`), Solr logs.
• Ensure the following data sources are available: `sourcetype=solr:core_status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `STATUS` for all cores on a schedule; capture `instanceDir`, `dataDir`, `uptime`, replication/Cloud role fields. Ingest ERROR lines from `solr.log`. Alert when core state is not active, recovery fails, or leader/replica roles mismatch expectations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="solr:core_status"
| where state!="active" OR isnotnull(error_msg)
| stats latest(state) as state, latest(index_version) as index_version by core, collection, node_name
| sort state
```

Understanding this SPL

**Solr Core Admin Health** — Core-level errors (recovery failures, corrupt index flags, leader election issues) degrade search for specific collections; admin health checks catch per-core problems early.

Documented **Data sources**: `sourcetype=solr:core_status`. **App/TA** (typical add-on context): Custom scripted input (`/admin/cores?action=STATUS`), Solr logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: solr:core_status. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="solr:core_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state!="active" OR isnotnull(error_msg)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by core, collection, node_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (core × healthy), Table (cores with errors), Single value (unhealthy core count).

## SPL

```spl
index=database sourcetype="solr:core_status"
| where state!="active" OR isnotnull(error_msg)
| stats latest(state) as state, latest(index_version) as index_version by core, collection, node_name
| sort state
```

## Visualization

Status grid (core × healthy), Table (cores with errors), Single value (unhealthy core count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
