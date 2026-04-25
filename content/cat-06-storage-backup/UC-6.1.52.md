<!-- AUTO-GENERATED from UC-6.1.52.json — DO NOT EDIT -->

---
id: "6.1.52"
title: "NetApp ONTAP SnapMirror lag versus configured recovery point objective"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.52 · NetApp ONTAP SnapMirror lag versus configured recovery point objective

## Description

Comparing lag to each relationship's RPO catches bandwidth, snapshot lock, and schedule drift that a static minute threshold misses. This aligns monitoring with how DR policies are actually written.

## Value

Prioritizes replication backlog before audits or failover drills, preserving RPO commitments for NAS and SAN DR pairs.

## Implementation

Poll `/api/snapmirror/relationships` via the TA and extract `lag_time`, `policy`, and `healthy`. Convert ISO8601 lag to seconds if needed using `strptime`. Alert when lag exceeds `rpo_sec` for two consecutive samples; throttle during bulk resync using a `state` filter.

## SPL

```spl
index=storage sourcetype="netapp:ontap:snapmirror"
| eval lag_sec=coalesce(lag_time, relationship_lag_seconds, lag_seconds, if(isnotnull(lag_time_millis), round(lag_time_millis/1000,0), null()))
| eval rpo_sec=coalesce(policy_rpo_seconds, rpo_seconds, 3600)
| where isnotnull(lag_sec) AND lag_sec > rpo_sec
| eval breach_ratio=round(lag_sec/rpo_sec,2)
| stats max(lag_sec) as max_lag max(rpo_sec) as policy_rpo max(breach_ratio) as breach by relationship_name, destination_path, cluster_name
| sort - max_lag
```

## Visualization

Scatter (RPO vs lag), timechart of lag by relationship, table of worst breaches.

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/1664)
- [SnapMirror overview](https://docs.netapp.com/us-en/ontap/snapmirror/index.html)
