<!-- AUTO-GENERATED from UC-2.7.5.json — DO NOT EDIT -->

---
id: "2.7.5"
title: "Proxmox VE ZFS Replication Lag and Error Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.7.5 · Proxmox VE ZFS Replication Lag and Error Trending

## Description

ZFS replication provides asynchronous DR copies for many Proxmox estates. Growing lag or intermittent errors predict broken snapshots, network saturation, or target pool exhaustion before the standby site is useless.

## Value

Holds RPO targets and speeds root-cause analysis between replication endpoints.

## Implementation

Normalize last-sync timestamps to epoch seconds. Alert when lag exceeds policy minutes or `fail_count` increments. Enrich with pool free-space from `proxmox:storage` on the target.

## SPL

```spl
index=pve sourcetype="proxmox:replication" earliest=-24h
| eval lag_sec=now()-tonumber(coalesce(last_sync_epoch, last_sync, last_run_epoch))
| eval errs=tonumber(coalesce(fail_count, errors, error_count))
| where lag_sec>3600 OR errs>0 OR match(lower(coalesce(error, _raw)), "(?i)error|fail")
| stats latest(lag_sec) as repl_lag_sec, max(errs) as err_peak, values(error) as err_msgs by guest, target
| sort - repl_lag_sec
```

## Visualization

Area chart replication lag; single value worst pair; table of error strings.

## References

- [Proxmox Storage Replication](https://pve.proxmox.com/wiki/Storage_Replication)
