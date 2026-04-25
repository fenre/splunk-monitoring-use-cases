<!-- AUTO-GENERATED from UC-3.3.24.json — DO NOT EDIT -->

---
id: "3.3.24"
title: "MachineHealthCheck Remediations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.24 · MachineHealthCheck Remediations

## Description

MachineHealthChecks automatically remediate unhealthy nodes by deleting and replacing them. Frequent remediations indicate persistent infrastructure problems such as failing hardware, cloud provider issues, or misconfigurations.

## Value

MachineHealthChecks automatically remediate unhealthy nodes by deleting and replacing them. Frequent remediations indicate persistent infrastructure problems such as failing hardware, cloud provider issues, or misconfigurations.

## Implementation

Scripted input: `oc get machinehealthcheck -n openshift-machine-api -o json`. Parse `status.currentHealthy` vs `status.expectedMachines`. Also capture remediation events. Run every 300 seconds. Alert when remediations exceed 2 per hour or currentHealthy < expectedMachines.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get machinehealthcheck -n openshift-machine-api -o json` scripted input, event forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:machinehealthcheck`, `sourcetype=kube:events`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get machinehealthcheck -n openshift-machine-api -o json`. Parse `status.currentHealthy` vs `status.expectedMachines`. Also capture remediation events. Run every 300 seconds. Alert when remediations exceed 2 per hour or currentHealthy < expectedMachines.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift (sourcetype="kube:events" involvedObject.kind="Machine" reason="Remediated") OR (sourcetype="openshift:machinehealthcheck" currentHealthy<expectedMachines)
| stats count as remediations, values(involvedObject.name) as machines by namespace, cluster
| where remediations>0
| sort -remediations
```

Understanding this SPL

**MachineHealthCheck Remediations** — MachineHealthChecks automatically remediate unhealthy nodes by deleting and replacing them.

Documented **Data sources**: `sourcetype=openshift:machinehealthcheck`, `sourcetype=kube:events`. **App/TA** context: `oc get machinehealthcheck -n openshift-machine-api -o json` scripted input, event forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (MHC, healthy, expected, remediations), Timeline of remediation events, Single value (total remediations/24h).

## SPL

```spl
index=openshift (sourcetype="kube:events" involvedObject.kind="Machine" reason="Remediated") OR (sourcetype="openshift:machinehealthcheck" currentHealthy<expectedMachines)
| stats count as remediations, values(involvedObject.name) as machines by namespace, cluster
| where remediations>0
| sort -remediations
```

## Visualization

Table (MHC, healthy, expected, remediations), Timeline of remediation events, Single value (total remediations/24h).

## References

- [OpenShift MachineHealthCheck documentation](https://docs.openshift.com/container-platform/latest/machine_management/deploying-machine-health-checks.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
