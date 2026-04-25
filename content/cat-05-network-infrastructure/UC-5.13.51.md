<!-- AUTO-GENERATED from UC-5.13.51.json — DO NOT EDIT -->

---
id: "5.13.51"
title: "Site Hierarchy Inventory"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.51 · Site Hierarchy Inventory

## Description

Provides a complete inventory of the Catalyst Center site hierarchy (areas, buildings, floors) for infrastructure documentation and capacity planning.

## Value

Understanding the site hierarchy is foundational for location-based analytics. This inventory ensures Splunk has a complete map of the physical infrastructure.

## Implementation

Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA calls `GET /dna/intent/api/v1/topology/site-topology` on a **3600s** (1 hour) default interval. Key fields: `siteId`, `siteType`, `siteName`, `parentSiteName`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538); **site topology** in `index=catalyst`, sourcetype `cisco:dnac:site:topology` (Intent API `GET /dna/intent/api/v1/topology/site-topology`).
• A Catalyst Center design or NOC owner who keeps the **hierarchy** in Catalyst current; Splunk is read-only, so fixes to parents and names are done in the controller first.
• When you onboard buildings or run renovations, reflect that in **Network > Sites** the same week and re-run this search to confirm Splunk matches.
• For TA location and `inputs.conf` patterns, see `docs/implementation-guide.md`.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/topology/site-topology` — confirm the exact path in the API reference for your Catalyst Center release; minor version differences can namespace endpoints.
• **TA input:** `site_topology` in the add-on; destination index `catalyst`, assigned sourcetype `cisco:dnac:site:topology`.
• **Default interval:** 3600 seconds (1 hour) is typical; hierarchy changes are infrequent, so avoid a shorter poll unless you have a business reason and headroom on API rate limits.
• **Key fields:** `siteId`, `siteType` (for example area, building, or floor; values follow your design), `siteName`, `parentSiteName`.

Step 2 — Create the search and report

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(siteId) as total_sites values(siteType) as types by parentSiteName | sort parentSiteName
```

Understanding this SPL
• Rolling up by `parentSiteName` matches how many teams navigate Catalyst Center. If you nest several levels (region, campus, building), add a second panel that breaks out `by siteName` for leaf sites only.
• `values(siteType)` is a sanity list of what appeared under a parent, not a compliance count; a single parent can host many child site types at once.

**Pipeline walkthrough**
• `stats` deduplicates by `siteId` under each `parentSiteName` and orders rows for a drilldown that matches the Catalyst UI’s site tree.

Step 3 — Validate
• In Catalyst, open **Network > Sites** and compare `siteName` and `parentSiteName` to the Splunk table for the last poll, allowing up to one poll cycle of delay.
• If `total_sites` is zero for a parent you expect, run `| stats count by siteName` in a broad search to see if sites were moved under a new regional parent.

Step 4 — Operationalize
• Use an indented table in a “Campus & sites” dashboard; export CSV to Confluence or the CMDB so on-call runbooks use the same site names as Catalyst.
• Rebuild a nightly `siteId` lookup for joins to device, AP, and client UCs so dashboards stay aligned when the hierarchy changes often.

Step 5 — Troubleshooting
• **No `cisco:dnac:site:topology` events:** the `site_topology` input is disabled, credentials or base URL are wrong, or the service account cannot read topology; check the TA on the input host in `splunkd.log`.
• **Duplicate `siteId` in results:** a reparent or reindex may emit duplicates; add `| dedup siteId` before `stats` if needed, then confirm in Catalyst which parent is current.
• **Parents in Splunk that are not in the UI:** old cached events or a checkpoint problem after migration; work with a bump/restart of the input per Cisco guidance, coordinated with change windows in production.
• **Orphaned sites after org changes:** a Catalyst admin must reassign `parentSiteName`; governance errors are not something Splunk can correct at the source.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(siteId) as total_sites values(siteType) as types by parentSiteName | sort parentSiteName
```

## Visualization

Hierarchical or indented table (parentSiteName, total_sites, types), tree or Sankey if exported to a viz app, single value of global site count in a subsearch if needed.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
