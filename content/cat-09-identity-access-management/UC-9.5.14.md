<!-- AUTO-GENERATED from UC-9.5.14.json — DO NOT EDIT -->

---
id: "9.5.14"
title: "Duo Push Fraud Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.14 · Duo Push Fraud Detection

## Description

Push bombing and fraudulent approve taps are common MFA bypass techniques; correlating push volume and user behavior stops approval fatigue attacks.

## Value

Push bombing and fraudulent approve taps are common MFA bypass techniques; correlating push volume and user behavior stops approval fatigue attacks.

## Implementation

Track push attempts per user per short window. Alert on high-frequency pushes (fatigue) or pushes with `result="fraud"` or Duo fraud reasons. Integrate with Duo Risk-Based Authentication. Pair with Okta MFA events for dual IdP visibility.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco Duo TA.
• Ensure the following data sources are available: `sourcetype=duo:authentication`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track push attempts per user per short window. Alert on high-frequency pushes (fatigue) or pushes with `result="fraud"` or Duo fraud reasons. Integrate with Duo Risk-Based Authentication. Pair with Okta MFA events for dual IdP visibility.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=duo sourcetype="duo:authentication" factor="push"
| bin _time span=5m
| stats count by user, _time
| where count > 5
| sort -count
```

Understanding this SPL

**Duo Push Fraud Detection** — Push bombing and fraudulent approve taps are common MFA bypass techniques; correlating push volume and user behavior stops approval fatigue attacks.

Documented **Data sources**: `sourcetype=duo:authentication`. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: duo; **sourcetype**: duo:authentication. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=duo, sourcetype="duo:authentication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by user, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Duo Push Fraud Detection** — Push bombing and fraudulent approve taps are common MFA bypass techniques; correlating push volume and user behavior stops approval fatigue attacks.

Documented **Data sources**: `sourcetype=duo:authentication`. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Duo Admin (Authentication Log, admin actions, enrollment, and device trust) for the same time range and identities.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, push count in window), Line chart (pushes per user), Timeline (fraud-marked events).

## SPL

```spl
index=duo sourcetype="duo:authentication" factor="push"
| bin _time span=5m
| stats count by user, _time
| where count > 5
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=5m | sort - count
```

## Visualization

Table (user, push count in window), Line chart (pushes per user), Timeline (fraud-marked events).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
