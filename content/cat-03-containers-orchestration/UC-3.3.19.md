<!-- AUTO-GENERATED from UC-3.3.19.json — DO NOT EDIT -->

---
id: "3.3.19"
title: "Ingress Controller Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.19 · Ingress Controller Errors

## Description

The OpenShift Ingress Controller (HAProxy-based router) handles all external traffic into the cluster. 5xx errors, backend connection failures, and route misconfigurations directly impact application availability.

## Value

The OpenShift Ingress Controller (HAProxy-based router) handles all external traffic into the cluster. 5xx errors, backend connection failures, and route misconfigurations directly impact application availability.

## Implementation

Forward HAProxy access logs from the router pods or expose HAProxy stats. Parse status codes, backend names, and response times. Alert when 5xx error rate exceeds threshold per backend. Also monitor IngressController object for Degraded condition.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift HAProxy log forwarding, `oc get ingresscontroller -n openshift-ingress-operator -o json` scripted input
• Have these sources flowing into Splunk: `sourcetype=openshift:haproxy`, `sourcetype=openshift:ingresscontroller`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Forward HAProxy access logs from the router pods or expose HAProxy stats. Parse status codes, backend names, and response times. Alert when 5xx error rate exceeds threshold per backend. Also monitor IngressController object for Degraded condition.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:haproxy"
| where status_code>=500
| bin _time span=5m
| stats count as errors by backend_name, status_code, _time
| where errors>10
| sort -errors
```

Understanding this SPL

**Ingress Controller Errors** — The OpenShift Ingress Controller (HAProxy-based router) handles all external traffic into the cluster.

Documented **Data sources**: `sourcetype=openshift:haproxy`, `sourcetype=openshift:ingresscontroller`. **App/TA** context: OpenShift HAProxy log forwarding, `oc get ingresscontroller -n openshift-ingress-operator -o json` scripted input. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Timechart (5xx rate by backend), Table (backend, status, count), Error rate single value.

## SPL

```spl
index=openshift sourcetype="openshift:haproxy"
| where status_code>=500
| bin _time span=5m
| stats count as errors by backend_name, status_code, _time
| where errors>10
| sort -errors
```

## Visualization

Timechart (5xx rate by backend), Table (backend, status, count), Error rate single value.

## References

- [OpenShift Ingress Operator documentation](https://docs.openshift.com/container-platform/latest/networking/ingress-operator.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
