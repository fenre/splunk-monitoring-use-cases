<!-- AUTO-GENERATED from UC-8.2.41.json — DO NOT EDIT -->

---
id: "8.2.41"
title: "Microsoft IIS Worker Process CPU and Memory vs App Pool Limits"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.41 · Microsoft IIS Worker Process CPU and Memory vs App Pool Limits

## Description

`w3wp.exe` CPU and working set reflect real pool cost versus `cpuLimit`, recycling limits, and VM size. Sustained pressure precedes automatic recycles that users perceive as random logouts.

## Value

Aligns hardware, IIS application pool settings, and observed worker footprint before outages force emergency scale-up.

## Implementation

Enable `WinHostMon` process monitoring in `Splunk_TA_windows` `inputs.conf`. Compare with IIS `applicationPool` CPU throttling settings.

## SPL

```spl
index=windows sourcetype="WinHostMon"
| where Type="Process" AND Name="w3wp*"
| eval cpu=tonumber(CpuPerc) mem_mb=tonumber(Memory)
| timechart span=5m perc95(cpu) as p95_cpu perc95(mem_mb) as p95_mem by host
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## References

- [Microsoft IIS documentation](https://docs.splunk.com/Documentation/WindowsAddOn/latest/User/ConfigureWinHostMon)
