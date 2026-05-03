<!-- AUTO-GENERATED from UC-5.11.9.json — DO NOT EDIT -->

---
id: "5.11.9"
title: "Hardware Component Health (Fan, PSU, Temperature)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.9 · Hardware Component Health (Fan, PSU, Temperature)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault

*We help you see hot gear or sick fans and power supplies early, so you can fix cooling or swap parts before the box throttles or fails.*

---

## Description

Environmental monitoring via SNMP Entity-MIB polling is slow and often unreliable. gNMI streaming of `/components/component/state` provides real-time temperature, fan speed, and power supply status. A failing fan in a top-of-rack switch triggers thermal throttling within minutes — early detection prevents performance degradation and emergency hardware swaps during business hours.

## Value

Network operations teams monitor hardware health (temperature, fans, PSUs) via structured gNMI telemetry, maintaining cooling redundancy, predicting thermal issues, and preventing environmental-related outages.

## Implementation

Subscribe to `/components/component/state` at 60s intervals. Filter for component types FAN, POWER_SUPPLY, and SENSOR. Set thresholds per component type: chassis inlet >40°C warning, ASIC >85°C critical, fan speed <2000 RPM warning. Alert on PSU state changes (redundancy loss). Track temperature trends to detect environmental issues (HVAC failure, hot aisle containment breach).

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with SAMPLE subscription to hardware component health. OpenConfig paths: `/components/component/state/temperature` for temperature sensors, `/components/component/fan/state` for fan speed and status, `/components/component/power-supply/state` for PSU status. Sample interval: 60 seconds (hardware parameters change slowly).
- Understanding hardware health monitoring: network devices have multiple temperature sensors (CPU, line cards, ambient, exhaust), redundant fans (typically N+1 — can survive one fan failure), and redundant PSUs (typically 1+1 — can survive one PSU failure). Monitoring these via gNMI provides structured, machine-readable data versus parsing unstructured syslog messages.
- Temperature thresholds vary by component: CPU junction (warning: 85°C, critical: 95°C), intake/ambient (warning: 35°C, critical: 45°C), exhaust (warning: 55°C, critical: 65°C). Build a `hardware_thresholds.csv` lookup: `component_type,warn_temp,alarm_temp` or use vendor-specified thresholds from the device DOM (Digital Optical Monitoring) when available.
- Vendor-specific paths: Cisco IOS-XR: `Cisco-IOS-XR-envmon-oper:environment-monitoring`; NX-OS: OpenConfig `/components` generally supported; Arista EOS: OpenConfig supported; Juniper: `junos-chassis-state`.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_components_temp"
  origin = "openconfig"
  path = "/components/component/state/temperature"
  subscription_mode = "sample"
  sample_interval = "60s"

[[inputs.gnmi.subscription]]
  name = "openconfig_components_fan"
  origin = "openconfig"
  path = "/components/component/fan/state"
  subscription_mode = "sample"
  sample_interval = "60s"

[[inputs.gnmi.subscription]]
  name = "openconfig_components_psu"
  origin = "openconfig"
  path = "/components/component/power-supply/state"
  subscription_mode = "sample"
  sample_interval = "60s"
```

Verify data:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics
| search metric_name="openconfig_components*"
```

### Step 2 — Create the search and alert

**Primary search — Temperature monitoring with threshold evaluation:**
```spl
| mstats latest("openconfig_components_temp.instant") AS temp_c WHERE index=gnmi_metrics BY host, component_name span=5m
| lookup hardware_thresholds.csv component_type as component_name OUTPUT warn_temp alarm_temp
| eval warn=coalesce(warn_temp, 75)
| eval alarm=coalesce(alarm_temp, 85)
| eval status=case(temp_c > alarm, "ALARM", temp_c > warn, "WARNING", 1==1, "OK")
| where status!="OK"
| sort -temp_c
```

#### Understanding this SPL: Evaluates every temperature sensor against component-specific thresholds. Sensors exceeding the alarm threshold indicate imminent hardware damage or thermal shutdown. Warning thresholds indicate environmental issues (failed fan, hot aisle, blocked airflow) that should be addressed before they become critical.

**Fan status and speed monitoring:**
```spl
| mstats latest("openconfig_components_fan.speed") AS fan_speed latest("openconfig_components_fan.status") AS fan_status WHERE index=gnmi_metrics BY host, component_name span=5m
| eval fan_state=case(fan_status==1, "OK", fan_status==0, "FAILED", isnotnull(fan_speed) AND fan_speed==0, "STOPPED", 1==1, "Unknown")
| where fan_state!="OK"
| eval impact=case(fan_state=="FAILED" OR fan_state=="STOPPED", "N+1 redundancy lost — replace ASAP", 1==1, "Monitor")
| sort host, component_name
```

#### Understanding this SPL: In N+1 fan configurations, a single fan failure is survivable but reduces cooling redundancy. A second fan failure typically triggers thermal shutdown. A failed fan that's not replaced promptly is a ticking time bomb, especially in warm environments.

**PSU status and redundancy monitoring:**
```spl
| mstats latest("openconfig_components_psu.enabled") AS psu_enabled latest("openconfig_components_psu.capacity") AS psu_watts WHERE index=gnmi_metrics BY host, component_name span=5m
| eval psu_state=case(psu_enabled==1, "OK", psu_enabled==0, "DISABLED/FAILED", isnull(psu_enabled), "NO DATA", 1==1, "Unknown")
| stats count AS total_psus sum(eval(if(psu_state=="OK", 1, 0))) AS healthy_psus by host
| eval redundancy=case(healthy_psus >= total_psus, "Full Redundancy", healthy_psus >= 1, "Degraded (single PSU)", 1==1, "NO POWER REDUNDANCY")
| where redundancy!="Full Redundancy"
| sort redundancy
```

#### Understanding this SPL: Tracks PSU health and redundancy status. In 1+1 configurations, one PSU failure means no redundancy — the next PSU failure causes a full device outage. Detect degraded redundancy before it matters.

**Temperature trending for environmental capacity planning:**
```spl
| mstats avg("openconfig_components_temp.instant") AS temp_c WHERE index=gnmi_metrics BY host, component_name span=1h earliest=-30d
| eventstats first(temp_c) AS baseline_temp by host, component_name
| eval temp_increase=round(temp_c - baseline_temp, 1)
| where temp_increase > 5
| sort -temp_increase
```

### Step 3 — Validate
(a) On the device: `show environment temperature` (Cisco), `show system environment temperature` (Arista), `show chassis environment` (Juniper). Compare sensor readings with `mstats` values.
(b) Verify fan status: `show environment fan`. If a fan is reported as failed, verify it appears in the gNMI alert.
(c) PSU check: `show environment power`. Verify redundancy status matches the Splunk search output.

### Step 4 — Operationalize
Dashboard ("Network — Hardware Health"):
- Row 1 — Single-value tiles: "Temperature alarms", "Failed fans", "PSU redundancy lost", "Devices with issues".
- Row 2 — Table: host, component, current temp, status. Color-coded (green/yellow/red).
- Row 3 — Timechart: selected device temperature sensors over 7 days (for trend analysis).
- Row 4 — Fan and PSU status grid: one cell per device, color-coded by redundancy status.

Alerting:
- Critical (temperature > alarm threshold): page NOC — thermal shutdown imminent. Check for environmental issues (HVAC failure, hot aisle containment breach).
- Critical (PSU redundancy lost — only 1 PSU active): alert for same-day replacement.
- High (fan failure): alert for next-business-day replacement (N+1 still active).
- Warning (temperature trend increasing > 5°C over 30 days): alert facilities team — environmental capacity issue.

Runbook:
1. **Temperature alarm**: Check HVAC status in the data center. Verify fan operation. If all fans are running and HVAC is normal, the device may be overloaded (high CPU generates heat). Consider reducing workload or improving airflow.
2. **Fan failure**: Order replacement fan tray. In the interim, verify remaining fans are running at higher speed to compensate. If the device is in a warm location, consider temporary supplemental cooling.
3. **PSU failure**: Replace PSU as priority. Verify the device is on a UPS and that power capacity is adequate.

### Step 5 — Troubleshooting

- **Temperature metrics show in Celsius but thresholds are in Fahrenheit** — Standardize on Celsius (OpenConfig uses Celsius). Convert if needed: `| eval temp_f=temp_c*9/5+32`.

- **Fan speed reported as RPM instead of percentage** — Some platforms report absolute RPM, others report percentage of max. Normalize in the lookup or search.

- **PSU capacity not available** — Not all platforms expose power capacity via gNMI. Use SNMP (ENTITY-SENSOR-MIB) as a fallback for power metrics.

- **Component names differ between platforms** — Arista may report "Fan1/1", Cisco may report "Fan Tray 1", Juniper may report "FAN 0". Use regex or a standardization lookup to normalize component names across the fleet.

## SPL

```spl
| mstats latest("openconfig_platform.temperature_instant") AS temp_c WHERE index=gnmi_metrics BY host, name span=5m
| where temp_c > 65
| eval severity=case(temp_c > 85, "CRITICAL", temp_c > 75, "HIGH", temp_c > 65, "WARNING")
| table _time, host, name, temp_c, severity
| sort -temp_c
```

## Visualization

Gauge (temperature per component), Status grid (fan/PSU status across fabric), Line chart (temperature trend), Table (components above threshold).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
