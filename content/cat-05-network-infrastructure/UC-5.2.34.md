<!-- AUTO-GENERATED from UC-5.2.34.json — DO NOT EDIT -->

---
id: "5.2.34"
title: "Internet Uplink Failover Events and Recovery Time (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.34 · Internet Uplink Failover Events and Recovery Time (Meraki MX)

## Description

Tracks failover events, recovery time, and uplink behavior to ensure high availability.

## Value

Tracks failover events, recovery time, and uplink behavior to ensure high availability.

## Implementation

Monitor failover and recovery events from syslog. Calculate recovery MTTR.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*failover*" OR signature="*recovery*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor failover and recovery events from syslog. Calculate recovery MTTR.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*failover*" OR signature="*recovery*")
| stats count as failover_count, latest(recovery_time) as recovery_duration by uplink_id, failure_reason
| where failover_count > 0
```

Understanding this SPL

**Internet Uplink Failover Events and Recovery Time (Meraki MX)** — Tracks failover events, recovery time, and uplink behavior to ensure high availability.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*failover*" OR signature="*recovery*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by uplink_id, failure_reason** so each row reflects one combination of those dimensions.
• Filters the current rows with `where failover_count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm VPN paths, tunnel states, uplinks, and device names you expect there match the Splunk view.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Failover timeline; recovery time gauge; uplink failure cause pie chart.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*failover*" OR signature="*recovery*")
| stats count as failover_count, latest(recovery_time) as recovery_duration by uplink_id, failure_reason
| where failover_count > 0
```

## Visualization

Failover timeline; recovery time gauge; uplink failure cause pie chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
