<!-- AUTO-GENERATED from UC-5.13.7.json — DO NOT EDIT -->

---
id: "5.13.7"
title: "Device Health Score Degradation (Anomaly Detection)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.7 · Device Health Score Degradation (Anomaly Detection)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*We use statistics to spot when a device's health drops below what's normal *for that specific device* — not just below some one-size-fits-all number. A device that usually scores 90 and suddenly drops to 65 is in trouble even if 65 looks fine on paper. We catch that kind of slow, sneaky degradation before it turns into a real outage.*

---

## Description

Applies per-device statistical anomaly detection to health scores, identifying devices whose current health has dropped significantly below their *own* historical baseline — catching degradation that fixed thresholds (UC-5.13.3) miss because the device normally runs at 95 and dropped to 70, which is still above the fleet-wide threshold of 50.

## Value

Fixed thresholds work for catastrophic failures but miss slow-burn degradation. A core switch that normally runs at 92 and drops to 68 is deeply anomalous for *that* device — even though 68 is "healthy" by fleet standards. This UC catches the drift before it becomes a hard failure. It also catches devices whose health *should* have improved after a firmware push but didn't, providing post-change validation that UC-5.13.2 (trending) shows visually but this UC quantifies statistically.

## Implementation

Requires UC-5.13.1 and UC-5.13.2 with at least 7 days of retained data. The `eventstats` runs across the full result set in the search window — use a **7–14 day** lookback for a balance between baseline stability and search performance. Schedule as a twice-daily report (not real-time alert) because the statistical baseline shifts with each search.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health Overview) and UC-5.13.2 (Device Health Trending) must be operational. This UC builds on their data feed and extends it with statistical analysis.
- **Minimum 7 days of historical data** in the `catalyst` index. The `eventstats` baseline needs enough hourly samples per device to produce meaningful `avg` and `stdev` values. Rule of thumb: 7 days = 168 hourly buckets per device; 14 days = 336 (more stable baselines).
- **Search performance consideration**: the `eventstats` runs across ALL rows returned by the search. For a 500-device fleet with a 14-day window: 500 × 336 = 168,000 rows. This is manageable. For a 5,000-device fleet: 1.68M rows — consider narrowing to 7 days or filtering to critical device types only.
- This UC is a **run-tier** analytical view, not a real-time alert. It's designed for twice-daily review by network engineering, not for NOC paging. For real-time alerting, use UC-5.13.3 (threshold-based).
- Document that this technique uses a **same-window rolling baseline** — changing the time picker changes the baseline, which changes the results. This is a feature, not a bug, but it must be understood by operators.

### Step 1 — Configure data collection
No additional configuration. Same `devicehealth` input as UC-5.13.1.

For this UC to produce useful results, confirm sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-14d
| stats earliest(_time) as first_event latest(_time) as last_event dc(deviceName) as devices
| eval days_of_data=round((last_event-first_event)/86400,1)
| table first_event, last_event, days_of_data, devices
```
If `days_of_data < 7`, wait until enough history accumulates before deploying this UC.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| bin _time span=1h
| stats avg(overallHealth) as avg_health by deviceName, _time
| eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName
| where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0
| eval deviation=round((baseline-avg_health)/stdev_health,1)
| sort -deviation
```

Why `where overallHealth > 0` first: filters Assurance recomputation zeros that would corrupt the baseline. Without this filter, a single zero event in a 7-day window can shift the baseline and stdev enough to either mask real anomalies or generate false ones.

Why `bin _time span=1h` + `stats avg() by deviceName, _time`: converts raw per-poll events into hourly averages per device. This smooths within-hour jitter (a single poll reporting 5 points lower than the others in the same hour) while preserving hour-to-hour variation. Without binning, `eventstats` would operate on raw 15-minute polls — noisier and 4× more rows.

Why `eventstats avg + stdev by deviceName`: computes a per-device baseline and standard deviation across the entire search window. Each device gets its own baseline — a core switch averaging 92 has a different baseline than an access switch averaging 75. This is the key advantage over fixed thresholds.

Why 2σ (two standard deviations): the classic statistical threshold. For normally distributed health scores, ~95% of hourly averages fall within ±2σ of the mean. An hour below (baseline - 2σ) is unusual enough to investigate. Tune to 2.5σ or 3σ if you see too many results (more conservative), or 1.5σ for more sensitive detection.

Why `stdev_health > 0` guard: a device with perfectly constant health (stdev = 0) would produce a division-by-zero error in the deviation calculation and trigger a false anomaly on any minor fluctuation.

Schedule as Report: cron `0 7,19 * * *` (7 AM and 7 PM daily), time range `-14d to now`. Output to the Anomaly Detection dashboard panel. Do NOT schedule as a paging alert — the statistical baseline shifts with every run and the results are meant for analytical review, not incident response.

### Step 3 — Validate
(a) Run the search over the last 14 days. You should see 0–10 device-hours flagged as anomalous. If you see > 50, the sigma multiplier is too low or the search window is too short. Try `baseline - 2.5*stdev_health`.

(b) Cross-reference: pick a device flagged as anomalous. Open its timechart in UC-5.13.2 and visually confirm that the flagged hour shows a visible dip below the device's normal operating range. If the dip is indistinguishable from normal variation, increase sigma.

(c) Known incident check: review the last 30 days for any known network incidents. The anomaly detection should flag hours that correlate with those incidents. If it misses them, the sigma is too high (too conservative).

(d) Baseline stability: run the search twice with different time ranges (7 days and 14 days). The same devices should appear in both results. If the results change dramatically, the baseline is unstable — prefer the longer window.

(e) Performance check: note the search runtime. If > 120 seconds, consider filtering to critical device types only (`| where deviceType IN ("Cisco Catalyst 9500 Switch", "Cisco Catalyst 9800 Wireless Controller")`) or narrowing the window.

### Step 4 — Operationalize
Dashboard placement (dedicated "Anomaly Detection" dashboard or as a row on the Advanced Analytics dashboard):
- Table of anomalous device-hours with deviation score, baseline, and current health.
- For the top-3 devices in the table, show an inline timechart of their `avg_health` with a shaded band for `baseline ± 2σ`. Use a post-process search and Dashboard Studio's overlay capabilities.
- Single value: "Devices with anomalous health" — count of unique devices in the results.

Interpretation guide:
- **High deviation (> 4σ)**: severe degradation relative to the device's own history. Investigate immediately — likely a hardware issue, firmware bug, or configuration error.
- **Moderate deviation (2–4σ)**: notable but not catastrophic. Check whether it correlates with a known change or seasonal pattern.
- **Same device appearing repeatedly across multiple hours**: persistent degradation — the device's baseline is shifting downward. Flag for capacity review or firmware investigation.

Runbook (owner: Network Engineering, twice-daily review):
1. Open the anomaly table. Note which devices have the highest deviation scores.
2. For each anomalous device: check the subscore breakdown (`cpuScore`, `memoryScore`, `interDeviceLinkScore`) to identify the component causing the drop.
3. Correlate with UC-5.13.21 (Issues): did Catalyst Center's AI detect an issue for the same device in the same timeframe?
4. Correlate with UC-5.13.46 (Audit): was there a configuration change on or near the device in the same timeframe?
5. If the device has been anomalous for 3+ consecutive days: open a problem ticket for root-cause investigation.

### Step 5 — Troubleshooting

- **Hundreds of rows returned** — baseline window too short or sigma too low. Lengthen the search to 14+ days or increase to 2.5σ or 3σ. Also add `| where stdev_health > 3` to exclude devices with near-zero natural variance.

- **No rows ever returned** — all devices are very stable (good!) or sigma is too high. Try 1.5σ and check whether any rows appear. Also verify the search window has enough history (at least 7 days).

- **Same devices flagged on every run** — these devices have permanently shifted to a lower health level. Their baseline will eventually adjust to the new level, but in the meantime they'll keep appearing. Add them to a `catalyst_anomaly_acknowledged` lookup and filter them out, or create a separate watchlist.

- **Search takes > 5 minutes** — too many rows for `eventstats`. Solutions: (a) reduce the window from 14d to 7d; (b) filter to critical device types only; (c) use summary indexing to pre-compute hourly averages and run `eventstats` on the summary; (d) consider MLTK for more efficient anomaly detection.

- **Baseline shift around holidays** — a device with low weekday traffic and even lower weekend traffic has a mixed baseline that may flag Monday mornings as anomalous. Use `| eventstats avg(avg_health) as baseline by deviceName, date_wday` for day-of-week-aware baselines.

- **Device disappeared from the fleet mid-window** — if a device was decommissioned or renamed, `eventstats` may compute a skewed baseline from the partial history. Add `| eventstats count as sample_count by deviceName | where sample_count >= 100` to exclude devices with insufficient data.

- **False anomalies from Assurance recomputation** — if the `| where overallHealth > 0` filter was accidentally removed, zeros during recomputation will corrupt baselines and generate false results. Re-add the filter.

- **Deviation values are extremely high (> 10σ)** — the device experienced a catastrophic drop (e.g., from 90 to 0). In most cases this is a real event, but verify it wasn't a data error (single corrupt event). Check the raw events for that device-hour.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| bin _time span=1h
| stats avg(overallHealth) as avg_health by deviceName, _time
| eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName
| where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0
| eval deviation=round((baseline-avg_health)/stdev_health,1)
| sort -deviation
```

## Visualization

(1) Table: deviceName, avg_health (current hour), baseline, stdev_health, deviation — sorted by deviation descending. (2) Line chart: for the top-5 devices in the table, show `avg_health` timechart with a shaded band for `baseline ± 2σ`. (3) Single value: count of devices currently below their 2σ band. (4) Scatter plot: `baseline` (x) vs `avg_health` (y) per device, with the diagonal line representing "no change" — devices below the diagonal are degrading.

## Known False Positives

**Planned maintenance causing a temporary deviation.** During firmware upgrades or controlled failovers, a device's health score drops below its baseline, triggering anomaly detection. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` or ITSM change records. Suppress by excluding known maintenance windows from the baseline computation: filter `| where NOT (maintenance_flag=1)` using a `catalyst_maintenance_windows` lookup before `eventstats`.

**Seasonal patterns creating periodic deviations.** A device in a school that runs hot during term and cool during holidays will have different baselines depending on the search window. Distinguish by checking whether the same pattern occurs at the same time in previous weeks. Suppress by using time-aware baselines: `| eventstats avg(avg_health) as baseline by deviceName, date_wday` or using MLTK for seasonal decomposition.

**Baseline instability from short search windows.** A 3-day search window produces unstable baselines — a single bad hour can shift the mean and stdev significantly. Distinguish by checking `stdev_health` — values < 2 indicate a very stable device where even small drops look anomalous. Suppress by requiring `stdev_health > 3` to filter out devices with near-zero natural variance.

**New device with insufficient history.** A device onboarded 2 days ago has only 48 data points — too few for reliable statistical baselines. Distinguish by checking `| stats count by deviceName` — devices with fewer than 100 data points should be excluded. Suppress by adding `| eventstats count as sample_count by deviceName | where sample_count >= 100` before the anomaly filter.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk eventstats command — statistical overlays](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eventstats)
