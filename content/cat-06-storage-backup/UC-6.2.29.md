<!-- AUTO-GENERATED from UC-6.2.29.json — DO NOT EDIT -->

---
id: "6.2.29"
title: "Ceph pool PG autoscaler adjustment and target PG change events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.29 · Ceph pool PG autoscaler adjustment and target PG change events

## Description

Autoscaler changes affect placement group counts and can trigger backfill storms. Tracking adjustments explains sudden load increases after capacity events.

## Value

Helps operators correlate performance changes with configuration—not mystery hardware faults.

## Implementation

Increase log verbosity temporarily during expansions; tag events with change ticket via lookup on `pool_name`.

## SPL

```spl
index=os sourcetype="ceph:log" earliest=-24h
| search pg_autoscaler OR "suggested pgs" OR "target pg"
| rex field=_raw "(?i)pool\s+'?(?<pool_name>[A-Za-z0-9_-]+)'?"
| stats count as adjustments latest(_time) as last_seen by pool_name, cluster_name
| sort - adjustments
```

## Visualization

Event timeline, table (pool, adjustments).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
