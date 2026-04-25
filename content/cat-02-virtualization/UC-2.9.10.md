<!-- AUTO-GENERATED from UC-2.9.10.json — DO NOT EDIT -->

---
id: "2.9.10"
title: "OpenStack Cinder Snapshot Creation Backlog and Slow Jobs"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.9.10 · OpenStack Cinder Snapshot Creation Backlog and Slow Jobs

## Description

Snapshot backlogs delay backup windows and complicate restore testing. Queue time exposes slow arrays or overloaded cinder-volume workers.

## Value

Keeps backup RPO realistic and prevents overlapping snapshot storms.

## Implementation

Track queue duration. Alert when many snapshots exceed 30 minutes queued. Correlate with array replication load.

## SPL

```spl
index=openstack sourcetype="openstack:cinder" earliest=-24h
| eval prog=tonumber(progress_pct)
| eval q=tonumber(queued_sec)
| where prog<100 AND q>1800
| stats count as backlog by backend, host
```

## Visualization

Area chart backlog; table volumes; worker host breakdown.

## References

- [OpenStack Cinder Snapshots](https://docs.openstack.org/cinder/latest/cli/cli-cinder-snapshots.html)
