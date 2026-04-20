---
id: "1.4.1"
title: "Hardware Sensor Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.1 · Hardware Sensor Monitoring

## Description

Temperature, voltage, and fan speed anomalies predict impending hardware failures before they cause unplanned downtime.

## Value

Temperature, voltage, and fan speed anomalies predict impending hardware failures before they cause unplanned downtime.

## Implementation

Install `ipmitool` on hosts. Create scripted input: `ipmitool sensor list` (interval=300). Parse sensor name, reading, unit, and status. Alert on Critical/Non-Recoverable status. Alternatively, use SNMP to poll vendor-specific MIBs (Dell iDRAC, HP iLO, Lenovo IMM).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`), SNMP.
• Ensure the following data sources are available: IPMI sensor data via scripted input, `sourcetype=ipmi:sensor` (custom).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install `ipmitool` on hosts. Create scripted input: `ipmitool sensor list` (interval=300). Parse sensor name, reading, unit, and status. Alert on Critical/Non-Recoverable status. Alternatively, use SNMP to poll vendor-specific MIBs (Dell iDRAC, HP iLO, Lenovo IMM).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=ipmi:sensor
| eval is_critical = if(status="Critical" OR status="Non-Recoverable", 1, 0)
| where is_critical=1
| table _time host sensor_name reading unit status
| sort -_time
```

Understanding this SPL

**Hardware Sensor Monitoring** — Temperature, voltage, and fan speed anomalies predict impending hardware failures before they cause unplanned downtime.

Documented **Data sources**: IPMI sensor data via scripted input, `sourcetype=ipmi:sensor` (custom). **App/TA** (typical add-on context): Custom scripted input (`ipmitool`), SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: ipmi:sensor. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=ipmi:sensor. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_critical** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where is_critical=1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Hardware Sensor Monitoring**): table _time host sensor_name reading unit status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of critical sensors, Gauge per sensor type, Heatmap across hosts.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ipmi:sensor
| eval is_critical = if(status="Critical" OR status="Non-Recoverable", 1, 0)
| where is_critical=1
| table _time host sensor_name reading unit status
| sort -_time
```

## Visualization

Table of critical sensors, Gauge per sensor type, Heatmap across hosts.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
