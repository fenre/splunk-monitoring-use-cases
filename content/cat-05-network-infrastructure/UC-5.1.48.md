---
id: "5.1.48"
title: "QoS Queue Drops and Priority Violations (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.48 · QoS Queue Drops and Priority Violations (Meraki MS)

## Description

Detects QoS queue overflow and drops that indicate traffic priority issues.

## Value

Detects QoS queue overflow and drops that indicate traffic priority issues.

## Implementation

Monitor QoS-related syslog events and drops. Alert on significant drop rates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*QoS*" OR signature="*queue*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor QoS-related syslog events and drops. Alert on significant drop rates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*QoS*" OR signature="*queue*" OR signature="*drop*")
| stats sum(packets_dropped) as total_drops by switch_name, queue_id
| where total_drops > 1000
```

Understanding this SPL

**QoS Queue Drops and Priority Violations (Meraki MS)** — Detects QoS queue overflow and drops that indicate traffic priority issues.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*QoS*" OR signature="*queue*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, queue_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where total_drops > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of drops by queue; time-series of drop events; traffic distribution pie chart.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*QoS*" OR signature="*queue*" OR signature="*drop*")
| stats sum(packets_dropped) as total_drops by switch_name, queue_id
| where total_drops > 1000
```

## Visualization

Table of drops by queue; time-series of drop events; traffic distribution pie chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
