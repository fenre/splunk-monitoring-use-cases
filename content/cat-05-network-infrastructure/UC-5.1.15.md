<!-- AUTO-GENERATED from UC-5.1.15.json — DO NOT EDIT -->

---
id: "5.1.15"
title: "Environmental Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.15 · Environmental Monitoring

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with environmental monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Temperature alerts catch cooling failures before they cause device outages.

## Value

Operations teams monitor network device temperature sensors and environmental thresholds, detecting thermal risks from fan failures, HVAC issues, or airflow blockage before devices reach protective shutdown.

## Implementation

Poll ENVMON-MIB temperature sensors every 300s. Alert when >45°C.

## Detailed Implementation

### Prerequisites
* Environmental monitoring data (temperature, voltage). Data in `index=network` with syslog or SNMP. Key mnemonics: Cisco `%ENVMON-4-ALERT`, `%PLATFORM_ENV-1-TEMP_THRESH`; SNMP CISCO-ENVMON-MIB: ciscoEnvMonTemperatureStatusValue.
* Environmental monitoring: tracks device internal temperatures, inlet/outlet temperatures, and voltage levels. Exceeding thresholds causes thermal throttling and eventually protective shutdown. Often correlated with fan failures (UC-5.1.11) or HVAC issues in data center.

### Step 1 — - Configure data collection
```
# SNMP polling for environmental data
[snmp_environment]
interval = 300
sourcetype = snmp:environment
index = network
# OIDs: ciscoEnvMonTemperatureStatusValue, ciscoEnvMonTemperatureThreshold

# Cisco IOS -- temperature threshold alerts are automatic
```
Verify:
```spl
index=network earliest=-4h
| where match(_raw, "(?i)ENVMON|temperature|temp.*threshold|thermal|overheat|voltage")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Temperature and environmental monitoring:**
```spl
index=network earliest=-4h
| eval temp_c=tonumber(coalesce(ciscoEnvMonTemperatureStatusValue, temperature, temp))
| eval threshold=tonumber(coalesce(ciscoEnvMonTemperatureThreshold, temp_threshold))
| eval device=coalesce(host, device_name)
| eval sensor=coalesce(sensor_name, sensor, "chassis")
| where isnotnull(temp_c) OR match(_raw, "(?i)ENVMON.*ALERT|temp.*threshold|thermal.*shutdown|overheat")
| eval temp_pct=if(isnotnull(threshold) AND threshold > 0, round(100*temp_c/threshold, 1), null())
| bin _time span=5m
| stats avg(temp_c) as avg_temp max(temp_c) as max_temp latest(threshold) as threshold latest(temp_pct) as temp_pct by _time, device, sensor
| eval avg_temp=round(avg_temp, 1)
| eval severity=case(
    temp_pct > 95, "CRITICAL -- temperature approaching shutdown threshold",
    temp_pct > 85, "WARNING -- temperature elevated",
    max_temp > 70 AND isnotnull(max_temp), "WARNING -- high temperature reading",
    match(_raw, "(?i)thermal.*shutdown"), "CRITICAL -- thermal shutdown occurred",
    1==1, "OK")
| where severity != "OK"
| table _time, device, sensor, avg_temp, max_temp, threshold, temp_pct, severity
| sort severity, -max_temp
```

### Step 3 — - Validate
(a) CLI: `show environment temperature` -- check current sensor readings.
(b) CLI: `show environment all` -- full environmental status.
(c) Correlate with fan failure events (UC-5.1.11) and data center HVAC.

### Step 4 — - Operationalize
Dashboard ("Network -- Environmental Monitoring"):
* Row 1 -- Single-value: "Devices > 85% threshold", "Max temperature", "Thermal alerts".
* Row 2 -- Temperature timechart by device.

Alert: Critical (>95% of thermal threshold): imminent shutdown risk.

### Step 5 — - Troubleshooting

* **Rising temperature trend** -- Check: (1) fan status (UC-5.1.11), (2) blocked airflow (cable management, blanking panels), (3) data center HVAC status, (4) adjacent high-heat devices.

* **Thermal shutdown** -- Device shut down to protect hardware. After cooling, device will restart. Investigate root cause: fan failure, HVAC failure, or excessive load.

* **Voltage alerts** -- May indicate failing power supply or unstable power feed. Check UPS output voltage and PSU status.

## SPL

```spl
index=network sourcetype="snmp:environment"
| stats latest(ciscoEnvMonTemperatureValue) as temp_c by host | where temp_c > 45
```

## Visualization

Gauge per device, Line chart (trending), Table.

## Known False Positives

Datacenter temperature and humidity often swing during CRAC work, door propping, or seasonal load—pair alerts with BMS or site tickets.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
