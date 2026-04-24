---
id: "5.13.15"
title: "Client Health Category Breakdown (Good/Fair/Poor/Idle/New)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.15 · Client Health Category Breakdown (Good/Fair/Poor/Idle/New)

## Description

Provides a detailed breakdown of client health across all Catalyst Center health categories (good, fair, poor, idle, nodata, new), showing the full distribution of client experience.

## Value

The full category breakdown goes beyond simple healthy/unhealthy to show idle clients (potential AP capacity waste), new clients (onboarding quality), and nodata clients (monitoring gaps).

## Implementation

Build after UC-5.13.9 when `scoreDetail` is reliable. Use `eventstats sum(count) as total` with `eval pct=round(count*100/total,1)` so percentages share one denominator and total 100 per snapshot; for multi-snapshot data, pre-dedup with `stats latest` per category. Place as a static panel next to the UC-5.13.9 headline tiles.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
• Complete **UC-5.13.9** first so **clienthealth** and **`scoreDetail`** are validated.
• **Intent API:** `GET /dna/intent/api/v1/client-health`; **TA input:** **clienthealth**; **interval:** **900s** default.
• **Flattening:** full **`scoreDetail{}`** objects via **`spath`/`mvexpand`** (not `scoreDetail{}.scoreCategory` alone) is the supported pattern for stable field extraction here.
• **Percent math:** `eventstats` provides a **single total** for all rows; if you merge multiple time buckets, `stats latest` per **scoreCategory** before `eventstats` to avoid double-counting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats latest(clientCount) as count by scoreCategory | eventstats sum(count) as total | eval pct=round(count*100/total,1) | table scoreCategory count pct | sort -count
```

Understanding this SPL

**Client Health Category Breakdown (Good/Fair/Poor/Idle/New)** — The full category breakdown goes beyond simple healthy/unhealthy to show idle clients (potential AP capacity waste), new clients (onboarding quality), and nodata clients (monitoring gaps).

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:clienthealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• **`spath path=scoreDetail{}`** (full objects) and **`mvexpand`** normalize nested **client health** rows more reliably than targeting **`scoreDetail{}.scoreCategory`** alone.
• `stats latest` per `scoreCategory` stabilizes a per-category population for the search window, assuming steady **clienthealth** polling.
• **`eventstats sum(count) as total`** then **`eval pct=round(count*100/total,1)`** computes percentages with a **consistent denominator**; `table` and `sort` format the **Good/Fair/Poor/Idle** story next to UC-5.13.9.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: 100% stacked bar or pie of pct by scoreCategory, table with count and pct, trellis of category mix over sites if you later join `siteId`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats latest(clientCount) as count by scoreCategory | eventstats sum(count) as total | eval pct=round(count*100/total,1) | table scoreCategory count pct | sort -count
```

## Visualization

100% stacked bar or pie of pct by scoreCategory, table with count and pct, trellis of category mix over sites if you later join `siteId`.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
