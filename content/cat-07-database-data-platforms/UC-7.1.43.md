<!-- AUTO-GENERATED from UC-7.1.43.json — DO NOT EDIT -->

---
id: "7.1.43"
title: "MongoDB Long-Running Operations (currentOp)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.43 · MongoDB Long-Running Operations (currentOp)

## Description

Operations stuck in currentOp with high secs_running or waitingForLock tie up WiredTiger tickets and delay replication. This is standard MongoDB operations monitoring for runaway aggregations, migrations, and index builds.

## Value

Prevents cluster-wide latency incidents by surfacing blocking and long-lived operations before they exhaust database resources.

## Implementation

Every 30–60 seconds, collect active ops from mongos/mongod. Include opid, ns, op, secs_running, waitingForLock, query shape (hashed). Exclude legitimate index builds via op type lookup. Alert when secs_running exceeds policy or waitingForLock persists.

## SPL

```spl
index=database sourcetype="mongodb:currentop"
| where secs_running > 60 OR waitingForLock=="true"
| stats max(secs_running) as max_sec latest(op) as op latest(ns) as ns by opid, host
| sort -max_sec
```

## Visualization

Table (opid, ns, op, duration), Timeline (long ops), Single value (count blocked).

## References

- [MongoDB db.currentOp](https://www.mongodb.com/docs/manual/reference/method/db.currentOp/)
- [DBX Add-on for MongoDB JDBC (Splunkbase)](https://splunkbase.splunk.com/app/7095)
