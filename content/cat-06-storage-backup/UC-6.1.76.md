<!-- AUTO-GENERATED from UC-6.1.76.json — DO NOT EDIT -->

---
id: "6.1.76"
title: "Pure Storage FlashArray controller failover and nondisruptive upgrade status"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.76 · Pure Storage FlashArray controller failover and nondisruptive upgrade status

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Change &middot; **Status:** Draft

*We help you see how your arrays and related gear are doing before small issues turn into full outages or restore surprises.*

---

## Description

Unexpected controller failovers during upgrades or steady state point to power, firmware, or path issues. Correlating NDU windows prevents false escalations.

## Value

Keeps maintenance slots trustworthy and reduces Sev1 noise during controller replacements.

## Implementation

Tag change windows via lookup on `array_name` and suppress benign NDU messages. Retain raw events in a long-retention index for vendor cases.

## SPL

```spl
index=storage sourcetype="purestorage:alert"
| search controller OR failover OR "nondisruptive" OR NDU OR upgrade
| eval arr=coalesce(array_name, array)
| stats count as evts latest(_time) as last_seen by arr, message
| sort - evts
```

## Visualization

Event timeline, table (array, message, count).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
