<!-- AUTO-GENERATED from UC-6.3.27.json — DO NOT EDIT -->

---
id: "6.3.27"
title: "TrueNAS Dataset Quota and Refquota Threshold Breach"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.27 · TrueNAS Dataset Quota and Refquota Threshold Breach

## Description

ZFS datasets with quotas or refquotas enforce hard stops for SMB/NFS shares and application logs; crossing 90% typically means user-visible errors within hours.

## Value

Prevents surprise write outages on multi-tenant filers and keeps VMware NFS datastores from freezing when quotas are tighter than pool free space suggests.

## Implementation

Poll dataset inventory every 15 minutes. Flatten nested `used` objects from TrueNAS SCALE JSON. Treat `refquota` separately if you enforce it without a parent `quota`. Feed results to ITSM with owner mapping from a lookup keyed by `dataset_name`.

## SPL

```spl
index=storage sourcetype="truenas:dataset" earliest=-1h
| eval used=coalesce(used_bytes, used.bytes, used)
| eval quota=coalesce(quota_bytes, quota, refquota_bytes, refquota)
| eval pct_used=if(quota>0, round(used/quota*100,2), null())
| where isnotnull(pct_used) AND pct_used > 90
| stats latest(pct_used) as pct_used latest(used) as used_b latest(quota) as quota_b by hostname dataset_name
| sort - pct_used
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

Bar chart (dataset vs %), table (dataset, used, quota), forecast line using `predict` on used bytes.

## References

- [TrueNAS SCALE — Dataset documentation](https://www.truenas.com/docs/scale/scaleuireference/storage/datasets/)
- [OpenZFS manual — native properties (quota, refquota)](https://openzfs.github.io/openzfs-docs/man/master/7/zfsprops.7.html)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
