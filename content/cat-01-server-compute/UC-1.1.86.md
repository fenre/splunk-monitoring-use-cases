<!-- AUTO-GENERATED from UC-1.1.86.json — DO NOT EDIT -->

---
id: "1.1.86"
title: "Fork Bomb Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.86 · Fork Bomb Detection

## Description

Compares the latest **process_count** sample on a host to that host’s within-window **mean** and **standard deviation**, alerting when the live count clears **mean+4σ** (and **σ>0** to skip flat baselines).

## Value

Runaway **fork** patterns blow up **PID** tables and **scheduler** queues; this is a coarse but fast statistical tripwire on the **process** count signal alone.

## Implementation

Emit `process_count` from `ps -e | wc -l` or `/proc` stat readers. Widen the **stats** window or use `streamstats` over **7d** if your sample rate is sparse.

## Detailed Implementation

Prerequisites
• A script that can read **process** count as a non-root user in your security model (often yes on **proc**).

**Fix note** — Earlier templates referenced `process_count` after `stats` without carrying the field forward; this revision **latest(process_count)** keeps the field for the threshold line.


Step 3 — Validate
`ps -e | wc -l` and `uptime` on the host in the same minute; use `pstree` only for **visual** proof, not as the primary metric.

Step 4 — Operationalize
If this fires, also check **nproc** **ulimit** and **systemd** **TasksMax** for the service **unit**.



## SPL

```spl
index=os sourcetype=custom:process_count host=*
| stats latest(process_count) as process_count, avg(process_count) as avg_procs, stdev(process_count) as stddev by host
| where process_count>(avg_procs+4*stddev) AND stddev>0
```

## Visualization

Alert, Anomaly Chart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
