<!-- AUTO-GENERATED from UC-6.2.55.json — DO NOT EDIT -->

---
id: "6.2.55"
title: "TrueNAS dataset compression ratio by algorithm and workload"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.55 · TrueNAS dataset compression ratio by algorithm and workload

## Description

Compression ratios validate whether LZ4/ZSTD settings match data types; incompressible scientific data should not waste CPU at ZSTD-19.

## Value

Optimizes CPU and improves effective capacity for multi-tenant NAS offerings.

## Implementation

Parse `compressratio` strings like `2.10x` with `replace` to numeric. Join dataset to application class lookup.

## SPL

```spl
index=storage sourcetype="truenas:dataset" earliest=-12h
| eval algo=coalesce(compression, compression_type)
| eval ratio=coalesce(compressratio, compression_ratio, logical_to_physical)
| where algo!="off" AND isnotnull(ratio)
| stats latest(ratio) as compress_ratio by dataset_name, algo, hostname
| sort - compress_ratio
```

## Visualization

Table (dataset, algo, ratio), boxplot by algo.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
