---
id: "5.1.28"
title: "STP Topology Change Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.28 · STP Topology Change Rate

## Description

Frequent topology changes indicating Layer 2 instability.

## Value

Frequent topology changes indicating Layer 2 instability.

## Implementation

Poll BRIDGE-MIB dot1dStpTopChanges every 300s; ingest syslog for SPANTREE events. Alert when topology changes exceed 3 in 10 minutes. Correlate with root bridge changes for critical alerts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: BRIDGE-MIB (dot1dStpTopChanges), syslog STP events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll BRIDGE-MIB dot1dStpTopChanges every 300s; ingest syslog for SPANTREE events. Alert when topology changes exceed 3 in 10 minutes. Correlate with root bridge changes for critical alerts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype=snmp:stp OR sourcetype="cisco:ios") ("dot1dStpTopChanges" OR "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE")
| eval stp_event=if(match(_raw,"TOPOTCHANGE|ROOTCHANGE|dot1dStpTopChanges"),1,0)
| bin _time span=10m
| stats sum(stp_event) as topo_changes by host, _time
| where topo_changes > 3
| sort -topo_changes
```

Understanding this SPL

**STP Topology Change Rate** — Frequent topology changes indicating Layer 2 instability.

Documented **Data sources**: BRIDGE-MIB (dot1dStpTopChanges), syslog STP events. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:stp, cisco:ios. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:stp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **stp_event** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where topo_changes > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (topology changes per host), Table (host, count), Timeline.

## SPL

```spl
index=network (sourcetype=snmp:stp OR sourcetype="cisco:ios") ("dot1dStpTopChanges" OR "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE")
| eval stp_event=if(match(_raw,"TOPOTCHANGE|ROOTCHANGE|dot1dStpTopChanges"),1,0)
| bin _time span=10m
| stats sum(stp_event) as topo_changes by host, _time
| where topo_changes > 3
| sort -topo_changes
```

## Visualization

Line chart (topology changes per host), Table (host, count), Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
