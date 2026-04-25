<!-- AUTO-GENERATED from UC-8.6.32.json — DO NOT EDIT -->

---
id: "8.6.32"
title: "ActiveMQ KahaDB Journal and Checkpoint Errors"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.6.32 · ActiveMQ KahaDB Journal and Checkpoint Errors

## Description

Journal I/O failures, checkpoint exceptions, or corruption hints mean the broker cannot durably enqueue/dequeue—often a precursor to forced offline recovery.

## Value

Triggers immediate storage and backup drills before brokers enter an inconsistent state that loses messages.

## Implementation

Route these alerts to the messaging platform team with attached disk SMART metrics. Practice snapshot/restore runbooks quarterly. Suppress during known storage migrations using host lookups.

## SPL

```spl
index=messaging sourcetype="activemq:log"
| search ("KahaDB" OR "Journal" OR "checkpoint") AND ("ERROR" OR "Exception" OR "failed" OR "corrupt")
| stats latest(_raw) as sample by host
| eval kahadb_fault=1
```

## Visualization

Timeline (KahaDB errors), Table (host, sample), Single value (brokers affected).

## References

- [Apache ActiveMQ — KahaDB](https://activemq.apache.org/components/classic/documentation/kahadb)
- [Apache ActiveMQ — Troubleshooting](https://activemq.apache.org/components/classic/documentation/faq)
