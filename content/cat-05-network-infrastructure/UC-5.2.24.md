<!-- AUTO-GENERATED from UC-5.2.24.json — DO NOT EDIT -->

---
id: "5.2.24"
title: "Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.24 · Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)

## Description

Measures the impact of traffic shaping policies on bandwidth distribution and priority.

## Value

Measures the impact of traffic shaping policies on bandwidth distribution and priority.

## Implementation

Extract priority_queue field from flow logs. Measure bandwidth by priority.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract priority_queue field from flow logs. Measure bandwidth by priority.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow priority_queue=*
| stats sum(bytes) as total_bytes, avg(latency) as avg_latency by priority_queue
| eval efficiency=round(total_bytes/sum(total_bytes)*100, 2)
```

Understanding this SPL

**Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)** — Measures the impact of traffic shaping policies on bandwidth distribution and priority.

Documented **Data sources**: `sourcetype=meraki type=flow sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by priority_queue** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **efficiency** — often to normalize units, derive a ratio, or prepare for thresholds.

Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow priority_queue=*
| stats sum(bytes) as total_bytes, avg(latency) as avg_latency by priority_queue
| eval efficiency=round(total_bytes/sum(total_bytes)*100, 2)
```

## Visualization

Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
