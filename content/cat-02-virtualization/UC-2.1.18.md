<!-- AUTO-GENERATED from UC-2.1.18.json — DO NOT EDIT -->

---
id: "2.1.18"
title: "VMware Tools Status and Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.18 · VMware Tools Status and Version Compliance

## Description

Outdated or missing VMware Tools causes loss of guest-host integration — no graceful shutdown, no quiesced snapshots, no balloon driver, degraded network/disk performance, and inaccurate guest OS reporting. Tools must be current for vMotion to function optimally.

## Value

Outdated or missing VMware Tools causes loss of guest-host integration — no graceful shutdown, no quiesced snapshots, no balloon driver, degraded network/disk performance, and inaccurate guest OS reporting. Tools must be current for vMotion to function optimally.

## Implementation

Collected automatically via Splunk_TA_vmware inventory. Run daily compliance report. toolsStatus values: toolsOk, toolsOld, toolsNotInstalled, toolsNotRunning. Alert on toolsNotInstalled for production VMs. Track version_status to ensure Tools are current across the fleet.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm` (inventory data).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected automatically via Splunk_TA_vmware inventory. Run daily compliance report. toolsStatus values: toolsOk, toolsOld, toolsNotInstalled, toolsNotRunning. Alert on toolsNotInstalled for production VMs. Track version_status to ensure Tools are current across the fleet.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(toolsStatus) as tools_status, latest(toolsVersionStatus) as version_status, latest(toolsRunningStatus) as running_status by vm_name, host, guest_os
| where tools_status!="toolsOk" OR version_status!="guestToolsCurrent"
| sort tools_status
| table vm_name, host, guest_os, tools_status, version_status, running_status
```

Understanding this SPL

**VMware Tools Status and Version Compliance** — Outdated or missing VMware Tools causes loss of guest-host integration — no graceful shutdown, no quiesced snapshots, no balloon driver, degraded network/disk performance, and inaccurate guest OS reporting. Tools must be current for vMotion to function optimally.

Documented **Data sources**: `sourcetype=vmware:inv:vm` (inventory data). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host, guest_os** so each row reflects one combination of those dimensions.
• Filters the current rows with `where tools_status!="toolsOk" OR version_status!="guestToolsCurrent"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VMware Tools Status and Version Compliance**): table vm_name, host, guest_os, tools_status, version_status, running_status

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (Tools status distribution), Table (non-compliant VMs), Bar chart (by guest OS).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(toolsStatus) as tools_status, latest(toolsVersionStatus) as version_status, latest(toolsRunningStatus) as running_status by vm_name, host, guest_os
| where tools_status!="toolsOk" OR version_status!="guestToolsCurrent"
| sort tools_status
| table vm_name, host, guest_os, tools_status, version_status, running_status
```

## Visualization

Pie chart (Tools status distribution), Table (non-compliant VMs), Bar chart (by guest OS).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
