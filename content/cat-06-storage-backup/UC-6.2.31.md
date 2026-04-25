<!-- AUTO-GENERATED from UC-6.2.31.json — DO NOT EDIT -->

---
id: "6.2.31"
title: "Ceph scrub and deep-scrub error detection from cluster logs"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.31 · Ceph scrub and deep-scrub error detection from cluster logs

## Description

Scrub errors can indicate silent disk corruption or firmware bugs. They require immediate investigation to avoid data loss on erasure-coded pools.

## Value

Triggers hardware replacement and filesystem checks before multiple OSDs fail.

## Implementation

Route high-severity copies to a restricted index. Correlate `pg_id` with `ceph:pg` state snapshots.

## SPL

```spl
index=os sourcetype="ceph:log" earliest=-24h
| search scrub AND (error OR mismatch OR "deep-scrub")
| rex field=_raw "(?i)pg\s+(?<pg_id>[0-9a-f]+\.(?<pg_num>[0-9a-f]+))"
| stats count as scrub_errors latest(_time) as last_seen by host, pg_id
| where scrub_errors > 0
| sort - scrub_errors
```

## Visualization

Table (host, pg, errors), timeline.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
