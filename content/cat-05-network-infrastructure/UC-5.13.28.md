<!-- AUTO-GENERATED from UC-5.13.28.json — DO NOT EDIT -->

---
id: "5.13.28"
title: "Device Compliance Status Overview"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.28 · Device Compliance Status Overview

## Description

Provides an overview of device compliance status across the managed infrastructure as reported by Catalyst Center compliance policies.

## Value

Compliance is a continuous requirement. This overview shows at a glance how many devices are compliant, non-compliant, or in error state.

## Implementation

Enable the `compliance` input in the Cisco Catalyst TA. The TA polls `GET /dna/intent/api/v2/compliance/detail` on a **900s** default interval. Key fields: `complianceStatus` (COMPLIANT, NON_COMPLIANT, ERROR, IN_PROGRESS, NOT_APPLICABLE), `deviceName`, `complianceType` (RUNNING_CONFIG, IMAGE, PSIRT, EOX, NETWORK_SETTINGS).

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538) installed; **compliance** feed landing in `index=catalyst` with sourcetype `cisco:dnac:compliance`.
• Catalyst Center **2.2+** (confirm **Intent API v2** in your build); service account with **`NETWORK-ADMIN-ROLE`** or higher read access to **Compliance** APIs (exact role names may vary by version—verify in ISE/AAA for the API user).
• Retention and export policy aligned to **NIST/PCI** evidence needs (often **90–365 days** in the `catalyst` index or a **summary** index for compliance snapshots).
• See `docs/implementation-guide.md` for `inputs.conf`, secure credential storage, and index sizing.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v2/compliance/detail`.
• **TA input name:** **compliance**; sourcetype `cisco:dnac:compliance`.
• **Default interval:** **900 seconds (15 minutes)**—balance API load vs freshness; shorten only if your change-approval process requires it.
• **Key fields:** `complianceStatus` (**COMPLIANT**, **NON_COMPLIANT**, **ERROR**, **IN_PROGRESS**, **NOT_APPLICABLE**), `deviceName`, `complianceType` (**RUNNING_CONFIG**, **IMAGE**, **PSIRT**, **EOX**, **NETWORK_SETTINGS**).
• **Volume note:** the TA may emit **one or many events** per poll—use **dedup**/`latest` in downstream panels if you see duplicate **deviceName** + **complianceType** rows per bucket.

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats count by complianceStatus | eventstats sum(count) as _total | eval pct=round(100*count/_total,1)
```

Understanding this SPL
• **`stats` + `eventstats`** yields a **stable percentage** of each `complianceStatus` value for the selected window (prefer **`eventstats`** over `sum(count)` in **`eval`** alone for clarity at scale).
• Filter with `complianceType=<value>` in a **post-process** or **base + append** if you need **separate** pies per policy family (for example **IMAGE** vs **RUNNING_CONFIG**).

**Pipeline walkthrough**
• Scopes **`cisco:dnac:compliance`**; rolls up **counts** and attaches **%** of total for dashboard tiles and audit tables.

Step 3 — Validate
• **Compare the percentage of devices in each status (especially COMPLIANT vs NON_COMPLIANT) against the Catalyst Center Compliance dashboard** for the same scope and time—Splunk and the UI should agree within one **poll**.
• Spot-check a few **deviceName** values that appear as **ERROR** or **IN_PROGRESS** in Splunk and confirm the same in the GUI.
• Run **`| timechart count by complianceStatus`** to ensure **continuous** ingestion; long gaps indicate TA or API issues, not a silent “all green” network.

Step 4 — Operationalize
• **Dashboard:** donut or bar by **complianceStatus**, **single value** for **% COMPLIANT**, plus a **table** of top exceptions when filtered to **NON_COMPLIANT**.
• **Evidence:** schedule this saved search **daily** and archive CSV/PDF to your GRC or evidence store per your control framework.
• **IN_PROGRESS spikes** often follow **bulk template pushes**—annotate change windows on the panel so teams do not misread a temporary state.

Step 5 — Troubleshooting
• **No events:** enable **compliance** input, re-check **Catalyst** base URL, token, and role; search **`splunkd.log`** for **HTTP 401/403/429**.
• **Partial statuses only:** your policies may be **unassigned** for some platforms—**NOT_APPLICABLE** dominance is a **Catalyst** configuration topic, not a Splunk parse bug.
• **Count mismatch vs UI:** align **time zone**, **device inventory scope** (virtual domain / site), and **dedup** logic with what the operator filters in the **Compliance** UI.
• **Stuck IN_PROGRESS:** confirm **on-device** or **Catalyst** jobs are not **stalled**; open **TAC** if compliance jobs **never** complete for a class of devices.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats count by complianceStatus | eventstats sum(count) as _total | eval pct=round(100*count/_total,1)
```

## Visualization

Pie or donut (count by complianceStatus), single value (compliant %), table with status and percentage.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
