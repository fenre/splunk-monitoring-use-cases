<!-- AUTO-GENERATED from UC-5.1.54.json — DO NOT EDIT -->

---
id: "5.1.54"
title: "Carrier Connection Health and Network Performance (Meraki MG)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.54 · Carrier Connection Health and Network Performance (Meraki MG)

## Description

Monitors carrier connectivity and network performance metrics for backup internet links.

## Value

Monitors carrier connectivity and network performance metrics for backup internet links.

## Implementation

Monitor carrier connection and network events. Alert on issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*carrier*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor carrier connection and network events. Alert on issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*carrier*")
| stats count as event_count by event_type, carrier_name
| where event_type="connection_error" OR event_type="network_error"
```

Understanding this SPL

**Carrier Connection Health and Network Performance (Meraki MG)** — Monitors carrier connectivity and network performance metrics for backup internet links.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*carrier*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by event_type, carrier_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where event_type="connection_error" OR event_type="network_error"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki dashboard, select the same organization, site, and UTC window as the Splunk search. Open Network-wide event log or the device event log and confirm a sample event count and field (for example `event_type` or `carrier_name`) matches what you see in Splunk.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Carrier health timeline; connection error table; network performance gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*carrier*")
| stats count as event_count by event_type, carrier_name
| where event_type="connection_error" OR event_type="network_error"
```

## Visualization

Carrier health timeline; connection error table; network performance gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
