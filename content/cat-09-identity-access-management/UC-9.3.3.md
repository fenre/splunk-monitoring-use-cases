<!-- AUTO-GENERATED from UC-9.3.3.json — DO NOT EDIT -->

---
id: "9.3.3"
title: "Token Anomaly Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.3 · Token Anomaly Detection

## Description

Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.

## Value

Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.

## Implementation

Monitor token issuance and usage patterns. Alert on tokens used from multiple IPs (potential replay). Track token lifetime and refresh patterns. Detect anomalous token requests outside normal application patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, IdP audit logs.
• Ensure the following data sources are available: IdP token issuance logs, application token validation logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor token issuance and usage patterns. Alert on tokens used from multiple IPs (potential replay). Track token lifetime and refresh patterns. Detect anomalous token requests outside normal application patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as unique_ips by actor.alternateId, target{}.displayName
| where unique_ips > 3
```

Understanding this SPL

**Token Anomaly Detection** — Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.

Documented **Data sources**: IdP token issuance logs, application token validation logs. **App/TA** (typical add-on context): `Splunk_TA_okta`, IdP audit logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, target{}.displayName** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_ips > 3` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user Authentication.app span=1h
| where src_count > 3
```

Understanding this CIM / accelerated SPL

**Token Anomaly Detection** — Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.

Documented **Data sources**: IdP token issuance logs, application token validation logs. **App/TA** (typical add-on context): `Splunk_TA_okta`, IdP audit logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where src_count > 3` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (anomalous token usage), Timeline (suspicious events), Bar chart (tokens by application).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as unique_ips by actor.alternateId, target{}.displayName
| where unique_ips > 3
```

## CIM SPL

```spl
| tstats `summariesonly` count dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user Authentication.app span=1h
| where src_count > 3
```

## Visualization

Table (anomalous token usage), Timeline (suspicious events), Bar chart (tokens by application).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
