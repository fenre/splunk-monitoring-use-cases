<!-- AUTO-GENERATED from UC-6.1.33.json — DO NOT EDIT -->

---
id: "6.1.33"
title: "Pure FlashArray Pod and Asynchronous Replication Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.33 · Pure FlashArray Pod and Asynchronous Replication Lag

## Description

ActiveCluster pods and asynchronous replication links that fall behind increase failover risk and break RPO targets for business-critical LUNs and file workloads on FlashArray.

## Value

Surfaces replication lag before failover or DR exercises fail, so storage teams can fix networking, bandwidth, or snapshot schedules while data is still converging.

## Implementation

Deploy the Unified Add-on on a heavy forwarder, create one secured REST input per FlashArray using an API token with observability scope, and enable pod or protection-group metrics (or forward array alerts). Confirm extracted field names in Search; some builds flatten `replication_lag_*` differently—alias in `props.conf` if needed. Alert warning at 5 minutes lag and critical beyond 15 minutes unless a longer RPO is approved.

## SPL

```spl
index=storage (sourcetype="purestorage:*" OR sourcetype="PureStorage_REST")
| eval lag_ms=coalesce(replication_lag_ms, replication_lag_millisec)
| eval lag_sec=coalesce(replication_lag_sec, if(isnotnull(lag_ms), round(lag_ms/1000,0), null()), pod_replication_lag_seconds)
| where isnotnull(lag_sec) AND lag_sec > 300
| stats max(lag_sec) as max_lag_sec latest(array_name) as array by pod_name
| sort - max_lag_sec
```

## Visualization

Time chart (lag by pod), single value (worst lag), table (pod, array, max lag).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference — array monitoring](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
