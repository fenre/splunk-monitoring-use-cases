---
id: "5.8.4"
title: "Network Device Inventory"
criticality: "low"
splunkPillar: "Security"
---

# UC-5.8.4 · Network Device Inventory

## Description

Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.

## Value

Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.

## Implementation

Poll SNMP sysDescr, sysName, sysLocation from all devices. Cross-reference with NMS discovery exports. Maintain inventory lookup for enrichment.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined sources (NMS APIs, SNMP sysDescr).
• Ensure the following data sources are available: NMS discovery, SNMP polling.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll SNMP sysDescr, sysName, sysLocation from all devices. Cross-reference with NMS discovery exports. Maintain inventory lookup for enrichment.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:system"
| stats latest(sysDescr) as description, latest(sysLocation) as location by host
| table host description location
```

Understanding this SPL

**Network Device Inventory** — Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.

Documented **Data sources**: NMS discovery, SNMP polling. **App/TA** (typical add-on context): Combined sources (NMS APIs, SNMP sysDescr). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:system. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Network Device Inventory**): table host description location


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, model, location, version), Pie chart (by model/vendor).

## SPL

```spl
index=network sourcetype="snmp:system"
| stats latest(sysDescr) as description, latest(sysLocation) as location by host
| table host description location
```

## Visualization

Table (device, model, location, version), Pie chart (by model/vendor).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
