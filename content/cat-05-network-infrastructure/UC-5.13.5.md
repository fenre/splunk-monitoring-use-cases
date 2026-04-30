<!-- AUTO-GENERATED from UC-5.13.5.json — DO NOT EDIT -->

---
id: "5.13.5"
title: "Device Health by Site Hierarchy"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.5 · Device Health by Site Hierarchy

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We rank every office building and campus site by how healthy the network equipment inside it is. The buildings at the top of the list are the ones with the most problems — so your team knows exactly which location needs attention, instead of guessing from a fleet-wide average.*

---

## Description

Aggregates device health scores by Catalyst Center site hierarchy (area, building, floor), ranking locations by their concentration of unhealthy devices so operations can identify physical sites with systemic infrastructure problems — a failing UPS, an overloaded IDF, or a building with deferred maintenance.

## Value

UC-5.13.4 tells you which *type* of device is struggling; this UC tells you *where*. A distribution switch at score 40 in Building A is a very different problem from score 40 in Building B — different team, different vendor, different escalation path. Breaking health by site maps directly to your facilities and regional operations structure, and the ranked list focuses remediation budget on the sites that generate the most device-level pain.

## Implementation

Same data feed as UC-5.13.1. Requires `siteId` in the device health events (always present in Catalyst Center 2.3.5+). For human-readable site names, either (a) enable the `site:topology` input (UC-5.13.51) and build a lookup, or (b) create `lookups/catalyst_site_lookup.csv` manually from **Catalyst Center > Design > Network Hierarchy**.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational — same `devicehealth` data feed.
- `siteId` must be populated in the events. In Catalyst Center 2.3.5+, `siteId` is always present if the device is assigned to a site. Run `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | stats count(eval(isnull(siteId))) as null_sites, count as total`. If `null_sites > 0`, some devices are in the "Unassigned" pool — assign them in **Catalyst Center > Provision > Inventory**.
- For human-readable site names, create a lookup. Option A: enable UC-5.13.51 (Site Hierarchy Inventory) and build the lookup from `cisco:dnac:site:topology` events: `index=catalyst sourcetype="cisco:dnac:site:topology" | stats latest(siteName) as siteName by siteId | outputlookup catalyst_site_lookup`. Option B: export from **Catalyst Center > Design > Network Hierarchy** as CSV and upload to `$SPLUNK_HOME/etc/apps/<app>/lookups/catalyst_site_lookup.csv`.
- Understand your hierarchy depth: Catalyst Center uses a 4-level structure: Global > Area > Building > Floor. This UC aggregates at whatever level `siteId` represents — typically Building. If you need Area-level rollup, join with the site topology data and group by `parentSiteName`.

### Step 1 — Configure data collection
No additional input configuration. The `devicehealth` input from UC-5.13.1 includes `siteId` in every event. For the site name lookup, enable the `site:topology` input if not already running:

| Setting | Value |
|---------|-------|
| Input type | Site Topology |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `3600` (hourly — hierarchy rarely changes) |

Build the lookup:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as siteName latest(siteType) as siteType latest(parentSiteName) as parentSiteName by siteId
| outputlookup catalyst_site_lookup
```
Schedule this as a saved search running daily to keep the lookup current.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId
| eval unhealthy_pct=round(unhealthy_count*100/device_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -unhealthy_pct
| head 20
```

Why `by siteId` not `by siteName` in the base stats: `siteId` is the stable identifier — `siteName` can be renamed in the hierarchy without changing the UUID. Grouping by `siteId` and then enriching with `| lookup` ensures the stats are correct even if the site name changes between the poll and the search.

Why `head 20`: in a large enterprise with 100+ sites, the full list is overwhelming. The top-20 ranked by `unhealthy_pct` focuses attention on the worst sites. For the full list, remove `| head 20` and export as CSV for the facilities team.

Why `coalesce(siteName, siteId)`: if the lookup is incomplete (a new site was added but the lookup hasn't refreshed), fall back to the UUID so the site still appears in results. A missing name is better than a missing row.

This is a report for weekly operations reviews and facilities planning, not a real-time alert. Schedule: cron `0 7 * * 1` (Monday 7 AM), output to PDF.

### Step 3 — Validate
(a) Run the search and sum `device_count` across all rows. It should match the total device count from UC-5.13.1. If lower, some devices have null `siteId` and are excluded from the `by siteId` grouping.

(b) Pick the worst site from the results. Drill in: `index=catalyst sourcetype="cisco:dnac:devicehealth" siteId="<that-id>" | where overallHealth < 50 | table deviceName overallHealth deviceType`. Verify these devices are genuinely unhealthy in **Catalyst Center > Assurance > Health > Device** filtered by that site.

(c) Verify site name resolution: check that `site_label` shows building names, not UUIDs. If all labels are UUIDs, the lookup is empty — regenerate per Step 1.

(d) Cross-reference with **Catalyst Center > Assurance > Health > Network Health by Site**. The ranked order should be similar, though Catalyst Center may weight sites differently than a simple `unhealthy_pct`.

(e) Check for the "Global" catch-all: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count by siteId | sort -count | head 5`. If one `siteId` has a disproportionate device count, it's likely the unassigned root — filter or investigate.

### Step 4 — Operationalize
Dashboard placement:
- **Row 4** on the Device Health Overview dashboard, or as the main panel on a dedicated "Site Health" dashboard.
- Bar chart: top 20 sites by `unhealthy_pct`, horizontal bars, red/yellow/green colour coding.
- Table next to the chart for exact numbers.
- Token-driven drilldown: click a site → filter UC-5.13.1 table, UC-5.13.9 client health, and UC-5.13.21 issues all to that `siteId`.

Runbook (owner: Regional Operations):
1. Identify the site with the highest `unhealthy_pct`.
2. Check whether the devices are unhealthy due to the same subscore (cpuScore, memoryScore, interDeviceLinkScore) — if so, the cause is likely systemic to that site (power, cooling, shared upstream).
3. Check whether the site had a recent maintenance event: `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-7d | search "*<siteName>*"`.
4. For physical infrastructure issues (multiple devices failing simultaneously at one site): contact the facilities team for that building — check UPS, HVAC, and cabling.
5. For firmware-related issues concentrated at one site: check UC-5.13.56 (Firmware Non-Compliance) filtered by that site's devices.
6. Track site rankings month-over-month. A site that consistently ranks in the top 5 worst is a candidate for an infrastructure refresh project.

### Step 5 — Troubleshooting

- **All devices grouped under one siteId** — the site hierarchy is flat (everything under Global). Fix in Catalyst Center by creating Area > Building > Floor hierarchy and assigning devices. This UC only adds value when the hierarchy is meaningful.

- **Site names show as UUIDs** — the `catalyst_site_lookup` is empty or stale. Regenerate per Step 1. Common cause: the `site:topology` input is not enabled, or the `outputlookup` saved search hasn't run.

- **A site shows 100% unhealthy with high device count** — this is a real site-wide event (power failure, upstream link down). Verify in Catalyst Center and escalate.

- **Duplicate sites with similar names** — Catalyst Center may have test or backup hierarchy entries. Check in **Catalyst Center > Design > Network Hierarchy** for orphaned or duplicate buildings.

- **`unhealthy_pct` doesn't match Catalyst Center's site health view** — Catalyst Center's site health includes client and application health, not just device health. This UC only measures device health by site. For a combined view, correlate with UC-5.13.13 (Client Health by Site) and UC-5.13.19 (Network Health by Site).

- **New site appears with bad health** — a newly created site with devices recently assigned may show poor health because Assurance hasn't built baselines. Wait 24–48 hours before acting on the data.

- **Site hierarchy change invalidates historical comparisons** — if sites were reorganised, the same `siteId` may now represent a different physical area. Note the change date and compare trends separately for before/after.

- **Search is slow on large fleets** — with 10,000+ devices across 200+ sites, the `stats by siteId` is processing many events. Narrow the time range to `-20m` (one poll cycle) for the current snapshot. For trending, use summary indexing.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId
| eval unhealthy_pct=round(unhealthy_count*100/device_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -unhealthy_pct
| head 20
```

## Visualization

(1) Bar chart: top 20 sites by `unhealthy_pct`, red bars (> 10%), yellow (5–10%), green (< 5%). (2) Table: site_label | device_count | avg_health | unhealthy_count | unhealthy_pct — drilldown to UC-5.13.1 filtered by `siteId`. (3) Optional choropleth/tile map if you join geo-coordinates from the site hierarchy or a CMDB lookup. (4) Trellis of sparklines: one per top-10 site showing `avg_health` over 7 days for trend context.

## Known False Positives

**Site hierarchy reorganisation moving devices between siteIds.** When Catalyst Center's site hierarchy is restructured (buildings moved between areas, floors renumbered), the same device may appear under a different `siteId`, creating phantom improvements at the old site and phantom degradation at the new site. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for site hierarchy changes. Suppress by tracking by `deviceName` (stable) when investigating anomalies and only using `siteId` for steady-state views.

**Small site with 1–2 devices producing misleading percentages.** A remote branch with 2 switches where one is briefly unhealthy shows 50% `unhealthy_pct` — alarming on the chart but representing a single device. Distinguish by checking `device_count`. Suppress by filtering `| where device_count >= 5` for the ranked chart and showing small sites separately.

**`siteId` null for devices not assigned to a site.** Devices in the "Unassigned" or "Global" default site show `siteId` as a root UUID or null, aggregating unrelated devices into one bucket. Distinguish by checking whether the "site" is the catch-all Global. Suppress by filtering `| where siteId != "<global-root-uuid>"` or by assigning all devices to proper sites in Catalyst Center.

**Multi-building campus sharing one siteId.** If the site hierarchy was not granulated below the area level, multiple buildings may share one `siteId`, masking per-building differences. Distinguish by checking the hierarchy depth in Catalyst Center > Design > Network Hierarchy. No Splunk suppression — fix the hierarchy in Catalyst Center to get floor/building-level granularity.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide — Site Hierarchy](docs/guides/catalyst-center.md#field-dictionary)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
