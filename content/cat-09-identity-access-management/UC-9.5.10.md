<!-- AUTO-GENERATED from UC-9.5.10.json — DO NOT EDIT -->

---
id: "9.5.10"
title: "Federated SSO Token Abuse"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.10 · Federated SSO Token Abuse

## Description

Excessive OAuth/OIDC grants, refresh-token reuse, or token minting from new clients can indicate session theft or malicious automation.

## Value

Excessive OAuth/OIDC grants, refresh-token reuse, or token minting from new clients can indicate session theft or malicious automation.

## Implementation

Track token grants per user per IP and client. Use `transaction` or `streamstats` to detect rapid grants. Alert on unusual client IDs or scopes. Correlate with OAuth abuse detections from IdP.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`app.oauth2.*`, `app.oauth2.token.*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track token grants per user per IP and client. Use `transaction` or `streamstats` to detect rapid grants. Alert on unusual client IDs or scopes. Correlate with OAuth abuse detections from IdP.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count by actor.alternateId, client.ipAddress
| where count > 100
| sort -count
```

Understanding this SPL

**Federated SSO Token Abuse** — Excessive OAuth/OIDC grants, refresh-token reuse, or token minting from new clients can indicate session theft or malicious automation.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`app.oauth2.*`, `app.oauth2.token.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, client.ipAddress** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Federated SSO Token Abuse** — Excessive OAuth/OIDC grants, refresh-token reuse, or token minting from new clients can indicate session theft or malicious automation.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`app.oauth2.*`, `app.oauth2.token.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, IP, grant count), Line chart (grants per minute), Bar chart (token grants by client).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count by actor.alternateId, client.ipAddress
| where count > 100
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (user, IP, grant count), Line chart (grants per minute), Bar chart (token grants by client).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
