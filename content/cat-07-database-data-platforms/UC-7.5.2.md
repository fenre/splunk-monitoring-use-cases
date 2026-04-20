---
id: "7.5.2"
title: "Elasticsearch Shard Allocation Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.2 · Elasticsearch Shard Allocation Failures

## Description

Unassigned or stuck relocating shards leave data unavailable or at risk; allocation explain output points to disk, routing, or settings issues before outages spread.

## Value

Unassigned or stuck relocating shards leave data unavailable or at risk; allocation explain output points to disk, routing, or settings issues before outages spread.

## Implementation

Ingest `_cat/shards` with `state` filter and, for unassigned primaries, poll `POST _cluster/allocation/explain` on a schedule. Parse `allocate_explanation` and decider names. Alert when any primary shard is unassigned >5 minutes or replica unassigned count exceeds policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_cluster/allocation/explain`, `_cat/shards`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:shard_allocation`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest `_cat/shards` with `state` filter and, for unassigned primaries, poll `POST _cluster/allocation/explain` on a schedule. Parse `allocate_explanation` and decider names. Alert when any primary shard is unassigned >5 minutes or replica unassigned count exceeds policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:shard_allocation"
| where state="UNASSIGNED" OR allocation_decision="NO"
| stats latest(deciders) as deciders, count by index, shard, prirep
| sort -count
```

Understanding this SPL

**Elasticsearch Shard Allocation Failures** — Unassigned or stuck relocating shards leave data unavailable or at risk; allocation explain output points to disk, routing, or settings issues before outages spread.

Documented **Data sources**: `sourcetype=elasticsearch:shard_allocation`. **App/TA** (typical add-on context): Custom REST scripted input (`_cluster/allocation/explain`, `_cat/shards`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:shard_allocation. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:shard_allocation". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state="UNASSIGNED" OR allocation_decision="NO"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by index, shard, prirep** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (index, shard, state, reason), Single value (unassigned shard count), Timeline of allocation events.

## SPL

```spl
index=database sourcetype="elasticsearch:shard_allocation"
| where state="UNASSIGNED" OR allocation_decision="NO"
| stats latest(deciders) as deciders, count by index, shard, prirep
| sort -count
```

## Visualization

Table (index, shard, state, reason), Single value (unassigned shard count), Timeline of allocation events.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
