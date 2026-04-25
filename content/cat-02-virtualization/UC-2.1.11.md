<!-- AUTO-GENERATED from UC-2.1.11.json — DO NOT EDIT -->

---
id: "2.1.11"
title: "ESXi Host Hardware Alerts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.11 · ESXi Host Hardware Alerts

## Description

CIM-based hardware health detects physical component failures (fans, PSU, temperature) at the hypervisor level before they cause host failure.

## Value

CIM-based hardware health detects physical component failures (fans, PSU, temperature) at the hypervisor level before they cause host failure.

## Implementation

vCenter triggers hardware alarms via CIM providers on ESXi hosts. Splunk_TA_vmware collects these alarm events. Alert on red/yellow hardware alarms. Ensure CIM providers are installed on ESXi (vendor-specific VIBs).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events` (vCenter alarms).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
vCenter triggers hardware alarms via CIM providers on ESXi hosts. Splunk_TA_vmware collects these alarm events. Alert on red/yellow hardware alarms. Ensure CIM providers are installed on ESXi (vendor-specific VIBs).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" (event_type="AlarmStatusChangedEvent") alarm_name="Host hardware*"
| table _time host alarm_name old_status new_status
| where new_status="red" OR new_status="yellow"
| sort -_time
```

Understanding this SPL

**ESXi Host Hardware Alerts** — CIM-based hardware health detects physical component failures (fans, PSU, temperature) at the hypervisor level before they cause host failure.

Documented **Data sources**: `sourcetype=vmware:events` (vCenter alarms). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **ESXi Host Hardware Alerts**): table _time host alarm_name old_status new_status
• Filters the current rows with `where new_status="red" OR new_status="yellow"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Host health grid (red/yellow/green), Events table, Alert panel.

## SPL

```spl
index=vmware sourcetype="vmware:events" (event_type="AlarmStatusChangedEvent") alarm_name="Host hardware*"
| table _time host alarm_name old_status new_status
| where new_status="red" OR new_status="yellow"
| sort -_time
```

## Visualization

Host health grid (red/yellow/green), Events table, Alert panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
