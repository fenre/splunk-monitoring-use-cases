---
id: "5.1.2"
title: "Interface Error Rates"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.2 · Interface Error Rates

## Description

CRC errors, drops indicate cabling, transceiver, or duplex issues.

## Value

CRC errors, drops indicate cabling, transceiver, or duplex issues.

## Implementation

Poll IF-MIB (ifInErrors, ifOutErrors, ifInDiscards) at 300s. Use `streamstats` for delta. Alert on increasing counts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:interface`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll IF-MIB (ifInErrors, ifOutErrors, ifInDiscards) at 300s. Use `streamstats` for delta. Alert on increasing counts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev by host, ifDescr
| eval delta = ifInErrors - prev | where delta > 0
| table _time host ifDescr delta
```

Understanding this SPL

**Interface Error Rates** — CRC errors, drops indicate cabling, transceiver, or duplex issues.

Documented **Data sources**: `sourcetype=snmp:interface`. **App/TA** (typical add-on context): SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:interface. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:interface". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `streamstats` rolls up events into metrics; results are split **by host, ifDescr** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where delta > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Interface Error Rates**): table _time host ifDescr delta

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate), Table, Heatmap across devices.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev by host, ifDescr
| eval delta = ifInErrors - prev | where delta > 0
| table _time host ifDescr delta
```

## Visualization

Line chart (error rate), Table, Heatmap across devices.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
