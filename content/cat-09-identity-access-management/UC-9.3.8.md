<!-- AUTO-GENERATED from UC-9.3.8.json — DO NOT EDIT -->

---
id: "9.3.8"
title: "SAML Assertion Replay Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.8 · SAML Assertion Replay Detection

## Description

Replayed SAML assertions can grant access without fresh authentication. Correlating assertion IDs and NotOnOrAfter windows catches reuse.

## Value

Replayed SAML assertions can grant access without fresh authentication. Correlating assertion IDs and NotOnOrAfter windows catches reuse.

## Implementation

Ingest assertion IDs from IdP or SP debug logs (privacy-safe hashing if needed). Alert on duplicate assertion_id for same SP. Enforce short assertion lifetimes at IdP.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: IdP logs, application SAML trace (e.g., Shibboleth, Okta, ADFS).
• Ensure the following data sources are available: SAML response logs with `AssertionID`, `InResponseTo`, `NotOnOrAfter`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest assertion IDs from IdP or SP debug logs (privacy-safe hashing if needed). Alert on duplicate assertion_id for same SP. Enforce short assertion lifetimes at IdP.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=saml sourcetype="saml:assertion"
| stats count by assertion_id, sp_entity_id
| where count > 1
| table assertion_id, sp_entity_id, count
```

Understanding this SPL

**SAML Assertion Replay Detection** — Replayed SAML assertions can grant access without fresh authentication. Correlating assertion IDs and NotOnOrAfter windows catches reuse.

Documented **Data sources**: SAML response logs with `AssertionID`, `InResponseTo`, `NotOnOrAfter`. **App/TA** (typical add-on context): IdP logs, application SAML trace (e.g., Shibboleth, Okta, ADFS). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: saml; **sourcetype**: saml:assertion. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=saml, sourcetype="saml:assertion". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by assertion_id, sp_entity_id** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SAML Assertion Replay Detection**): table assertion_id, sp_entity_id, count

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**SAML Assertion Replay Detection** — Replayed SAML assertions can grant access without fresh authentication. Correlating assertion IDs and NotOnOrAfter windows catches reuse.

Documented **Data sources**: SAML response logs with `AssertionID`, `InResponseTo`, `NotOnOrAfter`. **App/TA** (typical add-on context): IdP logs, application SAML trace (e.g., Shibboleth, Okta, ADFS). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (duplicate assertions), Timeline, Single value (replay attempts).

## SPL

```spl
index=saml sourcetype="saml:assertion"
| stats count by assertion_id, sp_entity_id
| where count > 1
| table assertion_id, sp_entity_id, count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (duplicate assertions), Timeline, Single value (replay attempts).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
