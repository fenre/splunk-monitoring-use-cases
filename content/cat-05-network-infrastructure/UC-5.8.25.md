<!-- AUTO-GENERATED from UC-5.8.25.json — DO NOT EDIT -->

---
id: "5.8.25"
title: "SNMP Trap Storm Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.25 · SNMP Trap Storm Detection

## Description

Excessive SNMP traps from a device indicating failure cascade.

## Value

Excessive SNMP traps from a device indicating failure cascade.

## Implementation

Configure Splunk SNMP trap input or forward traps from snmptrapd. Parse trap OID and host. Alert when trap rate from a single device exceeds 100/min or 3 standard deviations above baseline. Trap storms often indicate device failure, link flapping, or misconfiguration.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input (trap receiver).
• Ensure the following data sources are available: snmptrapd, Splunk SNMP trap input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk SNMP trap input or forward traps from snmptrapd. Parse trap OID and host. Alert when trap rate from a single device exceeds 100/min or 3 standard deviations above baseline. Trap storms often indicate device failure, link flapping, or misconfiguration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmptrap
| bin _time span=1m
| stats count as trap_count by host, _time
| eventstats avg(trap_count) as avg_traps, stdev(trap_count) as std_traps by host
| where trap_count > (avg_traps + 3*std_traps) OR trap_count > 100
| sort -trap_count
```

Understanding this SPL

**SNMP Trap Storm Detection** — Excessive SNMP traps from a device indicating failure cascade.

Documented **Data sources**: snmptrapd, Splunk SNMP trap input. **App/TA** (typical add-on context): SNMP modular input (trap receiver). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmptrap. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmptrap. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where trap_count > (avg_traps + 3*std_traps) OR trap_count > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

SNMP traps are usually not in the CIM Alerts model without tagging; treat this as raw sourcetype validation.


Step 3 — Validate
Generate a test trap or poll from a lab device, confirm it lands with the expected `sourcetype` (`snmp:trap`, `snmp:*`, or your normalized name) and that host and trap fields parse; compare a burst window to the NMS on the same device.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (traps per host over time), Table (host, count, threshold), Single value (devices in storm).

## SPL

```spl
index=network sourcetype=snmptrap
| bin _time span=1m
| stats count as trap_count by host, _time
| eventstats avg(trap_count) as avg_traps, stdev(trap_count) as std_traps by host
| where trap_count > (avg_traps + 3*std_traps) OR trap_count > 100
| sort -trap_count
```

## Visualization

Line chart (traps per host over time), Table (host, count, threshold), Single value (devices in storm).

## References

- [Cisco ThousandEyes App for Splunk](https://splunkbase.splunk.com/app/7719)
