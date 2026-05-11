<!-- AUTO-GENERATED from UC-6.1.54.json — DO NOT EDIT -->

---
id: "6.1.54"
title: "NetApp ONTAP NVMe-oF namespace latency versus FC or iSCSI LUN latency"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.54 · NetApp ONTAP NVMe-oF namespace latency versus FC or iSCSI LUN latency

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch how full your storage is getting and give you time to add space or clean up snapshots and old data before an application or job suddenly stops working.*

---

## Description

NVMe-oF namespaces should generally outperform legacy SAN paths on the same controllers. Persistent protocol skew points to host multipathing, queue depth, or SAN zoning issues.

## Value

De-risks NVMe-oF rollouts for Tier-1 databases by validating latency parity against existing FC/iSCSI baselines.

## Implementation

Configure TA counter inputs for `namespace` and `lun` objects (60–300s interval). Alias counter fields in `props.conf` if the TA prefixes with `counters.`. Filter `instance_name` with a lookup of production devices to reduce noise.

## SPL

```spl
index=storage (sourcetype="netapp:ontap:perf" OR sourcetype="netapp:ontap:counter")
| eval obj=lower(coalesce(object_name, object))
| where obj="namespace" OR obj="lun"
| eval lat_ms=coalesce(read_latency, avg_latency, total_latency)
| eval proto=if(obj=="namespace","NVMe-oF","FC_iSCSI")
| timechart span=5m perc95(lat_ms) as p95_ms by proto, instance_name
```

## Visualization

Line chart (p95 by protocol), table (worst instances).

## Known False Positives

FC port errors can spike during cable replacements, SFP swaps, zoning changes, or approved maintenance on the fabric.

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/1664)
- [NVMe support](https://docs.netapp.com/us-en/ontap/)
