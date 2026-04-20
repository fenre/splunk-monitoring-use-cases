---
id: "8.3.12"
title: "ZooKeeper Ensemble Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.12 · ZooKeeper Ensemble Health

## Description

Leader election state, outstanding requests, and watch count indicate ZooKeeper stability. Frequent leader changes or growing outstanding requests signal ensemble instability affecting Kafka, HBase, and other dependents.

## Value

Leader election state, outstanding requests, and watch count indicate ZooKeeper stability. Frequent leader changes or growing outstanding requests signal ensemble instability affecting Kafka, HBase, and other dependents.

## Implementation

Enable ZooKeeper AdminServer or use 4-letter commands (`echo mntr | nc localhost 2181`). Poll mntr output every minute via scripted input. Parse mode (leader/follower/standalone), outstanding_requests, num_alive_connections, watch_count, zk_approximate_data_size. Forward to Splunk via HEC. Alert when outstanding_requests exceeds 100 or num_alive_connections drops (ensemble partition). Track leader changes via mode transitions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (ZooKeeper 4-letter commands or AdminServer).
• Ensure the following data sources are available: mntr command output, ZooKeeper AdminServer `/commands/monitor`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ZooKeeper AdminServer or use 4-letter commands (`echo mntr | nc localhost 2181`). Poll mntr output every minute via scripted input. Parse mode (leader/follower/standalone), outstanding_requests, num_alive_connections, watch_count, zk_approximate_data_size. Forward to Splunk via HEC. Alert when outstanding_requests exceeds 100 or num_alive_connections drops (ensemble partition). Track leader changes via mode transitions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=zookeeper sourcetype="zookeeper:mntr"
| where outstanding_requests > 100 OR (mode!="standalone" AND num_alive_connections < 2)
| timechart span=5m max(outstanding_requests) as outstanding by host
```

Understanding this SPL

**ZooKeeper Ensemble Health** — Leader election state, outstanding requests, and watch count indicate ZooKeeper stability. Frequent leader changes or growing outstanding requests signal ensemble instability affecting Kafka, HBase, and other dependents.

Documented **Data sources**: mntr command output, ZooKeeper AdminServer `/commands/monitor`. **App/TA** (typical add-on context): Custom scripted input (ZooKeeper 4-letter commands or AdminServer). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: zookeeper; **sourcetype**: zookeeper:mntr. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=zookeeper, sourcetype="zookeeper:mntr". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where outstanding_requests > 100 OR (mode!="standalone" AND num_alive_connections < 2)` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (node × mode), Line chart (outstanding requests over time), Single value (leader node), Table (ensemble health summary).

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
index=zookeeper sourcetype="zookeeper:mntr"
| where outstanding_requests > 100 OR (mode!="standalone" AND num_alive_connections < 2)
| timechart span=5m max(outstanding_requests) as outstanding by host
```

## Visualization

Status grid (node × mode), Line chart (outstanding requests over time), Single value (leader node), Table (ensemble health summary).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
