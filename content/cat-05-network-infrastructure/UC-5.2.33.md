<!-- AUTO-GENERATED from UC-5.2.33.json — DO NOT EDIT -->

---
id: "5.2.33"
title: "WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.33 · WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)

## Description

Continuously monitors WAN quality metrics to detect link degradation before impacting users.

## Value

Continuously monitors WAN quality metrics to detect link degradation before impacting users.

## Implementation

Query appliance API for uplink WAN metrics. Monitor quality KPIs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api wan_metrics=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query appliance API for uplink WAN metrics. Monitor quality KPIs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" uplink=*
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(packet_loss) as avg_loss by uplink_id
| eval link_quality=case(avg_loss > 5, "Critical", avg_latency > 100, "Poor", avg_jitter > 50, "Fair", 1=1, "Good")
```

Understanding this SPL

**WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)** — Continuously monitors WAN quality metrics to detect link degradation before impacting users.

Documented **Data sources**: `sourcetype=meraki:api wan_metrics=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by uplink_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **link_quality** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" uplink=*
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(packet_loss) as avg_loss by uplink_id
| eval link_quality=case(avg_loss > 5, "Critical", avg_latency > 100, "Poor", avg_jitter > 50, "Fair", 1=1, "Good")
```

## Visualization

Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
