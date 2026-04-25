<!-- AUTO-GENERATED from UC-9.2.5.json — DO NOT EDIT -->

---
id: "9.2.5"
title: "Azure AD / Entra ID Conditional Access Policy Evaluation Failures"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.2.5 · Azure AD / Entra ID Conditional Access Policy Evaluation Failures

## Description

Policy conflicts causing access denials; helps fine-tune conditional access and reduce user friction.

## Value

Policy conflicts causing access denials; helps fine-tune conditional access and reduce user friction.

## Implementation

Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Parse appliedConditionalAccessPolicies array for policy names and results. Alert on spikes in failures per policy. Track reportOnlyNotApplied for policy tuning. Correlate with userPrincipalName and appDisplayName to identify affected users and apps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`).
• Ensure the following data sources are available: Azure AD Sign-in logs (conditionalAccessStatus, appliedConditionalAccessPolicies).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Parse appliedConditionalAccessPolicies array for policy names and results. Alert on spikes in failures per policy. Track reportOnlyNotApplied for policy tuning. Correlate with userPrincipalName and appDisplayName to identify affected users and apps.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:signin"
| where conditionalAccessStatus="failure" OR conditionalAccessStatus="reportOnlyNotApplied"
| spath path=conditionalAccessPolicies{}
| mvexpand conditionalAccessPolicies{} limit=500
| spath input=conditionalAccessPolicies{} path=displayName
| spath input=conditionalAccessPolicies{} path=result
| where result="failure" OR result="reportOnlyNotApplied"
| stats count by displayName, result
| sort -count
```

Understanding this SPL

**Azure AD / Entra ID Conditional Access Policy Evaluation Failures** — Policy conflicts causing access denials; helps fine-tune conditional access and reduce user friction.

Documented **Data sources**: Azure AD Sign-in logs (conditionalAccessStatus, appliedConditionalAccessPolicies). **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:signin. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:signin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where conditionalAccessStatus="failure" OR conditionalAccessStatus="reportOnlyNotApplied"` — typically the threshold or rule expression for this monitoring goal.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where result="failure" OR result="reportOnlyNotApplied"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by displayName, result** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Azure AD / Entra ID Conditional Access Policy Evaluation Failures** — Policy conflicts causing access denials; helps fine-tune conditional access and reduce user friction.

Documented **Data sources**: Azure AD Sign-in logs (conditionalAccessStatus, appliedConditionalAccessPolicies). **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Entra ID sign-in and audit logs in the Microsoft Entra or Azure portal for the same users, resources, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failures by policy), Table (blocked users with policy details), Line chart (failure rate trend), Pie chart (failures by application).

## SPL

```spl
index=azure sourcetype="azure:aad:signin"
| where conditionalAccessStatus="failure" OR conditionalAccessStatus="reportOnlyNotApplied"
| spath path=conditionalAccessPolicies{}
| mvexpand conditionalAccessPolicies{} limit=500
| spath input=conditionalAccessPolicies{} path=displayName
| spath input=conditionalAccessPolicies{} path=result
| where result="failure" OR result="reportOnlyNotApplied"
| stats count by displayName, result
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Bar chart (failures by policy), Table (blocked users with policy details), Line chart (failure rate trend), Pie chart (failures by application).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
