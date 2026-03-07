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

### UC-14.1.2 · UPS Battery Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** UPS battery failure during power loss causes complete outage. Proactive monitoring prevents unprotected power events.
- **App/TA:** SNMP TA (UPS-MIB)
- **Data Sources:** SNMP UPS-MIB (upsEstimatedMinutesRemaining, upsBatteryStatus, upsBatteryTemperature)
- **SPL:**
```spl
index=power sourcetype="snmp:ups"
| where battery_status!="normal" OR runtime_remaining_min < 30 OR battery_temp_c > 35
| table _time, ups_name, battery_status, charge_pct, runtime_remaining_min, battery_temp_c
```
- **Implementation:** Poll UPS via SNMP every 5 minutes. Alert on low charge (<80%), low runtime (<30 min), high temperature (>35°C), or abnormal status. Track battery health trend to predict replacement needs.
- **Visualization:** Gauge (charge %), Line chart (runtime trend), Table (UPS status), Single value (runtime remaining).
- **CIM Models:** N/A

---

### UC-14.1.3 · Power Consumption Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Power consumption trending supports capacity planning, cost management, and sustainability reporting. Anomalies indicate equipment issues.
- **App/TA:** SNMP TA, smart PDU API
- **Data Sources:** Smart PDU metrics (per-outlet, per-circuit power)
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| timechart span=1h avg(power_watts) as avg_power by rack_id
| predict avg_power as predicted future_timespan=30
```
- **Implementation:** Poll PDU power metrics via SNMP. Track per-rack and per-circuit consumption. Baseline normal patterns. Alert on unusual spikes (potential hardware issue) or drops (server failure). Use for PUE calculation.
- **Visualization:** Line chart (power per rack), Heatmap (rack × time power usage), Bar chart (top consumers), Stacked area (floor/room power).
- **CIM Models:** N/A

---

### UC-14.1.4 · Access Control Event Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Physical access logs correlate with logical access events for security investigation. Audit trail required for compliance.
- **App/TA:** Access control syslog, API input
- **Data Sources:** Access control system logs (badge events, door status)
- **SPL:**
```spl
index=physical sourcetype="access_control"
| stats count by badge_holder, door, action
| sort -count
```
- **Implementation:** Forward access control events via syslog or API. Parse badge holder, door, time, and action (granted, denied). Alert on after-hours access to sensitive areas. Correlate physical access with logical authentication events.
- **Visualization:** Table (access events), Bar chart (access by door), Timeline (access events for specific person), Geo/floor plan.
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

### 14.2 Industrial Control Systems (ICS/SCADA)

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
| stats count by src_ip, dest_ip, dest_port, app
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
| stats count by src_ip, dest_ip, dest_port
| sort -count
```
- **Implementation:** Monitor access to ICS networks from all sources. Alert on connections from non-whitelisted IPs. Track engineering workstation access sessions. Correlate with physical access to control rooms. Report for ICS cybersecurity compliance.
- **Visualization:** Table (access events), Timeline (unauthorized attempts), Bar chart (blocked connections by source).
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

### UC-14.3.8 · Data Center Humidity & Condensation Risk
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Prevents equipment failure by detecting dew point conditions before condensation forms on servers and network infrastructure.
- **App/TA:** Splunk Edge Hub (humidity + temperature sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` tag=humidity tag=temperature, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(Humidity), avg(Temperature) as temp by host
| eval dew_point=(243.04*(ln(Humidity/100)+((17.625*temp)/(243.04+temp))))/(17.625-ln(Humidity/100)-((17.625*temp)/(243.04+temp)))
| eval condensation_risk=case(temp<=dew_point, "CRITICAL", temp-dew_point<2, "HIGH", 1=1, "NORMAL")
| where condensation_risk!="NORMAL"
```
- **Implementation:** Deploy Edge Hub in raised floor or ceiling-mounted configuration with humidity sensor exposed to air circulation. Configure Advanced Settings → Sensor Polling interval to 30 seconds for real-time dew point calculation. Use local SQLite backlog to ensure no readings are lost during Splunk connectivity outages.
- **Visualization:** Gauge (dew point vs actual temp), time-series overlay, condensation risk heatmap.
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
| join host [| mstats avg(light_level) as lux by host, _time span=5m | where lux < 10]
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
| join host [index=edge-hub-logs camera_occupancy_count > 0 | stats count as people_detected by host, _time span=15m]
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
| join host [| mstats avg(external_pressure) as ext_press by host, _time span=1h]
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
| join opcua_tag [| rest /services/saved/data-model/indexes/OT_Industry_Process_Assets | fields asset_id, tag_name, expected_data_type]
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
| join meter_id [| rest /services/saved/data-model/indexes/energy_meter_cost_model | fields meter_id, cost_per_kwh]
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
| join program_id [| rest /services/saved/data-model/indexes/plc_program_baseline | fields program_id, last_known_timestamp, last_known_user]
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
| join location [| rest /services/data-model/indexes/edge_hub_fleet_baseline | fields location, target_firmware_version]
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
| join device_id [| rest /services/data-model/indexes/edge_hub_location_baseline | fields device_id, expected_latitude, expected_longitude, geofence_radius_meters]
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
| join location [| rest /services/data-model/indexes/approved_fleet_configs | fields location, approved_config_hash, approved_timestamp]
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
| join location [| rest /services/data-model/indexes/facility_capacity_limits | fields location, max_occupancy_safe, max_occupancy_emergency]
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
| join host [| mstats avg(temperature) as avg_temp by host | eval weather_context_available=1]
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
| join equipment_class [| rest /services/data-model/indexes/equipment_vibration_limits | fields equipment_class, vibration_max_safe_g, vibration_alarm_g]
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

All 50 new use cases (UC-14.3.8 through UC-14.3.57) are documented with:
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

