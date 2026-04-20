---
id: "7.2.19"
title: "Cassandra Tombstone Accumulation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.19 · Cassandra Tombstone Accumulation

## Description

High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

## Value

High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

## Implementation

Poll tablestats weekly or daily per large tables. Alert on droppable tombstones above baseline. Correlate with TTL/schema design reviews.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, `nodetool tablestats`.
• Ensure the following data sources are available: `Estimated droppable tombstones`, read path tombstone thresholds.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll tablestats weekly or daily per large tables. Alert on droppable tombstones above baseline. Correlate with TTL/schema design reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="cassandra:tablestats"
| where droppable_tombstones > 100000 OR live_sstable_count > 50
| stats latest(droppable_tombstones) as tombstones by keyspace, table, host
| sort -tombstones
```

Understanding this SPL

**Cassandra Tombstone Accumulation** — High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

Documented **Data sources**: `Estimated droppable tombstones`, read path tombstone thresholds. **App/TA** (typical add-on context): JMX, `nodetool tablestats`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: cassandra:tablestats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="cassandra:tablestats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where droppable_tombstones > 100000 OR live_sstable_count > 50` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by keyspace, table, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (KS, table, tombstones), Bar chart (top tables), Line chart (tombstone trend).

## SPL

```spl
index=database sourcetype="cassandra:tablestats"
| where droppable_tombstones > 100000 OR live_sstable_count > 50
| stats latest(droppable_tombstones) as tombstones by keyspace, table, host
| sort -tombstones
```

## Visualization

Table (KS, table, tombstones), Bar chart (top tables), Line chart (tombstone trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
