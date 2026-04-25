<!-- AUTO-GENERATED from UC-6.1.40.json — DO NOT EDIT -->

---
id: "6.1.40"
title: "Dell EMC PowerMax RDF/A Replication Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.40 · Dell EMC PowerMax RDF/A Replication Lag

## Description

`r1_r2_lag_time` tracks how far asynchronous RDF mirrors fall behind; sustained lag breaches RPO commitments for mainframe and open-systems DR pairs on PowerMax.

## Value

Surfaces WAN compression issues, RDF director faults, or workload spikes before remote sites are too stale for failover approvals.

## Implementation

In the TA input, enable RDF Group (or RDF/A) KPI/custom metrics including `R1_R2_Lag_Time`. Confirm events include `reporting_level` and `array_id`. Set thresholds from the business RPO (e.g., 5 minutes warn, 15 minutes critical) and exclude maintenance windows with a lookup.

## SPL

```spl
index=storage sourcetype="dellemc:vmax:rest" r1_r2_lag_time=*
| stats latest(r1_r2_lag_time) as lag_sec by array_id rdf_group_name
| where lag_sec > 300
| eval lag_min=round(lag_sec/60,1)
| sort - lag_sec
```

## Visualization

Line chart (lag trend), table (RDF group, lag minutes), single value (worst lag).

## References

- [Dell EMC PowerMax Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/3416)
- [PowerMax for Splunk — configuration (sourcetype dellemc:vmax:rest)](https://powermax-for-splunk.readthedocs.io/en/stable/configuration.html)
