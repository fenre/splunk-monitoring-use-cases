---
id: "5.9.48"
title: "ThousandEyes Activity Log Audit Trail"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.9.48 · ThousandEyes Activity Log Audit Trail

## Description

Ingests ThousandEyes platform activity logs into Splunk for audit, compliance, and change tracking. Tracks who created, modified, or deleted tests, users, and alert rules — essential for troubleshooting test behavior changes and meeting compliance requirements.

## Value

Ingests ThousandEyes platform activity logs into Splunk for audit, compliance, and change tracking. Tracks who created, modified, or deleted tests, users, and alert rules — essential for troubleshooting test behavior changes and meeting compliance requirements.

## Implementation

Configure the Activity Log input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Activity logs are fetched at a configurable interval via the ThousandEyes API. Update the `activity_index` macro to point to the correct index. Events include test creation/modification/deletion, user management, alert rule changes, and account group configuration changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Activity Log API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure the Activity Log input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Activity logs are fetched at a configurable interval via the ThousandEyes API. Update the `activity_index` macro to point to the correct index. Events include test creation/modification/deletion, user management, alert rule changes, and account group configuration changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`activity_index`
| stats count by event, accountGroupName, aid
| sort -count
```

Understanding this SPL

**ThousandEyes Activity Log Audit Trail** — Ingests ThousandEyes platform activity logs into Splunk for audit, compliance, and change tracking. Tracks who created, modified, or deleted tests, users, and alert rules — essential for troubleshooting test behavior changes and meeting compliance requirements.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Activity Log API. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `activity_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by event, accountGroupName, aid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (event type, account group, count), Timeline (activity events), Pie chart (activity by event type).

## SPL

```spl
`activity_index`
| stats count by event, accountGroupName, aid
| sort -count
```

## Visualization

Table (event type, account group, count), Timeline (activity events), Pie chart (activity by event type).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
