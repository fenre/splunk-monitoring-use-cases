<!-- AUTO-GENERATED from UC-8.3.8.json — DO NOT EDIT -->

---
id: "8.3.8"
title: "Consumer Group Rebalancing"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.8 · Consumer Group Rebalancing

## Description

Frequent rebalances cause processing pauses and duplicate message delivery. Detection identifies unstable consumers.

## Value

Frequent rebalances cause processing pauses and duplicate message delivery. Detection identifies unstable consumers.

## Implementation

Parse Kafka broker logs for rebalance events. Track rebalance frequency per consumer group. Alert when rebalances occur more than 5 times per hour. Correlate with consumer heartbeat timeouts and session timeouts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kafka broker logs, JMX.
• Ensure the following data sources are available: Kafka GroupCoordinator logs, consumer group state.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse Kafka broker logs for rebalance events. Track rebalance frequency per consumer group. Alert when rebalances occur more than 5 times per hour. Correlate with consumer heartbeat timeouts and session timeouts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:server"
| search "Preparing to rebalance group" OR "Stabilized group"
| rex "group (?<consumer_group>\S+)"
| stats count by consumer_group
| where count > 5
```

Understanding this SPL

**Consumer Group Rebalancing** — Frequent rebalances cause processing pauses and duplicate message delivery. Detection identifies unstable consumers.

Documented **Data sources**: Kafka GroupCoordinator logs, consumer group state. **App/TA** (typical add-on context): Kafka broker logs, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:server. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:server". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by consumer_group** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (rebalances per consumer group), Timeline (rebalance events), Line chart (rebalance frequency trend).

## SPL

```spl
index=kafka sourcetype="kafka:server"
| search "Preparing to rebalance group" OR "Stabilized group"
| rex "group (?<consumer_group>\S+)"
| stats count by consumer_group
| where count > 5
```

## Visualization

Bar chart (rebalances per consumer group), Timeline (rebalance events), Line chart (rebalance frequency trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
