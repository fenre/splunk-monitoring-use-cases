<!-- AUTO-GENERATED from UC-5.11.5.json — DO NOT EDIT -->

---
id: "5.11.5"
title: "Optical Transceiver Health Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.5 · Optical Transceiver Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault

*We help you watch the little lasers and optics so a weak cable or part does not take down a whole high-speed path without warning.*

---

## Description

Optical transceivers fail gradually — Tx power drops, Rx power drifts, temperature climbs. By the time an interface goes down, the damage (packet loss, CRC errors, application impact) is already done. gNMI streaming of `/components/component` optic data at 60-second intervals enables predictive failure alerting: catch a dimming laser or overheating module hours before it causes an outage.

## Value

Network operations teams proactively detect optical transceiver degradation via power level trending, predicting failures weeks in advance and scheduling replacements during planned maintenance windows instead of reacting to 3 AM link failures.

## Implementation

Subscribe to `/components/component/transceiver/state` at 60s intervals. Optic thresholds vary by type — SFP+ typically alarms at Rx < -14 dBm, QSFP28 at Rx < -21 dBm. Set warning at 3 dB above vendor alarm threshold. Track trends to predict failure: a steady decline of 0.5 dBm/week indicates a dying laser. Cross-reference with interface errors (UC-5.11.2) to correlate optic degradation with CRC/FCS errors.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with SAMPLE subscription to OpenConfig path `/components/component/transceiver/state` or `/components/component/optical-channel/state`. Key metrics: `input-power` (receive power in dBm), `output-power` (transmit power), `laser-bias-current` (mA), `module-temperature` (degrees C). Sample interval: 60 seconds (optical parameters change slowly).
- Understanding optical power thresholds: SFP/SFP+/QSFP transceivers have vendor-specified operating ranges. Typical single-mode SFP+ (10G-LR): Tx power -1 to -8.2 dBm, Rx power -1 to -14.4 dBm. Below Rx sensitivity = link errors. Build a `transceiver_thresholds.csv` lookup: `host,name,rx_low_warn,rx_low_alarm,rx_high_alarm,tx_low_warn,tx_low_alarm,temp_high_warn,temp_high_alarm`.
- Optical degradation is the #1 root cause for CRC errors on fiber links. A transceiver with Rx power trending toward its sensitivity threshold will start producing errors weeks before it fails completely. Proactive monitoring avoids unplanned outages.
- Vendor-specific paths: Cisco IOS-XR: `Cisco-IOS-XR-controller-optics-oper:optics-oper/optics-ports/optics-port`; NX-OS: OpenConfig `/components/component` supported; Arista: OpenConfig supported; Juniper: `junos-optics`.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_transceiver"
  origin = "openconfig"
  path = "/components/component/transceiver/state"
  subscription_mode = "sample"
  sample_interval = "60s"
```

Verify data arrival:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics
| search metric_name="openconfig_transceiver*"
```
Expected: `openconfig_transceiver.input_power`, `openconfig_transceiver.output_power`, `openconfig_transceiver.laser_bias_current`, `openconfig_transceiver.temperature`.

### Step 2 — Create the search and alert

**Primary search — Optical power health with threshold evaluation:**
```spl
| mstats latest("openconfig_transceiver.input_power") AS rx_power latest("openconfig_transceiver.output_power") AS tx_power latest("openconfig_transceiver.laser_bias_current") AS bias_current latest("openconfig_transceiver.temperature") AS temp WHERE index=gnmi_metrics BY host, name span=5m
| lookup transceiver_thresholds.csv host name OUTPUT rx_low_warn rx_low_alarm tx_low_warn tx_low_alarm temp_high_warn temp_high_alarm
| eval rx_status=case(rx_power < rx_low_alarm, "ALARM-LOW", rx_power < rx_low_warn, "WARN-LOW", 1==1, "OK")
| eval tx_status=case(tx_power < tx_low_alarm, "ALARM-LOW", tx_power < tx_low_warn, "WARN-LOW", 1==1, "OK")
| eval temp_status=case(temp > temp_high_alarm, "ALARM-HIGH", temp > temp_high_warn, "WARN-HIGH", 1==1, "OK")
| where rx_status!="OK" OR tx_status!="OK" OR temp_status!="OK"
| eval worst_status=case(rx_status="ALARM-LOW" OR tx_status="ALARM-LOW" OR temp_status="ALARM-HIGH", "CRITICAL", 1==1, "WARNING")
| sort worst_status, -rx_power
```

#### Understanding this SPL: Evaluates each transceiver against its specific thresholds. A transceiver hitting the ALARM threshold is at imminent risk of link failure. WARN thresholds indicate degradation that should be scheduled for replacement. The `input_power` (Rx) is the most important metric — low Rx power means the far-end transmitter is weak, the cable is degraded, or there's a dirty connector.

**Optical degradation trending (early warning):**
```spl
| mstats avg("openconfig_transceiver.input_power") AS rx_power WHERE index=gnmi_metrics BY host, name span=1d earliest=-30d
| eventstats first(rx_power) AS initial_power by host, name
| eval degradation_dB=round(initial_power - rx_power, 2)
| where degradation_dB > 1
| eval rate_dBm_per_day=round(degradation_dB/30, 3)
| lookup transceiver_thresholds.csv host name OUTPUT rx_low_alarm
| eval days_to_alarm=if(rate_dBm_per_day > 0, round((rx_power - rx_low_alarm) / rate_dBm_per_day, 0), null())
| where isnotnull(days_to_alarm) AND days_to_alarm < 90
| sort days_to_alarm
```

#### Understanding this SPL: Tracks optical power degradation over 30 days and predicts when each transceiver will hit its alarm threshold. A transceiver losing > 1 dB over 30 days is degrading. If the predicted failure is within 90 days, schedule proactive replacement. This is true predictive maintenance — replacing optics during planned windows rather than 3 AM emergencies.

**Temperature anomaly detection:**
```spl
| mstats avg("openconfig_transceiver.temperature") AS temp WHERE index=gnmi_metrics BY host, name span=1h earliest=-7d
| eventstats avg(temp) AS avg_temp stdev(temp) AS std_temp by host, name
| where temp > avg_temp + (3 * std_temp) OR temp > 70
| eval deviation=round(temp - avg_temp, 1)
| sort -temp
```

### Step 3 — Validate
(a) On the device, check optical power: `show interface transceiver` (Arista), `show hw-module subslot transceiver` (Cisco). Compare Rx/Tx power values with `mstats` output.
(b) Verify thresholds: the `transceiver_thresholds.csv` should match the vendor datasheet for each optic type. Check `show interface transceiver detail` for vendor-specified thresholds.
(c) Cross-reference with UC-5.11.2: interfaces showing CRC errors should also show degraded Rx power in this UC.

### Step 4 — Operationalize
Dashboard ("Network — Optical Transceiver Health"):
- Row 1 — Single-value tiles: "Transceivers in ALARM", "Transceivers in WARNING", "Predicted failures (90d)", "Monitored transceivers".
- Row 2 — Table: host, interface, rx_power, tx_power, temp, rx_status, tx_status, days_to_alarm.
- Row 3 — Line chart: selected transceiver Rx power trending over 30 days with threshold lines.
- Row 4 — Temperature heatmap: all transceivers by host.

Alerting:
- Critical (Rx power at ALARM threshold): replace optic at next opportunity — link errors are imminent or already occurring.
- Warning (Rx power at WARN threshold or predicted failure within 30 days): schedule replacement during next maintenance window.
- Temperature alarm (> 70°C): check for environmental issues (hot aisle, failed fan, blocked airflow).

Runbook (owner: Network Operations):
1. **Low Rx power alarm**: First clean the fiber connectors on both ends. If power doesn't improve, try a known-good optic. If the optic is fine, test the fiber with an OTDR.
2. **Degradation trending**: Order replacement optics proactively. Schedule a maintenance window. Verify the patch cable path for excessive bends or kinks.
3. **High temperature**: Check environmental conditions in the rack. Verify fan status (UC-5.11.9). High temperature accelerates optic degradation.

### Step 5 — Troubleshooting

- **Optical power values appear as raw mW instead of dBm** — Some platforms report in milliwatts. Convert: `| eval rx_dBm=10*log(rx_power)/log(10)` (if rx_power is in mW, divide by 1000 first).

- **Missing transceiver data for some interfaces** — Not all interfaces have optical transceivers (copper ports, built-in ports). Filter to only fiber interfaces in the lookup.

- **Rx power fluctuates wildly** — This can indicate a dirty connector (intermittent contact) or a loose fiber. Clean connectors and reseat the optic.

- **Different metric names across vendors** — OpenConfig standardizes under `openconfig_transceiver`, but Cisco IOS-XR native may report as `optics_oper`. Check `| mcatalog values(metric_name) WHERE index=gnmi_metrics host=<device>` for actual names.

## SPL

```spl
| mstats latest("openconfig_platform.output_power_instant") AS tx_dbm, latest("openconfig_platform.input_power_instant") AS rx_dbm, latest("openconfig_platform.laser_bias_current_instant") AS bias_ma, latest("openconfig_platform.temperature_instant") AS temp_c WHERE index=gnmi_metrics BY host, name span=5m
| where rx_dbm < -25 OR tx_dbm < -8 OR temp_c > 75
| eval concern=case(rx_dbm < -28, "CRITICAL: Rx near failure", rx_dbm < -25, "WARNING: Rx degrading", tx_dbm < -8, "WARNING: Tx low output", temp_c > 85, "CRITICAL: Overheating", temp_c > 75, "WARNING: High temp", 1=1, "Check")
| table _time, host, name, tx_dbm, rx_dbm, bias_ma, temp_c, concern
| sort -temp_c
```

## Visualization

Table (optics near threshold), Line chart (Rx/Tx power trend over weeks), Heatmap (temperature across all ports), Gauge (worst-case margin).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
