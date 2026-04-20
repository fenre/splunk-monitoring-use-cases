---
id: "5.4.5"
title: "Client Count Trending"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.5 · Client Count Trending

## Description

Client count trending informs capacity planning and AP density decisions.

## Value

Client count trending informs capacity planning and AP density decisions.

## Implementation

Poll client counts via API or SNMP. Track per AP, per SSID, and per building over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Meraki API, WLC SNMP.
• Ensure the following data sources are available: WLC/Meraki client data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll client counts via API or SNMP. Track per AP, per SSID, and per building over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="meraki:api"
| timechart span=1h dc(client_mac) as client_count by ap_name
```

Understanding this SPL

**Client Count Trending** — Client count trending informs capacity planning and AP density decisions.

Documented **Data sources**: WLC/Meraki client data. **App/TA** (typical add-on context): Meraki API, WLC SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: meraki:api. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by ap_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (clients over time), Table (AP, count), Heatmap.

## SPL

```spl
index=network sourcetype="meraki:api"
| timechart span=1h dc(client_mac) as client_count by ap_name
```

## Visualization

Line chart (clients over time), Table (AP, count), Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
