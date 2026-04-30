<!-- AUTO-GENERATED from UC-5.13.70.json — DO NOT EDIT -->

---
id: "5.13.70"
title: "Catalyst Center + Meraki Branch Network Health"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.70 · Catalyst Center + Meraki Branch Network Health

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We combine the health scores from two different network management systems — the campus network (Catalyst Center) and the branch network (Meraki) — into a single view per building. This shows your team the full picture instead of checking two separate dashboards and hoping someone notices when both say different things about the same location.*

---

## Description

Compares Catalyst Center campus network health with Meraki branch network health to identify divergence between campus and branch office performance.

## Value

Many organizations use Catalyst Center for campus and Meraki for branches. Comparing both reveals whether network problems are campus-specific, branch-specific, or universal.

## Implementation

Deploy **Cisco Catalyst Add-on (7538)** for `cisco:dnac:networkhealth` on `index=catalyst` and **Cisco Meraki Add-on (5580)** for organization API data as `sourcetype=meraki:api` (commonly `index=cisco_network` or your org standard).

1. **Meraki API:** In the Meraki TA, add an org API key and enable the inputs that produce device/network health and status (health or summary endpoints per TA version).
2. **Field names:** The SPL uses `health_score` and `status` on Meraki events — if your field names differ (`uplinkStatus`, `device status`), map them with `eval` before `stats`.
3. **Time sync:** `appendcols` is row-aligned; for production, bin `_time` on both sides to the same span (e.g. 5m) or use a **join** on discrete `_time` buckets.
4. **Thresholds:** Adjust `15` to match the noise floor for your environment.

## Detailed Implementation

### Prerequisites
- UC-5.13.16 (Network Health Score Overview) and UC-5.13.1 (Device Health) must be operational for the Catalyst Center campus health dimension.
- **Meraki Dashboard API integration** must be configured separately — either via the Cisco Meraki Add-on for Splunk or a custom REST API input polling `GET /api/v1/organizations/{orgId}/networks/{networkId}/health`. Meraki data typically lands in `index=meraki` with sourcetypes like `meraki:api:networks` or `meraki:api:devices`.
- **Join field**: the correlation between Catalyst Center and Meraki is based on site/location matching — there is no shared device ID. You need a `site_to_meraki_network` lookup that maps Catalyst Center `siteId` to Meraki `networkId` or `networkName`. This lookup is manually curated because Catalyst Center and Meraki have independent site hierarchies.
- This is a **run-tier** cross-product UC that requires both Catalyst Center AND Meraki data flowing in Splunk. It provides the unified site health view that neither platform can produce alone.

### Step 1 — Configure data collection
Catalyst Center: same `networkhealth` and `devicehealth` inputs as UC-5.13.1/UC-5.13.16.

Meraki: configure the Meraki integration to poll network health data. The Meraki Dashboard API provides:
- `GET /api/v1/networks/{networkId}/health/alerts` — health alerts per network
- `GET /api/v1/organizations/{orgId}/devices/statuses` — device online/offline status
- `GET /api/v1/organizations/{orgId}/uplinks/statuses` — WAN uplink health

Ensure both data sources are indexed and searchable:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | stats count as catalyst_events
| appendcols [search index=meraki earliest=-1h | stats count as meraki_events]
```

Build the site-to-network mapping lookup:
```
siteId,siteName,meraki_networkId,meraki_networkName
a1b2c3-uuid,Branch-NYC,N_12345,NYC-Branch-Meraki
d4e5f6-uuid,Branch-LON,N_67890,LON-Branch-Meraki
```
Upload as `lookups/site_to_meraki_network.csv`.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as catalyst_health dc(deviceName) as catalyst_devices by siteId
| lookup site_to_meraki_network siteId OUTPUT meraki_networkId, meraki_networkName
| where isnotnull(meraki_networkId)
| join type=left meraki_networkId
    [search index=meraki sourcetype="meraki:api:*"
     | stats avg(health_score) as meraki_health dc(serial) as meraki_devices by networkId
     | rename networkId as meraki_networkId]
| eval combined_health=round((catalyst_health*0.5 + coalesce(meraki_health,catalyst_health)*0.5),1)
| lookup catalyst_site_lookup siteId OUTPUT siteName
| table siteName, catalyst_health, catalyst_devices, meraki_health, meraki_devices, combined_health
| sort combined_health
```

Why a combined health score: sites with both Catalyst Center-managed campus infrastructure AND Meraki cloud-managed branches need a unified health view. A site where the Catalyst Center campus scores 90 but the Meraki branch scores 40 has a problem that neither platform shows in isolation. The 50/50 weighting is a starting point — adjust based on which infrastructure carries more user traffic at each site.

Why `join type=left`: keeps sites that have Catalyst Center data even if Meraki data is missing (the Catalyst Center campus may not have a corresponding Meraki network). `coalesce(meraki_health, catalyst_health)` falls back to Catalyst-only health when Meraki data is absent.

Why the lookup-based correlation: Catalyst Center and Meraki have completely independent device inventories, site hierarchies, and health scoring algorithms. There is no automatic join key — the `site_to_meraki_network` lookup is the bridge, curated by the network architecture team who knows which physical locations have both Catalyst and Meraki infrastructure.

Schedule: weekly (cron `0 7 * * 1`), output to the Multi-Domain dashboard.

### Step 3 — Validate
(a) Pick a site that has both Catalyst and Meraki infrastructure. Verify `catalyst_health` matches UC-5.13.1 for that site and `meraki_health` matches the Meraki Dashboard health view for the corresponding network.

(b) Confirm the `site_to_meraki_network` lookup correctly maps physical locations. A mismatch here produces misleading combined health scores.

(c) Check for sites with Catalyst data but no Meraki data (expected for campus-only sites) and vice versa. The `join type=left` should handle both gracefully.

(d) Compare the combined health ranking with each individual platform's ranking. Sites that rank poorly on both dimensions are the highest-priority remediation targets.

(e) Vendor UI parity: open both **Catalyst Center > Assurance > Health** and **Meraki Dashboard > Network-wide > Clients** for the same site. The individual scores should correlate with the Splunk values.

### Step 4 — Operationalize
- Multi-domain dashboard: unified site health table showing both Catalyst and Meraki dimensions side by side.
- The sites with the lowest `combined_health` are the priority targets for cross-domain investigation.
- When `catalyst_health` is high but `meraki_health` is low: the problem is in the Meraki branch (WAN uplink, AP, switch). Investigate in the Meraki Dashboard.
- When `catalyst_health` is low but `meraki_health` is high: the problem is in the Catalyst campus infrastructure. Investigate with UC-5.13.1.
- When both are low: systemic site-level issue (power, ISP, building infrastructure). Contact facilities.

Runbook (owner: Network Architecture):
1. Review the weekly multi-domain health table.
2. For sites with low combined health: determine which platform is contributing to the degradation.
3. Route Catalyst issues to the campus network team; route Meraki issues to the cloud-managed network team.
4. For sites with both platforms degraded: investigate shared infrastructure (ISP link, DNS, DHCP).
5. Track combined health month-over-month for capacity planning.

### Step 5 — Troubleshooting

- **No Meraki data** — the Meraki integration is not configured. Set up the Meraki Add-on or custom REST input.

- **`site_to_meraki_network` lookup is empty** — create it manually by mapping physical locations to Meraki network IDs.

- **Join produces no results** — the `meraki_networkId` field name may differ. Check `| head 1` on both data sources for the exact field names.

- **Combined health seems wrong** — check the individual scores. If `catalyst_health=90` and `meraki_health=0`, the combined=45. Verify that `meraki_health=0` is real (total Meraki outage) vs a data issue.

- **Meraki health scoring differs from Catalyst** — expected. Meraki and Catalyst Center use different algorithms to compute health. The combined score is an approximation, not an exact metric. Use it for relative ranking, not absolute thresholds.

- **Want to add SD-WAN or ThousandEyes** — extend the pattern: add another `join` or `appendcols` with the additional data source. See UC-5.13.69 (SD-WAN) and UC-5.13.71 (ThousandEyes) for those specific correlations.

- **Site-to-network mapping changes** — update the lookup when new sites are added or Meraki networks are reorganised. Schedule a quarterly review of the lookup accuracy.

- **Performance** — the `join` command can be expensive with large datasets. Pre-aggregate each data source to one row per site before joining.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health by _time | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health count(eval(status="offline")) as offline_branches by _time] | eval campus_vs_branch=campus_health-branch_health | where abs(campus_vs_branch) > 15 | table _time campus_health branch_health offline_branches campus_vs_branch
```

## Visualization

Dual-axis line: campus_health vs branch_health; table when `abs(campus_vs_branch) > 15`; optional single value for `offline_branches` with a threshold.

## Known False Positives

**Meraki cloud connectivity issue causing stale Meraki health data while campus data is current.** If the Meraki dashboard API is slow or unavailable, the Meraki health data in Splunk may be stale while Catalyst Center data is fresh. Distinguish by comparing the latest `_time` from both sourcetypes. Suppress by alerting when the Meraki data staleness exceeds 2x the expected poll interval.

**Different health score scales between Catalyst Center and Meraki.** Catalyst Center uses 0-100 while Meraki may use a different scale or calculation method. A direct numeric comparison may not be meaningful. Distinguish by checking the health score normalization — if Meraki scores cluster around 80-100 while campus scores cluster around 60-80, the scales may not be comparable. Suppress by normalizing both scores to percentile rank within their own distribution before comparing.

**Branch site maintenance causing Meraki health drop for one location while campus is stable.** A single branch office undergoing renovation or equipment replacement will lower the Meraki average. Distinguish by checking whether the Meraki health drop is localized to one network or site. Do not suppress — enrich the alert with the specific branch context.

**Meraki API rate limiting causing incomplete health data.** The Meraki Dashboard API has rate limits that may prevent the TA from collecting health data for all organizations/networks in a single poll. Distinguish by checking `index=_internal` for Meraki TA errors related to HTTP 429 rate limiting. Suppress by increasing the Meraki poll interval or splitting organizations across multiple inputs.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco Meraki Add-on (Splunkbase 5580)](https://splunkbase.splunk.com/app/5580)
- [Catalyst Center Network Health API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
