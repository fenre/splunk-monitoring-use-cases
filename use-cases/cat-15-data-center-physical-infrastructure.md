## 15. Data Center Physical Infrastructure

### 15.1 Power & UPS

**Primary App/TA:** SNMP TA (UPS-MIB, PDU-MIB), vendor APIs (APC, Eaton, Vertiv).

---

### UC-15.1.1 · UPS Battery Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** UPS battery degradation is the single largest cause of unprotected power events. Proactive replacement prevents data center outages.
- **App/TA:** SNMP TA (UPS-MIB)
- **Data Sources:** SNMP UPS-MIB (battery status, charge, runtime, temperature, replace indicator)
- **SPL:**
```spl
index=power sourcetype="snmp:ups"
| where battery_replace_indicator="yes" OR charge_pct < 80 OR runtime_min < 15
| table ups_name, location, battery_status, charge_pct, runtime_min, battery_age_months
```
- **Implementation:** Poll UPS battery metrics via SNMP every 5 minutes. Alert on replace indicator, low charge, or low runtime. Track battery age and capacity trend over time to predict replacement needs.
- **Visualization:** Table (UPS battery status), Gauge (charge per UPS), Line chart (capacity trend), Single value (UPS needing replacement).
- **CIM Models:** N/A

---

### UC-15.1.2 · PDU Power per Rack
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Per-rack power monitoring prevents circuit overloads and enables efficient rack placement for new equipment.
- **App/TA:** SNMP TA (PDU-MIB), vendor API
- **Data Sources:** Smart PDU per-outlet and per-circuit metrics
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| eval pct_capacity=round(current_amps/rated_amps*100,1)
| where pct_capacity > 80
| table rack_id, pdu_name, circuit, current_amps, rated_amps, pct_capacity
```
- **Implementation:** Poll PDU metrics via SNMP. Track per-outlet and per-circuit power. Alert when any circuit exceeds 80% capacity. Report on rack power distribution for capacity planning. Track power trends per rack.
- **Visualization:** Heatmap (rack × power usage), Gauge (% capacity per circuit), Bar chart (power by rack), Table (overloaded circuits).
- **CIM Models:** N/A

---

### UC-15.1.3 · Power Redundancy Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Loss of A/B feed redundancy means a single power failure will cause an outage. Immediate awareness enables emergency response.
- **App/TA:** SNMP TA, PDU/UPS events
- **Data Sources:** PDU input status, UPS input voltage, transfer switch events
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| where input_status!="normal" OR input_voltage < 180
| table _time, pdu_name, rack_id, feed, input_status, input_voltage
```
- **Implementation:** Monitor PDU input status and UPS input voltage. Alert immediately on loss of any power feed. Track ATS (Automatic Transfer Switch) events. Maintain power topology documentation for impact analysis.
- **Visualization:** Status grid (rack × A/B feed status), Table (power events), Timeline (redundancy loss events), Single value (racks with full redundancy %).
- **CIM Models:** N/A

---

### UC-15.1.4 · Generator Test Results
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Generators are the last line of defense during extended outages. Failed tests mean they may not start when needed.
- **App/TA:** BMS integration, manual log input
- **Data Sources:** Generator controller logs, BMS events
- **SPL:**
```spl
index=power sourcetype="generator:test"
| stats latest(result) as last_result, latest(_time) as last_test by generator_id
| eval days_since_test=round((now()-last_test)/86400)
| where last_result!="pass" OR days_since_test > 30
```
- **Implementation:** Log generator test results (manual or automated). Track test frequency and outcomes. Alert on failed tests and missed test schedules. Monitor fuel levels. Report on generator readiness for management.
- **Visualization:** Table (generator test history), Single value (days since last test), Status indicator (pass/fail).
- **CIM Models:** N/A

---

### UC-15.1.5 · PUE Calculation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Power Usage Effectiveness is the primary data center efficiency metric. Trending drives energy optimization and sustainability goals.
- **App/TA:** Aggregate power metrics from PDU/UPS/BMS
- **Data Sources:** Total facility power, IT load power
- **SPL:**
```spl
index=power sourcetype="power:aggregate"
| timechart span=1h avg(total_facility_kw) as facility, avg(it_load_kw) as it_load
| eval pue=round(facility/it_load,2)
```
- **Implementation:** Aggregate total facility power and IT equipment power from PDU/UPS/BMS data. Calculate PUE hourly and daily. Track seasonal variation. Report monthly to operations and sustainability teams. Target PUE <1.5.
- **Visualization:** Gauge (current PUE), Line chart (PUE trend), Single value (monthly average PUE), Bar chart (PUE by month).
- **CIM Models:** N/A

---

### UC-15.1.6 · Circuit Breaker Trips
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Breaker trips cause immediate power loss to affected equipment. Detection enables rapid response and root cause investigation.
- **App/TA:** PDU/BMS event logs
- **Data Sources:** PDU events, BMS alerts, UPS transfer events
- **SPL:**
```spl
index=power sourcetype="pdu:events" OR sourcetype="bms:events"
| search "breaker" OR "overcurrent" OR "trip"
| table _time, device, location, event_type, circuit, message
```
- **Implementation:** Forward PDU and BMS events to Splunk. Alert immediately on breaker trips or overcurrent events. Track affected equipment from PDU-to-server mapping. Investigate root cause (overload, short circuit, equipment failure).
- **Visualization:** Timeline (breaker events), Table (trip details), Single value (trips this month).
- **CIM Models:** N/A

---

### 15.2 Cooling & Environmental

**Primary App/TA:** SNMP, BMS integration, environmental sensor inputs.

---

### UC-15.2.1 · Temperature Monitoring per Zone
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Data center temperature exceedances risk equipment damage and unplanned shutdowns. Per-zone monitoring localizes issues.
- **App/TA:** SNMP environmental sensors
- **Data Sources:** Environmental sensors (intake, exhaust, ambient temperature)
- **SPL:**
```spl
index=environment sourcetype="sensor:temperature"
| where temp_f > 80 OR temp_f < 64
| table _time, zone, rack, sensor_position, temp_f
| sort -temp_f
```
- **Implementation:** Deploy temperature sensors per ASHRAE recommendations (intake, exhaust, per-row). Poll via SNMP every minute. Alert on exceedance of ASHRAE A1 limits (64-80°F intake). Correlate with cooling unit status.
- **Visualization:** Heatmap (zone × temperature), Line chart (temperature trend per zone), Floor plan visualization, Single value (hottest zone).
- **CIM Models:** N/A

---

### UC-15.2.2 · Humidity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Low humidity causes ESD risk; high humidity causes condensation. Maintaining 40-60% RH protects equipment.
- **App/TA:** SNMP environmental sensors
- **Data Sources:** Humidity sensors
- **SPL:**
```spl
index=environment sourcetype="sensor:humidity"
| where humidity_pct > 60 OR humidity_pct < 40
| table _time, zone, humidity_pct
```
- **Implementation:** Deploy humidity sensors alongside temperature sensors. Alert on out-of-range humidity (below 40% or above 60% RH). Track dew point to prevent condensation. Correlate with HVAC system humidifier/dehumidifier operation.
- **Visualization:** Line chart (humidity trend), Gauge (current humidity per zone), Table (zones out of range).
- **CIM Models:** N/A

---

### UC-15.2.3 · CRAC/CRAH Unit Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Cooling unit failures can cause rapid temperature rise. Monitoring operational status enables immediate response and failover.
- **App/TA:** BMS/SNMP integration
- **Data Sources:** CRAC/CRAH unit SNMP metrics, BMS alarms
- **SPL:**
```spl
index=cooling sourcetype="bms:crac"
| where unit_status!="running" OR supply_temp_f > setpoint_f + 5 OR compressor_status!="normal"
| table _time, unit_name, unit_status, supply_temp_f, setpoint_f, compressor_status
```
- **Implementation:** Monitor cooling unit operational status, supply/return temperatures, and compressor health via SNMP/BMS. Alert on unit failure or degraded performance. Track runtime hours for maintenance scheduling.
- **Visualization:** Status grid (unit × operational status), Table (unit health), Line chart (supply/return temps), Gauge (cooling capacity %).
- **CIM Models:** N/A

---

### UC-15.2.4 · Hot Aisle Temperature Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Hot aisle trends indicate cooling efficiency and capacity margin. Rising trends signal approaching cooling limits.
- **App/TA:** Environmental sensors
- **Data Sources:** Hot aisle return air temperature sensors
- **SPL:**
```spl
index=environment sourcetype="sensor:temperature" position="hot_aisle"
| timechart span=1h avg(temp_f) as avg_temp by zone
| predict avg_temp as predicted future_timespan=7
```
- **Implementation:** Deploy sensors in hot aisle containment. Track return air temperatures. Compare hot aisle temps across zones to identify cooling imbalances. Use prediction to forecast capacity issues.
- **Visualization:** Line chart (hot aisle temps with prediction), Heatmap (zone × time), Bar chart (avg hot aisle by zone).
- **CIM Models:** N/A

---

### UC-15.2.5 · Water Leak Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Water in a data center causes immediate equipment damage and potential electrical hazards. Seconds matter in detection.
- **App/TA:** Leak detection sensor inputs
- **Data Sources:** Water leak detection system (rope sensors, spot detectors)
- **SPL:**
```spl
index=environment sourcetype="leak_detection"
| where leak_detected="true"
| table _time, zone, sensor_id, location_description
```
- **Implementation:** Deploy water leak detection sensors under raised floors, near CRAC units, and along pipe routes. Alert at critical priority on any detection. Integrate with building facilities team notification. Test sensors quarterly.
- **Visualization:** Single value (active leak alerts — target: 0), Floor plan (sensor locations with status), Timeline (leak events).
- **CIM Models:** N/A

---

### UC-15.2.6 · Cooling Capacity Planning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Trending cooling load vs capacity ensures adequate cooling for current and planned equipment deployments.
- **App/TA:** BMS metrics
- **Data Sources:** CRAC/CRAH cooling output, IT heat load calculations
- **SPL:**
```spl
index=cooling sourcetype="bms:cooling_capacity"
| timechart span=1d avg(cooling_output_kw) as output, avg(cooling_capacity_kw) as capacity
| eval utilization_pct=round(output/capacity*100,1)
```
- **Implementation:** Calculate cooling load from IT power consumption (1 watt IT ≈ 3.41 BTU/h heat). Compare against total cooling capacity. Track utilization percentage. Alert when approaching 80% capacity. Plan for seasonal variations.
- **Visualization:** Dual-axis chart (load vs capacity), Gauge (cooling utilization %), Line chart (utilization trend).
- **CIM Models:** N/A

---

### 15.3 Physical Security

**Primary App/TA:** Access control system integration, camera system syslog/API.

---

### UC-15.3.1 · Badge Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Complete badge access audit trail is required for compliance (SOC2, PCI-DSS) and supports security investigations.
- **App/TA:** Access control syslog/API
- **Data Sources:** Access control system events
- **SPL:**
```spl
index=physical sourcetype="access_control"
| table _time, badge_holder, badge_id, door, action, result
| sort -_time
```
- **Implementation:** Forward access control events to Splunk. Parse all badge events (granted, denied, door held, forced). Retain per compliance requirements. Enable search by person, door, or time for investigations.
- **Visualization:** Table (access log), Bar chart (access by door), Timeline (access events for person), Single value (total access today).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-15.3.2 · After-Hours Access Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Data center access outside business hours requires additional scrutiny. Alerts ensure authorized personnel are verified.
- **App/TA:** Access control system
- **Data Sources:** Access events with time-based rules
- **SPL:**
```spl
index=physical sourcetype="access_control" result="granted"
| eval hour=strftime(_time,"%H")
| where (hour < 6 OR hour > 22) AND NOT match(badge_holder, "NOC|Security|Facilities")
| table _time, badge_holder, door, badge_id
```
- **Implementation:** Define business hours per facility. Alert on access outside hours (excluding authorized roles like NOC, security). Require pre-authorization for after-hours access. Track after-hours access patterns.
- **Visualization:** Table (after-hours access events), Bar chart (after-hours by person), Heatmap (time × access volume).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-15.3.3 · Tailgating Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Tailgating bypasses access control, allowing unauthorized entry. Detection supports physical security integrity.
- **App/TA:** Access control system
- **Data Sources:** Access events (badge-in vs badge-out patterns)
- **SPL:**
```spl
index=physical sourcetype="access_control" door="DC_Main_Entry"
| transaction badge_id maxspan=10s
| where eventcount > 1 AND action="entry"
| table _time, badge_holder, badge_id, eventcount
```
- **Implementation:** Analyze badge-in/badge-out patterns. Detect multiple entries without corresponding exits (or vice versa). Alert on anti-passback violations. Correlate with camera footage for investigation. Report on tailgating trends.
- **Visualization:** Table (tailgating events), Bar chart (by door), Line chart (tailgating trend), Single value (incidents this week).
- **CIM Models:** N/A

---

### UC-15.3.4 · Camera System Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Offline cameras create security blind spots. Monitoring ensures continuous surveillance coverage.
- **App/TA:** NVR/VMS syslog or API
- **Data Sources:** Video management system logs (camera status, recording status)
- **SPL:**
```spl
index=physical sourcetype="vms:camera_status"
| where recording_status!="recording" OR connection_status!="connected"
| table camera_id, location, connection_status, recording_status, last_frame
```
- **Implementation:** Poll camera/NVR status via API or forward VMS events. Alert on camera offline, recording failure, or storage issues. Track camera uptime percentage. Report on coverage gaps.
- **Visualization:** Status grid (camera × status), Table (offline cameras), Single value (cameras recording %), Floor plan (camera locations with status).
- **CIM Models:** N/A

---

### UC-15.3.5 · Cabinet Door Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Unauthorized cabinet access could indicate tampering. Door sensors provide granular physical security for critical racks.
- **App/TA:** Cabinet lock sensor input
- **Data Sources:** Smart cabinet lock events
- **SPL:**
```spl
index=physical sourcetype="cabinet_lock"
| where action="opened" AND NOT authorized="true"
| table _time, rack_id, user, action, method
```
- **Implementation:** Deploy smart cabinet locks with event logging. Forward events to Splunk. Alert on unauthorized openings. Track door open duration. Correlate with badge access events for validation. Report on cabinet access frequency.
- **Visualization:** Table (cabinet access events), Timeline (open/close events), Bar chart (access by rack).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

