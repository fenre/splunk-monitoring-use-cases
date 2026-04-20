---
id: "7.2.5"
title: "Compaction Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.2.5 · Compaction Monitoring

## Description

Pending compactions consume I/O and can cause write amplification. Monitoring ensures compaction keeps pace with writes.

## Value

Pending compactions consume I/O and can cause write amplification. Monitoring ensures compaction keeps pace with writes.

## Implementation

Poll compaction stats via JMX (Cassandra) or scripted input. Track pending compaction tasks and throughput. Alert when pending tasks grow consistently, indicating compaction cannot keep up with write volume.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX input (Cassandra), database logs.
• Ensure the following data sources are available: Cassandra `nodetool compactionstats`, MongoDB WiredTiger stats, Elasticsearch merge stats.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll compaction stats via JMX (Cassandra) or scripted input. Track pending compaction tasks and throughput. Alert when pending tasks grow consistently, indicating compaction cannot keep up with write volume.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="cassandra:compaction"
| timechart span=15m avg(pending_tasks) as pending, sum(bytes_compacted) as compacted
| where pending > 50
```

Understanding this SPL

**Compaction Monitoring** — Pending compactions consume I/O and can cause write amplification. Monitoring ensures compaction keeps pace with writes.

Documented **Data sources**: Cassandra `nodetool compactionstats`, MongoDB WiredTiger stats, Elasticsearch merge stats. **App/TA** (typical add-on context): JMX input (Cassandra), database logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: cassandra:compaction. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="cassandra:compaction". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where pending > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (pending compactions over time), Dual-axis (pending + throughput), Single value (current pending).

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
index=database sourcetype="cassandra:compaction"
| timechart span=15m avg(pending_tasks) as pending, sum(bytes_compacted) as compacted
| where pending > 50
```

## Visualization

Line chart (pending compactions over time), Dual-axis (pending + throughput), Single value (current pending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
