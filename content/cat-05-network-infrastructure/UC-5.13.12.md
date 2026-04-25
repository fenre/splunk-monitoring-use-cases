<!-- AUTO-GENERATED from UC-5.13.12.json — DO NOT EDIT -->

---
id: "5.13.12"
title: "Client Health by SSID and VLAN"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.12 · Client Health by SSID and VLAN

## Description

Breaks down client health by SSID and VLAN to identify specific wireless networks or network segments with poor performance.

## Value

Different SSIDs serve different purposes (corporate, guest, IoT). Isolating health by SSID reveals which user communities are most affected.

## Implementation

Prerequisite: UC-5.13.9. Use `spath` to normalize nested `scoreDetail` so each segment name becomes a row; confirm Catalyst Center is emitting the segment identifiers you expect (sometimes encoded in `scoreCategory`). If SSID and VLAN are split across other APIs, consider a `lookup` join in a later version of this panel.

## Detailed Implementation

Prerequisites
• **UC-5.13.9** working: `clienthealth` input, sourcetype `cisco:dnac:clienthealth`, and visible nested `scoreDetail` in at least one raw event.
• Cisco Catalyst Add-on (7538); Assurance client health licensed. The TA polls the Intent API (client health) on a default 900s interval.
• SSID vs VLAN: Catalyst may encode segment or WLAN identity inside nested `scoreCategory` fields—the exact path varies by release. Validate field names in raw JSON before relying on the panel for exec reporting.
• See `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• Enable the `clienthealth` modular input; destination index `catalyst`.
• If `scoreCategory` is nested, use `spath input=scores` after `mvexpand` so `scoreCategory.value` and the label field used in `by` are populated.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=scores path=scoreDetail{} | mvexpand scores | spath input=scores | search scoreCategory.scoreCategory="*" | stats avg(scoreCategory.value) as avg_health sum(clientCount) as total_clients by scoreCategory.scoreCategory | sort -total_clients
```

Understanding this SPL
• The `spath` / `mvexpand` / `spath input=scores` pattern matches the flattening approach in UC-5.13.9 but targets nested `scoreCategory.*` for segment labels in your build.
• The `search scoreCategory.scoreCategory="*"` clause drops empty labels; replace with a fixed list of production SSIDs if test WLANs add noise.
• Sorting by `total_clients` surfaces high-traffic wireless segments first; read alongside `avg_health` so a tiny guest SSID with few clients does not dominate the story by mistake.

**Pipeline walkthrough**
• `mvexpand` on `scoreDetail` rows, then `stats` by the SSID/segment name field, summing client counts and averaging the health value for that slice.

Step 3 — Validate
• Capture one event and confirm the nested fields used in the `stats` match what Catalyst Center shows under Client health for a named SSID in the same time range.
• If the search returns no rows, compare to UC-5.13.9’s `spath path=scoreDetail{}` path—your payload may use different key names; adjust field paths accordingly.

Step 4 — Operationalize
• Use a table (segment name, avg_health, total_clients) on a Wi-Fi or client experience dashboard; optional site or building token if you add `siteId` enrichment in another panel.
• For poor rows, the runbook should point to WLC config, RADIUS policy, and Catalyst issues apps—not this search alone.

Step 5 — Troubleshooting
• Null or missing `scoreCategory.value`: inspect one `scores` string after `mvexpand`; update `spath` or field names after TA or Catalyst upgrades.
• Duplicate or doubled client counts: dedupe on poll time and device, or narrow the time range if the same client health batch ingests twice.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=scores path=scoreDetail{} | mvexpand scores | spath input=scores | search scoreCategory.scoreCategory="*" | stats avg(scoreCategory.value) as avg_health sum(clientCount) as total_clients by scoreCategory.scoreCategory | sort -total_clients
```

## Visualization

Table (scoreCategory, avg_health, total_clients), bar chart of total_clients, optional heat map when pivoted with site in another panel.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
