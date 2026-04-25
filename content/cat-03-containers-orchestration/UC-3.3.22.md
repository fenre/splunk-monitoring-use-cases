<!-- AUTO-GENERATED from UC-3.3.22.json — DO NOT EDIT -->

---
id: "3.3.22"
title: "Pod Security Admission Violations"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.22 · Pod Security Admission Violations

## Description

Pod Security Admission (PSA) replaced PodSecurityPolicies in OpenShift 4.12+. Violations of baseline or restricted profiles indicate workloads requesting disallowed capabilities such as privileged containers, host networking, or writable root filesystems.

## Value

Pod Security Admission (PSA) replaced PodSecurityPolicies in OpenShift 4.12+. Violations of baseline or restricted profiles indicate workloads requesting disallowed capabilities such as privileged containers, host networking, or writable root filesystems.

## Implementation

Forward OpenShift audit logs. Filter for pod create events containing PSA violation annotations. Track violations by namespace and user. Alert on enforce-mode rejections and audit/warn-mode violations for trend analysis.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift audit log forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:audit`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Forward OpenShift audit logs. Filter for pod create events containing PSA violation annotations. Track violations by namespace and user. Alert on enforce-mode rejections and audit/warn-mode violations for trend analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:audit" objectRef.resource="pods" verb="create"
| search "pod-security.kubernetes.io" ("violat*" OR "would have been")
| stats count by user.username, objectRef.namespace, 'annotations.pod-security.kubernetes.io/audit-violations'
| sort -count
```

Understanding this SPL

**Pod Security Admission Violations** — Pod Security Admission (PSA) replaced PodSecurityPolicies in OpenShift 4.

Documented **Data sources**: `sourcetype=openshift:audit`. **App/TA** context: OpenShift audit log forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (namespace, user, violation), Bar chart by violation type, Timechart trend.

## SPL

```spl
index=openshift sourcetype="openshift:audit" objectRef.resource="pods" verb="create"
| search "pod-security.kubernetes.io" ("violat*" OR "would have been")
| stats count by user.username, objectRef.namespace, 'annotations.pod-security.kubernetes.io/audit-violations'
| sort -count
```

## Visualization

Table (namespace, user, violation), Bar chart by violation type, Timechart trend.

## References

- [OpenShift Pod Security Admission](https://docs.openshift.com/container-platform/latest/authentication/understanding-and-managing-pod-security-admission.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
