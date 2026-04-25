<!-- AUTO-GENERATED from UC-3.3.25.json — DO NOT EDIT -->

---
id: "3.3.25"
title: "LimitRange Enforcement Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.25 · LimitRange Enforcement Tracking

## Description

LimitRanges set default and maximum resource requests/limits per container or pod in a namespace. When workloads are rejected for exceeding these limits, deployments fail. Tracking enforcement events helps teams right-size their resource requests.

## Value

LimitRanges set default and maximum resource requests/limits per container or pod in a namespace. When workloads are rejected for exceeding these limits, deployments fail. Tracking enforcement events helps teams right-size their resource requests.

## Implementation

Forward OpenShift events. Filter for FailedCreate events with LimitRange or quota-related messages. Also periodically export LimitRange definitions to compare against actual workload requests. Alert on repeated failures per namespace.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get limitrange -A -o json` scripted input, event forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:limitrange`, `sourcetype=kube:events`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Forward OpenShift events. Filter for FailedCreate events with LimitRange or quota-related messages. Also periodically export LimitRange definitions to compare against actual workload requests. Alert on repeated failures per namespace.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="kube:events" reason="FailedCreate"
| search "forbidden: exceeded quota" OR "must be less than or equal to" OR "LimitRange"
| stats count by namespace, involvedObject.kind, involvedObject.name, message
| sort -count
```

Understanding this SPL

**LimitRange Enforcement Tracking** — LimitRanges set default and maximum resource requests/limits per container or pod in a namespace.

Documented **Data sources**: `sourcetype=openshift:limitrange`, `sourcetype=kube:events`. **App/TA** context: `oc get limitrange -A -o json` scripted input, event forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (namespace, workload, message), Bar chart by namespace, Timeline of rejections.

## SPL

```spl
index=openshift sourcetype="kube:events" reason="FailedCreate"
| search "forbidden: exceeded quota" OR "must be less than or equal to" OR "LimitRange"
| stats count by namespace, involvedObject.kind, involvedObject.name, message
| sort -count
```

## Visualization

Table (namespace, workload, message), Bar chart by namespace, Timeline of rejections.

## References

- [OpenShift LimitRange documentation](https://docs.openshift.com/container-platform/latest/nodes/clusters/nodes-cluster-limit-ranges.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
