<!-- AUTO-GENERATED from UC-6.2.43.json — DO NOT EDIT -->

---
id: "6.2.43"
title: "TrueNAS replication task lag failures and last snapshot age"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.43 · TrueNAS replication task lag failures and last snapshot age

## Description

ZFS replication protects against ransomware and site loss. Failed tasks or multi-hour lag silently invalidate DR assumptions for remote datasets.

## Value

Preserves RPO for SMB/NFS datasets replicated to colo or cloud targets.

## Implementation

Flatten recursive task trees if using periodic snapshots. Join `task` to dataset mapping via lookup for owner paging.

## SPL

```spl
index=storage sourcetype="truenas:replication" earliest=-2h
| eval state=coalesce(state, status, job_state)
| eval lag=coalesce(lag_seconds, delay_seconds, snapshot_age_sec)
| where match(state, "(?i)error|fail") OR lag > 3600
| eval task=coalesce(task_name, name, id)
| table _time, hostname, task, state, lag
```

## Visualization

Timeline of failures, table (task, lag).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
