<!-- AUTO-GENERATED from UC-9.3.7.json — DO NOT EDIT -->

---
id: "9.3.7"
title: "Session Hijacking Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.7 · Session Hijacking Detection

## Description

Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.

## Value

Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.

## Implementation

Track session IDs across events. Alert when a single session is used from multiple IP addresses simultaneously (excluding known VPN/proxy IPs). Correlate with user agent changes for additional confidence.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, IdP session logs.
• Ensure the following data sources are available: IdP session activity logs, application session logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track session IDs across events. Alert when a single session is used from multiple IP addresses simultaneously (excluding known VPN/proxy IPs). Correlate with user agent changes for additional confidence.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log"
| stats dc(client.ipAddress) as unique_ips, values(client.ipAddress) as ips by authenticationContext.externalSessionId, actor.alternateId
| where unique_ips > 2
| table actor.alternateId, authenticationContext.externalSessionId, unique_ips, ips
```

Understanding this SPL

**Session Hijacking Detection** — Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.

Documented **Data sources**: IdP session activity logs, application session logs. **App/TA** (typical add-on context): `Splunk_TA_okta`, IdP session logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by authenticationContext.externalSessionId, actor.alternateId** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_ips > 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Session Hijacking Detection**): table actor.alternateId, authenticationContext.externalSessionId, unique_ips, ips

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user span=1h
| where src_count > 3
```

Understanding this CIM / accelerated SPL

**Session Hijacking Detection** — Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.

Documented **Data sources**: IdP session activity logs, application session logs. **App/TA** (typical add-on context): `Splunk_TA_okta`, IdP session logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where src_count > 3` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (hijacked sessions), Timeline (suspicious session events), Bar chart (users with multi-IP sessions).

## SPL

```spl
index=okta sourcetype="OktaIM2:log"
| stats dc(client.ipAddress) as unique_ips, values(client.ipAddress) as ips by authenticationContext.externalSessionId, actor.alternateId
| where unique_ips > 2
| table actor.alternateId, authenticationContext.externalSessionId, unique_ips, ips
```

## CIM SPL

```spl
| tstats `summariesonly` dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user span=1h
| where src_count > 3
```

## Visualization

Table (hijacked sessions), Timeline (suspicious session events), Bar chart (users with multi-IP sessions).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
