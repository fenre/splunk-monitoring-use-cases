<!-- AUTO-GENERATED from UC-6.2.50.json — DO NOT EDIT -->

---
id: "6.2.50"
title: "TrueNAS jail and plugin CPU memory utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.50 · TrueNAS jail and plugin CPU memory utilization

## Description

Plugins and jails share the same kernel as ZFS; runaway containers can starve ARC and storage daemons, hurting NAS clients.

## Value

Keeps application stacks colocated on TrueNAS from impacting primary file services.

## Implementation

If API lacks per-jail CPU, use `jexec` scripted samples. Tag jails with owner email in KV lookup.

## SPL

```spl
index=storage sourcetype="truenas:jail" earliest=-1h
| eval jail=coalesce(jail_name, name)
| eval cpu=coalesce(cpu_percent, cpu_usage)
| eval mem=coalesce(mem_percent, memory_usage_percent)
| where cpu > 85 OR mem > 90
| timechart span=15m max(cpu) as cpu_pct max(mem) as mem_pct by jail
```

## Visualization

Line chart (CPU/mem by jail), table (peak usage).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
