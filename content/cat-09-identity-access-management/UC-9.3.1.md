<!-- AUTO-GENERATED from UC-9.3.1.json — DO NOT EDIT -->

---
id: "9.3.1"
title: "MFA Challenge Failure Rate"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.3.1 · MFA Challenge Failure Rate

## Description

High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.

## Value

High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.

## Implementation

Ingest IdP logs via API. Track MFA success/failure rates per user and per factor type. Alert on high failure rates (>20% per user). Detect MFA fatigue patterns (rapid repeated pushes). Report on factor type distribution.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, `Cisco Security Cloud` app (Splunkbase, replaces Duo Splunk Connector).
• Ensure the following data sources are available: Okta system log, Duo authentication log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest IdP logs via API. Track MFA success/failure rates per user and per factor type. Alert on high failure rates (>20% per user). Detect MFA fatigue patterns (rapid repeated pushes). Report on factor type distribution.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count(eval(outcome.result="FAILURE")) as failures, count(eval(outcome.result="SUCCESS")) as successes by actor.displayName
| eval fail_rate=round(failures/(failures+successes)*100,1)
| where fail_rate > 20
```

Understanding this SPL

**MFA Challenge Failure Rate** — High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.

Documented **Data sources**: Okta system log, Duo authentication log. **App/TA** (typical add-on context): `Splunk_TA_okta`, `Cisco Security Cloud` app (Splunkbase, replaces Duo Splunk Connector). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.displayName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 20` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user,Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**MFA Challenge Failure Rate** — High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.

Documented **Data sources**: Okta system log, Duo authentication log. **App/TA** (typical add-on context): `Splunk_TA_okta`, `Cisco Security Cloud` app (Splunkbase, replaces Duo Splunk Connector). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failure rate by user), Pie chart (factor type distribution), Line chart (MFA success rate trend).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count(eval(outcome.result="FAILURE")) as failures, count(eval(outcome.result="SUCCESS")) as successes by actor.displayName
| eval fail_rate=round(failures/(failures+successes)*100,1)
| where fail_rate > 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user,Authentication.src span=1h
| where count > 10
```

## Visualization

Bar chart (failure rate by user), Pie chart (factor type distribution), Line chart (MFA success rate trend).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [Cisco Security Cloud](https://splunkbase.splunk.com/app/7404)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
