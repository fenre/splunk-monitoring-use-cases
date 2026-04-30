<!-- AUTO-GENERATED from UC-6.2.21.json — DO NOT EDIT -->

---
id: "6.2.21"
title: "Ceph placement group stuck inactive unclean undersized or stale states"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.21 · Ceph placement group stuck inactive unclean undersized or stale states

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

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

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
