<!-- AUTO-GENERATED from UC-2.1.26.json — DO NOT EDIT -->

---
id: "2.1.26"
title: "VM Hardware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.26 · VM Hardware Version Compliance

## Description

Older VM hardware versions lack support for newer features — vNVMe, UEFI secure boot, vTPM, higher vCPU/memory limits, and improved device emulation. Running mixed hardware versions complicates fleet management and limits what features you can enable cluster-wide.

## Value

Older VM hardware versions lack support for newer features — vNVMe, UEFI secure boot, vTPM, higher vCPU/memory limits, and improved device emulation. Running mixed hardware versions complicates fleet management and limits what features you can enable cluster-wide.

## Implementation

Collected via Splunk_TA_vmware inventory. Define target hardware version per cluster (e.g., vmx-19 for vSphere 7.0 U2+, vmx-20 for vSphere 8.0). Generate weekly compliance reports. Coordinate upgrades during maintenance windows as they require VM power cycle.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via Splunk_TA_vmware inventory. Define target hardware version per cluster (e.g., vmx-19 for vSphere 7.0 U2+, vmx-20 for vSphere 8.0). Generate weekly compliance reports. Coordinate upgrades during maintenance windows as they require VM power cycle.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(hw_version) as hw_version, latest(guest_os) as guest_os by vm_name, host
| eval hw_num=tonumber(replace(hw_version, "vmx-", ""))
| where hw_num < 19
| stats count by hw_version
| sort hw_version
| table hw_version, count
```

Understanding this SPL

**VM Hardware Version Compliance** — Older VM hardware versions lack support for newer features — vNVMe, UEFI secure boot, vTPM, higher vCPU/memory limits, and improved device emulation. Running mixed hardware versions complicates fleet management and limits what features you can enable cluster-wide.

Documented **Data sources**: `sourcetype=vmware:inv:vm`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hw_num** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hw_num < 19` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by hw_version** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Hardware Version Compliance**): table hw_version, count

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (hardware version distribution), Table (VMs needing upgrade), Bar chart (versions by cluster).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(hw_version) as hw_version, latest(guest_os) as guest_os by vm_name, host
| eval hw_num=tonumber(replace(hw_version, "vmx-", ""))
| where hw_num < 19
| stats count by hw_version
| sort hw_version
| table hw_version, count
```

## Visualization

Pie chart (hardware version distribution), Table (VMs needing upgrade), Bar chart (versions by cluster).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
