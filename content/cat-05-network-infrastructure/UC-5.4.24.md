<!-- AUTO-GENERATED from UC-5.4.24.json — DO NOT EDIT -->

---
id: "5.4.24"
title: "Wireless Health Score Trending (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.24 · Wireless Health Score Trending (Meraki MR)

## Description

Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.

## Value

Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.

## Implementation

Pull health_score metric from MR devices API. Aggregate across network.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MR`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Pull health_score metric from MR devices API. Aggregate across network.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats avg(health_score) as network_health, min(health_score) as worst_ap, count(eval(health_score<80)) as unhealthy_aps by network_id
| eval health_status=if(network_health >= 85, "Healthy", if(network_health >= 70, "Degraded", "Critical"))
```

Understanding this SPL

**Wireless Health Score Trending (Meraki MR)** — Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.

Documented **Data sources**: `sourcetype=meraki:api device_type=MR`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by network_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **health_status** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats avg(health_score) as network_health, min(health_score) as worst_ap, count(eval(health_score<80)) as unhealthy_aps by network_id
| eval health_status=if(network_health >= 85, "Healthy", if(network_health >= 70, "Degraded", "Critical"))
```

## Visualization

Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
