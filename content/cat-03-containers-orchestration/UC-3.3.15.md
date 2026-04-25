<!-- AUTO-GENERATED from UC-3.3.15.json — DO NOT EDIT -->

---
id: "3.3.15"
title: "OAuth Access Token Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.15 · OAuth Access Token Audit

## Description

OpenShift OAuth tokens grant API access. Tracking token creation and deletion reveals unauthorized access attempts, service account abuse, or compromised credentials.

## Value

OpenShift OAuth tokens grant API access. Tracking token creation and deletion reveals unauthorized access attempts, service account abuse, or compromised credentials.

## Implementation

Enable and forward OpenShift audit logs (API server audit policy). Filter for `oauthaccesstokens` and `oauthauthorizetokens` resource operations. Alert on unusual token creation volume, token creation from unexpected IPs, or bulk token deletions.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift audit log forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:audit`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Enable and forward OpenShift audit logs (API server audit policy). Filter for `oauthaccesstokens` and `oauthauthorizetokens` resource operations. Alert on unusual token creation volume, token creation from unexpected IPs, or bulk token deletions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:audit" (objectRef.resource="oauthaccesstokens" OR objectRef.resource="oauthauthorizetokens")
| stats count by verb, user.username, sourceIPs{}, responseStatus.code
| where verb="create" OR verb="delete"
| sort -count
```

Understanding this SPL

**OAuth Access Token Audit** — OpenShift OAuth tokens grant API access.

Documented **Data sources**: `sourcetype=openshift:audit`. **App/TA** context: OpenShift audit log forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (user, verb, source IP, status), Timechart (token creates/deletes), Bar chart by user.

## SPL

```spl
index=openshift sourcetype="openshift:audit" (objectRef.resource="oauthaccesstokens" OR objectRef.resource="oauthauthorizetokens")
| stats count by verb, user.username, sourceIPs{}, responseStatus.code
| where verb="create" OR verb="delete"
| sort -count
```

## Visualization

Table (user, verb, source IP, status), Timechart (token creates/deletes), Bar chart by user.

## References

- [OpenShift OAuth configuration](https://docs.openshift.com/container-platform/latest/authentication/understanding-authentication.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
