<!-- AUTO-GENERATED from UC-5.13.10.json — DO NOT EDIT -->

---
id: "5.13.10"
title: "Client Health Trending by Time"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.10 · Client Health Trending by Time

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track how your users' network experience changes throughout the day, week, and month — split between wired and wireless. When Wi-Fi gets worse every Tuesday afternoon, this chart catches the pattern so you can fix the cause, not just react each time. It also proves whether upgrades and changes actually made things better.*

---

## Description

Tracks the percentage of healthy clients over time by category (ALL, WIRED, WIRELESS), revealing patterns invisible in a single snapshot — peak-hour degradation, weekend improvements, the exact moment a firmware push helped or hurt Wi-Fi, and whether last month's SSID change actually improved the user experience or just moved the problem.

## Value

UC-5.13.9 tells you the current client health state. This UC tells you the *story* — when did it get worse, how fast did it recover, and is the long-term trend going up or down? A wireless healthy percentage that drops from 85% to 60% every Tuesday at 10 AM is a recurring problem (conference room overload, RRM conflict, DHCP exhaustion) that a point-in-time snapshot will never catch. The trend also gives executives the before/after proof that a Wi-Fi investment actually worked, expressed in a metric they can understand without network engineering background.

## Implementation

Same data feed as UC-5.13.9 — no additional input. Ensure `catalyst` index retention covers the trending period (recommend 90+ days). Place the timechart below UC-5.13.9's single-value tiles on the Client Experience dashboard. Use `span=1h` for daily views, `span=4h` for weekly/monthly views.

## Detailed Implementation

### Prerequisites
- UC-5.13.9 must be operational — same `clienthealth` data feed. No additional input configuration required.
- `catalyst` index retention: set to at least **90 days** for meaningful trending. Client health trend data is extremely lightweight (~350 KB/day) so the storage cost for 365-day retention is trivial.
- Confirm the nested `healthyClientsPercentage` field is present in your events. Some Catalyst Center versions or TA builds may not include this field — validate with `| head 1 | spath` (see UC-5.13.9 Step 1 for the full nested structure).
- Agree with stakeholders on the trending granularity: `span=1h` for daily/weekly views (4 data points per hour), `span=4h` for monthly views (cleaner lines), `span=1d` for quarterly/annual views (one point per day).

### Step 1 — Configure data collection
No additional configuration. Same `clienthealth` input as UC-5.13.9. Confirm data is flowing with sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" earliest=-30d
| stats earliest(_time) as first_event latest(_time) as last_event
| eval days_of_data=round((last_event-first_event)/86400,1)
| table first_event, last_event, days_of_data
```
If `days_of_data < 7`, wait until enough history accumulates for meaningful trends.

### Step 2 — Create the search and dashboard panel
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=cat_name path=scoreCategory.scoreCategory
| spath input=categories output=healthy_pct path=healthyClientsPercentage
| where isnum(healthy_pct)
| timechart span=1h avg(healthy_pct) as avg_healthy_pct by cat_name
```

Why `spath | mvexpand | spath` instead of direct field references: client health uses double-nested JSON (see UC-5.13.9 Step 2). Direct references like `scoreDetail{}.healthyClientsPercentage` break between TA versions. The three-stage extraction is reliable.

Why `where isnum(healthy_pct)`: some poll cycles may return null or non-numeric values for `healthyClientsPercentage` (during Assurance recomputation or when no clients are connected). Without this filter, `avg()` would either ignore nulls (correct) or fail on strings (error). The explicit filter also documents the data quality expectation.

Why `avg()` not `latest()` for trending: within each 1-hour span, there are ~4 polls (at 900s interval). `avg()` smooths these into a representative hourly value. `latest()` would pick only the last poll in each hour, which may happen to be during an Assurance recomputation dip.

Why `by cat_name`: produces separate series for ALL, WIRED, and WIRELESS. The divergence between these lines IS the signal — when WIRELESS drops but WIRED stays flat, you know the problem is in the RF/wireless layer, not the infrastructure backbone.

This is a dashboard panel, not an alert. Trending is for visual analysis. For alerting on client health drops, use UC-5.13.11.

### Step 3 — Validate
(a) Run the search over the last 7 days. You should see 3 lines (ALL, WIRED, WIRELESS) with values generally between 60% and 100%. ALL should be between the WIRED and WIRELESS lines (it's a weighted average). If ALL is consistently above both, the weighting includes categories you're not seeing — check for additional `cat_name` values.

(b) Compare a specific hour: pick yesterday at 14:00. In Splunk, note the `avg_healthy_pct` for WIRELESS at that hour. In **Catalyst Center > Assurance > Client Health**, filter to WIRELESS and check the healthy percentage for the same hour. They should agree within 2 percentage points.

(c) Check for gaps: `index=catalyst sourcetype="cisco:dnac:clienthealth" | timechart span=1h count | where count=0`. Zero-count hours mean no data was ingested — investigate with `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR`.

(d) Confirm the trend shape makes sense: wireless healthy percentage should typically be lower than wired (Wi-Fi is inherently less reliable). Both should show higher values during off-hours (fewer clients, less congestion) and lower during business peaks.

(e) Vendor UI parity: open **Catalyst Center > Assurance > Health > Client Health** and switch to the trend view. The shape of the curve should match the Splunk timechart, even if exact values differ slightly due to aggregation differences.

### Step 4 — Operationalize
Dashboard placement (on the "Catalyst Center — Client Experience" dashboard, below UC-5.13.9's single-value tiles):
- **Full-width timechart panel**. Default time range: Last 7 days. Title: "Client Health Trending (Healthy %)".
- Y-axis: 0–100% with SLO reference line at 80% (or your agreed target). WIRELESS line in blue, WIRED in green, ALL in grey dashed.
- Time-picker presets: "Last 24 hours" (incident review), "Last 7 days" (weekly ops), "Last 30 days" (monthly review), "Last 90 days" (quarterly executive view).
- Annotations: overlay maintenance windows and significant changes (SSID additions, firmware pushes, RRM changes) from `catalyst_maintenance_windows` lookup or audit log events.

Interpretation guide:
- **Gradual downward slope over weeks**: increasing client load without proportional AP/switch investment. Flag for capacity review.
- **Recurring daily dip at specific hours**: peak-hour congestion, DHCP pool exhaustion, or RRM channel conflicts during high-density periods.
- **Sudden step-down that doesn't recover**: configuration change gone wrong, AP failure, or upstream switch issue. Correlate with UC-5.13.46 (audit log) for the change.
- **WIRELESS diverging from WIRED**: the problem is in the RF/wireless layer — investigate with UC-5.13.42 (RSSI/SNR), UC-5.13.12 (by SSID), UC-5.13.44 (roaming).
- **Both lines dropping together**: shared-infrastructure problem — DHCP, DNS, RADIUS, or upstream routing.

Capacity review (monthly):
- Query: `<base search> | timechart span=1d avg(avg_healthy_pct) by cat_name`. Export 30-day CSV for the capacity review deck. Compare month-over-month slopes.

### Step 5 — Troubleshooting

- **Only one series appears (ALL) without WIRED/WIRELESS split** — the `scoreCategory.scoreCategory` path may differ in your TA version. Run `| head 1 | spath` and check the actual path to the category name. Adjust the `spath ... path=` accordingly.

- **`healthy_pct` is always null** — your Catalyst Center version may not include `healthyClientsPercentage` in the API response. Fall back to the `value` field from `scoreCategory`: replace the `spath ... path=healthyClientsPercentage` with `spath ... path=scoreCategory.value` (this is the overall health score, not the percentage — but it's the best available proxy).

- **Flat line at 100% for WIRED** — if your campus has very few wired clients or all wired clients are healthy, this is expected. The interesting signal is usually in the WIRELESS line.

- **Chart shows data only for the last 7 days** — the `catalyst` index retention is too short. Extend `frozenTimePeriodInSecs` in `indexes.conf`. Existing data that was already frozen cannot be recovered.

- **Trend shows a spike to 100% during off-hours** — with very few clients connected overnight (e.g., 5 wired clients, all healthy), the percentage hits 100%. This is mathematically correct but not operationally meaningful. Add client count as a secondary axis or overlay to provide context.

- **Series labels show raw strings like `scoreCategory.scoreCategory` instead of `ALL/WIRED/WIRELESS`** — the `spath` output field name collides with the JSON path. Use explicit `output=cat_name` in the `spath` command and reference `cat_name` in the `by` clause.

- **Timechart has holes on weekends** — if no polls ran during weekends (unlikely with a 15-min interval, but possible if the input was manually disabled), the chart shows gaps. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst"` for the weekend period.

- **Trend shape doesn't match the Catalyst Center client health trend** — Catalyst Center uses a different aggregation window (5 minutes vs your 1-hour span) and may weight clients differently. Exact parity is not expected; directional agreement (both show the same dips and recoveries) is sufficient.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=cat_name path=scoreCategory.scoreCategory
| spath input=categories output=healthy_pct path=healthyClientsPercentage
| where isnum(healthy_pct)
| timechart span=1h avg(healthy_pct) as avg_healthy_pct by cat_name
```

## Visualization

(1) Multi-series line chart: `avg_healthy_pct` by category (ALL, WIRED, WIRELESS) with y-axis 0–100% and an SLO reference line at 80%. WIRED and WIRELESS as separate coloured lines; ALL as a dashed overlay. (2) Stat panels: min, max, avg of `healthy_pct` per category over the selected range. (3) Change-window annotations: vertical markers for firmware pushes, SSID changes, RRM adjustments from `catalyst_maintenance_windows` or `index=catalyst sourcetype="cisco:dnac:audit:logs"`. (4) Optional week-over-week comparison: this week's WIRELESS line vs last week's, to quantify improvement/regression.

## Known False Positives

**Daylight saving time or timezone shift causing apparent gaps in the timechart.** If the Splunk search head and Catalyst Center use different timezone configurations, the 1-hour `timechart span` may show a gap or compressed data during DST transitions. Distinguish by checking raw event timestamps around the transition boundary. Suppress by ensuring consistent timezone configuration across Splunk and Catalyst Center; no SPL filter needed.

**Mass firmware upgrade window causing coordinated client disconnection.** When many access switches or APs are upgraded simultaneously, their clients disconnect and reconnect, creating a visible dip in the client health trend. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for upgrade activity. Suppress by annotating the timechart with maintenance windows using `| eval is_maint=if(...)` or chart annotations.

**New SSID deployment or policy change shifting client distribution.** A new SSID rolled out across the campus changes the client mix between wired and wireless categories, causing the trend to shift without an actual health problem. Distinguish by checking whether the client count per category changed significantly at the same time the trend shifted. Suppress by normalizing the chart as percentage-based rather than absolute, or by using a 7-day rolling baseline.

**RRM channel reoptimization affecting wireless client health trend.** Periodic RRM adjustments cause brief wireless client health dips that appear as recurring troughs in the timechart. Distinguish by checking whether the dips occur at regular intervals (e.g., every 6 hours) matching the RRM optimization schedule. Suppress by smoothing the timechart with `| trendline sma5(healthy_pct)` to filter out periodic transients.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-client-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk timechart command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart)
