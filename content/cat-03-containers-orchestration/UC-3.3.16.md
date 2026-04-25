<!-- AUTO-GENERATED from UC-3.3.16.json — DO NOT EDIT -->

---
id: "3.3.16"
title: "DeploymentConfig Rollout Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.16 · DeploymentConfig Rollout Failures

## Description

DeploymentConfig rollouts can fail due to image pull errors, readiness probe timeouts, or resource limits. Stalled rollouts leave applications on old versions and consume resources.

## Value

DeploymentConfig rollouts can fail due to image pull errors, readiness probe timeouts, or resource limits. Stalled rollouts leave applications on old versions and consume resources.

## Implementation

Forward OpenShift events filtered for DeploymentConfig-related reasons. Alert on DeploymentFailed, CancelledRollout, or rollouts that remain in progress beyond the configured deadline.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift event forwarding
• Have these sources flowing into Splunk: `sourcetype=kube:events`, `sourcetype=openshift:deploymentconfig`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Forward OpenShift events filtered for DeploymentConfig-related reasons. Alert on DeploymentFailed, CancelledRollout, or rollouts that remain in progress beyond the configured deadline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="kube:events" involvedObject.kind="DeploymentConfig" (reason="DeploymentFailed" OR reason="RollbackDone" OR reason="CancelledRollout")
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```

Understanding this SPL

**DeploymentConfig Rollout Failures** — DeploymentConfig rollouts can fail due to image pull errors, readiness probe timeouts, or resource limits.

Documented **Data sources**: `sourcetype=kube:events`, `sourcetype=openshift:deploymentconfig`. **App/TA** context: OpenShift event forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (DC, namespace, reason, message), Timeline of rollouts, Success rate bar chart.

## SPL

```spl
index=openshift sourcetype="kube:events" involvedObject.kind="DeploymentConfig" (reason="DeploymentFailed" OR reason="RollbackDone" OR reason="CancelledRollout")
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```

## Visualization

Table (DC, namespace, reason, message), Timeline of rollouts, Success rate bar chart.

## References

- [OpenShift DeploymentConfig strategies](https://docs.openshift.com/container-platform/latest/applications/deployments/what-deployments-are.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
