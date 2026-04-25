<!-- AUTO-GENERATED from UC-2.1.35.json — DO NOT EDIT -->

---
id: "2.1.35"
title: "VM Guest OS Disk Space via VMware Tools"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.35 · VM Guest OS Disk Space via VMware Tools

## Description

VMware Tools reports guest OS filesystem utilization to vCenter, enabling disk space monitoring without an in-guest agent. Particularly valuable for appliances, embedded systems, and VMs where you cannot install a Splunk forwarder. Catches disk-full conditions before they crash applications.

## Value

VMware Tools reports guest OS filesystem utilization to vCenter, enabling disk space monitoring without an in-guest agent. Particularly valuable for appliances, embedded systems, and VMs where you cannot install a Splunk forwarder. Catches disk-full conditions before they crash applications.

## Implementation

Requires VMware Tools running in the guest. Splunk_TA_vmware collects guest disk info as part of VM inventory. Alert at 85% (warning) and 95% (critical). Note: this is less granular than an in-guest agent — it reports per-partition but with slower refresh intervals (typically 5-10 minutes).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm` (guest disk info).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires VMware Tools running in the guest. Splunk_TA_vmware collects guest disk info as part of VM inventory. Alert at 85% (warning) and 95% (critical). Note: this is less granular than an in-guest agent — it reports per-partition but with slower refresh intervals (typically 5-10 minutes).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" guest_disk_path=*
| eval used_pct=round((guest_disk_capacity - guest_disk_freeSpace) / guest_disk_capacity * 100, 1)
| where used_pct > 85
| sort -used_pct
| table vm_name, host, guest_disk_path, used_pct, guest_disk_capacity, guest_disk_freeSpace
```

Understanding this SPL

**VM Guest OS Disk Space via VMware Tools** — VMware Tools reports guest OS filesystem utilization to vCenter, enabling disk space monitoring without an in-guest agent. Particularly valuable for appliances, embedded systems, and VMs where you cannot install a Splunk forwarder. Catches disk-full conditions before they crash applications.

Documented **Data sources**: `sourcetype=vmware:inv:vm` (guest disk info). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Guest OS Disk Space via VMware Tools**): table vm_name, host, guest_disk_path, used_pct, guest_disk_capacity, guest_disk_freeSpace

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, disk, usage), Gauge per critical VM, Bar chart (top full disks).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" guest_disk_path=*
| eval used_pct=round((guest_disk_capacity - guest_disk_freeSpace) / guest_disk_capacity * 100, 1)
| where used_pct > 85
| sort -used_pct
| table vm_name, host, guest_disk_path, used_pct, guest_disk_capacity, guest_disk_freeSpace
```

## Visualization

Table (VM, disk, usage), Gauge per critical VM, Bar chart (top full disks).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
