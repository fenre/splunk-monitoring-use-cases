---
id: "5.1.35"
title: "LLDP / CDP Neighbor Change Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.35 · LLDP / CDP Neighbor Change Detection

## Description

Unexpected topology changes in cabling/connections.

## Value

Unexpected topology changes in cabling/connections.

## Implementation

Poll LLDP-MIB lldpRemTable and CISCO-CDP-MIB; ingest syslog for CDP/LLDP neighbor change events. Baseline neighbor table; alert on unexpected changes (new/removed neighbors). Useful for change validation and cable swap detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: LLDP-MIB (lldpRemTable), CISCO-CDP-MIB, syslog CDP/LLDP events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll LLDP-MIB lldpRemTable and CISCO-CDP-MIB; ingest syslog for CDP/LLDP neighbor change events. Baseline neighbor table; alert on unexpected changes (new/removed neighbors). Useful for change validation and cable swap detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype=snmp:lldp OR sourcetype=snmp:cdp OR sourcetype="cisco:ios") ("lldpRem" OR "CDP-4-NATIVE" OR "LLDP" OR "neighbor")
| rex "neighbor (?<neighbor>\S+)|lldpRemSysName[=:]\s*(?<neighbor>\S+)|port (?<port>\S+)"
| bin _time span=1h
| stats dc(neighbor) as neighbor_changes, values(neighbor) as neighbors by host, port, _time
| where neighbor_changes > 1
| table host port _time neighbor_changes neighbors
```

Understanding this SPL

**LLDP / CDP Neighbor Change Detection** — Unexpected topology changes in cabling/connections.

Documented **Data sources**: LLDP-MIB (lldpRemTable), CISCO-CDP-MIB, syslog CDP/LLDP events. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:lldp, snmp:cdp, cisco:ios. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:lldp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, port, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where neighbor_changes > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **LLDP / CDP Neighbor Change Detection**): table host port _time neighbor_changes neighbors


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, port, changes), Timeline, Single value (unexpected changes).

## SPL

```spl
index=network (sourcetype=snmp:lldp OR sourcetype=snmp:cdp OR sourcetype="cisco:ios") ("lldpRem" OR "CDP-4-NATIVE" OR "LLDP" OR "neighbor")
| rex "neighbor (?<neighbor>\S+)|lldpRemSysName[=:]\s*(?<neighbor>\S+)|port (?<port>\S+)"
| bin _time span=1h
| stats dc(neighbor) as neighbor_changes, values(neighbor) as neighbors by host, port, _time
| where neighbor_changes > 1
| table host port _time neighbor_changes neighbors
```

## Visualization

Table (host, port, changes), Timeline, Single value (unexpected changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
