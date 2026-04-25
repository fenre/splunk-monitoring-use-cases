<!-- AUTO-GENERATED from UC-8.5.33.json — DO NOT EDIT -->

---
id: "8.5.33"
title: "ActiveMQ Producer Flow Control Activation Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.33 · ActiveMQ Producer Flow Control Activation Events

## Description

When memory, store, or temp usage crosses configured watermarks, ActiveMQ enables producer flow control and publishers stall—often the first user-visible symptom of downstream consumer slowness or oversized messages. Log lines mentioning flow control are high-signal operational events.

## Value

Shortens MTTR for send-timeouts and thread pileups in producers by proving the broker deliberately slowed publishers rather than a vague network fault.

## Implementation

Set log level to capture INFO/WARN usage-manager messages in production (avoid DEBUG noise). Dedupe on host + minute for paging. Correlate with `activemq:broker` usage percentages from JMX on the same timestamp.

## SPL

```spl
index=messaging sourcetype="activemq:log" earliest=-24h
| regex _raw="(?i)Producer Flow Control|blocking message production|BlockingProducer|Usage Manager.*(Memory|Store|Temp)|message production.*blocked"
| rex field=_raw max_match=1 "(?i)(?<usage_component>Memory|Store|Temp)(?:\s+[Uu]sage)?"
| stats count as flow_events latest(_raw) as sample by host, usage_component
| where flow_events >= 3
| sort -flow_events
```

## Visualization

Timeline of flow-control keywords, top hosts by event count, drilldown to raw log sample.

## References

- [Apache ActiveMQ — Producer Flow Control](https://activemq.apache.org/producer-flow-control)
- [Apache ActiveMQ — Features](https://activemq.apache.org/features)
