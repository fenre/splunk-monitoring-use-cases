<!-- AUTO-GENERATED from UC-5.13.77.json — DO NOT EDIT -->

---
id: "5.13.77"
title: "Network Change MTTR Analysis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.77 · Network Change MTTR Analysis

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Operational &middot; **Wave:** Run &middot; **Status:** Verified

*We measure how long it takes to fix each network problem and whether the problem was caused by a planned change or happened on its own. This tells management which problems are preventable (by improving the change process) and which need faster response (by improving runbooks or adding automation).*

---

## Description

Analyzes mean time to repair (MTTR) for Catalyst Center issues and correlates with configuration changes to determine whether changes are improving or degrading resolution times.

## Value

MTTR is the key operational efficiency metric. Correlating with configuration changes reveals whether changes are helping (reducing MTTR) or hurting (introducing new issues).

## Implementation

1. **Issues:** Requires `cisco:dnac:issue` with `status=RESOLVED`, a valid **creation** time and **resolved** time — the SPL uses `_time` as detect and `resolved_time` as resolution; if your payload uses `creationTime`/`lastUpdatedTime`, rewrite `eval` lines to match **epoch** seconds.
2. **Audit:** `cisco:dnac:audit:logs` from Intent API audit stream; `auditRequestType="CONFIG*"` filters configuration changes. If your field is `auditRequestType` vs `requestType`, adjust.
3. **Join on category:** Both issue and audit must share a stable `category` string; if audit lacks `category`, join on `siteId` + time window instead (advanced).
4. **Schedule:** Weekly or monthly report; store in summary index for trending.
5. **Privacy:** Audit logs may contain usernames — restrict role access to this report.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) and UC-5.13.24 (Issue Resolution Time) must be operational — this UC extends MTTR analysis with change-correlation context.
- UC-5.13.46 (Configuration Change Audit Trail) must be operational for change-event data.
- Retain **90+ days** of both issue and audit data for meaningful MTTR trending.
- This is a **run-tier** operations management UC. The audience is the operations leadership team reviewing process effectiveness, not the day-to-day NOC.

### Step 1 — Configure data collection
Same `issue` and `audit_logs` inputs as UC-5.13.21 and UC-5.13.45. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED"
| stats earliest(_time) as detected latest(_time) as resolved latest(priority) as priority latest(category) as category by issueId, name
| eval mttr_hours=round((resolved-detected)/3600,1)
| eval detected_date=strftime(detected, "%Y-%m-%d %H:%M")
| eval resolved_date=strftime(resolved, "%Y-%m-%d %H:%M")
| join type=left issueId
    [search index=catalyst sourcetype="cisco:dnac:audit:logs" auditRequestType IN ("PUT","POST","DELETE")
     | eval change_time=_time
     | eval change_user=auditUserName
     | eval change_desc=auditDescription
     | table change_time, change_user, change_desc, issueId]
| eval change_related=if(isnotnull(change_user), "Change-related: ".change_user." — ".change_desc, "No correlated change")
| table issueId, name, priority, category, detected_date, resolved_date, mttr_hours, change_related
| sort priority, -mttr_hours
```

Why correlate MTTR with changes: the most important question after "how long did it take to fix?" is "what caused it?" Issues triggered by configuration changes (change-related MTTR) have different root causes and different prevention strategies than issues that arise spontaneously (organic MTTR). Change-related issues should be prevented by improving the change process. Organic issues should be prevented by infrastructure investment or design improvements.

Why `join type=left`: keeps all resolved issues even if there's no correlated change event. Many issues won't correlate with a change — they're organic (hardware failure, environmental, traffic-driven). The `change_related` field distinguishes the two.

For MTTR by change vs organic:
```spl
<base search>
| eval issue_source=if(isnotnull(change_user), "Change-related", "Organic")
| stats avg(mttr_hours) as avg_mttr median(mttr_hours) as median_mttr count as issues by priority, issue_source
| sort priority, issue_source
```
This table shows whether change-related issues are resolved faster or slower than organic ones. If change-related P1s have higher MTTR, the rollback process needs improvement.

For MTTR trending (monthly):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED"
| stats earliest(_time) as detected latest(_time) as resolved by issueId, priority
| eval mttr_hours=round((resolved-detected)/3600,1)
| bin detected span=1w
| stats avg(mttr_hours) as weekly_mttr by detected, priority
| timechart span=1w avg(weekly_mttr) by priority
```

Schedule: monthly (cron `0 7 1 * *`), output to PDF for the operations leadership review.

### Step 3 — Validate
(a) Pick a resolved issue with known MTTR. Compare the Splunk-calculated `mttr_hours` with the actual resolution time from the incident ticket.

(b) For change-correlated issues: verify that the `change_user` and `change_desc` match the actual change that caused the issue. False correlations can occur if unrelated changes happen near the same time.

(c) Compare with UC-5.13.24's MTTR metrics. The numbers should match for non-change-correlated issues. Change-correlated issues add the context dimension.

(d) Check the organic-vs-change split: what percentage of issues are change-related? Typical: 20–40% of issues are triggered by changes. If > 50%, the change management process needs tightening.

### Step 4 — Operationalize
- Monthly operations review: MTTR by priority + change correlation. Two key metrics:
  1. Is overall MTTR improving month-over-month?
  2. Is the percentage of change-related issues declining (better change testing)?
- For change management improvement: track which change types (template pushes, firmware upgrades, policy modifications) generate the most post-change issues.
- For process ROI: after implementing a new runbook or SOAR automation, compare MTTR before vs after. The improvement is the automation ROI.

Runbook (owner: Operations Manager):
1. Monthly: review MTTR by priority. P1 MTTR should be < 1 hour. P2 < 4 hours.
2. If MTTR is increasing: identify the bottleneck (detection delay? triage delay? fix delay?) and address.
3. Track change-related MTTR separately. If change-related issues have higher MTTR than organic, the change rollback process needs improvement.
4. Identify repeat change-related issues: if the same change type keeps causing issues, improve pre-change testing or add to the change checklist.

### Step 5 — Troubleshooting

- **No RESOLVED issues in the data** — the TA may filter resolved issues. Check `| stats values(status)`.

- **MTTR looks unrealistically long** — a few long-standing issues skew the average. Use median instead of average.

- **Change correlation produces false matches** — the `join` may match unrelated changes. Narrow the time window in the join or require `change_time` to be within 2 hours of `detected`.

- **Organic-vs-change split is 100% organic** — no audit data is available, or the `join` isn't finding matches. Check the audit log input (UC-5.13.45).

- **MTTR differs from ITSM data** — Splunk measures from Catalyst Center AI detection to issue resolution. ITSM measures from ticket creation to closure. The gap is the detection-to-ticket delay — itself a valuable metric.

- **Want to track MTTR by team** — add a `device_team_ownership` lookup that maps `deviceName` to the responsible team. Group MTTR by team to identify which teams resolve issues fastest.

- **Trend shows MTTR spike** — check if a major incident with long resolution inflated the period's average. Exclude the outlier for trend analysis or use median.

- **Want to include MTTA (mean time to acknowledge)** — this requires a timestamp for when the on-call engineer acknowledged the alert. Add PagerDuty/On-Call acknowledgement data via a webhook or REST API integration.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval detect_time=_time | eval resolve_duration_hrs=round((resolved_time-detect_time)/3600,1) | stats avg(resolve_duration_hrs) as avg_mttr_hrs median(resolve_duration_hrs) as median_mttr_hrs p90(resolve_duration_hrs) as p90_mttr_hrs count as resolved_issues by category | join type=left category [search index=catalyst sourcetype="cisco:dnac:audit:logs" auditRequestType="CONFIG*" | stats count as related_changes by category] | eval change_correlation=if(isnotnull(related_changes),"Changes detected","No changes") | sort avg_mttr_hrs
```

## Visualization

Table: category, avg_mttr_hrs, median_mttr_hrs, p90_mttr_hrs, resolved_issues, related_changes, change_correlation; optional timechart of avg MTTR by week; box plot of resolve_duration_hrs.

## Known False Positives

**Auto-resolved issues with very short MTTR skewing the average downward.** Transient issues that Assurance auto-resolves within minutes show near-zero MTTR, making the team's response appear faster than it actually is. Distinguish by checking whether `resolve_duration_hrs < 0.1` (under 6 minutes), indicating auto-resolution. Suppress by filtering `| where resolve_duration_hrs >= 0.5` for MTTR analysis to focus on issues that required human intervention.

**Issue resolution timestamp missing or inaccurate for manually closed issues.** When an operator manually closes an issue in Catalyst Center, the `resolved_time` may not accurately reflect when the problem was actually fixed. Distinguish by checking whether `resolved_time` is populated and reasonable. Suppress by filtering `| where isnotnull(resolved_time) AND resolved_time>detect_time`.

**Maintenance-window issues included in MTTR calculation.** Issues generated during planned maintenance have their resolution time determined by the maintenance duration, not the team's operational response. Distinguish by correlating with ITSM change records. Suppress by excluding maintenance-window issues from the MTTR metric.

**Change-related issues where the change itself is the resolution.** Some Assurance issues are created because a configuration change was detected. The change is intentional, and the issue resolves when Assurance re-scans. These are not incidents requiring response. Distinguish by checking whether the `category` is "Configuration" and correlating with audit log configuration changes. Suppress by filtering configuration-change issues from MTTR analysis.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Issues API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!issues)
