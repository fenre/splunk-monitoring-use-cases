---
id: "5.1.3"
title: "Interface Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.3 · Interface Utilization

## Description

Saturated links cause drops and congestion. Trending enables proactive upgrades.

## Value

Saturated links cause drops and congestion. Trending enables proactive upgrades.

## Implementation

Poll 64-bit counters every 300s. Alert at 80% sustained. Use `predict` for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: SNMP IF-MIB (ifHCInOctets, ifHCOutOctets, ifSpeed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll 64-bit counters every 300s. Alert at 80% sustained. Use `predict` for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifHCInOctets) as prev_in, last(_time) as prev_time by host, ifDescr
| eval in_bps=((ifHCInOctets-prev_in)*8)/(_time-prev_time)
| eval util_pct=round(in_bps/ifSpeed*100,1) | where util_pct>80
```

Understanding this SPL

**Interface Utilization** — Saturated links cause drops and congestion. Trending enables proactive upgrades.

Documented **Data sources**: SNMP IF-MIB (ifHCInOctets, ifHCOutOctets, ifSpeed). **App/TA** (typical add-on context): SNMP Modular Input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:interface. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:interface". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `streamstats` rolls up events into metrics; results are split **by host, ifDescr** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **in_bps** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct>80` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.thruput) as thruput_bps
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
| where thruput_bps > 0
```

Understanding this CIM / accelerated SPL

**Interface Utilization** — Saturated links cause drops and congestion. Trending enables proactive upgrades.

Documented **Data sources**: SNMP IF-MIB (ifHCInOctets, ifHCOutOctets, ifSpeed). **App/TA** (typical add-on context): SNMP Modular Input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where thruput_bps > 0` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart, Gauge per critical link, Table sorted by utilization.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifHCInOctets) as prev_in, last(_time) as prev_time by host, ifDescr
| eval in_bps=((ifHCInOctets-prev_in)*8)/(_time-prev_time)
| eval util_pct=round(in_bps/ifSpeed*100,1) | where util_pct>80
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.thruput) as thruput_bps
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
| where thruput_bps > 0
```

## Visualization

Line chart, Gauge per critical link, Table sorted by utilization.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
