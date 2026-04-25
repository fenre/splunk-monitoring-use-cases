<!-- AUTO-GENERATED from UC-6.1.37.json — DO NOT EDIT -->

---
id: "6.1.37"
title: "Ceph Placement Group Degraded or Peering Stuck States"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.37 · Ceph Placement Group Degraded or Peering Stuck States

## Description

PGs that stay in `peering`, `degraded`, `undersized`, or `stuck` states mean data is not fully redundant; prolonged states risk data loss if additional OSDs fail.

## Value

Narrows blast radius to specific pools and PG counts so on-call engineers can target OSD hosts, CRUSH rules, or network partitions before the cluster blocks I/O.

## Implementation

Run a privileged script every 5 minutes on a management host with keyring access: parse `ceph pg dump_stuck unclean` or full JSON, flatten `pgid`, `state`, `pool_name`, and `cluster_name`, and send via HEC. Complement UC-6.1.14 (`ceph:status`)—this UC focuses on PG-level persistence, not the summary health string.

## SPL

```spl
index=storage sourcetype="ceph:pg" earliest=-30m
| where NOT match(pg_state, "(?i)active\+clean")
| stats dc(pg_id) as affected_pgs values(pg_state) as states latest(pool_name) as pool by cluster_name
| where affected_pgs > 0
| sort - affected_pgs
```

## Visualization

Single value (count of bad PGs), treemap (by pool), table (pg_state, count).

## References

- [Ceph Documentation — Placement groups](https://docs.ceph.com/en/latest/rados/operations/placement-groups/)
- [Splunk Docs — Send data to HTTP Event Collector](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
