<!-- AUTO-GENERATED from UC-3.3.14.json — DO NOT EDIT -->

---
id: "3.3.14"
title: "Node NotReady Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.14 · Node NotReady Detection

## Description

Nodes transitioning to NotReady, SchedulingDisabled, or reporting disk/memory/PID pressure cause pod evictions and workload disruption across the cluster.

## Value

Nodes transitioning to NotReady, SchedulingDisabled, or reporting disk/memory/PID pressure cause pod evictions and workload disruption across the cluster.

## Implementation

Scripted input: `oc get nodes -o json`. Parse `status.conditions` for Ready, MemoryPressure, DiskPressure, PIDPressure. Run every 120 seconds. Alert immediately when any node is NotReady or reporting pressure conditions.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get nodes -o json` scripted input
• Have these sources flowing into Splunk: `sourcetype=openshift:node`, `sourcetype=kube:events`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get nodes -o json`. Parse `status.conditions` for Ready, MemoryPressure, DiskPressure, PIDPressure. Run every 120 seconds. Alert immediately when any node is NotReady or reporting pressure conditions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:node"
| where status!="Ready"
| stats latest(status) as status, latest(reason) as reason, count by cluster, node, role
| sort cluster, node
```

Understanding this SPL

**Node NotReady Detection** — Nodes transitioning to NotReady, SchedulingDisabled, or reporting disk/memory/PID pressure cause pod evictions and workload disruption across the cluster.

Documented **Data sources**: `sourcetype=openshift:node`, `sourcetype=kube:events`. **App/TA** context: `oc get nodes -o json` scripted input. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Node status grid (green/yellow/red), Table (node, role, status, reason), Timeline.

## SPL

```spl
index=openshift sourcetype="openshift:node"
| where status!="Ready"
| stats latest(status) as status, latest(reason) as reason, count by cluster, node, role
| sort cluster, node
```

## Visualization

Node status grid (green/yellow/red), Table (node, role, status, reason), Timeline.

## References

- [OpenShift Node health documentation](https://docs.openshift.com/container-platform/latest/nodes/nodes/nodes-nodes-viewing.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
