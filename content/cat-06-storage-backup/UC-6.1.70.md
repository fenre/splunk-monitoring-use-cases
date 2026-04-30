<!-- AUTO-GENERATED from UC-6.1.70.json — DO NOT EDIT -->

---
id: "6.1.70"
title: "Pure Storage FlashArray SafeMode snapshot immutability audit"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.70 · Pure Storage FlashArray SafeMode snapshot immutability audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Compliance &middot; **Status:** Draft

*We track copy and mirror health so a planned outage or a bad link does not leave you with an old or broken remote copy when you need it most.*

---

## Description

SafeMode immutability underpins ransomware recovery guarantees for snapshots. Volumes or groups without SafeMode weaken legal and cyber insurance evidence.

## Value

Demonstrates immutability coverage for auditors and speeds incident response when restore points must be trusted.

## Implementation

Extend volume JSON parsing to include SafeMode flags from Purity REST. Join protection groups if modeled separately. Export weekly CSV for GRC archives.

## SPL

```spl
index=storage sourcetype="purestorage:volume"
| eval sm=coalesce(safemode_enabled, snapshot_safemode, protection_group_safemode)
| where isnull(sm) OR sm="false" OR sm="0"
| stats values(volume_name) as volumes by array_name
| where mvcount(volumes) > 0
```

## Visualization

Table (array, volumes missing SafeMode), single value (% volumes protected).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
