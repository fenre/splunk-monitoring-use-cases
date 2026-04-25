<!-- AUTO-GENERATED from UC-6.2.44.json — DO NOT EDIT -->

---
id: "6.2.44"
title: "TrueNAS snapshot hold space consumption by dataset"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.44 · TrueNAS snapshot hold space consumption by dataset

## Description

Snapshot holds can balloon after backup or replication issues, consuming pool headroom faster than active data growth.

## Value

Avoids emergency deletes and supports lifecycle policies aligned with compliance retention.

## Implementation

Normalize path-style dataset names. Alert when week-over-week snapshot bytes grow >25% using `delta` command.

## SPL

```spl
index=storage sourcetype="truenas:dataset" earliest=-6h
| eval snap_b=coalesce(usedbysnapshots, used_by_snapshot, snapshot_used_bytes)
| eval ds=coalesce(dataset_name, name)
| timechart span=6h sum(snap_b) as snapshot_bytes by ds
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Stacked area (snapshot bytes), table (dataset, snap TB).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
