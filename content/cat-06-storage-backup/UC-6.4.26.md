<!-- AUTO-GENERATED from UC-6.4.26.json — DO NOT EDIT -->

---
id: "6.4.26"
title: "Commvault tape library slot utilization and drive online availability"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.4.26 · Commvault tape library slot utilization and drive online availability

## Description

High slot utilization risks export/import failures mid-backup window; offline drives extend backup duration and jeopardize batch completion.

## Value

Supports mainframe and long-retention programs that still depend on physical tape economics.

## Implementation

Schedule hourly inventory jobs from Commvault REST. Map `library_name` to datacenter rows. Alert when `pct>90` for 3 consecutive samples.

## SPL

```spl
index=backup sourcetype="commvault:library" earliest=-1h
| eval used=coalesce(slots_used, used_slots)
| eval total=coalesce(slots_total, total_slots)
| eval pct=if(total>0, round(used/total*100,1), null())
| eval drives_up=coalesce(drives_online, online_drives)
| eval drives_all=coalesce(drives_total, total_drives)
| where pct > 90 OR drives_up < drives_all
| table _time, library_name, pct, drives_up, drives_all, site
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Gauge (slot %), table (library, drives).

## References

- [Commvault Documentation — Splunk integration](https://documentation.commvault.com/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
