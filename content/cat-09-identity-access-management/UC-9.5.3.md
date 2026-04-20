---
id: "9.5.3"
title: "Okta Suspicious Sign-In Activity"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.5.3 · Okta Suspicious Sign-In Activity

## Description

Okta threat signals and anomalous sessions (new device, new country, Tor) surface account takeovers before lateral movement.

## Value

Okta threat signals and anomalous sessions (new device, new country, Tor) surface account takeovers before lateral movement.

## Implementation

Forward full threat and session events. Map `severity`, `outcome`, and Okta risk context. Create alerts for `security.threat.detected` and for sessions with risk scores above your baseline. Integrate with SOAR for step-up auth.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`security.threat.detected`, `user.session.start`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward full threat and session events. Map `severity`, `outcome`, and Okta risk context. Create alerts for `security.threat.detected` and for sessions with risk scores above your baseline. Integrate with SOAR for step-up auth.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" (eventType="security.threat.detected" OR severity="WARN")
| stats count by actor.alternateId, client.ipAddress, outcome.result, displayMessage
| where count > 0
| sort -count
```

Understanding this SPL

**Okta Suspicious Sign-In Activity** — Okta threat signals and anomalous sessions (new device, new country, Tor) surface account takeovers before lateral movement.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`security.threat.detected`, `user.session.start`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, client.ipAddress, outcome.result, displayMessage** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Okta Suspicious Sign-In Activity** — Okta threat signals and anomalous sessions (new device, new country, Tor) surface account takeovers before lateral movement.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`security.threat.detected`, `user.session.start`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, IP, message), Map (sign-in geo), Line chart (threat events per day).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" (eventType="security.threat.detected" OR severity="WARN")
| stats count by actor.alternateId, client.ipAddress, outcome.result, displayMessage
| where count > 0
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (user, IP, message), Map (sign-in geo), Line chart (threat events per day).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
