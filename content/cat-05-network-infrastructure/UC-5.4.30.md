---
id: "5.4.30"
title: "Guest Network Access Patterns and Usage (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.30 · Guest Network Access Patterns and Usage (Meraki MR)

## Description

Tracks guest network adoption, usage patterns, and peak times for network provisioning.

## Value

Tracks guest network adoption, usage patterns, and peak times for network provisioning.

## Implementation

Filter clients API results for guest SSIDs. Track concurrent count over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api ssid="guest*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Filter clients API results for guest SSIDs. Track concurrent count over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" ssid="guest"
| stats count as guest_users by _time
| timechart avg(guest_users) as avg_concurrent_guests
```

Understanding this SPL

**Guest Network Access Patterns and Usage (Meraki MR)** — Tracks guest network adoption, usage patterns, and peak times for network provisioning.

Documented **Data sources**: `sourcetype=meraki:api ssid="guest*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time-series of guest users; daily/weekly heatmap; trend dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" ssid="guest"
| stats count as guest_users by _time
| timechart avg(guest_users) as avg_concurrent_guests
```

## Visualization

Time-series of guest users; daily/weekly heatmap; trend dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
