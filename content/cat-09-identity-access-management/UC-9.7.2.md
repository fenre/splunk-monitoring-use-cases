<!-- AUTO-GENERATED from UC-9.7.2.json — DO NOT EDIT -->

---
id: "9.7.2"
title: "MFA Adoption Rate Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.7.2 · MFA Adoption Rate Trending

## Description

Tracking the percentage of users enrolled in multi-factor authentication over time proves progress toward zero-trust and regulatory expectations. Flat or declining adoption after rollout indicates gaps in onboarding, excluded groups, or integration problems that leave accounts easier to abuse.

## Value

Tracking the percentage of users enrolled in multi-factor authentication over time proves progress toward zero-trust and regulatory expectations. Flat or declining adoption after rollout indicates gaps in onboarding, excluded groups, or integration problems that leave accounts easier to abuse.

## Implementation

Align field names with your vendor (Okta `mfaFactors`, Duo `is_enrolled`, Entra `strongAuthenticationDetail`). Prefer a daily saved search that snapshots user inventory or use change events if full-state logs are large. Compare adoption_pct to HR onboarding cohorts to find departments lagging behind. Use the same definition of “enrolled” as your security policy for audit evidence.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Okta Add-on for Splunk, Duo Security App for Splunk, Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) (Entra ID reporting).
• Ensure the following data sources are available: `index=okta` `sourcetype` in (`Okta:im`, `OktaIM2`) user objects; `index=duo` `sourcetype=duo:admin` or authentication logs with enrollment fields; Entra ID audit / user detail exports ingested with MFA columns.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Align field names with your vendor (Okta `mfaFactors`, Duo `is_enrolled`, Entra `strongAuthenticationDetail`). Prefer a daily saved search that snapshots user inventory or use change events if full-state logs are large. Compare adoption_pct to HR onboarding cohorts to find departments lagging behind. Use the same definition of “enrolled” as your security policy for audit evidence.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta (sourcetype="Okta:im" OR sourcetype="OktaIM2") objectType=user earliest=-90d@d
| eval has_mfa=if(mvcount('mfaFactors{}.factorType')>0 OR mvcount(mfaFactors)>0 OR like(lower(mfaStatus),"active"),1,0)
| bin _time span=1d
| stats sum(has_mfa) as mfa_enrolled_users, dc(id) as distinct_users by _time
| eval adoption_pct=round(100*mfa_enrolled_users/distinct_users,2)
| sort _time
| trendline sma7(adoption_pct) as adoption_sma7
| predict adoption_pct as adoption_forecast algorithm=LLP future_timespan=14
```

Understanding this SPL

**MFA Adoption Rate Trending** — Tracking the percentage of users enrolled in multi-factor authentication over time proves progress toward zero-trust and regulatory expectations. Flat or declining adoption after rollout indicates gaps in onboarding, excluded groups, or integration problems that leave accounts easier to abuse.

Documented **Data sources**: `index=okta` `sourcetype` in (`Okta:im`, `OktaIM2`) user objects; `index=duo` `sourcetype=duo:admin` or authentication logs with enrollment fields; Entra ID audit / user detail exports ingested with MFA columns. **App/TA** (typical add-on context): Okta Add-on for Splunk, Duo Security App for Splunk, Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) (Entra ID reporting). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: Okta:im, OktaIM2. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="Okta:im", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **has_mfa** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **adoption_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **MFA Adoption Rate Trending**): trendline sma7(adoption_pct) as adoption_sma7
• Pipeline stage (see **MFA Adoption Rate Trending**): predict adoption_pct as adoption_forecast algorithm=LLP future_timespan=14


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single-value with sparkline; line chart of adoption_pct and sma7; stacked bar of enrolled vs not enrolled by day.

## SPL

```spl
index=okta (sourcetype="Okta:im" OR sourcetype="OktaIM2") objectType=user earliest=-90d@d
| eval has_mfa=if(mvcount('mfaFactors{}.factorType')>0 OR mvcount(mfaFactors)>0 OR like(lower(mfaStatus),"active"),1,0)
| bin _time span=1d
| stats sum(has_mfa) as mfa_enrolled_users, dc(id) as distinct_users by _time
| eval adoption_pct=round(100*mfa_enrolled_users/distinct_users,2)
| sort _time
| trendline sma7(adoption_pct) as adoption_sma7
| predict adoption_pct as adoption_forecast algorithm=LLP future_timespan=14
```

## Visualization

Single-value with sparkline; line chart of adoption_pct and sma7; stacked bar of enrolled vs not enrolled by day.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
