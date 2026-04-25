<!-- AUTO-GENERATED from UC-5.13.19.json — DO NOT EDIT -->

---
id: "5.13.19"
title: "Network Health by Site (Area/Building)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.19 · Network Health by Site (Area/Building)

## Description

Compares network health scores across Catalyst Center sites to identify locations with the worst performance and prioritize remediation.

## Value

Not all sites are equal. Comparing health across sites reveals which locations need immediate attention and which are performing well.

## Implementation

Build on UC-5.13.16 with per-site `siteId` in each network health event. If your feed is global only, re-pull site-level API metrics or merge with a site mapping from device health. Enrich the table with building names from a `lookup` for executive readability.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (7538) with **networkhealth** to `cisco:dnac:networkhealth` in `index=catalyst`.
• **Confirm `siteId` exists and is populated** in raw `networkhealth` events for your TA version. If the feed is **global-only** (one row per poll without per-site fields), you cannot use this exact SPL without switching to a site-scoped API source or **joining** to **device health** (UC-5.13.1) or **site health** (UC-5.13.x sitehealth sourcetype) to roll up by site.
• Optional: a **lookup** of `siteId` to building or campus name for NOC-friendly tables.
• `docs/implementation-guide.md` for index routing and the **networkhealth** input host.

Step 1 — Configure data collection
• **Intent API context:** `GET /dna/intent/api/v1/network-health` and any **site** query parameters the TA supports (read the add-on **README** for per-site vs cluster-wide mode).
• **TA input:** **networkhealth**; verify **sourcetype** `cisco:dnac:networkhealth` and interval (**900s** default).
• **Key fields for this panel:** `siteId`, `healthScore`, `goodCount`, `badCount` (names must match a sample event).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad by siteId | eval total=good+bad | eval healthy_pct=round(good*100/total,1) | sort health_score | head 20
```

Understanding this SPL (totals, zero-divide, head 20)
• **`eval total=good+bad`** assumes the two counts partition the same population; if the API reports **other** states, add them to **total** or use **`totalCount`** if present in your payload (macro recommended).
• **Guard** empty totals: in production, append **`| where total>0`** or `eval` a safe `healthy_pct` so you do not divide by zero during Assurance startup.
• **`head 20`:** floor or raise **20** for your estate; tie-break by **`bad`** in a v2 with **`sort` multiple fields** if many sites sit at the same score.

**Pipeline walkthrough**
• `latest()` per `siteId` picks the most recent **Assurance** roll-up for that site in the time range.
• `sort` ascending on **`health_score`** lists **worst sites first** for dispatch.

Step 3 — Validate
• Compare the **top** sites in Splunk to **Catalyst Center** filtered by the same **site** scope; mismatch often means **Splunk** is aggregating a **wider** time window or the TA is on a different **virtual domain**.
• `| fieldsummary siteId` to confirm **cardinality** matches your **Network Hierarchy**; **null `siteId`** rows should be triaged to props or a join.
• Spot-check one **poor** site’s devices in **Assurance** in the same hour as UC-5.13.1.

Step 4 — Operationalize
• **Dashboard:** table of **20 worst** with **link** to a **site** or **device** drilldown (tokens for `siteId`).
• **Map:** if you have **lat/long** in a **lookup**, add a **choropleth** or **map** in Dashboard Studio; keep **table** for export to QBRs.
• **Not for** paging by itself without thresholds—use **UC-5.13.18** for fleet-wide **degradation** alerts.

Step 5 — Troubleshooting
• **Single row or no `siteId`:** the TA is likely sending **one** **cluster** summary; enable **per-site** collection or add a **by-site** data path from the API.
• **All sites same score:** **good/bad** counts may be **zeros** or **NULL**—`fieldsummary` the week of upgrade; re-check **Assurance** licensing.
• **Percent over 100 or negative:** count math is wrong; align **`total`** with the **Catalyst** UI denominator.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad by siteId | eval total=good+bad | eval healthy_pct=round(good*100/total,1) | sort health_score | head 20
```

## Visualization

Table (top 20 sites, health_score, good/bad, healthy_pct), bar chart, optional map of sites if geo is joined via CMDB export.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
