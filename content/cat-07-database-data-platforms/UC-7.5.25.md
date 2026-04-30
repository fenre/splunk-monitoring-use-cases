<!-- AUTO-GENERATED from UC-7.5.25.json — DO NOT EDIT -->

---
id: "7.5.25"
title: "MongoDB Index Build and collMod Operations"
status: "draft"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-7.5.25 · MongoDB Index Build and collMod Operations

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Change &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

## Description

Index builds change performance characteristics and can throttle production workloads. Operators track createIndexes/dropIndexes/collMod events for correlation with latency regressions.

## Value

Speeds root-cause analysis when deployments coincide with long-running index builds on large collections.

## Implementation

Ensure mongod logs include command namespace. For Atlas, ship equivalent audit events. Pair with currentOp index builds panel. Filter routine automation via service account lookup.

## SPL

```spl
index=database sourcetype="mongodb:log"
| search "createIndexes" OR "dropIndexes" OR "collMod"
| rex field=_raw "ns:\s+(?<ns>[^\s]+)"
| stats earliest(_time) as started latest(_raw) as sample by ns, host
| sort -started
```

## Visualization

Timeline (operations), Table (ns, host), Drill to raw sample.

## Known False Positives

Maintenance work (ANALYZE, VACUUM, REINDEX, index builds) and ETL or large report jobs may show up as long-running or blocking — compare with the maintenance and batch schedule.

## References

- [MongoDB Index Builds on Populated Collections](https://www.mongodb.com/docs/manual/core/index-creation/)
