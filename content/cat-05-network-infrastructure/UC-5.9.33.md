<!-- AUTO-GENERATED from UC-5.9.33.json — DO NOT EDIT -->

---
id: "5.9.33"
title: "Cloud Provider Path Visualization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.33 · Cloud Provider Path Visualization

## Description

Hop-by-hop path visualization through cloud provider backbones reveals routing decisions, peering points, and potential bottlenecks within AWS, Azure, or GCP networks that are otherwise invisible.

## Value

Hop-by-hop path visualization through cloud provider backbones reveals routing decisions, peering points, and potential bottlenecks within AWS, Azure, or GCP networks that are otherwise invisible.

## Implementation

Enable "Include Network Path Data" in the Tests Stream input for cloud-targeted tests. Path Visualization data shows every hop between the agent and target. The `path_viz_index` macro must be configured. For detailed path analysis, use the `thousandeyes.permalink` to drill into the ThousandEyes UI path visualization view.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Path Visualization data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Include Network Path Data" in the Tests Stream input for cloud-targeted tests. Path Visualization data shows every hop between the agent and target. The `path_viz_index` macro must be configured. For detailed path analysis, use the `thousandeyes.permalink` to drill into the ThousandEyes UI path visualization view.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats count values(hop_ip) as hops by thousandeyes.test.name, thousandeyes.source.agent.name
| sort thousandeyes.test.name
```

Understanding this SPL

**Cloud Provider Path Visualization** — Hop-by-hop path visualization through cloud provider backbones reveals routing decisions, peering points, and potential bottlenecks within AWS, Azure, or GCP networks that are otherwise invisible.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Path Visualization data. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `path_viz_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (test, agent, hop list), Drilldown to ThousandEyes path viz, Network topology diagram.

## SPL

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats count values(hop_ip) as hops by thousandeyes.test.name, thousandeyes.source.agent.name
| sort thousandeyes.test.name
```

## Visualization

Table (test, agent, hop list), Drilldown to ThousandEyes path viz, Network topology diagram.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
