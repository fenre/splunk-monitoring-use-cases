<!-- AUTO-GENERATED from UC-2.3.4.json — DO NOT EDIT -->

---
id: "2.3.4"
title: "KVM Guest Agent Heartbeat"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.3.4 · KVM Guest Agent Heartbeat

## Description

Guest agent (QEMU GA) unavailability prevents graceful shutdown, snapshot consistency, and time sync. Detecting agent loss ensures proper VM management.

## Value

Guest agent (QEMU GA) unavailability prevents graceful shutdown, snapshot consistency, and time sync. Detecting agent loss ensures proper VM management.

## Implementation

Script that iterates VMs and runs `virsh qemu-agent-command <domain> '{"execute":"guest-ping"}'`. Ingest result (0/1) per VM. Run every 60 seconds. Alert when agent stops responding.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (virsh qemu-agent-command).
• Ensure the following data sources are available: `virsh qemu-agent-command <vm> '{"execute":"guest-ping"}'`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Script that iterates VMs and runs `virsh qemu-agent-command <domain> '{"execute":"guest-ping"}'`. Ingest result (0/1) per VM. Run every 60 seconds. Alert when agent stops responding.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=kvm_guest_agent host=*
| stats latest(agent_ok) as ok by host, vm_name
| where ok != 1
| table host vm_name _time
```

Understanding this SPL

**KVM Guest Agent Heartbeat** — Guest agent (QEMU GA) unavailability prevents graceful shutdown, snapshot consistency, and time sync. Detecting agent loss ensures proper VM management.

Documented **Data sources**: `virsh qemu-agent-command <vm> '{"execute":"guest-ping"}'`. **App/TA** (typical add-on context): Custom scripted input (virsh qemu-agent-command). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_guest_agent. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=kvm_guest_agent. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where ok != 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **KVM Guest Agent Heartbeat**): table host vm_name _time

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (VM vs. agent OK), Table of VMs with no agent.

## SPL

```spl
index=virtualization sourcetype=kvm_guest_agent host=*
| stats latest(agent_ok) as ok by host, vm_name
| where ok != 1
| table host vm_name _time
```

## Visualization

Status grid (VM vs. agent OK), Table of VMs with no agent.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
