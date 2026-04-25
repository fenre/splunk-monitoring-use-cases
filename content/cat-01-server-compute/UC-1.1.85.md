<!-- AUTO-GENERATED from UC-1.1.85.json — DO NOT EDIT -->

---
id: "1.1.85"
title: "Memory Hog Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.85 · Memory Hog Detection

## Description

Averages **mem_pct** per **(host,process)** from `top` samples in the window and surfaces processes that sit above **40**% of host memory on average—tune per your headroom policy.

## Value

Memory hogs push the kernel toward **OOM**; seeing the process name early steers you to **cgroup** limits, config, or leak triage faster than host-level **free** alone.

## Implementation

If your **top** feed uses **RSS** in **KB** instead of **mem_pct**, replace the `stats` with `avg(rss_kb)/mem_total_kb` after you join a **meminfo** snapshot for the same **host**+**_time**.

## Detailed Implementation

Prerequisites
• `top` interval fast enough to catch bursty **malloc** storms; pair with **vmstat** UC for reclaim context.


Step 3 — Validate
`top` / `ps aux --sort=-%mem` on the host; `pmap` or **language**-level profilers if a leak is suspected.

Step 4 — Operationalize
If **OOM** already happened, pivot to **dmesg** for the **killer** line in the same minute as this search.



## SPL

```spl
index=os sourcetype=top host=*
| stats avg(mem_pct) as avg_mem by host, process
| where avg_mem>40
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Processes.mem_usage) as avg_mem from datamodel=Endpoint.Processes by Processes.dest Processes.process_name span=5m | where avg_mem>40
```

## Visualization

Table, Gauge

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
