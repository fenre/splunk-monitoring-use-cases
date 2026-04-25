<!-- AUTO-GENERATED from UC-6.2.41.json — DO NOT EDIT -->

---
id: "6.2.41"
title: "TrueNAS disk SMART reallocated and pending sector threshold breach"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.41 · TrueNAS disk SMART reallocated and pending sector threshold breach

## Description

Reallocated and pending sectors predict imminent disk failure. Catching them before vdev degradation reduces rebuild windows and backup stress.

## Value

Lowers data loss risk on ZFS pools serving SMB/NFS/iSCSI to production.

## Implementation

Enable periodic SMART tests in TrueNAS UI; ingest SMART JSON after each short test. Thresholds vary by vendor—maintain `disk_vendor_thresholds.csv` lookup.

## SPL

```spl
index=storage sourcetype="truenas:disk" earliest=-1h
| eval realloc=coalesce(smart_reallocated_sector_ct, reallocated_sector_count)
| eval pending=coalesce(smart_current_pending_sector, pending_sectors)
| where realloc > 0 OR pending > 0
| eval disk=coalesce(disk_name, name, devname)
| stats latest(realloc) as realloc latest(pending) as pending by hostname, disk
| sort - pending
```

## Visualization

Table (disk, realloc, pending), heatmap.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
