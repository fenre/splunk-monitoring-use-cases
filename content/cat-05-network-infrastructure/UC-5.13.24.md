<!-- AUTO-GENERATED from UC-5.13.24.json — DO NOT EDIT -->

---
id: "5.13.24"
title: "Issue Resolution Time Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.24 · Issue Resolution Time Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operational &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how long it takes your team to fix each type of network problem — from the moment the system detects it to the moment it is resolved. This tells management which problems get fixed quickly and which ones sit too long, so they can improve the process for the slow ones.*

---

## Description

Measures how long Catalyst Center Assurance issues take to resolve, broken down by priority and category — giving operations leadership a data-driven MTTR metric that reveals which issue types are handled quickly and which languish for days, enabling targeted process improvements.

## Value

MTTR is the single most important operational performance metric. A P1 MTTR of 30 minutes is excellent; a P1 MTTR of 4 hours means your escalation process is broken. Tracking MTTR by category reveals structural bottlenecks: if Connectivity issues resolve in 1 hour but Onboarding issues average 8 hours, the identity/RADIUS team needs more resources or better runbooks. The trend over months proves whether process improvements (new runbooks, SOAR automation, staffing changes) are actually reducing resolution times or just redistributing the problem.

## Implementation

Same `issue` input as UC-5.13.21. MTTR is approximated by the time between first and last poll for each `issueId`. For precise timestamps, use `lastOccurenceTime` if available. Schedule as a monthly report for operations leadership.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — same `issue` data feed.
- Retain **30–90+ days** of issue data for meaningful MTTR statistics. Monthly reporting needs at least 30 days; quarterly comparisons need 90+ days.
- Understand the MTTR calculation method: this UC approximates resolution time using `earliest(_time)` (first poll where the issue appeared) and `latest(_time)` (last poll where the issue was active) per `issueId`. This is bounded by the poll interval — a 900s interval means ±15 minutes precision. For sub-minute MTTR, you'd need webhook-based real-time event data (UC-5.13.64).
- Decide whether to include auto-resolved issues in the MTTR calculation. Auto-resolved issues (transient problems that clear within 1-2 polls) produce very short MTTRs that may not reflect human response time.

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. For the most accurate MTTR, ensure the `issue` input runs consistently (no gaps) so `earliest/_time` and `latest/_time` accurately bracket each issue's active window.

Confirm resolved issues are in the data:
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-30d
| stats count by status
```
You should see both `ACTIVE` and `RESOLVED` (or equivalent). If only `ACTIVE` appears, the TA may filter resolved issues — check the input configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(status) as final_status by issueId, priority, category, name
| where final_status="RESOLVED"
| eval resolve_hrs=round((last_seen-first_seen)/3600,1)
| stats avg(resolve_hrs) as avg_mttr median(resolve_hrs) as median_mttr perc95(resolve_hrs) as p95_mttr count as resolved_count by priority, category
| sort priority
```

Why `earliest(_time)` and `latest(_time)` per `issueId`: for each unique issue, this captures the first time it appeared in Splunk data (creation) and the last time it was polled (before resolution or at resolution). The difference approximates the active duration.

Why `final_status="RESOLVED"`: only measures issues that were actually resolved. Active issues are excluded because their MTTR is incomplete (still running). For a view including active issues' age, see the variant below.

Why `median` over `avg`: average MTTR is heavily skewed by outliers (a single 30-day issue drags the average from 2h to 8h). Median gives the "typical" resolution time. P95 shows the worst-case excluding extreme outliers.

Why `by priority, category`: breaks MTTR into actionable segments. A high MTTR for "P2 / Onboarding" issues tells you the identity team's response process needs improvement, not the network team's.

Variant — active issue age (how old are currently-unresolved issues):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| stats earliest(_time) as first_seen by issueId, priority, category, name
| eval age_hrs=round((now()-first_seen)/3600,1)
| sort -age_hrs
| head 20
```

Schedule as Report: monthly (cron `0 7 1 * *`), output to PDF for the operations review meeting.

### Step 3 — Validate
(a) Pick a resolved issue from the results. Check its `first_seen` and `last_seen` timestamps against the issue's timeline in **Catalyst Center > Assurance > Issues > [issue detail]**. The Splunk-calculated MTTR should approximate the Catalyst Center-displayed resolution time (within the poll interval precision).

(b) Sanity check: P1 average MTTR should be shorter than P3 average (critical issues are resolved faster). If P1 MTTR > P3 MTTR, investigate — it may indicate that P1 issues are harder to resolve, or that the classification is wrong.

(c) Check for auto-resolution inflation: `| where resolve_hrs < 0.5 | stats count`. If this is > 50% of resolved issues, auto-resolved transients are dominating. Consider filtering them for a human-response MTTR view.

(d) Compare with your ITSM's MTTR for the same period. If the Splunk MTTR is significantly different from ServiceNow/Jira MTTR, the definitions may differ (Splunk measures from AI detection; ITSM measures from ticket creation).

(e) Run the active issue age variant. The oldest unresolved issues are your highest-priority problem management candidates.

### Step 4 — Operationalize
Dashboard placement (on an "Operations Performance" or "SLA Metrics" dashboard):
- Table: priority | category | avg_mttr | median_mttr | p95_mttr | resolved_count.
- Bar chart: median MTTR by category, coloured by priority.
- Monthly trend: `| timechart span=1w avg(resolve_hrs) as weekly_mttr by priority` showing whether MTTR is improving or degrading.
- SLA compliance: `| eval sla_met=case(priority="P1" AND resolve_hrs<=1,"Met", priority="P1","Missed", priority="P2" AND resolve_hrs<=4,"Met", priority="P2","Missed", 1==1,"N/A") | stats count by sla_met`.

Operations review (monthly):
- Compare this month vs last month: is MTTR improving?
- Identify the category with the worst MTTR — assign a process improvement owner.
- Check the P95 — these are the long-tail issues that need Problem Management attention.
- Track the impact of process changes: if a new runbook was deployed last month for Onboarding issues, did the Onboarding MTTR improve?

Runbook (owner: Operations Manager):
1. Review monthly MTTR report.
2. For categories with MTTR > SLA target: identify the 5 slowest-resolved issues. Were they slow due to detection delay, triage delay, or fix delay?
3. For detection delay: improve alerting (UC-5.13.23) or reduce poll interval.
4. For triage delay: improve runbooks (who responds, what to check first).
5. For fix delay: invest in automation (SOAR, UC-5.13.76) or team capacity.

### Step 5 — Troubleshooting

- **All MTTRs show 0 hours** — `first_seen ≈ last_seen` because issues are auto-resolved within one poll cycle. Filter `| where resolve_hrs > 0` or reduce the poll interval for better precision.

- **No RESOLVED issues in the data** — the TA may not include resolved issues. Check `| stats values(status)`. If only ACTIVE appears, the TA filters resolved issues server-side — check the input configuration for a status filter option.

- **MTTR looks unrealistically long (hundreds of hours)** — a few long-standing issues are skewing the average. Use `median` instead of `avg`. Or filter `| where resolve_hrs < 168` (cap at 1 week) to exclude chronic issues.

- **`resolve_hrs` is negative** — clock skew between Splunk and Catalyst Center. Check `_indextime - _time` distribution.

- **Monthly MTTR trend fluctuates wildly** — small sample sizes. If only 5 P1 issues resolve per month, one outlier changes the median by hours. Require `| where resolved_count >= 10` for statistically meaningful MTTR.

- **ITSM MTTR ≠ Splunk MTTR** — different measurement points. Splunk measures from AI detection to issue resolution in Catalyst Center. ITSM measures from ticket creation to ticket closure. The gap between them is the detection-to-ticket delay — itself a valuable metric.

- **Auto-resolved issues dominate** — create two views: "MTTR including auto-resolution" (system efficiency) and "MTTR excluding auto-resolution" (team response time). The `| where resolve_hrs >= 0.5` filter separates them.

- **Issue re-opening not reflected** — the current SPL treats each `issueId` as one lifecycle. An issue that's resolved and re-opened appears as one long event. For per-cycle MTTR, use `streamstats` to detect status transitions.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(status) as final_status by issueId, priority, category, name
| where final_status="RESOLVED"
| eval resolve_hrs=round((last_seen-first_seen)/3600,1)
| stats avg(resolve_hrs) as avg_mttr median(resolve_hrs) as median_mttr perc95(resolve_hrs) as p95_mttr count as resolved_count by priority, category
| sort priority
```

## Visualization

(1) Table: priority, category, avg_mttr, median_mttr, p95_mttr, resolved_count. (2) Bar chart: median MTTR by category, coloured by priority. (3) Timechart: `| timechart span=1w avg(resolve_hrs) by priority` for monthly MTTR trending. (4) Histogram: MTTR distribution `| bin resolve_hrs span=2 | stats count by resolve_hrs` to see the shape — bimodal (fast fixes + slow escalations) vs normal.

## Known False Positives

**Auto-resolved issues skewing MTTR downward.** Catalyst Center auto-resolves some transient issues (brief device unreachability, temporary client health dips) within 1-2 poll cycles, producing sub-30-minute MTTR that doesn't reflect human response time. Distinguish by checking whether `resolve_hrs < 0.5` — these are likely auto-resolved. Suppress by filtering `| where resolve_hrs >= 0.5` for human-response MTTR, and tracking auto-resolution separately.

**Long-standing known issues inflating MTTR upward.** Issues associated with known bugs or deferred maintenance may persist for weeks or months, dragging up the average MTTR. Distinguish by checking for outliers in the p95 — if p95 >> median, a few long-standing issues are skewing the data. Suppress by using median instead of average for the primary metric, or by filtering known issues from a `catalyst_known_issues` lookup.

**Issue re-opening creating multiple resolution cycles.** An intermittent problem may cause the same `issueId` to be resolved and re-opened multiple times. The first_seen to last_seen span would include the entire lifecycle, not individual resolution cycles. Distinguish by checking `| stats count by issueId | where count > 100` for issues with many poll events. Track individual resolution cycles with `streamstats` for more precise MTTR.

**Poll interval limiting MTTR precision.** At a 900s poll interval, the minimum measurable MTTR is ~15 minutes. Issues resolved between polls (e.g., a 3-minute AP reboot) show MTTR of 0 or 15 minutes, not the actual resolution time. Distinguish by noting that all sub-15-minute MTTRs are estimates. For precise MTTR, use webhook events (UC-5.13.64) which provide real-time timestamps.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [ITIL MTTR and SLA Measurement Best Practices](https://www.atlassian.com/incident-management/kpis/common-metrics)
