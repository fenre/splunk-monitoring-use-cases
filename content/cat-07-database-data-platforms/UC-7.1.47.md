<!-- AUTO-GENERATED from UC-7.1.47.json — DO NOT EDIT -->

---
id: "7.1.47"
title: "OpenSearch Shard Recovery Stall Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.47 · OpenSearch Shard Recovery Stall Detection

## Description

Shard recoveries that fail to complete indicate disk or network bottlenecks during node replacement or rolling upgrades. OpenSearch operators track recovery stage and percent like Elasticsearch.

## Value

Reduces time-to-green after failures by catching stuck recoveries before search capacity degrades for extended periods.

## Implementation

Poll the recovery API on the same cadence as Elasticsearch equivalents. Normalize sourcetype at ingest. Align thresholds with maintenance windows and large shard counts.

## SPL

```spl
index=database sourcetype="opensearch:recovery"
| where (files_percent < 100 AND stage!="done") OR stage IN ("index","translog","finalize")
| eval stall_age_min=round((now()-_time)/60,1)
| where stall_age_min > 30
| stats latest(files_percent) as files_pct latest(bytes_percent) as bytes_pct latest(stage) as stage by index, shard, node
```

## Visualization

Table (index, shard, stage, percent), Timeline (recovery), Single value (stuck count).

## References

- [OpenSearch REST API — cat recovery](https://docs.opensearch.org/latest/api-reference/cat/cat-recovery/)
