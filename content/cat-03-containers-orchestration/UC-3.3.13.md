<!-- AUTO-GENERATED from UC-3.3.13.json — DO NOT EDIT -->

---
id: "3.3.13"
title: "MachineSet Scaling Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.13 · MachineSet Scaling Failures

## Description

MachineSets control node scaling in IPI clusters. When desired replicas diverge from ready/available counts, new machines may be stuck provisioning, failing cloud API calls, or hitting infrastructure limits.

## Value

MachineSets control node scaling in IPI clusters. When desired replicas diverge from ready/available counts, new machines may be stuck provisioning, failing cloud API calls, or hitting infrastructure limits.

## Implementation

Scripted input: `oc get machineset -n openshift-machine-api -o json`. Parse `spec.replicas`, `status.readyReplicas`, `status.availableReplicas`. Run every 300 seconds. Alert when replicas != readyReplicas for more than 15 minutes.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get machineset -n openshift-machine-api -o json` scripted input
• Have these sources flowing into Splunk: `sourcetype=openshift:machineset`, `sourcetype=kube:events`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get machineset -n openshift-machine-api -o json`. Parse `spec.replicas`, `status.readyReplicas`, `status.availableReplicas`. Run every 300 seconds. Alert when replicas != readyReplicas for more than 15 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:machineset"
| where replicas!=readyReplicas OR replicas!=availableReplicas
| eval gap=replicas-readyReplicas
| table _time cluster machineset namespace replicas readyReplicas gap
| sort -gap
```

Understanding this SPL

**MachineSet Scaling Failures** — MachineSets control node scaling in IPI clusters.

Documented **Data sources**: `sourcetype=openshift:machineset`, `sourcetype=kube:events`. **App/TA** context: `oc get machineset -n openshift-machine-api -o json` scripted input. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (machineset, desired, ready, gap), Single value (total gap), Timeline of scaling events.

## SPL

```spl
index=openshift sourcetype="openshift:machineset"
| where replicas!=readyReplicas OR replicas!=availableReplicas
| eval gap=replicas-readyReplicas
| table _time cluster machineset namespace replicas readyReplicas gap
| sort -gap
```

## Visualization

Table (machineset, desired, ready, gap), Single value (total gap), Timeline of scaling events.

## References

- [OpenShift Machine management documentation](https://docs.openshift.com/container-platform/latest/machine_management/index.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
