<!-- AUTO-GENERATED from UC-5.13.52.json — DO NOT EDIT -->

---
id: "5.13.52"
title: "Site Topology Change Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.52 · Site Topology Change Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for changes to the map of your offices, buildings, and campuses — new locations being added, existing ones being renamed or reorganised. When the map changes, we update all the dashboards and reports that use it so nothing breaks and no building gets lost in the system.*

---

## Description

Detects changes to the Catalyst Center site hierarchy — new areas, buildings, and floors being added; sites being renamed or reorganised — that may affect device assignment, policy application, and reporting groupings across all site-based UCs in the Catalyst Center family.

## Value

Site hierarchy changes ripple through every location-based dashboard and alert. A new building added without updating the `catalyst_site_lookup` means UC-5.13.5 (Device Health by Site) shows a UUID instead of a name. A site renamed breaks dashboard labels. A site moved to a different area changes which regional team is responsible for the devices inside it. This UC catches all hierarchy changes within 24 hours so downstream configurations stay aligned — and for compliance, it documents when the managed-infrastructure footprint changed.

## Implementation

Same `site_topology` input as UC-5.13.51. The SPL detects new sites by checking `earliest(_time)` within the last 7 days. For rename and deletion detection, use the variant searches in Step 2. Schedule daily for operations review.

## Detailed Implementation

### Prerequisites
- UC-5.13.51 (Site Hierarchy Inventory) must be operational — same `site_topology` data feed.
- The `catalyst_site_lookup` (built in UC-5.13.51) should be in place so that change detection can trigger a lookup refresh.
- At least **7 days** of historical site topology data to distinguish 'new' sites from the initial data load.

### Step 1 — Configure data collection
Same `site_topology` input as UC-5.13.51. No additional configuration.

### Step 2 — Create the search and report
New site detection:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| where first_seen > relative_time(now(), "-7d")
| eval change_type="New site added"
| sort -first_seen
```

Site rename detection:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-14d latest=-7d
| stats latest(siteName) as old_name by siteId
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-1d | stats latest(siteName) as new_name by siteId]
| where isnotnull(new_name) AND old_name != new_name
| eval change_type="Renamed: ".old_name." → ".new_name
```

Site deletion detection:
```spl
| inputlookup catalyst_site_lookup
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-2d | stats latest(siteName) as current_name by siteId]
| where isnull(current_name)
| eval change_type="DELETED — no longer in Catalyst Center"
```

Why `earliest(_time) > relative_time(now(), "-7d")` for new sites: a site whose first appearance in Splunk was within the last 7 days was recently added to the Catalyst Center hierarchy.

Schedule: daily (cron `0 7 * * *`). When changes are detected, trigger a `catalyst_site_lookup` refresh.

### Step 3 — Validate
(a) Create a test floor in Catalyst Center under an existing building. Within 1 hour, the new-site search should detect it.
(b) Rename a test site in Catalyst Center. The rename search should detect the change.
(c) Verify the deletion search correctly identifies sites that exist in the lookup but no longer appear in the data.
(d) Cross-reference with **Catalyst Center > Design > Network Hierarchy** change log (if available).

### Step 4 — Operationalize
- Daily check: review new/renamed/deleted sites.
- When a new site is detected: regenerate the `catalyst_site_lookup` (UC-5.13.51 Step 2). Update any hardcoded site references in dashboards.
- When a site is deleted: check whether devices were reassigned or decommissioned.
- Document hierarchy changes for compliance (infrastructure footprint changes).

### Step 5 — Troubleshooting

- **All sites appear as 'new'** — insufficient historical data. The `site_topology` input needs 7+ days of history before new-site detection is meaningful.

- **Rename detection produces false positives** — the time windows for 'old' and 'new' snapshots may not align perfectly. Adjust the `earliest`/`latest` boundaries.

- **Deletion detection shows false positives** — the `catalyst_site_lookup` contains stale entries. Regenerate the lookup.

- **No changes detected but hierarchy was modified** — the `site_topology` input poll interval (1 hour) means changes are detected within 1 hour. If the change was made and reverted within the same hour, it may not be captured.

- **Site metadata changed but `siteId` is stable** — `siteId` (UUID) never changes for a given site. Only names and parent assignments change. Track by `siteId` for stable identification.

- **Want to track which devices moved between sites** — join site changes with `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(siteId) as current_site by deviceName` over two time periods.

- **Too many floor additions cluttering the report** — filter `| where siteType IN ("area","building")` for building-level changes only.

- **Hierarchy change broke a dashboard** — dashboards that use hardcoded `siteId` or `siteName` values may break after renames. Use the `catalyst_site_lookup` with `coalesce()` fallback instead of hardcoded values.

For automated lookup refresh on hierarchy change:
```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| where first_seen > relative_time(now(), "-24h")
| outputlookup append=true catalyst_site_changes_log
```
Schedule daily. Each new site triggers a lookup refresh and a notification to the network architecture team.

For deletion detection with CMDB reconciliation:
```spl
| inputlookup catalyst_site_lookup
| join type=left siteId [search index=catalyst sourcetype="cisco:dnac:site:topology" earliest=-2d | stats latest(siteName) as current_name by siteId]
| where isnull(current_name)
| lookup cmdb_sites siteId OUTPUT cmdb_status
| eval action=case(cmdb_status="decommissioned", "Expected — site decommissioned", cmdb_status="active", "UNEXPECTED — site missing from Catalyst Center", 1==1, "Unknown — not in CMDB")
| table siteId, siteName, action
```

Capacity planning integration:
- Track `dc(siteId)` over time: `| timechart span=1w dc(siteId) as total_sites`. Growing site count indicates organisational expansion that requires proportional network investment.
- Compare site growth rate with device growth rate (UC-5.13.54). Sites growing faster than devices = new locations not yet provisioned.

Runbook expansion:
1. New site detected: verify it was intentionally created. Update `catalyst_site_lookup` (UC-5.13.51). Check if devices have been assigned.
2. Site renamed: update all hardcoded site references in dashboards, lookups, and tokens. The `siteId` UUID doesn't change — only the display name.
3. Site deleted: verify all devices were reassigned or decommissioned before the site was removed. Archive the site's historical data for compliance.
4. Hierarchy reorganisation: when an area is restructured, all child buildings move to new parents. Track with `parentSiteName` changes. Update regional team assignments.
5. Floor additions: new floors in existing buildings indicate expansion. Verify AP and switch provisioning for the new floor.

Troubleshooting expansion:
- **Rename detection produces stale results** — the 7-day comparison window may include old renames that were already documented. Narrow to `-2d` for recent changes only.
- **CMDB reconciliation shows many 'Unknown'** — the `cmdb_sites` lookup is incomplete. Work with the facilities team to populate it.
- **Want to track who made hierarchy changes** — correlate with `index=catalyst sourcetype="cisco:dnac:audit:logs" auditDescription="*site*" OR auditDescription="*hierarchy*"`.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(siteName) as name latest(siteType) as type latest(parentSiteName) as parent by siteId
| where first_seen > relative_time(now(), "-7d")
| eval change_type="New site added"
| sort -first_seen
```

## Visualization

(1) Table: siteId, name, type, parent, first_seen, change_type. (2) Alert: new site detected → update `catalyst_site_lookup`. (3) Timeline: site additions/changes over 30 days. (4) Comparison table for deletions: sites in the lookup that no longer appear in the data.

## Known False Positives

**Initial data load appearing as many new sites.** When the `site_topology` input is first enabled, all sites appear as 'new' because they have no history in Splunk. Distinguish by checking whether all sites have `first_seen` within the same hour. Suppress by establishing a baseline period (7+ days) before enabling change alerting.

**Site hierarchy reorganisation creating many simultaneous changes.** A planned hierarchy restructure (merging areas, renaming buildings) generates many changes at once. Distinguish by correlating with ITSM change records. Document as an approved batch change.

**Floor additions during building expansion.** Adding floors to an existing building creates new site entries that are operationally expected. Distinguish by checking `siteType=floor` and `parentSiteName` matching an existing building. These are growth events, not anomalies.

**Catalyst Center upgrade changing site metadata format.** Some upgrades may change how site attributes are stored, causing apparent changes without actual hierarchy modifications. Distinguish by checking whether `siteId` values are stable (UUIDs don't change) even if attribute formatting changed.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Network Hierarchy — Cisco Docs](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/design-guide.html)
