<!-- AUTO-GENERATED from UC-9.1.23.json — DO NOT EDIT -->

---
id: "9.1.23"
title: "Entra PIM Activation Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.23 · Entra PIM Activation Audit

## Description

Privileged Identity Management activations grant time-bound admin roles; auditing ensures approvals and detects abuse.

## Value

Privileged Identity Management activations grant time-bound admin roles; auditing ensures approvals and detects abuse.

## Implementation

Ingest PIM-related audit events. Alert on activations outside business hours, without ticket ID (custom field), or for highly privileged roles. Report monthly for access reviews.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra audit logs (`Add member to role completed`, PIM `RequestApproved` / `RoleAssignmentSchedule`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest PIM-related audit events. Alert on activations outside business hours, without ticket ID (custom field), or for highly privileged roles. Report monthly for access reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:audit"
| search "PIM" OR activityDisplayName IN ("Add member to role in PIM completed","Add member to role completed")
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, result, activityDisplayName
| sort -_time
```

Understanding this SPL

**Entra PIM Activation Audit** — Privileged Identity Management activations grant time-bound admin roles; auditing ensures approvals and detects abuse.

Documented **Data sources**: Entra audit logs (`Add member to role completed`, PIM `RequestApproved` / `RoleAssignmentSchedule`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Entra PIM Activation Audit**): table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, result, activityDisplayName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Entra PIM Activation Audit** — Privileged Identity Management activations grant time-bound admin roles; auditing ensures approvals and detects abuse.

Documented **Data sources**: Entra audit logs (`Add member to role completed`, PIM `RequestApproved` / `RoleAssignmentSchedule`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Entra ID sign-in and audit logs in the Microsoft Entra or Azure portal for the same users, resources, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (activations), Bar chart (role activations by user), Timeline.

## SPL

```spl
index=azure sourcetype="azure:aad:audit"
| search "PIM" OR activityDisplayName IN ("Add member to role in PIM completed","Add member to role completed")
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, result, activityDisplayName
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (activations), Bar chart (role activations by user), Timeline.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
