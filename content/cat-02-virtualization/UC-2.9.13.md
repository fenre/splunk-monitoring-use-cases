<!-- AUTO-GENERATED from UC-2.9.13.json — DO NOT EDIT -->

---
id: "2.9.13"
title: "OpenStack Nova Live Migration Progress and Failure Reasons"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.9.13 · OpenStack Nova Live Migration Progress and Failure Reasons

## Description

Live migrations should converge quickly; stalled jobs tie up CPU and network. Failures during maintenance windows risk unprotected hosts.

## Value

Supports non-disruptive hypervisor operations and capacity balancing.

## Implementation

Extract migration UUID. Alert on failure reason codes. Compare with Neutron MTU issues if TCP migration.

## SPL

```spl
index=openstack sourcetype="openstack:nova" earliest=-24h
| eval mt=lower(coalesce(migration_type, type))
| where match(mt, "(?i)live")
| eval st=lower(status)
| where st="failed" OR tonumber(progress_pct)<100 AND now()-_time>3600
| stats values(reason) as reasons by instance_uuid, src_host, dest_host
```

## Visualization

Timechart in-flight migrations; table failures; bandwidth overlay if metrics exist.

## References

- [OpenStack Nova Live Migration](https://docs.openstack.org/nova/latest/admin/live-migration-usage.html)
