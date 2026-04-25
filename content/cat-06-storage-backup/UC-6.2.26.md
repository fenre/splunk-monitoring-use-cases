<!-- AUTO-GENERATED from UC-6.2.26.json — DO NOT EDIT -->

---
id: "6.2.26"
title: "Ceph BlueStore compression ratio effectiveness by pool"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.26 · Ceph BlueStore compression ratio effectiveness by pool

## Description

Compression that no longer yields ratio >1 wastes CPU and obscures capacity planning. Pool-level ratios highlight mis-set `compression_algorithm` or incompressible data.

## Value

Right-sizes CPU spend and improves effective $/TB for backup and archive pools.

## Implementation

Flatten `pools` array from `ceph df detail`. Join pool to application owner via lookup for chargeback.

## SPL

```spl
index=storage sourcetype="ceph:pool" earliest=-1h
| eval stored=coalesce(stored_bytes, stored)
| eval raw=coalesce(stored_raw_bytes, stored_raw)
| eval ratio=if(raw>0, round(stored/raw,3), null())
| where isnotnull(ratio) AND compression_mode!="none"
| timechart span=6h latest(ratio) as compress_ratio by pool_name
```

## Visualization

Line chart (ratio by pool), table (pool, mode, ratio).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
