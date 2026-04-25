<!-- AUTO-GENERATED from UC-2.8.1.json — DO NOT EDIT -->

---
id: "2.8.1"
title: "oVirt Engine API Health and engine.log Fatal Errors"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.8.1 · oVirt Engine API Health and engine.log Fatal Errors

## Description

Engine is the control plane for oVirt/RHV. ERROR/FATAL bursts or database connectivity messages precede UI outages, failed scheduling, and stuck workflows.

## Value

Protects orchestration uptime and prevents cascading failures across hosts and storage domains.

## Implementation

Ship engine logs with fast time sync. Deduplicate using `correlation_id`. Page on FATAL or DB errors; warn on ERROR rate vs baseline. Pair with database and JVM metrics.

## SPL

```spl
index=ovirt sourcetype="ovirt:engine" earliest=-1h
| eval lv=upper(coalesce(log_level, level, priority))
| where lv="ERROR" OR lv="FATAL" OR match(lower(_raw), "(?i)fatal|outofmemory|jdbc|database.*unavailable")
| stats count as ev by correlation_id, thread
| where ev>=5
```

## Visualization

Timechart ERROR rate; top correlation_id table; raw drilldown.

## References

- [Red Hat Virtualization Administration Guide](https://docs.redhat.com/en/documentation/red_hat_virtualization/)
