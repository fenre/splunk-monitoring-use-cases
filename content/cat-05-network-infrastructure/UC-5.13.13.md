<!-- AUTO-GENERATED from UC-5.13.13.json — DO NOT EDIT -->

---
id: "5.13.13"
title: "Client Health by Site"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.13 · Client Health by Site

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We rank every building and campus by how good the network experience is for the people inside. The buildings with the most connectivity problems show up at the top, so your team knows which location needs attention — whether that means sending someone to fix the Wi-Fi, upgrade a switch, or call the building electrician.*

---

## Description

Ranks Catalyst Center sites by client experience quality — showing which buildings and campuses have the highest concentration of users with poor connectivity, so operations can prioritise site-specific remediation (AP placement, DHCP scope, cabling) over fleet-wide changes that may not address localised problems.

## Value

UC-5.13.12 tells you which SSID is the problem; this UC tells you *where*. A corporate SSID with 75% healthy clients campus-wide may hide the fact that Building A is at 90% while Building C is at 40% — because Building C had a renovation that introduced RF-blocking walls. Without the site split, you'd optimise RRM globally when you only need to add APs in one building. The ranked list also identifies sites for proactive Wi-Fi surveys before users complain, and tracks whether a site-specific remediation (AP install, switch upgrade) actually improved the user experience at that location.

## Implementation

Requires the `client` detail input (same as UC-5.13.12). For human-readable site names, use the `catalyst_site_lookup` from UC-5.13.5 or UC-5.13.51. Schedule as a weekly report for regional operations teams.

## Detailed Implementation

### Prerequisites
- UC-5.13.9 (Client Health Overview) and UC-5.13.12 (Client Health by SSID) should be operational for context.
- Requires the `client` detail input — same high-volume feed as UC-5.13.12 (~1 event per client per poll). Ensure license/volume capacity: 500 clients ≈ 37 MB/day, 2,000 clients ≈ 150 MB/day.
- `siteId` must be populated in client events. Run `index=catalyst sourcetype="cisco:dnac:client" earliest=-1h | stats count(eval(isnull(siteId))) as null_sites, count as total`. If `null_sites` is significant, some clients have no site assignment — they'll be grouped under a null bucket.
- For site name resolution, use the `catalyst_site_lookup` from UC-5.13.5 or UC-5.13.51.
- Service account with **NETWORK-ADMIN-ROLE** for client detail data.

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.12. No additional configuration. Confirm per-client data includes `siteId`:
```spl
index=catalyst sourcetype="cisco:dnac:client" earliest=-30m
| stats dc(siteId) as sites, dc(macAddress) as clients
```
If `sites = 0`, the `siteId` field may not be populated for clients — check the TA version and client API endpoint configuration.

For site name resolution, ensure the `catalyst_site_lookup` is populated:
```spl
| inputlookup catalyst_site_lookup | stats count
```
If count = 0, build it from UC-5.13.51's `outputlookup` search.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client"
| stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count count(eval(healthScore{}.score<50)) as poor_clients by siteId
| eval poor_pct=round(poor_clients*100/client_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -poor_pct
| head 20
```

Why `count(eval(healthScore{}.score<50))` as the ranking metric: `avg_health` can be misleading — a site with 99 healthy clients and 1 critically unhealthy client averages 98. `poor_pct` surfaces sites with the highest *concentration* of bad experiences, regardless of total population.

Why `dc(macAddress)` not `count`: within the search window, each client produces multiple events (one per poll cycle). `dc(macAddress)` gives the unique client count per site. `count` would inflate with poll frequency.

Why include both wired and wireless (no `connectionType` filter): site-level client health should capture the full user experience. If you need wireless-only, add `| where connectionType="WIRELESS"`. For a split view, add `connectionType` to the `by` clause.

Why `coalesce(siteName, siteId)`: if the lookup doesn't contain a particular siteId (new site not yet in the lookup), fall back to the UUID so the site still appears in results. A missing name is better than a missing row.

Why `head 20`: in a large enterprise with 100+ sites, the full list is overwhelming. The top-20 ranked by `poor_pct` focuses attention on the worst sites. For the full list, remove `| head 20` and export as CSV for the facilities team.

For wireless-only per-site analysis:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count count(eval(healthScore{}.score<50)) as poor_clients by siteId
| eval poor_pct=round(poor_clients*100/client_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -poor_pct
| head 20
```

For combined device + client health per site (most comprehensive):
```spl
index=catalyst sourcetype="cisco:dnac:client"
| stats avg(healthScore{}.score) as client_health dc(macAddress) as clients by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as device_health dc(deviceName) as devices by siteId]
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval combined_health=round((client_health*0.6 + device_health*0.4),1)
| sort combined_health
| head 20
```

Schedule as Report: weekly (cron `0 7 * * 1`), output to PDF for the regional operations meeting.

### Step 3 — Validate
(a) Run the search and sum `client_count` across all rows. Compare with `| stats dc(macAddress)` on the raw data. They should match (minus any clients with null `siteId`).

(b) Pick the worst site from the results. Drill in: `index=catalyst sourcetype="cisco:dnac:client" siteId="<that-id>" | where healthScore{}.score < 50 | stats dc(macAddress) as poor by ssid`. This shows which SSIDs are contributing to the poor health at that site.

(c) Cross-reference with UC-5.13.5 (Device Health by Site) — do the worst sites for client health also have the worst device health? If yes → infrastructure problem. If device health is fine but client health is poor → wireless/DHCP/DNS issue.

(d) Verify site name resolution: all `site_label` values should be building names, not UUIDs. If all are UUIDs, regenerate the `catalyst_site_lookup` per UC-5.13.51.

(e) Vendor UI parity: open **Catalyst Center > Assurance > Health > Client Health** and compare the per-site client health view with the Splunk results. Directional agreement is expected; exact parity depends on aggregation method differences.

(f) Check for the null-site bucket: `| stats count(eval(isnull(siteId))) as null_site_clients`. If significant, these clients are excluded from all site-based analysis — assign them to sites in Catalyst Center.

### Step 4 — Operationalize
Dashboard placement (on the "Client Experience" dashboard, below UC-5.13.12's SSID table):
- Bar chart: top 20 sites by `poor_pct`, colour-coded red/yellow/green.
- Table with drilldown: click a site → filter UC-5.13.12 (by SSID at that site) and UC-5.13.42 (RSSI/SNR at that site) to isolate the root cause.
- Token-driven filter: add a site dropdown populated by `| inputlookup catalyst_site_lookup | stats count by siteName | sort -count` so engineers can focus on one site at a time.

Runbook (owner: Regional Operations):
1. Identify the site with the highest `poor_pct`.
2. Cross-reference with UC-5.13.5 (Device Health by Site): is device health also poor at this site? If yes → infrastructure problem (power, cabling, switch health). If device health is fine → client/wireless problem.
3. Check UC-5.13.12 filtered by this site: is the problem on one SSID or all SSIDs?
   - One SSID: suspect SSID-specific issue (RADIUS policy, VLAN, QoS). Escalate to the wireless or identity team.
   - All SSIDs: suspect shared infrastructure (DHCP server, DNS, upstream switch, or RF coverage).
4. Check UC-5.13.42 (RSSI/SNR) filtered by this site: is signal quality poor?
   - Poor RSSI → schedule a wireless site survey. AP placement, power, or antenna orientation may need adjustment.
   - Good RSSI but poor health → check DHCP, DNS, RADIUS response times.
5. If the problem is widespread across multiple sites: suspect centralised infrastructure (DHCP server, RADIUS server, DNS). Escalate to the infrastructure team.
6. Track site rankings month-over-month. Sites consistently in the bottom 5 are candidates for infrastructure investment (AP refresh, switch upgrade, cabling improvement).

Capacity review (monthly, owner: Network Architecture):
- Compare client count per site with building headcount. Sites where client_count >> headcount may have IoT proliferation. Sites where client_count << headcount may have Wi-Fi coverage gaps driving users to mobile data.
- Track per-site client growth: `| timechart span=1w dc(macAddress) by siteId`. Growing sites need capacity planning.

### Step 5 — Troubleshooting

- **All clients grouped under one siteId** — site hierarchy is flat (everything under Global). Fix in Catalyst Center by creating a proper Area > Building > Floor hierarchy and assigning devices/APs to sites. Clients inherit their site from the AP they're connected to.

- **Site names show as UUIDs** — the `catalyst_site_lookup` is empty or stale. Regenerate per UC-5.13.51 Step 1: `index=catalyst sourcetype="cisco:dnac:site:topology" | stats latest(siteName) as siteName by siteId | outputlookup catalyst_site_lookup`.

- **`healthScore{}.score` is null for many clients** — the nested health score path may differ in your TA version. Run `| head 1 | spath` on a raw client event and search for any field containing "health" and "score" to find the correct path. Common variants: `healthScore{}.score`, `healthScore.score`, `health_score`.

- **Client count at a site doesn't match physical headcount** — not all employees connect to the corporate network; some use mobile data, and contractors may use a different SSID. The client count is the *connected* population, not the *employee* population. Also, MAC randomisation inflates wireless client counts (see UC-5.13.40).

- **Search is very slow** — the `client` sourcetype is high-volume (1 event per client per poll). Narrow to `earliest=-20m` for a snapshot. For weekly reports over longer ranges, use summary indexing: schedule a daily `| stats avg(healthScore{}.score) as health dc(macAddress) as clients by siteId | collect index=catalyst_summary sourcetype=site_client_health` and query the summary for trending.

- **One site dominates the chart with very high client count** — headquarters or main campus. Consider normalising by showing `poor_pct` rather than absolute `poor_clients` count. Already handled by the default sort on `poor_pct`.

- **Wireless and wired mixed in one number** — add `connectionType` to the `by` clause for separate wired/wireless analysis per site. Wireless problems and wired problems have different root causes and different remediation teams.

- **Poor_pct seems too low even when users complain** — the health score threshold of < 50 for "poor" is conservative. Lower to < 60 for a more sensitive view: `count(eval(healthScore{}.score<60)) as poor_clients`.

- **Same site appears in the bottom 5 every week for months** — this is the intended signal. The site has a chronic problem that needs investment, not just alerting. Escalate to network architecture for a design review.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client"
| stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count count(eval(healthScore{}.score<50)) as poor_clients by siteId
| eval poor_pct=round(poor_clients*100/client_count,1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -poor_pct
| head 20
```

## Visualization

(1) Table: site_label, client_count, avg_health, poor_clients, poor_pct — sorted worst-first. Drilldown to UC-5.13.12 filtered by `siteId`. (2) Bar chart: poor_pct by site, red/yellow/green colour coding. (3) Optional choropleth or tile map if geo-coordinates are available per site. (4) Trellis sparklines: one per top-10 site showing avg_health over 7 days for trend context.

## Known False Positives

**Small-population sites with volatile percentages.** A branch office with 5 connected clients where 1 is unhealthy shows 20% poor — alarming but representing a single device. Distinguish by checking `client_count`. Suppress by filtering `| where client_count >= 20` for the ranked chart.

**Conference/event venues with temporary client surges.** A convention centre or auditorium may show poor client health during events due to density and device diversity, then recover to near-100% when empty. Distinguish by checking whether `client_count` spiked in the same window. Suppress by using time-of-day-aware baselines for event venues.

**Overnight shift sites with different baselines.** A 24/7 data centre has fundamentally different usage patterns than a 9-to-5 office. Comparing them in the same ranked list is misleading. Suppress by adding a `site_category` column from a lookup (office/DC/retail/warehouse) and comparing within categories.

**Site hierarchy reorganisation shifting clients between siteIds.** Same issue as UC-5.13.5 — a hierarchy change can make one site appear to improve while another degrades. Distinguish by tracking `dc(macAddress)` per site over time.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
