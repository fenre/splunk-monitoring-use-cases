<!-- AUTO-GENERATED from UC-2.7.4.json — DO NOT EDIT -->

---
id: "2.7.4"
title: "Proxmox VE Live Migration Completion Time and Error Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.7.4 · Proxmox VE Live Migration Completion Time and Error Rate

## Description

Live migrations should finish quickly and without errors during host maintenance. Long tail durations or failures highlight inadequate migration network bandwidth, storage latency, or pinned CPU configurations.

## Value

Keeps host evacuation and hardware refresh projects on schedule while avoiding hidden guest impact.

## Implementation

Filter only migration task types to reduce noise. Establish per–node-pair baselines. Alert on failures immediately; warn on p95 above your SLO. Compare with `proxmox:pveproxy` latency and `proxmox:storage` latency in the same window.

## SPL

```spl
index=pve sourcetype="proxmox:task" earliest=-24h
| eval t=lower(coalesce(type, task_type, operation))
| where match(t, "(?i)qmigrate|migrate")
| eval dur=tonumber(coalesce(duration_sec, duration))
| eval ok=if(match(lower(coalesce(status, result)), "(?i)ok|success"),1,0)
| stats count as migrations, median(dur) as med_dur, perc95(dur) as p95_dur,
    sum(eval(if(ok==0,1,0))) as failed by src_node, dst_node
| where failed>0 OR p95_dur>600
```

## Visualization

Heat map of p95 duration by node pair; timechart median migration time; table of failed vmid samples.

## References

- [QEMU/KVM Migration on Proxmox](https://pve.proxmox.com/wiki/QEMU/KVM_Migration)
