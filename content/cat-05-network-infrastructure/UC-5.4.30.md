<!-- AUTO-GENERATED from UC-5.4.30.json — DO NOT EDIT -->

---
id: "5.4.30"
title: "Guest Network Access Patterns and Usage (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.30 · Guest Network Access Patterns and Usage (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch guest network access patterns and usage (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks guest network adoption, usage patterns, and peak times for network provisioning.

## Value

Facilities teams monitor Meraki MT environmental sensor data (temperature, humidity, air quality) at wireless infrastructure locations, detecting IDF overheating and environmental conditions that degrade equipment.

## Implementation

Filter clients API results for guest SSIDs. Track concurrent count over time.

## Detailed Implementation

### Prerequisites
- Meraki providing environmental sensor data from MR-capable sensors. Data in `index=meraki` with `sourcetype=meraki:api:sensor` or `sourcetype=meraki:events`. Key fields: `metric` (temperature, humidity, tvoc, pm2.5, noise, co2), `value`, `sensor_serial`, `network`.
- Meraki MT sensors (MT10 for temperature/humidity, MT12 for water leak detection, MT14 for temperature/humidity/indoor air quality, MT15 for indoor air quality, MT20 for door open/close, MT30 for button/automation) can report environmental conditions that affect wireless performance. High temperature in an IDF closet can cause AP overheating; humidity can cause corrosion.

### Step 1 — Configure data collection
Verify sensor data:
```spl
index=meraki (sourcetype="meraki:api:sensor" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(metric) AND isnotnull(value)
| stats latest(value) as current_value by metric, sensor_serial, network
```

### Step 2 — Create the search and alert

**Primary search — Environmental anomaly detection:**
```spl
index=meraki (sourcetype="meraki:api:sensor" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(metric) AND isnotnull(value)
| lookup meraki_sensors.csv sensor_serial OUTPUT location sensor_name threshold_high threshold_low
| eval alert_status=case(value > threshold_high, "HIGH_ALERT", value < threshold_low, "LOW_ALERT", 1==1, "NORMAL")
| where alert_status != "NORMAL"
| eval concern=case(metric="temperature" AND value > threshold_high, "Overheating — risk of equipment damage", metric="humidity" AND value > threshold_high, "High humidity — risk of condensation/corrosion", metric="tvoc" AND value > threshold_high, "Poor air quality — occupant health concern", metric="pm2.5" AND value > threshold_high, "High particulate matter", 1==1, "Threshold exceeded")
| table sensor_name, location, metric, value, threshold_high, threshold_low, alert_status, concern
| sort alert_status, -value
```

**Environmental trending:**
```spl
index=meraki (sourcetype="meraki:api:sensor" OR sourcetype="meraki:events") earliest=-24h
| where metric="temperature" AND isnotnull(value)
| bin _time span=15m
| lookup meraki_sensors.csv sensor_serial OUTPUT location
| stats avg(value) as avg_temp by _time, location
| timechart span=15m avg(avg_temp) by location
```

### Step 3 — Validate
(a) Check current sensor readings against physical thermometer/hygrometer.
(b) Open an IDF closet door and verify temperature change is reflected.
(c) Compare with Meraki Dashboard: Environmental > Sensors.

### Step 4 — Operationalize
Dashboard ("Meraki — Environmental Monitoring"):
- Row 1 — Single-value: "Active alerts", "Average temperature", "Average humidity", "Air quality index".
- Row 2 — Environmental alert table with sensor location and concern.
- Row 3 — Temperature trending by location.

Alerting:
- Critical (IDF/server room temperature > 35°C): equipment overheating — immediate action.
- Warning (humidity > 80%): condensation risk.
- Info (air quality index > threshold): ventilation review.

### Step 5 — Troubleshooting

- **Sensor not reporting** — Check battery level (MT sensors are battery-powered with multi-year life). Verify the sensor is within BLE range of an MR AP (gateway). Check Meraki Dashboard: Sensors > Monitor.

- **Temperature spikes** — Check HVAC status, UPS heat output, and equipment density. IDF closets with insufficient cooling are a common problem.

- **Data gaps** — MT sensors report periodically (not continuously). Default reporting interval is 5-10 minutes. Gaps longer than 30 minutes indicate connectivity issues.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" ssid="guest"
| stats count as guest_users by _time
| timechart avg(guest_users) as avg_concurrent_guests
```

## Visualization

Time-series of guest users; daily/weekly heatmap; trend dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
