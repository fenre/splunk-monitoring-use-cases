---
id: "5.2.35"
title: "Cellular Modem Failover Activation and Usage (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.35 · Cellular Modem Failover Activation and Usage (Meraki MX)

## Description

Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.

## Value

Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.

## Implementation

Ingest cellular failover events. Track data consumption.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*4G*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest cellular failover events. Track data consumption.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*4G*" OR signature="*LTE*")
| stats count as cellular_events, sum(data_usage_mb) as total_cellular_data by event_type
| where total_cellular_data > 0
```

Understanding this SPL

**Cellular Modem Failover Activation and Usage (Meraki MX)** — Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*4G*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by event_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where total_cellular_data > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Cellular usage timeline; failover event table; data usage gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*4G*" OR signature="*LTE*")
| stats count as cellular_events, sum(data_usage_mb) as total_cellular_data by event_type
| where total_cellular_data > 0
```

## Visualization

Cellular usage timeline; failover event table; data usage gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
