---
id: "5.9.6"
title: "Network Path Change Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.6 · Network Path Change Detection

## Description

Detects when the network path between an agent and a target changes, which can indicate routing instability, ISP re-routing, or failover events. Correlating path changes with latency spikes helps isolate root cause.

## Value

Detects when the network path between an agent and a target changes, which can indicate routing instability, ISP re-routing, or failover events. Correlating path changes with latency spikes helps isolate root cause.

## Implementation

Path Visualization data must be enabled in the Tests Stream input. This use case requires building a path fingerprint (hash of intermediate hops) over time windows to detect when routes shift. Correlate with `network.latency` from the metrics stream to identify performance-impacting path changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Path Visualization data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Path Visualization data must be enabled in the Tests Stream input. This use case requires building a path fingerprint (hash of intermediate hops) over time windows to detect when routes shift. Correlate with `network.latency` from the metrics stream to identify performance-impacting path changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```

Understanding this SPL

**Network Path Change Detection** — Detects when the network path between an agent and a target changes, which can indicate routing instability, ISP re-routing, or failover events. Correlating path changes with latency spikes helps isolate root cause.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Path Visualization data. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `path_viz_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where unique_paths > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (path changes over time), Table (agent, server, unique paths), Drilldown to ThousandEyes via `thousandeyes.permalink`.

## SPL

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```

## Visualization

Timeline (path changes over time), Table (agent, server, unique paths), Drilldown to ThousandEyes via `thousandeyes.permalink`.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
