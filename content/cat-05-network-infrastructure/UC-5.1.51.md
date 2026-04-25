<!-- AUTO-GENERATED from UC-5.1.51.json — DO NOT EDIT -->

---
id: "5.1.51"
title: "Uplink Health and Failover Events (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.51 · Uplink Health and Failover Events (Meraki MS)

## Description

Monitors primary/secondary uplink status to detect failover events and connection issues.

## Value

Monitors primary/secondary uplink status to detect failover events and connection issues.

## Implementation

Monitor uplink status change events in syslog. Alert on failover.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*Uplink*" OR signature="*failover*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor uplink status change events in syslog. Alert on failover.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Uplink*" OR signature="*failover*")
| stats count as failover_count by uplink_name, event_type
| where failover_count > 0
```

Understanding this SPL

**Uplink Health and Failover Events (Meraki MS)** — Monitors primary/secondary uplink status to detect failover events and connection issues.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*Uplink*" OR signature="*failover*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by uplink_name, event_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where failover_count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki dashboard, select the same organization, site, and UTC window as the Splunk search. Open Network-wide event log or the device event log and confirm a sample event count and field (for example `event_type` or `carrier_name`) matches what you see in Splunk.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Uplink status dashboard; failover event timeline; connection health gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Uplink*" OR signature="*failover*")
| stats count as failover_count by uplink_name, event_type
| where failover_count > 0
```

## Visualization

Uplink status dashboard; failover event timeline; connection health gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
