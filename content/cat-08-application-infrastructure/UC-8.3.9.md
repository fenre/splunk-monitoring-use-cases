---
id: "8.3.9"
title: "Partition Leader Elections"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.9 · Partition Leader Elections

## Description

Frequent leader elections indicate broker instability, causing temporary unavailability for affected partitions.

## Value

Frequent leader elections indicate broker instability, causing temporary unavailability for affected partitions.

## Implementation

Monitor Kafka controller logs and JMX metrics. Track leader election rate and duration. Alert on elevated election rates. Correlate with broker restarts, network events, and ZooKeeper/KRaft issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, Kafka controller logs.
• Ensure the following data sources are available: Kafka JMX (`LeaderElectionRateAndTimeMs`), controller logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Kafka controller logs and JMX metrics. Track leader election rate and duration. Alert on elevated election rates. Correlate with broker restarts, network events, and ZooKeeper/KRaft issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:controller"
| search "leader" "election"
| timechart span=15m count as elections
| where elections > 10
```

Understanding this SPL

**Partition Leader Elections** — Frequent leader elections indicate broker instability, causing temporary unavailability for affected partitions.

Documented **Data sources**: Kafka JMX (`LeaderElectionRateAndTimeMs`), controller logs. **App/TA** (typical add-on context): JMX, Kafka controller logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:controller. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:controller". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `timechart` plots the metric over time using **span=15m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where elections > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (elections over time), Single value (elections per hour), Table (affected topics/partitions).

## SPL

```spl
index=kafka sourcetype="kafka:controller"
| search "leader" "election"
| timechart span=15m count as elections
| where elections > 10
```

## Visualization

Line chart (elections over time), Single value (elections per hour), Table (affected topics/partitions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
