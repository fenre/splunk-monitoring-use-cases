<!-- AUTO-GENERATED from UC-6.1.69.json — DO NOT EDIT -->

---
id: "6.1.69"
title: "Pure Storage ActiveCluster mediator connectivity and witness health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.69 · Pure Storage ActiveCluster mediator connectivity and witness health

## Description

Loss of the ActiveCluster mediator or witness path risks split-brain protection gaps during site failures. Early detection preserves automatic failover guarantees.

## Value

Protects synchronous stretch-cluster RPO=0 designs relied on by Tier-0 applications.

## Implementation

Forward array alert REST feed and syslog duplicates into the same index. Deduplicate on `alert_id` with `stats latest(*) by alert_id`. Page on any mediator-down event outside maintenance.

## SPL

```spl
index=storage (sourcetype="purestorage:alert" OR sourcetype="purestorage:array")
| search mediator OR ActiveCluster OR "witness" OR "tiebreaker"
| eval sev=coalesce(severity, level, priority)
| eval arr=coalesce(array_name, array)
| table _time, arr, sev, component, message, state
```

## Visualization

Timeline of mediator alerts, table (array, message).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
