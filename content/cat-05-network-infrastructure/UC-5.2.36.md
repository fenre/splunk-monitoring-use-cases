<!-- AUTO-GENERATED from UC-5.2.36.json — DO NOT EDIT -->

---
id: "5.2.36"
title: "Warm Spare Failover and Appliance Redundancy (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.36 · Warm Spare Failover and Appliance Redundancy (Meraki MX)

## Description

Ensures warm spare failover mechanism is operational and redundancy is maintained.

## Value

Ensures warm spare failover mechanism is operational and redundancy is maintained.

## Implementation

Monitor HA/warm spare events. Alert on status != "active/standby".

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*warm spare*" OR signature="*HA*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor HA/warm spare events. Alert on status != "active/standby".

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*warm spare*" OR signature="*HA*" OR signature="*redundancy*")
| stats latest(ha_status) as redundancy_status, count as status_change_count by appliance_pair
| where ha_status!="active/standby"
```

Understanding this SPL

**Warm Spare Failover and Appliance Redundancy (Meraki MX)** — Ensures warm spare failover mechanism is operational and redundancy is maintained.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*warm spare*" OR signature="*HA*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by appliance_pair** so each row reflects one combination of those dimensions.
• Filters the current rows with `where ha_status!="active/standby"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm VPN paths, tunnel states, uplinks, and device names you expect there match the Splunk view.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: HA status dashboard; failover timeline; redundancy health gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*warm spare*" OR signature="*HA*" OR signature="*redundancy*")
| stats latest(ha_status) as redundancy_status, count as status_change_count by appliance_pair
| where ha_status!="active/standby"
```

## Visualization

HA status dashboard; failover timeline; redundancy health gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
