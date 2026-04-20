---
id: "5.1.52"
title: "Cellular Gateway Signal Strength Trending (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.52 · Cellular Gateway Signal Strength Trending (Meraki MG)

## Description

Monitors cellular signal strength to ensure reliable backup connectivity.

## Value

Monitors cellular signal strength to ensure reliable backup connectivity.

## Implementation

Query MG device API for signal metrics. Alert on degraded signal.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MG`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MG device API for signal metrics. Alert on degraded signal.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats avg(signal_strength) as avg_signal, min(signal_strength) as min_signal by cellular_gateway_id
| eval signal_quality=case(avg_signal > -90, "Excellent", avg_signal > -110, "Good", 1=1, "Poor")
```

Understanding this SPL

**Cellular Gateway Signal Strength Trending (Meraki MG)** — Monitors cellular signal strength to ensure reliable backup connectivity.

Documented **Data sources**: `sourcetype=meraki:api device_type=MG`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cellular_gateway_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **signal_quality** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Signal strength gauge; trend timeline; cellular quality status.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats avg(signal_strength) as avg_signal, min(signal_strength) as min_signal by cellular_gateway_id
| eval signal_quality=case(avg_signal > -90, "Excellent", avg_signal > -110, "Good", 1=1, "Poor")
```

## Visualization

Signal strength gauge; trend timeline; cellular quality status.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
