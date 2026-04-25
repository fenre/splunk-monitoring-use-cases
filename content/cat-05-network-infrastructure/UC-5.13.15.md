<!-- AUTO-GENERATED from UC-5.13.15.json — DO NOT EDIT -->

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
• **UC-5.13.9** in place: reliable `cisco:dnac:clienthealth` and visible `scoreDetail` arrays in raw data.
• Cisco Catalyst Add-on (7538); `clienthealth` input; `GET /dna/intent/api/v1/client-health` behind the scenes.
• Use full `scoreDetail{}` objects with `spath` and `mvexpand` so Good/Fair/Poor/Idle/New/nodata rows extract consistently across TA versions.
• See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Default 900s poll; ensure Assurance client analytics is on for the sites you report.
• Category enum strings (GOOD, POOR, IDLE, etc.) may vary—run `| stats values(scoreCategory)` after flattening before publishing executive labels.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats latest(clientCount) as count by scoreCategory | eventstats sum(count) as total | eval pct=round(count*100/total,1) | table scoreCategory count pct | sort -count
```

Understanding this SPL
• `latest(clientCount) by scoreCategory` takes the most recent population per health bucket in the time window; if multiple polls are present, narrow the time picker to “last poll” or pre-dedupe with `| stats latest(_time) as t by scoreCategory` pattern if you need a single snapshot.
• `eventstats sum(count) as total` gives one denominator for percentage so all buckets on the same table sum to 100% for that snapshot.
• `sort -count` lists the largest segments first; compare next to UC-5.13.9 headline “wired vs wireless” when storytelling.

**Pipeline walkthrough**
• Flatten nested JSON → per-category `clientCount` → percent of whole.

Step 3 — Validate
• Compare category totals to Catalyst Center Client health pie or table for the same scope and time; allow one poll skew.
• If percentages do not add to ~100%, duplicate polls or double `mvexpand` may be present—`dedup` on `_raw`+`_time` in a test.

Step 4 — Operationalize
• 100% stacked bar or table beside UC-5.13.9; use for NOC and exec “experience mix” reviews. When nodata is high, open inventory and client telemetry coverage, not just RF tuning.
• Optional: clone panel with `by siteId` in a pre-search if the feed is site-scoped per event.

Step 5 — Troubleshooting
• Category missing after upgrade: Cisco renamed enums—rebuild `values(scoreCategory)` and update the dashboard labels.
• All nodata: client health not enabled for site or `scoreDetail` empty in JSON—revisit clienthealth input and API permissions.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | stats latest(clientCount) as count by scoreCategory | eventstats sum(count) as total | eval pct=round(count*100/total,1) | table scoreCategory count pct | sort -count
```

## Visualization

100% stacked bar or pie of pct by scoreCategory, table with count and pct, trellis of category mix over sites if you later join `siteId`.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
