---
id: "1.4.9"
title: "Out-of-Band Sensor Threshold Breach (IPMI)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.4.9 · Out-of-Band Sensor Threshold Breach (IPMI)

## Description

IPMI sensor events (temperature, voltage, fan) indicate environmental or hardware problems before they cause crashes. Critical for datacenter and server health.

## Value

IPMI sensor events (temperature, voltage, fan) indicate environmental or hardware problems before they cause crashes. Critical for datacenter and server health.

## Implementation

Create scripted input: `ipmitool sdr type temperature` (and voltage, fan). Parse thresholds and current readings. Forward IPMI SEL for discrete events. Alert on Critical/Warning threshold breach.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Unix and Linux (scripted input), IPMI.
• Ensure the following data sources are available: `ipmitool sdr`, IPMI SEL (System Event Log).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `ipmitool sdr type temperature` (and voltage, fan). Parse thresholds and current readings. Forward IPMI SEL for discrete events. Alert on Critical/Warning threshold breach.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=ipmi_sdr host=*
| search sensor_type="Temperature" OR sensor_type="Voltage" OR sensor_type="Fan"
| eval status=case(sensor_reading >= upper_critical, "Critical", sensor_reading >= upper_non_critical, "Warning", 1=1, "OK")
| where status != "OK"
| table _time host sensor_name sensor_reading upper_critical status
```

Understanding this SPL

**Out-of-Band Sensor Threshold Breach (IPMI)** — IPMI sensor events (temperature, voltage, fan) indicate environmental or hardware problems before they cause crashes. Critical for datacenter and server health.

Documented **Data sources**: `ipmitool sdr`, IPMI SEL (System Event Log). **App/TA** (typical add-on context): Splunk Add-on for Unix and Linux (scripted input), IPMI. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: ipmi_sdr. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=ipmi_sdr. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where status != "OK"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Out-of-Band Sensor Threshold Breach (IPMI)**): table _time host sensor_name sensor_reading upper_critical status


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauges per sensor, Table of breached sensors, Timeline of SEL events.

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
index=hardware sourcetype=ipmi_sdr host=*
| search sensor_type="Temperature" OR sensor_type="Voltage" OR sensor_type="Fan"
| eval status=case(sensor_reading >= upper_critical, "Critical", sensor_reading >= upper_non_critical, "Warning", 1=1, "OK")
| where status != "OK"
| table _time host sensor_name sensor_reading upper_critical status
```

## Visualization

Gauges per sensor, Table of breached sensors, Timeline of SEL events.

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
