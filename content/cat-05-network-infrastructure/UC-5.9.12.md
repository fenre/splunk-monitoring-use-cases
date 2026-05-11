<!-- AUTO-GENERATED from UC-5.9.12.json — DO NOT EDIT -->

---
id: "5.9.12"
title: "Prefix Reachability by Region"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.12 · Prefix Reachability by Region

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We check whether people in different parts of the world — the Americas, Europe, and Asia — can all reach our addresses on the internet. Sometimes a cable break or regional outage makes us unreachable from one part of the world while everything looks fine from another, and this catches that before our customers in the affected region start complaining.*

---

## Description

Aggregates BGP prefix reachability by geographic region (Americas, EMEA, APAC) to detect regional routing outages — situations where a prefix is fully reachable from most of the world but unreachable from a specific region. This is a common pattern during submarine cable cuts, regional ISP outages, or localized BGP policy misconfigurations.

## Value

A prefix can be 98% reachable globally and still be completely unreachable from one region. The global average in UC-5.9.8 might not even trigger an alert because 290 out of 300 monitors still see the prefix. But if all 10 APAC monitors show 0% reachability, your entire Asia-Pacific user base is blacked out. This UC surfaces that regional disparity — showing the NOC immediately that the problem is APAC-specific, which narrows the investigation to APAC ISPs, submarine cable routes, or regional peering. Without regional breakdowns, the NOC might spend 30 minutes investigating globally before discovering the problem is localized.

## Implementation

Uses the same BGP data as UC-5.9.8. The `thousandeyes.monitor.location` field provides the geographic location of each monitor. The SPL maps these to business regions using a `case()` with country-code matching. Customize the region mapping to match your organization's operational regions. For more precise mapping, maintain a lookup table of `monitor_location` → `region`.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.8 apply — BGP tests configured, Tests Stream enabled, BGP data flowing.
- **Monitor geographic coverage:** For regional analysis to be meaningful, you need monitors in each region you care about. Check coverage:
```spl
index=thousandeyes_metrics thousandeyes.test.type="bgp" earliest=-1h
| stats dc(thousandeyes.monitor.name) as monitors by thousandeyes.monitor.location
| sort -monitors
```
If a critical region (e.g., APAC) has no monitors, regional analysis for that region is not possible.
- **Region mapping customization:** The default `case()` in the SPL uses common two-letter country codes. Customize for your business regions. For a more maintainable approach, create a lookup file `bgp_monitor_regions.csv`:
```csv
monitor_location,region
"San Jose, CA, US",Americas
"New York, NY, US",Americas
"Frankfurt, DE",EMEA
"London, GB",EMEA
"Tokyo, JP",APAC
"Singapore, SG",APAC
```
Then replace the `eval region=case(...)` with `| lookup bgp_monitor_regions monitor_location as thousandeyes.monitor.location OUTPUT region`.

### Step 1 — Configure data collection
Same as UC-5.9.8. No additional configuration.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location, "US|CA|MX|BR|AR|CL|CO"), "Americas",
    match(thousandeyes.monitor.location, "GB|DE|FR|NL|SE|NO|IT|ES|PL|IE|CH|AT|BE|ZA|AE|IL|NG"), "EMEA",
    match(thousandeyes.monitor.location, "JP|SG|AU|IN|KR|HK|TW|NZ|ID|TH|PH|MY|CN"), "APAC",
    1=1, "Other")
| stats avg(avg_reachability) as regional_reachability count as monitor_count by region, network.prefix
| sort region, network.prefix
```

**Understanding this SPL**

First `stats avg(bgp.reachability) ... by thousandeyes.monitor.location, network.prefix` — computes per-monitor-location reachability. This intermediate step is necessary because monitors at the same location may have different peering views.

`eval region=case(...)` — maps monitor locations to business regions. The `match()` function looks for country codes in the location string. This is a best-effort mapping that works for most ThousandEyes monitor location formats. For production use, the lookup-based approach (see Prerequisites) is more maintainable.

Second `stats avg(avg_reachability) ... by region, network.prefix` — aggregates the per-location reachability into regional averages. Also counts the number of monitor locations contributing to each regional average (`monitor_count`) — essential for assessing confidence in the regional score.

**Alert variant** (detect regional disparity):
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location, "US|CA|MX|BR|AR|CL|CO"), "Americas",
    match(thousandeyes.monitor.location, "GB|DE|FR|NL|SE|NO|IT|ES|PL|IE|CH|AT|BE|ZA|AE|IL|NG"), "EMEA",
    match(thousandeyes.monitor.location, "JP|SG|AU|IN|KR|HK|TW|NZ|ID|TH|PH|MY|CN"), "APAC",
    1=1, "Other")
| stats avg(avg_reachability) as regional_reachability count as monitor_count by region, network.prefix
| where regional_reachability < 95 AND monitor_count >= 5
| sort regional_reachability
```
The `monitor_count >= 5` filter ensures you don't alert on sparse regions where one flaky monitor skews the average.

**Cross-regional disparity detection** (find prefixes that are OK in some regions but degraded in others):
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location, "US|CA|MX|BR|AR|CL|CO"), "Americas",
    match(thousandeyes.monitor.location, "GB|DE|FR|NL|SE|NO|IT|ES|PL|IE|CH|AT|BE|ZA|AE|IL|NG"), "EMEA",
    match(thousandeyes.monitor.location, "JP|SG|AU|IN|KR|HK|TW|NZ|ID|TH|PH|MY|CN"), "APAC",
    1=1, "Other")
| stats avg(avg_reachability) as regional_reachability count as monitor_count by region, network.prefix
| eventstats max(regional_reachability) as best_region min(regional_reachability) as worst_region by network.prefix
| eval disparity = best_region - worst_region
| where disparity > 10
| sort -disparity
```
This finds prefixes where the best-performing region and worst-performing region differ by more than 10 percentage points — the hallmark of a regional routing issue.

**Scheduling:** Dashboard: auto-refresh every 15 minutes. Alert: cron `*/15 * * * *`, time range `-30m to now`. Throttle by `network.prefix` + `region` for 2 hours (regional outages need faster re-alerting than global ones).

### Step 3 — Validate
(a) **Region mapping accuracy.** Run: `| stats count by region, thousandeyes.monitor.location | sort region`. Verify that each monitor location mapped to the correct region. Fix any mismatches in your `case()` or lookup.

(b) **Monitor coverage per region.** Run: `| stats dc(thousandeyes.monitor.location) as locations by region`. You want at least 5 locations per critical region for meaningful analysis.

(c) **Known regional event.** If a regional ISP outage or submarine cable cut occurred recently, verify that the regional reachability for affected regions shows the drop. Cross-reference with ThousandEyes Outages page or bgpstream.com.

(d) **All-region parity.** During normal operations, all regions should show ~100% reachability. If one region consistently shows lower reachability (e.g., 97% vs 100% for others), investigate the specific monitors in that region — they may have local peering issues.

### Step 4 — Operationalize
**Dashboard** ("BGP Regional Health" — add as a tab in the UC-5.9.8 "BGP Prefix Health" dashboard):
- Row 1 — Column chart: regional reachability side by side per prefix. Colour-code: green ≥ 99%, yellow 95–99%, red < 95%.
- Row 2 — World map with monitor locations colour-coded by reachability.
- Row 3 — Heatmap: prefix × region → reachability %. This gives a compact overview of all prefixes across all regions.
- Row 4 — Disparity table: prefixes with > 10% regional disparity, showing best vs worst region.

**Runbook** (owner: Network Engineering / ISP Relations):
1. **Regional outage detected (one region < 95%, others at 100%).** Identify which monitors in the affected region show unreachable.
2. **Check submarine cable status.** For APAC outages, check submarinecablemap.com and ISP status pages. Cable cuts cause predictable regional outages.
3. **Check regional ISP status.** Look up the ISPs operating the affected monitors. Contact them with ThousandEyes evidence.
4. **Mitigation:** If you have regional traffic engineering capability (anycast, GeoDNS), reroute affected region's users to an alternate path.
5. **For data sovereignty concerns:** If the regional routing change causes traffic to transit through restricted countries, escalate to the compliance team.

### Step 5 — Troubleshooting

- **All monitors fall into "Other" region** — The `thousandeyes.monitor.location` format doesn't match your `match()` patterns. Check the actual format: `| stats count by thousandeyes.monitor.location | head 20`. The location may include city, state, and country name (not code). Adjust the patterns or switch to a lookup.

- **One region always shows 100% while others show < 100%** — This may be correct if the prefix is geographically localized. Or it may indicate that the region's monitors have favorable peering. Check monitor count per region to ensure adequate coverage.

- **All common troubleshooting** — See UC-5.9.8 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location, "US|CA|MX|BR|AR|CL|CO"), "Americas",
    match(thousandeyes.monitor.location, "GB|DE|FR|NL|SE|NO|IT|ES|PL|IE|CH|AT|BE|ZA|AE|IL|NG"), "EMEA",
    match(thousandeyes.monitor.location, "JP|SG|AU|IN|KR|HK|TW|NZ|ID|TH|PH|MY|CN"), "APAC",
    1=1, "Other")
| stats avg(avg_reachability) as regional_reachability count as monitor_count by region, network.prefix
| sort region, network.prefix
```

## Visualization

(1) World map: colour-coded by reachability per monitor location (the ThousandEyes app includes a built-in map). (2) Column chart: regional reachability side by side per prefix — immediately shows regional disparities. (3) Table: region, prefix, reachability %, monitor count — sorted by lowest reachability first. (4) Heatmap: prefix (Y-axis) × region (X-axis) → reachability % — cells turn red when reachability drops.

## Known False Positives

**Sparse monitor coverage in a region.** If only 2–3 monitors exist in a region and one has a local peering issue, regional reachability drops to 50–67% even though the region is fine. Distinguish by checking `monitor_count` — if it's < 5, the regional average is unreliable. Consider adding the `monitor_count` to your alert criteria: `where regional_reachability < 95 AND monitor_count >= 5`.

**Anycast prefix routing to different regional instances.** If your prefix is anycasted to different regions, some monitors may reach a regional instance while others reach a global instance. Reachability should still be 100%, but if a regional instance goes down, that region's reachability drops while other regions remain fine — this is a real outage (the anycast instance is down), not a false positive, but the root cause is your infrastructure rather than a BGP routing issue.

**Country-code mapping inaccuracy.** The `match()` function uses simplified country-code patterns. Some ThousandEyes monitor locations include city names, states, or country codes that may not match your regex patterns. If a monitor doesn't match any region, it falls into "Other," reducing coverage of the intended region. Verify by running `| stats count by region` and checking whether any monitors land in "Other" that should be in a specific region.

**Regional ISP maintenance during off-peak hours.** ISPs in some regions (especially APAC) perform maintenance during local off-peak hours, causing brief reachability dips. These typically last 1–4 hours and occur during known maintenance windows. Suppress with a regional maintenance calendar lookup.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes BGP Route Monitoring](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/)
- [Submarine Cable Map — shows physical cable routes relevant to regional reachability](https://www.submarinecablemap.com/)
