---
id: "5.8.13"
title: "Network Device Inventory and Change Audit (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.13 · Network Device Inventory and Change Audit (Meraki)

## Description

Maintains accurate inventory of network devices and tracks hardware/software changes.

## Value

Maintains accurate inventory of network devices and tracks hardware/software changes.

## Implementation

Query devices API to build current inventory. Track additions/removals.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query devices API to build current inventory. Track additions/removals.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by device_type, network_id
| append [search index=cisco_network sourcetype="meraki:api" | stats count as org_count]
| fillnull device_count value=0
```

Understanding this SPL

**Network Device Inventory and Change Audit (Meraki)** — Maintains accurate inventory of network devices and tracks hardware/software changes.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_type, network_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Appends rows from a subsearch with `append`.
• Fills null values with `fillnull`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Inventory summary table; device count by type pie chart; change log timeline.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by device_type, network_id
| append [search index=cisco_network sourcetype="meraki:api" | stats count as org_count]
| fillnull device_count value=0
```

## Visualization

Inventory summary table; device count by type pie chart; change log timeline.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
