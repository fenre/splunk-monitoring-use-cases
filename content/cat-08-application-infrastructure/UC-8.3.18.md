---
id: "8.3.18"
title: "RabbitMQ Memory Alarm"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.18 · RabbitMQ Memory Alarm

## Description

`mem_alarm` blocks publishers when `vm_memory_high_watermark` is hit. Early warning from `memory` and `allocated` fields.

## Value

`mem_alarm` blocks publishers when `vm_memory_high_watermark` is hit. Early warning from `memory` and `allocated` fields.

## Implementation

Poll nodes every minute. Alert at 75% memory or alarm true. Flow control from alarm requires immediate consumer scale-up or queue purge policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RabbitMQ management API `/api/nodes`.
• Ensure the following data sources are available: `mem_used`, `mem_limit`, `mem_alarm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll nodes every minute. Alert at 75% memory or alarm true. Flow control from alarm requires immediate consumer scale-up or queue purge policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:node"
| where mem_alarm==true OR mem_used/mem_limit > 0.75
| table _time, name, mem_used, mem_limit, mem_alarm
```

Understanding this SPL

**RabbitMQ Memory Alarm** — `mem_alarm` blocks publishers when `vm_memory_high_watermark` is hit. Early warning from `memory` and `allocated` fields.

Documented **Data sources**: `mem_used`, `mem_limit`, `mem_alarm`. **App/TA** (typical add-on context): RabbitMQ management API `/api/nodes`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:node. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:node". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where mem_alarm==true OR mem_used/mem_limit > 0.75` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **RabbitMQ Memory Alarm**): table _time, name, mem_used, mem_limit, mem_alarm


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (memory % per node), Line chart (mem_used trend), Table (nodes in alarm).

## SPL

```spl
index=messaging sourcetype="rabbitmq:node"
| where mem_alarm==true OR mem_used/mem_limit > 0.75
| table _time, name, mem_used, mem_limit, mem_alarm
```

## Visualization

Gauge (memory % per node), Line chart (mem_used trend), Table (nodes in alarm).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
