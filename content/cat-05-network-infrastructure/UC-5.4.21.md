---
id: "5.4.21"
title: "Wireless Latency Analysis by SSID and Location (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.21 · Wireless Latency Analysis by SSID and Location (Meraki MR)

## Description

Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.

## Value

Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.

## Implementation

Use API clients endpoint with latency metric. Aggregate by SSID and AP location.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use API clients endpoint with latency metric. Aggregate by SSID and AP location.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" latency=*
| stats avg(latency) as avg_latency, max(latency) as max_latency, count by ssid, ap_name
| eval latency_sla="OK"
| eval latency_sla=if(avg_latency > 50, "Warning", latency_sla)
| eval latency_sla=if(avg_latency > 100, "Critical", latency_sla)
```

Understanding this SPL

**Wireless Latency Analysis by SSID and Location (Meraki MR)** — Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ssid, ap_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **latency_sla** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **latency_sla** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **latency_sla** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" latency=*
| stats avg(latency) as avg_latency, max(latency) as max_latency, count by ssid, ap_name
| eval latency_sla="OK"
| eval latency_sla=if(avg_latency > 50, "Warning", latency_sla)
| eval latency_sla=if(avg_latency > 100, "Critical", latency_sla)
```

## Visualization

Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
