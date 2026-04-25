<!-- AUTO-GENERATED from UC-2.7.2.json — DO NOT EDIT -->

---
id: "2.7.2"
title: "Proxmox VE vzdump Backup Duration Trending and Failure Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.7.2 · Proxmox VE vzdump Backup Duration Trending and Failure Detection

## Description

Backup jobs that run too long or fail quietly break restore-point SLAs. vzdump emits explicit completion status and timings; trending them exposes storage bottlenecks, snapshot locks, and guest I/O storms before the next compliance audit or recovery drill.

## Value

Protects recoverability commitments and prioritizes remediation on the slowest backup targets first.

## Implementation

Parse vzdump lines into structured fields. Baseline p95 duration per `storage`. Alert on any `failed` job or p95 beyond the overnight window. For failures, drill into `proxmox:task` UPIDs matching the same `jobid` timestamp.

## SPL

```spl
index=pve sourcetype="proxmox:backup" earliest=-7d@d latest=now
| eval dur=tonumber(coalesce(duration_sec, duration, job_duration_sec))
| eval ok=if(match(lower(coalesce(status, result)), "(?i)ok|success|finished"), 1, 0)
| bin _time span=1d
| stats count as jobs, sum(ok) as ok_jobs, avg(dur) as avg_dur, perc95(dur) as p95_dur,
    sum(eval(if(ok==0,1,0))) as failed by storage, _time
| where failed>0 OR p95_dur>14400
| table _time, storage, jobs, ok_jobs, failed, avg_dur, p95_dur
```

## Visualization

Stacked column ok vs failed jobs; line chart p95 duration; table of latest errors with vmid.

## References

- [Proxmox VZDump Backup](https://pve.proxmox.com/wiki/VZDump_Backup)
