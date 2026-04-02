## 14. IoT & Operational Technology (OT)

### 14.1 Building Management Systems (BMS)

**Primary App/TA:** MQTT inputs, Modbus TA, SNMP, BACnet gateways, custom API inputs.

---

### UC-14.1.1 · HVAC Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** HVAC issues in data centers risk equipment damage; in buildings they affect occupant comfort and energy costs.
- **App/TA:** Modbus TA, MQTT input, BMS API
- **Data Sources:** BACnet/Modbus sensors (temperature setpoint, actual, supply/return air)
- **SPL:**
```spl
index=bms sourcetype="modbus:hvac"
| eval deviation=abs(actual_temp-setpoint_temp)
| where deviation > 3
| table _time, zone, setpoint_temp, actual_temp, deviation
```
- **Implementation:** Connect BMS to Splunk via MQTT broker or Modbus gateway. Ingest setpoints and actuals per zone. Alert when deviation exceeds 3°F/2°C for sustained period. Track energy consumption per HVAC unit.
- **Visualization:** Line chart (setpoint vs actual per zone), Heatmap (zone × temperature), Single value (zones out of spec).
- **CIM Models:** N/A

---

### UC-14.1.5 · Elevator/Equipment Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Equipment fault codes enable predictive maintenance, reducing downtime and extending equipment life.
- **App/TA:** BMS integration, MQTT
- **Data Sources:** BMS event logs, equipment fault codes
- **SPL:**
```spl
index=bms sourcetype="bms:faults"
| stats count by equipment_id, fault_code, description
| sort -count
```
- **Implementation:** Forward BMS fault events to Splunk. Map fault codes to descriptions via lookup. Track fault frequency per equipment. Alert on critical faults. Report on recurring issues for maintenance planning.
- **Visualization:** Table (equipment faults), Bar chart (faults by equipment), Timeline (fault events).
- **CIM Models:** N/A

---

### UC-14.1.6 · Environmental Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Temperature/humidity exceedances in data centers risk equipment damage; in labs they invalidate experiments. Compliance monitoring is mandatory.
- **App/TA:** Environmental sensor inputs (SNMP, MQTT)
- **Data Sources:** Environmental sensors (temperature, humidity, differential pressure)
- **SPL:**
```spl
index=environment sourcetype="sensor:environmental"
| where temp_f > 80 OR temp_f < 64 OR humidity_pct > 60 OR humidity_pct < 40
| table _time, zone, sensor, temp_f, humidity_pct
```
- **Implementation:** Deploy environmental sensors per ASHRAE guidelines. Ingest via SNMP or MQTT. Alert immediately on out-of-range conditions. Log compliance data for audit. Track seasonal patterns for cooling optimization.
- **Visualization:** Heatmap (zone × temperature), Line chart (temp/humidity trend), Single value (zones in compliance %), Gauge (current temp per zone).
- **CIM Models:** N/A

---

### UC-14.1.7 · LoRaWAN Gateway Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Gateway uplink/downlink success rate and RSSI trending indicate network coverage and reliability. Degraded gateways cause packet loss and affect IoT application availability.
- **App/TA:** Custom (LoRaWAN Network Server API, e.g. ChirpStack)
- **Data Sources:** LoRaWAN NS API (gateway stats, rx/tx packets)
- **SPL:**
```spl
index=iot sourcetype="lorawan:gateway_stats"
| eval uplink_success_rate=if(uplink_total>0, (uplink_ok/uplink_total)*100, null), downlink_success_rate=if(downlink_total>0, (downlink_ok/downlink_total)*100, null)
| stats avg(rssi) as avg_rssi, avg(uplink_success_rate) as uplink_pct, avg(downlink_success_rate) as downlink_pct by gateway_id, _time span=1h
| where uplink_pct < 95 OR downlink_pct < 95 OR avg_rssi < -120
| table gateway_id, avg_rssi, uplink_pct, downlink_pct
```
- **Implementation:** Poll LoRaWAN Network Server API (ChirpStack, TTN, etc.) for gateway statistics. Ingest rx/tx packet counts, success/failure, and RSSI per gateway. Configure HEC or scripted input to forward JSON to Splunk. Alert when uplink or downlink success rate drops below 95% or RSSI trends below -120 dBm. Track gateway health for capacity planning.
- **Visualization:** Table (gateways with degraded success rate), Line chart (RSSI trend by gateway), Gauge (uplink/downlink success %), Status grid (gateway × health).
- **CIM Models:** N/A

---

### UC-14.1.8 · Modbus Device Communication Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Poll timeout tracking across Modbus TCP/RTU slaves identifies communication failures before they impact process control. High failure rates indicate network issues, slave overload, or misconfiguration.
- **App/TA:** Splunk Edge Hub, custom (Modbus polling logs)
- **Data Sources:** Modbus gateway/master logs (poll success/failure per slave address)
- **SPL:**
```spl
index=ot sourcetype="modbus:poll_log" OR sourcetype="modbus:gateway"
| rex "slave=(?<slave_addr>\d+)|address=(?<slave_addr>\d+)|(?<status>success|timeout|failure|error)"
| eval poll_ok=if(lower(status)="success", 1, 0), poll_fail=if(lower(status)!="success" AND status!="", 1, 0)
| stats sum(poll_ok) as ok, sum(poll_fail) as fail by slave_addr, host, _time span=15m
| eval total=ok+fail, failure_rate_pct=if(total>0, (fail/total)*100, 0)
| where failure_rate_pct > 10 OR fail > 5
| table slave_addr, host, ok, fail, failure_rate_pct
```
- **Implementation:** Configure Modbus gateway or Edge Hub Modbus connector to log poll success/failure per slave address. Parse slave address and status from logs. Ingest via syslog or file monitor. Alert when failure rate exceeds 10% over 15 minutes or more than 5 consecutive failures for a critical slave. Correlate with network and PLC health.
- **Visualization:** Table (slaves with high failure rate), Line chart (failure rate trend by slave), Bar chart (top failing slaves), Single value (slaves in spec %).
- **CIM Models:** N/A

---

### UC-14.1.9 · OPC-UA Server Session Count and Subscription Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Session limits and subscription keep-alive failures indicate OPC-UA server capacity and client connectivity. Exceeding session limits or subscription failures cause data gaps and break real-time monitoring.
- **App/TA:** Splunk Edge Hub, custom (OPC-UA server diagnostics)
- **Data Sources:** OPC-UA server diagnostics node (ServerDiagnosticsSummary)
- **SPL:**
```spl
index=ot sourcetype="opcua:diagnostics" OR sourcetype="opcua:server"
| eval session_pct=if(session_limit>0, (current_sessions/session_limit)*100, null), subscription_ok=if(subscription_failures==0 OR isnull(subscription_failures), 1, 0)
| where session_pct > 85 OR current_sessions >= session_limit OR subscription_failures > 0
| table _time, server_endpoint, current_sessions, session_limit, session_pct, subscription_count, subscription_failures, rejected_session_count
```
- **Implementation:** Read OPC-UA ServerDiagnosticsSummary node (standard diagnostics object) via Edge Hub OPC-UA connector or custom client. Ingest current session count, session limit, subscription count, and subscription failure metrics. Poll every 1–5 minutes. Alert when session count exceeds 85% of limit, subscription failures occur, or rejected session count increases. Track trends for capacity planning.
- **Visualization:** Gauge (session utilization %), Table (servers with subscription failures), Line chart (session count and subscription health trend), Single value (OPC-UA servers healthy).
- **CIM Models:** N/A


#### 14.1 SNMP & Network Devices

**Primary App/TA:** SNMP Modular Input (TA), SNMP trap receiver (syslog/HEC), vendor NMS exports.

---

### UC-14.1.10 · SNMP Trap Storm Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Trap floods overwhelm collectors and obscure real faults; rapid detection enables rate limiting and upstream device triage.
- **App/TA:** SNMP trap receiver, `snmptrapd` → syslog
- **Data Sources:** `index=network` `sourcetype="snmp:trap"` or `snmptrapd:syslog`
- **SPL:**
```spl
index=network sourcetype IN ("snmp:trap","snmptrapd:syslog")
| timechart span=1m count as trap_rate by device_ip
| where trap_rate > 500
```
- **Implementation:** Baseline traps/min per agent IP. Alert when rate exceeds 5× baseline or absolute threshold. Correlate with link flaps or misconfigured threshold on managed device.
- **Visualization:** Line chart (trap rate by device), Single value (peak traps/min), Table (top storm sources).
- **CIM Models:** N/A

---

### UC-14.1.11 · Device MIB Polling Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Failed GET/GETNEXT/WALK cycles mean stale metrics and blind spots in capacity management.
- **App/TA:** SNMP TA (modular input), polling audit logs
- **Data Sources:** `sourcetype="snmp:poll_status"` or `sourcetype="snmp:ta:log"`
- **SPL:**
```spl
index=network sourcetype="snmp:poll_status"
| where status!="success" OR timeout_ms > 3000
| stats count by host, device_ip, oid_tree, error_code
| sort -count
```
- **Implementation:** Emit structured poll result per target (success, timeout, auth error). Alert on sustained failure rate >5% or SNMP timeout storms. Verify SNMP community/v3 creds and ACLs on device.
- **Visualization:** Table (devices with poll failures), Line chart (failure % trend), Status grid (device × OID family).
- **CIM Models:** N/A

---

### UC-14.1.12 · Firmware Version Compliance Across Fleet
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Known-bad IOS/NX-OS/IOS-XE builds expose the network to CVEs; compliance reporting supports change windows.
- **App/TA:** SNMP TA (ENTITY-MIB, vendor OIDs), SolarWinds/Prime export
- **Data Sources:** `sourcetype="snmp:inventory"` (sysDescr, entPhysicalFirmwareRev)
- **SPL:**
```spl
index=network sourcetype="snmp:inventory"
| stats latest(firmware_version) as fw by device_name, model
| lookup approved_network_firmware.csv model OUTPUT approved_fw
| where fw!=approved_fw
| table device_name, model, fw, approved_fw
```
- **Implementation:** Poll ENTITY-MIB / vendor firmware revision OIDs on a weekly schedule. Maintain CSV of approved builds per platform. Drive remediation tickets for non-compliant devices.
- **Visualization:** Table (non-compliant devices), Pie chart (compliance %), Bar chart (by site).
- **CIM Models:** N/A

---

### UC-14.1.13 · Environmental Sensor Threshold Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Rack intake temperature and humidity from SNMP sensors protect IT and edge equipment from thermal damage.
- **App/TA:** SNMP TA (UPS-MIB, custom sensor MIBs)
- **Data Sources:** `sourcetype="snmp:env_sensor"` (tempC, humidityPct)
- **SPL:**
```spl
index=environment sourcetype="snmp:env_sensor"
| where temp_c > 30 OR temp_c < 10 OR humidity_pct > 70 OR humidity_pct < 20
| table _time, device_ip, sensor_id, temp_c, humidity_pct, location
```
- **Implementation:** Map OIDs to sensor labels. Alert per ASHRAE/site policy. Correlate with HVAC/BMS where available.
- **Visualization:** Heatmap (rack × temp), Line chart (sensor trend), Table (exceedances).
- **CIM Models:** N/A

---

### UC-14.1.14 · SNMPv3 Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Auth failures indicate credential rotation gaps, brute force, or misconfigured collectors.
- **App/TA:** Device syslog, SNMP engine logs
- **Data Sources:** `sourcetype="snmp:auth"` or `sourcetype="cisco:ios"` (SNMPv3 usmStats)
- **SPL:**
```spl
index=network sourcetype IN ("snmp:auth","cisco:ios")
| search "authentication failure" OR "Unknown user name" OR "usmStatsUnknownUserNames"
| eval user=coalesce(user, user_name)
| stats count by src, device_name, user
| where count > 10
| sort -count
```
- **Implementation:** Forward device-side SNMPv3 error counters to Splunk. Alert on burst from single IP or new engine ID. Correlate with NetOps change tickets.
- **Visualization:** Table (top sources of auth failures), Timeline (failure bursts), Map (geo of source IPs if routed).
- **CIM Models:** N/A


---


### UC-14.1.15 · Temperature Sensor Threshold Alerts (Meraki MT)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Alerts when environmental temperatures exceed safe thresholds to prevent equipment damage.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*temperature*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*temperature*"
| stats latest(temperature) as current_temp, min(temperature) as min_temp, max(temperature) as max_temp by sensor_location
| where current_temp > 30 OR current_temp < 5
```
- **Implementation:** Monitor temperature sensor threshold alerts from syslog. Alert on exceedance.
- **Visualization:** Temperature gauge per location; trend timeline; alert dashboard.
- **CIM Models:** N/A

---

### UC-14.1.16 · Humidity Monitoring and Dew Point Tracking (Meraki MT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Monitors humidity levels to ensure optimal conditions for equipment and prevent moisture damage.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*humidity*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*humidity*"
| stats latest(humidity) as current_humidity, avg(humidity) as avg_humidity by sensor_location
| eval dew_point="calculated_value"
```
- **Implementation:** Monitor humidity sensor data. Calculate dew point for condensation risk.
- **Visualization:** Humidity gauge per location; humidity vs temperature correlation; trend chart.
- **CIM Models:** N/A

---

### UC-14.1.17 · Door Open/Close Event Detection and Alerts (Meraki MT)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks door access events for security and facility monitoring.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*door*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*door*" (action="open" OR action="close")
| stats count as door_events, latest(timestamp) as last_event by door_location, action
```
- **Implementation:** Monitor door sensor events. Alert on unusual access patterns.
- **Visualization:** Door event timeline; access pattern analysis; alert table.
- **CIM Models:** N/A

---

### UC-14.1.18 · Water Leak Detection and Flood Alerts (Meraki MT)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Immediately detects water leaks to prevent equipment damage and business interruption.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*water*" OR signature="*leak*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*water*" OR signature="*leak*")
| stats count as leak_events, latest(timestamp) as last_detection by sensor_location
| where leak_events > 0
```
- **Implementation:** Monitor water/leak detection sensors. Create critical alert.
- **Visualization:** Leak alert dashboard; sensor location map; event timeline.
- **CIM Models:** N/A

---

### UC-14.1.19 · Power Monitoring and Electrical Load Analysis (Meraki MT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks electrical power consumption and load to identify anomalies and plan upgrades.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="power" power_watts=*
| stats avg(power_watts) as avg_power, max(power_watts) as peak_power by location
| eval power_capacity_pct=round(peak_power*100/15000, 2)
```
- **Implementation:** Query sensor API for power metrics. Track consumption and peaks.
- **Visualization:** Power consumption gauge; peak load timeline; capacity planning chart.
- **CIM Models:** N/A

---

### UC-14.1.20 · Air Quality and CO2 Monitoring (Meraki MT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors indoor air quality to ensure safe working conditions.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api sensor_type="air_quality"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="air_quality" co2_ppm=*
| stats latest(co2_ppm) as current_co2, avg(co2_ppm) as avg_co2 by location
| where current_co2 > 1000
```
- **Implementation:** Monitor CO2 and air quality sensor data. Alert on high levels.
- **Visualization:** CO2 level gauge per location; trend timeline; air quality status chart.
- **CIM Models:** N/A

---

### UC-14.1.21 · Ambient Noise Level Monitoring and Trend Analysis (Meraki MT)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks noise levels to ensure comfortable working environment and detect anomalies.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api sensor_type="noise"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="noise" noise_db=*
| stats avg(noise_db) as avg_noise, max(noise_db) as peak_noise by location
| timechart avg(noise_db) by location
```
- **Implementation:** Ingest noise sensor data. Track by location and time of day.
- **Visualization:** Noise level gauge; time-of-day heat map; location comparison chart.
- **CIM Models:** N/A

---

### UC-14.1.22 · Indoor Climate Trending and HVAC Optimization (Meraki MT)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Analyzes temperature and humidity trends to optimize HVAC system efficiency.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api sensor_type IN ("temperature", "humidity")`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type IN ("temperature", "humidity")
| stats avg(value) as avg_value by sensor_type, location
| timechart avg(value) by sensor_type
```
- **Implementation:** Correlate temperature and humidity data. Identify optimization opportunities.
- **Visualization:** Climate trend line chart; comfort zone indicator; energy efficiency analysis.
- **CIM Models:** N/A

---

### UC-14.1.23 · Environmental Sensor Battery Health and Replacement Alerts (Meraki MT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks sensor battery levels to ensure sensors remain operational and schedule replacements.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" battery_level=*
| stats latest(battery_level) as battery_pct by sensor_id, location
| where battery_pct < 20
| sort battery_pct
```
- **Implementation:** Query sensor API for battery metrics. Alert on <20% battery.
- **Visualization:** Battery health table; battery trend timeline; replacement alert dashboard.
- **CIM Models:** N/A

---

### UC-14.1.24 · Sensor Connectivity and Heartbeat Monitoring (Meraki MT)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Ensures all sensors maintain connectivity and operational status.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(last_report) as last_checkin by sensor_id
| eval hours_since_checkin=round((now()-strptime(last_report, "%Y-%m-%dT%H:%M:%S"))/3600, 1)
| where hours_since_checkin > 2
```
- **Implementation:** Query sensor API for last report time. Alert on missing heartbeats.
- **Visualization:** Sensor status table; last heartbeat timeline; offline sensor list.
- **CIM Models:** N/A

---

### UC-14.1.25 · AHU Supply Air Temperature Deviation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Air Handling Unit supply air temperature drifting from setpoint indicates coil fouling, valve failures, or economizer faults — wasting energy and degrading occupant comfort. Catching deviations early prevents complaints and energy waste.
- **App/TA:** BACnet gateway (e.g. Cimetrics BACstac, Contemporary Controls), Splunk Edge Hub, custom scripted input
- **Data Sources:** `sourcetype=bms:bacnet`, `sourcetype=bms:hvac`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" object_type="AHU"
| eval delta=abs(supply_air_temp - supply_air_setpoint)
| bin _time span=15m
| stats avg(delta) as avg_deviation, max(delta) as max_deviation, avg(supply_air_temp) as avg_supply, latest(supply_air_setpoint) as setpoint by ahu_name, _time
| where avg_deviation > 2
| table _time, ahu_name, setpoint, avg_supply, avg_deviation, max_deviation
```
- **Implementation:** Ingest AHU BACnet points via Edge Hub or BACnet gateway. Compare supply air temperature to setpoint. Alert on sustained deviation >2°F/1°C.
- **Visualization:** Line chart (supply temp vs setpoint per AHU); deviation heatmap by AHU and time of day; single value (worst deviation).
- **CIM Models:** N/A

---

### UC-14.1.26 · VAV Box Damper Position Stuck Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Approximately 30% of VAV boxes operate with faults in typical buildings. A stuck damper actuator causes a zone to receive constant airflow regardless of demand — wasting 15-25% of HVAC energy per affected zone and creating hot/cold complaints.
- **App/TA:** BACnet gateway, Splunk Edge Hub, BMS vendor API (Honeywell/Siemens/JCI)
- **Data Sources:** `sourcetype=bms:bacnet`, `sourcetype=bms:hvac`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" object_type="VAV"
| bin _time span=1h
| stats stdev(damper_position_pct) as damper_variance, avg(damper_position_pct) as avg_position, avg(zone_temp) as avg_zone_temp, avg(zone_setpoint) as avg_setpoint by vav_id, zone_name, _time
| where damper_variance < 2 AND abs(avg_zone_temp - avg_setpoint) > 2
| table _time, vav_id, zone_name, avg_position, damper_variance, avg_zone_temp, avg_setpoint
```
- **Implementation:** Monitor damper position variance over 1-hour windows. If position barely changes while zone temp drifts from setpoint, flag as stuck actuator. Dispatch HVAC technician.
- **Visualization:** Table of stuck VAV boxes; zone comfort heatmap; damper position timeline per VAV.
- **CIM Models:** N/A

---

### UC-14.1.27 · Chiller Plant COP Efficiency Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Chiller plants consume 30-50% of total building energy. Tracking Coefficient of Performance (COP) identifies degradation from condenser fouling, refrigerant loss, or suboptimal sequencing — enabling 15-30% cooling energy savings.
- **App/TA:** BACnet gateway, Modbus TCP (for power meters), BMS vendor API
- **Data Sources:** `sourcetype=bms:hvac`, `sourcetype=bms:energy`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" object_type="chiller"
| bin _time span=30m
| stats avg(cooling_output_kw) as avg_cooling, avg(power_input_kw) as avg_power, avg(chilled_water_supply_temp) as avg_chws, avg(condenser_water_return_temp) as avg_cwr by chiller_id, _time
| eval cop=round(avg_cooling/avg_power, 2)
| where avg_power > 10
| eval efficiency_status=case(cop>=5, "Excellent", cop>=4, "Good", cop>=3, "Degraded", cop<3, "Poor")
| table _time, chiller_id, cop, efficiency_status, avg_cooling, avg_power, avg_chws, avg_cwr
```
- **Implementation:** Collect chiller cooling output (tons or kW) and electrical input from BACnet or power meters. Calculate COP. Trend over time and compare to manufacturer baseline. Alert on sustained COP below threshold.
- **Visualization:** COP trend line per chiller; efficiency gauge vs baseline; chiller comparison chart; kW/ton dashboard.
- **CIM Models:** N/A

---

### UC-14.1.28 · Cooling Tower Approach Temperature Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Approach temperature (difference between condenser water leaving the tower and outdoor wet bulb) reveals cooling tower effectiveness. Rising approach indicates fill media fouling, fan issues, or scale buildup — directly impacting chiller efficiency.
- **App/TA:** BACnet gateway, outdoor weather station integration
- **Data Sources:** `sourcetype=bms:hvac`, `sourcetype=weather:station`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" object_type="cooling_tower"
| bin _time span=30m
| stats avg(leaving_water_temp) as avg_lwt, avg(wet_bulb_temp) as avg_wb by tower_id, _time
| eval approach=round(avg_lwt - avg_wb, 1)
| where approach > 0
| eval status=case(approach<=5, "Normal", approach<=8, "Watch", approach>8, "Degraded")
| table _time, tower_id, approach, status, avg_lwt, avg_wb
```
- **Implementation:** Ingest cooling tower leaving water temperature and outdoor wet bulb from weather station or BMS. Calculate approach. Alert when approach exceeds design value by more than 3°F.
- **Visualization:** Approach temperature trend per tower; status indicator; comparison to design baseline.
- **CIM Models:** N/A

---

### UC-14.1.29 · HVAC Setpoint Override Frequency and Duration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Frequent manual setpoint overrides by occupants or operators indicate either comfort issues or poor control tuning. Tracking override patterns helps identify problem zones and quantifies energy waste from overrides that persist beyond work hours.
- **App/TA:** BMS vendor API (Honeywell EBI, Siemens Desigo, Johnson Controls Metasys), BACnet gateway
- **Data Sources:** `sourcetype=bms:hvac`, `sourcetype=bms:bacnet`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" event_type="setpoint_override"
| eval override_duration_hrs=round(override_duration_min/60, 1)
| bin _time span=1d
| stats count as override_count, avg(override_duration_hrs) as avg_duration, sum(override_duration_hrs) as total_override_hrs, dc(zone_name) as zones_affected by building, _time
| where override_count > 5
| table _time, building, override_count, zones_affected, avg_duration, total_override_hrs
```
- **Implementation:** Capture BMS override events with zone, user, original setpoint, override value, and duration. Track daily override frequency. Alert on zones with excessive overrides.
- **Visualization:** Override count heatmap by zone and time; daily override trending; top override zones table.
- **CIM Models:** N/A

---

### UC-14.1.30 · Economizer Free Cooling Hours Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Economizer mode uses outside air for free cooling when conditions permit, saving significant compressor energy. Tracking actual free cooling hours vs available hours reveals malfunctioning dampers, faulty enthalpy sensors, or misconfigured switchover points.
- **App/TA:** BACnet gateway, BMS vendor API
- **Data Sources:** `sourcetype=bms:hvac`, `sourcetype=weather:station`
- **SPL:**
```spl
index=building sourcetype="bms:hvac" object_type="AHU"
| eval is_economizer=if(economizer_mode="active", 1, 0)
| eval could_economize=if(outside_air_temp < return_air_temp AND outside_air_temp < 65, 1, 0)
| bin _time span=1d
| stats sum(is_economizer) as economizer_hours, sum(could_economize) as available_hours by ahu_name, _time
| eval utilization_pct=round(economizer_hours*100/available_hours, 1)
| where available_hours > 2 AND utilization_pct < 50
| table _time, ahu_name, economizer_hours, available_hours, utilization_pct
```
- **Implementation:** Track AHU economizer mode status alongside outdoor conditions. Calculate available vs actual free cooling hours. Alert when utilization drops below 50% of available hours.
- **Visualization:** Free cooling utilization gauge per AHU; seasonal trend; missed opportunity cost estimate.
- **CIM Models:** N/A

---

### UC-14.1.31 · Building Energy Consumption Intensity (kWh/m²)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Energy Use Intensity (EUI) in kWh per square meter is the standard benchmark for building energy performance. Tracking EUI trending and comparing across buildings reveals efficiency opportunities and supports ENERGY STAR, LEED, and ESG reporting.
- **App/TA:** Smart utility meters via Modbus TCP or pulse counting, BMS energy meters, scripted input from utility APIs
- **Data Sources:** `sourcetype=bms:energy`, `sourcetype=bms:meter`
- **SPL:**
```spl
index=building sourcetype="bms:energy" meter_type="electricity"
| bin _time span=1d
| stats sum(kwh_consumed) as daily_kwh by building_name, _time
| lookup building_info.csv building_name OUTPUTNEW floor_area_sqm, building_type
| eval eui=round(daily_kwh/floor_area_sqm, 2)
| eval annual_eui_projected=eui*365
| eval benchmark_status=case(annual_eui_projected<150, "Excellent", annual_eui_projected<250, "Good", annual_eui_projected<350, "Average", annual_eui_projected>=350, "Poor")
| table _time, building_name, building_type, daily_kwh, floor_area_sqm, eui, annual_eui_projected, benchmark_status
```
- **Implementation:** Install smart energy meters on main electrical feeds. Ingest kWh readings via Modbus or pulse counter. Join with building floor area lookup. Calculate daily and projected annual EUI. Compare to industry benchmarks (ENERGY STAR, CIBSE).
- **Visualization:** EUI trend per building; benchmark comparison bar chart; building ranking table; year-over-year comparison.
- **CIM Models:** N/A

---

### UC-14.1.32 · Sub-Meter Energy Distribution by System
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sub-metering breaks total energy into HVAC, lighting, plug loads, and other systems. Knowing which system consumes the most energy directs efficiency investments where they'll have the biggest impact — typically HVAC at 40-60%.
- **App/TA:** Smart sub-meters via Modbus TCP, BMS energy management module
- **Data Sources:** `sourcetype=bms:energy`, `sourcetype=bms:meter`
- **SPL:**
```spl
index=building sourcetype="bms:energy" meter_type="sub_meter"
| bin _time span=1d
| stats sum(kwh_consumed) as daily_kwh by building_name, system_type, _time
| eventstats sum(daily_kwh) as total_kwh by building_name, _time
| eval pct_of_total=round(daily_kwh*100/total_kwh, 1)
| table _time, building_name, system_type, daily_kwh, pct_of_total
| sort _time, building_name, -pct_of_total
```
- **Implementation:** Deploy sub-meters on HVAC, lighting, plug load, and elevator panels. Ingest readings. Calculate percentage distribution. Trend over time. Identify systems with growing share.
- **Visualization:** Pie chart of energy by system; stacked area chart over time; system comparison across buildings.
- **CIM Models:** N/A

---

### UC-14.1.33 · After-Hours Energy Waste Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Buildings typically waste 20-30% of energy outside occupied hours from HVAC systems running on override, lights left on, or equipment not in unoccupied mode. Detecting after-hours energy above baseline enables quick wins with minimal investment.
- **App/TA:** Smart utility meters via Modbus, BMS schedule integration
- **Data Sources:** `sourcetype=bms:energy`, `sourcetype=bms:hvac`
- **SPL:**
```spl
index=building sourcetype="bms:energy" meter_type="electricity"
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval is_after_hours=if((hour<7 OR hour>19) OR dow>5, 1, 0)
| bin _time span=1h
| stats sum(kwh_consumed) as hourly_kwh by building_name, is_after_hours, _time
| where is_after_hours=1 AND hourly_kwh > 0
| eventstats perc25(hourly_kwh) as baseline_kwh by building_name
| eval waste_kwh=if(hourly_kwh > baseline_kwh*1.5, hourly_kwh - baseline_kwh, 0)
| where waste_kwh > 0
| table _time, building_name, hourly_kwh, baseline_kwh, waste_kwh
```
- **Implementation:** Compare after-hours energy consumption to baseline (minimum observed usage). Flag hours where consumption exceeds 150% of baseline. Cross-reference with BMS schedules and override events to identify root cause.
- **Visualization:** After-hours vs occupied hours comparison chart; waste energy trending; building ranking by waste percentage.
- **CIM Models:** N/A

---

### UC-14.1.34 · Peak Demand Shaving Effectiveness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Utility demand charges based on peak 15-minute kW draw can represent 30-50% of a commercial building's electric bill. Monitoring peak demand and evaluating load-shedding effectiveness helps control costs and supports demand response programs.
- **App/TA:** Smart utility meters, BMS demand limiting module
- **Data Sources:** `sourcetype=bms:energy`, `sourcetype=bms:meter`
- **SPL:**
```spl
index=building sourcetype="bms:energy" meter_type="electricity"
| bin _time span=15m
| stats avg(kw_demand) as demand_kw by building_name, _time
| eventstats max(demand_kw) as peak_demand by building_name
| eval pct_of_peak=round(demand_kw*100/peak_demand, 1)
| eval month=strftime(_time, "%Y-%m")
| stats max(demand_kw) as monthly_peak_kw, avg(demand_kw) as avg_demand_kw by building_name, month
| eval load_factor=round(avg_demand_kw*100/monthly_peak_kw, 1)
| table month, building_name, monthly_peak_kw, avg_demand_kw, load_factor
```
- **Implementation:** Monitor 15-minute demand intervals from utility meters. Track monthly peak demand. Calculate load factor (average/peak). Higher load factor means better demand management. Alert when approaching contract demand limit.
- **Visualization:** Demand profile chart (15-min intervals); monthly peak trending; load factor gauge; demand limit threshold line.
- **CIM Models:** N/A

---

### UC-14.1.35 · Lighting Schedule Compliance and Override Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Lighting left on outside scheduled hours wastes 10-20% of lighting energy. Tracking schedule compliance and manual override patterns identifies zones where schedules need adjustment or occupancy sensors should be added.
- **App/TA:** DALI/KNX gateway, BMS lighting control module, smart relay monitoring
- **Data Sources:** `sourcetype=bms:lighting`, `sourcetype=bms:bacnet`
- **SPL:**
```spl
index=building sourcetype="bms:lighting" event_type IN ("on", "off", "override")
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval scheduled_off=if((hour>=21 OR hour<6) AND dow<=5, 1, if(dow>5, 1, 0))
| where event_type="on" AND scheduled_off=1
| stats count as after_hours_on, dc(zone) as zones_affected by building, floor
| sort -after_hours_on
| table building, floor, zones_affected, after_hours_on
```
- **Implementation:** Monitor lighting circuit status from BMS or DALI/KNX gateway. Compare on/off events to published schedule. Track overrides with timestamp and duration. Alert on sustained after-hours lighting without override justification.
- **Visualization:** Schedule compliance percentage gauge; after-hours lighting heatmap by floor; override frequency chart.
- **CIM Models:** N/A

---

### UC-14.1.36 · Elevator Trip Count and Usage Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Elevator trip counts, floor-by-floor usage patterns, and duty cycles drive maintenance scheduling and modernization planning. High-traffic elevators need more frequent service. Usage data also informs tenant space planning and lobby redesign.
- **App/TA:** Elevator controller API (KONE, Otis, Schindler, ThyssenKrupp), IoT gateway, custom scripted input
- **Data Sources:** `sourcetype=bms:elevator`
- **SPL:**
```spl
index=building sourcetype="bms:elevator"
| bin _time span=1h
| stats count as trips, sum(distance_traveled_m) as total_distance, avg(travel_time_sec) as avg_travel_time, dc(floor_stop) as floors_served by elevator_id, _time
| eval trips_per_hour=trips
| eventstats avg(trips_per_hour) as baseline_trips by elevator_id
| eval utilization=round(trips_per_hour*100/baseline_trips, 1)
| table _time, elevator_id, trips, floors_served, avg_travel_time, utilization
```
- **Implementation:** Integrate with elevator controller via vendor API or IoT gateway. Collect trip events with timestamp, origin floor, destination floor, and travel time. Aggregate into hourly/daily patterns.
- **Visualization:** Trip count timeline per elevator; floor usage heatmap; peak hour analysis; elevator comparison chart.
- **CIM Models:** N/A

---

### UC-14.1.37 · Elevator Door Fault Frequency and Prediction
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Door faults are the most common elevator malfunction and the leading cause of entrapments. Monitoring door close force, cycle time, and motor amperage detects deteriorating door systems 2-6 weeks before failure — preventing passenger entrapments and service calls.
- **App/TA:** Elevator controller API, vibration/current sensors via IoT gateway
- **Data Sources:** `sourcetype=bms:elevator`
- **SPL:**
```spl
index=building sourcetype="bms:elevator" event_type="door_*"
| eval is_fault=if(event_type="door_fault" OR door_close_time_ms > 5000 OR door_reversal=1, 1, 0)
| bin _time span=1d
| stats sum(is_fault) as daily_faults, count as total_door_cycles, avg(door_close_time_ms) as avg_close_time, sum(door_reversal) as reversals by elevator_id, _time
| eval fault_rate_pct=round(daily_faults*100/total_door_cycles, 2)
| where fault_rate_pct > 1 OR daily_faults > 5
| table _time, elevator_id, daily_faults, total_door_cycles, fault_rate_pct, avg_close_time, reversals
```
- **Implementation:** Collect door cycle events including close force, cycle time, and reversal events. Trend door close time — increasing values indicate worn rollers, dirty tracks, or actuator degradation. Alert when fault rate exceeds 1% or close time exceeds 5 seconds.
- **Visualization:** Door fault trend per elevator; close time degradation chart; reversal frequency; fault prediction timeline.
- **CIM Models:** N/A

---

### UC-14.1.38 · Elevator Wait Time and Service Quality
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Average wait time is the primary measure of elevator service quality visible to occupants. Industry target is under 30 seconds for office buildings. Excessive wait times indicate traffic imbalance, out-of-service cars, or poor dispatching algorithms.
- **App/TA:** Elevator controller API, hall call registration sensors
- **Data Sources:** `sourcetype=bms:elevator`
- **SPL:**
```spl
index=building sourcetype="bms:elevator" event_type="hall_call"
| eval wait_time_sec=(response_time - call_time)
| bin _time span=1h
| stats avg(wait_time_sec) as avg_wait, perc95(wait_time_sec) as p95_wait, count as total_calls by building, elevator_group, _time
| eval sla_status=if(avg_wait<=30, "Meeting SLA", "SLA Breach")
| where avg_wait > 30 OR p95_wait > 60
| table _time, building, elevator_group, avg_wait, p95_wait, total_calls, sla_status
```
- **Implementation:** Capture hall call registration and car arrival timestamps from elevator controller. Calculate wait time per call. Aggregate into hourly metrics. Compare to industry SLA (30s average, 60s 95th percentile).
- **Visualization:** Wait time gauge per elevator group; hourly pattern chart; SLA compliance timeline; floor-level analysis.
- **CIM Models:** N/A

---

### UC-14.1.39 · Water Consumption Trending and Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Undetected water leaks can waste thousands of liters daily and cause structural damage. Continuous flow monitoring detects leaks, running toilets, and irrigation faults within hours rather than the weeks it takes for a utility bill to reveal problems.
- **App/TA:** Smart water meters (Modbus, pulse), IoT flow sensors, building management API
- **Data Sources:** `sourcetype=bms:water`
- **SPL:**
```spl
index=building sourcetype="bms:water" meter_type="main_feed"
| bin _time span=1h
| stats sum(liters) as hourly_liters by building_name, _time
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval is_occupied=if(hour>=7 AND hour<=19 AND dow<=5, 1, 0)
| where is_occupied=0 AND hourly_liters > 50
| eventstats avg(hourly_liters) as baseline_unoccupied by building_name
| eval anomaly_ratio=round(hourly_liters/baseline_unoccupied, 1)
| where anomaly_ratio > 3
| table _time, building_name, hourly_liters, baseline_unoccupied, anomaly_ratio
```
- **Implementation:** Install smart water meters on main feeds and key branches. Monitor flow during unoccupied hours — sustained flow indicates leaks or running fixtures. Alert when unoccupied consumption exceeds 3x baseline.
- **Visualization:** Water consumption timeline; occupied vs unoccupied comparison; anomaly alert dashboard; leak detection map.
- **CIM Models:** N/A

---

### UC-14.1.40 · Domestic Hot Water Temperature Compliance (Legionella Prevention)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Legionella bacteria thrive in water between 20-45°C. Building codes require domestic hot water storage above 60°C and distribution above 50°C. Temperature drops below these thresholds create serious health risks and regulatory violations.
- **App/TA:** BACnet gateway, temperature sensors via Modbus or IoT
- **Data Sources:** `sourcetype=bms:water`, `sourcetype=bms:bacnet`
- **SPL:**
```spl
index=building sourcetype="bms:water" system="domestic_hot_water"
| bin _time span=15m
| stats avg(temperature_c) as avg_temp, min(temperature_c) as min_temp by location, sensor_type, _time
| eval compliance=case(
    sensor_type="storage" AND min_temp>=60, "Compliant",
    sensor_type="storage" AND min_temp<60, "NON-COMPLIANT",
    sensor_type="return" AND min_temp>=50, "Compliant",
    sensor_type="return" AND min_temp<50, "NON-COMPLIANT")
| where compliance="NON-COMPLIANT"
| table _time, location, sensor_type, avg_temp, min_temp, compliance
```
- **Implementation:** Monitor hot water storage tank and return line temperatures continuously. Alert immediately on any reading below compliance threshold. Log all temperature data for regulatory audit trail.
- **Visualization:** Temperature compliance gauge per system; temperature timeline; non-compliance alert log; regulatory compliance report.
- **CIM Models:** N/A

---

### UC-14.1.41 · Cooling Tower Water Chemistry Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cooling tower water chemistry (conductivity, pH, biocide levels) directly impacts heat transfer efficiency and equipment life. Scale buildup from poor chemistry increases chiller energy by 2-5% per mm of scale and accelerates corrosion.
- **App/TA:** Water chemistry controller (Nalco, Chemtrol) via Modbus or API, IoT sensors
- **Data Sources:** `sourcetype=bms:water`
- **SPL:**
```spl
index=building sourcetype="bms:water" system="cooling_tower"
| bin _time span=1h
| stats avg(conductivity_us) as avg_conductivity, avg(ph) as avg_ph, avg(cycles_of_concentration) as avg_coc, latest(biocide_ppm) as biocide_level by tower_id, _time
| eval chem_status=case(
    avg_conductivity > 3000, "High Conductivity - Blowdown Needed",
    avg_ph < 7.0 OR avg_ph > 9.0, "pH Out of Range",
    biocide_level < 0.5, "Low Biocide",
    avg_coc > 6, "High Concentration",
    1=1, "Normal")
| where chem_status!="Normal"
| table _time, tower_id, chem_status, avg_conductivity, avg_ph, avg_coc, biocide_level
```
- **Implementation:** Integrate with water treatment controller via Modbus or API. Monitor conductivity, pH, cycles of concentration, and biocide levels. Alert on out-of-range values. Track chemical consumption trends.
- **Visualization:** Chemistry parameter trend lines; status indicator per tower; chemical consumption dashboard.
- **CIM Models:** N/A

---

### UC-14.1.42 · Fire Alarm Panel Zone Health and Event Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Fire alarm panel trouble conditions (ground faults, open circuits, dirty detectors) must be resolved promptly to maintain life safety protection. Centralizing fire panel events enables multi-building oversight and faster trouble resolution.
- **App/TA:** Fire alarm panel integration via syslog, serial gateway, or Notifier/Edwards/Simplex API
- **Data Sources:** `sourcetype=bms:fire`
- **SPL:**
```spl
index=building sourcetype="bms:fire" event_type IN ("trouble", "alarm", "supervisory")
| bin _time span=1h
| stats count as events, dc(zone) as zones_affected, values(event_type) as event_types, latest(description) as latest_event by panel_id, building, _time
| eval severity=case(
    mvfind(event_types, "alarm")>=0, "ALARM",
    mvfind(event_types, "supervisory")>=0, "Supervisory",
    mvfind(event_types, "trouble")>=0, "Trouble")
| table _time, building, panel_id, severity, zones_affected, events, latest_event
| sort -severity, -events
```
- **Implementation:** Connect fire alarm panels via syslog receiver or serial-to-IP converter. Normalize events into alarm, trouble, and supervisory categories. Alert on any alarm immediately. Track trouble conditions for resolution within code-required timeframes.
- **Visualization:** Fire panel status dashboard; event timeline; trouble condition age tracking; multi-building overview map.
- **CIM Models:** N/A

---

### UC-14.1.43 · Sprinkler System Valve Tamper and Supervisory Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Closed or partially closed sprinkler valves are the number one reason sprinkler systems fail to operate during a fire. Valve tamper switches provide immediate notification when a valve position changes — NFPA 25 requires monitoring.
- **App/TA:** Fire alarm panel integration (valve tamper switches connected to panel), syslog
- **Data Sources:** `sourcetype=bms:fire`
- **SPL:**
```spl
index=building sourcetype="bms:fire" event_type="supervisory" device_type IN ("valve_tamper", "waterflow", "low_pressure")
| eval urgency=case(
    device_type="valve_tamper" AND state="closed", "CRITICAL",
    device_type="waterflow", "ALARM",
    device_type="low_pressure", "HIGH",
    1=1, "Medium")
| stats count as events, latest(state) as current_state, latest(_time) as last_event by building, zone, device_type, device_id
| where current_state IN ("closed", "active", "low")
| table building, zone, device_type, device_id, current_state, urgency, last_event, events
| sort urgency
```
- **Implementation:** Ensure all valve tamper switches, waterflow switches, and pressure switches report to fire panel. Forward panel events to Splunk. Alert immediately on valve tamper events. Track restoration time for compliance.
- **Visualization:** Valve status map by building; tamper event timeline; open trouble list; NFPA 25 compliance dashboard.
- **CIM Models:** N/A

---

### UC-14.1.44 · Fire Pump Controller Status and Run Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Fire pumps must be ready to operate instantly during a fire. Controller monitoring tracks pump starts, run duration, phase voltage, and jockey pump cycling. Excessive jockey pump cycling often indicates system leaks that degrade firefighting readiness.
- **App/TA:** Fire pump controller (via syslog or serial gateway), BMS integration
- **Data Sources:** `sourcetype=bms:fire`
- **SPL:**
```spl
index=building sourcetype="bms:fire" device_type="fire_pump"
| bin _time span=1d
| stats count(eval(event_type="pump_start")) as starts, sum(run_duration_min) as total_run_min, avg(phase_a_voltage) as avg_voltage, count(eval(pump_type="jockey" AND event_type="pump_start")) as jockey_starts by building, pump_id, _time
| eval jockey_concern=if(jockey_starts > 20, "Excessive Cycling - Check for Leaks", "Normal")
| table _time, building, pump_id, starts, total_run_min, avg_voltage, jockey_starts, jockey_concern
```
- **Implementation:** Monitor fire pump controller via syslog or serial gateway. Track all pump starts (test and demand), run duration, and electrical parameters. Flag excessive jockey pump cycling (>20 starts/day). Log for NFPA 25 weekly/monthly test compliance.
- **Visualization:** Pump run history timeline; jockey pump cycling chart; weekly test compliance tracker; voltage quality gauge.
- **CIM Models:** N/A

---

### UC-14.1.45 · BACnet Controller Communication Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** BACnet controllers are the brains of building automation — each manages a zone, floor, or system. Communication loss means affected areas run in fallback mode with no remote visibility or control. Monitoring network health catches issues before occupants notice.
- **App/TA:** BACnet network scanner, BMS supervisory controller, SNMP
- **Data Sources:** `sourcetype=bms:bacnet`
- **SPL:**
```spl
index=building sourcetype="bms:bacnet" event_type="device_status"
| stats latest(status) as current_status, latest(_time) as last_seen, count(eval(status="offline")) as offline_events by device_id, device_name, network_id, location
| eval hours_since_seen=round((now()-last_seen)/3600, 1)
| eval health=case(
    current_status="offline" OR hours_since_seen > 1, "OFFLINE",
    offline_events > 3, "Unstable",
    1=1, "Online")
| where health!="Online"
| table device_id, device_name, location, network_id, health, hours_since_seen, offline_events
| sort health, -hours_since_seen
```
- **Implementation:** Periodically scan BACnet network for device presence using BACnet Who-Is/I-Am or poll device status from supervisory controller. Track response times and offline events. Alert on any controller going offline or showing unstable communication.
- **Visualization:** Controller status map; network health dashboard; offline device list; communication stability trend.
- **CIM Models:** N/A

---

### UC-14.1.46 · BMS Alarm Flood Detection and Suppression
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** A single equipment failure (e.g., chiller trip) can generate hundreds of cascading BMS alarms across downstream systems — overwhelming operators and burying the root cause. Detecting alarm floods and identifying the source event reduces mean time to resolve.
- **App/TA:** BMS alarm feed via syslog, BACnet alarm notifications, vendor API
- **Data Sources:** `sourcetype=bms:bacnet`, `sourcetype=bms:hvac`
- **SPL:**
```spl
index=building sourcetype="bms:*" event_type="alarm"
| bin _time span=5m
| stats count as alarm_count, dc(device_id) as devices_affected, dc(alarm_type) as alarm_types, earliest(alarm_description) as first_alarm, earliest(device_name) as first_device by building, _time
| where alarm_count > 20
| eval flood_status="ALARM FLOOD", probable_root_cause=first_device." - ".first_alarm
| table _time, building, alarm_count, devices_affected, alarm_types, probable_root_cause
```
- **Implementation:** Aggregate all BMS alarms. Detect bursts exceeding 20 alarms in 5 minutes. Identify the earliest alarm as probable root cause. Suppress downstream alarms in operator dashboard. Track alarm flood frequency for system reliability improvement.
- **Visualization:** Alarm volume timeline; flood event timeline; root cause table; alarm type distribution during floods.
- **CIM Models:** N/A

---

### UC-14.1.47 · Parking Occupancy Trending and Capacity Planning
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Real-time parking occupancy data optimizes space utilization, reduces circling time, and informs expansion or reduction decisions. Trending occupancy by day-of-week and time helps set pricing tiers and plan EV charging capacity.
- **App/TA:** Parking guidance system API (SKIDATA, SWARCO, ParkAssist), gate controller, IoT occupancy sensors
- **Data Sources:** `sourcetype=bms:parking`
- **SPL:**
```spl
index=building sourcetype="bms:parking"
| bin _time span=30m
| stats latest(occupied_spaces) as occupied, latest(total_spaces) as total by parking_facility, level, _time
| eval available=total-occupied, occupancy_pct=round(occupied*100/total, 1)
| eval status=case(occupancy_pct>=95, "Full", occupancy_pct>=80, "Busy", occupancy_pct>=50, "Moderate", occupancy_pct<50, "Available")
| table _time, parking_facility, level, occupied, available, total, occupancy_pct, status
```
- **Implementation:** Integrate with parking guidance system API or gate entry/exit counters. Track occupancy per level. Trend by time of day and day of week. Alert when approaching capacity.
- **Visualization:** Occupancy gauge per level; daily pattern heatmap; available spaces single value; trend chart.
- **CIM Models:** N/A

---

### UC-14.1.48 · EV Charging Station Availability and Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** EV charging infrastructure is rapidly growing in commercial buildings. Monitoring station availability, session duration, and energy delivery helps right-size charging capacity, identify broken stations, and plan electrical load management.
- **App/TA:** OCPP-compatible charging management system (ChargePoint, Blink, ABB), custom API input
- **Data Sources:** `sourcetype=bms:ev_charging`
- **SPL:**
```spl
index=building sourcetype="bms:ev_charging"
| eval session_duration_hrs=round(session_duration_min/60, 1), energy_kwh=round(energy_delivered_wh/1000, 1)
| bin _time span=1d
| stats count as sessions, avg(session_duration_hrs) as avg_duration, sum(energy_kwh) as total_energy_kwh, dc(station_id) as active_stations, count(eval(status="faulted")) as faulted_count by facility, _time
| lookup ev_station_inventory.csv facility OUTPUTNEW total_stations
| eval utilization_pct=round(active_stations*100/total_stations, 1)
| table _time, facility, sessions, avg_duration, total_energy_kwh, active_stations, total_stations, utilization_pct, faulted_count
```
- **Implementation:** Connect to charging management platform via OCPP or vendor API. Track session starts, energy delivered, and station faults. Monitor utilization rates. Alert on faulted stations. Feed energy data to demand management.
- **Visualization:** Station availability map; energy delivery trend; utilization by time of day; faulted station alerts; session duration histogram.
- **CIM Models:** N/A

---

### UC-14.1.49 · Indoor Air Quality (IAQ) Index Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Post-pandemic, indoor air quality is a top tenant concern. CO2 concentration is a direct proxy for ventilation effectiveness and occupant density. PM2.5, VOCs, and CO2 together create a composite IAQ index that supports WELL Building and RESET Air certification.
- **App/TA:** IAQ sensors (Airthings, Awair, Kaiterra) via API, BACnet IAQ points, Meraki MT
- **Data Sources:** `sourcetype=bms:iaq`, `sourcetype=bms:bacnet`
- **SPL:**
```spl
index=building sourcetype="bms:iaq"
| bin _time span=15m
| stats avg(co2_ppm) as avg_co2, avg(pm25_ugm3) as avg_pm25, avg(tvoc_ppb) as avg_tvoc, avg(temperature_c) as avg_temp, avg(humidity_pct) as avg_rh by zone, floor, building, _time
| eval co2_score=case(avg_co2<600, 100, avg_co2<800, 80, avg_co2<1000, 60, avg_co2<1500, 40, avg_co2>=1500, 20)
| eval pm25_score=case(avg_pm25<12, 100, avg_pm25<25, 80, avg_pm25<35, 60, avg_pm25<55, 40, avg_pm25>=55, 20)
| eval iaq_index=round((co2_score*0.5 + pm25_score*0.3 + if(avg_tvoc<300, 100, 50)*0.2), 0)
| eval iaq_status=case(iaq_index>=80, "Good", iaq_index>=60, "Moderate", iaq_index>=40, "Poor", iaq_index<40, "Unhealthy")
| where iaq_index < 60
| table _time, building, floor, zone, avg_co2, avg_pm25, avg_tvoc, iaq_index, iaq_status
```
- **Implementation:** Deploy IAQ sensors measuring CO2, PM2.5, TVOC, temperature, and humidity. Calculate composite IAQ index weighted by parameter importance. Alert on poor zones. Correlate with HVAC ventilation rates for root cause. Support WELL/RESET certification data logging.
- **Visualization:** IAQ index gauge per zone; floor plan heatmap; CO2 trend with occupancy overlay; certification compliance dashboard.
- **CIM Models:** N/A

---

### UC-14.1.50 · Carbon Emissions Tracking from Building Operations (Scope 1+2)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** ESG reporting increasingly requires Scope 1 (on-site combustion) and Scope 2 (purchased electricity) carbon emissions tracking. Automating carbon calculations from utility meter data provides real-time emissions dashboards and supports Science Based Targets.
- **App/TA:** Utility meters via Modbus, gas meters, BMS energy data, grid emissions factor lookup
- **Data Sources:** `sourcetype=bms:energy`, `sourcetype=bms:meter`
- **SPL:**
```spl
index=building sourcetype="bms:energy"
| bin _time span=1d
| stats sum(eval(if(meter_type="electricity", kwh_consumed, 0))) as electricity_kwh, sum(eval(if(meter_type="gas", therms_consumed, 0))) as gas_therms by building_name, _time
| lookup grid_emissions_factors.csv region OUTPUTNEW kg_co2_per_kwh
| eval scope2_kg=round(electricity_kwh * kg_co2_per_kwh, 1)
| eval scope1_kg=round(gas_therms * 5.3, 1)
| eval total_co2_kg=scope1_kg + scope2_kg
| eval total_co2_tonnes=round(total_co2_kg/1000, 2)
| table _time, building_name, electricity_kwh, gas_therms, scope1_kg, scope2_kg, total_co2_kg, total_co2_tonnes
```
- **Implementation:** Collect electricity (kWh) and gas (therms/m³) consumption from utility meters. Apply grid emissions factors (varying by region and time) for Scope 2. Apply standard combustion factors for Scope 1. Aggregate for ESG reporting. Track against reduction targets.
- **Visualization:** Carbon emissions trend; Scope 1 vs 2 breakdown; building comparison; progress toward reduction target; annual emissions summary for ESG report.
- **CIM Models:** N/A

**Primary App/TA:** Splunk Edge Hub (OPC-UA, Modbus, MQTT protocols), Splunk OT Intelligence (Splunkbase #5180).

---

### UC-14.2.1 · PLC/RTU Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Controller failures halt industrial processes. Monitoring CPU, memory, and communication status prevents unplanned downtime.
- **App/TA:** OPC-UA input, Modbus TA
- **Data Sources:** OPC-UA metrics (CPU, memory, I/O status), Modbus register data
- **SPL:**
```spl
index=ot sourcetype="opcua:metrics"
| where plc_cpu_pct > 80 OR plc_memory_pct > 90 OR comm_status!="OK"
| table _time, plc_name, plc_cpu_pct, plc_memory_pct, comm_status
```
- **Implementation:** Connect to PLCs via OPC-UA server or Modbus gateway through Splunk Edge Hub. Poll health metrics every 30 seconds. Alert on CPU >80%, memory >90%, or communication loss. Track uptime per controller.
- **Visualization:** Status grid (PLC × health), Gauge (CPU/memory per PLC), Line chart (health trend).
- **CIM Models:** N/A

---

### UC-14.2.2 · Process Variable Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Process variables (pressure, flow, temperature) outside normal ranges indicate equipment failure or process upset. Early detection prevents safety incidents.
- **App/TA:** OPC-UA input, Edge Hub anomaly detection
- **Data Sources:** OPC-UA/Modbus process data (analog values)
- **SPL:**
```spl
index=ot sourcetype="opcua:process"
| where value > high_limit OR value < low_limit
| table _time, tag_name, value, low_limit, high_limit, unit
```
- **Implementation:** Ingest process variables via OPC-UA. Define normal ranges per tag. Use Edge Hub kNN anomaly detection for ML-based alerting. Alert on limit exceedances. Track process stability over time.
- **Visualization:** Line chart (process variable with limit bands), Table (out-of-range events), Single value (current value with status color).
- **CIM Models:** N/A

---

### UC-14.2.3 · Safety System Activation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Safety system activations (ESD, interlocks) indicate dangerous conditions. Each activation requires investigation and documentation.
- **App/TA:** Safety PLC logs, OPC-UA events
- **Data Sources:** Safety PLC event logs, emergency shutdown events
- **SPL:**
```spl
index=ot sourcetype="safety_plc"
| search event_type IN ("ESD","interlock_trip","safety_shutdown")
| table _time, system, event_type, cause, action_taken
```
- **Implementation:** Forward safety PLC events to Splunk (isolated network — use data diode or Edge Hub). Alert at critical priority on any safety activation. Maintain incident log for regulatory compliance. Track activation frequency per system.
- **Visualization:** Single value (safety activations — target: 0), Table (activation history), Timeline (safety events).
- **CIM Models:** N/A

---

### UC-14.2.4 · Network Segmentation Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** IT/OT network boundary violations create cybersecurity risk to critical infrastructure. Continuous monitoring validates segmentation.
- **App/TA:** Firewall TAs, network flow data
- **Data Sources:** Industrial firewall logs, network flow data at IT/OT boundary
- **SPL:**
```spl
index=network sourcetype="pan:traffic" zone_pair="IT-to-OT"
| where action="allow"
| stats count by src, dest, dest_port, app
| sort -count
```
- **Implementation:** Forward IT/OT boundary firewall logs. Monitor all traffic crossing the boundary. Alert on unexpected protocols or connections. Validate against whitelist of approved communications. Report for ICS security audits.
- **Visualization:** Table (cross-boundary traffic), Sankey diagram (IT→OT flows), Bar chart (by protocol), Single value (unauthorized connections).
- **CIM Models:** N/A

---

### UC-14.2.5 · Firmware Version Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** OT devices with outdated firmware are vulnerable to exploitation. Inventory tracking supports patching during maintenance windows.
- **App/TA:** Scripted inventory input, OPC-UA
- **Data Sources:** Asset inventory scans, OPC-UA system attributes
- **SPL:**
```spl
index=ot sourcetype="ics_inventory"
| stats latest(firmware_version) as current by device_name, vendor, model
| lookup approved_firmware.csv vendor, model OUTPUT approved_version
| where current!=approved_version
| table device_name, vendor, model, current, approved_version
```
- **Implementation:** Conduct periodic OT asset inventory scans (during maintenance windows). Ingest firmware versions. Maintain approved firmware lookup. Report on compliance. Prioritize based on CISA ICS advisories.
- **Visualization:** Table (devices with outdated firmware), Pie chart (compliance distribution), Single value (% compliant).
- **CIM Models:** N/A

---

### UC-14.2.6 · Unauthorized Access Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unauthorized access to ICS systems could lead to physical damage or safety incidents. Detection is critical for industrial cybersecurity.
- **App/TA:** Firewall TAs, ICS network monitoring
- **Data Sources:** ICS network logs, industrial firewalls, IDS alerts
- **SPL:**
```spl
index=ot sourcetype="ics_firewall"
| search action="deny" OR src_zone="untrusted"
| stats count by src, dest, dest_port
| sort -count
```
- **Implementation:** Monitor access to ICS networks from all sources. Alert on connections from non-whitelisted IPs. Track engineering workstation access sessions. Correlate with physical access to control rooms. Report for ICS cybersecurity compliance.
- **Visualization:** Table (access events), Timeline (unauthorized attempts), Bar chart (blocked connections by source).
- **CIM Models:** N/A


---

### UC-14.2.7 · Modbus TCP Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Unusual read/write rates or register ranges can indicate process upset or malicious manipulation.
- **App/TA:** Splunk OT Intelligence, Modbus TA
- **Data Sources:** `sourcetype="modbus:traffic"` or `modbus:gateway`
- **SPL:**
```spl
index=ot sourcetype="modbus:traffic"
| bin _time span=5m
| stats count by _time, unit_id, function_code, src
| eventstats median(count) as med by unit_id, function_code
| where count > med * 5 AND count > 100
```
- **Implementation:** Baseline requests per 5m per unit and function code. Use MLTK or `eventstats` for median. Alert on spikes without corresponding maintenance window.
- **Visualization:** Line chart (Modbus req rate), Table (anomalous unit × function), Heatmap (time × unit).
- **CIM Models:** N/A

---

### UC-14.2.8 · OPC-UA Session Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Excessive sessions or anonymous binds from new clients can indicate scanning or unauthorized access.
- **App/TA:** OPC-UA server audit logs, Edge Hub
- **Data Sources:** `sourcetype="opcua:session"` (server audit events)
- **SPL:**
```spl
index=ot sourcetype="opcua:session"
| where event_type IN ("CreateSession","ActivateSession") AND (is_anonymous=1 OR rejected=1)
| stats dc(session_id) as sessions, dc(client_ip) as clients by server_endpoint, _time span=1h
| where sessions > 50 OR clients > 10
```
- **Implementation:** Ingest OPC-UA audit events. Whitelist known engineering hosts. Alert on anonymous session creation or high rejection rate.
- **Visualization:** Table (servers with suspicious sessions), Bar chart (sessions by client IP).
- **CIM Models:** N/A

---

### UC-14.2.9 · PLC Firmware Change Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Change
- **Value:** Unexpected firmware changes on PLCs can be maintenance errors or malicious reprogramming.
- **App/TA:** PLC vendor export, OPC-UA device metadata
- **Data Sources:** `sourcetype="plc:inventory"` (firmware, serial)
- **SPL:**
```spl
index=ot sourcetype="plc:inventory"
| streamstats current=firmware_version window=2 global=f by plc_name
| where firmware_version!=f
| table _time, plc_name, f, firmware_version, user
```
- **Implementation:** Snapshot firmware nightly or on change event from vendor tool. Correlate with change tickets. Alert on any drift without CMDB match.
- **Visualization:** Timeline (firmware changes), Table (PLCs with unexpected version).
- **CIM Models:** N/A

---

### UC-14.2.10 · ICS Protocol Violation Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Malformed DNP3/Modbus/Profinet frames or wrong L4 ports indicate misconfiguration or attacks.
- **App/TA:** Industrial IDS, Zeek ICS parsers
- **Data Sources:** `sourcetype="ics:protocol"` IDS alerts
- **SPL:**
```spl
index=ot sourcetype="ics:protocol"
| where severity IN ("high","critical") OR match(message,"(?i)(malformed|illegal|out.of.range)")
| stats count by protocol, src, dest, signature
| sort -count
```
- **Implementation:** Normalize IDS fields into Splunk. Tune for false positives on legacy equipment. Route critical to SOC and OT jointly.
- **Visualization:** Table (violations), Timeline (events), Sankey (src → dest).
- **CIM Models:** N/A

---

### UC-14.2.11 · NERC CIP Compliance Checks
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Compliance
- **Industry:** Energy and Utilities
- **Value:** Evidence of electronic access controls, logging, and change management for bulk electric systems.
- **App/TA:** Custom (CIP evidence packs), Splunk Enterprise Security
- **Data Sources:** Firewall, VPN, AD, asset logs tagged `nerc_cip`
- **SPL:**
```spl
index=security sourcetype IN ("vpn:log","firewall:traffic") nerc_cip=1
| where action="deny" OR match(user,"(?i)orphan")
| stats count by asset_id, control_id, evidence_type
```
- **Implementation:** Tag in-scope assets and controls. Use saved searches per CIP requirement (e.g., access logging, 30-day log retention). Document in Splunk as authoritative evidence store.
- **Visualization:** Compliance dashboard (control × status), Table (gaps by site).
- **CIM Models:** N/A

---

### UC-14.2.12 · Historian Data Integrity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Gaps or duplicated timestamps in historian feeds break batch quality and regulatory reporting.
- **App/TA:** PI / OPC-UA historian export
- **Data Sources:** `sourcetype="historian:point"` (value, quality, ts)
- **SPL:**
```spl
index=ot sourcetype="historian:point"
| sort 0 + _time
| streamstats window=2 global=prev
| eval gap_sec=_time-prev_ts
| where gap_sec > 300 OR quality!="Good"
| stats count by tag_name, gap_sec
```
- **Implementation:** Ingest quality codes and source timestamps. Alert on gap > SLA or bad quality >10% of samples per tag group.
- **Visualization:** Line chart (insert rate), Table (tags with gaps), Single value (data quality %).
- **CIM Models:** N/A

---

### UC-14.2.13 · Safety Instrumented System Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** SIS trips, bypasses, and diagnostics demand immediate visibility and audit trails.
- **App/TA:** SIS vendor DCS export, OPC-UA alarms
- **Data Sources:** `sourcetype="sis:event"` (trip, bypass, fault)
- **SPL:**
```spl
index=ot sourcetype="sis:event"
| where event_type IN ("trip","bypass","fault","demand")
| table _time, sis_tag, event_type, cause, sil_level
| sort -_time
```
- **Implementation:** Segregate SIS data per safety policy. Never route writes from IT networks. Alert on any bypass or fault.
- **Visualization:** Timeline (SIS events), Single value (active bypasses), Table (trip history).
- **CIM Models:** N/A

---

### UC-14.2.14 · HMI Unauthorized Access
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** HMIs should only be reachable from jump hosts; direct access from corporate networks is a red flag.
- **App/TA:** HMI audit logs, RDP/VNC syslog
- **Data Sources:** `sourcetype="hmi:audit"` (login, operator action)
- **SPL:**
```spl
index=ot sourcetype="hmi:audit"
| where action="login" AND NOT cidrmatch("10.50.0.0/16",src)
| stats count by src, hmi_name, user
| sort -count
```
- **Implementation:** Define allowed HMI source subnets. Alert on logins from outside. Correlate with physical access.
- **Visualization:** Table (non-compliant logins), Map (source IP).
- **CIM Models:** N/A

---

### UC-14.2.15 · Control Loop Deviation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** PV diverging from SP with saturated output indicates tuning issues or actuator faults.
- **App/TA:** OPC-UA process tags
- **Data Sources:** `sourcetype="opcua:control"` (pv, sp, out)
- **SPL:**
```spl
index=ot sourcetype="opcua:control"
| eval err=abs(pv-sp)
| where err > deadband*5 OR (abs(out)>95 AND err>deadband)
| timechart span=1m avg(err) by loop_id
```
- **Implementation:** Define deadband per loop. Alert when sustained error exceeds threshold or output pegs. Integrate with maintenance CMMS.
- **Visualization:** Line chart (PV vs SP), Gauge (loop error), Table (loops in alarm).
- **CIM Models:** N/A

---

### UC-14.2.16 · Process Variable Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Slow drift before alarm limits supports predictive maintenance and energy optimization.
- **App/TA:** OPC-UA historian
- **Data Sources:** `sourcetype="opcua:process"`
- **SPL:**
```spl
index=ot sourcetype="opcua:process"
| timechart span=1h avg(value) as avg_val by tag_name
| predict avg_val as pred future_timespan=24
| where pred > high_limit OR pred < low_limit
```
- **Implementation:** Use `predict` for critical tags. Alert when forecast crosses limits before physical alarm. Tune per process area.
- **Visualization:** Line chart (actual vs predicted), Table (tags trending to limit).
- **CIM Models:** N/A

---

### UC-14.2.17 · ICS Network Segmentation Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Hosts in wrong VLANs or east-west traffic across zones violates Purdue model and IEC 62443.
- **App/TA:** Firewall, switch NetFlow, ARP tables
- **Data Sources:** `sourcetype="pan:traffic"` `zone_pair` or `sourcetype="flow:ics"`
- **SPL:**
```spl
index=network sourcetype="flow:ics"
| where src_zone!=dest_zone AND allowed_pair="false"
| stats count by src, dest, dest_port, app
| sort -count
```
- **Implementation:** Maintain `allowed_pair` lookup for zone-to-zone. Alert on any deny or unexpected allow. Quarterly review.
- **Visualization:** Sankey (zones), Table (violations), Single value (open violations).
- **CIM Models:** N/A

---

### UC-14.2.18 · Engineering Workstation Anomaly
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** USB inserts, new binaries, or remote sessions on EWS workstations are high-risk in OT.
- **App/TA:** EDR on EWS, Windows Security / Sysmon
- **Data Sources:** `sourcetype="sysmon:windows"` `tag=ews`
- **SPL:**
```spl
index=ot sourcetype="sysmon:windows" host_tag="EWS"
| search EventCode=1 OR EventCode=11
| where NOT match(Image,"(?i)(approved\\\\path)")
| stats count by Computer, Image, ParentImage
| sort -count
```
- **Implementation:** Lock down EWS to approved paths. Alert on new process or driver load. Correlate with maintenance windows.
- **Visualization:** Table (suspicious processes), Timeline (EWS events).
- **CIM Models:** N/A

---

### UC-14.2.19 · OT Asset External Communication Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** PLCs, HMIs, or sensors initiating outbound sessions to the internet or untrusted zones indicate misconfiguration, malware, or pivot from IT — a top IEC 62443 / NERC CIP concern.
- **App/TA:** Firewall, OT NetFlow, passive tap (Zeek OT)
- **Data Sources:** `sourcetype="flow:ics"`, `sourcetype="pan:traffic"` with OT zone tags
- **SPL:**
```spl
index=ot sourcetype="flow:ics" src_zone="OT_L3"
| lookup ot_asset_inventory ip as src OUTPUT asset_class
| lookup vendor_update_nets network as dest OUTPUT network as vendor_net
| where NOT cidrmatch("10.0.0.0/8",dest) AND isnull(vendor_net)
| stats count, values(dest_port) as ports by src, dest, app
| sort -count
```
- **Implementation:** Maintain allowlisted update CDNs and remote-support jump hosts; default-deny egress from L3 devices. Alert on first-seen external `dest`.
- **Visualization:** Map (flows), Table (assets), Sankey (zone → egress).
- **CIM Models:** N/A

---

### UC-14.2.20 · OT Protocol Port Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unexpected Modbus, DNP3, or EtherNet/IP ports on non-asset IPs reveal rogue devices or scanning.
- **App/TA:** SPAN / Zeek OT, industrial firewall
- **Data Sources:** `sourcetype="zeek:conn"` with OT VLANs, `sourcetype="ics:protocol"`
- **SPL:**
```spl
index=ot (sourcetype="zeek:conn" OR sourcetype="ics:protocol")
| where dest_port IN (502,20000,44818,2404) OR service IN ("modbus","dnp3","enip")
| lookup ot_authorized_peers src dest OUTPUT approved
| where approved!="true"
| stats count by src, dest, dest_port, service
| sort -count
```
- **Implementation:** Pair with asset inventory; tune for engineering laptops in maintenance windows.
- **Visualization:** Table (unexpected sessions), Bar chart (port mix), Timeline.
- **CIM Models:** N/A

---

### UC-14.2.21 · Removable Media in OT Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** USB events on HMIs or engineering stations violate many site policies and are common malware vectors.
- **App/TA:** Windows Security, EDR (where allowed on EWS), USB control agents
- **Data Sources:** `sourcetype="WinEventLog:Security"` EventCode=6416, `sourcetype="sysmon:windows"` EventCode=11
- **SPL:**
```spl
index=ot (sourcetype="WinEventLog:Security" EventCode=6416) OR (sourcetype="sysmon:windows" EventCode=11)
| search Computer IN ("*HMI*","*EWS*") OR tag=ot_workstation
| stats count by Computer, DeviceDescription, User, Image
| sort -_time
```
- **Implementation:** Physical port block by default; break-glass USB with logged approval ticket.
- **Visualization:** Table (USB events), Timeline, Single value (events per shift).
- **CIM Models:** N/A

---

### UC-14.2.22 · OT/IT Boundary Traffic Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Baselines permitted jump-server, patch, and historian replication across the Purdue boundary; flags new apps or volume spikes.
- **App/TA:** Firewall, data diode logs (if bidirectional return path exists)
- **Data Sources:** `sourcetype="pan:traffic"` `zone_pair`, `sourcetype="flow:ics"`
- **SPL:**
```spl
index=network sourcetype="pan:traffic" zone_pair="IT_DMZ_to_OT_L3"
| bin _time span=1h
| stats sum(bytes) as b, dc(dest_port) as ports by app, _time
| eventstats avg(b) as baseline by app
| where b > 3*baseline AND ports>5
| sort -b
```
- **Implementation:** Document each allowed application; use application-aware rules; quarterly rule review with OT owners.
- **Visualization:** Line chart (bytes by app), Table (anomalies), Heatmap (hour × app).
- **CIM Models:** N/A

---

### UC-14.2.23 · ICS Change Management Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Logic downloads, firmware pushes, or HMI project changes without a linked work order break IEC 62443 SR-7 / internal change policy.
- **App/TA:** PLC programming tools audit, engineering station logs
- **Data Sources:** `sourcetype="plc:download"`, `sourcetype="tia:audit"`
- **SPL:**
```spl
index=ot sourcetype="plc:download"
| lookup cmms_work_orders change_id OUTPUT wo_status requester
| where isnull(wo_status) OR wo_status!="approved"
| stats count by plc_name, engineer_id, project_version
| sort -count
```
- **Implementation:** Require pre-approved WO for all downloads; correlate with maintenance windows from MES.
- **Visualization:** Table (unauthorized downloads), Bar chart (by line), Gantt (WO vs. event time).
- **CIM Models:** N/A

---

### UC-14.2.24 · Production Line Downtime Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Industry:** Manufacturing
- **Value:** Correlates controller faults, jam sensors, and Andon events for OEE and root-cause — feeds continuous improvement.
- **App/TA:** MES, PLC fault bits, SCADA alarms
- **Data Sources:** `sourcetype="mes:line_status"`, `sourcetype="opcua:alarm"`
- **SPL:**
```spl
index=ot sourcetype="mes:line_status"
| where state="DOWN" OR fault_code!=0
| transaction line_id maxspan=24h startswith="state=UP" endswith="state=DOWN" keepevicted=true
| eval downtime_min=duration/60
| stats sum(downtime_min) as total_down, count as stops by line_id, shift
| sort -total_down
```
- **Implementation:** Normalize fault codes to reason trees; exclude planned changeovers via MES schedule lookup.
- **Visualization:** Bar chart (downtime by line), Timeline (stops), Single value (MTBF).
- **CIM Models:** N/A

---

### UC-14.2.25 · OEE Metrics Collection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Industry:** Manufacturing
- **Value:** Availability × Performance × Quality from SCADA/MES tags — executive and plant KPIs.
- **App/TA:** Historian, OPC-UA, MES
- **Data Sources:** `sourcetype="opcua:tag"`, `sourcetype="historian:sample"`
- **SPL:**
```spl
index=ot sourcetype="opcua:tag" tag=oee
| bin _time span=1h
| stats avg(availability_pct) as A, avg(performance_pct) as P, avg(quality_pct) as Q by line_id, _time
| eval oee=round((A*P*Q)/10000,2)
| where oee < 0.75
| sort _time
```
- **Implementation:** Align tag naming per ISA-95; validate against manual OEE samples monthly.
- **Visualization:** Line chart (OEE trend), Gauge (current OEE), Bar chart (loss buckets).
- **CIM Models:** N/A

---

### UC-14.2.26 · Batch Process Deviation Alerting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Quality, Safety
- **Industry:** Manufacturing
- **Value:** Recipe phase duration, temperature, or agitator speed outside limits risks scrap or unsafe reactions.
- **App/TA:** Batch executive (S88), historian
- **Data Sources:** `sourcetype="batch:phase"`, `sourcetype="historian:sample"`
- **SPL:**
```spl
index=ot sourcetype="batch:phase" batch_id=*
| lookup recipe_limits recipe phase OUTPUT min_temp max_temp max_duration_sec
| where temp_c < min_temp OR temp_c > max_temp OR phase_duration_sec > max_duration_sec
| stats latest(batch_id) as batch, values(phase) as phases by reactor_id
| sort -_time
```
- **Implementation:** Integrate with quality hold workflow; electronic signatures for parameter overrides.
- **Visualization:** Table (deviations), Control chart (temp), Timeline (phases).
- **CIM Models:** N/A

---

### UC-14.2.27 · EDI Acknowledgement Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operations
- **Industry:** Manufacturing
- **Value:** Missing 997/999/CONTRL acks for ASNs or orders disrupt supply-chain and inventory — common in automotive / discrete manufacturing.
- **App/TA:** B2B gateway (IBM/Seeburger), VAN logs
- **Data Sources:** `sourcetype="edi:control"`, `sourcetype="as2:mdn"`
- **SPL:**
```spl
index=edi sourcetype="edi:control"
| stats earliest(_time) as sent latest(ack_time) as ack by interchange_id, doc_type, partner_id
| eval ack_latency_sec=ack-sent
| where isnull(ack) OR ack_latency_sec>3600
| sort -sent
```
- **Implementation:** SLA per trading partner; auto-retry and partner escalation on NAK codes.
- **Visualization:** Table (late/missing acks), Line chart (ack latency trend), Bar chart (by partner).
- **CIM Models:** N/A

---

### UC-14.2.28 · Supplier Delivery Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operations
- **Value:** On-time delivery % and lead-time variance from ASN/OTIF feeds support supplier scorecards and production planning.
- **App/TA:** TMS, EDI 856/855, MES receipts
- **Data Sources:** `sourcetype="edi:asn"`, `sourcetype="wms:receipt"`
- **SPL:**
```spl
index=supply sourcetype="edi:asn"
| eval on_time=if(actual_arrival <= promised_date,1,0)
| stats sum(on_time) as ot, count as total, avg((actual_arrival-promised_date)/86400) as avg_late_days by supplier_id
| eval otif_pct=round(100*ot/total,1)
| sort otif_pct
| head 20
```
- **Implementation:** Join to GRN for quantity accuracy; exclude force majeure with reason codes.
- **Visualization:** Bar chart (OTIF % by supplier), Table (worst performers), Trend (rolling 13 weeks).
- **CIM Models:** N/A

---

### 14.3 Splunk Edge Hub

**Primary App/TA:** Splunk Edge Hub (hardware device), Splunk OT Intelligence (Splunkbase #5180). Sensor data flows as metrics via HEC to dedicated indexes.

---

### UC-14.3.1 · Temperature Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Edge-based kNN anomaly detection provides faster response than cloud-based processing for critical temperature monitoring in data centers and industrial environments.
- **App/TA:** Splunk Edge Hub (built-in kNN model), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `index=edge-hub-anomalies` (anomaly metrics), `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(_value) as avg_temp
  where index=edge-hub-data AND metric_name=temperature
  span=5m by extracted_host
| where avg_temp > 35 OR avg_temp < 10

| comment "Anomaly query"
| mstats count where index=edge-hub-anomalies AND metric_name=temperature AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Deploy Edge Hub device (IP66-rated, built-in temperature sensor ±0.2°C accuracy). Enable kNN anomaly detection via the Edge Hub mobile app — toggle "Anomaly Detection" on the temperature sensor tile. Sensor data streams as metrics to `edge-hub-data` index; anomalies to `edge-hub-anomalies` index via HEC. Create alerts on anomaly count spikes. Optional: attach external I²C temperature probes via the 3.5mm jack for additional measurement points.
- **Visualization:** Line chart (mstats temperature trend by device), Single value (current temperature), Timeline (anomaly events from edge-hub-anomalies).
- **CIM Models:** N/A

---

### UC-14.3.2 · Vibration & Motion Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Equipment vibration changes indicate bearing wear, misalignment, or imbalance. Edge Hub's built-in 3-axis accelerometer and gyroscope enable predictive maintenance without external sensors.
- **App/TA:** Splunk Edge Hub (built-in sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in 3-axis accelerometer + 6-axis gyroscope
- **SPL:**
```spl
| mstats avg(_value) as avg_accel
  where index=edge-hub-data AND metric_name IN (accelerometer_x, accelerometer_y, accelerometer_z)
  span=5m by metric_name, extracted_host
| eval rms = sqrt(pow(avg_accel, 2))

| comment "Anomaly-based approach"
| mstats count where index=edge-hub-anomalies AND metric_name="accelerometer*" AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Mount Edge Hub near rotating equipment (IP66 enclosure suits industrial environments, operating -40°C to 80°C). The built-in accelerometer and gyroscope stream metrics to `edge-hub-data`. Enable kNN anomaly detection via the mobile app for each axis. Deploy MLTK Smart Outlier Detection model for more advanced analysis (requires OT Intelligence 4.8.0+ and Edge Hub OS 2.0+). Alert on anomaly detections. Note: one ML model per sensor; performance degrades with 2+ concurrent models.
- **Visualization:** Line chart (accelerometer axes over time), Single value (current RMS), Timeline (anomaly events).
- **CIM Models:** N/A

---

### UC-14.3.3 · Air Quality & VOC Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Indoor air quality affects occupant health and productivity. Edge Hub's optional VOC sensor provides IAQ scoring for workplace wellness monitoring.
- **App/TA:** Splunk Edge Hub (optional air quality sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in VOC sensor (optional, <1s response, IAQ score)
- **SPL:**
```spl
| mstats avg(_value) as avg_iaq
  where index=edge-hub-data AND metric_name IN (voc, iaq_score)
  span=15m by metric_name, extracted_host
| where metric_name="iaq_score" AND avg_iaq > 200

| comment "Combined with humidity for comfort index"
| mstats avg(_value) as value
  where index=edge-hub-data AND metric_name IN (voc, humidity, temperature)
  span=15m by metric_name, extracted_host
```
- **Implementation:** Deploy Edge Hub with optional VOC/air quality sensor module. The sensor provides IAQ (Indoor Air Quality) score with <1 second response time. Data streams as metrics to `edge-hub-data` index. Note: Edge Hub measures VOC and IAQ score — it does not have a CO2 or PM2.5 sensor natively. For CO2/PM2.5, connect external sensors via MQTT or I²C. Alert when IAQ score exceeds thresholds. Correlate with humidity sensor data for comfort indexing.
- **Visualization:** Line chart (IAQ score over time), Gauge (current IAQ), Multi-metric dashboard (VOC + humidity + temperature).
- **CIM Models:** N/A

---

### UC-14.3.4 · Sound Level Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unusual sound patterns near equipment indicate mechanical issues. Edge Hub's stereo microphone enables acoustic monitoring without external sensors.
- **App/TA:** Splunk Edge Hub (built-in stereo microphone), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in stereo microphone
- **SPL:**
```spl
| mstats avg(_value) as avg_db
  where index=edge-hub-data AND metric_name=sound_level
  span=5m by extracted_host
| where avg_db > 85

| comment "Anomaly detection"
| mstats count where index=edge-hub-anomalies AND metric_name=sound_level AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Deploy Edge Hub near critical equipment. The built-in stereo microphone captures ambient sound levels. Enable kNN anomaly detection to baseline normal patterns and detect deviations. Alert on sustained high levels (OSHA >85dB threshold) and sudden changes (potential equipment failure). Sound data streams as metrics to `edge-hub-data`; anomalies to `edge-hub-anomalies`.
- **Visualization:** Line chart (sound level trend), Single value (current dB), Timeline (anomaly events).
- **CIM Models:** N/A

---

### UC-14.3.5 · MQTT Device Integration Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Edge Hub's built-in MQTT broker aggregates IoT sensor data from external devices. Monitoring broker health ensures data pipeline reliability.
- **App/TA:** Splunk Edge Hub (built-in MQTT broker), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics from MQTT topics), `index=edge-hub-logs sourcetype=splunk_edge_hub_log` (broker logs)
- **SPL:**
```spl
| comment "Metrics from MQTT-connected sensors"
| mstats avg(_value) as avg_v
  where index=edge-hub-data AND metric_name=temperature_celsius
  span=1m by extracted_host

| comment "Broker health via device logs"
index=edge-hub-logs sourcetype=splunk_edge_hub_log "mqtt" OR "broker"
| stats count by log_level, message
```
- **Implementation:** Configure MQTT topics via Edge Hub Advanced Settings → MQTT tab. Create metric or event topic subscriptions with transformations (metric name, dimensions, timestamps). External IoT devices publish to Edge Hub's built-in MQTT broker (port 1883). Data is transformed and forwarded to Splunk via HEC. For TLS-secured external brokers, upload certificates via Advanced Settings → MQTT → TLS Configuration. Monitor for disconnected publishers and message rate drops.
- **Visualization:** Line chart (MQTT metric trends), Table (connected device inventory), Single value (active MQTT topics).
- **CIM Models:** N/A

---

### UC-14.3.6 · SNMP Device Polling from Edge
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Edge Hub bridges OT/IT network segmentation by polling SNMP-enabled devices on isolated networks and forwarding data to Splunk Cloud.
- **App/TA:** Splunk Edge Hub (SNMP integration), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-snmp sourcetype=edge_hub` — SNMP polls via Edge Hub to local devices
- **SPL:**
```spl
index=edge-hub-snmp hub_name="datacenter-eh-01" sourcetype=edge_hub
| stats latest(value) as current by oid_alias
| table oid_alias, current

| comment "Monitor polling health"
index=edge-hub-logs sourcetype=splunk_edge_hub_log "snmp" ("timeout" OR "unreachable")
| stats count by host, message
```
- **Implementation:** Configure SNMP polling via Edge Hub Advanced Settings → SNMP tab. Add devices by IP, set SNMP version (v1/v2c/v3), community string or v3 credentials, and define OIDs with aliases. Set polling interval (default 60s). Edge Hub polls local OT devices and forwards results to `edge-hub-snmp` index via HEC. This bridges the air-gap — enterprise Splunk never touches the OT network directly. Alert on device unreachability or metric threshold violations.
- **Visualization:** Table (device OID values), Status grid (device × poll status), Line chart (metric trends).
- **CIM Models:** N/A

---

### UC-14.3.7 · Edge-to-Cloud Data Pipeline Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Edge Hub pipeline health ensures IoT/OT data reaches Splunk. A disconnected Edge Hub creates blind spots — the device backlogs up to 3M sensor data points locally in SQLite.
- **App/TA:** Splunk Edge Hub (system health), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health sourcetype=edge_hub` (device health metrics), `index=edge-hub-logs sourcetype=splunk_edge_hub_log` (system logs)
- **SPL:**
```spl
| comment "Device resource health"
index=edge-hub-health sourcetype=edge_hub
| stats latest(cpu_usage) as CPU, latest(memory_usage) as Memory,
        latest(disk_usage) as Disk by host
| eval Health=if(CPU<80 AND Memory<80 AND Disk<80, "Healthy", "Warning")

| comment "Connectivity and forwarding issues"
index=edge-hub-logs sourcetype=splunk_edge_hub_log
  ("connection" OR "unreachable" OR "timeout")
| timechart count by log_level
```
- **Implementation:** Edge Hub streams device health data to `edge-hub-health` index and system logs to `edge-hub-logs` index. The device checks Splunk reachability every 15 seconds — LED ring shows green (connected) or red (disconnected). When disconnected, data backlogs locally: 3M sensor data points and 100K health/logs/anomalies/SNMP entries each (FIFO, batches of 100 via HEC on reconnect). Monitor CPU, memory, disk utilization on the device. Alert on connectivity loss or sustained high resource usage.
- **Visualization:** Single value (connectivity status with LED color mapping), Gauge (CPU/memory/disk), Line chart (forwarding rate over time).
- **CIM Models:** N/A

---


---

### UC-14.3.9 · Cold Storage Room Temperature Excursion Alert
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Ensures pharmaceutical, food, or vaccine storage integrity by alerting within minutes of unplanned temperature rise.
- **App/TA:** Splunk Edge Hub (temperature sensor ±0.2°C), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp by host, _time span=5m
| eval expected_range="[-20,-15]"
| where temp > -15 OR temp < -20
| eval deviation=if(temp > -15, temp - (-15), (-20) - temp)
| stats count as excursion_count, max(deviation) as max_deviation by host
| where excursion_count >= 3
```
- **Implementation:** Configure temperature sensor with Advanced Settings → Alerts enabled at -15°C upper threshold. Store locally for 30 minutes via SQLite backlog. For sub-zero operation, verify Edge Hub -40°C to 80°C operating range covers your environment. MQTT topic subscription can include external low-cost temp probes via I²C port (3.5mm jack).
- **Visualization:** Single-value alert indicator, time-series trend, deviation log.
- **CIM Models:** N/A

---

---

### UC-14.3.10 · Museum & Archive Climate Control Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Documents preservation requirements (typically 18-21°C, 35-45% RH) for regulatory compliance and insurance.
- **App/TA:** Splunk Edge Hub (temperature + humidity dual sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature OR metric_name=humidity, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh by host, _time span=10m
| eval temp_compliant=if(temp>=18 AND temp<=21, 1, 0), rh_compliant=if(rh>=35 AND rh<=45, 1, 0)
| eval compliance_score=((temp_compliant + rh_compliant) / 2) * 100
| stats avg(compliance_score) as avg_compliance, count as hours by host
| where avg_compliance < 95
```
- **Implementation:** Mount Edge Hub in archival vault with sensors in passive airflow zone. Configure 10-minute polling intervals via Advanced Settings → Sensor Polling for daily compliance reporting. Use edge-hub-health index to track sensor drift (humidity can drift ±5% annually). Maintain audit trail in edge-hub-logs for regulatory documentation.
- **Visualization:** Compliance scorecard, historical trend, excursion timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.11 · Greenhouse Humidity & Growth Optimization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Optimizes plant growth rates by maintaining ideal VPD (vapor pressure deficit) and reducing fungal disease risk.
- **App/TA:** Splunk Edge Hub (humidity + temperature + optional light sensor), custom edge.json container
- **Data Sources:** `index=edge-hub-data` metric_name=humidity OR metric_name=temperature OR metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh, max(light_level) as lux by host, _time span=1h
| eval sat_pressure=610.5*exp((17.27*temp)/(temp+237.7))
| eval vpd=(sat_pressure*(100-rh)/100)/1000
| eval growth_optimal=if(vpd>=0.8 AND vpd<=1.5 AND temp>=20 AND temp<=28, "YES", "NO")
| stats count(eval(growth_optimal="YES")) as optimal_hours, count as total_hours by host
| eval growth_score=(optimal_hours/total_hours)*100
```
- **Implementation:** Deploy Edge Hub with external humidity/temp probe via I²C (3.5mm jack) placed in plant canopy zone. Optional light sensor integration measures lux for photosynthesis optimization. Build custom ARM64 container to interface with greenhouse HVAC controller via Modbus TCP (port 502) for automated adjustment. Store 3M data points locally for real-time analytics without cloud latency.
- **Visualization:** VPD gauge, growth score trend, hourly optimization heatmap.
- **CIM Models:** N/A

---

---

### UC-14.3.12 · Security Camera Motion Detection with Light Level Correlation
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Security
- **Value:** Reduces false motion alerts by correlating camera motion events with ambient light levels and eliminating day/night false positives.
- **App/TA:** Splunk Edge Hub (light sensor + USB camera container with NPU), v2.1+
- **Data Sources:** `index=edge-hub-data` metric_name=light, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log, camera motion event
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log motion_detected=true
| join max=1 host [| mstats avg(light_level) as lux by host, _time span=5m | where lux < 10]
| stats count as false_positives by host
| eval false_positive_rate=(false_positives / (false_positives + true_detections)) * 100
```
- **Implementation:** Deploy Edge Hub with USB camera attached (requires USB device passthrough v2.1+). Build custom ARM64 container with OpenCV + NPU inference for motion detection. Filter detections with built-in ambient light sensor: suppress alerts when lux < 10 (night) or > 50000 (direct sun glare). Configure edge.json manifest with resource limits (memory: 256MB, CPU: 1 core) to avoid impacting sensor polling.
- **Visualization:** Motion vs light correlation scatter, false positive trend, alert effectiveness dashboard.
- **CIM Models:** N/A

---

---

### UC-14.3.13 · Energy Management & HVAC Occupancy-Based Control
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Reduces HVAC energy consumption 15-30% by correlating occupancy detection with temperature setpoints.
- **App/TA:** Splunk Edge Hub (light + USB camera + custom container), Modbus TCP actuator control
- **Data Sources:** `index=edge-hub-data` metric_name=light, `index=edge-hub-logs` camera_occupancy_count, `index=edge-hub-logs` sourcetype=edge_hub modbus_register
- **SPL:**
```spl
| mstats avg(light_level) as lux by host, _time span=15m
| join max=1 host [index=edge-hub-logs camera_occupancy_count > 0 | stats count as people_detected by host, _time span=15m]
| eval hvac_mode=case(people_detected > 0 AND lux < 500, "COMFORT", people_detected = 0 AND lux > 500, "ECO", 1=1, "TRANSITION")
| stats count by hvac_mode, host
```
- **Implementation:** Deploy custom ARM64 container with TensorFlow Lite occupancy counting model (CNN) running on NPU. Integrate Modbus TCP gateway to read/write HVAC controller setpoint registers (port 502). Use light sensor as secondary occupancy indicator. Configure container resource limits to ensure 30-second sensor polling remains unaffected. Implement local alerting logic in container to adjust setpoint without cloud round-trip latency.
- **Visualization:** Occupancy vs light scatter, energy savings trend, HVAC mode timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.14 · Warehouse Inventory Light-Based Shelf Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Detects empty or partially depleted shelves in real-time by monitoring light pattern changes in high-bay storage.
- **App/TA:** Splunk Edge Hub (light sensor array), custom container for pattern recognition
- **Data Sources:** `index=edge-hub-data` metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(light_level) as lux by host, rack_id, shelf_position, _time span=5m
| delta lux as lux_change
| eval significant_change=if(abs(lux_change) > 20, "YES", "NO")
| stats count(eval(significant_change="YES")) as change_events, avg(lux) as avg_lux by host, rack_id, shelf_position
| where change_events > 5
| eval inventory_status=case(avg_lux > 1000, "EMPTY", avg_lux > 500, "LOW", 1=1, "STOCKED")
```
- **Implementation:** Mount Edge Hub light sensor facing shelving unit. Deploy custom Python container that learns baseline light patterns for each shelf over 1-week baseline period. Use machine learning to detect sustained light increases (empty shelf) vs brief shadows (restocking activity). Reference Advanced Settings → Containers tab to set container polling interval to 5 minutes. Store 3M light data points locally for historical baseline calculation.
- **Visualization:** Shelf occupancy heatmap, light level trend by shelf, inventory status dashboard.
- **CIM Models:** N/A

---

---

### UC-14.3.15 · Structural Health Monitoring via Vibration Baseline Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault
- **Value:** Detects early-stage structural degradation (loose bolts, bearing wear) before catastrophic failure by monitoring vibration signature drift.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + 6-axis gyroscope), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=acceleration_x OR acceleration_y OR acceleration_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(acceleration_x) as ax, avg(acceleration_y) as ay, avg(acceleration_z) as az by host, _time span=10m
| eval vibration_magnitude=sqrt((ax^2 + ay^2 + az^2))
| eval baseline=avg(vibration_magnitude)
| relative_entropy baseline, vibration_magnitude
| where vibration_magnitude > (baseline * 1.5)
| stats count as anomalies, max(vibration_magnitude) as peak_mag by host
```
- **Implementation:** Mount Edge Hub on bridge structure, machinery frame, or building floor with accelerometer facing primary load direction. Collect 7-day baseline using kNN built-in anomaly detection (one model per sensor). Enable MLTK Smart Outlier Detection v4.8.0+ for drift tracking over months. Store 3M data points locally for baseline comparison. Note: MQTT sensors only support MLTK; if using built-in accelerometer, use built-in kNN algorithm.
- **Visualization:** Vibration magnitude trend, baseline drift scatter, anomaly frequency timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.16 · Door Open/Close Detection via Accelerometer Tilt
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors facility access by detecting door swing events without motion sensors or contact switches.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer with gravity component), custom edge.json container
- **Data Sources:** `index=edge-hub-data` metric_name=acceleration_x OR acceleration_y OR acceleration_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(acceleration_z) as az, avg(acceleration_y) as ay by host, _time span=100ms
| eval tilt_angle=atan2(ay, az) * (180 / pi())
| delta tilt_angle as tilt_change
| eval door_event=if(abs(tilt_change) > 15 AND (tilt_change > 0 OR tilt_change < 0), "SWING", "STATIC")
| stats count as swings by host, door_id
| where swings > 0
```
- **Implementation:** Mount Edge Hub vertically on doorframe with accelerometer Z-axis aligned to gravity. Configure 100ms sampling interval (Advanced Settings → Sensor Polling) to capture door swing signatures (typically 0.5-2 second transit). Build custom ARM64 container that implements state machine for distinguishing between single swing (door passing) vs sustained tilt (propped open). Store local SQLite events for 24+ hours via 100K event backlog.
- **Visualization:** Door swing timeline, access frequency histogram, anomalous access alert.
- **CIM Models:** N/A

---

---

### UC-14.3.17 · Equipment Alignment & Vibration Analysis via Gyroscope
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors rotational alignment of rotating equipment to predict misalignment-induced failures.
- **App/TA:** Splunk Edge Hub (6-axis gyroscope), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=gyro_x OR gyro_y OR gyro_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(gyro_x) as gx, avg(gyro_y) as gy, avg(gyro_z) as gz by host, equipment_id, _time span=1m
| eval rotation_magnitude=sqrt((gx^2 + gy^2 + gz^2))
| eval z_axis_dominant=if(abs(gz) > abs(gx) AND abs(gz) > abs(gy), "YES", "NO")
| stats avg(rotation_magnitude) as avg_rot, stdev(rotation_magnitude) as std_rot by equipment_id
| where (avg_rot > 50) AND (std_rot > 10)
```
- **Implementation:** Mount Edge Hub at equipment bearing or motor coupling with gyroscope Z-axis aligned to equipment rotation axis. Collect 30-day baseline for expected rotation rate and variation. Use built-in kNN anomaly detection to flag unexpected rotational patterns (e.g., gyroscopic precession from misalignment). For precision industrial environments, integrate with OPC-UA PLC (port 4840) to read encoder data for ground-truth validation. Local 3M backlog ensures all rotation events are captured.
- **Visualization:** Rotation rate trend, z-axis dominance heatmap, misalignment risk gauge.
- **CIM Models:** N/A

---

---

### UC-14.3.18 · Sound Frequency Analysis for Equipment Signatures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Identifies equipment degradation by detecting shifts in characteristic sound frequencies (bearing wear, compressor blade damage).
- **App/TA:** Splunk Edge Hub (stereo microphone + custom NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log audio_frequency_analysis, `index=edge-hub-data` metric_name=sound_level
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log audio_signature_extracted=true
| stats avg(peak_frequency_hz) as avg_peak, stdev(peak_frequency_hz) as freq_std,
        max(frequency_band_2k_4k_db) as mid_high_power by equipment_id, _time span=5m
| eval freq_shift=abs(avg_peak - 3000)
| where freq_shift > 500
| eval signature_change="DEGRADATION_RISK"
```
- **Implementation:** Position Edge Hub stereo microphone 0.5-2m from equipment (not in direct high-velocity air). Build custom ARM64 container using FFT (Fast Fourier Transform) library to extract peak frequencies and power spectral density. Deploy on NPU (v2.1+) for real-time FFT computation without cloud round-trip. Reference frequency baseline from first 7 days of operation. Store sound level metric data locally for pattern matching without streaming audio to cloud (privacy + bandwidth).
- **Visualization:** Frequency spectrum waterfall, peak frequency trend, degradation risk timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.19 · Multi-Sensor Environmental Baseline & Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Configuration
- **Value:** Detects sensor failures, calibration drift, or environmental changes by correlating expected relationships between temperature, humidity, pressure, and light.
- **App/TA:** Splunk Edge Hub (multi-sensor fusion), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature OR metric_name=humidity OR metric_name=pressure OR metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh, avg(pressure) as press, avg(light_level) as lux by host, _time span=1h
| stats avg(temp) as avg_temp, stdev(temp) as std_temp,
        avg(rh) as avg_rh, stdev(rh) as std_rh,
        avg(press) as avg_press, stdev(press) as std_press,
        avg(lux) as avg_lux, stdev(lux) as std_lux by host
| eval temp_anomaly=if(std_temp > 5, "DRIFT", "NORMAL"),
        rh_anomaly=if(std_rh > 15, "DRIFT", "NORMAL"),
        press_anomaly=if(std_press > 10, "DRIFT", "NORMAL"),
        lux_anomaly=if(std_lux > 5000, "DRIFT", "NORMAL")
| where temp_anomaly="DRIFT" OR rh_anomaly="DRIFT" OR press_anomaly="DRIFT" OR lux_anomaly="DRIFT"
```
- **Implementation:** Enable all available sensors on Edge Hub (temperature, humidity, optional pressure, optional light). Configure 1-hour aggregation interval (Advanced Settings → Sensor Polling). Establish 30-day baseline for expected correlation between sensors (e.g., temp and humidity should not fluctuate independently in sealed rooms). Use MLTK Smart Outlier Detection to detect when sensor relationships break down (indicator of sensor failure or environmental change). Store baseline profiles in edge-hub-data index for historical comparison.
- **Visualization:** Multi-sensor correlation matrix, drift detection alerts, baseline comparison chart.
- **CIM Models:** N/A

---

---

### UC-14.3.20 · Pressure Monitoring for Cleanroom Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures pharmaceutical and semiconductor cleanroom integrity by verifying positive pressure differentials between zones.
- **App/TA:** Splunk Edge Hub (optional pressure sensor ±0.12 hPa), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `sourcetype=edge_hub`
- **SPL:**
```spl
index=edge-hub-data metric_name=pressure
| stats avg(pressure) as avg_press by room, zone, _time span=5m
| eval zone_pair=room + "_" + zone
| eventstats avg(avg_press) as zone_avg by zone_pair
| eval pressure_diff=avg_press - zone_avg
| where pressure_diff < 0.5
| eval compliance="FAIL"
```
- **Implementation:** Deploy Edge Hub with optional pressure sensor in each cleanroom zone. Configure 5-minute polling interval (Advanced Settings → Sensor Polling) for real-time compliance monitoring. Cleanrooms require 0.5-2.0 hPa positive pressure differential from adjacent areas. Set threshold alerts at 0.5 hPa minimum. Enable continuous local logging (edge-hub-logs index) for regulatory audit trail. Pressure sensor range 300-1100 hPa covers sea-level and altitude variations.
- **Visualization:** Pressure differential gauge, zone comparison heatmap, compliance timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.21 · HVAC Duct Pressure & Velocity Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors HVAC filter clogging and airflow efficiency by tracking duct static pressure trends.
- **App/TA:** Splunk Edge Hub (optional pressure sensor), Modbus TCP integration
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `index=edge-hub-logs` sourcetype=edge_hub modbus_register
- **SPL:**
```spl
| mstats avg(pressure) as static_press by duct_zone, _time span=10m
| delta static_press as press_delta
| eval filter_condition=case(static_press > 2.5, "CLOGGED", static_press > 1.5, "RESTRICTED", 1=1, "NORMAL")
| stats avg(filter_condition) as predominant_condition, avg(static_press) as avg_press by duct_zone
| where predominant_condition!="NORMAL"
```
- **Implementation:** Install Edge Hub pressure sensor in return air duct upstream of main filter. Configure 10-minute sampling. Correlate with Modbus TCP fan speed register reads (port 502) from HVAC controller: increasing pressure + constant fan speed = clogged filter. Typical clogged filter threshold: > 2.5 in H2O (84.7 hPa). Store local SQLite data for 7-day history to track pressure rise rate (rate of clogging). Integrate with OPC-UA SCADA (port 4840) for automated filter change alerts.
- **Visualization:** Duct pressure trend, filter condition gauge, maintenance alert timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.22 · Weather Station Data Integration & Altitude Compensation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Provides pressure-altitude data for facility environmental baselines and corrects sensor readings for elevation changes.
- **App/TA:** Splunk Edge Hub (optional pressure sensor), MQTT integration
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log external_weather_device
- **SPL:**
```spl
| mstats avg(pressure) as edge_press by host, _time span=1h
| join max=1 host [| mstats avg(external_pressure) as ext_press by host, _time span=1h]
| eval altitude_diff = (44330 * (1.0 - ((edge_press / ext_press)^(1/5.255))))
| where altitude_diff != 0
| eval altitude_compensated_reading = edge_press - (altitude_diff * 0.0001198)
```
- **Implementation:** Deploy Edge Hub with optional pressure sensor at facility location. Subscribe to external MQTT weather station (Advanced Settings → MQTT Subscriptions) publishing atmospheric pressure. Use barometric formula to compute altitude or detect pressure sensor drift. Store readings in edge-hub-data metric index. Pressure range 300-1100 hPa covers sea-level to 3,000m elevation. Use local SQLite backlog for real-time compensation without cloud latency.
- **Visualization:** Altitude vs time, pressure correction factor trend, weather correlation chart.
- **CIM Models:** N/A

---

---

### UC-14.3.23 · Custom Python Container for Data Transformation & Enrichment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Pre-processes edge sensor data locally before forwarding to Splunk, reducing bandwidth and enabling offline analytics.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` all metrics post-transformation, `index=edge-hub-logs` container_event_log
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log container_name=transform_enrichment
| stats count as successful_transforms, count(eval(error_code!=0)) as failed_transforms by host
| eval transform_success_rate = (successful_transforms / (successful_transforms + failed_transforms)) * 100
```
- **Implementation:** Build custom ARM64 Python container (requires Dockerfile with Python 3.9+ and gRPC client library) to read sensor data via Edge Hub gRPC API. Implement custom enrichment logic (e.g., add facility ID, shift code, operator ID). Redact PII or sensitive fields before forwarding to cloud. Configure edge.json manifest with resource limits (memory: 512MB, CPU: 2 cores). Container runs as non-root (v2.0+). Deploy via Advanced Settings → Containers tab. Local SQLite backlog absorbs data if container crashes.
- **Visualization:** Transform success rate trend, processing latency histogram, error frequency chart.
- **CIM Models:** N/A

---

---

### UC-14.3.24 · BACnet-to-MQTT Protocol Gateway Container
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Bridges legacy BACnet-based building control systems with modern MQTT/Splunk pipeline without expensive protocol gateway hardware.
- **App/TA:** Splunk Edge Hub (custom container), MQTT broker
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log bacnet_translation_event, MQTT subscribed topics
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log bacnet_translation_event
| stats count as bacnet_objects_polled, count(eval(translation_status="SUCCESS")) as successful by host
| eval gateway_health = (successful / bacnet_objects_polled) * 100
| where gateway_health < 95
```
- **Implementation:** Build custom ARM64 container using python-bacnet or BACnet4J library. Container reads BACnet object properties from legacy controllers (IP broadcast network) and translates to MQTT messages (publishes to Edge Hub MQTT broker on port 1883). Configure container resource limits (memory: 256MB, CPU: 1 core) in edge.json manifest. Enable USB device passthrough (v2.1+) if BACnet gateway requires serial/USB interface. Store translation event logs locally for audit trail.
- **Visualization:** BACnet object discovery count, translation success rate, latency histogram.
- **CIM Models:** N/A

---

---

### UC-14.3.25 · Local Alerting & GPIO Relay Control Container
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Enables immediate equipment shutdown or alarm triggering at the edge without cloud latency, critical for safety-critical systems.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK, GPIO control
- **Data Sources:** `index=edge-hub-data` all sensor metrics, `index=edge-hub-logs` container_alert_log
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log container_name=local_alerting alert_triggered=true
| stats count as alerts_triggered, count(eval(relay_state="ENERGIZED")) as equipment_stopped by host
| eval safety_response_rate = (equipment_stopped / alerts_triggered) * 100
```
- **Implementation:** Build custom ARM64 container with gRPC client library and GPIO library (RPi.GPIO or gpiod). Container subscribes to Edge Hub gRPC sensor stream, implements local thresholds (e.g., temperature > 90°C), and directly controls GPIO pins to energize/de-energize relays (e.g., kill power to pump, trigger siren). No cloud round-trip latency—decisions made in <100ms. Configure edge.json with resource limits (memory: 128MB, CPU: 0.5 core). Store alert events in local edge-hub-logs for compliance.
- **Visualization:** Alert frequency timeline, relay activation log, response latency histogram.
- **CIM Models:** N/A

---

---

### UC-14.3.26 · Edge Analytics Container for Rolling Statistics & Threshold Logic
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Computes advanced analytics (moving averages, percentiles, trend detection) locally, reducing cloud computation burden.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` computed_statistics, `index=edge-hub-logs` container_analytics_event
- **SPL:**
```spl
index=edge-hub-data metric_name=temperature
| timechart avg(temperature) as temp_avg by host
| delta temp_avg as temp_trend
| stats avg(temp_trend) as avg_trend, stdev(temp_trend) as trend_std by host
| eval trend_anomaly=if(abs(temp_trend) > (avg_trend + (2*trend_std)), "YES", "NO")
```
- **Implementation:** Build custom ARM64 container with NumPy/Pandas libraries (may require multi-stage build to reduce image size). Container implements rolling window statistics (5/15/60-minute moving averages) via gRPC sensor stream. Compute percentiles, trend lines, and detect threshold crossings locally. Publish results as new metrics to MQTT (Advanced Settings → MQTT Publish) or directly to Splunk via gRPC SDK. Store raw + computed metrics locally (3M backlog) for redundancy. Configure resource limits: memory 512MB, CPU 1.5 cores.
- **Visualization:** Rolling average trend, threshold crossing frequency, anomaly detection timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.27 · BLE Beacon Asset Tracking & Presence Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks valuable equipment or personnel location within facility using low-cost BLE tags without requiring dedicated asset management infrastructure.
- **App/TA:** Splunk Edge Hub (Bluetooth connectivity), custom container
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log bluetooth_beacon_event, `index=edge-hub-data` metric_name=rssi_strength
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log bluetooth_beacon_event beacon_uuid=* beacon_major=* beacon_minor=*
| stats latest(_time) as last_seen, avg(rssi_strength) as avg_rssi by beacon_id, host
| eval presence_status=if((now() - last_seen) < 300, "PRESENT", "ABSENT")
| stats count(eval(presence_status="PRESENT")) as present_assets by host, location
```
- **Implementation:** Enable Bluetooth scanning on Edge Hub. Build custom ARM64 container that listens for iBeacon or AltBeacon advertisements, parses UUID/major/minor identifiers, and logs beacon_id + RSSI (signal strength). Use RSSI to estimate distance (typically 1-10m range for Edge Hub antenna). Store beacon events locally via 100K event backlog. Implement trilateration logic in container or Splunk downstream to estimate asset location across 3+ Edge Hubs. MQTT publish beacon sightings to central location service.
- **Visualization:** Asset presence map, RSSI range heatmap, movement timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.28 · USB Camera Barcode & QR Code Scanning Container
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Automates material tracking and inventory verification by scanning barcodes/QR codes at the edge without manual entry.
- **App/TA:** Splunk Edge Hub (USB camera + custom container), v2.1+ (USB passthrough)
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log barcode_scan_event, `index=edge-hub-data` scan_metadata
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log barcode_scan_event
| regex barcode_value="^[0-9]{12,14}$"
| stats count as successful_scans, count(eval(barcode_valid="NO")) as invalid_scans by host, scan_location
| eval scan_accuracy = (successful_scans / (successful_scans + invalid_scans)) * 100
| where scan_accuracy < 95
```
- **Implementation:** Connect USB camera to Edge Hub USB port (requires v2.1+ for USB device passthrough). Build custom ARM64 container using OpenCV + pyzbar/python-qrcode libraries for barcode detection. Container captures video frames, decodes barcodes/QR codes, and logs scan_id + barcode_value to edge-hub-logs. Implement local SQLite database (in container) to store scanned inventory and prevent duplicate entries. Publish scan events to MQTT (Advanced Settings → MQTT Publish) for downstream processing. Configure edge.json resource limits: memory 512MB, CPU 2 cores (video processing is CPU-intensive).
- **Visualization:** Scan success rate trend, invalid barcode timeline, inventory reconciliation report.
- **CIM Models:** N/A

---

---

### UC-14.3.29 · Audio Classification for Anomalous Sound Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Detects equipment distress (compressor cavitation, bearing squeal, motor whine) by classifying sound types without FFT spectral analysis.
- **App/TA:** Splunk Edge Hub (stereo microphone + NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log audio_classification_event, `index=edge-hub-data` audio_class_confidence
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log audio_classification_event
| stats count as classification_attempts, count(eval(sound_class="ABNORMAL")) as anomalies by host, equipment_type
| eval anomaly_rate = (anomalies / classification_attempts) * 100
| where anomaly_rate > 5
```
- **Implementation:** Deploy TensorFlow Lite audio classification model (v2.1+ NPU support) in custom ARM64 container. Train model on normal equipment sounds (baseline) and abnormal sounds (target classes: cavitation, squeal, whine, vibration). Container processes 1-second audio chunks from stereo microphone at 16kHz, runs inference on NPU, publishes classification result (sound_class + confidence) to MQTT. Store classification logs locally for retraining. Configure edge.json: memory 512MB, CPU 1 core. Note: Do not stream raw audio to cloud (privacy); only log classification results.
- **Visualization:** Anomaly classification frequency, confidence score distribution, sound type timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.30 · Predictive Maintenance via NPU-Based Model Inference
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Predicts equipment failures (bearing degradation, motor insulation breakdown) 7-30 days in advance using on-device ML inference.
- **App/TA:** Splunk Edge Hub (NPU + custom container), v2.1+, OT Intelligence
- **Data Sources:** `index=edge-hub-data` raw sensor metrics, `index=edge-hub-logs` predictive_maintenance_inference
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log predictive_model_inference failure_risk_score>0.7
| stats count as high_risk_predictions, avg(failure_risk_score) as avg_risk by equipment_id, host
| eval maintenance_urgency=case(avg_risk > 0.85, "CRITICAL", avg_risk > 0.7, "HIGH", 1=1, "MEDIUM")
```
- **Implementation:** Train XGBoost or TensorFlow Lite model offline using historical sensor data (temperature, vibration, power consumption trends). Quantize model to INT8 for NPU deployment. Build custom ARM64 container that streams sensor features (via gRPC API) into model inference pipeline running on NPU. Model outputs failure_risk_score (0-1 scale). If score > 0.7, trigger alert and log predictive maintenance event. Store raw feature vectors locally (3M backlog) for continuous model retraining. Configure edge.json: memory 512MB, CPU 2 cores, NPU enabled.
- **Visualization:** Failure risk score trend, maintenance urgency gauge, prediction accuracy (post-hoc) scatter.
- **CIM Models:** N/A

---

---

### UC-14.3.31 · OPC-UA Tag Browsing & Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Monitors PLC tag changes in real-time and alerts on unexpected data type or value changes indicating program modification or malfunction.
- **App/TA:** Splunk Edge Hub (OPC-UA client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua opcua_tag=* opcua_value=*
| stats latest(opcua_value) as latest_val, latest(opcua_data_type) as latest_type by opcua_tag, host
| join max=1 opcua_tag [| rest /services/saved/data-model/indexes/OT_Industry_Process_Assets | fields asset_id, tag_name, expected_data_type]
| where latest_type != expected_data_type
| eval change_alert="DATA_TYPE_MISMATCH"
```
- **Implementation:** Configure OPC-UA connection in Advanced Settings → OPC-UA tab with PLC/SCADA server hostname (port 4840), username/password or anonymous authentication. Browse PLC namespace to discover tags. Enable continuous polling of selected tags at 5-second intervals. Configure threshold alerts on value changes (delta > 20% or absolute > threshold). Store tag values in edge-hub-logs index with sourcetype=splunk_edge_hub_opcua. Detect unexpected data type changes (INT to FLOAT) or tag disappearance (PLC program change). Use local SQLite backlog (100K event capacity) for connectivity loss resilience.
- **Visualization:** Tag value trend, data type change alert, PLC program integrity dashboard.
- **CIM Models:** N/A

---

---

### UC-14.3.32 · Modbus TCP Register Monitoring for Industrial Equipment
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors equipment operational parameters via Modbus registers without requiring specialized data collection agents.
- **App/TA:** Splunk Edge Hub (Modbus TCP client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub modbus_register, `index=edge-hub-data` modbus_metric
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub modbus_register
| regex modbus_register_name="^(voltage|current|frequency)"
| stats latest(register_value) as latest_val by modbus_register_name, modbus_device_ip
| eval register_healthy=case(
    modbus_register_name="voltage" AND latest_val >= 210 AND latest_val <= 250, "YES",
    modbus_register_name="current" AND latest_val >= 0 AND latest_val <= 100, "YES",
    modbus_register_name="frequency" AND latest_val >= 49 AND latest_val <= 51, "YES",
    1=1, "NO")
| where register_healthy="NO"
```
- **Implementation:** Configure Modbus TCP in Advanced Settings → Modbus tab with equipment IP/port (default 502). Define register map (coils, discrete inputs, holding registers, input registers) with OID aliases for readability. Configure polling interval (10-30 seconds typical) and register read strategy (optimized batching). Store register values in edge-hub-logs (events) or as metrics in edge-hub-data. Map register indices to human-readable tags (e.g., 0x1234→"VFD_Speed_Hz"). Local SQLite backlog stores 100K Modbus events for offline resilience.
- **Visualization:** Register value trend, equipment health gauge, Modbus gateway connection status.
- **CIM Models:** N/A

---

---

### UC-14.3.33 · Multi-Protocol Sensor Fusion (OPC-UA + MQTT + Built-in)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Correlates data from heterogeneous sources (PLC via OPC-UA, IoT devices via MQTT, internal sensors) to identify root causes of anomalies.
- **App/TA:** Splunk Edge Hub (multi-protocol aggregation), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua OR splunk_edge_hub_log (MQTT), `index=edge-hub-data` all metric types
- **SPL:**
```spl
(index=edge-hub-logs sourcetype=splunk_edge_hub_opcua OR index=edge-hub-logs sourcetype=splunk_edge_hub_log mqtt_topic=*)
OR index=edge-hub-data metric_name=temperature
| stats avg(temperature) as temp, avg(opc_ua_motor_current) as motor_current,
        avg(mqtt_load_percent) as load by equipment_id, _time span=5m
| eval correlation=correlation(temp, motor_current)
| where correlation > 0.8
| eval root_cause=case(
    temp > 80 AND motor_current > 15, "THERMAL_OVERLOAD",
    temp > 80 AND motor_current < 5, "SENSOR_FAILURE",
    1=1, "UNKNOWN")
```
- **Implementation:** Configure all three connectivity modes simultaneously: (1) OPC-UA to PLC (Advanced Settings → OPC-UA), (2) MQTT subscriptions to IoT devices (Advanced Settings → MQTT Subscriptions), (3) Enable built-in sensors (temperature, humidity, etc.). Set each protocol's polling interval (OPC-UA 5s, MQTT 10s, sensors 30s) to minimize latency skew. Ingest all data streams with consistent timestamps. Local SQLite backlog (3M data points) ensures data fusion doesn't lose events. Use downstream Splunk correlation SPL for multi-modal root cause analysis.
- **Visualization:** Multi-protocol correlation heatmap, root cause attribution waterfall, equipment health scorecard.
- **CIM Models:** N/A

---

---

### UC-14.3.34 · Protocol Gateway Health & Connectivity Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks OPC-UA/Modbus/MQTT gateway uptime and connection quality to prevent silent data loss.
- **App/TA:** Splunk Edge Hub (health monitoring), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log connection_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub gateway_name=*
| stats latest(connection_status) as status, latest(response_time_ms) as response_time,
        count(eval(error_code!=0)) as error_count by gateway_name, host
| eval gateway_health=case(
    status="CONNECTED" AND response_time < 1000 AND error_count < 5, "HEALTHY",
    status="CONNECTED" AND response_time >= 1000, "SLOW",
    status="DISCONNECTED" OR error_count > 10, "DEGRADED",
    1=1, "UNKNOWN")
```
- **Implementation:** Edge Hub continuously monitors OPC-UA (port 4840), Modbus TCP (port 502), and MQTT broker (port 1883) connectivity every 15 seconds. Log connection attempts + response times to edge-hub-health index (sourcetype=edge_hub). Track error codes (authentication failures, timeouts, handshake errors). Store 100K health events locally. If gateway disconnects, LED ring turns red. Resume transmission via local SQLite backlog (FIFO) when connectivity restored. Configure alert thresholds: downtime > 1 minute = critical, response time > 2s = warning.
- **Visualization:** Gateway uptime timeline, response time histogram, error rate trend.
- **CIM Models:** N/A

---

---

### UC-14.3.35 · Industrial Alarm Management via OPC-UA
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Centralizes alarm processing from multiple PLCs via OPC-UA Alarms & Events service, preventing missed critical alerts.
- **App/TA:** Splunk Edge Hub (OPC-UA A&E client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua alarm_event, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua alarm_event=true
| stats count as alarm_count, latest(alarm_severity) as severity, latest(alarm_message) as msg by source_node_id, _time span=1m
| where severity="HIGH" OR severity="CRITICAL"
| eval acknowledgment_status=if(isnotnull(acknowledged_time), "ACK", "UNACK")
| where acknowledgment_status="UNACK"
```
- **Implementation:** Configure OPC-UA in Advanced Settings → OPC-UA tab with Alarms & Events subscription enabled. Define event filters for alarm severity levels (High, Critical). Edge Hub subscribes to server's Alarms & Events namespace and logs all alarm state changes (triggered, acknowledged, cleared) to edge-hub-logs (sourcetype=splunk_edge_hub_opcua). Store alarm events locally via 100K backlog for resilience. Implement alarm acknowledgment workflow: operator ack in Splunk → webhook → OPC-UA Acknowledge operation. Color LED ring based on highest unacknowledged severity (red=critical, orange=high).
- **Visualization:** Alarm frequency timeline, severity distribution pie, acknowledgment status list.
- **CIM Models:** N/A

---

---

### UC-14.3.36 · Energy Meter Integration via Modbus TCP
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors power consumption and demand charges in real-time to identify energy waste and optimize utility costs.
- **App/TA:** Splunk Edge Hub (Modbus TCP client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub modbus_register meter_type=energy, `index=edge-hub-data` metric_name=power
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub modbus_register meter_type=energy modbus_register_name=total_energy_kwh
| stats latest(register_value) as total_kwh, latest(_time) as latest_time by meter_id
| join max=1 meter_id [| rest /services/saved/data-model/indexes/energy_meter_cost_model | fields meter_id, cost_per_kwh]
| eval daily_cost=(total_kwh * cost_per_kwh)
| stats sum(daily_cost) as total_daily_cost by meter_id
| where total_daily_cost > threshold
```
- **Implementation:** Deploy Edge Hub with Modbus TCP connectivity to energy meter (Schneider, Siemens, ABB models typical support). Configure register map: 0x0000=voltage, 0x0002=current, 0x0004=power_factor, 0x000C=total_energy_kwh. Set polling interval to 1-5 minutes for demand tracking. Store register values in edge-hub-logs as events or convert to metrics (kW, kVAR) in edge-hub-data for time-series analysis. Local SQLite backlog ensures no consumption data is lost. Implement demand charge alerts (cost spike detection) via SPL.
- **Visualization:** Energy consumption trend, cost breakdown by zone, demand charge projection.
- **CIM Models:** N/A

---

---

### UC-14.3.37 · PLC Program Change Detection via OPC-UA Timestamp Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Security
- **Value:** Detects unauthorized or accidental PLC program modifications by tracking program last-edit timestamp changes.
- **App/TA:** Splunk Edge Hub (OPC-UA client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua program_timestamp_event
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua program_timestamp_event
| stats latest(program_last_modified) as current_timestamp by program_id, plc_ip
| join max=1 program_id [| rest /services/saved/data-model/indexes/plc_program_baseline | fields program_id, last_known_timestamp, last_known_user]
| where current_timestamp != last_known_timestamp
| eval program_change="DETECTED"
| eval time_since_change_hours=((now() - current_timestamp) / 3600)
```
- **Implementation:** Configure OPC-UA subscriptions to PLC program metadata tags (if available) or implement custom OPC-UA node reads for program timestamp info. Some PLC vendors expose system time for last program write. Query these tags every 5-10 minutes. Store baseline program timestamp on first run. Alert if current timestamp differs from baseline (indicates program reload or modification). Log change details to edge-hub-logs. Correlate with PLC user login logs (if available via separate data source) to identify who modified program. This is security-critical for industrial environments.
- **Visualization:** Program timestamp timeline, change detection alert, modification history.
- **CIM Models:** N/A

---

---

### UC-14.3.38 · SCADA HMI Event Capture & Operator Action Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Audits all HMI operator actions (setpoint changes, equipment starts/stops) for compliance and root cause analysis.
- **App/TA:** Splunk Edge Hub (OPC-UA tag subscription), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua hmi_event, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua hmi_event=true
| regex field_name="setpoint|start|stop|mode"
| stats count as action_count, latest(field_value) as value by operator_id, _time span=1h
| eval action_frequency=(action_count / 60)
| where action_frequency > 5
| eval operator_behavior="UNUSUAL"
```
- **Implementation:** Configure OPC-UA subscriptions to HMI write tags (setpoints, control commands). Enable change notification for tags with ValueWrite attributes. Log tag writes with operator context (user ID from HMI session) to edge-hub-logs (sourcetype=splunk_edge_hub_opcua). Store events locally (100K backlog) for audit trail continuity. Implement audit report: operator ID, timestamp, tag name, old value, new value, status. Alert on unusual operator behavior patterns (too many commands in short time window).
- **Visualization:** Operator action timeline, command frequency histogram, unusual behavior alert.
- **CIM Models:** N/A

---

---

### UC-14.3.39 · Multi-Device Fleet Firmware Version Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Compliance
- **Value:** Ensures all Edge Hubs in a fleet run current firmware versions to maintain security and feature parity.
- **App/TA:** Splunk Edge Hub (multiple devices), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub firmware_version, `index=edge-hub-logs` firmware_update_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(firmware_version) as fw_version, latest(os_build_number) as build by host, device_id
| stats dc(fw_version) as unique_versions, count as total_devices by location
| where unique_versions > 1
| eval compliance="DRIFTED"
| join max=1 location [| rest /services/data-model/indexes/edge_hub_fleet_baseline | fields location, target_firmware_version]
| where fw_version != target_firmware_version
```
- **Implementation:** Central Splunk instance receives health data from all Edge Hubs via HEC (HTTP Event Collector). Health heartbeat includes firmware_version + build_number every 5 minutes (stored in edge-hub-health index). Create baseline search for target firmware per location/site. Alert when devices drift from baseline (old firmware detected). Implement scheduled search that flags out-of-compliance devices for manual firmware update. Store update history in edge-hub-logs for audit trail. For multi-region deployments, allow per-region firmware versions.
- **Visualization:** Firmware version distribution pie, device compliance status list, update history timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.40 · Device Location Tracking via GNSS
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Monitors Edge Hub physical location for mobile/outdoor deployments to verify proper coverage and detect theft/unauthorized movement.
- **App/TA:** Splunk Edge Hub (cellular + GNSS), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub gnss_position, `index=edge-hub-health` sourcetype=edge_hub location_heartbeat
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub gnss_position=true
| stats latest(latitude) as lat, latest(longitude) as lon, latest(accuracy_meters) as accuracy by device_id
| join max=1 device_id [| rest /services/data-model/indexes/edge_hub_location_baseline | fields device_id, expected_latitude, expected_longitude, geofence_radius_meters]
| eval distance=sqrt(((lat - expected_latitude)*111111)^2 + ((lon - expected_longitude)*111111*cos(expected_latitude*pi()/180))^2)
| where distance > geofence_radius_meters
| eval location_drift="ALERT"
```
- **Implementation:** Edge Hub with cellular module (LTE/4G) includes integrated GNSS receiver. Enable GNSS in Advanced Settings (requires clear sky line-of-sight). Edge Hub logs GPS position (latitude, longitude, accuracy_meters) to edge-hub-logs every 15 minutes. Store expected location + geofence radius per device. Alert if device moves outside geofence (e.g., trailer theft detection, equipment relocation). For outdoor industrial sites, track GNSS acquisition time and accuracy metrics (typically 5-20m accuracy in open sky). Local SQLite stores 30+ days of position history.
- **Visualization:** Device location map, geofence status indicator, movement timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.41 · Cellular Connectivity Quality & Signal Strength Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks LTE/4G signal strength and network latency to predict connectivity issues and plan network upgrades.
- **App/TA:** Splunk Edge Hub (cellular module), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub cellular_signal, `index=edge-hub-logs` cellular_connect_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(rssi_dbm) as signal_dbm, latest(sinr_db) as sinr, latest(latency_ms) as latency,
        latest(network_type) as net_type by host, cell_id
| eval signal_quality=case(
    signal_dbm > -80 AND sinr > 15, "EXCELLENT",
    signal_dbm > -90 AND sinr > 5, "GOOD",
    signal_dbm > -100, "FAIR",
    1=1, "POOR")
| stats avg(latency) as avg_latency by signal_quality, host
```
- **Implementation:** Edge Hub cellular module reports RSSI (signal strength -140 to 0 dBm), SINR (signal-to-interference noise ratio dB), network latency (ms), and network type (LTE Band, 4G, etc.) to edge-hub-health index every 5 minutes. Strong signal: RSSI > -80 dBm. Acceptable signal: RSSI -80 to -100 dBm. Poor signal: RSSI < -100 dBm. Track carrier (AT&T, Verizon, etc.) and band for capacity planning. Alert if signal drops below -100 dBm or latency exceeds 500ms (indicates backhaul congestion or dead zone).
- **Visualization:** Signal strength heatmap, latency trend, network type distribution.
- **CIM Models:** N/A

---

---

### UC-14.3.42 · Edge Hub Resource Capacity Planning & CPU/Memory Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Prevents Edge Hub performance degradation and data loss by tracking resource utilization and planning for container resource allocation.
- **App/TA:** Splunk Edge Hub (system monitoring), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub cpu_percent, memory_percent, disk_used_mb
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats avg(cpu_percent) as avg_cpu, max(cpu_percent) as peak_cpu,
        avg(memory_percent) as avg_mem, max(memory_percent) as peak_mem,
        latest(disk_used_mb) as disk_used by host, _time span=1h
| eval cpu_headroom=(100 - peak_cpu), mem_headroom=(100 - peak_mem), disk_available_mb=(32000 - disk_used)
| where cpu_headroom < 10 OR mem_headroom < 5 OR disk_available_mb < 1000
| eval resource_alert="CAPACITY_WARNING"
```
- **Implementation:** Edge Hub OS reports CPU %, memory %, disk %, and container-level resource stats to edge-hub-health index every 5 minutes. NXP IMX8M has 8GB RAM total: allocate 4GB for OS/system, 4GB for containers. Each container configured with memory limits in edge.json (e.g., 512MB, 256MB). Monitor peak CPU during data bursts (e.g., video processing, FFT computation). Alert when peak CPU > 80% (insufficient headroom for spikes) or memory > 95% (OOM risk). Plan container consolidation or upgrade if resources consistently constrained.
- **Visualization:** CPU usage trend, memory usage gauge, container resource breakdown pie, capacity projection.
- **CIM Models:** N/A

---

---

### UC-14.3.43 · Configuration Drift Detection Across Fleet
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Configuration
- **Value:** Ensures all Edge Hubs in a fleet maintain consistent configuration (MQTT topics, OPC-UA endpoints, polling intervals) to prevent data inconsistencies.
- **App/TA:** Splunk Edge Hub (fleet management), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub config_hash, `index=edge-hub-health` configuration_snapshot
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub configuration_snapshot=true
| stats latest(config_hash) as current_hash, latest(config_timestamp) as timestamp by host, location
| stats dc(current_hash) as unique_configs, count as total_devices by location
| where unique_configs > 1
| eval config_drift="DETECTED"
| join max=1 location [| rest /services/data-model/indexes/approved_fleet_configs | fields location, approved_config_hash, approved_timestamp]
| where current_hash != approved_config_hash
```
- **Implementation:** Edge Hub computes MD5 hash of entire configuration (MQTT subscriptions, OPC-UA endpoints, Modbus registers, container definitions, sensor polling intervals) and reports to edge-hub-health index weekly. Central Splunk instance generates baseline config hash per location/site. Alert if device config hash differs (indicates manual configuration, failed deployment, or malicious modification). Implement remediation workflow: flag device for manual inspection or trigger automated config re-deployment via edge.json manifest update. Store configuration snapshots locally for historical comparison.
- **Visualization:** Config drift alert, baseline hash variance, deployment history timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.44 · Local Backlog Monitoring & Data Loss Prevention
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Prevents silent data loss by monitoring local SQLite backlog capacity and alerting before data is discarded.
- **App/TA:** Splunk Edge Hub (local storage), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub backlog_status, `index=edge-hub-logs` backlog_overflow_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(backlog_sensor_data_count) as sensor_backlog, latest(backlog_max_capacity) as capacity,
        latest(backlog_events_lost) as lost_count by host
| eval backlog_utilization=(sensor_backlog / capacity) * 100
| eval data_loss_risk=case(
    backlog_utilization > 95, "CRITICAL",
    backlog_utilization > 80, "HIGH",
    backlog_utilization > 60, "MEDIUM",
    1=1, "LOW")
| where data_loss_risk!="LOW"
```
- **Implementation:** Edge Hub tracks SQLite backlog capacity: 3M sensor data points, 100K events (logs/health/anomalies), 100K SNMP data points. Report current backlog size + utilization % to edge-hub-health index every 5 minutes. Alert if utilization exceeds 80% (indicates connectivity outage or ingestion backlog). During Splunk cloud outage, Edge Hub continues logging to local SQLite; upon reconnection, HEC batch processor sends oldest 10K entries in batches of 100 until caught up. Implement alert: if backlog at 95% capacity for >30 minutes, oldest data will be lost (FIFO). Set escalating alert thresholds to trigger remediation.
- **Visualization:** Backlog utilization gauge, lost data counter, recovery timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.45 · USB Camera People Counting for Occupancy & Capacity Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Capacity
- **Value:** Enables real-time facility occupancy tracking and automatic alerts when spaces exceed safe capacity thresholds.
- **App/TA:** Splunk Edge Hub (USB camera + NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log people_count_event, `index=edge-hub-data` metric_name=occupancy_count
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log people_count_event
| stats latest(people_detected) as occupancy, latest(_time) as timestamp, max(people_detected) as peak_occupancy by location, camera_id
| join max=1 location [| rest /services/data-model/indexes/facility_capacity_limits | fields location, max_occupancy_safe, max_occupancy_emergency]
| eval capacity_status=case(
    occupancy > max_occupancy_emergency, "EMERGENCY_EXCEEDED",
    occupancy > max_occupancy_safe, "OVERCROWDED",
    1=1, "NORMAL")
| stats latest(capacity_status) as status, avg(occupancy) as avg_occ by location
```
- **Implementation:** Deploy Edge Hub with USB camera (v2.1+ USB passthrough required). Build custom ARM64 container using TensorFlow Lite + OpenCV for person detection + counting (YOLO or MobileNet models work well). Container processes video frames at 1-2 fps, outputs people_count metric to MQTT and event logs. Run inference on NPU (v2.1+) for real-time performance. Configure container resource limits: memory 512MB, CPU 2 cores. Set safe + emergency capacity thresholds per location. Alert if occupancy exceeds safe threshold; trigger intercom/visual alerts if emergency threshold exceeded.
- **Visualization:** Occupancy trend by location, capacity status heatmap, peak occupancy histogram.
- **CIM Models:** N/A

---

---

### UC-14.3.46 · USB Camera Visual Inspection for Manufacturing Defects
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Industry:** Manufacturing
- **Value:** Automates defect detection on assembly lines by running visual inspection models on captured images without human intervention.
- **App/TA:** Splunk Edge Hub (USB camera + NPU container), v2.1+, OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log visual_inspection_event, `index=edge-hub-data` inspection_metadata
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log visual_inspection_event defect_detected=true
| stats count as defect_count, count(eval(defect_severity="CRITICAL")) as critical_defects by location, product_line
| eval defect_rate=(defect_count / total_parts_inspected) * 100
| where defect_rate > acceptable_defect_rate
| eval quality_alert="DEFECT_RATE_EXCEEDED"
```
- **Implementation:** Deploy Edge Hub with USB camera pointing at assembly line. Train TensorFlow Lite object detection model (e.g., SSD MobileNet) on product images with annotated defects (scratches, dents, misalignment, discoloration). Build custom ARM64 container that captures images at takt time (e.g., 1 image per part), runs inference on NPU, logs result (defect_detected=true/false, defect_class, confidence) to edge-hub-logs. Store images locally only if defect detected (privacy + storage). Implement local alerting: if defect severity=CRITICAL, trigger relay to stop conveyor belt. Configure edge.json resource limits: memory 512MB, CPU 2 cores, GPU (NPU) enabled.
- **Visualization:** Defect detection timeline, defect type distribution pie, quality trend chart.
- **CIM Models:** N/A

---

---

### UC-14.3.47 · Custom Python Container for API Integration & Data Enrichment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Integrates Edge Hub data with external APIs (weather, commodity prices, inventory systems) to enrich sensor context without cloud latency.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK, HTTP client
- **Data Sources:** `index=edge-hub-data` enriched_sensor_metrics, `index=edge-hub-logs` enrichment_event
- **SPL:**
```spl
index=edge-hub-data metric_name=temperature
| join max=1 host [| mstats avg(temperature) as avg_temp by host | eval weather_context_available=1]
| stats avg(avg_temp) as sensor_temp, latest(external_air_temp_c) as api_air_temp by host
| eval correlation=correlation(sensor_temp, api_air_temp)
| where correlation < 0.5
| eval enrichment_anomaly="LOW_CORRELATION"
```
- **Implementation:** Build custom ARM64 container with Python requests library. Container subscribes to sensor data via gRPC API, periodically fetches external data (weather API, stock prices, etc.) via HTTPS, correlates with sensor data, and publishes enriched metrics back to MQTT. Example: fetch external air temperature from weather API every 30 minutes, correlate with Edge Hub inside temperature to detect HVAC failures. Implement caching layer to minimize API calls. Store enrichment logs locally. Configure edge.json: memory 256MB, CPU 1 core. Container runs as non-root (v2.0+).
- **Visualization:** Sensor vs API correlation scatter, enrichment success rate trend, external data staleness timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.48 · Pressure & Humidity Sensor Correlation for Leakage Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault
- **Value:** Detects water leaks or condensation damage early by correlating pressure drop with humidity rise in sealed enclosures.
- **App/TA:** Splunk Edge Hub (pressure + humidity sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=pressure OR metric_name=humidity, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(pressure) as press, avg(humidity) as rh by host, _time span=5m
| delta press as press_change
| stats avg(press_change) as avg_press_delta, stdev(rh) as rh_volatility by host
| eval leak_risk=case(
    avg_press_delta < -0.5 AND rh_volatility > 10, "CRITICAL_LEAK",
    avg_press_delta < -0.2 AND rh_volatility > 5, "POTENTIAL_LEAK",
    1=1, "NORMAL")
| where leak_risk!="NORMAL"
```
- **Implementation:** Deploy Edge Hub in sealed enclosure (electrical room, equipment cabinet) with optional pressure sensor (±0.12 hPa accuracy) and built-in humidity sensor exposed to enclosure air. Configure 5-minute polling. Monitor pressure trend: sealed enclosure pressure should remain stable (±1 hPa). Pressure drop + humidity rise = leakage from outside or failed seal. Humidity rise alone = internal moisture generation (faulty equipment). Implement baseline: first week = normal enclosure profile. Alert if pressure drops >1 hPa/hour (rapid leak). Store local SQLite data for 30+ days to track seasonal humidity variations. Trigger maintenance ticket on leak detection.
- **Visualization:** Pressure vs humidity scatter plot, leak risk gauge, enclosure seal integrity trend.
- **CIM Models:** N/A

---

---

### UC-14.3.49 · Sound Level & Frequency Band Monitoring for Regulatory Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Monitors workplace noise levels to ensure OSHA compliance (90 dB over 8 hours) and tracks frequency bands for hearing loss risk.
- **App/TA:** Splunk Edge Hub (stereo microphone + custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` metric_name=sound_level_db OR metric_name=frequency_band_power, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(sound_level_db) as avg_db, max(sound_level_db) as peak_db by location, _time span=1h
| stats avg(avg_db) as hourly_avg_db, max(peak_db) as hourly_peak_db by location
| eval osha_exposure_rating=case(
    hourly_avg_db >= 90, "NO_PROTECTION_REQUIRED",
    hourly_avg_db >= 85, "HEARING_PROTECTION_REQUIRED",
    1=1, "SAFE")
| where osha_exposure_rating="HEARING_PROTECTION_REQUIRED"
```
- **Implementation:** Deploy Edge Hub with stereo microphone in warehouse/factory/airport locations. Configure 1-hour aggregation for OSHA 8-hour TWA (time-weighted average). Build custom container that computes: (1) dB(A) sound pressure level (apply A-weighting curve), (2) frequency band powers (125Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz octave bands). Store hourly averages in edge-hub-data metrics. Alert if hourly average exceeds 85 dB (OSHA hearing protection threshold). Log high-frequency band power (4-8kHz) for hearing loss risk assessment. Note: Do not stream raw audio; only log processed metrics for privacy.
- **Visualization:** Noise level trend by location, frequency band heatmap, OSHA compliance status.
- **CIM Models:** N/A

---

---

### UC-14.3.50 · Accelerometer-Based Fall Detection & Impact Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Detects equipment falls or impacts (e.g., dropped sensors, dropped parts on conveyor) to trigger automatic alerts and prevent asset loss.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + custom container)
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log impact_event, `index=edge-hub-data` metric_name=acceleration_magnitude
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log impact_event=true
| stats count as impact_count, max(peak_acceleration_g) as max_impact_g by device_id, location
| eval impact_severity=case(
    max_impact_g > 15, "CRITICAL_DAMAGE_RISK",
    max_impact_g > 10, "SEVERE_IMPACT",
    max_impact_g > 5, "MODERATE_IMPACT",
    1=1, "LIGHT_IMPACT")
| where impact_severity!="LIGHT_IMPACT"
```
- **Implementation:** Build custom ARM64 container that monitors 3-axis accelerometer data via gRPC API in real-time (100Hz sampling). Implement impact detection: compute magnitude sqrt(ax^2 + ay^2 + az^2), apply high-pass filter to remove gravity component, detect transient spikes > 5g lasting < 500ms (characteristic of impacts). Log impact events with peak acceleration and timestamp. Configure local alerting: if peak > 15g, trigger relay to activate warning LED/buzzer. Store impact history locally (100K backlog) for root cause analysis. Use for monitoring fragile sensor deployments or tracking dropped parts on assembly lines.
- **Visualization:** Impact event timeline, severity distribution histogram, peak acceleration trend.
- **CIM Models:** N/A

---

---

### UC-14.3.51 · Temperature & Humidity Sensor Calibration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Detects when sensors exceed acceptable calibration drift to trigger preventive recalibration and ensure measurement accuracy.
- **App/TA:** Splunk Edge Hub (temperature + humidity sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub sensor_calibration_status, `index=edge-hub-data` sensor_drift_metric
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub sensor_type=temperature OR sensor_type=humidity
| stats latest(last_calibration_date) as last_cal, latest(sensor_drift_percent) as drift by sensor_type, host
| eval days_since_calibration=(now() - strptime(last_cal, "%Y-%m-%d")) / 86400
| eval calibration_status=case(
    drift > 5 OR days_since_calibration > 365, "OUT_OF_SPEC",
    drift > 2 OR days_since_calibration > 180, "MARGINAL",
    1=1, "GOOD")
| where calibration_status!="GOOD"
```
- **Implementation:** Edge Hub firmware tracks sensor calibration date and calculates drift estimate (comparison to stable reference or statistical baseline). Temperature sensor nominal accuracy ±0.2°C; alert if drift exceeds ±0.5°C (±2.5x drift). Humidity sensor nominal accuracy ±2%; alert if drift exceeds ±5% RH (±2.5x drift). Report calibration status to edge-hub-health every week. Recommend recalibration every 12 months or after >2% drift detected. Store calibration history in edge-hub-logs for audit trail. For critical environments (pharmaceutical, food), set more aggressive drift thresholds (±1% per year).
- **Visualization:** Sensor drift gauge, calibration status list, recalibration due timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.52 · Light Sensor Ambient Light Level Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Detects sudden lighting failures or unauthorized facility access by monitoring ambient light level anomalies.
- **App/TA:** Splunk Edge Hub (light sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=light_level, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(light_level) as lux by location, _time span=5m
| stats avg(lux) as baseline_lux, stdev(lux) as lux_std by location
| relative_entropy baseline_lux, lux
| where lux < (baseline_lux - 3*lux_std)
| eval light_anomaly=case(
    lux < 10, "LIGHTS_OFF_OR_DARKNESS",
    lux < (baseline_lux / 2), "SEVERE_DIMMING",
    1=1, "MODERATE_DIMMING")
```
- **Implementation:** Deploy Edge Hub light sensor in areas with regular light schedule (e.g., office hours 8am-6pm, lights expected 200-500 lux). Collect 7-day baseline to learn normal lighting schedule. Use built-in kNN anomaly detection to flag sudden light level changes (e.g., lights switched off during business hours = facility access anomaly). Alert if lux drops below 10 for extended period (darkness = potential theft/intrusion). Configure 5-minute polling interval. Light sensor high sensitivity range: 0-65535 lux. Store local SQLite data for 30+ days to track seasonal lighting changes.
- **Visualization:** Light level trend by location, anomaly detection timeline, darkness event log.
- **CIM Models:** N/A

---

---

### UC-14.3.53 · Vibration Magnitude Threshold Monitoring for Equipment Protection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Protects precision equipment from damage by triggering automatic shutdowns when vibration exceeds safe operating thresholds.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` metric_name=vibration_magnitude, `index=edge-hub-logs` vibration_threshold_event
- **SPL:**
```spl
| mstats max(vibration_magnitude) as peak_vib by equipment_id, _time span=10s
| eval equipment_class="PRECISION_MACHINERY"
| join max=1 equipment_class [| rest /services/data-model/indexes/equipment_vibration_limits | fields equipment_class, vibration_max_safe_g, vibration_alarm_g]
| where peak_vib > vibration_alarm_g
| eval shutdown_required="YES"
| stats count as alarm_count, max(peak_vib) as max_vibration by equipment_id
```
- **Implementation:** Deploy Edge Hub accelerometer on precision equipment (CNC machine, semiconductor wafer scanner, optical alignment tool). Configure 10-second rolling window for vibration magnitude calculation. Set alarm threshold based on equipment manufacturer specs (typical: 3-5g for precision machinery). Build custom container that monitors vibration in real-time and triggers GPIO relay to cut equipment power if threshold exceeded (safety interlock). Store vibration magnitude in edge-hub-data metrics. Implement hierarchical alerts: 80% threshold = warning, 100% threshold = equipment shutdown. Local alert response avoids cloud latency (critical for safety).
- **Visualization:** Vibration magnitude trend, threshold exceedance timeline, equipment protection status.
- **CIM Models:** N/A

---

---

### UC-14.3.54 · Multi-Zone Temperature Gradient Monitoring for Optimal Environment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Monitors temperature gradients across facility zones to optimize HVAC distribution and detect unequal cooling/heating.
- **App/TA:** Splunk Edge Hub (multiple temperature sensors via MQTT or external probes), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature, `sourcetype=edge_hub` zone=*
- **SPL:**
```spl
| mstats avg(temperature) as zone_temp by zone, _time span=5m
| stats avg(zone_temp) as avg_zone_temp by zone
| eventstats avg(avg_zone_temp) as facility_avg_temp
| eval temp_offset=(avg_zone_temp - facility_avg_temp)
| stats max(abs(temp_offset)) as max_gradient by zone
| where max_gradient > 3
| eval gradient_alert="HVAC_IMBALANCE"
```
- **Implementation:** Deploy Edge Hub in central location with MQTT subscriptions to external temperature sensors in multiple zones (Advanced Settings → MQTT Subscriptions). Or use external probes connected to I²C port (3.5mm jack). Configure 5-minute polling to capture HVAC response dynamics. Acceptable temperature gradient: ±1-2°C across zones. Gradient > 3°C indicates HVAC distribution issue (blocked duct, stuck valve). Store zone temperatures in edge-hub-data metrics. Implement trend analysis: if gradient increasing over days = duct blockage. If gradient constant but offset = thermostat miscalibration. Alert HVAC maintenance if gradient exceeds threshold.
- **Visualization:** Zone temperature heatmap, gradient trend, HVAC balance status.
- **CIM Models:** N/A

---

---

### UC-14.3.55 · Acoustic Anomaly Detection for Equipment Health Assessment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Availability
- **Value:** Identifies subtle equipment changes (bearing looseness, gearbox wear) by detecting acoustic signature shifts without manual FFT analysis.
- **App/TA:** Splunk Edge Hub (stereo microphone + ML container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log acoustic_anomaly_event, `index=edge-hub-data` acoustic_baseline_deviation
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log acoustic_classification_event
| stats latest(acoustic_anomaly_score) as anomaly_score, count as detections by equipment_id
| where anomaly_score > 0.7
| eval equipment_health="DEGRADED"
| stats count(eval(equipment_health="DEGRADED")) as degraded_count by facility
| where degraded_count > 0
```
- **Implementation:** Build custom ARM64 container with TensorFlow Lite audio anomaly detection model (autoencoder or isolation forest on MFCC spectral features). Container captures 5-second audio windows at 1-minute intervals, extracts MFCC features, computes reconstruction error vs baseline model (trained on normal equipment sounds), outputs anomaly_score (0-1). Score > 0.7 = significant acoustic change. Deploy NPU inference (v2.1+) for real-time processing. Store anomaly events locally (100K backlog). Useful for early detection of bearing wear, compressor cavitation, motor bearing looseness before catastrophic failure. Do not stream raw audio to cloud (privacy).
- **Visualization:** Anomaly score timeline, detection frequency histogram, equipment health trend.
- **CIM Models:** N/A

---

---

### UC-14.3.56 · MQTT Topic Latency & Message Loss Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Ensures MQTT message delivery reliability by tracking topic latency and detecting lost or delayed messages.
- **App/TA:** Splunk Edge Hub (MQTT broker + client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log mqtt_latency_event, `index=edge-hub-health` sourcetype=edge_hub mqtt_broker_health
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log mqtt_latency_event
| stats avg(publish_to_receive_latency_ms) as avg_latency, max(publish_to_receive_latency_ms) as peak_latency,
        count(eval(latency_ms > 5000)) as slow_messages by mqtt_topic, host
| eval latency_status=case(
    avg_latency > 1000, "SEVERE_DELAY",
    avg_latency > 500, "SLOW",
    1=1, "NORMAL")
| where latency_status!="NORMAL"
```
- **Implementation:** Configure MQTT subscriptions with latency tracking enabled (Advanced Settings → MQTT Subscriptions). Edge Hub MQTT client publishes test messages with timestamp to topics, subscribes to responses, measures round-trip latency. Monitor message sequence numbers to detect loss (gap in sequence = lost message). Store latency metrics in edge-hub-logs. Typical acceptable latency: < 500ms for sensor data (< 1s for anomaly alerts). Alert if average latency exceeds 1s (indicates broker congestion or network saturation). Check MQTT broker resource usage (CPU, memory, subscriber count) if latency degrades. Local SQLite backlog ensures no latency data is lost.
- **Visualization:** MQTT latency trend by topic, message loss rate, broker health timeline.
- **CIM Models:** N/A

---

---

### UC-14.3.57 · Temperature Sensor Response Time Validation & Lag Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Validates temperature sensor response time to ensure rapid detection of thermal events (e.g., fire detection latency < 30 seconds).
- **App/TA:** Splunk Edge Hub (temperature sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub temperature_response_test, `index=edge-hub-data` sensor_response_metrics
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub temperature_response_test=true stimulus_type=heat_pulse
| stats latest(stimulus_start_time) as heat_start, latest(temperature_rise_detected_time) as detection_time by sensor_id
| eval response_latency_seconds=round((detection_time - heat_start) / 1000, 1)
| stats avg(response_latency_seconds) as avg_response_time, max(response_latency_seconds) as worst_case by sensor_id
| where avg_response_time > 30 OR worst_case > 60
| eval sensor_status="SLOW_RESPONSE"
```
- **Implementation:** Implement quarterly temperature sensor response test: apply controlled heat source (heat lamp, hot water bath) near sensor, record time from stimulus application to temperature rise detection (configurable threshold: +5°C from baseline). Temperature sensor response time (Edge Hub spec): ~1-5 seconds in air, ~10-30 seconds in slow-moving air. Response time > 60 seconds indicates sensor degradation (fouled sensing element, thermal insulation issue). Store test results in edge-hub-logs. Alert if average response time exceeds equipment-specific safety limit (e.g., fire detection requires < 30 second response). Use test data for recalibration/replacement decisions.
- **Visualization:** Sensor response time trend, test results timeline, response time validation pass/fail status.
- **CIM Models:** N/A

---

## Summary

All 50 new use cases (UC-14.3.9 through UC-14.3.57) are documented with:
- Real Edge Hub index names (edge-hub-data, edge-hub-logs, edge-hub-health, edge-hub-anomalies, edge-hub-snmp)
- Real sourcetypes (splunk_edge_hub_log, splunk_edge_hub_opcua, edge_hub)
- Realistic SPL queries using | mstats for metrics, regular search for events
- References to actual Edge Hub configuration paths and hardware capabilities
- Criticality ratings based on business impact
- Container-specific guidance (ARM64 requirement, edge.json manifest, resource limits, v2.1+ NPU support, v2.0+ non-root)
- MLTK limitations (MQTT sensors only, one model per sensor)
- Practical visualization recommendations

---

### 14.4 IoT Platforms & Sensors

**Primary App/TA:** Custom API inputs, MQTT, webhook receivers.

---

### UC-14.4.1 · Smart Sensor Fleet Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** IoT sensors with low batteries or offline status create monitoring gaps. Fleet management ensures comprehensive coverage.
- **App/TA:** IoT platform API input
- **Data Sources:** IoT platform device management API
- **SPL:**
```spl
index=iot sourcetype="iot_platform:devices"
| where battery_pct < 20 OR status!="online" OR last_seen < relative_time(now(),"-4h")
| table device_id, device_type, location, battery_pct, status, last_seen
```
- **Implementation:** Poll IoT platform API for device status. Track battery levels, connectivity, and data freshness. Alert on low battery (<20%) and offline devices (>4 hours). Report on fleet health for maintenance planning.
- **Visualization:** Table (devices needing attention), Gauge (fleet health %), Pie chart (device status distribution), Map (device locations with status).
- **CIM Models:** N/A

---

### UC-14.4.2 · Environmental Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Distributed environmental sensors provide early warning of conditions that could damage equipment or inventory.
- **App/TA:** MQTT input, IoT platform API
- **Data Sources:** Environmental sensor data (temperature, humidity, water leak, smoke)
- **SPL:**
```spl
index=iot sourcetype="sensor:environmental"
| where water_detected="true" OR smoke_detected="true" OR temp_f > 90
| table _time, sensor_id, location, alert_type, value
```
- **Implementation:** Deploy environmental sensors in server rooms, warehouses, and facilities. Ingest via MQTT or API. Alert immediately on water leak or smoke detection. Track temperature/humidity trends per location.
- **Visualization:** Floor plan (sensors with status), Line chart (environmental trends), Table (alerts), Single value (active environmental alerts).
- **CIM Models:** N/A

---

### UC-14.4.3 · Asset Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Real-time asset location reduces search time, prevents loss, and enables utilization optimization.
- **App/TA:** Custom API input, BLE/GPS data
- **Data Sources:** GPS/BLE beacon data, RFID events
- **SPL:**
```spl
index=iot sourcetype="asset_tracking"
| stats latest(location) as current_location, latest(_time) as last_seen by asset_id, asset_type
| eval hours_since=round((now()-last_seen)/3600,1)
| where hours_since > 24
```
- **Implementation:** Ingest asset tracking data from GPS/BLE/RFID systems. Track asset locations and movement patterns. Alert when high-value assets leave designated zones. Report on asset utilization by location.
- **Visualization:** Map (asset locations), Table (asset inventory with location), Timeline (asset movement), Single value (assets not reporting).
- **CIM Models:** N/A

---

### UC-14.4.4 · Home Automation Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Smart home monitoring provides energy usage insights, security awareness, and automation troubleshooting.
- **App/TA:** Custom API input (Homey, Home Assistant)
- **Data Sources:** Homey/Home Assistant API (device events, energy data)
- **SPL:**
```spl
index=smarthome sourcetype="homey:events"
| stats count by device_name, capability, event_type
| sort -count
```
- **Implementation:** Configure Homey/Home Assistant webhook or API to send events to Splunk HEC. Track device states, energy consumption, and automation triggers. Create dashboards for home energy management and security.
- **Visualization:** Line chart (energy usage), Table (device events), Status grid (device × state), Single value (energy today).
- **CIM Models:** N/A

---

### UC-14.4.5 · IoT Device Firmware Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** IoT devices are frequently targeted for botnets. Outdated firmware creates network security risks.
- **App/TA:** IoT platform API
- **Data Sources:** Device inventory with firmware versions
- **SPL:**
```spl
index=iot sourcetype="iot_platform:inventory"
| stats latest(firmware_version) as current by device_type, model
| lookup iot_approved_firmware.csv device_type, model OUTPUT approved_version
| where current!=approved_version
| table device_type, model, count, current, approved_version
```
- **Implementation:** Export IoT device inventory with firmware versions periodically. Maintain approved firmware lookup. Report on compliance percentage. Prioritize updates for internet-connected devices. Track firmware update campaigns.
- **Visualization:** Table (non-compliant devices), Pie chart (compliant vs non-compliant), Bar chart (by device type), Single value (compliance %).
- **CIM Models:** N/A

---

### UC-14.4.6 · IoT Device Connectivity and Last-Seen Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Devices that stop reporting indicate failure, network issues, or tampering. Last-seen monitoring ensures fleet visibility and rapid response to outages.
- **App/TA:** IoT platform, MQTT/CoAP gateway logs
- **Data Sources:** Device heartbeat, last telemetry timestamp per device
- **SPL:**
```spl
index=iot sourcetype="iot:telemetry"
| stats latest(_time) as last_seen by device_id, gateway
| eval gap_sec=now()-last_seen
| where gap_sec > 3600
| table device_id, gateway, last_seen, gap_sec
```
- **Implementation:** Track last-seen per device from telemetry or heartbeat. Alert when device has not reported for >1 hour (tune per use case). Report on connectivity rate and devices with longest gap. Correlate with gateway health.
- **Visualization:** Table (devices with gap), Single value (devices offline), Line chart (connectivity rate).
- **CIM Models:** N/A

---

### UC-14.4.7 · OT Protocol Anomaly and Unauthorized Command Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual Modbus/OPC-UA/DNP3 commands or write operations can indicate attack or misconfiguration. Detection supports OT security and safety.
- **App/TA:** OT protocol decoders, industrial IDS
- **Data Sources:** Modbus/OPC-UA/DNP3 traffic, write and function code logs
- **SPL:**
```spl
index=ot sourcetype="modbus:traffic"
| search (function_code=6 OR function_code=16 OR function_code IN ("0x10","0x06"))
| stats count by src, unit_id, function_code, register
| where count > 100
| sort -count
```
- **Implementation:** Ingest OT protocol traffic from sensors or IDS. Baseline normal read/write patterns. Alert on write to critical registers, unknown source, or high command rate. Report on command distribution by source and function.
- **Visualization:** Table (write events), Timeline (commands by source), Bar chart (function codes).
- **CIM Models:** N/A

---

### UC-14.4.8 · Sensor Calibration and Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sensor drift causes incorrect control and compliance issues. Detecting drift against reference or peer sensors supports maintenance and data quality.
- **App/TA:** Sensor telemetry, reference sensor or baseline data
- **Data Sources:** Sensor readings, calibration records
- **SPL:**
```spl
index=iot sourcetype="sensor:reading"
| stats avg(value) as avg_val, stdev(value) as stdev_val by sensor_id, metric, _time span=1d
| eventstats avg(avg_val) as fleet_avg by metric
| eval drift=abs(avg_val-fleet_avg)
| where drift > (stdev_val * 3)
```
- **Implementation:** Ingest sensor readings and optional reference values. Compute baseline or peer average. Alert when a sensor deviates beyond threshold. Track calibration history and flag sensors due for recalibration.
- **Visualization:** Line chart (sensor vs baseline), Table (sensors with drift), Bar chart (drift magnitude).
- **CIM Models:** N/A

---

### UC-14.4.9 · Gateway and Edge Node Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Overloaded gateways drop telemetry or delay processing. Monitoring CPU, memory, and queue depth ensures edge reliability and capacity planning.
- **App/TA:** Edge/gateway metrics, SNMP or agent
- **Data Sources:** Gateway CPU, memory, disk, message queue depth
- **SPL:**
```spl
index=iot sourcetype="gateway:metrics"
| stats latest(cpu_pct) as cpu, latest(mem_pct) as mem, latest(queue_depth) as queue by gateway_id
| where cpu > 80 OR mem > 85 OR queue > 1000
| table gateway_id, cpu, mem, queue
```
- **Implementation:** Collect gateway and edge node metrics via agent or SNMP. Alert when CPU/memory or queue exceeds threshold. Report on utilization trend and top-loaded gateways. Plan scale-out before saturation.
- **Visualization:** Table (gateways over threshold), Gauge (queue depth), Line chart (utilization trend).
- **CIM Models:** N/A

---

### UC-14.4.10 · IoT Data Pipeline Throughput and Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pipeline latency or drop in throughput affects real-time dashboards and alerts. Monitoring supports SLA and troubleshooting of ingestion and processing.
- **App/TA:** Pipeline metrics, message broker logs
- **Data Sources:** Ingestion rate, end-to-end latency, backlog size
- **SPL:**
```spl
index=iot sourcetype="pipeline:metrics"
| stats avg(ingestion_rate) as rate, avg(latency_ms) as latency, max(backlog) as backlog by pipeline_stage, _time span=5m
| where rate < 100 OR latency > 5000 OR backlog > 50000
| table pipeline_stage, rate, latency, backlog
```
- **Implementation:** Ingest pipeline stage metrics (rate, latency, backlog). Alert when rate drops or latency/backlog exceeds threshold. Report on throughput by stage and trend. Correlate with gateway and cloud health.
- **Visualization:** Line chart (throughput and latency), Table (stages with issues), Single value (pipeline health).
- **CIM Models:** N/A

---

### UC-14.4.11 · Aranet Environmental Sensor Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Safety
- **Value:** CO2, temperature, humidity, and atmospheric pressure from Aranet4/Aranet PRO sensors support workplace air quality and occupant comfort. Exceedances indicate ventilation issues and may violate ASHRAE 62.1 or local workplace standards.
- **App/TA:** Custom (Aranet Cloud API or local gateway)
- **Data Sources:** Aranet API (sensor readings JSON)
- **SPL:**
```spl
index=environment sourcetype="aranet:sensor"
| where co2_ppm > 1000 OR temp_c < 18 OR temp_c > 26 OR humidity_pct < 30 OR humidity_pct > 60 OR pressure_hpa < 980 OR pressure_hpa > 1050
| eval exceedance=case(co2_ppm>1000, "CO2", temp_c<18 OR temp_c>26, "Temperature", humidity_pct<30 OR humidity_pct>60, "Humidity", pressure_hpa<980 OR pressure_hpa>1050, "Pressure", 1=1, "OK")
| table _time, sensor_id, location, co2_ppm, temp_c, humidity_pct, pressure_hpa, exceedance
```
- **Implementation:** Integrate Aranet Cloud API or local Aranet gateway (e.g. Aranet Cloud Bridge) to fetch sensor readings. Schedule scripted input or HEC to ingest JSON (CO2 ppm, temperature °C, humidity %, pressure hPa) every 5–15 minutes. Alert when CO2 exceeds 1000 ppm (ASHRAE 62.1 recommends <1000 ppm for occupied spaces), temperature outside 18–26°C, or humidity outside 30–60%. Track trends for ventilation and HVAC tuning.
- **Visualization:** Gauge (CO2 ppm per zone), Line chart (CO2, temp, humidity trend), Heatmap (zone × CO2 level), Table (sensors with exceedances), Single value (zones in compliance %).
- **CIM Models:** N/A


---

### UC-14.4.12 · IoT Device Fleet Health Dashboard
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Single pane for battery, RSSI, last-seen, and firmware supports NOC and field operations.
- **App/TA:** IoT platform API, MQTT broker metrics
- **Data Sources:** `sourcetype="iot_platform:devices"`
- **SPL:**
```spl
index=iot sourcetype="iot_platform:devices"
| eval health=case(status!="online","offline", battery_pct<15,"low_battery", rssi< -110,"poor_rssi", 1=1,"ok")
| stats count by health, product_family
| sort health
```
- **Implementation:** Normalize vendor fields. Refresh dashboard every 5 min. Drill to device detail.
- **Visualization:** Status grid (region × health), Treemap (fleet by family), Single value (% healthy).
- **CIM Models:** N/A

---

### UC-14.4.13 · Firmware Update Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** OTA campaigns must complete; stragglers remain vulnerable to known exploits.
- **App/TA:** IoT DM, OTA job logs
- **Data Sources:** `sourcetype="iot:ota"` (job_id, status, version)
- **SPL:**
```spl
index=iot sourcetype="iot:ota"
| stats latest(target_version) as tgt by device_id
| join max=1 device_id [
  search index=iot sourcetype="iot_platform:devices"
  | stats latest(firmware_version) as cur by device_id
]
| where cur!=tgt
| table device_id, cur, tgt
```
- **Implementation:** Compare device inventory to OTA target per wave. Escalate devices >7 days behind.
- **Visualization:** Bar chart (compliance by wave), Table (lagging devices).
- **CIM Models:** N/A

---

### UC-14.4.14 · Sensor Data Gap Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Missing telemetry breaks automation and safety analytics; gaps often precede device failure.
- **App/TA:** MQTT/CoAP gateway logs
- **Data Sources:** `sourcetype="iot:telemetry"`
- **SPL:**
```spl
index=iot sourcetype="iot:telemetry"
| stats latest(_time) as last_seen by device_id, sensor_id
| eval gap_min=round((now()-last_seen)/60,1)
| where gap_min > 30
| table device_id, sensor_id, last_seen, gap_min
```
- **Implementation:** Tune gap threshold per sensor class (critical vs ambient). Alert on gap or stepped decrease in message rate.
- **Visualization:** Table (gaps), Heatmap (device × hour), Line chart (messages/min).
- **CIM Models:** N/A

---

### UC-14.4.15 · MQTT Broker Overload
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Broker CPU, connection count, and retained message backlog indicate need to shard or scale.
- **App/TA:** Mosquitto/HiveMQ/AWS IoT metrics
- **Data Sources:** `sourcetype="mqtt:broker_metrics"`
- **SPL:**
```spl
index=iot sourcetype="mqtt:broker_metrics"
| where connections > max_connections*0.9 OR cpu_pct > 85 OR dropped_messages > 0
| timechart span=1m avg(connections) as conn, avg(cpu_pct) as cpu, sum(dropped_messages) as drops
```
- **Implementation:** Scrape Prometheus or vendor API. Alert on sustained high utilization or any dropped messages. Correlate with misbehaving clients publishing at high QoS0 rate.
- **Visualization:** Line chart (connections and CPU), Table (brokers with drops), Gauge (connection %).
- **CIM Models:** N/A

---

### UC-14.4.16 · IoT Device Certificate Expiry
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Expired device certs break TLS to cloud and brick OTA; proactive rotation avoids mass outages.
- **App/TA:** PKI portal, device shadow attributes
- **Data Sources:** `sourcetype="iot:cert_inventory"` (device_id, not_after)
- **SPL:**
```spl
index=iot sourcetype="iot:cert_inventory"
| eval days_left=round((strptime(not_after,"%Y-%m-%dT%H:%M:%SZ")-now())/86400,0)
| where days_left < 45
| table device_id, not_after, days_left
| sort days_left
```
- **Implementation:** Ingest cert metadata from AWS IoT / Azure DPS / custom PKI. Alert at 45, 14, 7 days. Automate renewal jobs.
- **Visualization:** Table (certs expiring), Timeline (renewal window), Single value (devices <30d).
- **CIM Models:** N/A

---

### UC-14.4.17 · Edge-to-Cloud Sync Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Store-and-forward gaps mean stale dashboards and missed alerts for remote sites.
- **App/TA:** Edge agent logs (Azure IoT Edge, Greengrass)
- **Data Sources:** `sourcetype="edge:sync"`
- **SPL:**
```spl
index=iot sourcetype="edge:sync"
| where status="failed" OR backlog_mb > 100 OR last_success_age_sec > 600
| stats latest(backlog_mb) as backlog, latest(status) as st by edge_id, cloud_endpoint
| sort -backlog
```
- **Implementation:** Parse sync success, backoff, and queue depth. Alert on failure or growing backlog. Correlate with WAN outages.
- **Visualization:** Table (edges with backlog), Line chart (backlog MB), Single value (edges in sync).
- **CIM Models:** N/A

---

### UC-14.4.18 · IoT Device Provisioning Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Unauthorized provisioning events create shadow devices and billing abuse.
- **App/TA:** AWS IoT Fleet / Azure DPS audit
- **Data Sources:** AWS CloudTrail (`sourcetype="aws:cloudtrail"`; filter `eventSource` / `eventName` for IoT control-plane APIs such as `iot.amazonaws.com`), or a custom `iot:provisioning` sourcetype from your pipeline.
- **SPL:**
```spl
index=audit sourcetype="iot:provisioning"
| where action IN ("RegisterThing","CreateCertificate","AttachPolicy")
| stats count by actor, device_template, src
| where count > 50
| sort -count
```
- **Implementation:** Compare provisioning rate to approved baseline. Alert on new template or IAM principal. Cross-check with HR for contractor access. For AWS, prefer CloudTrail (`sourcetype="aws:cloudtrail"`) with `eventSource="iot.amazonaws.com"` (and relevant `eventName` values) instead of a non-standard `cloudtrail:iot` sourcetype; keep `iot:provisioning` only if that is your normalized pipeline.
- **Visualization:** Table (provisioning events), Timeline (bursts), Bar chart (by actor).
- **CIM Models:** N/A

---

### UC-14.4.19 · BLE/Zigbee Gateway Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Mesh coordinators and gateways aggregate low-power sensors; their health affects entire buildings.
- **App/TA:** Zigbee2MQTT, Home Assistant, vendor hub
- **Data Sources:** `sourcetype="zigbee:gateway"` OR `sourcetype="ble:gateway"`
- **SPL:**
```spl
index=iot sourcetype IN ("zigbee:gateway","ble:gateway")
| where coordinator_status!="OK" OR offline_devices > 5 OR mqtt_connected=0
| table _time, gateway_id, coordinator_status, offline_devices, mqtt_connected
```
- **Implementation:** Poll hub API for mesh depth, neighbor loss, and MQTT uplink. Alert on coordinator down or offline child count spike.
- **Visualization:** Status grid (gateway × health), Line chart (offline device count), Table (gateways degraded).
- **CIM Models:** N/A


---

### 14.5 MQTT and OPC-UA (Edge Hub and Gateways)

**Primary App/TA:** Splunk Edge Hub (built-in MQTT broker, OPC-UA connector), Azure IoT Edge Hub, MQTT brokers (Eclipse Mosquitto, HiveMQ), OPC-UA gateways (KEPServerEX, Prosys), Splunk OT Intelligence.

**Data Sources:** MQTT topics (sensors, actuators, BMS, SCADA); OPC-UA nodes (PLC tags, alarms, history); Edge Hub health and connector metrics; gateway logs.

---

### UC-14.5.1 · MQTT Topic Message Rate and Subscription Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Per-topic message rate and subscriber count indicate whether sensors and downstream consumers are healthy. Sudden drops mean a publisher or subscription failed; spikes can indicate a runaway device or replay.
- **App/TA:** Splunk Edge Hub (MQTT broker), MQTT broker metrics (Mosquitto, HiveMQ)
- **Data Sources:** `index=edge-hub-data` (metrics by topic), broker stats API or log-derived metrics
- **SPL:**
```spl
index=edge-hub-data OR index=ot sourcetype=mqtt OR sourcetype=edge_hub
| stats count as msg_count, latest(_time) as last_seen by topic, host, _time span=5m
| eval age_sec = now() - last_seen
| where age_sec > 600 OR msg_count < 1
| table topic host msg_count last_seen age_sec
```
- **Implementation:** Use Edge Hub MQTT topic subscriptions with metric extraction (topic as dimension). Or ingest broker metrics (e.g. Mosquitto stats, HiveMQ REST API) for messages per topic. Alert when a critical topic has no messages for >10 minutes or rate drops below baseline. Dashboard message rate by topic and subscriber count.
- **Visualization:** Line chart (message rate by topic), Table (topics with no recent data), Single value (topics healthy %).
- **CIM Models:** N/A

---

### UC-14.5.2 · OPC-UA Server Connection and Session Count
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** OPC-UA session count and connection state indicate whether Edge Hub or gateways are successfully bound to PLCs/servers. Lost sessions create data gaps and break real-time monitoring.
- **App/TA:** Splunk Edge Hub (OPC-UA connector), OPC-UA gateway (KEPServerEX, Prosys)
- **Data Sources:** `index=edge-hub-logs` (connector logs), gateway connection status API or logs
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log "opcua" OR "opc-ua"
| rex "session|connection|endpoint"
| stats count, latest(_time) as last_seen by host, connection_state
| where connection_state="disconnected" OR connection_state="failed"
| table host connection_state count last_seen
```
- **Implementation:** Configure Edge Hub OPC-UA connector with endpoint URL and security. Forward connector logs to edge-hub-logs. Parse connection/session state from log messages or gateway API. Alert when connection state is disconnected or session count drops to zero for a critical server.
- **Visualization:** Table (server, state, session count), Status grid (endpoint × state), Single value (OPC-UA connections healthy).
- **CIM Models:** N/A

---

### UC-14.5.3 · Edge Hub MQTT Broker Client Disconnections
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Frequent client disconnections or reconnect storms indicate network issues, broker overload, or misconfigured keep-alive. Monitoring supports stability and capacity planning.
- **App/TA:** Splunk Edge Hub (built-in MQTT broker), broker logs
- **Data Sources:** `index=edge-hub-logs sourcetype=splunk_edge_hub_log` (broker events), MQTT broker log (disconnect, connect)
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log "mqtt" ("disconnect" OR "connection closed" OR "client")
| rex "client_id=(?<client_id>\S+)|client (?<client_id>\S+)"
| stats count as disconnect_count by client_id, host, _time span=15m
| where disconnect_count > 5
| sort -disconnect_count
```
- **Implementation:** Enable MQTT broker logging on Edge Hub or external broker. Ingest disconnect and connection events. Count disconnects per client per 15 minutes. Alert on disconnect storms (>5 in 15 min) or when a critical client (e.g. PLC gateway) disconnects.
- **Visualization:** Table (client, disconnect count), Line chart (disconnects over time), Timeline (connection events).
- **CIM Models:** N/A

---

### UC-14.5.4 · OPC-UA Node Value Change Rate and Anomaly
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Anomaly
- **Value:** PLC tag value change rate and distribution indicate normal process behavior. Sudden change in rate or value distribution can signal sensor fault, process upset, or cyber event.
- **App/TA:** Splunk Edge Hub (OPC-UA connector), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data sourcetype=splunk_edge_hub_opcua` (node values)
- **SPL:**
```spl
index=edge-hub-data sourcetype=splunk_edge_hub_opcua
| stats count as sample_count, dc(node_id) as nodes_seen by host, _time span=5m
| eventstats avg(sample_count) as avg_count, stdev(sample_count) as std_count by host
| eval z = if(std_count>0, (sample_count-avg_count)/std_count, 0)
| where abs(z) > 3
| table host _time sample_count avg_count z
```
- **Implementation:** Ingest OPC-UA node samples from Edge Hub. Compute per-host message rate (samples per 5 min). Baseline mean and stdev; alert when rate exceeds 3 standard deviations. Optionally run MLTK anomaly detection on critical tags.
- **Visualization:** Line chart (sample rate by host), Table (anomalous intervals), Single value (current rate vs baseline).
- **CIM Models:** N/A

---

### UC-14.5.5 · Edge Hub to Cloud HEC Forwarding Backlog
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** When Edge Hub loses connectivity to Splunk, data backs up locally (e.g. 3M sensor points in SQLite). Backlog growth and drain rate indicate risk of data loss and recovery time.
- **App/TA:** Splunk Edge Hub (system health)
- **Data Sources:** `index=edge-hub-health sourcetype=edge_hub` (backlog, queue depth)
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(backlog_count) as backlog, latest(hec_connected) as connected by host
| where backlog > 10000 OR connected != 1
| table host backlog connected _time
```
- **Implementation:** Edge Hub reports backlog and HEC connection state to edge-hub-health. Ingest and alert when backlog exceeds threshold (e.g. 10K events) or connected=0. Track backlog drain rate after reconnect to estimate catch-up time.
- **Visualization:** Gauge (backlog per device), Single value (HEC connected), Line chart (backlog over time).
- **CIM Models:** N/A

---

### UC-14.5.6 · MQTT Retain and Last Will Message Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Retained messages and Last Will payloads can contain sensitive state. Auditing who published retain/LWT and when supports change control and security review.
- **App/TA:** MQTT broker (access log, audit log)
- **Data Sources:** Broker audit log (publish with retain=1, will payload)
- **SPL:**
```spl
index=ot sourcetype=mqtt_broker_audit (retain=1 OR "last_will" OR "will_message")
| stats count by client_id, topic, action, _time span=1h
| where count > 0
| table _time client_id topic action count
```
- **Implementation:** Enable broker audit or access logging for MQTT publish (include retain flag and will payload if logged). Forward to Splunk. Alert on new retain on sensitive topics or LWT changes. Dashboard retain/LWT events by client and topic.
- **Visualization:** Table (client, topic, retain/LWT events), Timeline (audit events).
- **CIM Models:** N/A

---

### UC-14.5.7 · OPC-UA Alarms and Events Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** OPC-UA alarm/event queues that grow indicate slow consumption or overflow risk. Overflow can drop critical alarms; depth trending supports connector and gateway sizing.
- **App/TA:** OPC-UA gateway, Edge Hub OPC-UA connector
- **Data Sources:** Gateway or connector metrics (alarm queue depth, event count)
- **SPL:**
```spl
index=edge-hub-data OR index=ot sourcetype=opcua_metrics
| stats latest(alarm_queue_depth) as queue, latest(events_pending) as pending by host, endpoint
| where queue > 100 OR pending > 500
| table host endpoint queue pending
```
- **Implementation:** Expose alarm/event queue depth from OPC-UA gateway or Edge Hub connector (if available). Ingest as metric. Alert when queue depth exceeds 100 or pending events >500. Tune subscription and sampling rate if queue grows persistently.
- **Visualization:** Gauge (queue depth), Line chart (queue over time), Table (endpoints over threshold).
- **CIM Models:** N/A

---

### UC-14.5.8 · MQTT QoS 0/1/2 Delivery and Drops
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** QoS 0 messages can be dropped under load; QoS 1/2 add overhead. Tracking delivery by QoS and drop rate supports SLA and broker tuning.
- **App/TA:** MQTT broker metrics (messages in/out, dropped)
- **Data Sources:** Broker stats (e.g. Mosquitto messages received/sent, dropped)
- **SPL:**
```spl
index=ot sourcetype=mqtt_broker_metrics
| stats sum(messages_in) as in, sum(messages_out) as out, sum(messages_dropped) as dropped by qos, _time span=5m
| eval drop_rate=if(in>0, round(dropped/in*100, 2), 0)
| where drop_rate > 1 OR dropped > 0
| table _time qos in out dropped drop_rate
```
- **Implementation:** Collect broker metrics (SNMP, REST, or log parsing) for messages in/out/dropped by QoS. Ingest to Splunk. Alert when drop rate exceeds 1% or absolute drops exceed threshold. Correlate with broker CPU and connection count.
- **Visualization:** Line chart (in/out/dropped by QoS), Table (drop rate by QoS), Single value (total drops).
- **CIM Models:** N/A

---

### UC-14.5.9 · OPC-UA Certificate Expiration and Trust
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** Expired or untrusted OPC-UA certificates break secure connections and prevent data collection. Proactive monitoring avoids blind spots after certificate rollover failures.
- **App/TA:** Edge Hub OPC-UA connector, OPC-UA gateway
- **Data Sources:** Connector/gateway logs (certificate validation, trust list)
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log "opcua" ("certificate" OR "trust" OR "expir" OR "reject")
| rex "expir|reject|invalid|cert"
| table _time host message
| sort -_time
```
- **Implementation:** Forward OPC-UA connector and gateway logs. Parse certificate and trust-related messages. Maintain a script or lookup of cert expiry dates; alert when expiry is within 30 days or when log shows validation failure.
- **Visualization:** Table (cert expiry by endpoint), Timeline (cert events), Single value (certs expiring in 30d).
- **CIM Models:** N/A

---

### UC-14.5.10 · Edge Hub Local Storage and SQLite Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Edge Hub stores backlog in SQLite when disconnected. Disk usage and backlog size must stay within limits (e.g. 3M sensor points) to avoid data loss and device lockup.
- **App/TA:** Splunk Edge Hub (device health)
- **Data Sources:** `index=edge-hub-health` (disk_usage, backlog_count)
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(disk_usage) as disk_pct, latest(backlog_count) as backlog by host
| where disk_pct > 85 OR backlog > 2000000
| table host disk_pct backlog _time
```
- **Implementation:** Edge Hub reports disk and backlog to edge-hub-health. Alert when disk exceeds 85% or backlog approaches device limit (e.g. 2M). Plan connectivity and storage upgrades before saturation.
- **Visualization:** Gauge (disk %), Line chart (backlog over time), Table (devices near limit).
- **CIM Models:** N/A

---

### UC-14.5.11 · MQTT Authentication Failure and ACL Denials
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed MQTT logins and publish/subscribe denials indicate credential abuse, misconfiguration, or attack. Monitoring supports access control and incident response.
- **App/TA:** MQTT broker (auth and ACL logs)
- **Data Sources:** Broker access log (auth failure, ACL deny)
- **SPL:**
```spl
index=ot sourcetype=mqtt_broker_log ("auth failed" OR "ACL deny" OR "access denied" OR "unauthorized")
| stats count by client_id, src, reason, _time span=15m
| where count > 5
| sort -count
```
- **Implementation:** Enable broker authentication and ACL logging. Forward to Splunk. Alert when failure count from a single client or IP exceeds threshold. Dashboard failures by client and topic.
- **Visualization:** Table (client, IP, reason, count), Timeline (denials), Bar chart (top denied clients).
- **CIM Models:** Authentication

---

### UC-14.5.12 · OPC-UA Subscription Latency and Sampling Overrun
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** High subscription latency or sampling overrun (server missing sample interval) degrades real-time visibility. Tracking supports connector and server tuning.
- **App/TA:** OPC-UA gateway, Edge Hub OPC-UA connector
- **Data Sources:** Connector metrics (subscription latency, overrun count)
- **SPL:**
```spl
index=edge-hub-data OR index=ot sourcetype=opcua_metrics
| stats avg(subscription_latency_ms) as avg_latency, sum(sampling_overrun_count) as overruns by host, subscription_id
| where avg_latency > 500 OR overruns > 0
| table host subscription_id avg_latency overruns
```
- **Implementation:** If gateway or Edge Hub exposes subscription latency and overrun metrics, ingest them. Alert when latency exceeds 500 ms or overrun count is non-zero. Reduce sampling rate or add resources if persistent.
- **Visualization:** Line chart (latency by subscription), Table (overruns by subscription), Single value (max latency).
- **CIM Models:** N/A

---

### UC-14.5.13 · Edge Hub Container Health (MQTT/OPC-UA Modules)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Edge Hub runs MQTT broker and OPC-UA connector as modules. Container restarts or OOM kills cause data gaps and require investigation.
- **App/TA:** Splunk Edge Hub (system logs)
- **Data Sources:** `index=edge-hub-logs` (container lifecycle, OOM)
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log ("container" OR "module" OR "oom" OR "restart")
| search "mqtt" OR "opcua" OR "opc-ua"
| stats count by log_level, message, _time span=1h
| where count > 0
| table _time log_level message count
```
- **Implementation:** Forward Edge Hub system logs. Parse container/module start, stop, and OOM events. Alert on any restart or OOM for MQTT or OPC-UA modules. Correlate with device memory and CPU from edge-hub-health.
- **Visualization:** Timeline (container events), Table (restart/OOM by module), Single value (modules healthy).
- **CIM Models:** N/A

---

### UC-14.5.14 · MQTT TLS Handshake and Cipher Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** TLS handshake failures or weak ciphers indicate misconfiguration or downgrade attacks. Monitoring ensures encrypted MQTT and policy compliance.
- **App/TA:** MQTT broker (TLS log), reverse proxy logs
- **Data Sources:** Broker or proxy TLS logs (handshake, cipher)
- **SPL:**
```spl
index=ot sourcetype=mqtt_tls_log ("handshake failed" OR "certificate verify" OR "TLS")
| rex "cipher=(?<cipher>\S+)|protocol=(?<protocol>\S+)"
| stats count by cipher, protocol, reason
| where cipher!="*TLS_AES*" OR protocol!="TLSv1.2" OR reason="failed"
| table cipher protocol reason count
```
- **Implementation:** Enable TLS logging on MQTT broker or proxy. Ingest handshake success/failure and negotiated cipher/protocol. Alert on handshake failure or use of non-approved ciphers (e.g. block TLS 1.0/1.1 and weak ciphers).
- **Visualization:** Table (cipher, protocol, failures), Timeline (handshake events), Single value (TLS failures).
- **CIM Models:** N/A

---

### UC-14.5.15 · OPC-UA Write and Permission Denials
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unauthorized write attempts or permission denials can indicate misconfiguration, abuse, or attack. Auditing supports least-privilege and security review.
- **App/TA:** OPC-UA server/gateway (audit or security log)
- **Data Sources:** OPC-UA server audit log (write request, status code)
- **SPL:**
```spl
index=ot sourcetype=opcua_audit action=write
| search status_code!="Good" OR permission_denied
| stats count by client_id, node_id, status_code, _time span=1h
| where count > 0
| table _time client_id node_id status_code count
```
- **Implementation:** Enable OPC-UA server audit or security logging for write requests. Forward to Splunk. Alert on write denials for critical nodes or high volume of denials from a single client. Dashboard writes by client and node.
- **Visualization:** Table (client, node, status, count), Timeline (write denials), Bar chart (denials by node).
- **CIM Models:** N/A

---

### UC-14.5.16 · HiveMQ Cluster Node Health and Split-Brain Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** MQTT broker cluster faults and split-brain conditions fragment subscriptions and retained state; early detection avoids cross-site messaging black holes.
- **App/TA:** HiveMQ Splunk Extension (SVA), HiveMQ Enterprise logging
- **Data Sources:** `index=ot` `sourcetype="hivemq:log"` cluster/quorum log lines; optional `sourcetype="hivemq:metrics"`
- **SPL:**
```spl
index=ot sourcetype="hivemq:log"
| rex field=_raw "(?i)(?<cluster_event>split.?brain|quorum|not enough members|cluster view|partition|lost majority)"
| where isnotnull(cluster_event)
| rex field=_raw "(?i)node[=\s]+(?<node_id>[^\s,;]+)"
| stats count by host, node_id, cluster_event
| sort - count
```
- **Implementation:** Forward HiveMQ broker logs with cluster logger categories enabled to Splunk. Normalize host to broker hostname. Alert on any match of split-brain/quorum strings or sudden role flaps.
- **Visualization:** Timeline (cluster events), Table (event counts by broker), Single value (split-brain indicators in last 24h).
- **CIM Models:** N/A

---

### UC-14.5.17 · MQTT Shared Subscription Load Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Shared subscriptions should balance load across consumers; skew indicates stuck consumers or broker-side dispatch issues that inflate latency.
- **App/TA:** HiveMQ Splunk Extension, MQTT Modular Input (Splunkbase 1890)
- **Data Sources:** `index=ot` `sourcetype="mqtt:message"` fields `topic`, optional `subscription_group`
- **SPL:**
```spl
index=ot sourcetype="mqtt:message"
| eval t=lower(topic)
| where like(t,"$share/%")
| rex field=topic "^\$share\/(?<share_group>[^/]+)\/(?<base_topic>.+)"
| stats count as msgs by share_group, base_topic
| eventstats sum(msgs) as total_by_topic by base_topic
| eval share_pct=round(100*msgs/total_by_topic,2)
| sort base_topic, -msgs
```
- **Implementation:** If the modular input does not preserve `$share/...` in topic, enable broker metrics for shared subscriptions or ingest dispatch logs. For high volume, sample at the broker or pre-aggregate.
- **Visualization:** Bar chart (messages per share group), Heatmap (group × time), Table (skew: max/min share_pct per base topic).
- **CIM Models:** N/A

---

### UC-14.5.18 · HiveMQ Retained Message Store Growth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Retained messages accumulate with misconfigured publishers; growth risks disk exhaustion and slower broker startup, especially at OT edge with constrained storage.
- **App/TA:** HiveMQ Splunk Extension (metrics to Splunk)
- **Data Sources:** `index=ot` `sourcetype="hivemq:metrics"` retained message counters
- **SPL:**
```spl
index=ot sourcetype="hivemq:metrics"
| eval m=lower(coalesce(metric_name, metric, name))
| where match(m, "retain")
| eval v=coalesce(value, metric_value, _value)
| bin _time span=1h
| stats max(v) as retained_max by host, _time
| timechart span=1h max(retained_max) by host
```
- **Implementation:** Map the exact HiveMQ metric name from your Prometheus/SVA mapping. Alert on week-over-week growth or crossing a capacity threshold. Correlate spikes with new devices publishing retained messages on unique topics.
- **Visualization:** Line chart (retained count over time), Area chart (growth rate), Single value (current max), Table (brokers over threshold).
- **CIM Models:** N/A

---

### UC-14.5.19 · MQTT Client Disconnect Reason Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Categorized disconnect reasons separate clean shutdowns from timeouts, kicks, and protocol errors — shortening MTTR for unstable OT clients.
- **App/TA:** HiveMQ Splunk Extension, HiveMQ broker logs
- **Data Sources:** `index=ot` `sourcetype="hivemq:log"` client disconnect lines
- **SPL:**
```spl
index=ot sourcetype="hivemq:log"
| search disconnect OR DISCONNECT OR "Client ID"
| rex field=_raw "(?i)client[_ ]?id[:=]\s*(?<client_id>[^\s,;]+)"
| eval category=case(
    match(_raw,"(?i)timeout|idle|keep.?alive"), "timeout",
    match(_raw,"(?i)admin|kick|forced"), "admin_kick",
    match(_raw,"(?i)reset|eof|closed"), "network_error",
    match(_raw,"(?i)not.?authorized|bad.?user"), "auth_failure",
    true(), "other"
  )
| stats count by category, client_id, host
| sort - count
```
- **Implementation:** Align rex patterns with HiveMQ log format for your version. If reason codes are numeric, maintain a lookup mapping code to category. Filter out expected maintenance windows.
- **Visualization:** Bar chart (disconnects by category), Pie chart (category mix), Table (top client_ids), Timeline (disconnect bursts).
- **CIM Models:** N/A

---

### UC-14.5.20 · HiveMQ Extension Execution Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** HiveMQ extensions (enterprise integrations, custom interceptors) can fail independently; tracking exceptions prevents silent drops in policy enforcement and data enrichment.
- **App/TA:** HiveMQ Splunk Extension, HiveMQ broker logs
- **Data Sources:** `index=ot` `sourcetype="hivemq:log"` extension error lines
- **SPL:**
```spl
index=ot sourcetype="hivemq:log"
| where match(_raw, "(?i)extension") AND (match(_raw, "(?i)error|exception|failed") OR match(_raw," ERROR "))
| rex field=_raw "(?i)extension[:\s]+(?<extension_id>[^\s\]\[]+)"
| rex field=_raw "(?i)(?<ex_type>[A-Za-z0-9_.]+Exception)"
| stats count by host, extension_id, ex_type
| sort - count
```
- **Implementation:** Ensure HiveMQ log level captures extension exceptions. Create suppressions for known benign stack signatures via a lookup table. Consider separate alerts for WARN vs ERROR thresholds.
- **Visualization:** Table (top extensions by errors), Line chart (error rate over time), Bar chart (errors by host).
- **CIM Models:** N/A

---

### UC-14.5.21 · MQTT Topic Tree Depth and Fan-Out Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Deep topic hierarchies and high fan-out increase broker memory and ACL evaluation costs; trending complexity helps right-size clusters and topic design reviews.
- **App/TA:** MQTT Modular Input (Splunkbase 1890), HiveMQ Splunk Extension
- **Data Sources:** `index=ot` `sourcetype="mqtt:message"` fields `topic`
- **SPL:**
```spl
index=ot sourcetype="mqtt:message"
| eval depth=mvcount(split(topic,"/"))
| eval parts=split(topic,"/")
| eval root=mvindex(parts,0)
| stats count as msgs, dc(topic) as unique_topics, max(depth) as max_depth, avg(depth) as avg_depth by root, host
| sort - unique_topics
```
- **Implementation:** For very high message rates, sample or pre-aggregate in HiveMQ metrics. Exclude test topics. Pair with ACL audit if unauthorized deep topics appear.
- **Visualization:** Bar chart (unique topics by root prefix), Histogram (depth distribution), Table (top fan-out roots).
- **CIM Models:** N/A

---

### UC-14.5.22 · HiveMQ License Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Connection growth toward license limits causes hard rejections during peaks; trending utilization supports procurement decisions before production brownouts.
- **App/TA:** HiveMQ Splunk Extension (metrics), HiveMQ license reporting
- **Data Sources:** `index=ot` `sourcetype="hivemq:metrics"` connection count gauges
- **SPL:**
```spl
index=ot sourcetype="hivemq:metrics"
| eval m=lower(coalesce(metric_name, metric, name))
| eval v=coalesce(value, metric_value, _value)
| where match(m, "connection") AND match(m,"current|active|open|established")
| bin _time span=5m
| stats max(v) as connections by host, _time
| eval license_limit=10000
| eval utilization_pct=round(100*connections/license_limit,2)
| where utilization_pct>85
```
- **Implementation:** Replace the static `license_limit` with a lookup or environment-specific value. Alert at 85%/95% thresholds with different severities.
- **Visualization:** Line chart (connections vs limit), Area chart (utilization %), Gauge (current utilization), Table (hosts approaching limit).
- **CIM Models:** N/A

---

### 14.6 Zeek ICS Deep Protocol Inspection

**Primary App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884), TA for Corelight (Splunkbase 3885). Parses CISA ICSNPP protocol analyzers.

**Data Sources:** Zeek ICS protocol logs from ICSNPP parsers: `sourcetype="zeek:s7comm:json"`, `sourcetype="zeek:modbus_detailed:json"`, `sourcetype="zeek:dnp3:json"`, `sourcetype="zeek:enip:json"`, `sourcetype="zeek:bacnet:json"`, `sourcetype="zeek:iec104:json"`, `sourcetype="zeek:hartip:json"`, `sourcetype="corelight_s7comm"`, etc.

---

### UC-14.6.1 · S7comm PLC Read/Write Operation Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance, Change
- **Industry:** Manufacturing
- **Value:** Unexpected write-heavy traffic to Siemens PLCs can indicate tampering or mis-engineered automation; tracking read versus write ratios supports least-privilege engineering and early detection of process-impacting changes.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:s7comm:json"` (ICSNPP `s7comm.log` fields such as `function_name`, `rosctr_name`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:s7comm:json"
| eval op=case(match(function_name,"(?i)read"),"read",match(function_name,"(?i)write"),"write","other")
| stats count(eval(op=="read")) as reads count(eval(op=="write")) as writes by source_h destination_h
| eval write_ratio=if(reads+writes>0, round(100*writes/(reads+writes),2), null())
| where writes>0 AND (reads=0 OR write_ratio>25)
| table source_h destination_h reads writes write_ratio
```
- **Implementation:** Deploy Zeek with ICSNPP-S7COMM on passive taps or SPAN ports on OT VLANs carrying PLC traffic; forward JSON logs to Splunk with TA for Zeek field extractions. Baseline read/write ratios per engineering workstation pair; tune the write-ratio threshold per zone and alert on off-hours spikes.
- **Visualization:** Bar chart (writes vs reads by source/destination pair), Single value (max write_ratio), Table (top writers).
- **CIM Models:** N/A

---

### UC-14.6.2 · S7comm Program Upload/Download Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Change, Compliance
- **Industry:** Manufacturing
- **Value:** PLC program upload/download changes process logic and safety envelopes; correlating these events with change tickets prevents unauthorized logic swaps that could disrupt operations or bypass interlocks.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:s7comm:json"` (ICSNPP `s7comm_upload_download.log`: `function_code`, `filename`, `block_type`, `block_number`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:s7comm:json"
| eval fc_hex=replace(function_code,"0x","")
| eval fc=coalesce(tonumber(fc_hex,16), tonumber(function_code))
| where fc IN (26,27) OR function_code IN ("0x1a","0x1b","26","27") OR isnotnull(filename)
| stats earliest(_time) as first_seen latest(_time) as last_seen values(filename) as filenames values(block_type) as block_types values(block_number) as block_numbers by source_h destination_h uid
| table first_seen last_seen source_h destination_h filenames block_types block_numbers
```
- **Implementation:** Enable ICSNPP upload/download logging on Zeek sensors at OT taps; ingest into `index=ot`. Map `function_code` 0x1a/0x1b (decimal 26/27) to engineering change workflows; require ticket IDs in SOAR for acknowledged maintenance windows.
- **Visualization:** Timeline (upload/download events), Table (filename, block, endpoints), Single value (events in last 24h).
- **CIM Models:** N/A

---

### UC-14.6.3 · S7comm CPU State Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Security, Availability
- **Industry:** Manufacturing
- **Value:** CPU stop/start or mode transitions can halt a line or leave a PLC in an unsafe state; detecting them from the wire supports both troubleshooting and detection of malicious or accidental operational disruption.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:s7comm:json"` (`rosctr_name`, `subfunction_name`, `function_name`, `error_class`)
- **SPL:**
```spl
index=ot sourcetype="zeek:s7comm:json"
| where match(subfunction_name,"(?i)STOP|START|RESUME") OR match(rosctr_name,"(?i)STOP|RUN|HOLD") OR match(function_name,"(?i)PLC|mode|cpu")
| stats count by source_h destination_h rosctr_name subfunction_name function_name
| sort - count
| head 100
```
- **Implementation:** Place Zeek on taps facing S7 controllers and HMIs; normalize `subfunction_name`/`rosctr_name` strings from production captures. Alert on stop/start patterns outside approved maintenance; correlate with MES/SCADA alarms for the same asset.
- **Visualization:** Timeline (state-related messages), Bar chart (count by subfunction_name), Table (source, destination, fields).
- **CIM Models:** N/A

---

### UC-14.6.4 · S7comm Unauthorized Function Block Access
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Industry:** Manufacturing
- **Value:** Access attempts to protected OB/FB/FC blocks may indicate credential abuse or ladder tampering; monitoring errors and targeted function names supports defense-in-depth around safety-related code.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:s7comm:json"` (`function_name`, `subfunction_name`, `error_class`, `error_code`)
- **SPL:**
```spl
index=ot sourcetype="zeek:s7comm:json"
| where (match(function_name,"(?i)block|OB|FB|FC|SFB") OR match(subfunction_name,"(?i)block"))
| where (isnotnull(error_code) AND error_code!="0x0000") OR (isnotnull(error_class) AND NOT error_class IN ("NONE","-",""))
| stats count by source_h destination_h function_name subfunction_name error_class error_code
| where count>=3
| sort - count
```
- **Implementation:** Deploy Zeek ICSNPP on segments with S7 controllers; build an allowlist of engineering hosts permitted to access safety-related blocks. Tune minimum event counts to suppress single-bit noise; integrate with asset inventory for PLC roles.
- **Visualization:** Table (source, destination, function, error), Bar chart (errors by source_h), Timeline (clusters of denied access).
- **CIM Models:** N/A

---

### UC-14.6.5 · Modbus Function Code Distribution Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Industry:** Manufacturing
- **Value:** Diagnostics and coil forcing are high-impact Modbus operations; a sudden shift in function-code mix can signal scanning, misuse, or a compromised HMI.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:modbus_detailed:json"` (`func`, `unit`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:modbus_detailed:json"
| eval fc=upper(trim(func))
| stats count by fc source_h destination_h
| eval risky=if(fc IN ("0x08","8","0x05","5","0x0F","15"),1,0)
| where risky=1 OR count>1000
| sort - count
```
- **Implementation:** Ingest ICSNPP `modbus_detailed` logs from Zeek sensors on Modbus TCP segments. Establish weekly baselines per RTU; alert when diagnostics (0x08) or force/write function codes spike versus baseline or appear from new masters.
- **Visualization:** Pie or bar chart (function code distribution), Table (risky FC by master), Timeline (spikes).
- **CIM Models:** N/A

---

### UC-14.6.6 · Modbus Register Value Change Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Change, Fault
- **Industry:** Manufacturing
- **Value:** Covert changes to holding registers can alter setpoints or interlocks; comparing matched request/response values highlights tampering distinct from normal operator writes.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:modbus_detailed:json"` (`func`, `address`, `unit`, `request_values`, `response_values`, `matched`, `network_direction`)
- **SPL:**
```spl
index=ot sourcetype="zeek:modbus_detailed:json" matched=true
| where func IN ("0x06","6","0x10","16")
| eval reg_key=destination_h."|".unit."|".address
| sort 0 reg_key _time
| streamstats window=2 global=f earliest(response_values) as earlier_resp latest(response_values) as later_resp by reg_key
| where isnotnull(earlier_resp) AND mvjoin(earlier_resp,",")!=mvjoin(later_resp,",")
| table _time source_h destination_h unit address func earlier_resp later_resp request_values
```
- **Implementation:** Deploy Zeek with ICSNPP-Modbus on taps near RTUs; ensure `request_values`/`response_values` are indexed. Focus on critical register ranges from asset documentation; schedule correlation with historian trends for validation.
- **Visualization:** Table (register_key, old vs new values), Timeline (changes), Line chart (change rate per hour).
- **CIM Models:** N/A

---

### UC-14.6.7 · Modbus Device Identification Enumeration (FC 43 / 0x2B)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Fault
- **Industry:** Manufacturing
- **Value:** Read Device Identification (FC 0x2B) is a common reconnaissance step; bursts from non-inventory hosts often precede targeted attacks or rogue integration attempts.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:modbus_detailed:json"` or `sourcetype="zeek:modbus_read_device_identification:json"` (`func`, `mei_type`, `object_id`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot (sourcetype="zeek:modbus_detailed:json" OR sourcetype="zeek:modbus_read_device_identification:json")
| where func IN ("0x2B","43","0x2b") OR mei_type="READ-DEVICE-IDENTIFICATION" OR isnotnull(object_id)
| stats count dc(destination_h) as targets by source_h
| where count>20 OR targets>5
| sort - count
```
- **Implementation:** Forward ICSNPP Modbus detailed and read-device-identification logs from OT VLAN taps. Allowlist asset-management scanners; alert on new sources or high fan-out to many slaves in a short window.
- **Visualization:** Bar chart (enumeration events by source), Table (source, target count), Map or table (distinct targets).
- **CIM Models:** N/A

---

### UC-14.6.8 · DNP3 Unsolicited Response Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault, Security
- **Industry:** Energy and Utilities
- **Value:** Unsolicited responses carry event-driven telemetry; abnormal volume or timing can indicate flooding, misconfiguration, or spoofed outstations affecting SCADA visibility.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:dnp3:json"` (Zeek `dnp3.log` / application function text, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:dnp3:json"
| where match(_raw,"UNSOLICITED") OR function="UNSOLICITED_RESPONSE"
| bin _time span=1m
| stats count by _time source_h destination_h
| eventstats median(count) as med by destination_h
| where count > med*3 AND count > 10
| table _time source_h destination_h count med
```
- **Implementation:** Deploy Zeek with DNP3 on serial-Ethernet gateways’ segments; verify `function` or raw tokens for unsolicited responses in your build. Baseline per-master/outstation pair; alert on bursts that exceed rolling median.
- **Visualization:** Timeline (unsolicited rate), Line chart (count vs median), Table (spikes).
- **CIM Models:** N/A

---

### UC-14.6.9 · DNP3 Control Relay Output Block (CROB) Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance, Change
- **Industry:** Energy and Utilities
- **Value:** CROB select/operate sequences directly actuate breakers and outputs; a full audit trail is required for NERC CIP-style reviews and post-incident forensics.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:dnp3:json"` (ICSNPP `dnp3_control.log`: `block_type`, `function_code`, `operation_type`, `index_number`, `trip_control_code`, `status_code`)
- **SPL:**
```spl
index=ot sourcetype="zeek:dnp3:json" block_type="Control_Relay_Output_Block"
| stats values(function_code) as phases values(operation_type) as ops values(trip_control_code) as trips latest(status_code) as last_status by _time source_h destination_h index_number uid
| table _time source_h destination_h index_number phases ops trips last_status
```
- **Implementation:** Enable ICSNPP-DNP3 control logging on Zeek sensors facing RTU/MTU paths. Ingest `dnp3_control` fields; map `index_number` to one-line diagrams. Require change correlation for OPERATE phases outside maintenance.
- **Visualization:** Table (full CROB audit), Timeline (SELECT vs OPERATE), Bar chart (operates by index_number).
- **CIM Models:** N/A

---

### UC-14.6.10 · DNP3 Cold/Warm Restart Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Security, Availability
- **Industry:** Energy and Utilities
- **Value:** Restart commands to outstations reset application context and can interrupt protection; unexpected restarts may follow malware or operator error.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:dnp3:json"` (`function`, `object_type`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:dnp3:json"
| where match(_raw,"(?i)COLD_RESTART|WARM_RESTART") OR match(function,"(?i)COLD_RESTART|WARM_RESTART") OR match(object_type,"(?i)COLD_RESTART|WARM_RESTART")
| stats earliest(_time) as evt_time values(function) as fn values(object_type) as ot by source_h destination_h
| table evt_time source_h destination_h fn ot
```
- **Implementation:** Capture DNP3 on links to critical RTUs via network tap; confirm field names (`function` vs `object_type`) against a sample capture. Alert any restart from non-master IPs or outside approved windows.
- **Visualization:** Timeline (restart events), Table (source, destination, function), Single value (restarts per day).
- **CIM Models:** N/A

---

### UC-14.6.11 · EtherNet/IP CIP Service Request Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Industry:** Manufacturing
- **Value:** Unusual CIP services (e.g., configuration writes) against controllers can precede firmware or logic manipulation; service baselines highlight drift from normal automation behavior.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:enip:json"` (`cip_service`, `cip_service_code`, `class_name`, `direction`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:enip:json" direction="Request"
| stats count by cip_service class_name source_h destination_h
| eventstats sum(count) as svc_total by destination_h
| eval pct=round(100*count/svc_total,3)
| where cip_service IN ("Set_Attribute_Single","Reset","Delete") OR pct<0.1
| sort destination_h - pct
| table destination_h cip_service class_name count pct source_h
```
- **Implementation:** Deploy ICSNPP-ENIP on Zeek at CIP/EtherNet/IP taps (ports 2222/44818 per policy). Build per-controller service profiles; alert on rare services or configuration-class access from non-engineering hosts.
- **Visualization:** Bar chart (CIP service mix), Table (rare services), Heatmap (service by source).
- **CIM Models:** N/A

---

### UC-14.6.12 · EtherNet/IP Unregistered Session Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Fault
- **Industry:** Manufacturing
- **Value:** EtherNet/IP sessions are normally established with explicit registration; traffic that skips expected session setup may indicate tooling errors, bypass attempts, or non-compliant devices on the plant floor.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:enip:json"` (`enip_command`, `session_handle`, `uid`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:enip:json"
| stats earliest(enip_command) as first_cmd values(enip_command) as cmds dc(enip_command) as cmd_variety by uid source_h destination_h
| where first_cmd!="Register_Session" AND (like(enip_command,"%SendRRData%") OR like(enip_command,"%Unit%") OR mvindex(cmds,0)!=first_cmd)
| table uid source_h destination_h first_cmd cmds
```
- **Implementation:** Ingest `enip.log` from Zeek on EtherNet/IP segments. Validate ordering with known-good PLC/HMI captures; tune exclusions for vendor-specific handshake quirks. Combine with asset roles so HMIs are not false-positive flagged incorrectly.
- **Visualization:** Table (sessions with anomalous first command), Timeline (connection uid), Bar chart (count by destination_h).
- **CIM Models:** N/A

---

### UC-14.6.13 · EtherNet/IP I/O Implicit Messaging Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault, Security
- **Industry:** Manufacturing
- **Value:** Implicit I/O carries real-time control data; sudden changes in payload size or timing can signal cable issues, configuration drift, or injection attempts affecting deterministic control.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:enip:json"` (ICSNPP `cip_io.log` merged or `sourcetype="zeek:cip_io:json"`: `connection_id`, `data_length`, `sequence_number`, `io_data`)
- **SPL:**
```spl
index=ot (sourcetype="zeek:cip_io:json" OR (sourcetype="zeek:enip:json" io_data=*))
| bin _time span=1s
| stats avg(data_length) as avg_len stdev(data_length) as sd_len count by _time connection_id source_h destination_h
| eventstats avg(avg_len) as baseline by connection_id
| where sd_len>0 OR abs(avg_len-baseline)>64
| table _time connection_id source_h destination_h avg_len sd_len baseline
```
- **Implementation:** Place Zeek on I/O scanner–adapter paths; prefer dedicated `cip_io` sourcetype when the TA splits logs. Learn normal `data_length` and sequence cadence per `connection_id`; alert on variance tied to control outages.
- **Visualization:** Line chart (data_length over time), Timeline (anomaly markers), Table (connection_id stats).
- **CIM Models:** N/A

---

### UC-14.6.14 · IEC 104 Interrogation Command Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance, Compliance
- **Industry:** Energy and Utilities
- **Value:** General interrogation and clock synchronization (types 100 and 103) can be abused for reconnaissance or time skew; auditing masters against expected scan behavior supports grid and plant operational integrity.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:iec104:json"` (`asdu_type`, `cot`, `stationinterrogation`, `cp56_*` clock fields, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:iec104:json"
| where asdu_type IN (100,103) OR stationinterrogation="T" OR match(_raw,"C_IC_NA_1|C_CS_NA_1")
| stats count by source_h destination_h asdu_type cot
| sort - count
```
- **Implementation:** Deploy Zeek IEC 60870-5-104 parser on 2404/tcp SCADA paths via tap. Map `asdu_type` 100 to general interrogation and 103 to clock sync per asset documentation; whitelist primary SCADA masters.
- **Visualization:** Timeline (interrogation and clock sync), Bar chart (count by asdu_type), Table (master, outstation, ASDU type).
- **CIM Models:** N/A

---

### UC-14.6.15 · IEC 104 Spontaneous Value Change Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault, Security
- **Industry:** Energy and Utilities
- **Value:** Monitoring spontaneous updates helps distinguish normal process swings from stale data or spoofed telemetry that could mask a physical fault.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:iec104:json"` (`cot`, `asdu_type`, `ioa`, `shortfloat`, `nva`, `sva`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:iec104:json" cot=3
| eval ioa_key=mvindex(ioa,0)
| bin _time span=5m
| stats latest(shortfloat) as sf by ioa_key destination_h _time
| sort 0 ioa_key destination_h _time
| streamstats window=2 global=f earliest(sf) as prev_sf latest(sf) as curr_sf by ioa_key destination_h
| where isnotnull(prev_sf) AND isnotnull(curr_sf) AND abs(curr_sf-prev_sf)>0.0001
| table _time destination_h ioa_key prev_sf curr_sf
```
- **Implementation:** Ingest IEC 104 JSON with vector fields expanded by TA; validate `cot` value for spontaneous (commonly 3). Tune magnitude thresholds per analog point class; integrate with EMS/Historian for cross-checks.
- **Visualization:** Line chart (value over time by IOA), Table (IOA, delta), Timeline (large deltas).
- **CIM Models:** N/A

---

### UC-14.6.16 · IEC 104 Clock Synchronization Deviation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Fault, Security
- **Industry:** Energy and Utilities
- **Value:** Time drift between master and outstation complicates event ordering and SOE correlation; detecting skew supports NERC-style evidence of synchronized operations.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:iec104:json"` (`asdu_type`, `cp56_minutes`, `cp56_hours`, `cp56_day`, `cp56_month`, `cp56_year`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:iec104:json" asdu_type=103
| eval wall=strptime(cp56_year."-".cp56_month."-".cp56_day." ".cp56_hours.":".cp56_minutes.":00","%Y-%m-%d %H:%M:%S")
| eval skew_sec=abs(_time-wall)
| where skew_sec>2 AND isnotnull(wall)
| stats max(skew_sec) as max_skew avg(skew_sec) as avg_skew by source_h destination_h
| where max_skew>5
| table source_h destination_h max_skew avg_skew
```
- **Implementation:** Capture C_CS_NA_1 clock sync ASDUs on OT taps; confirm `cp56_*` field population in your Zeek build. Alert when wire-time `_time` diverges from embedded CP56 time beyond policy (e.g., 2–5 seconds).
- **Visualization:** Single value (max skew), Line chart (skew over time), Table (endpoints, skew stats).
- **CIM Models:** N/A

---

### UC-14.6.17 · BACnet Object Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance, Change
- **Value:** Writes to analog outputs, schedules, or life-safety objects can change building or process environmental limits; auditing ReadProperty/WriteProperty supports both cyber and operational accountability.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:bacnet:json"` (`bacnet_property.log` via `pdu_service`, `object_type`, `property`, `value`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:bacnet:json"
| where match(pdu_service,"(?i)write.*property") OR pdu_service="Write_Property_Request"
| where object_type IN ("analog-output","binary-output","schedule","life-safety-point") OR match(property,"(?i)present.value|priority")
| stats count by source_h destination_h object_type instance_number property
| sort - count
```
- **Implementation:** Deploy ICSNPP-BACnet on UDP/47808 taps; use `bacnet_property` fields when the TA routes them into the same sourcetype or a dedicated property sourcetype. Define sensitive object lists per site; alert on writes from non-BMS servers.
- **Visualization:** Table (writes by object), Bar chart (writes by source_h), Timeline (write bursts).
- **CIM Models:** N/A

---

### UC-14.6.18 · BACnet Who-Is Broadcast Storm Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance, Fault
- **Value:** Excessive Who-Is/I-Am discovery floods MS/TP-to-IP bridges and can indicate misconfigured devices, loops, or active scanning that degrades BMS responsiveness.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:bacnet:json"` (`bacnet_discovery.log`: `pdu_service`, `device_id_number`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:bacnet:json" pdu_service IN ("who-is","i-am","who_is","i_am")
| bin _time span=1m
| stats count dc(source_h) as distinct_sources by _time destination_h
| where count>200 OR distinct_sources>20
| table _time destination_h count distinct_sources
```
- **Implementation:** Ingest discovery logs from Zeek on BACnet/IP VLANs. Set thresholds per campus; investigate sources with high Who-Is rates and verify router/broadcast management settings.
- **Visualization:** Area chart (Who-Is rate per minute), Table (spikes), Pie chart (share by pdu_service).
- **CIM Models:** N/A

---

### UC-14.6.19 · HART-IP Command 48 Additional Status Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance, Compliance
- **Value:** HART command 48 returns extended device status; tracking additional status fields helps catch sensor faults or configuration issues before they affect closed-loop control.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:hartip:json"` (`command`, `status`, `additional_status`, `source_h`, `destination_h`)
- **SPL:**
```spl
index=ot sourcetype="zeek:hartip:json"
| where command=48 OR command="0x30" OR match(_raw,"\"command\"\\s*:\\s*48")
| bin _time span=15m
| stats latest(status) as dev_status values(additional_status) as addl by destination_h _time
| where isnotnull(addl) OR (isnotnull(dev_status) AND dev_status!="0")
| table _time destination_h dev_status addl
```
- **Implementation:** Deploy ICSNPP HART-IP on segments with smart instruments; confirm JSON keys (`command`, `additional_status`) against a sample. Baseline healthy additional-status patterns; alert on new fault bits correlated with maintenance.
- **Visualization:** Timeline (command 48 events), Table (device, status, additional_status), Single value (devices reporting faults).
- **CIM Models:** N/A

---

### UC-14.6.20 · Unknown Protocol on OT VLAN Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance, Fault
- **Value:** Non-whitelisted protocols on ICS segments often indicate shadow IT, dual-homed misconfigurations, or tunneling that bypasses zone policies—each can bridge IT threats into OT.
- **App/TA:** TA for Zeek (Splunkbase 5466), Corelight App for Splunk (Splunkbase 3884)
- **Data Sources:** `index=ot` `sourcetype="zeek:conn:json"` (`service`, `proto`, `dest_port`, `vlan_id` or `vlan_name`)
- **SPL:**
```spl
index=ot sourcetype="zeek:conn:json" (like(vlan_name,"OT-%") OR cidrmatch("10.0.0.0/8",id.orig_h))
| eval svc=lower(service)
| where bytes_orig>0 AND bytes_resp>0
| where NOT (svc IN ("modbus","dnp3","bacnet","enip","s7comm","iec60870-5-104","hart-ip","dns","ntp") OR dest_port IN (502,20000,44818,47808,2222,2404,102,5094))
| stats sum(bytes_orig) as ob sum(bytes_resp) as rb dc(uid) as flows by "id.orig_h" "id.resp_h" dest_port proto service
| sort - flows
| head 200
```
- **Implementation:** Forward `conn.log` from Zeek on OT core taps with VLAN tags preserved. Maintain a Splunk lookup of approved services/ports per site; schedule nightly review of new triples (origin, destination, service). Tune DNS/NTP allowances.
- **Visualization:** Table (unexpected proto/port/service), Treemap (bytes by service), Timeline (first-seen connections).
- **CIM Models:** N/A

---

### 14.7 Litmus Edge Industrial IoT Gateway

**Primary App/TA:** Litmus Edge (built-in Splunk HEC connector), custom HEC inputs.

**Data Sources:** Litmus Edge gateway sends device data, health metrics, and alerts via HEC as JSON events. `sourcetype="litmus:edge"`, `sourcetype="litmus:health"`, `sourcetype="litmus:tag"`.

---

### UC-14.7.1 · Litmus Edge Gateway Connectivity Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Gateway offline events stop OT data from reaching Splunk; early detection reduces blind spots in plant visibility.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:health"` fields `gateway_id`, `status`, `online`
- **SPL:**
```spl
index=ot sourcetype="litmus:health"
| eval is_online=case(
    match(lower(status),"online|up|connected|running"), 1,
    match(lower(status),"offline|down|disconnected|stopped"), 0,
    online="true" OR online="1", 1,
    true(), 0)
| stats latest(is_online) as online_now, latest(_time) as last_health by gateway_id, site_id
| where online_now=0 OR isnull(online_now)
| eval minutes_since=round((now()-last_health)/60,1)
| table gateway_id, site_id, online_now, last_health, minutes_since
```
- **Implementation:** Enable the Litmus Edge Splunk HEC destination and send periodic health/heartbeat JSON. Ensure gateway_id and site_id are present. Alert if no healthy event for 2x the expected interval.
- **Visualization:** Single value (gateways offline), Table (gateway, site, last health), Status indicator (green/red per gateway).
- **CIM Models:** N/A

---

### UC-14.7.2 · PLC Tag Data Ingestion Validation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Industry:** Manufacturing
- **Value:** Missing or silent tag streams break dashboards, historians, and ML models; validating expected tags catches connector or network regressions before production impact.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:tag"` fields `gateway_id`, `tag_name`, `source_device`
- **SPL:**
```spl
index=ot sourcetype="litmus:tag"
| bin _time span=5m
| stats count as events, dc(tag_name) as distinct_tags by gateway_id, source_device, _time
| where events < 1 OR distinct_tags < 1
| table _time, gateway_id, source_device, events, distinct_tags
```
- **Implementation:** Normalize tag events so each sample carries gateway_id, tag_name, and source_device. Replace thresholds with per-device baselines from a lookup. For stricter checks, join to a required-tag lookup.
- **Visualization:** Line chart (events per minute by device), Table (devices below floor), Heatmap (device × time rate).
- **CIM Models:** N/A

---

### UC-14.7.3 · Edge-to-Splunk Data Pipeline Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** End-to-end latency distinguishes edge capture delays from Splunk indexing backlog; spikes indicate broker saturation, HEC backpressure, or clock skew.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:tag"` with `edge_timestamp` in JSON payload
- **SPL:**
```spl
index=ot sourcetype="litmus:tag"
| eval edge_sec=if(edge_timestamp>1e12, edge_timestamp/1000, edge_timestamp)
| where isnotnull(edge_timestamp) AND edge_sec>0
| eval latency_ms=abs(_time-edge_sec)*1000
| bin _time span=5m
| stats perc95(latency_ms) as p95_ms, avg(latency_ms) as avg_ms by gateway_id, _time
| where p95_ms > 5000
```
- **Implementation:** Configure Litmus to stamp each tag event with capture time in epoch. Keep NTP synchronized on Litmus and Splunk. Alert when p95 exceeds acceptable thresholds.
- **Visualization:** Line chart (p95/p99 latency by gateway), Area chart (latency distribution), Single value (fleet p95 latency).
- **CIM Models:** N/A

---

### UC-14.7.4 · Production Sensor Data Completeness Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Industry:** Manufacturing
- **Value:** Stale or missing sensor readings invalidate safety and quality analytics; completeness audits align telemetry coverage with regulatory expectations for critical measurements.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:tag"` fields `gateway_id`, `tag_name`, optional `quality`
- **SPL:**
```spl
index=ot sourcetype="litmus:tag"
| stats latest(_time) as last_seen by gateway_id, tag_name
| eval stale_sec=now()-last_seen
| where stale_sec > 300
| eval stale_minutes=round(stale_sec/60,1)
| table gateway_id, tag_name, last_seen, stale_minutes
| sort - stale_minutes
```
- **Implementation:** Set stale_threshold per tag class. Optionally join to a required-tag lookup and alert when any required tag is absent entirely.
- **Visualization:** Table (stale tags), Bar chart (count stale by gateway), Heatmap (tag × gateway freshness).
- **CIM Models:** N/A

---

### UC-14.7.5 · Litmus Edge Device Inventory Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Change
- **Value:** Unexpected devices or disappearing assets indicate misconfiguration or unauthorized connectivity; drift detection supports CMDB accuracy and OT security reviews.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:health"` OR `sourcetype="litmus:edge"` with `gateway_id`, `device_id`
- **SPL:**
```spl
index=ot (sourcetype="litmus:health" OR sourcetype="litmus:edge")
| eval device_key=coalesce(device_id, asset_id)
| where isnotnull(device_key)
| stats earliest(_time) as first_seen, latest(_time) as last_seen by gateway_id, device_key
| eval is_new=if(first_seen >= relative_time(now(),"-24h@h"), 1, 0)
| eval is_missing=if(last_seen < relative_time(now(),"-7d@d"), 1, 0)
| where is_new=1 OR is_missing=1
| eval drift_type=if(is_new=1, "new_device", "missing_device")
| table gateway_id, device_key, first_seen, last_seen, drift_type
```
- **Implementation:** Ensure device identifiers are stable in Litmus. Adjust the new/missing windows to match your change-management cadence. For baselines, use inputlookup and compare sets.
- **Visualization:** Table (new vs missing devices), Bar chart (drift events by gateway), Timeline (first seen for new devices).
- **CIM Models:** N/A

---

### UC-14.7.6 · Edge Data Transformation Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Transformation and normalization failures silently drop or corrupt OT fields; tracking error rates ties engineering changes to ingestion health.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:edge"` error fields or message text
- **SPL:**
```spl
index=ot sourcetype="litmus:edge"
| eval is_error=if(match(lower(_raw), "transform error|mapping error|parse error|conversion failed"), 1, 0)
| bin _time span=15m
| stats sum(is_error) as errors, count as total by gateway_id, _time
| eval error_rate_pct=round(100*errors/total,2)
| where errors>0
| table _time, gateway_id, errors, total, error_rate_pct
```
- **Implementation:** Route Litmus pipeline diagnostics to Splunk. Alert when error rate exceeds SLO (e.g., >1% over 15 minutes).
- **Visualization:** Line chart (error rate), Stacked bar (errors vs total), Table (top error pipelines), Single value (fleet error rate %).
- **CIM Models:** N/A

---

### UC-14.7.7 · Multi-Site Litmus Edge Fleet Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Aggregating gateway health by site highlights WAN issues, deployment drift, and capacity hotspots across plants without per-host manual checks.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** `index=ot` `sourcetype="litmus:health"` fields `site_id`, `gateway_id`, `status`
- **SPL:**
```spl
index=ot sourcetype="litmus:health"
| eval site=coalesce(site_id, plant_id, "unknown")
| eval is_ok=if(match(lower(status),"online|up|connected|running"), 1, 0)
| stats count as events, sum(is_ok) as ok_events, dc(gateway_id) as gateways by site
| eval health_pct=round(100*ok_events/events,1)
| table site, gateways, health_pct, ok_events, events
| sort health_pct
```
- **Implementation:** Require site_id in every Litmus health payload. Schedule a nightly report by site for executive visibility.
- **Visualization:** Bar chart (health % by site), Table (site ranking), Treemap (gateways × site).
- **CIM Models:** N/A

---

### UC-14.7.8 · Litmus Edge Connector Authentication Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** HEC token leakage, rotation mistakes, or clock skew cause auth failures that stop ingestion; monitoring auth errors accelerates rotation and prevents silent data gaps.
- **App/TA:** Litmus Edge (Splunk HEC connector)
- **Data Sources:** Splunk `_internal` HEC (`sourcetype="splunkd_http_input"`) for HTTP Event Collector rejections
- **SPL:**
```spl
index=_internal sourcetype="splunkd_http_input" (status=401 OR status=403)
| stats count as failures, values(source) as sources by host
| where failures > 0
| sort - failures
```
- **Implementation:** Ensure HEC is enabled only on the collector Litmus uses. Correlate spikes with token rotations and NTP drift. Alert on any 401/403 responses.
- **Visualization:** Line chart (auth failures over time), Table (hosts with failures), Single value (failures in last hour).
- **CIM Models:** N/A

---

### UC-14.7.9 · Centralized Model Retraining for Industrial Sensor ML (DSDL)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance, Fault
- **Value:** Edge-deployed ML models (autoencoder anomaly detection, XGBoost predictive maintenance, CNN visual inspection) degrade over time as equipment ages, processes change, and seasonal conditions shift. Centralized retraining in Splunk aggregates sensor data from all edge gateways, trains updated models via DSDL containers, and tracks model drift — ensuring edge predictions stay accurate without requiring data science expertise at each plant site.
- **App/TA:** Splunk Deep Learning Toolkit (DSDL), Splunk Edge Hub, Litmus Edge
- **Premium Apps:** None (DSDL is free)
- **Data Sources:** `index=ot sourcetype=edge_hub:metrics`, `index=ot sourcetype=litmus:edge`, model performance logs
- **SPL:**
```spl
index=ot sourcetype IN ("edge_hub:metrics","litmus:edge")
| bin _time span=1h
| stats avg(metric_value) as val stdev(metric_value) as val_std by _time, sensor_id, metric_name, site
| eval feature_vector=val.",".val_std
| fit AutoEncoderAE feature_vector into industrial_anomaly_model_v2
| summary industrial_anomaly_model_v2
| eval model_version="v2_".strftime(now(), "%Y%m%d")
| eval training_samples=count
| table model_version, training_samples, reconstruction_error_mean, reconstruction_error_std
```
- **Implementation:** Aggregate sensor data from all edge gateways (Edge Hub, Litmus Edge, Cisco EI) into a centralized OT index. Schedule weekly retraining jobs via DSDL containers running PyTorch or TensorFlow autoencoders. Track model performance metrics (reconstruction error distribution, anomaly detection rate, false positive rate) in a model registry KV store. Compare new model metrics against the production model before promotion. Deploy updated model weights back to edge gateways via the Edge Hub container management API or Litmus Edge's model deployment pipeline. Alert data engineering when model drift exceeds thresholds (reconstruction error mean shifting more than 2 standard deviations from the training baseline). Maintain model versioning and rollback capability.
- **Visualization:** Line chart (reconstruction error over model versions), Bar chart (anomaly detection rate by site), Table (model registry with version, accuracy, deployment status), Single value (model age in days).
- **CIM Models:** N/A

---

### 14.8 IoT & OT Trending

**Primary App/TA:** Splunk Add-on for Edge Hub (metrics), Industrial Protocols Add-ons (Modbus, OPC-UA), Splunk Operational Telemetry (OT/IoT) data model where enabled.

**Data Sources:** `index=ot` with `sourcetype=edge_hub:*`, `sourcetype=modbus:*`, `sourcetype=opcua:*`. Metrics indexes should expose device health, OEE, and anomaly scores via `metric_name` dimensions aligned to your Edge Hub pipelines.

---

### UC-14.8.1 · Device Fleet Online Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The share of devices reporting on schedule is a leading indicator of network, power, or gateway issues before production KPIs degrade; trending over 30 days shows whether fixes stick across sites.
- **App/TA:** Splunk Add-on for Edge Hub, optional Splunk OTel for OT gateways
- **Data Sources:** `index=ot` metrics: `sourcetype=edge_hub:metrics` with `metric_name` such as `device.online`, `device.heartbeat`, or `gateway.device_active`; dimensions `device_id`, `site_id`
- **SPL:**
```spl
| mstats avg(_value) WHERE index=ot metric_name IN ("device.online","device.heartbeat_ok") span=1d BY device_id
| eval online_flag=if('avg(_value)'>0.5,1,0)
| stats avg(online_flag) as fleet_online_rate by _time
| eval online_pct=round(100*fleet_online_rate,1)
| trendline sma7(online_pct) as online_trend
| eventstats median(online_pct) as med30
| eval vs_baseline=round(online_pct - med30,2)
```
- **Implementation:** Normalize `device.online` to 0/1 (or heartbeat) in the metrics pipeline. Multiply `fleet_online_rate` by a fleet `inputlookup` total if `mstats` only returns devices that reported—otherwise the average is the share of devices reporting at least one healthy sample per day. Align `metric_name` with Edge Hub transforms. If metrics are not available, use daily `dc(device_id)` from `edge_hub:*` heartbeats divided by the inventory lookup. Alert when `online_pct` drops more than 5 points below the 30-day median for three consecutive days.
- **Visualization:** Line chart (online % and trendline), Area chart (online versus offline device-days), Single value (current fleet availability).
- **CIM Models:** Operational Telemetry (Metrics) where tagged; otherwise N/A

---

### UC-14.8.2 · Sensor Data Quality Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Missing or stale readings break historians, dashboards, and ML features; daily trending exposes ingestion gaps early so teams can fix collectors, radios, or brokers before safety or quality thresholds are blind.
- **App/TA:** Edge Hub, Modbus/OPC-UA TAs
- **Data Sources:** `index=ot` `sourcetype IN ("edge_hub:metrics","edge_hub:events","modbus:readings","opcua:telemetry")`
- **SPL:**
```spl
index=ot sourcetype IN ("edge_hub:metrics","modbus:readings","opcua:telemetry") earliest=-30d@d
| eval bad=if(match(lower(coalesce(quality,data_quality)),"(?i)bad|invalid|stale") OR isnull(metric_value),1,0)
| timechart span=1d sum(bad) as bad_reads count as total_reads
| eval bad_pct=round(100*bad_reads/nullif(total_reads,0),2)
| trendline sma7(bad_pct) as quality_trend
| eventstats avg(bad_pct) as run_avg
| eval delta=round(bad_pct - run_avg,2)
```
- **Implementation:** Map your quality field (`good`, `192` OPC status, Modbus exception flags). If quality is not present, infer staleness with `streamstats` per `device_id` and `tag` using gaps between `_time` greater than `3×` the expected poll interval from a lookup. Dedupe by `device_id`+`tag` to avoid double counting. Tune thresholds per line speed—fast PLCs need tighter windows than environmental sensors.
- **Visualization:** Line chart (daily bad or stale % with trend), Stacked bar (bad readings by site), Table (worst devices by gap count).
- **CIM Models:** Operational Telemetry (Quality / Metrics) where mapped; otherwise N/A

---

### UC-14.8.3 · OEE Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Overall Equipment Effectiveness summarizes availability, performance, and quality; weekly or monthly trends show whether maintenance programs and changeovers are improving plant output without waiting for quarterly business reviews.
- **App/TA:** Edge Hub, MES or historian connectors (optional), OT metrics model
- **Data Sources:** `index=ot` `| mstats` on `metric_name="oee"` with `asset_id` or `line_id`; fallback `sourcetype=edge_hub:metrics` events carrying `oee` fields
- **SPL:**
```spl
| mstats avg(_value) WHERE index=ot metric_name="oee" span=1w BY asset_id
| rename "avg(_value)" as oee_avg
| eval oee_pct=round(oee_avg*100,2)
| stats avg(oee_pct) as fleet_oee by _time
| trendline sma4(fleet_oee) as oee_trend
| eval gap_to_target=round(85 - fleet_oee,2)
```
- **Implementation:** If OEE is not pre-calculated, derive it from availability × performance × quality metrics ingested separately (use `eval` in a scheduled search writing to a summary index). Align shifts and planned downtime using a `production_calendar` lookup to avoid penalizing scheduled stops. Compare assets to peers in the same technology line. Alert when 4-week rolling OEE drops more than 5 points below baseline.
- **Visualization:** Line chart (OEE % by line over weeks), Area chart (components if split metrics), Bullet chart (actual versus target OEE).
- **CIM Models:** Operational Telemetry (Production / OEE) where enabled; otherwise N/A

---

### UC-14.8.4 · Predictive Maintenance Alert Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** ML-driven anomaly counts should rise when equipment drifts but should fall after maintenance; tracking weekly volume validates model calibration and catches alert fatigue or broken scoring pipelines.
- **App/TA:** Splunk Machine Learning Toolkit (optional), Edge Hub anomaly outputs, DSDL or custom scoring jobs
- **Data Sources:** `index=ot` `sourcetype IN ("edge_hub:anomaly","edge_hub:alert","edge_hub:ml")` with `severity`, `model_id`, `asset_id`
- **SPL:**
```spl
index=ot sourcetype IN ("edge_hub:anomaly","edge_hub:alert") earliest=-90d@d
| timechart span=1w count as pred_alerts
| trendline sma6(pred_alerts) as alert_trend
| eventstats avg(pred_alerts) as baseline
| eval spike=if(pred_alerts > baseline*1.5,1,0)
```
- **Implementation:** Tag production ML alerts distinctly from threshold rules. Deduplicate repeated scores per asset per hour if the model emits bursts. Correlate spikes with maintenance windows—expected dips after work orders. If counts go to zero suddenly, validate the scoring container and HEC path. Feed counts back to data science for precision and recall reviews quarterly.
- **Visualization:** Line chart (weekly ML alert count with trend), Bar chart (alerts by asset), Single value (alerts versus 8-week average).
- **CIM Models:** Operational Telemetry (Maintenance / Security) as applicable; otherwise N/A

---


### 14.9 OT Network Security Monitoring (Cisco Cyber Vision / Nozomi Networks)

**Primary App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748), `Cisco Cyber Vision Splunk App` · `Nozomi Networks Universal Add-on` (Splunkbase 6905), `CCX Extensions for Nozomi Networks` (Splunkbase 6796).

**Data Sources:**
- **Cisco Cyber Vision:** API inputs (`cisco:cybervision:device`, `cisco:cybervision:event`, `cisco:cybervision:vulnerability`, `cisco:cybervision:flow`, `cisco:cybervision:activity`) and syslog (`cisco:cybervision:syslog` in CEF format).
- **Nozomi Networks:** API inputs (`nozomi:nn_asset`, `nozomi:node`, `nozomi:alert`, `nozomi:variable`, `nozomi:link`, `nozomi:link_events`, `nozomi:session`, `nozomi:health`, `nozomi:captured_urls`).

---

### UC-14.9.1 · OT Asset Discovery and Inventory Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Inventory
- **Value:** You cannot secure what you do not know exists. OT network security platforms (Cisco Cyber Vision, Nozomi Guardian) passively discover every device on your OT network via deep packet inspection of industrial protocols — PLCs, HMIs, drives, field devices — and builds an always-current inventory with vendor, model, firmware, serial number, and rack slot. This eliminates manual spreadsheets and provides the foundation for all other OT security use cases.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:device` · Nozomi: `sourcetype=nozomi:nn_asset`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:device"
| stats dc(device_id) as total_devices, dc(vendor) as vendors, values(vendor) as vendor_list by site_name
| eval device_summary=total_devices." devices from ".vendors." vendors"
| table site_name, total_devices, vendors, vendor_list, device_summary
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:nn_asset"
| stats dc(id) as total_devices, dc(vendor) as vendors, values(vendor) as vendor_list by zone
| eval device_summary=total_devices." devices from ".vendors." vendors"
| table zone, total_devices, vendors, vendor_list, device_summary
```
- **Implementation:** **Cyber Vision:** Configure Splunk Add-On with API token from Cyber Vision Center; add "Devices" input with polling interval (e.g. 3600s). **Nozomi:** Configure Universal Add-on with Guardian/Vantage API credentials; enable the `nn_asset` data input. Both platforms passively discover assets — use device data as the authoritative OT asset inventory for compliance and security programs.
- **Visualization:** Asset count single value; vendor breakdown pie chart; device table with firmware versions; site comparison bar chart.
- **CIM Models:** Asset Inventory

---

### UC-14.9.2 · New OT Device Detection Alert
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Any new device appearing on a baselined OT network is a potential threat — rogue devices, unauthorized laptops, or attacker implants. OT security platforms detect new components automatically and generate alerts. Immediate alerting enables rapid investigation before a threat can spread.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="ASSET-NEW")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="new_component"
| rex field=msg "New component detected on the network: IP (?<new_ip>[^,]+), MAC (?<new_mac>[^\s]+)"
| table _time, new_ip, new_mac, SCVSensorId, SCVComponentId
| sort -_time
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="ASSET-NEW"
| table _time, name, ip, mac_address, zone, risk
| sort -_time
```
- **Implementation:** **Cyber Vision:** Forward syslog to Splunk (CEF format via TCP/TLS); alert on `component_new` events. **Nozomi:** Enable `alert` data input; filter on `type_id="ASSET-NEW"`. Both platforms detect new devices automatically. Enrich with sensor/zone location to identify physical site. Cross-reference against approved asset list. Investigate unauthorized devices within SLA.
- **Visualization:** New device alert timeline; device location map by sensor; unauthorized device table.
- **CIM Models:** Network Traffic, Change

---

### UC-14.9.3 · OT Asset Vulnerability Detection and CVE Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** OT security platforms automatically match discovered OT assets against known CVEs, generating vulnerability alerts with CVE ID, CVSS score, and affected component. This eliminates manual vulnerability scanning in sensitive OT environments where active scanners can disrupt processes.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:vulnerability` · Nozomi: `sourcetype=nozomi:alert` (type_id contains "CVE")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:vulnerability"
| eval cvss_severity=case(cvss_score>=9.0, "Critical", cvss_score>=7.0, "High", cvss_score>=4.0, "Medium", cvss_score<4.0, "Low")
| stats count as vuln_count, max(cvss_score) as max_cvss, values(cve_id) as cve_list by device_name, device_ip, vendor, model
| where max_cvss >= 7.0
| sort -max_cvss
| table device_name, device_ip, vendor, model, vuln_count, max_cvss, cve_list
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="CVE-*"
| eval cvss_severity=case(cvss>=9.0, "Critical", cvss>=7.0, "High", cvss>=4.0, "Medium", cvss<4.0, "Low")
| stats count as vuln_count, max(cvss) as max_cvss, values(type_id) as cve_list by ip, name, zone
| where max_cvss >= 7.0
| sort -max_cvss
| table name, ip, zone, vuln_count, max_cvss, cve_list
```
- **Implementation:** **Cyber Vision:** Enable "Vulnerabilities" input; knowledge base updated weekly via Cisco Talos. **Nozomi:** Enable `alert` input; Guardian matches assets against NVD automatically. Both platforms provide passive vulnerability assessment without active scanning. Track vulnerability counts per asset. Prioritize remediation by CVSS severity and asset criticality.
- **Visualization:** Vulnerability count by severity pie chart; top 10 vulnerable assets table; CVE trend over time; CVSS distribution histogram.
- **CIM Models:** Vulnerabilities

---

### UC-14.9.4 · OT Asset Risk Score Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** OT security platforms calculate composite risk scores per device considering vulnerabilities, communication patterns, and security posture. Monitoring risk score changes over time shows whether your OT security posture is improving or degrading, and highlights which assets need immediate attention.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:device` · Nozomi: `sourcetype=nozomi:nn_asset`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:device" risk_score=*
| stats latest(risk_score) as current_risk, earliest(risk_score) as previous_risk by device_id, device_name, device_ip, site_name
| eval risk_change=current_risk - previous_risk
| eval risk_level=case(current_risk>=80, "Critical", current_risk>=60, "High", current_risk>=40, "Medium", current_risk<40, "Low")
| eval trend=case(risk_change>10, "Worsening", risk_change<-10, "Improving", 1=1, "Stable")
| where current_risk >= 60
| sort -current_risk
| table device_name, device_ip, site_name, current_risk, risk_level, risk_change, trend
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:nn_asset" risk=*
| stats latest(risk) as current_risk by id, name, ip, zone
| eval risk_level=case(current_risk>=8, "Critical", current_risk>=6, "High", current_risk>=4, "Medium", current_risk<4, "Low")
| where current_risk >= 6
| sort -current_risk
| table name, ip, zone, current_risk, risk_level
```
- **Implementation:** Both platforms calculate composite risk scores per device. Track score changes over time. Alert on assets crossing risk thresholds. Use risk scores to prioritize patching and segmentation efforts. Report on overall risk posture trends for management.
- **Visualization:** Risk distribution gauge; high-risk asset table; risk trend line per site; risk heatmap by asset group.
- **CIM Models:** Asset Inventory

---

### UC-14.9.5 · Baseline Deviation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** OT security platforms baseline normal network behavior — which devices talk to which, over what protocols, at what frequency. Deviations from baseline trigger alerts, detecting unauthorized communication changes, new data flows, or behavioral shifts that could indicate compromise or misconfiguration.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="ANOMALY")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype IN ("baseline_differences", "baseline_difference_nack")
| rex field=msg "Baseline '(?<baseline_name>[^']+)' got (?<diff_count>\d+) difference"
| eval severity_label=case(severity="3", "Critical", severity="2", "High", severity="1", "Medium", severity="0", "Low")
| stats count as total_deviations, sum(diff_count) as total_diffs, values(baseline_name) as baselines_affected by severity_label, _time
| sort -severity_label
| table _time, severity_label, baselines_affected, total_deviations, total_diffs
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="ANOMALY*"
| eval severity_label=case(risk>=8, "Critical", risk>=6, "High", risk>=4, "Medium", risk<4, "Low")
| stats count as total_deviations by severity_label, name, zone, _time
| sort -severity_label
| table _time, severity_label, name, zone, total_deviations
```
- **Implementation:** **Cyber Vision:** Create baselines for critical production zones; enable monitoring mode. **Nozomi:** Guardian automatically builds AI-powered behavioral baselines; anomaly alerts fire when deviations occur. Alert on any Critical or High severity deviations. Investigate and either acknowledge (legitimate change) or escalate (potential threat). Track unresolved deviations.
- **Visualization:** Deviation event timeline; baseline status dashboard; unresolved deviation count; severity distribution.
- **CIM Models:** Change, Intrusion Detection

---

### UC-14.9.6 · Snort IDS Threat Detection on OT Networks
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** OT security platforms include built-in IDS engines with threat intelligence updates to detect known threats — malware, C2 traffic, exploit attempts — crossing into OT networks. This provides signature-based threat detection without deploying separate IDS appliances in sensitive OT environments.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="SIGN")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="snort_event"
| rename SCVSnortEventMsg as signature, SCVSnortEventSid as sid, SCVSnortEventSrcAddr as src_ip, SCVSnortEventDstAddr as dest_ip, SCVSnortEventSrcPort as src_port, SCVSnortEventDstPort as dest_port
| eval severity_label=case(severity="3", "Critical", severity="2", "High", severity="1", "Medium", severity="0", "Low")
| stats count as hits, values(signature) as signatures, dc(dest_ip) as targets by src_ip, severity_label
| where severity_label IN ("Critical", "High")
| sort -hits
| table src_ip, severity_label, hits, targets, signatures
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="SIGN*"
| eval severity_label=case(risk>=8, "Critical", risk>=6, "High", risk>=4, "Medium", risk<4, "Low")
| stats count as hits, values(name) as signatures, dc(dst_ip) as targets by src_ip, severity_label
| where severity_label IN ("Critical", "High")
| sort -hits
| table src_ip, severity_label, hits, targets, signatures
```
- **Implementation:** **Cyber Vision:** Enable Snort IDS on sensors (4GB RAM required); configure Talos subscription for weekly rule updates. **Nozomi:** Guardian includes built-in threat intelligence with Nozomi Threat Intelligence updates. Both platforms provide signature-based IDS for OT. Forward events to Splunk. Correlate with IT security events in Splunk ES for unified threat detection. Alert SOC on Critical/High severity IDS hits targeting OT assets.
- **Visualization:** IDS alert timeline; top source IPs table; signature hit frequency chart; OT target heatmap.
- **CIM Models:** Intrusion Detection

---

### UC-14.9.7 · PLC Program Download/Upload Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Unauthorized PLC program changes can alter physical processes with safety implications. OT security platforms detect program download and upload events across industrial protocols (EtherNet/IP, S7, Modbus, Profinet) and generate Critical-severity alerts. Every program change must be verified against authorized change windows.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="PROTOCOL-ENGINEERING")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype IN ("flow_program_downloaded", "flow_program_uploaded", "flow_program_download_started")
| rename SCVFlowCmpaComponentId as source_id, SCVFlowCmpbComponentId as target_id
| eval action=case(SCVEventtype="flow_program_downloaded", "Program Downloaded", SCVEventtype="flow_program_uploaded", "Program Uploaded", SCVEventtype="flow_program_download_started", "Download Initiated")
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval outside_change_window=if((hour<6 OR hour>18) OR dow>5, "YES", "No")
| table _time, action, cmp-a, cmp-b, source_id, target_id, outside_change_window, SCVSensorId
| sort -_time
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id IN ("PROTOCOL-ENGINEERING-WRITE", "PROTOCOL-ENGINEERING-DOWNLOAD", "PROTOCOL-ENGINEERING-UPLOAD")
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval outside_change_window=if((hour<6 OR hour>18) OR dow>5, "YES", "No")
| table _time, name, src_ip, dst_ip, type_id, zone, outside_change_window
| sort -_time
```
- **Implementation:** Both platforms detect PLC program changes across industrial protocols. Alert on all program download/upload events. Cross-reference with change management system to validate authorized changes. Flag events outside approved maintenance windows. Require investigation and sign-off for every program change.
- **Visualization:** Program change timeline; authorized vs unauthorized change chart; target PLC table; change window compliance gauge.
- **CIM Models:** Change, Intrusion Detection

---

### UC-14.9.8 · Controller Firmware Activation Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Firmware activation on a controller changes the software running the physical process. Unauthorized firmware changes are a key indicator of advanced OT attacks (e.g., Stuxnet-style). OT security platforms detect firmware activation events across supported industrial protocols and generate Critical-severity alerts.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="PROTOCOL-ENGINEERING")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="firmware_activation"
| table _time, cmp-a, cmp-b, cmp-a-mac, cmp-b-mac, SCVSensorId, msg
| sort -_time
| join type=left cmp-b [| inputlookup ot_asset_inventory.csv | rename device_ip as cmp-b | fields cmp-b, device_name, zone, criticality]
| table _time, cmp-a, cmp-b, device_name, zone, criticality, msg
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="PROTOCOL-ENGINEERING-FIRMWARE*"
| table _time, name, src_ip, dst_ip, zone, risk
| sort -_time
```
- **Implementation:** Both platforms detect firmware activation events on controllers. Alert immediately — this is always high-priority. Cross-reference with approved change records. Investigate source and target. Validate firmware version matches approved versions.
- **Visualization:** Firmware activation event log; target controller details; change authorization correlation.
- **CIM Models:** Change

---

### UC-14.9.9 · Forced Variable Detection in OT Processes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Forcing a variable in a PLC overrides the normal program logic — the variable holds a fixed value regardless of what the control program calculates. While sometimes used legitimately during maintenance, forced variables left active in production can mask sensor readings and bypass safety logic. OT security platforms detect forced variable events with variable name and value.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:variable`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_forced_variable"
| rename SCVFlowForcedVariableVarName as var_name, SCVFlowForcedVariableValue as forced_value
| table _time, cmp-a, cmp-b, var_name, forced_value, SCVSensorId, msg
| sort -_time
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:variable" status="forced"
| table _time, node_id, variable_name, value, zone
| sort -_time
```
- **Implementation:** **Cyber Vision:** Detects `flow_forced_variable` events via syslog. **Nozomi:** Guardian tracks all process variables via the `nozomi:variable` sourcetype, including forced status. Alert on all forced variable events. Verify against active maintenance work orders. Track duration — any that remain active longer than the maintenance window must be investigated.
- **Visualization:** Forced variable event log; active forces table; force duration tracker; variable name word cloud.
- **CIM Models:** Change, Intrusion Detection

---

### UC-14.9.10 · Control Action Monitoring on Industrial Assets
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** OT security platforms track control action events when a control system modifies process variables — setpoint changes, valve commands, motor start/stop. Monitoring these actions detects unauthorized process manipulation and provides an audit trail for root cause analysis of production incidents.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:variable`, `sourcetype=nozomi:link_events`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_control_action"
| rename SCVFlowControlActionProcessName as process, SCVFlowControlActionVarName as variable, SCVFlowControlActionValue as new_value
| bin _time span=1h
| stats count as actions, dc(variable) as variables_changed, values(process) as processes by cmp-a, cmp-b, _time
| where actions > 50
| table _time, cmp-a, cmp-b, actions, variables_changed, processes
| sort -actions
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:variable"
| bin _time span=1h
| stats count as changes, dc(variable_name) as variables_changed by node_id, zone, _time
| where changes > 50
| table _time, node_id, zone, changes, variables_changed
| sort -changes
```
- **Implementation:** Both platforms track process variable changes. Baseline normal control action volume per source-target pair. Alert on spikes exceeding 2x baseline (mass parameter changes could indicate unauthorized batch modifications). Track who is making changes and which controllers are targets. Correlate with operator shift schedules.
- **Visualization:** Control action volume timeline; source-target relationship map; process change audit log.
- **CIM Models:** Change

---

### UC-14.9.11 · Controller Mode Change Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** OT security platforms detect when controllers are placed into online, offline, force, or run/stop modes — each a Critical-severity event. A controller taken offline stops controlling its physical process. An unauthorized mode change could halt production, disable safety systems, or prepare for a more destructive attack.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="PROTOCOL-ENGINEERING")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype IN ("flow_online", "flow_offline", "flow_force_mode", "flow_start_cpu", "flow_stop_cpu", "flow_restart_cpu", "flow_reset_process", "flow_init")
| eval action=case(
    SCVEventtype="flow_online", "Online",
    SCVEventtype="flow_offline", "Offline",
    SCVEventtype="flow_force_mode", "Force Mode",
    SCVEventtype="flow_start_cpu", "CPU Start",
    SCVEventtype="flow_stop_cpu", "CPU Stop",
    SCVEventtype="flow_restart_cpu", "CPU Restart",
    SCVEventtype="flow_reset_process", "Process Reset",
    SCVEventtype="flow_init", "Init")
| table _time, action, cmp-a, cmp-b, SCVFlowProtocolEventDetected, SCVSensorId, msg
| sort -_time
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id IN ("PROTOCOL-ENGINEERING-MODE*", "PROTOCOL-ENGINEERING-RUN*", "PROTOCOL-ENGINEERING-STOP*")
| table _time, name, src_ip, dst_ip, type_id, zone, risk
| sort -_time
```
- **Implementation:** Both platforms detect controller mode changes across industrial protocols. Alert immediately — CPU Stop and Offline events are highest priority as they halt physical processes. Cross-reference with scheduled maintenance. Track frequency of mode changes per controller. Investigate any mode change from unexpected source IPs.
- **Visualization:** Mode change timeline with color-coded severity; controller status dashboard; unauthorized source detection.
- **CIM Models:** Change, Intrusion Detection

---

### UC-14.9.12 · New Communication Flow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** In a stable OT environment, the set of communication flows between devices should be predictable. OT security platforms generate alerts when a previously unseen protocol flow appears between two components. New FTP, HTTP, or SSH flows in the control network may indicate lateral movement, data exfiltration, or unauthorized remote access tools.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:link_events`, `sourcetype=nozomi:link`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_new"
| rename SCVFlowCommunicationType as protocol
| bin _time span=1d
| stats count as new_flows, dc(protocol) as protocols, values(protocol) as protocol_list by _time
| eval concern=if(new_flows > 10, "High — investigate burst of new flows", "Normal")
| table _time, new_flows, protocols, protocol_list, concern
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:link_events" status="new"
| bin _time span=1d
| stats count as new_flows, dc(protocols) as protocol_count, values(protocols) as protocol_list by _time
| eval concern=if(new_flows > 10, "High — investigate burst of new flows", "Normal")
| table _time, new_flows, protocol_count, protocol_list, concern
```
- **Implementation:** Both platforms detect new communication flows after an initial learning period. Alert on new flows. Prioritize IT protocols appearing in OT zones (FTP, SSH, HTTP, RDP, SMB). Correlate with baseline deviations. Investigate source and destination to determine if the flow is legitimate.
- **Visualization:** New flow event timeline; protocol distribution chart; source-destination network graph.
- **CIM Models:** Network Traffic

---

### UC-14.9.13 · Protocol Exception Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Protocol exceptions (`illegal-function`, `invalid-data-address`, malformed packets) detected by OT DPI platforms indicate either misconfigured devices, faulty communication, or active exploitation attempts. An attacker probing Modbus function codes will trigger `illegal-function` exceptions. Repeated exceptions from a single source warrant investigation.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="PROTOCOL")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_exception"
| rename SCVExceptionLabel as exception_type
| stats count as exceptions, dc(exception_type) as exception_types, values(exception_type) as exception_list by cmp-a, cmp-b, SCVSensorId
| where exceptions > 5
| sort -exceptions
| table cmp-a, cmp-b, exceptions, exception_types, exception_list, SCVSensorId
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="PROTOCOL*"
| stats count as exceptions, dc(type_id) as exception_types, values(type_id) as exception_list by src_ip, dst_ip, zone
| where exceptions > 5
| sort -exceptions
| table src_ip, dst_ip, exceptions, exception_types, exception_list, zone
```
- **Implementation:** Both platforms detect protocol-level exceptions via DPI. Baseline normal exception rates per flow. Alert on sudden spikes (>5 exceptions from single source in short window). Differentiate between known interoperability issues and new attack patterns. Feed into SOC correlation rules.
- **Visualization:** Exception volume timeline; top exception source table; exception type distribution; attack pattern detection dashboard.
- **CIM Models:** Intrusion Detection

---

### UC-14.9.14 · OT Device Authentication Failure Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** OT security platforms detect login failure events including the number of failed authentication attempts and the protocol used. Brute-force login attempts against HMIs, engineering workstations, or web-enabled controllers indicate credential-based attacks that could lead to unauthorized process control.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="AUTH")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_login_failure"
| rename SCVFlowLoginFailureNumberOfAttempts as attempts, SCVFlowLoginFailureProtocol as protocol
| stats sum(attempts) as total_failures, count as failure_events, values(protocol) as protocols by cmp-a, cmp-b
| where total_failures >= 3
| sort -total_failures
| table cmp-a, cmp-b, total_failures, failure_events, protocols
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="AUTH*"
| stats count as total_failures by src_ip, dst_ip, zone
| where total_failures >= 3
| sort -total_failures
| table src_ip, dst_ip, total_failures, zone
```
- **Implementation:** Both platforms detect authentication failures on OT devices. Alert on repeated failures, especially against critical OT assets (PLCs, RTUs, SIS controllers). Correlate source IP with known engineering workstations. Unknown sources attempting authentication are high priority. Feed into Splunk ES notable events.
- **Visualization:** Failed auth timeline; top attack source table; target asset vulnerability assessment; brute force detection dashboard.
- **CIM Models:** Authentication

---

### UC-14.9.15 · Admin Connection Detection to ICS Assets
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** OT security platforms detect administrative connections to industrial components — engineering sessions to PLCs, configuration access to field devices. These events identify who is connecting to which controller, enabling detection of unauthorized engineering access that could modify process logic.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:session`, `sourcetype=nozomi:link`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="admin_connection"
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval outside_hours=if((hour<7 OR hour>18) OR dow>5, "After Hours", "Business Hours")
| stats count as connections by cmp-a, cmp-b, outside_hours
| where outside_hours="After Hours" OR connections > 10
| sort -connections
| table cmp-a, cmp-b, connections, outside_hours
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:session" session_type="engineering"
| eval hour=strftime(_time, "%H"), dow=strftime(_time, "%u")
| eval outside_hours=if((hour<7 OR hour>18) OR dow>5, "After Hours", "Business Hours")
| stats count as connections by src_ip, dst_ip, outside_hours, zone
| where outside_hours="After Hours" OR connections > 10
| sort -connections
| table src_ip, dst_ip, connections, outside_hours, zone
```
- **Implementation:** Both platforms detect engineering/admin connections to industrial assets. Baseline approved engineering workstation IPs. Alert on connections from unapproved sources or outside business hours. Track connection frequency per engineer. Correlate with change management tickets.
- **Visualization:** Admin connection timeline; source-destination network map; after-hours connection alerts; approved vs unapproved source comparison.
- **CIM Models:** Authentication, Network Traffic

---

### UC-14.9.16 · Port Scan Detection on OT Networks
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Port scanning is a reconnaissance technique used by attackers to map OT network topology and identify exploitable services. OT security platforms detect port scan events with scanner and target component identification. Port scans in OT networks are almost never legitimate and warrant immediate investigation.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="SCAN")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="port_scan"
| rename SCVPortScannerComponentId as scanner_id, SCVPortScanTargetComponentId as target_id, SCVPortScanDetailsProtocol as scan_protocol
| table _time, cmp-a, cmp-b, scan_protocol, scanner_id, target_id, SCVSensorId
| sort -_time
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="SCAN*"
| table _time, name, src_ip, dst_ip, zone, risk
| sort -_time
```
- **Implementation:** Both platforms detect port scanning in OT networks. Alert immediately on any port scan event. Identify scanner source — is it an authorized vulnerability scanner or unknown? Correlate with network baseline. Block scanning source at network boundary if unauthorized. Escalate to SOC and OT security team.
- **Visualization:** Port scan alert log; scanner source identification; target analysis; network map overlay.
- **CIM Models:** Intrusion Detection, Network Traffic

---

### UC-14.9.17 · Weak Encryption Detection in OT Communications
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Many OT protocols use weak or no encryption. OT security platforms identify flows using deprecated TLS versions, weak ciphers, or unencrypted protocols where encryption should be used. This supports IEC 62443 compliance and prioritizes protocol hardening efforts.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert` (type_id="PROTOCOL-CIPHER")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_weak_encryption"
| rename SCVFlowProtocolEventDetected as encryption_detail
| stats count as occurrences, dc(cmp-b) as affected_targets by cmp-a, encryption_detail
| sort -occurrences
| table cmp-a, encryption_detail, occurrences, affected_targets
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="PROTOCOL-CIPHER*"
| stats count as occurrences, dc(dst_ip) as affected_targets by src_ip, name, zone
| sort -occurrences
| table src_ip, name, occurrences, affected_targets, zone
```
- **Implementation:** Both platforms detect weak encryption in OT communications. Inventory all findings. Prioritize remediation by criticality of affected assets. Track progress toward encryption upgrade milestones. Report on IEC 62443 encryption compliance per zone.
- **Visualization:** Weak encryption finding table; affected asset count; compliance progress gauge; protocol breakdown.
- **CIM Models:** Network Traffic

---

### UC-14.9.18 · SMB Protocol Activity in OT Networks
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** SMB (Server Message Block) traffic in OT networks is frequently associated with ransomware propagation (WannaCry, NotPetya) and lateral movement. OT security platforms detect SMB protocol events. Any SMB activity in pure control network segments is suspicious and may indicate an active threat.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:session` (protocol="smb")
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="flow_smb"
| rename SCVFlowProtocolEventDetected as smb_detail
| stats count as smb_events, dc(cmp-b) as targets by cmp-a, smb_detail
| sort -smb_events
| table cmp-a, smb_detail, smb_events, targets
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:session" protocols="smb"
| stats count as smb_events, dc(dst_ip) as targets by src_ip, zone
| sort -smb_events
| table src_ip, smb_events, targets, zone
```
- **Implementation:** Both platforms detect SMB traffic via DPI. Map legitimate SMB usage (historian data transfer, Windows-based HMIs). Alert on SMB traffic to/from pure control devices (PLCs, RTUs, field devices) which should never use SMB. Correlate with IDS for known SMB exploit signatures. High priority for SOC investigation.
- **Visualization:** SMB activity timeline; source-target map; alert correlation with IDS; legitimate vs suspicious classification.
- **CIM Models:** Network Traffic, Intrusion Detection

---

### UC-14.9.19 · Network Redundancy and HA Failover Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** OT security platforms detect network redundancy failover events and router HA state changes across industrial protocols. Frequent failovers indicate network instability that could disrupt real-time control. Unexpected failovers may also indicate denial-of-service attacks or physical cable issues.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:link_events`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype IN ("flow_network_redundancy", "flow_router_ha")
| rename SCVFlowProtocolEventDetected as event_detail
| bin _time span=1h
| stats count as failover_events, values(event_detail) as details by cmp-a, cmp-b, _time
| where failover_events > 2
| table _time, cmp-a, cmp-b, failover_events, details
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:link_events" status IN ("up", "down", "flapping")
| bin _time span=1h
| stats count as failover_events by src_ip, dst_ip, status, zone, _time
| where failover_events > 2
| table _time, src_ip, dst_ip, status, failover_events, zone
```
- **Implementation:** Both platforms detect network redundancy and HA state changes. Baseline normal failover frequency (should be near zero in stable networks). Alert on any failover event. Multiple failovers in short succession (flapping) indicates a serious issue. Correlate with physical infrastructure monitoring.
- **Visualization:** Failover event timeline; network stability score; flapping device detection; HA state dashboard.
- **CIM Models:** Network Traffic, Change

---

### UC-14.9.20 · Cyber Vision Sensor Health and Resource Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** OT security sensors and appliances need monitoring themselves — high CPU, memory, or disk usage events fire when resources exceed thresholds. Degraded sensors may miss traffic, creating blind spots in OT visibility.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:health`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="sensor" SCVSensorAction="high ressources usage"
| rename SCVSensorCpu as cpu_pct, SCVSensorMemory as mem_pct, SCVSensorDisk as disk_pct, SCVSensorName as sensor_name, SCVSensorIp as sensor_ip, SCVSensorVersion as version
| table _time, sensor_name, sensor_ip, cpu_pct, mem_pct, disk_pct, version
| sort -cpu_pct
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:health"
| table _time, appliance_id, cpu_percent, memory_percent, disk_percent, version
| where cpu_percent > 80 OR memory_percent > 80 OR disk_percent > 80
| sort -cpu_percent
```
- **Implementation:** Both platforms expose sensor/appliance health metrics. **Cyber Vision:** Pre-filtered at 80% threshold via syslog. **Nozomi:** Guardian exposes health data via the `nozomi:health` sourcetype. Alert on high resource usage. Track trends per sensor. High CPU may indicate excessive traffic (DDoS, broadcast storm). Plan capacity upgrades or traffic optimization.
- **Visualization:** Sensor health dashboard; CPU/memory/disk gauges per sensor; resource trend lines; sensor fleet status map.
- **CIM Models:** Performance

---

### UC-14.9.21 · Cyber Vision Administration Audit Trail
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** All administrative actions in OT security platforms — user logins, configuration changes, sensor management, database operations — are logged. Maintaining an audit trail of who did what and when supports regulatory compliance (IEC 62443, NERC CIP) and insider threat detection.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:health`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" cat="Cisco Cyber Vision Administration" OR cat="Cisco Cyber Vision Operations"
| eval action=coalesce(SCVEventtype, "unknown")
| stats count as events by suser, action, cat
| sort -events
| table suser, action, cat, events
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:health" log_type="audit"
| stats count as events by user, action, appliance_id
| sort -events
| table user, action, appliance_id, events
```
- **Implementation:** Both platforms provide administrative audit trails. Forward all administration events to Splunk. Build compliance reports showing all administrative actions. Alert on high-severity admin events (system reboot, database restore, sensor deletion). Track user login patterns for anomaly detection.
- **Visualization:** Admin activity timeline; user action summary table; login pattern analysis; compliance audit report.
- **CIM Models:** Authentication, Change

---

### UC-14.9.22 · IEC 62443 Zone and Conduit Compliance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** IEC 62443 requires industrial networks to be segmented into security zones connected by controlled conduits. OT security platforms help control engineers define these zones and automatically detect cross-zone traffic that violates conduit policies. Monitoring zone compliance ensures segmentation remains effective over time.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:flow`, `sourcetype=cisco:cybervision:activity` · Nozomi: `sourcetype=nozomi:link`, `sourcetype=nozomi:session`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:flow"
| lookup ot_zone_mapping.csv device_ip OUTPUTNEW zone as src_zone
| lookup ot_zone_mapping.csv device_ip as dest_ip OUTPUTNEW zone as dest_zone
| where src_zone!=dest_zone
| stats count as cross_zone_flows, dc(protocol) as protocols, values(protocol) as protocol_list by src_zone, dest_zone
| lookup iec62443_conduit_policy.csv src_zone, dest_zone OUTPUTNEW allowed_protocols, conduit_status
| eval violation=if(conduit_status!="approved", "VIOLATION", "Compliant")
| where violation="VIOLATION"
| table src_zone, dest_zone, cross_zone_flows, protocol_list, conduit_status, violation
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:link"
| lookup iec62443_conduit_policy.csv src_zone, dst_zone OUTPUTNEW allowed_protocols, conduit_status
| where conduit_status!="approved"
| stats count as violations, values(protocols) as protocol_list by src_zone, dst_zone
| table src_zone, dst_zone, violations, protocol_list
```
- **Implementation:** Both platforms support zone-based monitoring aligned with IEC 62443. Export zone definitions to a lookup table. Define approved conduits with allowed protocols. Match actual cross-zone flows against policy. Alert on any unapproved cross-zone communication. Generate compliance reports for audits.
- **Visualization:** Zone topology map; conduit compliance matrix; violation count per zone pair; compliance trend over time.
- **CIM Models:** Network Traffic, Change

---

### UC-14.9.23 · OT Event Severity Distribution and Security Posture Dashboard
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** A high-level view of all OT security events by severity and category provides security posture at a glance. Trending event volumes over time shows whether security is improving (fewer Critical/High events) or degrading. Supports CISO reporting and board-level OT security metrics.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:event`, `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog"
| eval severity_label=case(severity="3", "Critical", severity="2", "High", severity="1", "Medium", severity="0", "Low")
| bin _time span=1d
| stats count as events by severity_label, cat, _time
| eventstats sum(events) as daily_total by _time
| eval pct_of_total=round(events*100/daily_total, 1)
| table _time, severity_label, cat, events, pct_of_total
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert"
| eval severity_label=case(risk>=8, "Critical", risk>=6, "High", risk>=4, "Medium", risk<4, "Low")
| bin _time span=1d
| stats count as events by severity_label, type_id, _time
| eventstats sum(events) as daily_total by _time
| eval pct_of_total=round(events*100/daily_total, 1)
| table _time, severity_label, type_id, events, pct_of_total
```
- **Implementation:** Both platforms provide event aggregation for security posture dashboards. Build executive dashboard showing daily event volumes, severity distribution, and trend lines. Track week-over-week and month-over-month changes. Alert on sudden spikes in Critical/High events.
- **Visualization:** Severity distribution pie chart; daily event volume stacked bar chart; trend line overlay; category breakdown table.
- **CIM Models:** N/A

---

### UC-14.9.24 · OT Protocol Usage Analysis and Inventory
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Inventory
- **Value:** OT security platforms identify all industrial protocols in use across the OT network — Modbus, EtherNet/IP, Profinet, S7, BACnet, DNP3, IEC 104, OPC-UA, and dozens more. Understanding protocol distribution helps prioritize security investments, plan protocol-specific IDS rules, and identify legacy protocols that need migration.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:activity` · Nozomi: `sourcetype=nozomi:link`, `sourcetype=nozomi:session`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:activity"
| stats dc(src_ip) as sources, dc(dest_ip) as destinations, sum(bytes) as total_bytes by protocol, site_name
| eval total_mb=round(total_bytes/1048576, 1)
| sort -sources
| table site_name, protocol, sources, destinations, total_mb
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:link"
| stats dc(src_ip) as sources, dc(dst_ip) as destinations, sum(bps_out) as total_bps by protocols, zone
| sort -sources
| table zone, protocols, sources, destinations, total_bps
```
- **Implementation:** Both platforms identify all industrial protocols in use via DPI. Analyze data to build protocol inventory per site/zone. Identify unexpected protocols (e.g., BACnet in a power substation, or Modbus in an enterprise zone). Compare protocol usage across sites for standardization. Feed into protocol-specific security policy development.
- **Visualization:** Protocol distribution pie chart per site; protocol comparison across sites; unexpected protocol alert table; protocol trend over time.
- **CIM Models:** Network Traffic

---

### UC-14.9.25 · Decode Failure and Malformed Packet Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** OT security platforms generate decode failure events when their DPI engine encounters packets it cannot properly parse — potentially indicating protocol fuzzing attacks, corrupted communications, or deliberately malformed exploit payloads targeting OT devices. Sustained decode failures from a single source may indicate active exploitation attempts.
- **App/TA:** `Cisco Cyber Vision Splunk Add-On` (Splunkbase 5748) · `Nozomi Networks Universal Add-on` (Splunkbase 6905)
- **Data Sources:** `sourcetype=cisco:cybervision:syslog` · Nozomi: `sourcetype=nozomi:alert`
- **SPL (Cisco Cyber Vision):**
```spl
index=cyber_vision sourcetype="cisco:cybervision:syslog" SCVEventtype="decode_failure"
| bin _time span=1h
| stats count as failures by SCVSensorId, _time
| where failures > 10
| table _time, SCVSensorId, failures
| sort -failures
```
- **SPL (Nozomi Networks):**
```spl
index=nozomi sourcetype="nozomi:alert" type_id="PROTOCOL-DECODE*"
| bin _time span=1h
| stats count as failures by zone, _time
| where failures > 10
| table _time, zone, failures
| sort -failures
```
- **Implementation:** Both platforms generate events when DPI encounters unparseable packets. Baseline normal decode failure rates per sensor/zone. Alert on sudden spikes exceeding 3x baseline, which may indicate a fuzzing or exploitation attempt. Correlate with IDS alerts from the same time window.
- **Visualization:** Decode failure timeline per sensor; spike detection; correlation with IDS events; sensor health overlay.
- **CIM Models:** Intrusion Detection

---
