<!-- AUTO-GENERATED from UC-6.2.53.json — DO NOT EDIT -->

---
id: "6.2.53"
title: "TrueNAS cloud sync task success rate and byte transfer variance"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.53 · TrueNAS cloud sync task success rate and byte transfer variance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations, Data Quality &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Cloud sync tasks back up datasets to object storage; silent failures or partial transfers erode offsite protection without ZFS noticing.

## Value

Preserves cloud backup SLAs for ransomware resilience and remote archival compliance.

## Implementation

Normalize provider names (S3, B2, Azure). Alert on zero-byte transfers when prior runs moved TB.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-7d
| search cloudsync OR "cloud sync" OR rclone
| eval ok=if(match(state,"(?i)success|finished"),1,0)
| stats sum(ok) as ok_count count as total sum(eval(bytes_transferred)) as bytes by task_name, hostname
| eval success_pct=round(ok_count/total*100,1)
| where success_pct < 95 OR total-ok_count > 2
| sort success_pct
```

## Visualization

Bar chart (success %), table (task, bytes).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
