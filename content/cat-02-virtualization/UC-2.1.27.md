---
id: "2.1.27"
title: "VM Disk Consolidation Needed"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.27 · VM Disk Consolidation Needed

## Description

After a failed snapshot deletion, VMs can have orphaned delta disks that keep growing and degrading I/O performance. The "consolidation needed" flag indicates the disk chain is broken and needs manual intervention before it causes datastore exhaustion.

## Value

After a failed snapshot deletion, VMs can have orphaned delta disks that keep growing and degrading I/O performance. The "consolidation needed" flag indicates the disk chain is broken and needs manual intervention before it causes datastore exhaustion.

## Implementation

Collected via Splunk_TA_vmware inventory. Alert immediately on any VM with consolidationNeeded=true. Consolidation should be performed during low-I/O periods as it can temporarily stun the VM. Track datastore free space for affected VMs as orphaned deltas grow continuously.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via Splunk_TA_vmware inventory. Alert immediately on any VM with consolidationNeeded=true. Consolidation should be performed during low-I/O periods as it can temporarily stun the VM. Track datastore free space for affected VMs as orphaned deltas grow continuously.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" consolidationNeeded="true"
| table vm_name, host, datastore, consolidationNeeded
| sort vm_name
```

Understanding this SPL

**VM Disk Consolidation Needed** — After a failed snapshot deletion, VMs can have orphaned delta disks that keep growing and degrading I/O performance. The "consolidation needed" flag indicates the disk chain is broken and needs manual intervention before it causes datastore exhaustion.

Documented **Data sources**: `sourcetype=vmware:inv:vm`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **VM Disk Consolidation Needed**): table vm_name, host, datastore, consolidationNeeded
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VMs needing consolidation), Single value (count), Status indicator.

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" consolidationNeeded="true"
| table vm_name, host, datastore, consolidationNeeded
| sort vm_name
```

## Visualization

Table (VMs needing consolidation), Single value (count), Status indicator.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
