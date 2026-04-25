<!-- AUTO-GENERATED from UC-8.1.90.json — DO NOT EDIT -->

---
id: "8.1.90"
title: "WildFly Transaction Manager Rollback Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.90 · WildFly Transaction Manager Rollback Rate

## Description

High rollback rates point to conflicting resources, timeouts, or downstream failures. Volume-based alerting finds systemic issues before single-ticket noise.

## Value

Preserves data integrity SLAs for transactional workloads.

## Implementation

Tune regex per WildFly version; exclude known integration-test hosts. Correlate with database outages.

## SPL

```spl
index=web sourcetype="jboss:server"
| regex _raw="(?i)(Transaction.*rolled back|Marking transaction.*rollbackOnly|javax.transaction.RollbackException)"
| bin _time span=5m
| stats count by host, _time
| where count > 50
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#transactions-subsystem)
