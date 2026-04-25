<!-- AUTO-GENERATED from UC-3.3.21.json — DO NOT EDIT -->

---
id: "3.3.21"
title: "ClusterRole and ClusterRoleBinding Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.21 · ClusterRole and ClusterRoleBinding Changes

## Description

Changes to ClusterRoles and ClusterRoleBindings affect cluster-wide RBAC permissions. Unauthorized modifications can grant excessive privileges or create backdoor access.

## Value

Changes to ClusterRoles and ClusterRoleBindings affect cluster-wide RBAC permissions. Unauthorized modifications can grant excessive privileges or create backdoor access.

## Implementation

Enable and forward OpenShift audit logs. Filter for create/update/patch/delete on `clusterroles` and `clusterrolebindings`. Alert on any modification outside of approved change windows or by non-admin users. Cross-reference with change management tickets.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift audit log forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:audit`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Enable and forward OpenShift audit logs. Filter for create/update/patch/delete on `clusterroles` and `clusterrolebindings`. Alert on any modification outside of approved change windows or by non-admin users. Cross-reference with change management tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:audit" (objectRef.resource="clusterroles" OR objectRef.resource="clusterrolebindings") verb!="get" verb!="list" verb!="watch"
| stats count by verb, user.username, objectRef.name, objectRef.resource, responseStatus.code
| sort -count
```

Understanding this SPL

**ClusterRole and ClusterRoleBinding Changes** — Changes to ClusterRoles and ClusterRoleBindings affect cluster-wide RBAC permissions.

Documented **Data sources**: `sourcetype=openshift:audit`. **App/TA** context: OpenShift audit log forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (user, verb, resource, name, status), Timeline of changes, Bar chart by user.

## SPL

```spl
index=openshift sourcetype="openshift:audit" (objectRef.resource="clusterroles" OR objectRef.resource="clusterrolebindings") verb!="get" verb!="list" verb!="watch"
| stats count by verb, user.username, objectRef.name, objectRef.resource, responseStatus.code
| sort -count
```

## Visualization

Table (user, verb, resource, name, status), Timeline of changes, Bar chart by user.

## References

- [OpenShift RBAC documentation](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
