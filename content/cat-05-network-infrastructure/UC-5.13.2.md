<!-- AUTO-GENERATED from UC-5.13.2.json — DO NOT EDIT -->

---
id: "5.13.2"
title: "Device Health Score Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.2 · Device Health Score Trending

## Description

Tracks device health scores over time to identify gradual degradation trends that may indicate aging hardware, software issues, or capacity constraints.

## Value

Transforms point-in-time health snapshots into trend lines that reveal slow-burning problems and support capacity planning decisions.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538), enable the device health input to `index=catalyst` with sourcetype `cisco:dnac:devicehealth`, and retain enough history for hourly `timechart` baselines. Poll interval defaults to 15 minutes; widen the dashboard time range for trend visibility.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538); device health to `index=catalyst`, sourcetype `cisco:dnac:devicehealth`.
• Catalyst Center **2.3.5+** for a stable `overallHealth` time series in historical charts.
• Retain **30–90+ days** in the index for meaningful baselines; seven days of hot data only is usually too short for trend reviews.
• API user with **`NETWORK-ADMIN-ROLE`** or **`SUPER-ADMIN-ROLE`** (and Assurance visibility).
• See `docs/implementation-guide.md` for TA deployment and credential storage.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/device-health`.
• **TA input name:** **devicehealth** modular input; sourcetype `cisco:dnac:devicehealth`, index `catalyst` (adjust `index=` in SPL if you use a different index name).
• **Default poll:** **900 seconds (15 minutes)**; for `timechart span=1h`, expect multiple samples per hour per device to land inside each bucket in large environments.
• **Volume:** approximately **one sample per managed device per poll**; chart series count follows **unique `deviceType`** values, not raw event volume.
• **Key fields:** `overallHealth` (numeric trend), `deviceType` (split-by field), `_time` for bucketing.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | timechart span=1h avg(overallHealth) as avg_health by deviceType | eval avg_health=round(avg_health,1)
```

Understanding this SPL (span, aggregation, and SLO alignment)
• **`span=1h`** smooths single-poll jitter inside the hour; use **`span=15m`** if you need faster visibility of dips (noisier lines, more chart points).
• **`avg(overallHealth)`** averages **across devices of the same type** in that hour—if one chassis drags the line, add a **parallel** panel with **`perc10(overallHealth)`** or filter `where deviceType="Switch"` for a story-based view.
• **Round to one decimal** is for clean labels; use two decimals if your SLO is written to tenths of a point.
• Map the y-axis to an **internal SLO** (for example, fleet average **>80**) in the dashboard layer; the SPL only supplies the series.

**Pipeline walkthrough**
• `timechart` buckets `_time` into one-hour slices and averages `overallHealth` for each `deviceType` series.
• `eval round()` keeps tick labels readable in Classic XML and Dashboard Studio.
• Pair with **maintenance annotations** when you know a code upgrade or RMA wave should move the lines.

Step 3 — Validate
• Run `| timechart span=1h count` (no `by`) to confirm buckets are populated end-to-end—gaps mean polling or indexing stopped.
• Spot-check one `deviceType` against **Assurance** drill-down for a sample of devices (the line is an aggregate, not a one-to-one GUI match).
• If a series vanishes, run `| stats values(deviceType) count` over 7d to see if a string rename occurred after an IOS-XE upgrade.
• Add `| where isnum(overallHealth)` before the chart if nulls slip through on some platforms.

Step 4 — Operationalize
• **Placement:** **wide center panel** on an **Assurance trends** row; default **Last 7 days** with quick tokens for **24h** and **30d**.
• **Annotations:** vertical markers for change windows; correlate dips that align with planned work vs. unexpected regressions.
• **Not a paging search** by itself—use **UC-5.13.3** for threshold-based alerting; this panel is for **slow drift** and capacity stories.
• **Clone** the panel per **region** using a **site or building** token if the TA enriches events with those fields.

Step 5 — Troubleshooting
• **Flat or missing series:** validate the **devicehealth** input is still **enabled** and that **`deviceType`** values did not collapse to `unknown` after a TA upgrade.
• **Sawtooth pattern every poll interval:** possible **double-ingest** of the same poll—consider `| dedup _time deviceName` before `timechart` if confirmed in `all` search mode.
• **Y-axis stuck at null:** open **Settings > Fields** for the sourcetype and confirm **EXTRACT-** / **KV** for `overallHealth`.
• **Low dynamic range:** a very stable fabric produces flat lines—combine with **client** and **network** health UCs for user-impacting signal.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | timechart span=1h avg(overallHealth) as avg_health by deviceType | eval avg_health=round(avg_health,1)
```

## Visualization

Line or area timechart (avg_health by deviceType), optional overlay for maintenance windows, stat panels for min/max per type.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
