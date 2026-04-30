<!-- AUTO-GENERATED from UC-2.10.5.json — DO NOT EDIT -->

---
id: "2.10.5"
title: "VxRail vSAN Witness Failover and Network Partition Detection"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.10.5 · VxRail vSAN Witness Failover and Network Partition Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Resilience &middot; **Status:** Verified

*We keep an eye on vxRail vSAN Witness Failover and Network Partition Detection and raise the alarm before it drags down real work or real outages start.*

---

## Description

Witness loss in stretched clusters changes failure tolerance. Rapid detection avoids running in a mode where a second fault loses objects.

## Value

Protects metro-stretch designs and guides fail-safe operator decisions.

## Implementation

Ingest witness heartbeat every minute. Page on unreachable >2 intervals. Run hook to validate external routing.

## SPL

```spl
index=vxrail sourcetype="vxrail:network" earliest=-2h
| eval wr=lower(witness_reachable)
| eval ps=lower(partition_state)
| where wr="false" OR match(ps, "(?i)partition|isolation")
| stats latest(_time) as last_evt by cluster_id, vsan_cluster_uuid
```

## Visualization

Timeline partition states; map witness path; related alerts.

## Known False Positives

IGEL and endpoint UMS health can warn during bulk firmware, certificate rotation, or when a single site loses WAN; use device cohorts to separate local noise from UMS issues.

## References

- [vSAN stretched cluster witness](https://core.vmware.com/resource/introduction-vmware-vsan-stretched-clusters)
