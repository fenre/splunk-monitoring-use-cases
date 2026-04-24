---
id: "5.13.9"
title: "Client Health Score Overview (Wired vs Wireless)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.9 · Client Health Score Overview (Wired vs Wireless)

## Description

Provides a high-level view of client health across the network, split by wired and wireless connections, using Catalyst Center's client health scoring.

## Value

Client experience is the ultimate measure of network health. This overview enables rapid assessment of how many users are experiencing good, fair, or poor connectivity.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and enable the client health input to `index=catalyst` with sourcetype `cisco:dnac:clienthealth`. Map nested `scoreDetail` fields in the TA or confirm automatic extraction. This overview depends on well-formed `scoreCategory` and `value` child fields; validate against the Catalyst Center UI for the same time range.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on; **clienthealth** data in `index=catalyst`, sourcetype `cisco:dnac:clienthealth`.
• Catalyst Center **2.3.5+** with **Assurance client** health enabled; wired-only campuses may emit fewer **scoreDetail** categories than large Wi-Fi sites.
• **Assurance** licensing for **Client 360**-style analytics; without it, nested `scoreDetail` may be empty.
• API user with **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** (read client health summaries; **pure observer** roles are often blocked in strict tenants).
• See `docs/implementation-guide.md` for nested field extraction and `props.conf` checks.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/client-health` (aggregated category rollups; not per-MAC in this crawl-tier search).
• **TA input name:** **clienthealth** modular input; sourcetype `cisco:dnac:clienthealth`.
• **Default interval:** **900 seconds (15 minutes)**—confirm in the modular input; some teams use 15m to match **Assurance** UI refresh expectations.
• **Volume:** typically **low** (summary batches), not one event per client MAC—**event count is not** “number of users.”
• **Key structure:** nested **`scoreDetail`** array with `scoreCategory` (labels), `value` / health band, `clientCount`, and often `healthyClientsPercentage` (build-dependent—validate in one **raw** JSON event).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats sum(clientCount) as total_clients by scoreCategory, value | rename value as health_score | eval client_type=case(scoreCategory=="ALL","All",scoreCategory=="WIRED","Wired",scoreCategory=="WIRELESS","Wireless",1==1,scoreCategory) | sort -total_clients
```

Understanding this SPL (spath, flattened rows, and trust boundaries)
• **`spath path=scoreDetail{}`** plus **`mvexpand`** turns each `scoreDetail` object into its own row, then **`spath input=categories`** extracts nested keys reliably—**avoid** fragile multivalue paths like `scoreDetail{}.scoreCategory.value` that break when the TA or payload shape shifts.
• **`case()` on `scoreCategory`** labels **All / Wired / Wireless** for common UI buckets; extend the `case` if your Catalyst build emits different enum strings (validate with one raw event).
• **Sums of `clientCount`** are useful for **ratios and trends**; do not treat them as **authoritative** user seats without cross-checking the **Catalyst** UI and your **IdP** data.
• If a category is missing from `scoreDetail`, that row never appears after `mvexpand`—do not infer zero from absence without checking the **Client health** UI for the same interval.

**Pipeline walkthrough**
• **`spath` / `mvexpand` / `spath input=`** flattens each entry in the **`scoreDetail`** array to fields such as `scoreCategory`, `value` (health score), and `clientCount`.
• **`stats sum(clientCount) ... by scoreCategory, value`** rolls up client totals per health band; **`rename value as health_score`** makes the score column obvious for chart labels.
• **`eval client_type=case(...)`** tags **ALL/WIRED/WIRELESS** (and falls back to the raw `scoreCategory` for other labels); **`sort -total_clients`** shows the largest populations first for dashboard tiles.

Step 3 — Validate
• Inspect one raw event: `index=catalyst sourcetype="cisco:dnac:clienthealth" | head 1` and confirm JSON under **`scoreDetail`**; then run **`| spath path=scoreDetail{} | mvexpand`** on a test search to see extracted field names before trusting charts.
• Compare **category totals and client counts** to **Catalyst Center > Client health** for the same **time window** (allow one **poll** skew).
• `| timechart count` to ensure the feed is **continuous**—a flat zero for a day is a **collection** problem, not a perfect user experience.
• If **`client_type`** labels look wrong, adjust the `case()` to match the exact `scoreCategory` strings in your data; re-check after **Catalyst** upgrades.

Step 4 — Operationalize
• **Dashboard layout:** place a **stacked bar** or **pie** of `total_clients` by `health_category` in the **client experience** row; add **single values** for “Good vs Poor” for exec readers.
• **Time picker:** **4–24 hours** for NOC; **7 days** for weekly reviews.
• **Drilldown:** add links to **device health (UC-5.13.1)** when `health_category` is **Poor** to separate **RF** issues from **backhaul** quickly.
• **Not for P1 paging alone** without companion issue UCs—this is a **fleet distribution** view.

Step 5 — Troubleshooting
• **Empty `scoreDetail`:** confirm **clienthealth** input is **enabled**, credentials valid, and **Assurance** is turned on for the site; check **`splunkd.log`** for REST errors.
• **All zeros:** the input may be scoped to an **empty** virtual domain or **lab** with no clients—re-scope the modular input in the add-on.
• **Nonsense rows after `mvexpand`:** dump one **`categories`** value with `| head 1` and **`spath` manually**; if the TA double-wraps JSON, add **`| rex`** or adjust **`spath`** path per `docs/implementation-guide.md`—do not over-trust the first install day.
• **GUI mismatch:** align **time zone** and “last 3 hours” in Catalyst vs **Last 4 hours** in Splunk before opening a TAC case.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats sum(clientCount) as total_clients by scoreCategory, value | rename value as health_score | eval client_type=case(scoreCategory=="ALL","All",scoreCategory=="WIRED","Wired",scoreCategory=="WIRELESS","Wireless",1==1,scoreCategory) | sort -total_clients
```

## Visualization

Stacked bar or pie (total_clients by health_category), trellis by client_type, single value totals for good versus poor.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
