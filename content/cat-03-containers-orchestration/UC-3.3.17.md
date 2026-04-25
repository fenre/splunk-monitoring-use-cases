<!-- AUTO-GENERATED from UC-3.3.17.json — DO NOT EDIT -->

---
id: "3.3.17"
title: "MachineConfigPool Degradation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.17 · MachineConfigPool Degradation

## Description

MachineConfigPools apply OS-level configuration (kernel args, kubelet config, chrony, SSH keys) to node groups. A degraded MCP means nodes failed to apply the desired config, blocking upgrades and leaving nodes in an inconsistent state.

## Value

MachineConfigPools apply OS-level configuration (kernel args, kubelet config, chrony, SSH keys) to node groups. A degraded MCP means nodes failed to apply the desired config, blocking upgrades and leaving nodes in an inconsistent state.

## Implementation

Scripted input: `oc get mcp -o json`. Parse `status.conditions` for Degraded, Updated, Updating. Extract `machineCount`, `readyMachineCount`, `degradedMachineCount`, `updatedMachineCount`. Run every 300 seconds. Alert when Degraded=True or when Updating=True for more than 60 minutes.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get mcp -o json` scripted input
• Have these sources flowing into Splunk: `sourcetype=openshift:machineconfigpool`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get mcp -o json`. Parse `status.conditions` for Degraded, Updated, Updating. Extract `machineCount`, `readyMachineCount`, `degradedMachineCount`, `updatedMachineCount`. Run every 300 seconds. Alert when Degraded=True or when Updating=True for more than 60 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:machineconfigpool"
| where degraded="True" OR updating="True"
| eval degraded_pct=round(degradedMachineCount/machineCount*100,1)
| table _time cluster pool machineCount readyMachineCount degradedMachineCount degraded_pct updating
| sort -degraded_pct
```

Understanding this SPL

**MachineConfigPool Degradation** — MachineConfigPools apply OS-level configuration (kernel args, kubelet config, chrony, SSH keys) to node groups.

Documented **Data sources**: `sourcetype=openshift:machineconfigpool`. **App/TA** context: `oc get mcp -o json` scripted input. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: MCP status grid (green/yellow/red), Table (pool, machines, ready, degraded), Progress bar for updates.

## SPL

```spl
index=openshift sourcetype="openshift:machineconfigpool"
| where degraded="True" OR updating="True"
| eval degraded_pct=round(degradedMachineCount/machineCount*100,1)
| table _time cluster pool machineCount readyMachineCount degradedMachineCount degraded_pct updating
| sort -degraded_pct
```

## Visualization

MCP status grid (green/yellow/red), Table (pool, machines, ready, degraded), Progress bar for updates.

## References

- [OpenShift MachineConfig Operator documentation](https://docs.openshift.com/container-platform/latest/post_installation_configuration/machine-configuration-tasks.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
