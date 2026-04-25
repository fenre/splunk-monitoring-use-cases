<!-- AUTO-GENERATED from UC-3.3.12.json — DO NOT EDIT -->

---
id: "3.3.12"
title: "Project Resource Quota Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.12 · Project Resource Quota Exhaustion

## Description

OpenShift projects enforce ResourceQuotas for CPU, memory, and pod count. When quotas approach exhaustion, new deployments and scaling operations fail silently.

## Value

OpenShift projects enforce ResourceQuotas for CPU, memory, and pod count. When quotas approach exhaustion, new deployments and scaling operations fail silently.

## Implementation

Scripted input: `oc get resourcequota -A -o json`. Parse `status.hard` and `status.used` for CPU, memory, and pods. Run every 300 seconds. Alert when any resource exceeds 85% of quota.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get resourcequota -A -o json` scripted input
• Have these sources flowing into Splunk: `sourcetype=openshift:resourcequota`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get resourcequota -A -o json`. Parse `status.hard` and `status.used` for CPU, memory, and pods. Run every 300 seconds. Alert when any resource exceeds 85% of quota.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:resourcequota"
| eval cpu_pct=round(used_cpu/hard_cpu*100,1), mem_pct=round(used_memory/hard_memory*100,1), pods_pct=round(used_pods/hard_pods*100,1)
| where cpu_pct>85 OR mem_pct>85 OR pods_pct>85
| table namespace quota_name cpu_pct mem_pct pods_pct
| sort -cpu_pct
```

Understanding this SPL

**Project Resource Quota Exhaustion** — OpenShift projects enforce ResourceQuotas for CPU, memory, and pod count.

Documented **Data sources**: `sourcetype=openshift:resourcequota`. **App/TA** context: `oc get resourcequota -A -o json` scripted input. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (namespace, quota, resource, used, hard, pct), Gauge per resource, Heatmap by namespace.

## SPL

```spl
index=openshift sourcetype="openshift:resourcequota"
| eval cpu_pct=round(used_cpu/hard_cpu*100,1), mem_pct=round(used_memory/hard_memory*100,1), pods_pct=round(used_pods/hard_pods*100,1)
| where cpu_pct>85 OR mem_pct>85 OR pods_pct>85
| table namespace quota_name cpu_pct mem_pct pods_pct
| sort -cpu_pct
```

## Visualization

Table (namespace, quota, resource, used, hard, pct), Gauge per resource, Heatmap by namespace.

## References

- [OpenShift ResourceQuotas documentation](https://docs.openshift.com/container-platform/latest/applications/quotas/quotas-setting-per-project.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
