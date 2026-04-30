<!-- AUTO-GENERATED from UC-8.5.20.json — DO NOT EDIT -->

---
id: "8.5.20"
title: "Kafka Dynamic Broker Configuration Change Detection"
status: "draft"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.20 · Kafka Dynamic Broker Configuration Change Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Change &middot; **Status:** Draft

*We use this to speed incident correlation when a sudden behavior change traces to an unplanned broker property update.*

---

## Description

Broker logs emit entries when `dynamicConfig` or alter-config paths change retention, ACLs, or listener properties—events that should map to approved change tickets.

## Value

Speeds incident correlation when a sudden behavior change traces to an unplanned broker property update.

## Implementation

Tune keywords to your broker distribution (Apache vs Confluent). Feed results into a change correlation lookup (ticket ID in CMDB). Suppress maintenance windows.

## SPL

```spl
index=kafka sourcetype="kafka:serverLog"
| search "Dynamic" AND ("config" OR "configuration") AND ("update" OR "alter" OR "changed")
| rex "^\[[^\]]+\]\s+(?<log_level>\w+)"
| where log_level IN ("INFO","WARN","ERROR")
| table _time, host, log_level, _raw
```

## Visualization

Timeline (config change events), Table (host, raw line), Single value (changes per day).

## Known False Positives

Queues and broker metrics swing during rebalancing, replay, or maintenance. We align with change windows.

## References

- [Apache Kafka — Updating Broker Config](https://kafka.apache.org/documentation/#brokerconfigs)
- [Source types for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Sourcetypes)
