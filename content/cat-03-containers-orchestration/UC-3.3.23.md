<!-- AUTO-GENERATED from UC-3.3.23.json — DO NOT EDIT -->

---
id: "3.3.23"
title: "Console and API Access Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.3.23 · Console and API Access Audit

## Description

Tracking who accesses the OpenShift console and API, from where, and what actions they perform provides a complete audit trail for compliance and security investigations.

## Value

Tracking who accesses the OpenShift console and API, from where, and what actions they perform provides a complete audit trail for compliance and security investigations.

## Implementation

Forward OpenShift audit logs. Filter out system service accounts. Distinguish console users (browser user-agent) from CLI/API users. Track source IPs per user. Alert on access from unexpected locations or outside business hours.

## Detailed Implementation

Prerequisites
• Install and configure: OpenShift audit log forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:audit`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Forward OpenShift audit logs. Filter out system service accounts. Distinguish console users (browser user-agent) from CLI/API users. Track source IPs per user. Alert on access from unexpected locations or outside business hours.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:audit"
| where NOT match('user.username', "^system:")
| stats count, dc(sourceIPs{}) as unique_ips, values(verb) as verbs by user.username, userAgent
| eval is_console=if(match(userAgent,"Mozilla"),"console","cli/api")
| sort -count
```

Understanding this SPL

**Console and API Access Audit** — Tracking who accesses the OpenShift console and API, from where, and what actions they perform provides a complete audit trail for compliance and security investigations.

Documented **Data sources**: `sourcetype=openshift:audit`. **App/TA** context: OpenShift audit log forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (user, access type, IPs, action count), Timechart (access patterns), Sankey (user to action).

## SPL

```spl
index=openshift sourcetype="openshift:audit"
| where NOT match('user.username', "^system:")
| stats count, dc(sourceIPs{}) as unique_ips, values(verb) as verbs by user.username, userAgent
| eval is_console=if(match(userAgent,"Mozilla"),"console","cli/api")
| sort -count
```

## Visualization

Table (user, access type, IPs, action count), Timechart (access patterns), Sankey (user to action).

## References

- [OpenShift audit log policy](https://docs.openshift.com/container-platform/latest/security/audit-log-policy-config.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
