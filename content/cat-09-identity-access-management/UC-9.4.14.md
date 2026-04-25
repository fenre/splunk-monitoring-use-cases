<!-- AUTO-GENERATED from UC-9.4.14.json — DO NOT EDIT -->

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

Step 3 — Validate
Compare with CyberArk PVWA and PSM session views for the same sessions, alerts, and policy hits in the same time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (alerts), Table (session detail), Single value (critical alerts 24h).

## SPL

```spl
index=pam sourcetype="cyberark:psm" OR sourcetype="cyberark:psm_alert"
| search alert_level IN ("High","Critical") OR policy_violation="true"
| table _time, user, target_account, session_id, alert_reason
| sort -_time
```

## Visualization

Timeline (alerts), Table (session detail), Single value (critical alerts 24h).

## References

- [Splunk Add-on for CyberArk](https://splunkbase.splunk.com/app/3084)
- [CyberArk Privileged Session Manager](https://docs.cyberark.com/)
