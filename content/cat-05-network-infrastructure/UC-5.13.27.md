<!-- AUTO-GENERATED from UC-5.13.27.json — DO NOT EDIT -->

---
id: "5.13.27"
title: "Issue Volume Anomaly Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.27 · Issue Volume Anomaly Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*We use statistics to spot when the number of network problems suddenly spikes above what is normal for your network. A flood of 30 problems appearing at once usually means something big went wrong — like a bad software update or a power failure — even if each individual problem looks minor by itself. We catch that pattern before anyone has to count them manually.*

---

## Description

Applies statistical anomaly detection to the volume of active Assurance issues, flagging time periods where the issue count spiked significantly above its historical baseline — catching correlated failure events where 30 devices simultaneously report P3 issues that no individual alert would escalate, but the volume spike is unmistakable evidence that something systemic just happened.

## Value

A P1 alert (UC-5.13.23) catches one critical issue. This UC catches 50 P3 issues appearing simultaneously — which collectively represent a major event that no single P3 alert would trigger. When a firmware push goes wrong and 30 switches simultaneously report 'Configuration Non-Compliance,' no individual issue is P1, but the volume spike is 4 standard deviations above normal. This UC detects correlated failure events by their statistical signature: an issue count that's unusually high compared to your network's normal volume. It's the difference between 'we have a few more issues than usual' and 'something systemic just happened and 30 devices are affected.'

## Implementation

Same `issue` input as UC-5.13.21. Schedule as twice-daily report (not real-time alert — the baseline shifts with each search window). Use 14-day lookback for stable baselines. Focus on upward anomalies (`issue_count > baseline + 2σ`) — unlike health scores, higher issue counts are always bad.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) and UC-5.13.22 (Issue Trending) must be operational — same `issue` data feed.
- **Minimum 7 days of historical data** for meaningful baselines. 14 days recommended. The `issue` sourcetype at 30 active issues produces ~1.7 MB/day, so even 90 days of history is affordable.
- This UC detects **upward** anomalies (issue spikes) rather than downward anomalies. A lower-than-normal issue count is good, not anomalous. The `where issue_count > (baseline + 2σ)` uses `>` (above baseline), not `<` (below baseline) as in UC-5.13.20 (health score anomalies).
- This is a **run-tier** analytical view for twice-daily engineering review, not a real-time paging alert. The `eventstats` baseline shifts with every search window — the results are interpretive, not deterministic.
- Document that changing the time picker changes the baseline — this is a feature (compare different baseline periods) but must be understood by operators.

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. No additional configuration.

Confirm sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-14d
| stats earliest(_time) as first latest(_time) as last count
| eval days=round((last-first)/86400,1)
| table first, last, days, count
```
If `days < 7`, wait until enough data accumulates before deploying this UC.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| bin _time span=4h
| stats dc(issueId) as issue_count by _time
| eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues
| where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0
| eval deviation=round((issue_count-baseline)/stdev_issues,1)
| sort -deviation
```

Why `status != "RESOLVED"`: counts only active issues. Including resolved issues would measure total issue churn (discovery + resolution) rather than active backlog size. For backlog anomaly detection, active-only is the right metric.

Why `dc(issueId)` not `count`: `count` inflates with poll frequency. `dc(issueId)` per time bucket gives the actual number of unique active issues in that period. This is essential for accurate anomaly detection — poll-inflated counts would produce artificially high baselines and mask real spikes.

Why `span=4h`: balances detail with noise. At `span=1h`, natural intra-day variation (more issues during business hours, fewer at night) may produce frequent false anomalies because the flat-baseline `eventstats` doesn't account for time-of-day patterns. At `span=1d`, short multi-hour spikes are averaged out and invisible. `span=4h` captures meaningful multi-hour events while smoothing within-hour noise. Each day has 6 data points — enough resolution to spot correlated events.

Why `> (baseline + 2σ)` not `< (baseline - 2σ)`: for issue volume, ABOVE normal is the problem. Below-normal volume is good (fewer issues = healthier network). This is the opposite of health-score anomaly detection (UC-5.13.20) where BELOW normal is the problem.

Why `stdev_issues > 0` guard: networks with perfectly constant issue counts (stdev = 0) would false-fire on any variation. The guard skips detection when the issue count is too stable to analyse statistically — which paradoxically means the network is very consistent (good or consistently bad).

For time-of-day-aware anomaly detection (reduces false positives during business hours):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| bin _time span=4h
| stats dc(issueId) as issue_count by _time
| eval hour_bucket=strftime(_time, "%H")
| eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues by hour_bucket
| where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0
| eval deviation=round((issue_count-baseline)/stdev_issues,1)
| sort -deviation
```
The `by hour_bucket` computes separate baselines for each time-of-day slot, so a business-hours spike is compared against historical business-hours volumes, not against overnight volumes.

For drilldown into a specific anomalous bucket:
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED" earliest=<bucket_start> latest=<bucket_end>
| stats dc(issueId) as count by name, category, priority
| sort -count
```
This shows WHAT issues caused the spike — the specific issue types and categories that drove the volume above the baseline.

Schedule as Report: cron `0 7,19 * * *` (twice daily, 7 AM and 7 PM), time range `-14d to now`. Output to the Anomaly Detection dashboard panel.

### Step 3 — Validate
(a) Run the search over the last 14 days. You should see 0–5 anomalous time periods. If you see > 20, sigma is too low or the baseline window is too short (noisy baselines from insufficient data).

(b) Cross-reference: pick an anomalous period from the results. Open UC-5.13.22 (Issue Trending) for the same time range. You should see a visible spike in the timechart at that time. If the spike is invisible in the trend, the sigma is too sensitive — increase to 2.5 or 3.

(c) Known incident check: if a firmware push or major event occurred last week, the anomaly detection should flag the corresponding time period. If it misses the event, the sigma is too high (too conservative) — decrease to 1.5.

(d) Baseline stability: compare results for 7-day vs 14-day search windows. The same major spikes should appear in both. If the results change dramatically between windows, the baseline is unstable — prefer the longer window.

(e) Drilldown test: for the top anomaly, run the drilldown search from Step 2. The results should show which issue types caused the spike — this is the actionable intelligence.

(f) False positive assessment: how many of the detected anomalies correspond to known maintenance windows or approved changes? Document each and add maintenance annotations to the chart.

### Step 4 — Operationalize
Dashboard placement (on the "Advanced Analytics" or "Network Anomaly" dashboard):
- Table of anomalous time periods with `_time`, `issue_count`, `baseline`, `deviation` — sorted by deviation descending.
- Line chart: `issue_count` over the search window with shaded band for `baseline ± 2σ`. Points above the upper band are highlighted in red.
- Single value: count of anomalous periods in the last 7 days (yellow ≥ 1, red ≥ 3).
- Drilldown: click a spike → populate a dependent panel showing the top issue names and categories from that period.

Interpretation guide:
- **Deviation > 4σ**: major correlated event. This is almost certainly a real incident or major maintenance impact. Check UC-5.13.21 for the dominant issue category and UC-5.13.26 for the affected devices/sites. Correlate with UC-5.13.46 (audit log) for the change that triggered it.
- **Deviation 2–4σ**: elevated issue volume. May be a minor change impact, a growing trend, or a recurring scheduled event. Investigate but don't escalate unless confirmed.
- **Same time-of-day appearing across multiple days**: recurring correlated event (e.g., backup window causing interface flaps, DHCP lease expiry wave, RRM optimisation cycle). The time-of-day-aware variant from Step 2 handles this.

Twice-daily engineering review:
1. Open the anomaly table at 7 AM. Any new anomalies from overnight?
2. For each: drilldown to see what issues spiked. Correlate with maintenance windows (UC-5.13.46) and device health changes (UC-5.13.1).
3. Document findings in the daily ops handoff notes.

### Step 5 — Troubleshooting

- **Every business day is flagged as anomalous** — the flat baseline doesn't account for time-of-day patterns. Use the `by hour_bucket` variant from Step 2 for hour-aware baselines.

- **No anomalies ever detected** — issue volume is very stable (good!), or sigma is too high (too conservative). Try 1.5σ to test sensitivity. Also verify the search window has enough data points (at least 7 days × 6 buckets/day = 42 data points).

- **Anomaly detected after every maintenance window** — expected. The maintenance window generates a legitimate issue spike. Suppress by annotating maintenance windows and filtering: `| lookup catalyst_maintenance_windows _time OUTPUT in_window | where in_window != "yes"` before `eventstats`.

- **`stdev_issues` is very small, causing false anomalies from tiny variations** — the issue count barely varies day to day, so even +1 issue triggers the anomaly. Add a minimum-delta guard alongside the sigma check: `| where issue_count > (baseline + 2*stdev_issues) AND issue_count > baseline + 5`. The `+ 5` absolute threshold ensures only meaningful spikes (not +1 noise) trigger detection.

- **Drilldown shows all issues are P4 informational** — the spike is from Assurance adding new informational detections (common after Catalyst Center upgrades), not from network degradation. Filter to `| where priority IN ("P1","P2","P3")` for operational anomaly detection that excludes informational noise.

- **Search returns different results depending on time picker** — expected. The `eventstats` baseline is computed from the search window. A 7-day window produces a different baseline than a 14-day window. Document this for operators: "use a fixed 14-day window for consistent results."

- **Issue count in Splunk ≠ Catalyst Center** — the GUI shows the *current* snapshot; this search shows historical unique issue counts per time bucket. They measure different things and are not directly comparable.

- **Performance concern** — the `issue` sourcetype is moderate volume (~1.7 MB/day for 30 issues). A 14-day `eventstats` window processes ~84 four-hour buckets — negligible compute. This is much lighter than UC-5.13.7 (device-level anomaly detection) which runs across thousands of device-hour combinations.

- **Want to detect volume drops too (not just spikes)** — a sudden drop in issue count could mean the `issue` input stopped or Catalyst Center itself is down. Add a companion search: `| where issue_count < (baseline - 2*stdev_issues) AND baseline > 5` to detect unusual drops. This catches collection failures that UC-5.13.74 (Data Collection Health) also monitors.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| bin _time span=4h
| stats dc(issueId) as issue_count by _time
| eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues
| where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0
| eval deviation=round((issue_count-baseline)/stdev_issues,1)
| sort -deviation
```

## Visualization

(1) Table: anomalous time buckets with issue_count, baseline, deviation — sorted by deviation descending. (2) Line chart: issue_count over the search window with shaded band for baseline ± 2σ. Points above the upper band are anomalies. (3) Single value: count of anomalous time periods in the last 7 days. (4) Drilldown: click an anomalous bucket → filter UC-5.13.21 to that time range to see which specific issues caused the spike.

## Known False Positives

**Catalyst Center upgrade adding new issue detection capabilities.** After upgrading Catalyst Center, the Assurance engine may detect issue types it previously missed, creating a legitimate spike in issue volume that's not a network degradation event. Distinguish by checking whether new issue `name` values appeared coincident with the upgrade. Suppress by annotating the chart with upgrade dates and allowing a 48-hour stabilisation window.

**Scheduled maintenance causing a correlated issue burst.** A firmware push affecting many devices simultaneously generates issues (Device Unreachable, Config Non-Compliant) that spike the volume. Distinguish by correlating with ITSM change records or `index=catalyst sourcetype="cisco:dnac:audit:logs"` for SWIM activity. Suppress with `catalyst_maintenance_windows` lookup.

**Issue volume naturally higher during business hours.** More clients connected during business hours means more potential issues detected. If the baseline doesn't account for time-of-day patterns, business-hour volumes may appear anomalous compared to a flat 24-hour average. Suppress by using `| eventstats avg(issue_count) as baseline by date_hour` for hour-of-day-aware baselines.

**Single high-impact event generating many correlated issues.** An upstream router failure may cause 30 related issues (each downstream device reports unhealthy). This IS a real event — do not suppress. But note that the root cause is one device, not 30.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk eventstats command — statistical overlays](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eventstats)
