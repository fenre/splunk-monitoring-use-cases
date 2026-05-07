<!-- AUTO-GENERATED from UC-5.13.51.json — DO NOT EDIT -->

---
id: "5.13.51"
title: "Site Hierarchy Inventory"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.51 · Site Hierarchy Inventory

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Inventory &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep an up-to-date map of every office, building, and campus that your network covers. This map is what lets us show you which building has the worst network health, because without knowing which devices are in which building, all you see is a list of device names with no context.*

---

## Description

Provides a complete inventory of the Catalyst Center site hierarchy — every area, building, and floor — as the foundational reference that enables all location-based analytics (UC-5.13.5, UC-5.13.13, UC-5.13.19, UC-5.13.26) and powers the `catalyst_site_lookup` used across the Catalyst Center UC family.

## Value

This is the map that makes all site-based UCs work. Without it, device health by site (UC-5.13.5) shows UUIDs instead of building names, and operations can't correlate issues to physical locations. The site hierarchy also serves as the infrastructure documentation that facilities management, capacity planning, and network architecture teams reference when planning expansions, renovations, or site decommissions. Changes to the hierarchy (new buildings, merged areas) are detected automatically through this inventory.

## Implementation

Enable the `site_topology` input (Inputs → Create → Site Topology: account `catcenter-prod`, index `catalyst`, interval `3600`). Build the `catalyst_site_lookup` from this data for use across all site-based UCs. Schedule a daily `outputlookup` to keep the lookup current.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) installed on Search Heads AND Heavy Forwarder.
- Service account with **NETWORK-ADMIN-ROLE** for site topology data.
- This UC is foundational — it provides the `catalyst_site_lookup` that UC-5.13.5, UC-5.13.13, UC-5.13.19, UC-5.13.26, and others use for site name resolution. Deploy this before any site-based analytics.

### Step 1 — Configure data collection
Enable the `site_topology` input:

| Setting | Value |
|---------|-------|
| Input type | Site Topology |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `3600` (hourly — hierarchy changes slowly) |

The TA polls `GET /dna/intent/api/v1/topology/site-topology`. Each site (area, building, floor) produces one JSON event.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-2h
| stats dc(siteId) as sites
```
Compare with the count in **Catalyst Center > Design > Network Hierarchy**.

Build the site lookup (schedule daily):
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as siteName latest(siteType) as siteType latest(parentSiteName) as parentSiteName by siteId
| outputlookup catalyst_site_lookup
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| sort parent, type, name
```

Why `latest()` per siteId: deduplicates across poll cycles. Each poll returns the full hierarchy, so `latest()` gives the current state.

Why sort by parent, type, name: produces a hierarchical view — areas first, then buildings within each area, then floors within each building.

For site change detection:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-7d latest=-6d
| stats latest(siteName) as old_name by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-1d | stats latest(siteName) as new_name by siteId]
| where old_name != new_name OR isnull(new_name)
| eval change=case(isnull(new_name), "DELETED", old_name != new_name, "RENAMED")
```

### Step 3 — Validate
(a) Compare the site list with **Catalyst Center > Design > Network Hierarchy**. All areas, buildings, and floors should appear.
(b) Verify the hierarchy is correct: buildings should have areas as parents, floors should have buildings as parents.
(c) Check the `catalyst_site_lookup` is populated: `| inputlookup catalyst_site_lookup | stats count`.
(d) Vendor UI parity: open **Catalyst Center > Design > Network Hierarchy** and compare the site tree with the Splunk table.

### Step 4 — Operationalize
- Build and maintain the `catalyst_site_lookup` via daily scheduled search.
- Track site count growth over time for capacity planning.
- Detect hierarchy changes (renames, additions, deletions) weekly.
- Documentation: export the site hierarchy as a reference for facilities management.

Runbook:
1. If a new site appears: verify it was intentionally created in Catalyst Center.
2. If a site disappears: verify it was intentionally deleted. Check if devices were reassigned.
3. If a site is renamed: update any hardcoded site references in dashboards or lookups.

### Step 5 — Troubleshooting

- **No site topology events** — the `site_topology` input is not enabled. Check TA → Inputs.

- **Only one site (Global) appears** — the hierarchy hasn't been configured in Catalyst Center beyond the root. Create Area > Building > Floor structure in **Design > Network Hierarchy**.

- **Site names don't match what the team uses** — Catalyst Center site names may differ from common building names. Maintain an alias lookup that maps `siteId` to your organisation's preferred names.

- **`catalyst_site_lookup` is empty** — the `outputlookup` saved search hasn't run. Execute it manually or check the schedule.

- **Lookup has stale entries** — the daily `outputlookup` overwrites the entire file. If sites were deleted from Catalyst Center, they'll be removed from the lookup on the next run.

- **Floor entries make the table too long** — filter `| where siteType IN ("area","building")` for a building-level view.

- **Want to see device count per site** — join with device health: `| join siteId [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as devices by siteId]`.

- **Site data is the same every poll** — expected. The hierarchy changes infrequently. The hourly poll ensures changes are captured within 1 hour.

For hierarchy depth analysis (how well-structured is your site hierarchy?):
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| stats count by type
| eval ideal_ratio=case(type="area", "1 per region", type="building", "1 per physical building", type="floor", "1 per floor per building")
| table type, count, ideal_ratio
```
A well-structured hierarchy has 3–10 areas, 10–200 buildings (depending on org size), and 2–5 floors per building. A flat hierarchy (0 buildings, everything under Global) means site-based analytics (UC-5.13.5, UC-5.13.13, UC-5.13.19) provide no value.

For site-to-device mapping validation (which sites have devices assigned?):
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as name latest(siteType) as type by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as devices by siteId]
| eval devices=coalesce(devices, 0)
| where type="building"
| sort devices
```
Buildings with 0 devices are either newly created, not yet provisioned, or have all devices assigned to floors instead of the building level.

For automated lookup freshness check:
```spl
| inputlookup catalyst_site_lookup
| stats count as lookup_sites
| appendcols [search index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-2h | stats dc(siteId) as live_sites]
| eval drift=abs(lookup_sites - live_sites)
| eval status=if(drift > 5, "STALE — regenerate lookup", "Current")
| table lookup_sites, live_sites, drift, status
```
Schedule daily. If the lookup drifts by > 5 sites from the live data, trigger the `outputlookup` refresh.

Runbook expansion:
1. Initial deployment: build the `catalyst_site_lookup` immediately. All site-based UCs depend on it.
2. Daily: verify lookup freshness with the automated check. Regenerate if stale.
3. Weekly: review the hierarchy for orphaned sites (sites with 0 devices and no recent activity).
4. Monthly: compare the Catalyst Center hierarchy with the facilities management system. New buildings or closed offices should be reflected in both.
5. Quarterly: review whether the hierarchy granularity is sufficient. If operations teams complain about site-level data being too coarse, add floor-level entries.

Troubleshooting expansion:
- **Only one site (Global) appears** — the hierarchy hasn't been configured beyond the root. Create Area > Building > Floor structure in **Catalyst Center > Design > Network Hierarchy**.
- **Site names don't match what teams use** — maintain an alias lookup that maps `siteId` to your organisation's preferred building names, distinct from the `siteName` in Catalyst Center.
- **Lookup regeneration fails** — the `outputlookup` command requires write permission. Check the scheduling user's capabilities.
- **Floor entries make reports too granular** — filter `| where siteType IN ("area","building")` for building-level views. Include floors only when investigating specific coverage issues.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| sort parent, type, name
```

## Visualization

(1) Table: siteId, name, type, parent — sorted hierarchically. (2) Tree diagram or indented list showing the Global > Area > Building > Floor hierarchy. (3) Single value: total site count. (4) Timechart: `| timechart span=1d dc(siteId) as site_count` for site growth tracking.

## Known False Positives

**Test or staging sites appearing in the inventory.** Catalyst Center may have test hierarchy entries from development or staging environments. Distinguish by checking `siteName` for test/staging naming patterns. Suppress by maintaining a `catalyst_excluded_sites` lookup.

**Site hierarchy changes appearing as new/deleted sites.** When a building is renamed or moved to a different area, it appears as a new site with a new `siteId` while the old entry disappears. Distinguish by checking `parentSiteName` changes. Do not suppress — document the change for audit trail continuity.

**Floor entries inflating site count.** Catalyst Center's 4-level hierarchy (Global > Area > Building > Floor) means one physical building may have 5+ floor entries. Distinguish by filtering `| where siteType="building"` for building-level counts. The total site count includes all levels.

**Orphaned sites with no assigned devices.** Sites created during planning but never populated with devices show in the inventory with zero devices. Distinguish by cross-referencing with `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) by siteId` to find empty sites.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Network Hierarchy — Cisco Docs](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/design-guide.html)
