<!-- AUTO-GENERATED from UC-7.1.46.json — DO NOT EDIT -->

---
id: "7.1.46"
title: "Elasticsearch Shard Recovery Stall Detection"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.46 · Elasticsearch Shard Recovery Stall Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

## Description

Recoveries that linger with low files_percent or bytes_percent indicate slow disks, network partitions, or allocation issues. SRE teams monitor recovery progress alongside cluster health.

## Value

Prevents prolonged yellow/red cluster states and uneven shard placement after node loss or rolling restarts.

## Implementation

Poll recovery API every 2–5 minutes. Include primary/replica role. Alert when any shard recovery is not done beyond your SLA window. Exclude expected long initializations by tagging index patterns.

## SPL

```spl
index=database sourcetype="elasticsearch:recovery"
| where (files_percent < 100 AND stage!="done") OR stage IN ("index","translog","finalize")
| eval stall_age_min=round((now()-_time)/60,1)
| where stall_age_min > 30
| stats latest(files_percent) as files_pct latest(bytes_percent) as bytes_pct latest(stage) as stage by index, shard, node
```

## Visualization

Table (index, shard, stage, percent), Timeline (recovery events), Single value (stuck recoveries).

## Known False Positives

Slow queries during full backup windows, statistics updates, or after index rebuilds; correlate with maintenance and batch schedules before paging.

## References

- [Elasticsearch cat recovery API](https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-recovery.html)
