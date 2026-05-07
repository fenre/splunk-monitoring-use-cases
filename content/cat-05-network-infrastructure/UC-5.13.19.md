<!-- AUTO-GENERATED from UC-5.13.19.json — DO NOT EDIT -->

---
id: "5.13.19"
title: "Network Health by Site (Area/Building)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.19 · Network Health by Site (Area/Building)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We rank every building and campus by how healthy the network equipment inside it is. The locations with the most infrastructure problems show up at the top, so your team knows exactly which building needs a visit — whether it is to fix a failing switch, replace a broken power supply, or call the building electrician.*

---

## Description

Ranks Catalyst Center sites by aggregate device health, showing which buildings and campuses have the worst infrastructure scores — enabling operations to prioritise site-level remediation over fleet-wide changes that may not address localised problems like a failing UPS, overloaded IDF, or deferred cabling maintenance.

## Value

UC-5.13.16 gives you one campus-wide number. This UC breaks it into *where*. A campus score of 82 may hide the fact that headquarters is at 95 while the branch office in Building C is at 55 — because Building C's HVAC failed last week and the switches are thermal-throttling. Without the site split, you'd tune RRM globally when you only need to call facilities for one building. The ranked list also identifies sites for proactive infrastructure surveys before users start complaining, and tracks whether a site-specific remediation (switch refresh, UPS replacement) actually moved the needle.

## Implementation

Uses the `devicehealth` feed (same as UC-5.13.1), grouped by `siteId`. For site name resolution, use the `catalyst_site_lookup` from UC-5.13.5 or UC-5.13.51. Schedule as weekly report for regional operations.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health Overview) must be operational — same `devicehealth` data feed.
- `siteId` must be populated in device health events (always present in Catalyst Center 2.3.5+ for assigned devices). Run `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | stats count(eval(isnull(siteId))) as null_sites, count as total`. If `null_sites > 0`, some devices are in the "Unassigned" pool — assign them in **Catalyst Center > Provision > Inventory**.
- `catalyst_site_lookup` must be populated for site name resolution. See UC-5.13.51 for building the lookup.
- Note: the `networkhealth` sourcetype (UC-5.13.16) is a cluster-wide aggregate with no `siteId` dimension. For per-site network health, this UC uses `devicehealth` grouped by `siteId` — a different approach that gives site-level granularity by aggregating per-device health scores.
- Understand your hierarchy depth: Catalyst Center uses a 4-level structure (Global > Area > Building > Floor). This UC aggregates at whatever level `siteId` represents — typically Building. If you need Area-level rollup, join with the site topology data and group by `parentSiteName`.

### Step 1 — Configure data collection
Same `devicehealth` input as UC-5.13.1. No additional configuration needed. For the site name lookup, ensure the `site_topology` input is enabled and the `catalyst_site_lookup` is built:
```spl
| inputlookup catalyst_site_lookup | stats count
```
If count = 0, build it: `index=catalyst sourcetype="cisco:dnac:site:topology" | stats latest(siteName) as siteName latest(siteType) as siteType latest(parentSiteName) as parentSiteName by siteId | outputlookup catalyst_site_lookup`

Verify `siteId` distribution:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
| stats dc(deviceName) as devices by siteId
| sort -devices
```
If one `siteId` has a disproportionate device count, it's likely the Global root — filter or investigate.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as bad_count by siteId
| eval bad_pct=round(bad_count*100/device_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -bad_pct
| head 20
```

Why use `devicehealth` instead of `networkhealth`: the `networkhealth` API returns a single cluster-wide aggregate without a `siteId` dimension. To get per-site health, you must aggregate per-device scores from `devicehealth` by `siteId`. This gives a different (but complementary) view: UC-5.13.16 is the official Assurance composite score; this UC is a device-health-only aggregate per location.

Why `where overallHealth > 0` before aggregation: filters Assurance recomputation artifacts (brief zero-score events) that would drag site averages down with zeros.

Why `bad_pct` as the ranking metric: `avg_health` can be misleading — a site with 49 healthy devices and 1 critically sick device averages 97. `bad_pct` surfaces the concentration of problems regardless of site size. Sorting by `bad_pct` descending puts the most-troubled sites at the top.

Why `coalesce(siteName, siteId)`: if the lookup doesn't resolve a siteId (new site not yet in the lookup), falls back to the UUID. A missing name is better than a missing row.

Why `head 20`: focuses the operations review on the top 20 worst sites. For the full list, remove `| head 20` and export as CSV for the facilities team.

For site-level health trending (capacity planning):
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| bin _time span=1d
| stats avg(overallHealth) as daily_health by siteId, _time
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| timechart span=1d avg(daily_health) by site_label
```

For combined device + client health per site:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| stats avg(overallHealth) as device_health dc(deviceName) as devices by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:client" | stats avg(healthScore{}.score) as client_health dc(macAddress) as clients by siteId]
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval combined=round((device_health*0.4 + coalesce(client_health,device_health)*0.6),1)
| sort combined
| head 20
```

Schedule as Report: weekly (cron `0 7 * * 1`), output to PDF for the regional ops meeting.

### Step 3 — Validate
(a) Sum `device_count` across all sites. Should match UC-5.13.1's total device count (minus any with null `siteId`).

(b) Pick the worst site from the results. Drill to UC-5.13.1 filtered by that `siteId`: `index=catalyst sourcetype="cisco:dnac:devicehealth" siteId="<that-id>" | where overallHealth < 50 | table deviceName overallHealth deviceType`. Verify these devices are genuinely unhealthy in **Catalyst Center > Assurance > Health > Device** filtered by that site.

(c) Verify site name resolution: all `site_label` values should be building names, not UUIDs. If all are UUIDs, regenerate the `catalyst_site_lookup`.

(d) Cross-reference with **Catalyst Center > Assurance > Health > Network Health by Site**. The ranked order should be similar, though Catalyst Center may weight sites differently than a simple `bad_pct`.

(e) Check for the "Global" catch-all: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) by siteId | sort -dc(deviceName) | head 5`. If one `siteId` has a disproportionate device count, it's likely the unassigned root — filter or investigate.

(f) Compare per-site device health with per-site client health (UC-5.13.13): sites that rank poorly on both dimensions have infrastructure AND user-experience problems — highest priority for investment.

### Step 4 — Operationalize
Dashboard placement:
- On the Network Health dashboard below UC-5.13.16's single-value gauge, or as the main panel on a dedicated "Site Health" dashboard.
- Bar chart: top 20 sites by `bad_pct`, horizontal bars, red/yellow/green colour coding.
- Table next to the chart for exact numbers. Token-driven drilldown: click a site → filter UC-5.13.1 table, UC-5.13.9 (Client Health), and UC-5.13.21 (Issues) all to that `siteId`.
- Time-picker presets: "Last 1 hour" (current state), "Last 7 days" (weekly review).

Runbook (owner: Regional Operations):
1. Identify the site with the highest `bad_pct`.
2. Check whether the bad devices share a common characteristic:
   - Same `deviceType` → fleet-level issue (firmware bug). Cross-reference with UC-5.13.4.
   - Same `platformId` → hardware-specific issue (bad batch, power supply model).
   - Mixed types → site-level issue (power, cooling, cabling, upstream link).
3. Cross-reference with UC-5.13.13 (Client Health by Site) to assess user impact:
   - Device health poor AND client health poor → confirmed user impact, high priority.
   - Device health poor BUT client health OK → devices are degraded but not yet impacting users — still needs remediation but lower urgency.
   - Device health OK BUT client health poor → problem is in the wireless/client layer (DHCP, DNS, RF), not the infrastructure.
4. For physical infrastructure issues (multiple devices failing simultaneously): contact the facilities team for that building — check UPS, HVAC, and cabling.
5. For firmware-related issues concentrated at one site: check UC-5.13.56 (Firmware Non-Compliance) filtered by that site's devices.
6. Track site rankings month-over-month. A site that consistently ranks in the top 5 worst is a candidate for an infrastructure refresh project.

Capacity planning (monthly, owner: Network Architecture):
- Overlay device count growth with health trends per site. Growing fleet + declining health = underinvestment at that site.
- Compare site rankings quarter-over-quarter. Sites that improve after investment confirm ROI. Sites that worsen despite investment need a design review.

### Step 5 — Troubleshooting

- **All devices grouped under one siteId** — the site hierarchy is flat (everything under Global). Fix in Catalyst Center by creating Area > Building > Floor hierarchy and assigning devices. This UC only adds value when the hierarchy is meaningful.

- **Site names show as UUIDs** — the `catalyst_site_lookup` is empty or stale. Regenerate per UC-5.13.51. Common cause: the `site:topology` input is not enabled, or the `outputlookup` saved search hasn't run.

- **A site shows 100% bad_pct with high device count** — this is a real site-wide event (power failure, upstream link down, switch stack failure). Verify in Catalyst Center and escalate immediately.

- **Per-site averages don't match the campus-wide score from UC-5.13.16** — expected. UC-5.13.16 uses the Assurance-computed composite (weighted by device role and health dimensions). This UC uses a simple `avg(overallHealth)` per site. The two views complement each other.

- **New site appears with poor health** — recently created site with newly assigned devices. Assurance needs 24–48 hours to build baselines.

- **Search is slow with large fleets** — with 10,000+ devices across 200+ sites, narrowing to `earliest=-20m` gives a single-poll snapshot. For trending, use summary indexing: schedule `| stats avg(overallHealth) dc(deviceName) by siteId | collect index=catalyst_summary` daily.

- **One site dominates with very high device count** — headquarters or data centre. Consider separating by `siteType`: `| lookup catalyst_site_lookup siteId OUTPUT siteType | where siteType="building"` to exclude data centres from the campus comparison.

- **Device count at a site doesn't match Catalyst Center Inventory for that site** — check virtual domain scope of the service account. The TA may see fewer devices than the full inventory if the service account is scoped to a subset of domains.

- **Duplicate sites with similar names** — Catalyst Center may have test or backup hierarchy entries. Check in **Catalyst Center > Design > Network Hierarchy** for orphaned or duplicate buildings. Clean up duplicates to prevent split metrics.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth > 0
| stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as bad_count by siteId
| eval bad_pct=round(bad_count*100/device_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -bad_pct
| head 20
```

## Visualization

(1) Bar chart: top 20 sites by `bad_pct`, red/yellow/green colour coding. (2) Table: site_label | device_count | avg_health | bad_count | bad_pct — drilldown to UC-5.13.1 filtered by `siteId`. (3) Optional choropleth map if geo-coordinates are available. (4) Timechart variant: `| timechart span=1d avg(overallHealth) by siteId` for per-site trending.

## Known False Positives

**Site hierarchy reorganisation moving devices between siteIds.** When Catalyst Center's hierarchy is restructured, devices may shift between siteIds, creating phantom improvements at the old site and phantom degradation at the new one. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for hierarchy changes. Suppress by tracking by `deviceName` (stable) when investigating anomalies.

**Small-population sites producing volatile percentages.** A remote branch with 3 devices where 1 is unhealthy shows 33% bad — alarming but a single device. Distinguish by checking `device_count`. Suppress by filtering `| where device_count >= 5` for the ranked chart.

**All devices at a site showing null siteId.** Devices in the unassigned 'Global' site aggregate into one misleading bucket. Distinguish by checking whether the `siteId` is the root UUID. Suppress by filtering or by assigning all devices to proper sites in Catalyst Center.

**Maintenance window at one site dragging its health down temporarily.** During a firmware upgrade at Building A, all its devices reload and show poor health. Distinguish by correlating with ITSM change records. Suppress by annotating the chart with maintenance windows.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
