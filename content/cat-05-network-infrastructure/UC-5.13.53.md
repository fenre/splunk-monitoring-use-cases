<!-- AUTO-GENERATED from UC-5.13.53.json — DO NOT EDIT -->

---
id: "5.13.53"
title: "Unmanaged or Orphaned Device Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.53 · Unmanaged or Orphaned Device Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Inventory, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We find network devices that haven't been assigned to a specific building or location in the system — meaning they are invisible to all the dashboards and reports that show health by building. We flag them so your team can put them in the right place and make sure nothing falls through the cracks.*

---

## Description

Identifies network devices managed by Catalyst Center that are not properly assigned to a site in the hierarchy — orphaned in the 'Global' or 'Unassigned' pool — meaning they miss site-specific policies, compliance checks, health-by-site analytics, and regional team assignments.

## Value

A device without a site assignment is invisible to every site-based UC in the Catalyst Center family (UC-5.13.5, UC-5.13.13, UC-5.13.19, UC-5.13.26). It doesn't appear in regional health dashboards, doesn't get site-specific compliance policies, and can't be routed to the correct regional operations team when it has problems. This UC finds these orphans so they can be assigned to the correct building and floor in Catalyst Center — closing the visibility gap before it becomes an unmonitored failure.

## Implementation

Same `devicehealth` input as UC-5.13.1. Cross-references with `catalyst_site_lookup` (UC-5.13.51) to identify devices whose siteId resolves to Global or null. Schedule weekly for inventory review.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health Overview) must be operational — provides the device list.
- UC-5.13.51 (Site Hierarchy Inventory) must be operational — provides the `catalyst_site_lookup` for site name resolution.
- Understand your organisation's site assignment policy: should every managed device have a specific building/floor assignment, or are some devices intentionally in the Global site?

### Step 1 — Configure data collection
Same `devicehealth` input as UC-5.13.1 and `site_topology` input as UC-5.13.51. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as health latest(siteId) as site latest(deviceType) as type latest(managementIpAddress) as ip by deviceName
| where isnull(site) OR site=""
| table deviceName, ip, type, health, site
```

Simplified approach: devices with null or empty `siteId` are definitely unassigned. For devices assigned to the root Global site (which may have a valid UUID but represent 'unassigned'), use the lookup-based approach:

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as health latest(siteId) as site latest(deviceType) as type latest(managementIpAddress) as ip by deviceName
| lookup catalyst_site_lookup siteId as site OUTPUT siteName
| where isnull(siteName) OR siteName="Global"
| table deviceName, ip, type, health, site
```

Why lookup-based detection: the Global root site has a valid `siteId` UUID, so `isnull(site)` alone won't catch devices parked in Global. The lookup resolves the UUID to a name; if it resolves to 'Global' or doesn't resolve at all, the device is orphaned.

Schedule: weekly (cron `0 7 * * 1`). Output to the inventory review dashboard.

### Step 3 — Validate
(a) Check **Catalyst Center > Provision > Inventory** and filter to 'Unassigned' or 'Global' devices. Compare with the Splunk search results.
(b) Verify that all properly-assigned devices are excluded from the results.
(c) Cross-reference: devices in UC-5.13.1 that don't appear in UC-5.13.5 (Device Health by Site) are likely orphaned.
(d) Vendor UI parity: compare the orphaned device list with the Catalyst Center inventory filtered to Global scope.

### Step 4 — Operationalize
- Weekly inventory review: identify and assign orphaned devices to the correct site.
- Track orphan count over time: `| timechart span=1w dc(deviceName) as orphaned`. A growing count indicates onboarding process gaps.
- For new device onboarding: add site assignment to the PnP workflow so devices are never orphaned.

Runbook:
1. Review the weekly orphaned device list.
2. For each device: determine the physical location (check asset management system, CMDB, or ask the network team).
3. Assign the device to the correct site in **Catalyst Center > Provision > Inventory > [device] > Assign to Site**.
4. Verify the device appears in site-based UCs within the next poll cycle.

### Step 5 — Troubleshooting

- **All devices appear as orphaned** — the `catalyst_site_lookup` is empty. Regenerate per UC-5.13.51.

- **No orphaned devices found** — either all devices are properly assigned (ideal) or the search logic isn't matching your site hierarchy structure. Check `| stats values(siteId) | head 5` to see the actual `siteId` format.

- **Devices with valid siteId appear in results** — the lookup doesn't contain that `siteId`. Regenerate the lookup.

- **Virtual devices flagged** — expected if you don't have a `virtual_devices` exception lookup. Create one or filter by `deviceType`.

- **Count fluctuates week to week** — devices are being discovered (added) and assigned (removed) at similar rates. Track the net trend.

- **PnP-onboarded devices always appear initially** — PnP assigns a site during provisioning, but there may be a 1–2 poll delay. Allow a grace period.

- **Global site UUID is unknown** — run `| stats count by siteId | sort -count | head 1`. The most-populated siteId is likely the Global root.

- **Want to alert on new orphans** — schedule daily with `| where first_seen > relative_time(now(), "-24h")` to catch newly-discovered unassigned devices.

For device-to-AP correlation (identify which AP an orphaned wireless device connects through):
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats latest(apName) as connected_ap latest(siteId) as client_site by macAddress
| where isnull(client_site) OR client_site=""
| stats dc(macAddress) as orphaned_clients by connected_ap
| sort -orphaned_clients
```
Orphaned clients connected to a specific AP indicate that AP needs site assignment — fixing the AP assignment fixes all its clients.

For periodic orphan tracking (is the backlog growing or shrinking?):
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| eval is_orphan=if(isnull(siteId) OR siteId="", 1, 0)
| timechart span=1d dc(eval(if(is_orphan=1, deviceName, null()))) as orphaned_devices
```
A declining line means the team is assigning devices. A growing line means new devices are being provisioned without site assignment — fix the PnP workflow.

For PnP onboarding enforcement:
- Modify the Catalyst Center PnP workflow to require site assignment during provisioning
- Track newly discovered devices that bypass PnP: `index=catalyst sourcetype="cisco:dnac:device" | stats earliest(_time) as discovered by hostname | where discovered > relative_time(now(), "-48h") | join type=left hostname [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(siteId) as site by deviceName | rename deviceName as hostname] | where isnull(site)`

Runbook expansion:
1. Weekly orphan review: identify all unassigned devices.
2. For each: determine physical location from CMDB, IP address range, or asking the network team.
3. Assign in **Catalyst Center > Provision > Inventory > [device] > Assign to Site**.
4. Verify the device appears in site-based UCs within the next poll cycle.
5. If the device can't be located physically: check if it's a virtual device, a decommissioned device still in inventory, or a device that was moved without updating Catalyst Center.
6. Track orphan count monthly. Goal: zero orphaned devices.

Troubleshooting expansion:
- **PnP-onboarded devices appear as orphaned temporarily** — PnP assigns a site during provisioning, but there's a 1-2 poll delay before the site assignment propagates to the devicehealth feed. Allow 2-hour grace period.
- **Virtual devices (WLC virtual interfaces, Catalyst Center appliance) flagged** — maintain a `virtual_devices` lookup to exclude non-physical devices.
- **Device count fluctuates** — devices being discovered and removed from inventory cause the orphan count to fluctuate. Track by `hostname` (stable) rather than event count.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as health latest(siteId) as site latest(deviceType) as type latest(managementIpAddress) as ip by deviceName
| where isnull(site) OR site="" OR match(site, "^[0-9a-f-]{36}$")
| lookup catalyst_site_lookup siteId as site OUTPUT siteName
| where isnull(siteName) OR siteName="Global"
| table deviceName, ip, type, health, site
```

## Visualization

(1) Table: orphaned devices with deviceName, IP, type, health — these need site assignment. (2) Single value: count of unassigned devices (yellow ≥ 1, red ≥ 10). (3) Pie: orphaned devices by deviceType to see which families are most commonly unassigned.

## Known False Positives

**Newly discovered devices pending site assignment.** Devices recently discovered by Catalyst Center haven't been assigned to a site yet. Distinguish by checking device discovery time (if available) — devices discovered within the last 48 hours are in the onboarding pipeline. Suppress by allowing a 48-hour grace period.

**Virtual appliances or cloud-managed devices that don't have physical sites.** Some devices in Catalyst Center inventory (virtual routers, cloud controllers) may not belong to a physical site. Distinguish by checking `deviceType` for virtual device indicators. Suppress by maintaining a `virtual_devices` lookup and excluding them.

**Devices intentionally kept in the Global site for management purposes.** Some organisations keep infrastructure devices (Catalyst Center appliance itself, WLC management interfaces) in the Global site by design. Distinguish by checking with the network architecture team. Suppress by adding these to a `catalyst_global_exceptions` lookup.

**Root siteId UUID matching the regex but representing a valid site.** The UUID regex `^[0-9a-f-]{36}$` may match a real site that just hasn't been resolved by the lookup. Distinguish by checking whether the UUID exists in `catalyst_site_lookup`. If it does, the device IS assigned — the search logic needs adjustment.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Device Provisioning — Cisco Docs](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/provision-guide.html)
