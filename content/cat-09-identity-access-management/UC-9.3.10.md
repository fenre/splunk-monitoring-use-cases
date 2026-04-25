<!-- AUTO-GENERATED from UC-9.3.10.json — DO NOT EDIT -->

---
id: "9.3.10"
title: "SSO Session Hijacking Indicators"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.10 · SSO Session Hijacking Indicators

## Description

Complements session ID correlation with user-agent flips, ASN changes mid-session, and impossible concurrent SSO from IdP telemetry.

## Value

Complements session ID correlation with user-agent flips, ASN changes mid-session, and impossible concurrent SSO from IdP telemetry.

## Implementation

Flag sessions with multiple user agents or countries within short windows. Tune for corporate VPN that rotates egress. Pair with UC-9.3.7 for IP-based hijack detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, Entra sign-in logs.
• Ensure the following data sources are available: IdP `user.authentication.sso` with session correlation ID, device fingerprint fields.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Flag sessions with multiple user agents or countries within short windows. Tune for corporate VPN that rotates egress. Pair with UC-9.3.7 for IP-based hijack detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| transaction authenticationContext.externalSessionId maxpause=300 maxevents=50
| eval ua_change=if(mvcount(client.userAgent.rawUserAgent)>2,1,0)
| where ua_change=1
| table authenticationContext.externalSessionId, actor.alternateId, client.userAgent.rawUserAgent
```

Understanding this SPL

**SSO Session Hijacking Indicators** — Complements session ID correlation with user-agent flips, ASN changes mid-session, and impossible concurrent SSO from IdP telemetry.

Documented **Data sources**: IdP `user.authentication.sso` with session correlation ID, device fingerprint fields. **App/TA** (typical add-on context): `Splunk_TA_okta`, Entra sign-in logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Groups related events into transactions — prefer `maxspan`/`maxpause`/`maxevents` for bounded memory.
• `eval` defines or adjusts **ua_change** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where ua_change=1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SSO Session Hijacking Indicators**): table authenticationContext.externalSessionId, actor.alternateId, client.userAgent.rawUserAgent

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**SSO Session Hijacking Indicators** — Complements session ID correlation with user-agent flips, ASN changes mid-session, and impossible concurrent SSO from IdP telemetry.

Documented **Data sources**: IdP `user.authentication.sso` with session correlation ID, device fingerprint fields. **App/TA** (typical add-on context): `Splunk_TA_okta`, Entra sign-in logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious sessions), Timeline, Bar chart (sessions with UA churn).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| transaction authenticationContext.externalSessionId maxpause=300 maxevents=50
| eval ua_change=if(mvcount(client.userAgent.rawUserAgent)>2,1,0)
| where ua_change=1
| table authenticationContext.externalSessionId, actor.alternateId, client.userAgent.rawUserAgent
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (suspicious sessions), Timeline, Bar chart (sessions with UA churn).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
