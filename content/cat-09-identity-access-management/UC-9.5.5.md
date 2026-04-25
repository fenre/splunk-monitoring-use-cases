<!-- AUTO-GENERATED from UC-9.5.5.json — DO NOT EDIT -->

---
id: "9.5.5"
title: "Okta Policy Modifications"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.5 · Okta Policy Modifications

## Description

Sign-on, MFA, and password policy edits can weaken security org-wide; detecting unauthorized or out-of-window changes is essential for governance.

## Value

Sign-on, MFA, and password policy edits can weaken security org-wide; detecting unauthorized or out-of-window changes is essential for governance.

## Implementation

Ingest policy lifecycle and rule events. Correlate with change tickets. Alert on any policy change outside maintenance windows or from non-admin service accounts. Snapshot policy names in a lookup for critical resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`policy.*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest policy lifecycle and rule events. Correlate with change tickets. Alert on any policy change outside maintenance windows or from non-admin service accounts. Snapshot policy names in a lookup for critical resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"policy.lifecycle%") OR like(eventType,"policy.rule%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -count
```

Understanding this SPL

**Okta Policy Modifications** — Sign-on, MFA, and password policy edits can weaken security org-wide; detecting unauthorized or out-of-window changes is essential for governance.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`policy.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(eventType,"policy.lifecycle%") OR like(eventType,"policy.rule%")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, eventType, target{}.displayName** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Okta Policy Modifications** — Sign-on, MFA, and password policy edits can weaken security org-wide; detecting unauthorized or out-of-window changes is essential for governance.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`policy.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (policy, actor, target), Timeline (policy changes), Single value (changes in last 24h).

## SPL

```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"policy.lifecycle%") OR like(eventType,"policy.rule%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (policy, actor, target), Timeline (policy changes), Single value (changes in last 24h).

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
