<!-- AUTO-GENERATED from UC-1.2.136.json — DO NOT EDIT -->

---
id: "1.2.136"
title: "macOS MDM Enrollment and User Channel Check-In SLA"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.136 · macOS MDM Enrollment and User Channel Check-In SLA

## Description

macOS devices that fall out of MDM enrollment lose policy baselines for disk encryption, firewall, and update cadence. Comparing enrollment flags and last MDM check-in timestamps surfaces unmanaged or ghost systems before auditors do.

## Value

Protects configuration compliance on Apple endpoints by catching MDM channel loss within hours instead of at quarterly inventory.

## Implementation

Ingest your MDM tool’s device export or webhook stream. Normalize fields: `mdm_enrolled` boolean, `last_contact_time_epoch`, `serial_number`, `udid`. For Jamf, mirror the classic Splunk-for-Jamf sourcetype naming; for Intune Graph pulls, use `intune:device`. Schedule hourly; alert when `mdm_enrolled=false` on corporately tagged assets or `hours_since > 48`. Join Splunk asset lookups for loaner exclusions.

## Detailed Implementation

Prerequisites
• HEC token or modular input with API credentials stored in Splunk secret storage.
• Field aliases aligned across MDM vendors.

Step 1 — Backfill baseline with a one-time `inputlookup` merge.

Step 2 — Alert routing to mobile device team with serial for Apple GSX lookup.

Step 3 — Validate against MDM console UI for a test device put in airplane mode.

Step 4 — Document BYOD exclusion rules.

## SPL

```spl
index=mdm sourcetype=jamf:computer_inventory OR sourcetype=intune:device OR sourcetype=ws1:device
| eval last_seen_epoch=coalesce(tonumber(last_contact_time_epoch), tonumber(last_seen_epoch))
| eval hours_since=round((now()-last_seen_epoch)/3600,2)
| where isnotnull(mdm_enrolled) AND mdm_enrolled=false OR hours_since > 48
| table _time, host, serial_number, mdm_enrolled, udid, hours_since, management_source
| sort - hours_since
```

## Visualization

Map (optional by site), Table (stale check-ins), Single value (unenrolled count).

## References

- [Apple Platform Deployment — MDM overview](https://support.apple.com/guide/deployment/depd0f22e45/web)
- [Splunk Docs: HTTP Event Collector setup](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
