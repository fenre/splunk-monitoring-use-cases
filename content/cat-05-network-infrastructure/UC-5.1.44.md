---
id: "5.1.44"
title: "Broadcast Storm Detection and Mitigation (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.44 · Broadcast Storm Detection and Mitigation (Meraki MS)

## Description

Identifies and alerts on broadcast storms that can freeze network performance across all switches.

## Value

Identifies and alerts on broadcast storms that can freeze network performance across all switches.

## Implementation

Monitor broadcast traffic thresholds. Alert on sustained high broadcast rates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*broadcast*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor broadcast traffic thresholds. Alert on sustained high broadcast rates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*broadcast*"
| stats sum(packet_count) as broadcast_packets by switch_name, port_id
| where broadcast_packets > 10000
```

Understanding this SPL

**Broadcast Storm Detection and Mitigation (Meraki MS)** — Identifies and alerts on broadcast storms that can freeze network performance across all switches.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*broadcast*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, port_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where broadcast_packets > 10000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Real-time alert dashboard; time-series of broadcast packets; affected port list.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*broadcast*"
| stats sum(packet_count) as broadcast_packets by switch_name, port_id
| where broadcast_packets > 10000
```

## Visualization

Real-time alert dashboard; time-series of broadcast packets; affected port list.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
