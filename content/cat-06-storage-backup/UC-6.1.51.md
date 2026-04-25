<!-- AUTO-GENERATED from UC-6.1.51.json — DO NOT EDIT -->

---
id: "6.1.51"
title: "NetApp ONTAP FabricPool cold tier activity and cloud footprint savings"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.51 · NetApp ONTAP FabricPool cold tier activity and cloud footprint savings

## Description

FabricPool moves cold blocks to object storage; if cloud footprint stalls while local utilization climbs, flash costs rise and backup windows stretch. Trending cloud vs local footprint validates tiering policies and savings.

## Value

Supports chargeback and FinOps by quantifying cloud tier offload, and flags misconfiguration before on-prem capacity is exhausted.

## Implementation

Enable TA volume inventory inputs. Map REST `space.cloud_storage` or `cloud_storage_footprint` with `FIELDALIAS` in `props.conf` if names differ by ONTAP release. Index to `storage`. Optional: join `ontap:vserver` events for SVM ownership.

## SPL

```spl
index=storage sourcetype="netapp:ontap:vol"
| eval cloud_b=coalesce(cloud_storage_footprint, space.cloud_storage, cloud_footprint_bytes, tier_footprint_bytes)
| eval local_b=coalesce(logical_space, size, space.logical)
| where isnotnull(cloud_b) AND cloud_b > 0
| eval cold_pct=if(local_b>0, round(cloud_b / local_b * 100, 2), null())
| timechart span=1h sum(cloud_b) as cloud_bytes sum(local_b) as logical_bytes by volume_name
```

## Visualization

Stacked area (cloud vs logical bytes), table (volume, cold_pct), single value (fleet cloud TB).

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/1664)
- [FabricPool overview](https://docs.netapp.com/us-en/ontap/fabricpool/index.html)
