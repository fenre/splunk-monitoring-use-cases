<!-- AUTO-GENERATED from UC-5.8.17.json — DO NOT EDIT -->

---
id: "5.8.17"
title: "Network Health Score Aggregation and Executive Reporting (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.17 · Network Health Score Aggregation and Executive Reporting (Meraki)

## Description

Provides high-level network health metric for executive dashboards and trend reporting.

## Value

Provides high-level network health metric for executive dashboards and trend reporting.

## Implementation

Aggregate device health scores. Calculate composite network score.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Aggregate device health scores. Calculate composite network score.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as device_health, count(eval(status="offline")) as offline_count by network_id
| eval network_health=round(device_health - (offline_count*5), 2)
| eval health_status=case(network_health >= 85, "Healthy", network_health >= 70, "Degraded", 1=1, "Critical")
```

Understanding this SPL

**Network Health Score Aggregation and Executive Reporting (Meraki)** — Provides high-level network health metric for executive dashboards and trend reporting.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by network_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **network_health** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **health_status** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network health gauge; health trend sparkline; status KPI dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as device_health, count(eval(status="offline")) as offline_count by network_id
| eval network_health=round(device_health - (offline_count*5), 2)
| eval health_status=case(network_health >= 85, "Healthy", network_health >= 70, "Degraded", 1=1, "Critical")
```

## Visualization

Network health gauge; health trend sparkline; status KPI dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
