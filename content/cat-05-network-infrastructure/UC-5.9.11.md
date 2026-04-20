---
id: "5.9.11"
title: "BGP AS Path Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.11 · BGP AS Path Monitoring

## Description

Tracking AS path changes reveals when traffic is routed through unexpected autonomous systems, which can indicate route leaks, hijacks, or ISP peering changes.

## Value

Tracking AS path changes reveals when traffic is routed through unexpected autonomous systems, which can indicate route leaks, hijacks, or ISP peering changes.

## Implementation

The OTel attribute `network.as.path` provides the full AS path as a space-separated list of ASNs. By tracking distinct AS paths over time for each prefix and monitor, you can detect when routing changes introduce new transit providers. Combine with `bgp.path_changes.count` spikes to focus investigation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel attribute `network.as.path` provides the full AS path as a space-separated list of ASNs. By tracking distinct AS paths over time for each prefix and monitor, you can detect when routing changes introduce new transit providers. Combine with `bgp.path_changes.count` spikes to focus investigation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats dc(network.as.path) as unique_paths values(network.as.path) as as_paths by network.prefix, thousandeyes.monitor.name
| where unique_paths > 1
| sort -unique_paths
```

Understanding this SPL

**BGP AS Path Monitoring** — Tracking AS path changes reveals when traffic is routed through unexpected autonomous systems, which can indicate route leaks, hijacks, or ISP peering changes.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by network.prefix, thousandeyes.monitor.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where unique_paths > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (prefix, monitor, AS paths seen), Timeline of path changes, Alert on new AS path appearance.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats dc(network.as.path) as unique_paths values(network.as.path) as as_paths by network.prefix, thousandeyes.monitor.name
| where unique_paths > 1
| sort -unique_paths
```

## Visualization

Table (prefix, monitor, AS paths seen), Timeline of path changes, Alert on new AS path appearance.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
