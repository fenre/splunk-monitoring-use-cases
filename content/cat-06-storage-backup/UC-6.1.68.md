<!-- AUTO-GENERATED from UC-6.1.68.json — DO NOT EDIT -->

---
id: "6.1.68"
title: "Pure Storage FlashArray Purity upgrade readiness and deferred software compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.68 · Pure Storage FlashArray Purity upgrade readiness and deferred software compliance

## Description

Arrays lagging approved Purity releases miss security fixes and interoperability certifications. Tracking pending upgrades supports change governance and vendor support posture.

## Value

Reduces exposure to known defects and speeds security audit responses with a single fleet view.

## Implementation

Maintain `pure_approved_purity_versions.csv` in `lookups/` and define `transforms.conf`. Refresh array inventory hourly via the TA. Exclude canary arrays with a `notes` field in the lookup.

## SPL

```spl
index=storage sourcetype="purestorage:array"
| eval ver=coalesce(version, purity_version, os_version)
| eval pending=coalesce(pending_upgrade, upgrade_pending, "false")
| lookup pure_approved_purity_versions env OUTPUT approved_version
| where isnull(approved_version) OR ver!=approved_version OR match(lower(pending), "true|yes|pending")
| stats latest(ver) as running latest(pending) as upgrade_pending by array_name
```

## Visualization

Table (array, version, approved, pending), single value (non-compliant count).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
