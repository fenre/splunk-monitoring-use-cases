<!-- AUTO-GENERATED from UC-8.3.3.json — DO NOT EDIT -->

---
id: "8.3.3"
title: "Broker Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.3 · Broker Health Monitoring

## Description

Broker failures cause message loss and application disruption. Health monitoring ensures cluster stability.

## Value

Broker failures cause message loss and application disruption. Health monitoring ensures cluster stability.

## Implementation

Poll broker health metrics via JMX every minute. Track disk usage, CPU, memory, network I/O. Alert on broker offline, under-replicated partitions, or controller election. Monitor ISR (In-Sync Replica) shrink rate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, broker metrics.
• Ensure the following data sources are available: Kafka JMX (broker metrics), RabbitMQ management API (`/api/nodes`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll broker health metrics via JMX every minute. Track disk usage, CPU, memory, network I/O. Alert on broker offline, under-replicated partitions, or controller election. Monitor ISR (In-Sync Replica) shrink rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:broker"
| stats latest(UnderReplicatedPartitions) as under_replicated, latest(ActiveControllerCount) as controllers by broker_id
| eventstats sum(controllers) as cluster_controllers
| where under_replicated > 0 OR cluster_controllers != 1
```

Understanding this SPL

**Broker Health Monitoring** — Broker failures cause message loss and application disruption. Health monitoring ensures cluster stability.

Documented **Data sources**: Kafka JMX (broker metrics), RabbitMQ management API (`/api/nodes`). **App/TA** (typical add-on context): JMX, broker metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:broker. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:broker". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by broker_id** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where under_replicated > 0 OR cluster_controllers != 1` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (broker × health), Single value (under-replicated partitions), Table (broker metrics), Line chart (broker resource usage).

## SPL

```spl
index=kafka sourcetype="kafka:broker"
| stats latest(UnderReplicatedPartitions) as under_replicated, latest(ActiveControllerCount) as controllers by broker_id
| eventstats sum(controllers) as cluster_controllers
| where under_replicated > 0 OR cluster_controllers != 1
```

## Visualization

Status grid (broker × health), Single value (under-replicated partitions), Table (broker metrics), Line chart (broker resource usage).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
