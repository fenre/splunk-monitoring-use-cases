<!-- AUTO-GENERATED from UC-8.5.37.json — DO NOT EDIT -->

---
id: "8.5.37"
title: "ActiveMQ Durable Subscriber Offline Backlog Growth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.37 · ActiveMQ Durable Subscriber Offline Backlog Growth

## Description

When a durable subscriber is offline, the broker retains messages in a dedicated backlog; rapid `QueueSize` growth on those internal destinations risks exhausting store limits and slowing all clients on the broker. Tracking inactive durable counts highlights forgotten test clients and zombie subscriptions.

## Value

Prevents silent store exhaustion from abandoned durable subscriptions and quantifies catch-up work before reconnect storms after maintenance.

## Implementation

Tune name filters to your `clientId`/`subscriptionName` conventions. Exclude known batch consumers via lookup. Alert on week-over-week growth, not just absolute depth, for seasonal workloads.

## SPL

```spl
index=messaging sourcetype="activemq:broker" earliest=-24h
| eval dest=coalesce(DestinationName, destination_name)
| eval qsize=coalesce(QueueSize, queue_size)
| eval inactive=coalesce(InactiveDurableSubscribers, inactive_durable_subscribers, 0)
| eval durable_name=coalesce(subscription_name, client_id, durable_name)
| where match(dest, "(?i)dur|sub|consumer") OR inactive>0 OR isnotnull(durable_name)
| where qsize > 1000 OR inactive>0
| timechart span=1h max(qsize) as durable_backlog max(inactive) as inactive_durables by dest, broker_name limit=15
```

## Visualization

Line chart (durable backlog), table (broker, destination, inactive count), single value (worst backlog).

## References

- [Apache ActiveMQ — Durable Subscribers](https://activemq.apache.org/manage-durable-subscribers)
- [Apache ActiveMQ — JMX](https://activemq.apache.org/jmx.html)
