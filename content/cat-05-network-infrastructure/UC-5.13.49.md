<!-- AUTO-GENERATED from UC-5.13.49.json — DO NOT EDIT -->

---
id: "5.13.49"
title: "After-Hours Administrative Activity"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.49 · After-Hours Administrative Activity

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for people making changes to the network management system during nights and weekends — times when changes are not normally expected. Each after-hours change gets checked against approved work orders, because unauthorised changes at 3 AM are a serious red flag that needs investigation.*

---

## Description

Detects state-changing administrative activity on the Catalyst Center platform during non-business hours (nights, weekends, holidays), flagging potentially unauthorised changes that occurred during periods of reduced operational oversight — the strongest indicator of either emergency work (should have a ticket) or compromised access (should trigger investigation).

## Value

Legitimate network changes happen during business hours or approved maintenance windows. Configuration modifications at 3 AM on a Saturday — especially without a change ticket — are either emergency response (document it) or unauthorised access (investigate it). This UC surfaces all after-hours state-changing activity so the security team can verify each event was legitimate the next business morning. For SOX ITGC, after-hours changes without corresponding emergency change tickets are potential control failures that require documentation.

## Implementation

Same `audit_logs` input as UC-5.13.45. Filter by time-of-day and day-of-week for after-hours activity. Maintain a `business_hours` definition (default: Mon–Fri 07:00–19:00). Schedule daily at 7 AM to review overnight activity.

## Detailed Implementation

### Prerequisites
- UC-5.13.45 (Audit Log Overview) must be operational — same `audit_logs` data feed.
- Define your organisation's business hours. Default: Mon–Fri 07:00–19:00 (local timezone). For 24/7 operations centres, define 'reduced-staff hours' instead.
- Maintain a `catalyst_maintenance_windows` lookup with approved off-hours maintenance schedules.
- Ensure the Splunk search head timezone aligns with the operational timezone. `date_hour` uses the search head's timezone setting.

### Step 1 — Configure data collection
Same `audit_logs` input as UC-5.13.45. No additional configuration.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| where (date_hour < 7 OR date_hour > 19) OR match(date_wday, "saturday|sunday")
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```

Why `auditRequestType IN ("PUT","POST","DELETE")`: after-hours browsing (GETs) is low-risk. State-changing operations are the concern because they can modify network configurations without oversight.

Why `isSystemEvent=false`: excludes automated Catalyst Center operations that run on schedules regardless of business hours.

Why `date_hour < 7 OR date_hour > 19`: captures evening (after 7 PM) and early morning (before 7 AM) activity. Adjust for your organisation's schedule.

Why `match(date_wday, "saturday|sunday")`: captures weekend activity regardless of hour. Weekend changes are almost always either emergency or unauthorised.

For maintenance-window exclusion:
```spl
<base search>
| lookup catalyst_maintenance_windows _time OUTPUT in_window, change_id
| eval classification=if(isnotnull(change_id), "Approved: ".change_id, "INVESTIGATE")
| table _time, auditUserName, auditRequestType, auditDescription, classification
```

Schedule as Alert: daily at 7 AM (cron `0 7 * * *`), time range `-14h to now` (covers the previous night). Trigger when results > 0.

### Step 3 — Validate
(a) Make a test change during after-hours (or adjust the time filter temporarily to include current hours). Verify it appears in the search results.
(b) Verify approved maintenance window activity is correctly excluded by the lookup.
(c) Check timezone alignment: `| eval splunk_hour=strftime(now(), "%H") | table splunk_hour`. This should match your wall clock.
(d) Run over 30 days to establish the baseline: how many after-hours changes occur per week? Is there a pattern (always the same user, always Saturday morning)?

### Step 4 — Operationalize
- Daily morning check: security team reviews any after-hours activity from the previous night.
- Each after-hours change event should have either: (1) an approved maintenance window entry, (2) an emergency incident ticket, or (3) be flagged for investigation.
- SOX evidence: monthly after-hours activity report with approval documentation for each event.

Runbook (owner: Security Operations, 7 AM daily):
1. Open the after-hours activity report for the previous night.
2. For each event: check ITSM for an emergency change ticket or incident ticket covering that user and time.
3. If approved emergency change: annotate as 'approved emergency, ticket #XXX.' Close.
4. If approved maintenance window: annotate as 'approved maintenance, window #XXX.' Close.
5. If NO approval exists: this is an unauthorised after-hours change. Investigate:
   - Contact the user. Was this intentional? Why no ticket?
   - Check UC-5.13.32 (Compliance Drift) to see if the change caused compliance violations.
   - Check UC-5.13.1 (Device Health) to see if the change impacted device health.
   - Document the investigation and corrective action.
6. For repeated unapproved after-hours activity from the same user: escalate to management.

### Step 5 — Troubleshooting

- **System events appearing despite `isSystemEvent=false`** — verify the field is boolean. Some TA versions emit the string `"false"` instead of boolean `false`. Adjust: `| where isSystemEvent=false OR isSystemEvent="false"`.

- **False positives from scheduled TA polls** — the TA generates GET events every 5 minutes. The `auditRequestType IN ("PUT","POST","DELETE")` filter excludes these.

- **Timezone mismatch** — `date_hour` uses the search head's timezone. If your team operates in a different timezone, adjust the hour boundaries or set `tz=<timezone>` in the search.

- **Holiday activity not detected** — weekday holidays are not caught by `date_wday`. Maintain a `holidays` lookup and add `| lookup holidays _time OUTPUT is_holiday | where is_holiday="yes"` to catch holiday activity.

- **Too many results from legitimate overnight maintenance** — classify scheduled maintenance via the `catalyst_maintenance_windows` lookup and show only the INVESTIGATE rows.

- **Multinational team creating false after-hours alerts** — add a `user_timezone` lookup and filter based on each user's local business hours rather than a universal schedule.

- **Want real-time alerting instead of daily** — schedule the alert every 30 minutes with `| where _time > relative_time(now(), "-35m")`. But note that after-hours changes rarely need sub-hour response — the daily review is usually sufficient.

- **Audit data retention concerns** — at ~50 KB/day, 365 days = ~18 MB. Negligible.

Additional operational context for After-Hours Administrative Activity:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| where (date_hour < 7 OR date_hour > 19) OR match(date_wday, "saturday|sunday")
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```

## Visualization

(1) Table: _time, auditUserName, auditRequestType, auditDescription — filtered to after-hours changes only. (2) Heatmap: activity count by hour-of-day × day-of-week to show patterns. (3) Single value: after-hours changes in last 24h (yellow ≥ 1, red ≥ 5). (4) Correlation: join with ITSM emergency change records to classify each event as approved or unapproved.

## Known False Positives

**Approved emergency changes during off-hours.** Legitimate emergency maintenance (P1 incident response) generates after-hours activity that has an associated incident ticket. Distinguish by cross-referencing with ITSM emergency change records. Do not suppress — document the event with the incident/change ID to close the audit loop.

**Automated SWIM firmware pushes scheduled for off-hours.** Firmware upgrades are often scheduled overnight to minimise user impact. These generate audit events from the service account or the scheduling user. Distinguish by checking `auditDescription` for SWIM-related operations and correlating with UC-5.13.57 (Upgrade Progress). Suppress by filtering known scheduled-operation users or annotating with the maintenance window.

**Multinational team with after-hours overlap.** A team member in a different timezone working during their business hours appears as after-hours in the primary timezone. Distinguish by checking the `auditUserName` against a user-timezone lookup. Suppress by defining per-user business hours rather than a universal schedule.

**System-generated events during overnight processing.** Despite the `isSystemEvent=false` filter, some automated operations (certificate auto-renewal, scheduled compliance scans) may be attributed to a service account but not flagged as system events. Distinguish by checking whether the `auditUserName` is a known service account. Filter with `| where auditUserName NOT IN ("<service-accounts>")`.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — AC-2 Account Management](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC-2)
