<!-- AUTO-GENERATED from UC-7.1.52.json — DO NOT EDIT -->

---
id: "7.1.52"
title: "MongoDB Index Build Progress via CurrentOp"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.52 · MongoDB Index Build Progress via CurrentOp

## Description

Long-running index builds with stalled `progress` fields tie up resources and can block deployments or maintenance. Watching `progress.done` versus `progress.total` alongside runtime distinguishes healthy long builds from stuck operations before they overlap peak traffic.

## Value

Reduces the chance of surprise storage and CPU saturation during change windows and helps DBAs decide when to kill or reschedule a build.

## Implementation

Poll `currentOp` via mongosh or the TA’s operational input; flatten `progress.done`, `progress.total`, `secs_running`, `ns`, and `opid` into indexed fields in `props.conf` (KV/JSON extraction). Exclude `idleSessionTimeout` noise. Dashboard with threshold: runtime >15m and completion <95%. Alert only outside approved maintenance if builds are rare in production.

## SPL

```spl
index=database sourcetype="mongodb:currentop"
| search op="command" AND match(_raw,"createIndexes")
| eval done=tonumber(mvindex('progress.done',0))
| eval total=tonumber(mvindex('progress.total',0))
| eval pct=if(total>0, round(100*done/total,1), null())
| where isnotnull(pct) AND pct < 95 AND secs_running > 900
| table _time, host, ns, secs_running, pct, opid
```

## Visualization

Bar chart (pct complete by opid), Table (ns, secs_running, pct), Line chart (pct over time per opid).

## References

- [MongoDB — currentOp](https://www.mongodb.com/docs/manual/reference/command/currentOp/)
- [MongoDB — index builds](https://www.mongodb.com/docs/manual/core/index-creation/)
