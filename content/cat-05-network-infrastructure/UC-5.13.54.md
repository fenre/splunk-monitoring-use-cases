<!-- AUTO-GENERATED from UC-5.13.54.json — DO NOT EDIT -->

---
id: "5.13.54"
title: "Site-to-Device Ratio and Capacity Planning"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.54 · Site-to-Device Ratio and Capacity Planning

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Inventory &middot; **Wave:** Walk &middot; **Status:** Verified

*We count how many network devices are installed at each building and compare it to the average. Buildings with many more devices than usual need extra attention and support, while buildings with very few might have coverage gaps. This helps your team plan where to invest in new equipment before running out of capacity.*

---

## Description

Analyses the distribution of network devices across Catalyst Center sites, showing device density per building and identifying over-provisioned sites (potential complexity), under-provisioned sites (potential coverage gaps), and sites whose device count deviates significantly from the fleet average — driving infrastructure capacity planning decisions.

## Value

A campus with 500 devices doesn't mean 50 per building. Building A might have 120 devices (data centre) while Building E has 8 (small branch). Understanding this distribution drives three decisions: (1) Support staffing — high-density sites need more engineering coverage. (2) Infrastructure investment — sites with growing device counts need switch/port expansion. (3) License allocation — Catalyst Center and DNA licenses may need redistribution as the fleet shifts between sites. The statistical density score highlights outliers that are significantly above or below the fleet average.

## Implementation

Same `devicehealth` input as UC-5.13.1. Groups by `siteId` and enriches with `catalyst_site_lookup` (UC-5.13.51). Schedule monthly for capacity planning review.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health Overview) and UC-5.13.51 (Site Hierarchy Inventory) must be operational.
- `catalyst_site_lookup` must be populated for site name resolution.
- For capacity planning, maintain a `site_capacity` lookup with columns: `siteId`, `max_devices`, `max_clients`, `building_sqft` — this enables density calculations and capacity threshold alerting.
- This is a walk-tier capacity planning UC. The audience is the quarterly network architecture review, not the daily operations team.

### Step 1 — Configure data collection
Same `devicehealth` input as UC-5.13.1. No additional configuration.

Confirm `siteId` is populated:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
| stats dc(deviceName) as devices by siteId
| sort -devices
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats dc(deviceName) as device_count avg(overallHealth) as avg_health by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName, siteType
| eval site_label=coalesce(siteName, siteId)
| eventstats avg(device_count) as fleet_avg stdev(device_count) as fleet_stdev
| eval density_z=if(fleet_stdev>0, round((device_count-fleet_avg)/fleet_stdev,1), 0)
| sort -device_count
```

Why `dc(deviceName)` per siteId: gives the unique device count per site within the search window. This is the infrastructure density metric — how much network equipment is installed at each location.

Why include `avg_health`: adds a health dimension to the density view. A high-density site with low average health is the highest-priority investment target — many devices AND they're struggling.

Why `density_z` (z-score): normalises device count against the fleet average. A z-score > 2 means the site has significantly more devices than average (data centre, headquarters). A z-score < -1 means significantly fewer (small branch). This highlights outliers for investigation or capacity planning attention.

For combined device + client density (comprehensive capacity view):
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats dc(deviceName) as devices by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as clients by siteId]
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval clients_per_device=if(devices>0, round(clients/devices,0), 0)
| sort -clients_per_device
```
Sites with very high `clients_per_device` may be undersized (too few switches/APs for the user population). Sites with very low ratios may be over-provisioned.

For device growth tracking (capacity planning trend):
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| timechart span=1w dc(deviceName) as weekly_devices by siteId
```
Sites with consistent growth need proactive switch/port expansion before they hit capacity limits.

For capacity threshold alerting (when a site exceeds its planned capacity):
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats dc(deviceName) as devices by siteId
| lookup site_capacity siteId OUTPUT max_devices, siteName
| where isnotnull(max_devices) AND devices > max_devices * 0.9
| eval status=case(devices > max_devices, "OVER CAPACITY", devices > max_devices*0.9, "NEAR CAPACITY")
| table siteName, devices, max_devices, status
```

Schedule: monthly (cron `0 7 1 * *`), output to PDF for the capacity planning review.

### Step 3 — Validate
(a) Compare total `dc(deviceName)` across all sites with UC-5.13.1's total device count. They should match (minus orphaned devices from UC-5.13.53).

(b) Verify the largest site by device_count matches your expectations (typically headquarters or data centre).

(c) Cross-reference with facilities data: does the device density correlate with building size and user population?

(d) The `density_z` outliers should match known high-density (data centre) and low-density (small branch) sites.

(e) Vendor UI parity: compare site device counts with **Catalyst Center > Provision > Inventory** filtered by site.

### Step 4 — Operationalize
- Monthly capacity review: which sites are growing? Which are shrinking?
- Investment planning: sites with high density_z AND low avg_health need both more equipment AND better equipment.
- Staffing: high-density sites need more engineering support coverage.
- License management: redistribute DNA licenses based on actual device distribution.
- Near-capacity alerts: sites at > 90% of planned capacity need expansion planning before they hit limits.

Runbook (owner: Network Architecture, monthly):
1. Review device count per site. Identify sites with > 10% growth over the past quarter.
2. For growing sites: verify switch port availability. Plan expansion if utilisation > 80%.
3. For high clients_per_device sites: check if users are experiencing poor connectivity (UC-5.13.13). If yes, add APs or switches.
4. For over-capacity sites: create a hardware procurement request for the next budget cycle.
5. Track month-over-month: are the same sites growing every month? Plan ahead.

### Step 5 — Troubleshooting

- **All sites show similar device counts** — the fleet may be uniformly distributed (unlikely in practice). Check if `siteId` is properly populated — all devices under Global would show one large site.

- **Data centre site has extreme density_z** — expected. Data centres have 10–100× more devices than branches. Use category-aware comparison: `| lookup site_categories siteId OUTPUT category | stats avg(device_count) as avg by category`.

- **Device count per site doesn't match CMDB** — check for devices assigned to the wrong site. Compare with the CMDB via a lookup join.

- **`catalyst_site_lookup` missing** — regenerate per UC-5.13.51.

- **Growth trend shows sudden spike at one site** — new devices provisioned (planned expansion) or devices reassigned from another site. Check audit logs.

- **`clients_per_device` is very high at wireless-heavy sites** — expected. Sites with many APs but few switches have high client-per-device ratios. This is healthy for wireless-dense deployments.

- **Search is slow for large fleets** — narrow to `earliest=-20m` for a snapshot. Use summary indexing for monthly trends.

- **Zero devices at some sites** — sites exist in the hierarchy but have no assigned devices. See UC-5.13.53 for orphaned device detection.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats dc(deviceName) as device_count avg(overallHealth) as avg_health by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName, siteType
| eval site_label=coalesce(siteName, siteId)
| eventstats avg(device_count) as fleet_avg stdev(device_count) as fleet_stdev
| eval density_z=if(fleet_stdev>0, round((device_count-fleet_avg)/fleet_stdev,1), 0)
| sort -device_count
```

## Visualization

(1) Table: site_label, siteType, device_count, avg_health, density_z — sorted by device_count. (2) Bar chart: device_count per site (top 20). (3) Scatter: device_count (x) vs avg_health (y) per site — sites with high device count and low health need attention. (4) Timechart: `| timechart span=1w dc(deviceName) by siteId` for device growth per site over 90 days.

## Known False Positives

**Data centre sites with very high device counts.** A data centre or core site naturally has many more devices than a branch office. Its high density_z score is expected, not anomalous. Distinguish by checking `siteType` or maintaining a `site_category` lookup (datacenter/campus/branch). Suppress by comparing within categories rather than across the entire fleet.

**New site with very few devices during build-out.** A site under construction may show an unusually low device count. Distinguish by checking the site's age (UC-5.13.52) and whether devices are being actively provisioned. No suppression needed — track as a growing site.

**Virtual domain scope limiting visible devices at some sites.** The TA service account may see fewer devices at sites where the virtual domain scope is restricted. Distinguish by comparing with the count in **Catalyst Center > Provision > Inventory** at Global scope. Fix by expanding the service account's virtual domain access.

**Devices assigned to the wrong site.** A device physically in Building A but assigned to Building B in Catalyst Center inflates B's count and deflates A's. Distinguish by cross-referencing with CMDB or physical site surveys. Fix in Catalyst Center > Provision > Inventory > [device] > Assign to Site.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide — Capacity Planning](../../docs/guides/catalyst-center.md#sizing)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
