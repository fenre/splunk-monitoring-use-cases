<!-- AUTO-GENERATED from UC-8.3.15.json — DO NOT EDIT -->

---
id: "8.3.15"
title: "Azure Service Bus Dead Letter Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.15 · Azure Service Bus Dead Letter Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We watch for signs that dLQ message count per topic/subscription and dead-letter reasons (, ) for cloud-native messaging.*

---

## Description

DLQ message count per topic/subscription and dead-letter reasons (`DeliveryCount`, `ExceptionDescription`) for cloud-native messaging.

## Value

DLQ message count per topic/subscription and dead-letter reasons (`DeliveryCount`, `ExceptionDescription`) for cloud-native messaging.

## Implementation

Enable metrics on topics/subscriptions. Alert on any DLQ growth for tier-1 entities. Sample DLQ messages via separate secure pipeline (not full body in Splunk if PII).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Azure Monitor Diagnostic Settings → Splunk.
- Ensure the following data sources are available: `DeadletteredMessages` metric, operational logs.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Enable metrics on topics/subscriptions. Alert on any DLQ growth for tier-1 entities. Sample DLQ messages via separate secure pipeline (not full body in Splunk if PII).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:servicebus:metrics"
| where metric_name="DeadletteredMessages" OR EntityName="*DeadLetter*"
| timechart span=5m sum(Total) as dlq_count by EntityName, SubscriptionName
| where dlq_count > 0
```

#### Understanding this SPL

**Azure Service Bus Dead Letter Monitoring** — DLQ message count per topic/subscription and dead-letter reasons (`DeliveryCount`, `ExceptionDescription`) for cloud-native messaging.

Documented **Data sources**: `DeadletteredMessages` metric, operational logs. **App/TA** (typical add-on context): Azure Monitor Diagnostic Settings → Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:servicebus:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=azure, sourcetype="azure:servicebus:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Filters the current rows with `where metric_name="DeadletteredMessages" OR EntityName="*DeadLetter*"` — typically the threshold or rule expression for this monitoring goal.
- `timechart` plots the metric over time using **span=5m** buckets with a separate series **by EntityName, SubscriptionName** — ideal for trending and alerting on this use case.
- Filters the current rows with `where dlq_count > 0` — typically the threshold or rule expression for this monitoring goal.


### Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DLQ count), Table (entity, subscription, count), Single value (total DLQ messages).

## SPL

```spl
index=azure sourcetype="azure:servicebus:metrics"
| where metric_name="DeadletteredMessages" OR EntityName="*DeadLetter*"
| timechart span=5m sum(Total) as dlq_count by EntityName, SubscriptionName
| where dlq_count > 0
```

## Visualization

Line chart (DLQ count), Table (entity, subscription, count), Single value (total DLQ messages).

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
