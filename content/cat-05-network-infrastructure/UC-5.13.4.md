<!-- AUTO-GENERATED from UC-5.13.4.json — DO NOT EDIT -->

---
id: "5.13.4"
title: "Device Health by Category (Access/Distribution/Core/Router/Wireless)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.4 · Device Health by Category (Access/Distribution/Core/Router/Wireless)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We break down the health of your network devices by their role — access switches in the closets, big routers in the data centre, wireless controllers. This tells your team whether the problem is in the Wi-Fi, the wiring, or the backbone, so they send the right people to the right place.*

---

## Description

Breaks down device health by network role category — access switches, distribution switches, core routers, wireless controllers, APs — revealing which infrastructure tier has the highest concentration of unhealthy devices and therefore the greatest operational risk.

## Value

A fleet-wide health score of 82 tells you something is wrong; this UC tells you *where*. If 90% of unhealthy devices are access switches in one building, you send a team with a cable tester to that IDF — not your WLC engineer to the data centre. Breaking health down by device role maps directly to your team structure (campus LAN vs wireless vs WAN) and budget categories (access refresh vs controller upgrade), making both triage and investment decisions faster.

## Implementation

Same data feed as UC-5.13.1. Validate that `deviceType` is populated and contains the expected categories for your fleet. If Catalyst Center uses generic strings like `Switches and Hubs`, consider enriching with a `device_role_lookup` that maps `platformId` → role (access/distribution/core/WLC/router).

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational — this UC uses the same `devicehealth` data feed.
- Understand your fleet composition: run `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as devices by deviceType | sort -devices` to see what `deviceType` values Catalyst Center assigns. Common values: `Cisco Catalyst 9300 Switch`, `Cisco Catalyst 9500 Switch`, `Cisco ISR 4461 Router`, `Cisco Catalyst 9800 Wireless Controller`, `Cisco Aironet Access Point`.
- If Catalyst Center lumps all switches under `Switches and Hubs`, you need a mapping lookup. Create `lookups/device_role_lookup.csv` with columns `platformId, device_role` and populate from your inventory. Example: `C9300-48P` → `access`, `C9500-24Y4C` → `distribution`, `ASR1006-X` → `core`.
- This UC is a walk-tier refinement of UC-5.13.1. It provides dimensional breakdown for operations, not real-time alerting (use UC-5.13.3 for alerts).

### Step 1 — Configure data collection
No additional configuration. Same `devicehealth` input as UC-5.13.1. Confirm `deviceType` is populated:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
| stats dc(deviceName) as devices by deviceType
| sort -devices
```
If `deviceType` is null for some devices, check whether those devices are fully discovered in Catalyst Center > Provision > Inventory. Partially discovered devices may have incomplete metadata.

If `deviceType` granularity is insufficient (e.g., all switches grouped as `Switches and Hubs`), enhance with a lookup:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| lookup device_role_lookup platformId OUTPUT device_role
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by device_role
| eval unhealthy_pct=round(unhealthy_count*100/device_count,1)
| sort -unhealthy_pct
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType
| eval unhealthy_pct=round(unhealthy_count*100/device_count,1)
| sort -unhealthy_pct
```

Why `avg(overallHealth)` across devices, not `latest()`: within a single poll cycle, there's one event per device, so `avg()` and `latest()` are equivalent for a single device. But across the search time window (e.g., last 1 hour = 4 polls), `avg()` gives you the central tendency per device type, smoothing out single-poll artifacts. For the current snapshot, narrow to `earliest=-20m` to cover one poll cycle.

Why `count(eval(overallHealth<50))` as the metric: `avg_health` can be misleading — a category with 99 healthy devices and 1 critically sick device still averages 89. `unhealthy_count` and `unhealthy_pct` surface the tail directly. Sort by `unhealthy_pct` to find the categories with the highest concentration of problems, regardless of fleet size.

Why `by deviceType` not `by deviceFamily`: `deviceType` gives you the specific platform (e.g., `Cisco Catalyst 9300 Switch`), while `deviceFamily` is broader (e.g., `Switches and Hubs`). Use `deviceType` for engineering-level triage, `deviceFamily` for management summaries. Your SPL choice depends on your audience.

This is a report, not an alert. Schedule for weekly ops review: cron `0 7 * * 1` (Monday 7 AM), output to PDF for the operations meeting.

### Step 3 — Validate
(a) Run the search and compare total `device_count` across all rows with `| stats dc(deviceName)` from UC-5.13.1. They should match. If this search shows fewer devices, some have null `deviceType` and are being dropped by the `by deviceType` clause.

(b) Pick the device type with the highest `unhealthy_pct`. Drill into that category: `index=catalyst sourcetype="cisco:dnac:devicehealth" deviceType="<that-type>" | where overallHealth < 50 | table deviceName overallHealth siteId`. Verify these devices are genuinely unhealthy in **Catalyst Center > Assurance > Device 360**.

(c) Check for suspiciously small categories: `| where device_count < 3`. These may produce 100% unhealthy from a single device — flag them as informational, not actionable at the category level.

(d) Cross-reference with `| stats count by deviceType` in the raw data to ensure event counts make sense. If one type has 10× the expected events, check for duplicate ingestion.

(e) Vendor UI parity: compare the category breakdown with **Catalyst Center > Assurance > Health > Device** using the device-type filter. The percentage of unhealthy devices per type should be comparable.

### Step 4 — Operationalize
Dashboard placement (on the "Catalyst Center — Device Health Overview" dashboard):
- **Row 3** — Two panels side by side:
  - Left: horizontal bar chart of `unhealthy_pct` by `deviceType`, sorted worst-first. Red bars (> 10%), yellow (5–10%), green (< 5%). Title: "Unhealthy Concentration by Device Role".
  - Right: table of `deviceType | device_count | avg_health | unhealthy_count | unhealthy_pct`. Drilldown: click a row → filter UC-5.13.1 table to that `deviceType`.
- Time-picker: default "Last 1 hour" for current state, "Last 7 days" for weekly review.

Runbook (owner: Network Operations lead, used in weekly ops review):
1. Open the Device Health by Category panel. Identify the device type with the highest `unhealthy_pct`.
2. If **wireless controllers** are the worst category: this usually means AP management issues, not WLC hardware. Check UC-5.13.60 (AP Health) and UC-5.13.42 (RSSI/SNR) for the wireless dimension.
3. If **access switches** are the worst: check whether the unhealthy devices are concentrated in one `siteId` (building-level issue like a failing UPS or HVAC) or distributed across sites (fleet-level issue like a firmware bug). Use UC-5.13.5 (by Site) to disambiguate.
4. If **core/distribution** is the worst: this is the highest-impact finding. Core device health below 50 affects every user downstream. Escalate immediately and correlate with UC-5.13.16 (Network Health) to confirm the aggregate impact.
5. Track this breakdown month-over-month. Categories that consistently appear at the top are candidates for targeted remediation projects (firmware campaign, hardware refresh, design change).

Capacity planning (monthly):
- Overlay fleet size growth with health trends: `| timechart span=1d dc(deviceName) as device_count avg(overallHealth) as avg_health by deviceType`. Growing fleet + declining health = underinvestment in that device category.

### Step 5 — Troubleshooting

- **Only one category appears** — all devices share the same `deviceType` string (common when Catalyst Center uses the generic `Switches and Hubs`). Create a `device_role_lookup` mapping `platformId` → role and use that instead. See Step 1.

- **A category shows 0% unhealthy but users report issues** — `overallHealth` is a composite score that may not weight client-facing metrics heavily enough. Cross-reference with UC-5.13.9 (Client Health) to see the user-experience dimension.

- **`deviceType` values changed after Catalyst Center upgrade** — run `| stats values(deviceType)` before and after the upgrade to identify renames. Update the `device_role_lookup` and any dashboard labels.

- **Unhealthy count is inflated** — the search window covers multiple polls and `stats count(eval(...))` counts events, not unique devices. Narrow to `earliest=-20m` for a single-poll snapshot, or change to `| stats latest(overallHealth) as health by deviceName, deviceType | where health < 50 | stats count by deviceType` for unique-device counts.

- **A new device type appears with very low health** — newly discovered devices often have incomplete Assurance baselines. Check `| stats earliest(_time) as first_seen by deviceType` and exclude types with `first_seen` within the last 48 hours.

- **Categories overlap (same device appears in two types)** — this shouldn't happen with `deviceType` (each event has one value), but can happen if your lookup maps one `platformId` to multiple roles. Ensure the lookup is one-to-one.

- **AP category dominates the chart** — APs typically outnumber switches 3:1 or more. Their collective health can dominate the category view. Consider separating APs into their own dashboard (UC-5.13.60) and filtering them out of this view: `| where deviceType != "Cisco Aironet Access Point"`.

- **Bar chart looks fine but table shows concerning `avg_health`** — a category can have 0% unhealthy (no device below 50) but `avg_health` of 55 (many devices in the 50–60 range, trending toward trouble). Add `avg_health` to the bar chart as a secondary axis for a fuller picture.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType
| eval unhealthy_pct=round(unhealthy_count*100/device_count,1)
| sort -unhealthy_pct
```

## Visualization

(1) Horizontal bar chart: `unhealthy_pct` by `deviceType`, sorted worst-first, red bars for > 10% unhealthy. (2) Table: deviceType | device_count | avg_health | unhealthy_count | unhealthy_pct — drilldown to UC-5.13.1 filtered by that device type. (3) Trellis of single-value tiles: one per `deviceType` showing `avg_health` with colour thresholds (green ≥ 80, yellow 60–80, red < 60). (4) Pie chart: `device_count` by `deviceType` for fleet composition context.

## Known False Positives

**Catalyst Center grouping multiple device models under a single `deviceType` string.** Catalyst Center may classify both Catalyst 9300 access switches and Catalyst 9500 distribution switches under `Switches and Hubs`, masking the access/distribution distinction. Distinguish by checking `platformId` for the actual hardware model. Suppress by creating a `device_role_lookup` that maps `platformId` → operational role (access, distribution, core) and using `| lookup device_role_lookup platformId OUTPUT device_role | stats ... by device_role` instead of `by deviceType`.

**Small device population in a category producing misleading percentages.** If you have only 2 WLCs and one is briefly unhealthy, `unhealthy_pct = 50%` looks alarming but represents a single device. Distinguish by checking `device_count` — categories with < 5 devices should not drive Pareto-style triage. Suppress by adding `| where device_count >= 5` for the bar chart, and showing small populations in a separate informational table.

**AP health scores inflating the category count without indicating infrastructure issues.** APs report individual health scores that can be low due to RF interference, not equipment failure. A building renovation with temporary RF blockage can make 30 APs report poor health. Distinguish by checking whether the unhealthy APs are geographically clustered (same `siteId`). Do not suppress — but route AP health alerts to the wireless team, not the switching team.

**Device type strings changing after Catalyst Center or IOS-XE upgrades.** A `deviceType` rename (e.g., `Unified AP` → `Cisco Aironet Access Point`) creates a new series in the chart and makes the old series disappear. Distinguish by running `| stats dc(deviceType) values(deviceType)` before and after the upgrade. Suppress by maintaining a `device_type_alias` lookup that normalises variant strings to canonical categories.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Device Types and Platform IDs](https://developer.cisco.com/docs/catalyst-center/#!get-device-list)
