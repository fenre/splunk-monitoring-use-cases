<!-- AUTO-GENERATED from UC-2.3.13.json — DO NOT EDIT -->

---
id: "2.3.13"
title: "Proxmox HA Group and Fence Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.3.13 · Proxmox HA Group and Fence Status

## Description

Proxmox HA automatically restarts VMs on surviving nodes when a host fails. If the HA manager cannot fence (isolate) a failed node, it cannot safely restart VMs — risking split-brain with shared storage. Monitoring HA state, fence status, and migration events ensures the safety net actually works.

## Value

Proxmox HA automatically restarts VMs on surviving nodes when a host fails. If the HA manager cannot fence (isolate) a failed node, it cannot safely restart VMs — risking split-brain with shared storage. Monitoring HA state, fence status, and migration events ensures the safety net actually works.

## Implementation

Create scripted input: `ha-manager status` to enumerate all HA-managed resources and their states. Monitor HA manager log (`/var/log/pve/ha-manager/`) for fence operations and migration events. Alert on failed fencing (node isolation), VMs in error state, and HA resources that cannot reach their requested state.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, syslog.
• Ensure the following data sources are available: Proxmox HA manager logs, `ha-manager status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `ha-manager status` to enumerate all HA-managed resources and their states. Monitor HA manager log (`/var/log/pve/ha-manager/`) for fence operations and migration events. Alert on failed fencing (node isolation), VMs in error state, and HA resources that cannot reach their requested state.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="proxmox_ha"
| stats latest(ha_state) as state, latest(node) as current_node, latest(request_state) as requested by vm_id, vm_name
| where state!="started" OR state!=requested
| table vm_id, vm_name, state, requested, current_node
```

Understanding this SPL

**Proxmox HA Group and Fence Status** — Proxmox HA automatically restarts VMs on surviving nodes when a host fails. If the HA manager cannot fence (isolate) a failed node, it cannot safely restart VMs — risking split-brain with shared storage. Monitoring HA state, fence status, and migration events ensures the safety net actually works.

Documented **Data sources**: Proxmox HA manager logs, `ha-manager status`. **App/TA** (typical add-on context): Custom scripted input, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: proxmox_ha. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="proxmox_ha". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_id, vm_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where state!="started" OR state!=requested` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Proxmox HA Group and Fence Status**): table vm_id, vm_name, state, requested, current_node

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (HA resources, state, node), Timeline (HA events), Status grid (resource health).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=virtualization sourcetype="proxmox_ha"
| stats latest(ha_state) as state, latest(node) as current_node, latest(request_state) as requested by vm_id, vm_name
| where state!="started" OR state!=requested
| table vm_id, vm_name, state, requested, current_node
```

## Visualization

Table (HA resources, state, node), Timeline (HA events), Status grid (resource health).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
