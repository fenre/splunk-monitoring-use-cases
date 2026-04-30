<!-- AUTO-GENERATED from UC-6.1.71.json — DO NOT EDIT -->

---
id: "6.1.71"
title: "Pure Storage FlashArray SSD wear leveling and drive endurance depletion rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.71 · Pure Storage FlashArray SSD wear leveling and drive endurance depletion rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Risk &middot; **Status:** Draft

*We help you see how your arrays and related gear are doing before small issues turn into full outages or restore surprises.*

---

## Description

Flash modules approaching end-of-life increase rebuild times and outage risk during double-fault windows. Trending remaining life supports proactive RMA scheduling.

## Value

Avoids emergency shipments and non-disruptive upgrade collisions during peak business periods.

## Implementation

If drive life is only in alerts, normalize alert text with `rex` into `life` field. Correlate with support cases using array serial in a lookup.

## SPL

```spl
index=storage (sourcetype="purestorage:array" OR sourcetype="purestorage:alert")
| eval life=coalesce(ssd_life_remaining_percent, drive_life_remaining, endurance_remaining_pct)
| eval drive=coalesce(drive_name, drive_id, component)
| where isnotnull(life) AND life < 20
| timechart span=1d min(life) as min_life by array_name
```

## Visualization

Line chart (min life by array), table (drive, life%).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
