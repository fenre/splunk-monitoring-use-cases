<!-- AUTO-GENERATED from UC-5.13.52.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538) with **site topology** in `index=catalyst`, sourcetype `cisco:dnac:site:topology` (Intent API `GET /dna/intent/api/v1/topology/site-topology`).
• A Catalyst Center design owner who maintains the site hierarchy; Splunk only mirrors what Catalyst Center publishes.
• For app install paths and modular input layout, see `docs/implementation-guide.md`.

Step 1 — Configure data collection
• **TA input name:** `site_topology` (or the stanza your version exposes under **Data inputs**); destination index `catalyst`, assigned sourcetype `cisco:dnac:site:topology`.
• **Default interval:** **3600 seconds (1 hour)** is common for topology; structure changes are infrequent, so avoid over-polling without reason.
• **Key fields:** `siteId`, `siteName`, `parentSiteName`, `siteType` (for example area, building, floor — values follow your design).

Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats earliest(_time) as first_seen latest(_time) as last_seen values(siteType) as types by siteId, siteName, parentSiteName | where first_seen > relative_time(now(), "-7d") | eval change_type="New site added" | sort -first_seen
```

Understanding this SPL

**Site Topology Change Detection** — Flags `siteId` keys whose **first** observation in the index fell within the lookback, which usually means a newly modeled site in Catalyst Center (or new data in Splunk).
• **7-day window:** shorten for stricter change control, or lengthen if your topology input runs less than daily. This pattern does not detect renames or deletes; add summary indexing or CMDB diff if you need those.
• **`stats` per siteId, siteName, parentSiteName** — if hostnames or parents change, you may get a “new” row; correlate with **Catalyst Center > Network > Sites**.

**Pipeline walkthrough**
• `earliest(_time)` / `latest(_time)` bound first and last see times per site key; `values(siteType)` helps validate expected types per site.
• `change_type` is a static label; extend with `case()` if you add logic for renames (compare prior lookup).

Step 3 — Validate
• Compare the result set to **Catalyst Center > Network > Sites** for the same week; allow up to one poll interval of lag from the topology modular input.
• Run `| stats count by siteType` to ensure floor/building/area mix matches your design standards.

Step 4 — Operationalize
• Schedule or alert for non-empty results; send to the team that owns site hierarchy and policy assignment.
• Optional: join `siteId` to device and AP dashboards so new sites are visible to NOC the same day they appear.

Step 5 — Troubleshooting
• **No `cisco:dnac:site:topology` events:** enable the `site_topology` input, check Catalyst Center base URL and credentials, and search `splunkd.log` for modular input errors on the collection tier.
• **Surge of “new” sites after Splunk maintenance:** `first_seen` is index-time; a re-ingest of historical files can look like a topology explosion — cross-check actual Catalyst Center UI before treating as a change wave.
• **False “new” site for renamed site:** a rename often creates a new `siteId`; treat as a data modeling change, not a physical build.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats earliest(_time) as first_seen latest(_time) as last_seen values(siteType) as types by siteId, siteName, parentSiteName | where first_seen > relative_time(now(), "-7d") | eval change_type="New site added" | sort -first_seen
```

## Visualization

Table (siteName, parentSiteName, first_seen, change_type, types), alert when new `siteId` row appears, optional comparison dashboard against CMDB site list.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
