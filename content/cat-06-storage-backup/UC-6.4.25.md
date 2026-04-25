<!-- AUTO-GENERATED from UC-6.4.25.json — DO NOT EDIT -->

---
id: "6.4.25"
title: "Commvault deduplication savings ratio declining trend on storage policies"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.4.25 · Commvault deduplication savings ratio declining trend on storage policies

## Description

A falling deduplication ratio often signals new encrypted or already-compressed data sources, misaligned block size, or engine fragmentation. It directly raises backend storage costs.

## Value

Gives backup admins early warning before library purchases accelerate and cloud tier bills spike.

## Implementation

Normalize percentage fields (50 vs 0.5) in `props.conf`. Use summary indexing for 90-day trends. Join `policy` to business unit for chargeback conversations.

## SPL

```spl
index=backup (sourcetype="commvault:storage" OR sourcetype="commvault:job")
| eval dr=coalesce(dedup_ratio, dedupe_ratio, space_saved_ratio, global_savings_ratio)
| eval pol=coalesce(storage_policy, policy_name)
| timechart span=1d latest(dr) as dedup_ratio by pol
| streamstats window=7 global=f current(dr) as dr_now earliest(dr) as dr_7dago
| eval drop_pct=round((dr_7dago-dr_now)/dr_7dago*100,1)
| where drop_pct > 15
```

## Visualization

Line chart (dedup ratio), table (policy, week drop %).

## References

- [Commvault Documentation — Splunk integration](https://documentation.commvault.com/)
