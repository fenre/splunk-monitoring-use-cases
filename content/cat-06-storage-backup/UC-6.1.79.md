<!-- AUTO-GENERATED from UC-6.1.79.json — DO NOT EDIT -->

---
id: "6.1.79"
title: "Pure Storage array alert storm detection from unified alert feed"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.79 · Pure Storage array alert storm detection from unified alert feed

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operational, Anomaly &middot; **Status:** Draft

*We help you see how your arrays and related gear are doing before small issues turn into full outages or restore surprises.*

---

## Description

Alert storms usually precede controller instability, fan-out of path failures, or misconfigured monitoring loops. Detecting burstiness triggers runbook steps before human fatigue sets in.

## Value

Improves operator focus during incidents and prevents duplicate tickets from noisy dependencies.

## Implementation

Use `streamstats` for rolling rate if static thresholds fail. Join with network maintenance lookup to suppress known events.

## SPL

```spl
index=storage sourcetype="purestorage:alert" earliest=-15m
| eval arr=coalesce(array_name, array)
| stats count as alert_count dc(component) as components dc(message) as signatures by arr
| where alert_count > 25 OR components > 10
```

## Visualization

Histogram of alert rate, table (array, count).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
