<!-- AUTO-GENERATED from UC-7.2.27.json — DO NOT EDIT -->

---
id: "7.2.27"
title: "MongoDB Replica Set Member State Degradation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.27 · MongoDB Replica Set Member State Degradation

## Description

Replica set members not in PRIMARY or SECONDARY healthy states indicate elections, sync loss, or network partitions—core MongoDB availability monitoring.

## Value

Shortens downtime by detecting bad member states before application drivers exhaust their server selection timeouts.

## Implementation

Poll rs.status() every 30–60s from a monitoring user. Normalize stateStr and health booleans. Suppress alerts during planned step-downs using change calendar. Track optime lag between primary and secondaries in a companion panel.

## SPL

```spl
index=database sourcetype="mongodb:rs_status"
| where stateStr IN ("STARTUP","STARTUP2","RECOVERING","ROLLBACK","DOWN","UNKNOWN") OR health==0 OR health=="0"
| stats latest(stateStr) as state latest(health) as health by name, set_name, host
| sort state
```

## Visualization

Table (member, state, health), Timeline (state changes), Single value (degraded members).

## References

- [MongoDB Replica Set Member States](https://www.mongodb.com/docs/manual/reference/replica-states/)
