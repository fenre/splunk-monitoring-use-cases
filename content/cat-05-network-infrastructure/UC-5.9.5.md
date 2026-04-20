---
id: "5.9.5"
title: "Path Hop Count Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.5 · Path Hop Count Analysis

## Description

Sudden changes in the number of hops to a target can indicate routing changes, path instability, or sub-optimal traffic engineering. The Splunk App provides min-hop drilldowns on the Network dashboard.

## Value

Sudden changes in the number of hops to a target can indicate routing changes, path instability, or sub-optimal traffic engineering. The Splunk App provides min-hop drilldowns on the Network dashboard.

## Implementation

Enable "Include Network Path Data" in the Tests Stream — Metrics input configuration. Update the `path_viz_index` macro to the correct index. Path Visualization data is collected at a configurable interval via the ThousandEyes API.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Path Visualization data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Include Network Path Data" in the Tests Stream — Metrics input configuration. Update the `path_viz_index` macro to the correct index. Path Visualization data is collected at a configurable interval via the ThousandEyes API.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats min(hop_count) as min_hops max(hop_count) as max_hops by thousandeyes.source.agent.name, server.address
| where max_hops - min_hops > 2
| sort -max_hops
```

Understanding this SPL

**Path Hop Count Analysis** — Sudden changes in the number of hops to a target can indicate routing changes, path instability, or sub-optimal traffic engineering. The Splunk App provides min-hop drilldowns on the Network dashboard.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Path Visualization data. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `path_viz_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where max_hops - min_hops > 2` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (min hops per target), Table (agent, server, min hops, max hops), Line chart (hop count trending).

## SPL

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats min(hop_count) as min_hops max(hop_count) as max_hops by thousandeyes.source.agent.name, server.address
| where max_hops - min_hops > 2
| sort -max_hops
```

## Visualization

Single value (min hops per target), Table (agent, server, min hops, max hops), Line chart (hop count trending).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
