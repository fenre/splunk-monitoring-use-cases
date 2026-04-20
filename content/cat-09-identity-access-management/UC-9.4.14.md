---
id: "9.4.14"
title: "CyberArk Session Recording Alerts"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.14 · CyberArk Session Recording Alerts

## Description

Real-time alerts on PSM recordings—policy violations, blocked commands, or session anomalies—enable SOC response before logout.

## Value

Real-time alerts on PSM recordings—policy violations, blocked commands, or session anomalies—enable SOC response before logout.

## Implementation

Forward PSM alert stream to Splunk. Map vendor severity to SOC tiers. Integrate with SOAR for session kill on critical patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk TA for CyberArk.
• Ensure the following data sources are available: PSM recording events, policy violation syslog from PSM.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward PSM alert stream to Splunk. Map vendor severity to SOC tiers. Integrate with SOAR for session kill on critical patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:psm" OR sourcetype="cyberark:psm_alert"
| search alert_level IN ("High","Critical") OR policy_violation="true"
| table _time, user, target_account, session_id, alert_reason
| sort -_time
```

Understanding this SPL

**CyberArk Session Recording Alerts** — Real-time alerts on PSM recordings—policy violations, blocked commands, or session anomalies—enable SOC response before logout.

Documented **Data sources**: PSM recording events, policy violation syslog from PSM. **App/TA** (typical add-on context): Splunk TA for CyberArk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:psm, cyberark:psm_alert. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:psm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **CyberArk Session Recording Alerts**): table _time, user, target_account, session_id, alert_reason
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**CyberArk Session Recording Alerts** — Real-time alerts on PSM recordings—policy violations, blocked commands, or session anomalies—enable SOC response before logout.

Documented **Data sources**: PSM recording events, policy violation syslog from PSM. **App/TA** (typical add-on context): Splunk TA for CyberArk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (alerts), Table (session detail), Single value (critical alerts 24h).

## SPL

```spl
index=pam sourcetype="cyberark:psm" OR sourcetype="cyberark:psm_alert"
| search alert_level IN ("High","Critical") OR policy_violation="true"
| table _time, user, target_account, session_id, alert_reason
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Timeline (alerts), Table (session detail), Single value (critical alerts 24h).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
