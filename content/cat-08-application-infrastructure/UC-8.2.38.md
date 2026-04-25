<!-- AUTO-GENERATED from UC-8.2.38.json — DO NOT EDIT -->

---
id: "8.2.38"
title: "Microsoft IIS Application Pool Recycling Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.38 · Microsoft IIS Application Pool Recycling Events

## Description

Recycling resets in-process state and can explain user session loss or cold-start latency spikes. Distinguishing scheduled, idle-timeout, and error-driven recycles focuses remediation on configuration versus code defects.

## Value

Cuts mean time to innocence for application teams during IIS instability windows.

## Implementation

Install Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`); enable IIS operational channels. Correlate EventCode meanings with MSDN. Tag planned maintenance.

## SPL

```spl
index=windows sourcetype="WinEventLog:Microsoft-Windows-IIS-Configuration/Operational" OR sourcetype="WinEventLog:Application"
| where EventCode IN (5074,5075,5117,5118,5119) OR match(_raw, "(?i)application pool.*recycle")
| stats count by EventCode, host, Message
| sort - count
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## References

- [Microsoft IIS documentation](https://learn.microsoft.com/en-us/iis/get-started/introduction-to-iis/iis-overview)
