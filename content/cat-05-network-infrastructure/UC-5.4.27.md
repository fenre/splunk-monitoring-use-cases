---
id: "5.4.27"
title: "Connection Duration and Session Quality (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.27 · Connection Duration and Session Quality (Meraki MR)

## Description

Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.

## Value

Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.

## Implementation

Extract connection_duration from clients API. Aggregate by SSID and time of day.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract connection_duration from clients API. Aggregate by SSID and time of day.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" connection_duration=*
| stats avg(connection_duration) as avg_session_time, min(connection_duration) as min_session, max(connection_duration) as max_session by ssid
| eval session_quality=if(avg_session_time > 3600, "Stable", "Short")
```

Understanding this SPL

**Connection Duration and Session Quality (Meraki MR)** — Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **session_quality** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Histogram of session durations; time-of-day heatmap; SSID comparison chart.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" connection_duration=*
| stats avg(connection_duration) as avg_session_time, min(connection_duration) as min_session, max(connection_duration) as max_session by ssid
| eval session_quality=if(avg_session_time > 3600, "Stable", "Short")
```

## Visualization

Histogram of session durations; time-of-day heatmap; SSID comparison chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
