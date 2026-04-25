<!-- AUTO-GENERATED from UC-5.13.5.json — DO NOT EDIT -->

---
id: "5.13.5"
title: "Device Health by Site Hierarchy"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.5 · Device Health by Site Hierarchy

## Description

Aggregates device health scores by Catalyst Center site hierarchy (area, building, floor), identifying locations with systemic network problems.

## Value

Pinpoints which physical locations have the worst network health, enabling site-specific remediation and resource allocation.

## Implementation

Prerequisite: UC-5.13.1 live with `siteId` and device health in `index=catalyst`. Enrich with a site name lookup if only IDs are present. Add this panel to regional operations dashboards; schedule a weekly report for the top 20 sites by unhealthy percentage.

## Detailed Implementation

Prerequisites
• **UC-5.13.1** with **`siteId`** on `cisco:dnac:devicehealth` (Catalyst **site hierarchy** must be populated in **Design > Network Hierarchy** and synced to inventory).
• Cisco Catalyst Add-on (7538), **devicehealth** input, **`NETWORK-ADMIN-ROLE`** or **`SUPER-ADMIN-ROLE`**.
• A **lookup** from **`siteId`** to **building name** is strongly recommended for tickets and reports.
• See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/device-health` via **devicehealth** modular input, sourcetype `cisco:dnac:devicehealth`.
• **Key field:** `siteId` (UUID or string as emitted)—confirm in **one raw event**; missing `siteId` means devices are unassigned in Catalyst **hierarchy**.
• **Poll:** default **900s**; for **head 20** weekly reports, **widen** the time range to **7d** to smooth single bad polls.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct | head 20
```

Understanding this SPL
• **Per-site** aggregation answers “**where** is the pain?”; **`head 20`** focuses leadership on the **worst** sites—**increase to 50** or **remove** `head` if you use **filters** (region) instead.
• **`<50` unhealthy** matches common **Poor** bands; align with your **SLO** per site **tier** (hospital vs. warehouse) if you add a **lookup** for stricter floors.
• Cross-check **`device_count`**: a site with **2** devices and **1** unhealthy is **50%**—interpret with care.

**Pipeline walkthrough**
• `stats` by **`siteId`**: **avg** health, population, and **count** below threshold.
• `eval` **percentage**; `sort` then **`head 20`** for a **regional** hot list.

Step 3 — Validate
• Join **`siteId`** to Catalyst **UI** **site** names; spot-check **unhealthy** devices at one site in **Assurance** vs. Splunk row.
• Compare **Top 20** **device totals** to **sum of site inventory** for the same scope—gaps point to **unassigned** devices.
• **`| where device_count>10`** in a test search to see how ranking changes for **noise** from small sites.

Step 4 — Operationalize
• **Dashboard:** **table** with **lookup**-enriched **site name**, **`avg_health`**, **`unhealthy_pct`**, **`device_count`**; default **Last 7 days** for exec reviews; **24h** for NOC.
• **Scheduled report:** weekly **PDF** to regional leads; **drill** to **UC-5.13.1** and **device** inventory for the same `siteId`.
• **Optional alert:** when **`unhealthy_pct`** for a **tier-1** site in a **lookup** exceeds **X%** with **min device_count**—avoid paging on every small branch blip.

Step 5 — Troubleshooting
• **All `siteId` = null:** fix **hierarchy** assignment in Catalyst and **re-inventory**; confirm TA sends the same field name.
• **Site missing from top 20 but users complain:** the issue may be **client**-side—use **UC-5.13.9+**; or devices may sit in a **different** `siteId` than users expect (VPN, SD-WAN).
• **Rankings shift every poll:** API instability or **duplicate** `deviceName` across sites—dedupe logic from **UC-5.13.1** notes applies.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct | head 20
```

## Visualization

Table (top 20 sites with avg_health, counts, unhealthy_pct), bar chart, choropleth or tile map if you join geo metadata.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
