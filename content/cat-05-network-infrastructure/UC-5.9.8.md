---
id: "5.9.8"
title: "BGP Reachability Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.8 · BGP Reachability Monitoring

## Description

Monitors whether BGP-advertised prefixes are reachable from global vantage points. Loss of reachability means users in affected regions cannot reach your services.

## Value

Monitors whether BGP-advertised prefixes are reachable from global vantage points. Loss of reachability means users in affected regions cannot reach your services.

## Implementation

Create BGP tests in ThousandEyes for your critical prefixes and stream to Splunk. The OTel metric `bgp.reachability` reports a percentage — 100% means the prefix is reachable from that monitor. The Splunk App Network dashboard includes a BGP Reachability map panel.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create BGP tests in ThousandEyes for your critical prefixes and stream to Splunk. The OTel metric `bgp.reachability` reports a percentage — 100% means the prefix is reachable from that monitor. The Splunk App Network dashboard includes a BGP Reachability map panel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.name, network.prefix
| where avg_reachability < 100
| sort avg_reachability
```

Understanding this SPL

**BGP Reachability Monitoring** — Monitors whether BGP-advertised prefixes are reachable from global vantage points. Loss of reachability means users in affected regions cannot reach your services.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.monitor.name, network.prefix** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_reachability < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (BGP reachability by monitor location), Single value (overall reachability %), Table (monitor, prefix, reachability).

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.name, network.prefix
| where avg_reachability < 100
| sort avg_reachability
```

## Visualization

Map (BGP reachability by monitor location), Single value (overall reachability %), Table (monitor, prefix, reachability).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
