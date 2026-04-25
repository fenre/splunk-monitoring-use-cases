<!-- AUTO-GENERATED from UC-1.4.9.json — DO NOT EDIT -->

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

Comparing each reading to its warning and critical cutoffs flags hot, weak power, and weak airflow before a server thermal-throttles or powers off, without waiting for the operating system to notice.

## Implementation

Create scripted input: `ipmitool sdr type temperature` (and voltage, fan). Parse thresholds and current readings. Forward IPMI SEL for discrete events. Alert on Critical/Warning threshold breach.

## Detailed Implementation

Prerequisites
• Install `ipmitool` on a collector or the host, or use a vendor poll from the out-of-band network.
• Parse `sourcetype=ipmi_sdr` with `sensor_type`, `sensor_reading`, `upper_critical`, and `upper_non_critical` (names must match the search or adjust the `eval`).
• For app packaging, the add-on for Unix and Linux is often installed next to the forwarder; the IPMI work is still custom scripting into your sourcetype.

Step 1 — Configure data collection
Run `ipmitool sdr elist` or per-type SDR and normalize units. Ingest to `index=hardware` with a stable `host` value for the target server. Forward SEL in parallel if you also alert on discrete events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the `case` logic to your vendor’s semantics):

```spl
index=hardware sourcetype=ipmi_sdr host=*
| search sensor_type="Temperature" OR sensor_type="Voltage" OR sensor_type="Fan"
| eval status=case(sensor_reading >= upper_critical, "Critical", sensor_reading >= upper_non_critical, "Warning", 1=1, "OK")
| where status != "OK"
| table _time host sensor_name sensor_reading upper_critical status
```

Understanding this SPL

**Out-of-Band Sensor Threshold Breach (IPMI)** — IPMI sensor events (temperature, voltage, fan) indicate environmental or hardware problems before they cause crashes. Critical for datacenter and server health.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=ipmi_sdr`.
• `search` and `eval` build a `status` from live reading vs. thresholds.
• `table` shows breached sensors for triage.


Step 3 — Validate
On a test server, compare `ipmitool sdr` to indexed fields. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ipmi_sdr host=*
| search sensor_type="Temperature" OR sensor_type="Voltage" OR sensor_type="Fan"
| eval status=case(sensor_reading >= upper_critical, "Critical", sensor_reading >= upper_non_critical, "Warning", 1=1, "OK")
| where status != "OK"
| table _time host sensor_name sensor_reading upper_critical status
```

## CIM SPL

```spl
N/A — SDR and threshold-breach logic are not a CIM data model; use a custom `ipmi_sdr` sourcetype with parsed `sensor_reading` and `upper_*` fields.
```

## Visualization

Gauges per sensor, Table of breached sensors, Timeline of SEL events.

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
