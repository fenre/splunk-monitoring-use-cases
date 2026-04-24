---
id: "5.13.52"
title: "Site Topology Change Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.52 · Site Topology Change Detection

## Description

Detects changes to the Catalyst Center site hierarchy — new sites, modified sites, or removed sites — that may require configuration updates.

## Value

Site hierarchy changes affect device assignment, policy application, and reporting groupings. Detecting them ensures downstream configurations stay aligned.

## Implementation

Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls site hierarchy data from the Catalyst Center Intent API every 60 minutes. Key fields: `siteId`, `siteType` (area, building, floor), `parentSiteName`, `siteName`. Pair with a longer baseline window if you need to diff deletes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:site:topology (Catalyst Center site data with siteId, siteName, parentSiteName, siteType, _time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls site hierarchy data from the Catalyst Center Intent API every 60 minutes. Key fields: `siteId`, `siteType` (area, building, floor), `parentSiteName`, `siteName`. Pair with a longer baseline window if you need to diff deletes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats earliest(_time) as first_seen latest(_time) as last_seen values(siteType) as types by siteId, siteName, parentSiteName | where first_seen > relative_time(now(), "-7d") | eval change_type="New site added" | sort -first_seen
```

Understanding this SPL

**Site Topology Change Detection** — Site hierarchy changes affect device assignment, policy application, and reporting groupings. Detecting them ensures downstream configurations stay aligned.

**Pipeline walkthrough**

• `stats` collapses to one row per `siteId`, `siteName`, and `parentSiteName`, keeping earliest and latest observation times and `siteType` multivalues when they vary.
• `where first_seen > relative_time(now(), "-7d")` approximates new sites that first appeared in the last seven days; adjust the lookback to match your change window.
• `eval change_type` labels the finding for dashboards; expand this pattern to compare with previous week snapshots to detect renames or removals if you add summary indexing.
• `sort -first_seen` lists the newest first for review with change management.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (siteName, parentSiteName, first_seen, change_type, types), alert when new `siteId` row appears, optional comparison dashboard against CMDB site list.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats earliest(_time) as first_seen latest(_time) as last_seen values(siteType) as types by siteId, siteName, parentSiteName | where first_seen > relative_time(now(), "-7d") | eval change_type="New site added" | sort -first_seen
```

## Visualization

Table (siteName, parentSiteName, first_seen, change_type, types), alert when new `siteId` row appears, optional comparison dashboard against CMDB site list.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
