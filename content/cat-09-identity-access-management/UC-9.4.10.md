<!-- AUTO-GENERATED from UC-9.4.10.json — DO NOT EDIT -->

---
id: "9.4.10"
title: "Just-in-Time Access Request Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.10 · Just-in-Time Access Request Monitoring

## Description

JIT access reduces standing privilege. Monitoring request and approval patterns ensures policy compliance and detects abuse.

## Value

JIT access reduces standing privilege. Monitoring request and approval patterns ensures policy compliance and detects abuse.

## Implementation

Ingest JIT request and approval events. Alert on excessive requests per user, self-approvals, or access outside business hours. Report on approval latency and denial rate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: PAM / JIT access system logs.
• Ensure the following data sources are available: Access request and approval audit logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest JIT request and approval events. Alert on excessive requests per user, self-approvals, or access outside business hours. Report on approval latency and denial rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="jit:requests"
| stats count, values(approver) as approvers by requester, resource, action
| where count > 20
| sort -count
```

Understanding this SPL

**Just-in-Time Access Request Monitoring** — JIT access reduces standing privilege. Monitoring request and approval patterns ensures policy compliance and detects abuse.

Documented **Data sources**: Access request and approval audit logs. **App/TA** (typical add-on context): PAM / JIT access system logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: jit:requests. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="jit:requests". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by requester, resource, action** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action | sort - count
```

Understanding this CIM / accelerated SPL

**Just-in-Time Access Request Monitoring** — JIT access reduces standing privilege. Monitoring request and approval patterns ensures policy compliance and detects abuse.

Documented **Data sources**: Access request and approval audit logs. **App/TA** (typical add-on context): PAM / JIT access system logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with CyberArk PrivateArk/Password Vault Web Access (or BeyondTrust / vendor console) for the same sessions, vault activity, and alerts.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (request summary), Bar chart (requests by requester), Line chart (approval latency).

## SPL

```spl
index=pam sourcetype="jit:requests"
| stats count, values(approver) as approvers by requester, resource, action
| where count > 20
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action | sort - count
```

## Visualization

Table (request summary), Bar chart (requests by requester), Line chart (approval latency).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
