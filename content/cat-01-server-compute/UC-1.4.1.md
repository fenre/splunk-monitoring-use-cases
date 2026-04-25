<!-- AUTO-GENERATED from UC-1.4.1.json — DO NOT EDIT -->

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

Seeing power, thermal, and fan problems on the management controller before the host locks up gives the data center time to swap parts in a planned window instead of during an outage.

## Implementation

Install `ipmitool` on hosts. Create scripted input: `ipmitool sensor list` (interval=300). Parse sensor name, reading, unit, and status. Alert on Critical/Non-Recoverable status. Alternatively, use SNMP to poll vendor-specific MIBs (Dell iDRAC, HP iLO, Lenovo IMM).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`), SNMP.
• Ensure the following data sources are available: IPMI sensor data via scripted input, `sourcetype=ipmi:sensor` (custom).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux or a supported out-of-band jump host, install `ipmitool` and use a scripted input: `ipmitool sensor list` (interval=300). Parse sensor name, reading, unit, and status. Alert on Critical/Non-Recoverable status. Alternatively, use SNMP to poll vendor-specific MIBs (Dell iDRAC, HPE iLO, Lenovo XCC).

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

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=ipmi:sensor`.
• `eval` flags **is_critical** from vendor or parsed status text.
• `table` and `sort` list recent critical readings for triage.


Step 3 — Validate
On a test server, run `ipmitool sensor` and compare field values to the indexed event. For SNMP-only paths, validate against the vendor’s management UI.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of critical sensors, Gauge per sensor type, Heatmap across hosts.

For scripted input examples, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ipmi:sensor
| eval is_critical = if(status="Critical" OR status="Non-Recoverable", 1, 0)
| where is_critical=1
| table _time host sensor_name reading unit status
| sort -_time
```

## CIM SPL

```spl
N/A — IPMI sensor readings are not mapped to a standard Common Information Model data model; keep the index/sourcetype search or build a private asset or metrics model.
```

## Visualization

Table of critical sensors, Gauge per sensor type, Heatmap across hosts.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
