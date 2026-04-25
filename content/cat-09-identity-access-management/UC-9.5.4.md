<!-- AUTO-GENERATED from UC-9.5.4.json — DO NOT EDIT -->

---
id: "9.5.4"
title: "Okta Admin Console Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.4 · Okta Admin Console Changes

## Description

Changes in the admin console affect global security posture; auditing who changed what supports SOC2/ISO investigations and insider-threat programs.

## Value

Changes in the admin console affect global security posture; auditing who changed what supports SOC2/ISO investigations and insider-threat programs.

## Implementation

Capture all admin app sessions and high-privilege system events. Restrict alerts to production Okta orgs; exclude known automation actors. Store lookups for approved admins and compare. Alert on first-time admin access from new ASN or country.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`system.*`, `user.session.access_admin_app`, `resource.*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Capture all admin app sessions and high-privilege system events. Restrict alerts to production Okta orgs; exclude known automation actors. Store lookups for approved admins and compare. Alert on first-time admin access from new ASN or country.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" (eventType="user.session.access_admin_app" OR like(eventType,"system.org%"))
| stats count by actor.alternateId, eventType, client.ipAddress, displayMessage
| sort -count
```

Understanding this SPL

**Okta Admin Console Changes** — Changes in the admin console affect global security posture; auditing who changed what supports SOC2/ISO investigations and insider-threat programs.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`system.*`, `user.session.access_admin_app`, `resource.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, eventType, client.ipAddress, displayMessage** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Okta Admin Console Changes** — Changes in the admin console affect global security posture; auditing who changed what supports SOC2/ISO investigations and insider-threat programs.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`system.*`, `user.session.access_admin_app`, `resource.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (admin actions), Table (actor, event, IP), Bar chart (events by admin user).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" (eventType="user.session.access_admin_app" OR like(eventType,"system.org%"))
| stats count by actor.alternateId, eventType, client.ipAddress, displayMessage
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Timeline (admin actions), Table (actor, event, IP), Bar chart (events by admin user).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
