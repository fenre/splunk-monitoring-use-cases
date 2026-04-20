---
id: "5.4.18"
title: "Client Device Type Distribution and Compliance (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.18 · Client Device Type Distribution and Compliance (Meraki MR)

## Description

Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.

## Value

Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.

## Implementation

Use API clients endpoint to retrieve device OS and type information. Aggregate across network.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use API clients endpoint to retrieve device OS and type information. Aggregate across network.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by os_type, device_family
| eval pct=round(device_count*100/sum(device_count), 2)
| sort - device_count
```

Understanding this SPL

**Client Device Type Distribution and Compliance (Meraki MR)** — Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by os_type, device_family** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by os_type, device_family
| eval pct=round(device_count*100/sum(device_count), 2)
| sort - device_count
```

## Visualization

Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
