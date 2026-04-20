---
id: "8.3.19"
title: "ActiveMQ Broker Store Usage"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.19 · ActiveMQ Broker Store Usage

## Description

Persistent store percent used (KahaDB) or JDBC store growth causes broker pause and producer blocking. JMX `StoreLimit` usage.

## Value

Persistent store percent used (KahaDB) or JDBC store growth causes broker pause and producer blocking. JMX `StoreLimit` usage.

## Implementation

Poll JMX every 5m. Alert at 80% store. Schedule garbage collection or archive old messages per policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: ActiveMQ JMX, `activemq` log.
• Ensure the following data sources are available: `org.apache.activemq:type=Broker` `StoreLimit`, `TempLimit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll JMX every 5m. Alert at 80% store. Schedule garbage collection or archive old messages per policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="activemq:broker"
| eval store_pct=round(store_used/store_limit*100,1)
| where store_pct > 80
| timechart span=5m max(store_pct) as pct by broker_name
```

Understanding this SPL

**ActiveMQ Broker Store Usage** — Persistent store percent used (KahaDB) or JDBC store growth causes broker pause and producer blocking. JMX `StoreLimit` usage.

Documented **Data sources**: `org.apache.activemq:type=Broker` `StoreLimit`, `TempLimit`. **App/TA** (typical add-on context): ActiveMQ JMX, `activemq` log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: activemq:broker. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="activemq:broker". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **store_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where store_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by broker_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (store %), Line chart (store usage), Table (brokers over threshold).

## SPL

```spl
index=messaging sourcetype="activemq:broker"
| eval store_pct=round(store_used/store_limit*100,1)
| where store_pct > 80
| timechart span=5m max(store_pct) as pct by broker_name
```

## Visualization

Gauge (store %), Line chart (store usage), Table (brokers over threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
