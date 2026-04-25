<!-- AUTO-GENERATED from UC-6.1.53.json — DO NOT EDIT -->

---
id: "6.1.53"
title: "NetApp ONTAP aggregate thin-provisioning overcommit ratio trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.53 · NetApp ONTAP aggregate thin-provisioning overcommit ratio trending

## Description

Thin provisioning allows logical commitments to exceed free physical space. A climbing overcommit ratio signals snapshot growth or volume sprawl that can cause sudden aggregate full events.

## Value

Provides runway analysis before writes fail across all volumes on the aggregate, informing procurement and volume moves.

## Implementation

Enable aggregate polling in the TA. If only percentages exist, derive bytes from `size` and `*_percent` fields. Accelerate a nightly summary of max overcommit per aggregate for long-term trending.

## SPL

```spl
index=storage sourcetype="netapp:ontap:aggr"
| eval phys=coalesce(physical_used, block_storage_physical_used)
| eval logi=coalesce(logical_used, block_storage_logical_used)
| eval overcommit=if(phys>0, round(logi/phys,3), null())
| timechart span=4h max(overcommit) as overcommit_ratio by aggregate_name
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

Line chart (overcommit by aggregate), reference band, table (latest ratio).

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/1664)
- [Disks and aggregates](https://docs.netapp.com/us-en/ontap/disks-aggregates/index.html)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
