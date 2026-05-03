<!-- AUTO-GENERATED from UC-5.9.47.json — DO NOT EDIT -->

---
id: "5.9.47"
title: "ThousandEyes Alert Timeline Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.47 · ThousandEyes Alert Timeline Trending

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Walk &middot; **Status:** Verified

*We chart how many network alerts we get each day over a month, so we can see if problems are getting worse or if our fixes are actually helping.*

---

## Description

Trends ThousandEyes alert volume over time (daily aggregation over 30 days) by severity. Reveals patterns: increasing alert volume (degrading infrastructure), seasonal patterns (business-hours congestion), and incident correlation (alert storms during outages).

## Value

A gradually increasing alert volume over weeks is a leading indicator of infrastructure deterioration that hasn't yet caused a major outage. If alert volume doubles week-over-week, something is getting worse. Conversely, a declining trend after infrastructure changes confirms the changes were effective. The daily timechart also reveals temporal patterns: if most alerts fire between 9 AM and 5 PM, the network may be capacity-constrained during business hours.

## Implementation

Same data source as UC-5.9.46. Use timechart for temporal analysis.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.19 apply — the Alerts Stream input must be configured (webhook → HEC push), and `thousandeyes_alerts` index must be receiving data. If you haven't set up alert streaming, complete UC-5.9.19 first.
- **Sufficient alert history.** This UC works best with at least 30 days of alert data. If the Alerts Stream was recently enabled, wait until enough history accumulates to identify meaningful trends.
- **ThousandEyes alerting configured.** This UC is only useful if you have meaningful alert rules in ThousandEyes. A blank alert history produces blank trends. Check ThousandEyes → Alerts → Alert Rules to verify you have active rules covering your key tests.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_alerts` (or the index the `stream_index` macro resolves to).

### Step 1 — Configure data collection
The Alerts Stream input is configured in UC-5.9.19. No additional configuration is needed.

Verify that alert data spans a sufficient time range:
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts"
| stats earliest(_time) as first_alert latest(_time) as last_alert count
| eval first_alert=strftime(first_alert, "%Y-%m-%d"), last_alert=strftime(last_alert, "%Y-%m-%d")
| eval days_of_data=round((now() - relative_time(now(), "@d")) / 86400, 0)
```
If `days_of_data` is less than 7, trending analysis will be limited. Wait for more data or use shorter spans.

**Understanding alert lifecycle in the data:**
- Each alert event in `thousandeyes_alerts` represents a state transition: `active` (alert fired), `cleared` (alert resolved), or `acknowledged` (alert acknowledged by user).
- The `severity` field values are: `info`, `minor`, `major`, `critical`. These are set in the ThousandEyes alert rule configuration.
- The `alert.rule.name` identifies the alerting rule, and `alert.test.name` identifies the test that triggered it.
- Multiple agents firing the same alert rule create multiple alert events — this inflates counts and must be accounted for in analysis.

### Step 2 — Create the search and report
**Daily alert volume by severity (primary trending view):**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-30d
| timechart span=1d count by severity
```

**Understanding this SPL**

`sourcetype="cisco:thousandeyes:alerts"` — filters to alert data only (the `stream_index` macro also returns metrics, so the sourcetype filter is essential).

`earliest=-30d` — 30-day window provides enough history to identify weekly patterns and multi-week trends. For quarterly reviews, extend to `-90d`.

`timechart span=1d count by severity` — aggregates alert counts per day, split by severity. The resulting chart shows stacked area/bars for info/minor/major/critical. If critical alerts are increasing daily, that's a strong signal of degrading infrastructure.

**Week-over-week comparison** (quantifies trend direction):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| stats count by week, severity
| xyseries severity week count
| eval pct_change=if(isnotnull('Last Week') AND 'Last Week'>0, round(('This Week' - 'Last Week') / 'Last Week' * 100, 1), "N/A")
| table severity, "Last Week", "This Week", pct_change
```
This shows per-severity: last week count, this week count, and percentage change. A +50% increase in critical alerts over one week is a red flag.

**Day-of-week breakdown** (reveals temporal patterns):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-30d
| eval day_of_week=strftime(_time, "%A")
| stats count by day_of_week, severity
| sort severity, day_of_week
```
If Monday consistently has more alerts, it may be due to maintenance windows ending, cache cold-starts, or weekly batch jobs.

**Hour-of-day breakdown** (identifies business-hour congestion):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-30d
| eval hour=strftime(_time, "%H")
| stats count by hour, severity
| sort hour
```
Alerts clustering between 09:00–17:00 suggest capacity-related issues during peak usage. Alerts clustering at 02:00–04:00 suggest maintenance or backup jobs.

**Alert storm detection** (identifies multi-alert bursts):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| bin _time span=15m
| stats count dc(alert.rule.name) as rules dc(alert.test.name) as tests by _time
| where count > 20
| sort -count
```
A burst of >20 alerts in a 15-minute window is an alert storm — typically caused by a major outage triggering multiple rules simultaneously. These storms should correlate with Internet Insights events (UC-5.9.18).

**Scheduling:** Weekly report: cron `0 9 * * 1` (Monday 9 AM), time range `-7d to now`. Generate a scheduled report (PDF or CSV) and email to the network operations team. For trending dashboards, no scheduled alert is needed — the dashboard should be on the NOC wall or reviewed in weekly operations meetings.

### Step 3 — Validate
(a) **Cross-reference with known incidents.** Identify a date when a known incident or outage occurred. The timechart should show a visible spike on that date. If no spike, check whether the alert rules in ThousandEyes were configured to fire for that type of issue.

(b) **Cross-reference with ThousandEyes UI.** Navigate to **Alerts → Alert History** in ThousandEyes and compare the alert count for a specific day with what Splunk shows. Counts may differ slightly because the ThousandEyes UI groups alerts by rule, while Splunk counts individual alert state events.

(c) **Verify severity distribution.** The severity breakdown should match your ThousandEyes alert rule configuration. If you only configured `major` and `critical` rules but Splunk shows `info` alerts, there may be default rules you're not aware of.

(d) **Check for alert rule changes.** Run UC-5.9.48 (Activity Log) for the same period. If alert rules were added or modified, annotate the timechart with those dates — otherwise, a step-change in alert volume may look like an infrastructure issue when it's actually a configuration change.

(e) **Validate deduplication.** Count unique alert instances vs total events: `| stats count dc(alert.rule.name) as unique_rules`. If `count` >> `unique_rules`, a single rule is firing many times (possibly once per agent per round). Consider deduplicating by `alert.rule.name, alert.test.name` for a cleaner trend.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes Alert Trends" — designed for weekly operations review):
- Row 1 — Single value tiles: "Alerts this week" vs "Alerts last week" with trend arrow (green = decreasing, red = increasing). "Alert-free hours this week" (green ≥ 120, yellow ≥ 80, red < 80 — out of 168 hours).
- Row 2 — Timechart: daily alert count by severity over 30 days. Stacked area chart with critical on top (red), major (orange), minor (yellow), info (blue). Add reference lines for weekly averages.
- Row 3 — Week-over-week comparison table: severity | last week | this week | % change. Colour-code the % change column (green < -10%, grey -10% to +10%, red > +10%).
- Row 4 — Day-of-week heat map: rows = severity, columns = Monday–Sunday, cells = alert count. Darker colour = more alerts. This immediately reveals temporal patterns.

**Alerting (meta-alert — alert about alerting trends):**
- Weekly alert volume increases > 50% week-over-week → email notification to network operations manager. This is a leading indicator of infrastructure degradation.
- Alert storm: > 50 alerts in 1 hour → immediate Slack notification. An alert storm usually indicates a major outage in progress.

**Monthly/quarterly review process** (owner: Network Operations Manager):
1. **Trending up.** Alert volume increasing over 4+ weeks → identify the top 3 noisiest rules (UC-5.9.46). For each: (a) Is the underlying issue real? Fix it. (b) Is the threshold too sensitive? Tune it. (c) Is the rule unnecessary? Disable it.
2. **Trending stable.** Alert volume consistent over 4+ weeks → healthy state. Check that the absolute volume is manageable (< 10 alerts/day per on-call engineer).
3. **Trending down.** Alert volume decreasing → confirm this is due to infrastructure improvements, not alert rules being silently disabled or tests being removed.
4. **Spikes.** Isolated spikes in the trend → correlate with incident records. Ensure each spike has a corresponding incident. If not, the alert-to-incident process may have gaps.
5. **Seasonal patterns.** Business-hours peaks → network capacity planning (UC-5.9.7). Weekend dips → expected, no action needed.

### Step 5 — Troubleshooting

- **Timechart shows no data for recent days** — Check that the Alerts Stream input is still running. Verify with `index=thousandeyes_alerts earliest=-1h | stats count`. If zero, the webhook may have stopped pushing (OAuth token expired, HEC endpoint unreachable). See UC-5.9.19 Step 5.

- **Alert counts seem too high** — Multiple agents firing the same rule create multiple events. Deduplicate: add `| dedup alert.rule.name, alert.test.name, _time span=5m` before the timechart to collapse multi-agent alerts into single incidents.

- **Severity values don't match expected** — ThousandEyes severity levels (info/minor/major/critical) are set per alert rule. If all alerts show the same severity, your alert rules may all use the same severity level. Review ThousandEyes → Alerts → Alert Rules.

- **Step change in alert volume not explained by incidents** — Check ThousandEyes Activity Log (UC-5.9.48) for alert rule changes (added, modified, deleted) or test changes (added, removed, modified). Configuration changes are the most common cause of unexplained alert volume shifts.

- **Week-over-week comparison shows "N/A"** — If last week had zero alerts for a severity level, percentage change can't be calculated (division by zero). The xyseries may show null for 'Last Week'. Handle with `| fillnull value=0 "Last Week" "This Week"`.

- **All common troubleshooting** — See UC-5.9.19 Step 5 for HEC webhook connectivity, OAuth token refresh, alert stream input status, and general app troubleshooting.

## SPL

```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-30d
| timechart span=1d count by severity
```

## Visualization

(1) Timechart: daily alert count by severity over 30 days. (2) Trend line: is alert volume increasing, stable, or decreasing? (3) Day-of-week breakdown: which days have the most alerts?

## Known False Positives

**Alert rule changes.** Adding new alert rules or modifying thresholds causes step changes in alert volume. Annotate the timechart with alert rule change dates.

**Test addition/removal.** Adding new tests increases alert volume; removing tests decreases it. These are configuration changes, not infrastructure changes.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes alerts documentation](https://docs.thousandeyes.com/product-documentation/alerts)
