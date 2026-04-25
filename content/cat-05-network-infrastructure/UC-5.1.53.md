<!-- AUTO-GENERATED from UC-5.1.53.json — DO NOT EDIT -->

---
id: "5.1.53"
title: "Cellular Data Usage and Overage Monitoring (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.53 · Cellular Data Usage and Overage Monitoring (Meraki MG)

## Description

Tracks cellular data consumption to manage carrier costs and prevent overages.

## Value

Tracks cellular data consumption to manage carrier costs and prevent overages.

## Implementation

Query MG API for data usage metrics. Track monthly consumption.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MG data_usage=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MG API for data usage metrics. Track monthly consumption.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG data_usage=*
| stats sum(data_usage) as total_data_usage_mb by cellular_gateway_id
| eval overage_alert=if(total_data_usage_mb > 100000, "Yes", "No")
```

Understanding this SPL

**Cellular Data Usage and Overage Monitoring (Meraki MG)** — Tracks cellular data consumption to manage carrier costs and prevent overages.

Documented **Data sources**: `sourcetype=meraki:api device_type=MG data_usage=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cellular_gateway_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **overage_alert** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
In the Meraki dashboard, select the same organization, site, and UTC window as the Splunk search. Open Network-wide event log or the device event log and confirm a sample event count and field (for example `event_type` or `carrier_name`) matches what you see in Splunk.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Data usage gauge per gateway; consumption timeline; overage alert table.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG data_usage=*
| stats sum(data_usage) as total_data_usage_mb by cellular_gateway_id
| eval overage_alert=if(total_data_usage_mb > 100000, "Yes", "No")
```

## Visualization

Data usage gauge per gateway; consumption timeline; overage alert table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
