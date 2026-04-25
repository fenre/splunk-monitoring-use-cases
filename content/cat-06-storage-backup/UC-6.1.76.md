<!-- AUTO-GENERATED from UC-6.1.76.json — DO NOT EDIT -->

---
id: "6.1.76"
title: "Pure Storage FlashArray controller failover and nondisruptive upgrade status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.76 · Pure Storage FlashArray controller failover and nondisruptive upgrade status

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

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
