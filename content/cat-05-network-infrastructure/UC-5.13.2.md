<!-- AUTO-GENERATED from UC-5.13.2.json — DO NOT EDIT -->

---
id: "5.13.2"
title: "Device Health Score Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.2 · Device Health Score Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track how healthy your network devices are over time, day by day and week by week. When things slowly get worse — too gradually for anyone to notice in the moment — the trend line catches it before it becomes a real problem. It also proves whether upgrades and fixes actually helped.*

---

## Description

Tracks the average device health score over time by device type (switches, routers, WLCs, APs), transforming point-in-time snapshots from UC-5.13.1 into trend lines that reveal gradual degradation invisible in a single poll — the slow memory leak, the aging power supply, the site that's been running warm for weeks.

## Value

UC-5.13.1 tells you what's wrong right now. This UC tells you what's *getting* worse. A core switch fleet averaging 88 last month and 74 this month is the difference between a planned IOS-XE upgrade during the next maintenance window and an unplanned outage at 2 AM. The trend line also proves to leadership that a remediation effort (firmware push, hardware refresh, SDA migration) actually improved health scores — or didn't, which is equally valuable because it redirects investment before the next budget cycle.

## Implementation

Same data feed as UC-5.13.1 — no additional input configuration required. Ensure the `catalyst` index has sufficient retention for trending (recommend 90+ days, matching `frozenTimePeriodInSecs = 7776000`). Place the timechart alongside UC-5.13.1's table on the Device Health dashboard.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational first — this UC uses the same `devicehealth` data feed. No additional input configuration is required.
- `catalyst` index retention: set `frozenTimePeriodInSecs` to at least **7,776,000** (90 days) for meaningful trend baselines. Catalyst Center's own Assurance window is only 7 days — Splunk is the sole long-term record. For capacity-review dashboards, 365 days is ideal.
- Splunk license: same as UC-5.13.1 — ~75 KB/device/day. This UC doesn't generate additional events; it queries the same data differently.
- Baseline knowledge: establish what "normal" looks like for each `deviceType` during the first 2 weeks. Typical ranges: core switches 85–95, distribution 80–90, access 70–85, WLCs 80–90. Seasonal patterns (higher load during business hours, lower on weekends) are normal.

### Step 1 — Configure data collection
No additional configuration. This UC consumes the same `cisco:dnac:devicehealth` events as UC-5.13.1. Confirm the input is producing events:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | stats count by deviceType
```
If you see rows for each expected device family, you're ready. If not, see UC-5.13.1 Step 1 troubleshooting.

For trending to work, ensure the `catalyst` index has sufficient retention. Check current settings:
```spl
| rest /servicesNS/-/-/data/indexes/catalyst | table title frozenTimePeriodInSecs maxTotalDataSizeMB
```
If `frozenTimePeriodInSecs` is less than 7,776,000 (90 days), increase it in `indexes.conf` or via the UI.

Expected storage for trending: `device_count × 75 KB/day × retention_days`. A 500-device campus at 90 days retention ≈ 3.4 GB for the `devicehealth` sourcetype alone.

### Step 2 — Create the search and dashboard panel
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| timechart span=1h avg(overallHealth) as avg_health by deviceType
| eval avg_health=round(avg_health,1)
```

Why `where overallHealth > 0` before `timechart`: Assurance recomputation briefly sets scores to 0 (see Known False Positives). Without the filter, these zeros pull hourly averages down by 5–15 points, creating false dips in the trend line that don't represent real degradation. Filtering zeros preserves the integrity of the trend.

Why `avg()` not `latest()` or `min()`: for trending, you want the central tendency per hour, not the worst moment. `avg()` across devices of the same type shows fleet-level health. If you need to spot individual device degradation, use UC-5.13.7 (Anomaly Detection) or add a companion panel with `perc10(overallHealth)` to show the bottom 10% of the fleet.

Why `span=1h`: at the default 900s poll interval, each hour contains ~4 polls per device. `span=1h` smooths single-poll jitter (a device temporarily reporting 0 during a brief API glitch) while preserving meaningful trends. For incident investigation, narrow to `span=15m`. For executive 30-day views, widen to `span=4h` or `span=1d` for cleaner lines.

Why `by deviceType`: this groups devices by their functional role (switches, routers, WLCs, APs). A degradation in wireless controllers that doesn't affect switches is a very different investigation than a fleet-wide drop. If your campus is multi-site, consider replacing `by deviceType` with `by siteId` or adding a second panel split by site.

This is a *dashboard panel*, not an alert. Trending is for visual analysis and capacity review, not real-time paging. For alerting on health drops, use UC-5.13.3 (Unhealthy Device Detection).

### Step 3 — Validate
(a) Run the search over the last 24 hours. You should see smooth hourly lines for each `deviceType`, with values generally between 70 and 100. If a line is flat at 0, check whether `overallHealth > 0` filter is in place and whether that device type has Assurance support.

(b) Spot-check: pick a specific hour in the timechart (e.g., yesterday at 14:00). Run `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=<that-hour> latest=<next-hour> deviceType="Switches and Hubs" | stats avg(overallHealth) as check`. The number should match the chart's data point within 0.5 points.

(c) Confirm series completeness: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceType) as types | table types`. Compare with the number of series in your timechart. If fewer series appear in the chart, some device types may have been renamed or removed.

(d) Check for gaps: `index=catalyst sourcetype="cisco:dnac:devicehealth" | timechart span=1h count | where count=0`. Any zero-count hours indicate polling interruptions — investigate with `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR`.

(e) Vendor UI parity: compare the general trend shape with **Catalyst Center > Assurance > Health > Device** over the same 24-hour window. Exact values won't match (Catalyst Center may use different aggregation) but the trend direction and relative device-type ordering should be consistent.

### Step 4 — Operationalize
Dashboard placement (on the "Catalyst Center — Device Health Overview" dashboard created for UC-5.13.1):
- **Row 4** — Full-width timechart panel. Default time range: Last 7 days. Title: "Device Health Trending by Type".
- Y-axis: fixed 0–100 with an SLO reference line at 80 (or your agreed target). Use Dashboard Studio's `| eval slo=80` + dual-axis overlay or Simple XML's `<option name="charting.axisY.minimumNumber">0</option>`.
- Colour each `deviceType` series consistently across all dashboards (e.g., switches = blue, routers = green, WLCs = purple).
- Time-picker presets: "Last 24 hours" (incident review), "Last 7 days" (weekly ops), "Last 30 days" (monthly capacity), "Last 90 days" (quarterly review).

Interpretation guide (add to the dashboard's "How to read this" panel or info tooltip):
- **Gradual downward slope** (1–2 points/week): indicates aging fleet, growing utilisation, or accumulated configuration debt. Action: schedule capacity review per UC-5.13.1 Step 4.
- **Sudden step-down** that doesn't recover: likely a persistent device failure or a Catalyst Center scoring algorithm change after an upgrade. Drill to UC-5.13.1 for the affected devices.
- **V-shaped dip** that recovers within 2–4 hours: maintenance window or Assurance recomputation. Annotate on the chart.
- **One series diverging** while others are stable: problem is specific to that device family. Common: WLC firmware bug, AP radio issue, access switch power supply.

Capacity review (cadence: monthly, owner: Network Architecture):
- Query: `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-30d | timechart span=1d avg(overallHealth) as daily_avg by deviceType`. Export as CSV for the capacity review deck.
- Compare month-over-month: is the fleet getting healthier or degrading? Overlay with the number of devices added/removed (from UC-5.13.51) to normalise for fleet growth.

### Step 5 — Troubleshooting

- **Flat line at 0 for a device type** — either `overallHealth > 0` filter is missing and recomputation zeros are dominating, or that device type genuinely isn't supported by Assurance (e.g., some Meraki devices appearing in Catalyst Center inventory). Add the filter and check Catalyst Center > Assurance for that device type.

- **Sawtooth pattern repeating every poll interval** — possible double-ingest of the same poll. Check `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count by _time, deviceName | where count > 1` for duplicates. If confirmed, add `| dedup _time deviceName` before `timechart`.

- **Series disappears after a Catalyst Center upgrade** — `deviceType` strings may have been renamed (e.g., "Switches" → "Switches and Hubs"). Run `| stats values(deviceType) by earliest(_time)` to identify the rename boundary. Update dashboard labels accordingly.

- **Y-axis shows null for some hours** — `overallHealth` is not being extracted. Check `index=catalyst sourcetype="cisco:dnac:devicehealth" | fieldsummary | search field=overallHealth`. If `count=0`, the field extraction is broken — check `props.conf` for the sourcetype.

- **All lines drop simultaneously and recover** — this is an Assurance recomputation cycle or a Catalyst Center API outage. The `| where overallHealth > 0` filter in Step 2 should prevent these from appearing in the trend. If they still show, check whether the TA is returning `overallHealth=0` (filtered) vs null (not filtered by this guard).

- **Very flat lines with no variation** — a well-managed, stable network genuinely has flat health scores. This is not an error — it means infrastructure health is good. The interesting signal is in UC-5.13.9 (client health) and UC-5.13.21 (issues), where user-facing problems surface first.

- **Trend shows improvement after firmware push but then regresses** — the Catalyst Center Assurance engine may need 24–48 hours to rebuild baselines after a major IOS-XE upgrade. Wait 2 days before evaluating the trend. If it still regresses, the firmware introduced a new issue — correlate with UC-5.13.21 for new issue types.

- **Storage growing faster than expected** — the `devicehealth` sourcetype is one of the heavier Catalyst Center feeds (~75 KB/device/day). At 90-day retention with 2,000 devices, expect ~13.5 GB. If this exceeds your budget, consider reducing retention to 30 days for `devicehealth` while keeping 365 days for the lighter `networkhealth` sourcetype.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| timechart span=1h avg(overallHealth) as avg_health by deviceType
| eval avg_health=round(avg_health,1)
```

## Visualization

(1) Multi-series line chart: `avg_health` by `deviceType` over the selected time range, with y-axis 0–100 and an SLO reference line at 80 or 85. (2) Same chart as an area stack to show fleet composition changes (new device types appearing over time). (3) Side panel: `| stats min(avg_health) as worst_hour max(avg_health) as best_hour by deviceType` for min/max context. (4) Optional overlay: maintenance window markers from `catalyst_maintenance_windows` lookup annotated on the time axis.

## Known False Positives

**Mass firmware upgrade cycle causing coordinated health dip.** When many devices of the same `deviceType` undergo IOS-XE upgrades simultaneously, their `overallHealth` drops during reload, pulling the average down for that device type in the timechart. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for template deployment or upgrade tasks, or check ITSM for an approved change ticket. Suppress by overlaying maintenance windows on the timechart using `| eval is_maint=if(match(_time, "..."), 1, 0)` or annotating the chart with event markers.

**Assurance recomputation artifacts in timechart data.** Brief health-score drops to 0 during Assurance recomputation can create artificial dips in the timechart, especially at 1-hour span granularity. Distinguish by checking whether the dip is exactly at the hour boundary and recovers within the next data point. Suppress by using `| where overallHealth>0` before the `timechart` command to filter recomputation artifacts.

**New device type appearing in the fleet.** When a new device family (e.g., Catalyst 9400) is first onboarded, it starts with limited history and may pull the average for its type down initially. Distinguish by checking `| stats earliest(_time) as first_seen by deviceType` and noting device types with very recent first-seen dates. Suppress by requiring at least 24 hours of data before including a new device type in trending analysis.

**Daylight saving time or timezone shift causing apparent data gaps.** If the Splunk search head's timezone differs from the Catalyst Center's timezone, timechart boundaries may show gaps or compressed data during DST transitions. Distinguish by checking the raw event timestamps around the transition. No suppression needed — ensure consistent timezone configuration across Splunk and Catalyst Center.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk timechart command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart)
