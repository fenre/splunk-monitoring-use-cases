---
id: "5.1.36"
title: "Port Utilization and Congestion Alerts (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.36 · Port Utilization and Congestion Alerts (Meraki MS)

## Description

Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.

## Value

Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.

## Implementation

Query MS switch device API for port utilization metrics. Alert on sustained >80% utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MS`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MS switch device API for port utilization metrics. Alert on sustained >80% utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(port_utilization) as avg_util, max(port_utilization) as max_util by switch_name, port_id
| where max_util > 80
| sort - max_util
```

Understanding this SPL

**Port Utilization and Congestion Alerts (Meraki MS)** — Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.

Documented **Data sources**: `sourcetype=meraki:api device_type=MS`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, port_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where max_util > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of congested ports; timeline showing peak congestion; port utilization heatmap.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(port_utilization) as avg_util, max(port_utilization) as max_util by switch_name, port_id
| where max_util > 80
| sort - max_util
```

## Visualization

Table of congested ports; timeline showing peak congestion; port utilization heatmap.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
