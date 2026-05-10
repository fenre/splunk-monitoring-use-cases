<!-- AUTO-GENERATED from UC-5.13.20.json — DO NOT EDIT -->

---
id: "5.13.20"
title: "Network Health Score Anomaly Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.20 · Network Health Score Anomaly Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*We use statistics to spot when the overall network health dips below what is normal for *your* network — not just below some one-size-fits-all number. A network that usually scores 92 and drops to 78 is in trouble, even if 78 sounds fine. We catch that kind of unusual drop before it becomes a real outage.*

---

## Description

Applies statistical anomaly detection to the aggregate network health score, flagging hours where the score dropped significantly below its own historical baseline — catching degradation that fixed-threshold alerts (UC-5.13.18) miss because the network normally runs at 92 and dropped to 78, which is above the threshold of 70 but deeply anomalous for *this* network.

## Value

Fixed thresholds can't account for networks that naturally run at different health levels. A hospital campus that normally scores 95 and drops to 80 is in serious trouble — but 80 is 'healthy' by fleet standards. A retail chain that normally scores 78 and drops to 65 is also anomalous — but from a completely different baseline. This UC catches both by computing per-network baselines from history. It also catches *gradual* degradation that never crosses the fixed threshold: a network slowly declining from 92 to 75 over 6 weeks won't trigger UC-5.13.18's threshold of 70, but the 2σ anomaly detection will flag the hours at 75 as unusual compared to the 92 baseline.

## Implementation

Requires UC-5.13.16 and UC-5.13.17 with at least 7 days of retained data. Schedule as a twice-daily report (not real-time alert) because the statistical baseline shifts with each search window. Use 14-day lookback for stable baselines.

## Detailed Implementation

### Prerequisites
- UC-5.13.16 (Network Health Overview) and UC-5.13.17 (Network Health Trending) must be operational — same `networkhealth` data feed.
- **Minimum 7 days of historical data** in the `catalyst` index. The `eventstats` baseline needs enough hourly samples to produce meaningful `avg` and `stdev` values. Rule of thumb: 7 days = 168 hourly buckets; 14 days = 336 (more stable baselines). The `networkhealth` sourcetype is only ~48 KB/day, so even 90 days of history is trivial to store.
- **Search performance**: `eventstats` runs across ALL rows in the result set. For `networkhealth` (one event/poll), 14 days = ~1,344 events × 6 computed fields = negligible. This is the lightest anomaly detection search in the Catalyst Center family.
- This UC is a **run-tier** analytical view, not a real-time alert. It's designed for twice-daily review by network engineering, not NOC paging. For real-time alerting on health drops, use UC-5.13.18.
- Document that this technique uses a **same-window rolling baseline** — changing the time picker changes the baseline, which changes the results. This is a feature (you can compare "last 7 days" vs "last 30 days" baselines) but it must be understood by operators.

### Step 1 — Configure data collection
No additional configuration. Same `networkhealth` input as UC-5.13.16.

Confirm sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" earliest=-14d
| stats earliest(_time) as first latest(_time) as last count
| eval days=round((last-first)/86400,1)
| table first, last, days, count
```
If `days < 7`, wait until enough data accumulates.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| bin _time span=1h
| stats avg(healthScore) as health by _time
| eventstats avg(health) as baseline stdev(health) as stdev_health
| where health < (baseline - 2*stdev_health) AND stdev_health > 0
| eval deviation=round((baseline-health)/stdev_health,1)
| sort -deviation
```

Why `where healthScore > 0` first: filters Assurance recomputation zeros that would corrupt the baseline. A single zero in a 7-day window can shift the mean by 1–2 points and inflate the stdev by 3–5 points, masking real anomalies or generating false ones.

Why `bin _time span=1h` + `stats avg()`: at 900s intervals, each hour has ~4 data points. Averaging them into hourly buckets smooths within-hour jitter. Without binning, `eventstats` would run on raw 15-minute polls — noisier and 4× more rows.

Why `eventstats` not `streamstats`: `eventstats` computes baseline and stdev across the *entire* result set (all hourly buckets in the search window). This gives a single, stable baseline for the whole period. `streamstats` would compute a rolling window, which drifts as new data arrives — useful for continuous monitoring but harder to interpret in a diagnostic report.

Why 2σ (two standard deviations): for roughly-normal health score distributions, ~95% of hourly averages fall within ±2σ of the mean. An hour below (baseline - 2σ) is in the bottom 2.5% — unusual enough to investigate. Tune to 2.5σ or 3σ if you see too many results (more conservative), or 1.5σ for more sensitive detection.

Why `stdev_health > 0` guard: a network with perfectly constant health (stdev = 0) would produce division-by-zero in the deviation calculation and false-fire on any minor fluctuation. This guard skips detection when the score is too stable to analyse statistically.

Schedule as Report: cron `0 7,19 * * *` (7 AM and 7 PM daily), time range `-14d to now`. Output to the Anomaly Detection dashboard panel. Do NOT schedule as a paging alert — the statistical baseline shifts with every run.

### Step 3 — Validate
(a) Run the search over the last 14 days. You should see 0–5 anomalous hours. If you see > 20, the sigma multiplier is too low or the search window is too short (noisy baselines).

(b) Cross-reference: pick an anomalous hour from the results. Check UC-5.13.17 (trending) for that same hour — you should see a visible dip in the trend line. If the anomaly is invisible in the trend, the sigma is too sensitive.

(c) Known incident check: review the last 30 days for any known network incidents. The anomaly detection should flag hours correlating with those incidents. If it misses them, the sigma is too high.

(d) Baseline stability test: run the search with `-7d` and again with `-14d`. The same hours should appear in both results. If the results change dramatically, the 7-day baseline is too unstable — prefer 14 days.

(e) Compare with UC-5.13.18 (fixed-threshold): did the anomaly detection catch hours that the fixed threshold missed? If yes, the statistical approach is adding value beyond the fixed alert.

### Step 4 — Operationalize
Dashboard placement (dedicated "Network Anomaly Detection" panel or on the Advanced Analytics dashboard):
- Table: anomalous hours with _time, health, baseline, deviation — sorted by deviation descending.
- Line chart: `health` over the search window with shaded band for `baseline ± 2σ`. Anomalous hours are the points below the lower band.
- Single value: "Anomalous hours in last 7 days" (yellow ≥ 1, red ≥ 5).

Interpretation guide:
- **High deviation (> 4σ)**: severe event — likely a major incident or maintenance window. If it corresponds to a known change, annotate and move on. If unexpected, investigate immediately.
- **Moderate deviation (2–4σ)**: notable but not catastrophic. May indicate a gradual issue (link degradation, increasing error rates) or a minor change impact.
- **Same hour appearing across multiple runs**: persistent degradation at that time of day. May be caused by a scheduled process (backups, batch jobs) or a recurring environmental factor (HVAC cycle, power fluctuation).
- **No anomalies ever detected**: the network is very stable (good!), or the sigma is too high. Try 1.5σ to test sensitivity.

Capacity review:
- If anomalies are clustering at the same times each day, investigate the time-correlated cause rather than the network infrastructure.

### Step 5 — Troubleshooting

- **Hundreds of rows returned** — baseline window too short, sigma too low, or a major event shifted the entire window. Solutions: extend to 14+ days, increase to 2.5σ or 3σ, or exclude the major-event period.

- **No rows ever returned** — the network is very stable (stdev near 0 and the guard `stdev_health > 0` is filtering). This is the expected state for a well-managed network. Lower sigma to 1.5 if you want to detect subtle variations.

- **Same hours flagged on every run** — the network has permanently shifted to a lower health level. The baseline will eventually adjust, but in the meantime those hours keep appearing. Acknowledge them by extending the search window so the new level becomes part of the baseline.

- **Anomalies appear only on weekends or holidays** — reduced traffic changes the health score computation differently. Use `| eventstats avg(health) as baseline by date_wday` for day-of-week-aware baselines.

- **Search returns different results depending on time range** — expected. The baseline is computed from the search window. A 7-day window after a major incident has a depressed baseline, making normal hours look anomalous. A 30-day window dilutes the incident's effect. Choose the window that best represents "normal" for your network.

- **`healthScore` suddenly shifts 5–10 points after Catalyst Center upgrade** — the Assurance scoring algorithm changed. The old baseline is no longer valid. Wait 7–14 days for the new baseline to stabilise, then resume anomaly detection.

- **Deviation is extremely high (> 10σ)** — the hour experienced a catastrophic drop (e.g., from 90 to 10). Verify it's real by checking `index=catalyst sourcetype="cisco:dnac:networkhealth"` raw events for that hour. If `healthScore=0`, it's likely a recomputation artifact — add `| where healthScore > 0` if not already present.

- **Performance concern with long lookbacks** — the `networkhealth` sourcetype is extremely lightweight (~48 KB/day). A 90-day search window produces ~8,640 hourly buckets — `eventstats` handles this in < 1 second. No performance optimisation needed.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| bin _time span=1h
| stats avg(healthScore) as health by _time
| eventstats avg(health) as baseline stdev(health) as stdev_health
| where health < (baseline - 2*stdev_health) AND stdev_health > 0
| eval deviation=round((baseline-health)/stdev_health,1)
| sort -deviation
```

## Visualization

(1) Table: anomalous hours with `_time`, `health`, `baseline`, `stdev_health`, `deviation` — sorted by deviation descending. (2) Line chart: `health` over the search window with shaded band for `baseline ± 2σ`. Hours below the band are the anomalies. (3) Single value: count of anomalous hours in the last 7 days. (4) Scatter: `baseline` (x) vs `health` (y) for each hour — points below the diagonal are degraded.

## Known False Positives

**Planned maintenance causing health score to deviate from the statistical baseline.** During firmware upgrades or network changes, the health score drops below the normal operating range, triggering a statistical anomaly. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for planned change activity. Suppress by excluding known maintenance windows from the baseline computation: use `| where NOT (maintenance_flag=1)` before computing `eventstats`.

**Seasonal network usage pattern creating periodic deviations.** Network health may follow predictable patterns (lower during business hours, higher on weekends) that appear anomalous compared to a flat 7-day baseline. Distinguish by checking whether the same pattern occurs at the same time in previous weeks. Suppress by using a time-aware baseline: compute separate baselines for business hours and off-hours, or use day-of-week segmented statistics.

**Assurance recomputation introducing brief outliers that inflate standard deviation.** A single poll returning `healthScore=0` during recomputation will widen the standard deviation and may cause subsequent normal scores to appear anomalous. Distinguish by checking whether the outlier event has `healthScore=0` exactly (characteristic of API recomputation). Suppress by adding `| where healthScore>0` before computing the baseline (already in the default SPL).

**Major inventory change shifting the health score distribution.** Adding a large batch of devices (e.g., a new building coming online) changes the health score composition. The statistical baseline computed from prior data becomes invalid. Distinguish by tracking `totalCount` alongside `healthScore` — if the count changed significantly, the baseline needs resetting. Suppress by requiring a minimum of 48 hours of data after a significant inventory change before re-enabling anomaly detection.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Network Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk eventstats command — statistical overlays](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eventstats)
