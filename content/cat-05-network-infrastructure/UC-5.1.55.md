---
id: "5.1.55"
title: "SIM Status and Plan Monitoring (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.55 · SIM Status and Plan Monitoring (Meraki MG)

## Description

Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.

## Value

Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.

## Implementation

Query MG API for SIM status and plan expiry. Alert before expiration.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MG sim_status=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MG API for SIM status and plan expiry. Alert before expiration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats latest(sim_status) as sim_status, latest(plan_expiry) as expiry_date by gateway_id, sim_id
| eval days_until_expire=round((strptime(plan_expiry, "%Y-%m-%d")-now())/86400, 0)
| where sim_status != "active" OR days_until_expire < 30
```

Understanding this SPL

**SIM Status and Plan Monitoring (Meraki MG)** — Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.

Documented **Data sources**: `sourcetype=meraki:api device_type=MG sim_status=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by gateway_id, sim_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **days_until_expire** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where sim_status != "active" OR days_until_expire < 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: SIM status table; plan expiry countdown; renewal alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats latest(sim_status) as sim_status, latest(plan_expiry) as expiry_date by gateway_id, sim_id
| eval days_until_expire=round((strptime(plan_expiry, "%Y-%m-%d")-now())/86400, 0)
| where sim_status != "active" OR days_until_expire < 30
```

## Visualization

SIM status table; plan expiry countdown; renewal alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
