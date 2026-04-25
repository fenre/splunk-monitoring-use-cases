<!-- AUTO-GENERATED from UC-1.1.84.json — DO NOT EDIT -->

---
id: "1.1.84"
title: "Runaway Process Detection (CPU Hog)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.84 · Runaway Process Detection (CPU Hog)

## Description

Averages per-process **cpu_pct** from `top` samples in the search window and flags **(host,process)** pairs above an **80**% average—tune to your workload class.

## Value

A single hot process on a shared host can starve others even when **vmstat** still looks “OK”; `top` granularity is the fastest path to the binary name for support teams.

## Implementation

Field may be **pctCPU** or **pcpu** depending on TA version—normalize in **props**. Add `| where count>10` on underlying events to require enough samples before paging.

## Detailed Implementation

Prerequisites
• `top` script enabled; confirm **cpu_pct** exists with a short **Fieldsummary**.

**CIM** — If `Processes.cpu_load_percent` does not exist in your build, adjust `cimSpl` to the field your **CIM** engineer published for per-process CPU.


Step 3 — Validate
Run `top` or `htop` on the host and **pidstat** for one-minute **CPU** proof; compare the **process** string to Splunk (watch for **truncation**).

Step 4 — Operationalize
Use the same panel next to the **CPU utilization trending** host-level UC for context.



## SPL

```spl
index=os sourcetype=top host=*
| stats avg(cpu_pct) as avg_cpu by host, process
| where avg_cpu>80
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Processes.cpu_load_percent) as avg_cpu from datamodel=Endpoint.Processes by Processes.dest Processes.process_name span=5m | where avg_cpu>80
```

## Visualization

Table, Timechart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
