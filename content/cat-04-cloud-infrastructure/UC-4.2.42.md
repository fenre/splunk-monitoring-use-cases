---
id: "4.2.42"
title: "Azure Monitor Alert Rule Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.42 · Azure Monitor Alert Rule Health

## Description

Disabled or misconfigured alert rules create silent monitoring gaps; tracking rule state protects on-call coverage.

## Value

Disabled or misconfigured alert rules create silent monitoring gaps; tracking rule state protects on-call coverage.

## Implementation

Ingest Activity Log for alert create/update/delete. Nightly compare inventory of enabled rules vs golden baseline lookup. Alert when production-critical rules are disabled > 15 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:audit` (scheduledQueryRules, metricAlerts), Activity Log for alert changes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Activity Log for alert create/update/delete. Nightly compare inventory of enabled rules vs golden baseline lookup. Alert when production-critical rules are disabled > 15 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" (operationName.value="*scheduledQueryRules*" OR operationName.value="*metricAlerts*")
| search disable OR Disabled OR delete OR Delete
| stats count by caller, operationName.value, resourceId
| sort -_time
```

Understanding this SPL

**Azure Monitor Alert Rule Health** — Disabled or misconfigured alert rules create silent monitoring gaps; tracking rule state protects on-call coverage.

Documented **Data sources**: `sourcetype=mscs:azure:audit` (scheduledQueryRules, metricAlerts), Activity Log for alert changes. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by caller, operationName.value, resourceId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, action, caller), Timeline (changes), Single value (disabled rules count).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" (operationName.value="*scheduledQueryRules*" OR operationName.value="*metricAlerts*")
| search disable OR Disabled OR delete OR Delete
| stats count by caller, operationName.value, resourceId
| sort -_time
```

## Visualization

Table (rule, action, caller), Timeline (changes), Single value (disabled rules count).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
