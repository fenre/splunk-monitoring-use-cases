---
id: "5.2.27"
title: "NAT Pool Usage and Exhaustion Alerts (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.27 · NAT Pool Usage and Exhaustion Alerts (Meraki MX)

## Description

Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.

## Value

Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.

## Implementation

Query appliance API for NAT pool metrics. Alert on >80% utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query appliance API for NAT pool metrics. Alert on >80% utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" nat_pool_usage=*
| stats max(nat_pool_usage) as peak_nat_usage, count by nat_pool_id
| eval nat_capacity_pct=round(peak_nat_usage*100/254, 2)
| where nat_capacity_pct > 80
```

Understanding this SPL

**NAT Pool Usage and Exhaustion Alerts (Meraki MX)** — Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by nat_pool_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **nat_capacity_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where nat_capacity_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" nat_pool_usage=*
| stats max(nat_pool_usage) as peak_nat_usage, count by nat_pool_id
| eval nat_capacity_pct=round(peak_nat_usage*100/254, 2)
| where nat_capacity_pct > 80
```

## Visualization

Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
