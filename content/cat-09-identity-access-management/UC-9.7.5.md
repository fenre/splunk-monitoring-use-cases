<!-- AUTO-GENERATED from UC-9.7.5.json — DO NOT EDIT -->

---
id: "9.7.5"
title: "Conditional Access Policy Block Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.7.5 · Conditional Access Policy Block Trending

## Description

Tracking which conditional access policies block the most sign-ins over time shows whether controls are too strict, mis-targeted, or under attack. Policy-level trends support tuning reviews and prove enforcement for audits without relying on one-off investigations.

## Value

Tracking which conditional access policies block the most sign-ins over time shows whether controls are too strict, mis-targeted, or under attack. Policy-level trends support tuning reviews and prove enforcement for audits without relying on one-off investigations.

## Implementation

Ensure sign-in logs include conditional access evaluation results (license and diagnostic settings in Entra). Expand `policy_name` with `mvexpand` if you need each policy in a multi-policy evaluation. Review top blockers monthly with app owners; correlate spikes with device compliance changes or new locations. Document exclusions for break-glass and service principals separately.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Microsoft Azure Add-on.
• Ensure the following data sources are available: `index=azure` or `index=mscs` `sourcetype="azure:aad:signin"` (fields such as `conditionalAccessStatus`, `conditionalAccessPolicies`, `status.errorCode`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure sign-in logs include conditional access evaluation results (license and diagnostic settings in Entra). Expand `policy_name` with `mvexpand` if you need each policy in a multi-policy evaluation. Review top blockers monthly with app owners; correlate spikes with device compliance changes or new locations. Document exclusions for break-glass and service principals separately.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:signin" earliest=-90d@d
| search conditionalAccessStatus="failure" OR status.errorCode="53003"
| eval policy_name=mvindex('conditionalAccessPolicies{}.displayName',0)
| fillnull value="unknown_policy" policy_name
| bin _time span=1d
| stats count as block_count by _time, policy_name
| timechart span=1d sum(block_count) by policy_name useother=f limit=10
| appendcols [
    search index=azure sourcetype="azure:aad:signin" earliest=-90d@d
      conditionalAccessStatus="failure" OR status.errorCode="53003"
    | bin _time span=1d
    | stats count as daily_ca_blocks by _time
    | trendline sma7(daily_ca_blocks) as daily_ca_blocks_sma7
  ]
```

Understanding this SPL

**Conditional Access Policy Block Trending** — Tracking which conditional access policies block the most sign-ins over time shows whether controls are too strict, mis-targeted, or under attack. Policy-level trends support tuning reviews and prove enforcement for audits without relying on one-off investigations.

Documented **Data sources**: `index=azure` or `index=mscs` `sourcetype="azure:aad:signin"` (fields such as `conditionalAccessStatus`, `conditionalAccessPolicies`, `status.errorCode`). **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Microsoft Azure Add-on. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:signin. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:signin", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **policy_name** — often to normalize units, derive a ratio, or prepare for thresholds.
• Fills null values with `fillnull`.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, policy_name** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by policy_name useother=f limit=10** — ideal for trending and alerting on this use case.
• Adds columns from a subsearch with `appendcols`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Conditional Access Policy Block Trending** — Tracking which conditional access policies block the most sign-ins over time shows whether controls are too strict, mis-targeted, or under attack. Policy-level trends support tuning reviews and prove enforcement for audits without relying on one-off investigations.

Documented **Data sources**: `index=azure` or `index=mscs` `sourcetype="azure:aad:signin"` (fields such as `conditionalAccessStatus`, `conditionalAccessPolicies`, `status.errorCode`). **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Microsoft Azure Add-on. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Entra ID sign-in and audit logs in the Microsoft Entra or Azure portal for the same users, resources, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area or line chart per policy; heatmap of policy vs week for executive summaries.

## SPL

```spl
index=azure sourcetype="azure:aad:signin" earliest=-90d@d
| search conditionalAccessStatus="failure" OR status.errorCode="53003"
| eval policy_name=mvindex('conditionalAccessPolicies{}.displayName',0)
| fillnull value="unknown_policy" policy_name
| bin _time span=1d
| stats count as block_count by _time, policy_name
| timechart span=1d sum(block_count) by policy_name useother=f limit=10
| appendcols [
    search index=azure sourcetype="azure:aad:signin" earliest=-90d@d
      conditionalAccessStatus="failure" OR status.errorCode="53003"
    | bin _time span=1d
    | stats count as daily_ca_blocks by _time
    | trendline sma7(daily_ca_blocks) as daily_ca_blocks_sma7
  ]
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=1d | sort - count
```

## Visualization

Stacked area or line chart per policy; heatmap of policy vs week for executive summaries.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
