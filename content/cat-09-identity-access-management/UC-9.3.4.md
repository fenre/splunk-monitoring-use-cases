---
id: "9.3.4"
title: "Application Access Patterns"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.3.4 · Application Access Patterns

## Description

Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.

## Value

Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.

## Implementation

Track SSO events per application. Build user-application access matrix. Detect users accessing applications outside their normal pattern. Report on application usage for license optimization and access reviews.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: IdP application access logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track SSO events per application. Build user-application access matrix. Detect users accessing applications outside their normal pattern. Report on application usage for license optimization and access reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| stats dc(actor.alternateId) as unique_users, count as total_access by target{}.displayName
| sort -unique_users
```

Understanding this SPL

**Application Access Patterns** — Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.

Documented **Data sources**: IdP application access logs. **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by target{}.displayName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count dc(Authentication.user) as user_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Application Access Patterns** — Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.

Documented **Data sources**: IdP application access logs. **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top applications by user count), Table (application usage summary), Heatmap (user × application access).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| stats dc(actor.alternateId) as unique_users, count as total_access by target{}.displayName
| sort -unique_users
```

## CIM SPL

```spl
| tstats `summariesonly` count dc(Authentication.user) as user_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.app span=1h
| sort -count
```

## Visualization

Bar chart (top applications by user count), Table (application usage summary), Heatmap (user × application access).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
