<!-- AUTO-GENERATED from UC-6.1.34.json — DO NOT EDIT -->

---
id: "6.1.34"
title: "Pure Storage Array Data Reduction Ratio Collapse"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.34 · Pure Storage Array Data Reduction Ratio Collapse

## Description

A sudden drop in data-reduction ratio often means new noisy workloads, encryption of source data, or loss of thin-provisioned savings—and usable physical capacity burns faster than forecasts.

## Value

Gives capacity owners early warning before free space cliffs, so they can rebalance volumes, change backup patterns, or expand arrays without emergency outages.

## Implementation

Ingest array-level space metrics at least hourly. Baseline the 7-day average reduction ratio per array and alert when the live ratio falls more than ~25% below that baseline. Validate field names against a sample event from your TA version; map REST `space.data_reduction` into `data_reduction_ratio` at ingest if the TA does not already.

## SPL

```spl
index=storage (sourcetype="purestorage:*" OR sourcetype="PureStorage_REST") earliest=-7d
| eval drr=coalesce(data_reduction_ratio, space_data_reduction_ratio, total_reduction)
| where isnotnull(drr) AND drr > 0
| sort 0 _time
| stats first(drr) as drr_start last(drr) as drr_end by array_name
| eval drop_pct=round((drr_start-drr_end)/drr_start*100,1)
| where drr_start > 2 AND drop_pct > 25
| table array_name drr_start drr_end drop_pct
```

## Visualization

Line chart (ratio trend), bar chart (delta vs baseline), table (array, drop %).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Splunk Connect for Syslog — Pure Storage](https://splunk.github.io/splunk-connect-for-syslog/main/sources/vendor/PureStorage/pure_storage/)
