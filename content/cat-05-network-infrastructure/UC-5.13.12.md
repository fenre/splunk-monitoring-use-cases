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
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prerequisite: UC-5.13.9. Use `spath` to normalize nested `scoreDetail` so each segment name becomes a row; confirm Catalyst Center is emitting the segment identifiers you expect (sometimes encoded in `scoreCategory`). If SSID and VLAN are split across other APIs, consider a `lookup` join in a later version of this panel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=scores path=scoreDetail{} | mvexpand scores | spath input=scores | search scoreCategory.scoreCategory="*" | stats avg(scoreCategory.value) as avg_health sum(clientCount) as total_clients by scoreCategory.scoreCategory | sort -total_clients
```

Understanding this SPL

**Client Health by SSID and VLAN** — Different SSIDs serve different purposes (corporate, guest, IoT). Isolating health by SSID reveals which user communities are most affected.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:clienthealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `spath` and `mvexpand` flatten each `scoreDetail` child object to its own row so you can work with `scoreCategory` and `clientCount` as first-class fields.
• A narrow `search` after `spath` keeps rows that actually carry a category token; adjust the pattern if you need to limit to a subset of segments.
• Final `stats` rolls up to average of `value` and sum of `clientCount` by category string, and `sort` shows the heaviest-usage segments with their health, guiding SSID- or segment-specific fixes next to UC-5.13.9.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (scoreCategory, avg_health, total_clients), bar chart of total_clients, optional heat map when pivoted with site in another panel.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=scores path=scoreDetail{} | mvexpand scores | spath input=scores | search scoreCategory.scoreCategory="*" | stats avg(scoreCategory.value) as avg_health sum(clientCount) as total_clients by scoreCategory.scoreCategory | sort -total_clients
```

## Visualization

Table (scoreCategory, avg_health, total_clients), bar chart of total_clients, optional heat map when pivoted with site in another panel.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
