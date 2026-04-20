---
id: "9.5.2"
title: "Okta MFA Bypass Attempts"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.2 · Okta MFA Bypass Attempts

## Description

Attempts to skip or weaken MFA (policy gaps, risky grant flows) are a direct path to account takeover; monitoring policy evaluation outcomes closes that gap.

## Value

Attempts to skip or weaken MFA (policy gaps, risky grant flows) are a direct path to account takeover; monitoring policy evaluation outcomes closes that gap.

## Implementation

Track sign-on policy evaluations where MFA was not satisfied or only password was used. Tune to your org’s allowed “password-only” apps and break-glass accounts. Alert on unexpected ALLOW without MFA for protected apps. Review `policy.evaluate_sign_on` with `outcome.result` and debug fields.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`policy.evaluate_sign_on`, `user.authentication`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track sign-on policy evaluations where MFA was not satisfied or only password was used. Tune to your org’s allowed “password-only” apps and break-glass accounts. Alert on unexpected ALLOW without MFA for protected apps. Review `policy.evaluate_sign_on` with `outcome.result` and debug fields.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="policy.evaluate_sign_on"
| where outcome.reason IN ("MFA_NOT_ENROLLED","FACTOR_NOT_USED","NONE")
| stats count by actor.alternateId, client.ipAddress, outcome.reason
| where count > 0
```

Understanding this SPL

**Okta MFA Bypass Attempts** — Attempts to skip or weaken MFA (policy gaps, risky grant flows) are a direct path to account takeover; monitoring policy evaluation outcomes closes that gap.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`policy.evaluate_sign_on`, `user.authentication`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where outcome.reason IN ("MFA_NOT_ENROLLED","FACTOR_NOT_USED","NONE")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, client.ipAddress, outcome.reason** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Okta MFA Bypass Attempts** — Attempts to skip or weaken MFA (policy gaps, risky grant flows) are a direct path to account takeover; monitoring policy evaluation outcomes closes that gap.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`policy.evaluate_sign_on`, `user.authentication`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, IP, reason), Timeline of policy events, Single value (bypass events per hour).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="policy.evaluate_sign_on"
| where outcome.reason IN ("MFA_NOT_ENROLLED","FACTOR_NOT_USED","NONE")
| stats count by actor.alternateId, client.ipAddress, outcome.reason
| where count > 0
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (user, IP, reason), Timeline of policy events, Single value (bypass events per hour).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
