<!-- AUTO-GENERATED from UC-6.2.40.json — DO NOT EDIT -->

---
id: "6.2.40"
title: "TrueNAS SCALE ZFS pool vdev degraded faulted or removed disk state"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.2.40 · TrueNAS SCALE ZFS pool vdev degraded faulted or removed disk state

## Description

Degraded vdevs mean single-disk failure away from pool loss. Immediate visibility into `FAULTED` or `REMOVED` topology nodes drives faster disk swap and sparing decisions.

## Value

Protects NAS and VM stores from silent escalation to unrecoverable RAID-Z loss.

## Implementation

Poll `/api/v2.0/pool` every 60s during incidents, 5 minutes steady state. Map `topology` JSON to a short `topology_summary` field at ingest. Authenticate with API keys in `passwords.conf`.

## SPL

```spl
index=storage sourcetype="truenas:pool" earliest=-15m
| eval st=coalesce(status, state, health)
| search degraded OR faulted OR removed OR offline OR UNAVAIL
| eval pool=coalesce(pool_name, name)
| table _time, hostname, pool, st, scan_state, topology_summary
```

## Visualization

Table (pool, status), single value (degraded count).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
