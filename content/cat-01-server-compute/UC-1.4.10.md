<!-- AUTO-GENERATED from UC-1.4.10.json — DO NOT EDIT -->

---
id: "1.4.10"
title: "Disk Controller and HBA Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.10 · Disk Controller and HBA Health

## Description

RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.

## Value

The controller is the traffic cop for the disks; if it reports a bad state or degraded virtual drives, you want a ticket while data is still recoverable, not when volumes go offline together.

## Implementation

Run vendor CLI (MegaCli, perccli, hpssacli) via scripted input every 15 minutes. Parse controller and virtual drive state. Alert when status is not Optimal or any array is degraded.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (MegaRAID, perccli, hpssacli).
• Ensure the following data sources are available: Vendor CLI output (e.g. `MegaCli64 -AdpAllInfo -aAll`), `/proc/scsi/` on Linux for context if needed.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux, install the vendor’s CLI in the same image as the forwarder or call it over SSH. Run every 15 minutes and emit `controller_status` and `degraded_virtual_drives` (or your naming) per `controller_id` and `host`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust healthy strings to your vendor):

```spl
index=hardware sourcetype=raid_controller host=*
| stats latest(controller_status) as status, latest(degraded_virtual_drives) as degraded by host, controller_id
| where status != "Optimal" OR degraded > 0
| table host controller_id status degraded
```

Understanding this SPL

**Disk Controller and HBA Health** — RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=raid_controller`.
• `stats` takes latest controller and degraded counts per `host` and `controller_id`.
• `where` flags not-`Optimal` or any `degraded` &gt; 0 in the sample.


Step 3 — Validate
On a test host, run the vendor CLI and compare to indexed `status` and `degraded`. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=raid_controller host=*
| stats latest(controller_status) as status, latest(degraded_virtual_drives) as degraded by host, controller_id
| where status != "Optimal" OR degraded > 0
| table host controller_id status degraded
```

## CIM SPL

```spl
N/A — RAID or HBA controller state is not a CIM data model; use a custom `raid_controller` sourcetype from vendor CLIs (Linux typical).
```

## Visualization

Status panel (Optimal/Degraded/Failed), Table of degraded arrays.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
