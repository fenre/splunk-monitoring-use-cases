<!-- AUTO-GENERATED from UC-5.13.26.json — DO NOT EDIT -->

---
id: "5.13.26"
title: "Issue Distribution by Device and Site"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.26 · Issue Distribution by Device and Site

## Description

Maps assurance issues to specific devices and sites to identify problem hotspots in the network infrastructure.

## Value

Some devices or sites generate disproportionate issue volumes. Identifying these hotspots focuses remediation where it has the most impact.

## Implementation

Enable the `issue` input. Confirm `siteId` is extracted from Catalyst Center issue payloads. If the field is missing, enrich using a site lookup or device inventory from Catalyst Center inventory feeds in Splunk.

## Detailed Implementation

Prerequisites
• **issue** events with **`deviceId`**; **`siteId`** is required for this **split**—if missing, **join** to **`cisco:dnac:device`** or a **CMDB/lookup** keyed by `deviceId` or serial (see other Catalyst UCs in this family).
• Cisco Catalyst Add-on 7538; confirm **field** names on raw JSON (some builds nest **location** under **site**).
• `docs/implementation-guide.md` for **lookup** placement in **`lookups/`** and **transforms**.

Step 1 — Configure data collection
• **API:** `GET /dna/intent/api/v1/issues` (same **issue** input as **UC-5.13.21**).
• **Key fields for this view:** `deviceId`, `siteId`, `name` (issue title).
• **Enrichment** when **`siteId` is null:** **`| lookup catal_site_lookup deviceId OUTPUT siteId`** (example) after you build the table from inventory or **device** **health** data.

Step 2 — Create the report
```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as issue_count dc(name) as unique_issues by deviceId, siteId | sort -issue_count | head 20
```

Understanding this SPL (breadth vs volume)
• **`dc(name)`** is **how many** **different** **Assurance** titles hit that **device**—**high** **issue_count** with **low** **unique_issues** is **stutter**; **high** on **both** is **broad** failure.
• **`head 20`:** change to **50** for large retailers; for **trellis** by **region**, add **post-process** filters.

**Pipeline walkthrough**
• **Hotspot** table for **war-room** wall: pair with **Catalyst** **Device 360** links using **`deviceId`** in the **drilldown** token.

Step 3 — Validate
• **Cross-check** top **`deviceId`** in **Catalyst** against **this device’s** open issues; **count** mismatch usually means **dedup** policy differs.
• **`| stats dc(siteId)`** to ensure **hierarchy** **coverage**; **all NULL** `siteId` means you must **enrich** before trusting the table.

Step 4 — Operationalize
• **Dashboard:** **table** + optional **treemap** (**site** parent, **device** child) in Dashboard Studio if cardinality allows.
• **Hand-off:** assign **RFO** for **#1** **site** each week in ops review—link **UC-5.13.25** for **chronic** **titles**.

Step 5 — Troubleshooting
• **Blank `deviceId`:** some **global** or **control-plane** issues are not tied to a **single** **device**—handle with a **'N/A'** **bucket** or **separate** **panel**.
• **Duplicate** **rows** for same **chassis** different **line cards:** normalize to **deviceName** in a v2 if your TA also sends **name** **fields** **per** **member** **switch**.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as issue_count dc(name) as unique_issues by deviceId, siteId | sort -issue_count | head 20
```

## Visualization

Table (top 20 by issue_count), treemap or packed bubble by siteId and deviceId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
