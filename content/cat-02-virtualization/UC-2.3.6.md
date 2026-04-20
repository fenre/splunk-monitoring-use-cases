---
id: "2.3.6"
title: "Virtual Disk Backing Chain and Snapshot Age"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.3.6 · Virtual Disk Backing Chain and Snapshot Age

## Description

Long snapshot chains and old snapshots degrade I/O and complicate recovery. Monitoring supports snapshot hygiene and prevents runaway growth.

## Value

Long snapshot chains and old snapshots degrade I/O and complicate recovery. Monitoring supports snapshot hygiene and prevents runaway growth.

## Implementation

Script to list VM disks and snapshot chains (e.g. `virsh snapshot-list`, `qemu-img info`). Compute chain depth and oldest snapshot age. Alert when depth >3 or oldest snapshot >30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`virsh domblkinfo`, `qemu-img info`).
• Ensure the following data sources are available: Libvirt/QEMU disk info.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Script to list VM disks and snapshot chains (e.g. `virsh snapshot-list`, `qemu-img info`). Compute chain depth and oldest snapshot age. Alert when depth >3 or oldest snapshot >30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=kvm_disk_chain host=*
| stats latest(chain_depth) as depth, latest(oldest_snapshot_days) as snapshot_days by host, vm_name, disk
| where depth > 3 OR snapshot_days > 30
| table host vm_name disk depth snapshot_days
| sort -snapshot_days
```

Understanding this SPL

**Virtual Disk Backing Chain and Snapshot Age** — Long snapshot chains and old snapshots degrade I/O and complicate recovery. Monitoring supports snapshot hygiene and prevents runaway growth.

Documented **Data sources**: Libvirt/QEMU disk info. **App/TA** (typical add-on context): Custom scripted input (`virsh domblkinfo`, `qemu-img info`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_disk_chain. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=kvm_disk_chain. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name, disk** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where depth > 3 OR snapshot_days > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Virtual Disk Backing Chain and Snapshot Age**): table host vm_name disk depth snapshot_days
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, disk, depth, oldest snapshot), Bar chart of snapshot age.

## SPL

```spl
index=virtualization sourcetype=kvm_disk_chain host=*
| stats latest(chain_depth) as depth, latest(oldest_snapshot_days) as snapshot_days by host, vm_name, disk
| where depth > 3 OR snapshot_days > 30
| table host vm_name disk depth snapshot_days
| sort -snapshot_days
```

## Visualization

Table (VM, disk, depth, oldest snapshot), Bar chart of snapshot age.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
