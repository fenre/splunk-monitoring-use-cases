<!-- AUTO-GENERATED from UC-5.13.17.json — DO NOT EDIT -->

---
id: "5.13.17"
title: "Network Health Score Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.17 · Network Health Score Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We draw a line chart showing how healthy the network has been over time — day by day, week by week, month by month. When the line goes down, something got worse. When it goes up, an upgrade or fix worked. The line also shows whether the network is slowly getting worse over months, which helps plan when to invest in improvements before things break.*

---

## Description

Tracks the aggregate network health score over time, revealing trends invisible in a single snapshot — the gradual post-upgrade improvement, the seasonal holiday dip, the slow degradation that's been masked by daily fluctuations. This is the line graph your CIO will look at in the quarterly business review.

## Value

UC-5.13.16 shows today's number. This UC shows the *story behind the number*. A network health score of 85 today is meaningless without context — was it 90 last month (degradation) or 75 (improvement)? The trend line answers three executive questions: (1) Is the network getting better or worse? (2) Did that infrastructure investment pay off? (3) When should we expect to breach our SLA based on the current trajectory? Since this sourcetype is only ~48 KB/day, you can retain 365+ days for year-over-year comparison at negligible cost.

## Implementation

Same data feed as UC-5.13.16 — no additional input. Ensure the `catalyst` index has 365+ day retention for this sourcetype (it's so lightweight that cost is not a concern). Place the timechart as a full-width panel on the executive and NOC dashboards.

## Detailed Implementation

### Prerequisites
- UC-5.13.16 must be operational — same `networkhealth` data feed. No additional input configuration.
- Index retention: set `frozenTimePeriodInSecs` for the `catalyst` index to at least **31,536,000** (365 days) for year-over-year trending. The `networkhealth` sourcetype generates only ~48 KB/day, so 365 days = ~17 MB total — the retention cost is negligible. This long history is the primary value of Splunk over Catalyst Center's 7-day window.
- Agree with leadership on the SLO reference line value: 80? 85? 90? This goes on the chart as a visual reference. The same number should appear in your SLA documentation.

### Step 1 — Configure data collection
No additional configuration. Same `networkhealth` input as UC-5.13.16. Confirm data is flowing with sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" earliest=-90d
| stats earliest(_time) as first_event latest(_time) as last_event count
| eval days_of_data=round((last_event-first_event)/86400,1)
| table first_event, last_event, days_of_data, count
```

### Step 2 — Create the search and dashboard panel
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| timechart span=1h latest(healthScore) as health_score
| eval health_score=round(health_score,1)
```

Why `latest()` not `avg()`: there's only ~1 event per poll, and we want the most recent value in each hour, not an average of possibly-duplicated events. `latest()` gives the cleanest point-per-hour for a smooth trend line.

Why `where healthScore > 0`: filters Assurance recomputation artifacts that briefly report 0 (see UC-5.13.16 Known False Positives). Without this, the trend line shows dramatic dips to 0 that aren't real.

Why `span=1h` as default: at 900s poll interval, each hour has ~4 data points. `span=1h` produces clean lines for 7-day and 30-day views. For daily views during incidents, use `span=15m`. For quarterly/annual views, use `span=1d`.

For week-over-week comparison (executive dashboard):
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| eval week=if(_time > relative_time(now(), "-7d@d"), "This week", "Last week")
| eval plot_time=if(week="Last week", _time + 604800, _time)
| timechart span=1h latest(healthScore) as health_score by week
```

For multi-month trend with daily granularity:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| timechart span=1d avg(healthScore) as daily_health
| trendline sma7(daily_health) as seven_day_avg
```

This is a dashboard panel, not an alert. For alerting on health drops, use UC-5.13.18.

### Step 3 — Validate
(a) Run the search over the last 7 days. The line should be generally smooth with values between 70 and 100. Brief dips should correspond to known maintenance or incidents.

(b) Compare the overall trend direction with your operational experience: if you know the network has been stable, the line should be flat. If you recently completed a major upgrade, you should see a step improvement.

(c) Check for gaps: `index=catalyst sourcetype="cisco:dnac:networkhealth" | timechart span=1h count | where count=0`. Zero-count hours indicate polling interruptions.

(d) Verify the `healthScore > 0` filter is working: run without the filter and check for dips to exactly 0 that recover in the next data point. These are recomputation artifacts and should be filtered.

(e) Cross-reference the general trend shape with **Catalyst Center > Assurance > Health** over the same period. Exact values won't match (different aggregation) but the directional trend should agree.

### Step 4 — Operationalize
Dashboard placement:
- **Full-width panel on the NOC dashboard**, typically Row 2 below the single-value health tiles from UC-5.13.16.
- **Full-width panel on the executive dashboard** with 90-day default range and SLO reference line.
- Time-picker presets: "Last 24 hours" (incident), "Last 7 days" (weekly ops), "Last 30 days" (monthly review), "Last 90 days" (quarterly), "Last 365 days" (annual comparison).
- SLO reference line: horizontal line at 85 (or your agreed target). Use Dashboard Studio annotation or `| eval slo=85` with a secondary series.
- Maintenance annotations: vertical markers for change windows overlaid on the chart.

Interpretation guide (add to dashboard documentation):
- **Gradual upward slope**: network health improving — investments paying off.
- **Gradual downward slope** (1–2 points/month): slow degradation — fleet aging, growing utilisation, or deferred maintenance. Action: schedule capacity review.
- **Step-change (sudden shift)**: correlate with changes — upgrade, config push, design change. If up, celebrate. If down, investigate.
- **Oscillating pattern**: indicates instability — RRM adjustments, HVAC cycles affecting equipment, or recurring AP reboots. Investigate the periodicity.
- **Flat line**: stable network — this is the ideal state. Continue monitoring for any break from stability.

Capacity review (quarterly):
- Query: `<base search> | timechart span=1d avg(healthScore) as daily | stats avg(daily) as quarterly_avg`. Compare current quarter vs previous quarter. Declining averages warrant a remediation plan.

### Step 5 — Troubleshooting

- **Line drops to 0 periodically** — the `| where healthScore > 0` filter is missing from the search. Add it.

- **No data for extended periods** — the `networkhealth` input stopped running. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR` for the gap period.

- **Score suddenly jumps 5–10 points after Catalyst Center upgrade** — the scoring algorithm changed. This is documented in Catalyst Center release notes. Annotate the chart with the upgrade date and note the scoring change in your SLA documentation.

- **Trend shows no variation (perfectly flat)** — your network may be genuinely stable (ideal), or the API is returning cached values. Verify by checking `_time` and `_indextime` — if `_indextime - _time > 3600`, the data may be stale. Restart the input.

- **Week-over-week comparison shows wildly different patterns** — check for maintenance windows, holidays, or other calendar-driven effects. Overlay with a `catalyst_calendar` lookup for context.

- **SLO reference line doesn't appear in the chart** — Dashboard Studio and Simple XML handle reference lines differently. In Simple XML, use `<option name="charting.chart.overlayFields">slo</option>`. In Dashboard Studio, use the annotation layer.

- **Historical data was lost after index rollover** — check `frozenTimePeriodInSecs` for the `catalyst` index. If it's set to the default (188697600 seconds = ~6 years), data loss is unlikely. If it was set too short (e.g., 2592000 = 30 days), extend it and accept the gap.

- **Trend line doesn't match the CIO's expectations** — the CIO may be comparing against a different time window, a different Catalyst Center cluster, or a metric from a different dashboard. Align by presenting the exact search, time range, and data source on the dashboard.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| timechart span=1h latest(healthScore) as health_score
| eval health_score=round(health_score,1)
```

## Visualization

(1) Line chart: `health_score` over the selected range with y-axis 0–100 and an SLO reference line at 85. (2) Stat panel: current score, 7-day average, 30-day average, and 90-day average — showing improvement/degradation at each timescale. (3) Change-window annotations: vertical markers for firmware pushes, major incidents, and infrastructure changes from `catalyst_maintenance_windows` or `index=catalyst sourcetype="cisco:dnac:audit:logs"`. (4) Week-over-week overlay: this week's line vs last week's for quick comparison.

## Known False Positives

**Planned maintenance window causing expected health score dip.** During firmware upgrades or network redesign work, the health score temporarily drops and then recovers. Distinguish by correlating with ITSM change records or audit logs. Suppress by annotating the chart with maintenance windows so viewers understand the dip was planned.

**Assurance recomputation creating brief dips to 0.** The `| where healthScore > 0` filter in the SPL handles this by excluding recomputation artifacts. Without the filter, brief drops to 0 appear as dramatic dips in the trend.

**Catalyst Center upgrade changing the scoring algorithm.** A Catalyst Center version upgrade may recalibrate how `healthScore` is computed, creating a step-change in the trend line that doesn't reflect an actual network change. Distinguish by checking whether the step-change coincides with a Catalyst Center upgrade date. Annotate the trend with the upgrade date.

**Seasonal patterns (holidays, campus closures).** During holidays or semester breaks, reduced traffic and fewer connected devices can cause the health score to rise (fewer failure sources) or fall (standby devices not maintained). Distinguish by overlaying the trend with a calendar of closures.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Network Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk timechart command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart)
