---
id: "5.4.15"
title: "SSID Performance Ranking and Trend Analysis (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.15 · SSID Performance Ranking and Trend Analysis (Meraki MR)

## Description

Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.

## Value

Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.

## Implementation

Aggregate client connection metrics by SSID. Compare average connection duration, client count, and signal strength.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Aggregate client connection metrics by SSID. Compare average connection duration, client count, and signal strength.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(connection_duration) as avg_duration, count as client_count, avg(rssi) as avg_rssi by ssid
| eval performance_score=round((avg_rssi+100)*client_count/100, 2)
| sort - performance_score
```

Understanding this SPL

**SSID Performance Ranking and Trend Analysis (Meraki MR)** — Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **performance_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(connection_duration) as avg_duration, count as client_count, avg(rssi) as avg_rssi by ssid
| eval performance_score=round((avg_rssi+100)*client_count/100, 2)
| sort - performance_score
```

## Visualization

Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
