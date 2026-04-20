---
id: "3.2.12"
title: "RBAC Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.12 · RBAC Audit

## Description

RBAC misconfigurations grant excessive permissions. Unauthorized access attempts indicate potential compromise or misconfigured service accounts.

## Value

RBAC misconfigurations grant excessive permissions. Unauthorized access attempts indicate potential compromise or misconfigured service accounts.

## Implementation

Enable Kubernetes audit logging (audit policy file). Forward audit logs to Splunk. Alert on 403 Forbidden responses, especially from service accounts. Track RBAC changes (ClusterRole, ClusterRoleBinding modifications).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes audit log forwarding.
• Ensure the following data sources are available: `sourcetype=kube:audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Kubernetes audit logging (audit policy file). Forward audit logs to Splunk. Alert on 403 Forbidden responses, especially from service accounts. Track RBAC changes (ClusterRole, ClusterRoleBinding modifications).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:audit" responseStatus.code>=403
| stats count by user.username, verb, objectRef.resource, objectRef.namespace
| sort -count
```

Understanding this SPL

**RBAC Audit** — RBAC misconfigurations grant excessive permissions. Unauthorized access attempts indicate potential compromise or misconfigured service accounts.

Documented **Data sources**: `sourcetype=kube:audit`. **App/TA** (typical add-on context): Kubernetes audit log forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by user.username, verb, objectRef.resource, objectRef.namespace** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, resource, verb, denials), Bar chart by user, Timeline.

## SPL

```spl
index=k8s sourcetype="kube:audit" responseStatus.code>=403
| stats count by user.username, verb, objectRef.resource, objectRef.namespace
| sort -count
```

## Visualization

Table (user, resource, verb, denials), Bar chart by user, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
