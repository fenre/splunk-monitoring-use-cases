---
id: "7.2.1"
title: "Cluster Membership Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.1 · Cluster Membership Changes

## Description

Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

## Value

Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

## Implementation

Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, database event logs.
• Ensure the following data sources are available: MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```

Understanding this SPL

**Cluster Membership Changes** — Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

Documented **Data sources**: MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state. **App/TA** (typical add-on context): Custom scripted input, database event logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Cluster Membership Changes**): table _time, host, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (membership events), Single value (current node count), Table (recent cluster changes).

## SPL

```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```

## Visualization

Timeline (membership events), Single value (current node count), Table (recent cluster changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
