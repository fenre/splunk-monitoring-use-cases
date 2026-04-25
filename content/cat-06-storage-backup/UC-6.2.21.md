<!-- AUTO-GENERATED from UC-6.2.21.json — DO NOT EDIT -->

---
id: "6.2.21"
title: "Ceph placement group stuck inactive unclean undersized or stale states"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.21 · Ceph placement group stuck inactive unclean undersized or stale states

## Description

Stuck PG states mean data is not fully available or not meeting min_size. Left unchecked, they threaten read/write availability and prolong recovery after node loss.

## Value

Prioritizes ceph engineer triage before client timeouts cascade into application outages.

## Implementation

Prefer JSON `pg dump` over parsing text; include `pgid`, `state`, `pool_name`. Throttle alerts until `bad_pgs` > threshold for 10 minutes to avoid flap during small blips.

## SPL

```spl
index=storage sourcetype="ceph:pg" earliest=-30m
| eval st=coalesce(pg_state, state)
| where match(st, "(?i)inactive|unclean|undersized|stale")
| stats dc(pg_id) as bad_pgs values(st) as states by pool_name, cluster_name
| sort - bad_pgs
```

## Visualization

Single value (bad PG count), table (pool, states).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
