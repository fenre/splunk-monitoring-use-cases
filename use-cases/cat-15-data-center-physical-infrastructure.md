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

### UC-15.1.7 · APC PDU Outlet-Level Power Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Per-outlet current draw and on/off state on APC rack PDUs enables granular power attribution, remote outlet control verification, and identification of high-draw devices within a rack.
- **App/TA:** SNMP modular input
- **Data Sources:** APC PowerNet-MIB (rPDU2OutletSwitchedStatusCurrent, rPDU2OutletSwitchedStatusState)
- **SPL:**
```spl
index=power sourcetype="snmp:apc:pdu"
| eval outlet_state=case(rPDU2OutletSwitchedStatusState="1","on",rPDU2OutletSwitchedStatusState="2","off",1=1,"unknown")
| where rPDU2OutletSwitchedStatusCurrent > 10 OR outlet_state="off"
| table _time, pdu_name, outlet_id, outlet_label, rPDU2OutletSwitchedStatusCurrent as current_amps, outlet_state
| sort -current_amps
```
- **Implementation:** Configure SNMP modular input to poll APC PowerNet-MIB. Map rPDU2OutletSwitchedStatusCurrent (0.1A resolution) and rPDU2OutletSwitchedStatusState per outlet. Poll every 5 minutes. Alert on outlets exceeding threshold (e.g., 10A) or unexpected off-state. Correlate outlet labels with DCIM for device mapping.
- **Visualization:** Table (outlet current by PDU), Bar chart (top outlets by draw), Status grid (outlet on/off state), Line chart (outlet current trend).
- **CIM Models:** N/A

---

### UC-15.1.8 · Generator Runtime and Fuel Level
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Diesel generator monitoring for extended outages; fuel level and run hours ensure generators can sustain operations during prolonged utility failures.
- **App/TA:** Custom (generator controller SNMP/Modbus, BMS integration)
- **Data Sources:** Generator controller telemetry (fuel_level_pct, run_hours, engine_status)
- **SPL:**
```spl
index=power sourcetype="generator:telemetry"
| stats latest(fuel_level_pct) as fuel_pct, latest(run_hours) as run_hrs, latest(engine_status) as status by generator_id
| where fuel_pct < 30 OR status!="standby" AND status!="running"
| table generator_id, fuel_pct, run_hrs, status
```
- **Implementation:** Integrate generator controller via SNMP or Modbus. Ingest fuel_level_pct, run_hours, engine_status (standby, running, fault). Poll every 5–15 minutes. Alert on low fuel (<30%), engine fault, or unexpected runtime. Correlate with utility outage events. Report fuel consumption rate during run events.
- **Visualization:** Gauge (fuel level per generator), Table (generator status), Line chart (fuel level trend), Single value (lowest fuel %).
- **CIM Models:** N/A

---

### UC-15.1.9 · Rack Power Density Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Watts per rack unit over time for capacity planning; identifies hot spots and supports safe equipment placement decisions.
- **App/TA:** SNMP modular input, DCIM integration
- **Data Sources:** PDU per-rack power readings, DCIM inventory (rack height, location)
- **SPL:**
```spl
index=power sourcetype="pdu:rack_power"
| lookup rack_inventory rack_id OUTPUT rack_u_height
| eval watts_per_u=round(power_watts/rack_u_height,1)
| timechart span=1d avg(watts_per_u) as avg_watts_per_u by rack_id
| predict avg_watts_per_u as predicted future_timespan=30
```
- **Implementation:** Aggregate PDU power per rack. Join with DCIM lookup for rack U height. Calculate watts/U. Poll daily or hourly. Alert when watts/U exceeds design threshold (e.g., 500W/U). Use prediction for capacity planning. Report top-density racks and trend by zone.
- **Visualization:** Line chart (watts/U trend by rack), Heatmap (rack × density), Bar chart (top racks by density), Table (capacity forecast).
- **CIM Models:** N/A


---

### UC-15.1.10 · UPS Battery Runtime Remaining
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Minutes of runtime remaining under present load is the actionable metric for graceful shutdown sequencing during outages.
- **App/TA:** SNMP TA (UPS-MIB upsEstimatedMinutesRemaining)
- **Data Sources:** `sourcetype="snmp:ups"` (runtime_min, load_pct)
- **SPL:**
```spl
index=power sourcetype="snmp:ups"
| where runtime_min < 10 OR (runtime_min < 20 AND load_pct > 70)
| table _time, ups_name, location, runtime_min, load_pct, battery_status
```
- **Implementation:** Poll `upsEstimatedMinutesRemaining` every 1–5 minutes. Alert when runtime drops below site policy (e.g., <10 min). Correlate with concurrent generator tests.
- **Visualization:** Gauge (runtime min per UPS), Line chart (runtime trend), Single value (minimum runtime in site).
- **CIM Models:** N/A

---

### UC-15.1.11 · PDU Outlet-Level Power Draw
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Per-outlet amps identify rogue devices and balance load across strips before branch trips.
- **App/TA:** SNMP TA (PDU-MIB, ENCLOSURE-MIB)
- **Data Sources:** `sourcetype="snmp:pdu:outlet"` (outlet_index, current_amps)
- **SPL:**
```spl
index=power sourcetype="snmp:pdu:outlet"
| eval pct_outlet=if(rated_amps_outlet>0, round(current_amps/rated_amps_outlet*100,1), null())
| where pct_outlet > 85 OR current_amps > 12
| table pdu_id, outlet_id, current_amps, rated_amps_outlet, pct_outlet
| sort -current_amps
```
- **Implementation:** Poll outlet bank tables on smart PDUs. Map outlet labels from DCIM. Alert on high draw or imbalance vs peer outlets on same strip.
- **Visualization:** Bar chart (outlet draw), Heatmap (PDU × outlet), Table (top consumers).
- **CIM Models:** N/A

---

### UC-15.1.12 · Generator Fuel Level Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tank level and burn rate determine how long the site can run off-grid; critical for extended utility failures.
- **App/TA:** BMS, generator controller Modbus/SNMP
- **Data Sources:** `sourcetype="generator:telemetry"` (fuel_level_pct, fuel_gallons)
- **SPL:**
```spl
index=power sourcetype="generator:telemetry"
| where fuel_level_pct < 25
| table generator_id, fuel_level_pct, fuel_gallons, engine_status
```
- **Implementation:** Poll fuel level and totalizer. Compute burn rate during engine run. Alert on low level and abnormal consumption (leak suspicion).
- **Visualization:** Gauge (fuel %), Line chart (level vs time), Table (hours of fuel at current load).
- **CIM Models:** N/A

---

### UC-15.1.13 · Transfer Switch Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** ATS transitions between utility and generator must be logged for root cause of brief outages and equipment stress.
- **App/TA:** ATS SNMP/BMS, relay contacts
- **Data Sources:** `sourcetype="ats:events"` (source, event, duration_ms)
- **SPL:**
```spl
index=power sourcetype="ats:events"
| where event IN ("transfer_to_gen","retransfer_to_utility","test") OR duration_ms > 500
| table _time, ats_id, event, source_side, duration_ms
| sort -_time
```
- **Implementation:** Ingest dry-contact or SNMP traps on transfer. Alert on failed transfer, oscillation, or long transfer time. Correlate with utility feeder events.
- **Visualization:** Timeline (transfer events), Table (last transfer by ATS), Single value (transfers in 24h).
- **CIM Models:** N/A

---

### UC-15.1.14 · Power Factor Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low PF increases utility demand charges and heats conductors; correction banks need verification.
- **App/TA:** Power meter SNMP (PQ meters)
- **Data Sources:** `sourcetype="power_meter:pq"` (pf, thd, kw, kvar)
- **SPL:**
```spl
index=power sourcetype="power_meter:pq"
| where pf < 0.92 OR thd_pct > 8
| timechart span=15m avg(pf) as avg_pf by feed_id
```
- **Implementation:** Poll main switchboard meters. Alert when PF drops below utility contract threshold. Correlate with capacitor bank status if monitored.
- **Visualization:** Line chart (PF trend), Gauge (current PF), Table (feeds out of spec).
- **CIM Models:** N/A

---

### UC-15.1.15 · PUE Efficiency Tracking vs Target
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Comparing live PUE to annual design target drives mechanical optimization and executive reporting.
- **App/TA:** BMS + IT load meters
- **Data Sources:** `sourcetype="power:aggregate"` (facility_kw, it_load_kw, pue_design)
- **SPL:**
```spl
index=power sourcetype="power:aggregate"
| eval pue=round(total_facility_kw/it_load_kw,2)
| where pue > pue_design * 1.1 OR pue > 1.6
| timechart span=1h avg(pue) as live_pue
```
- **Implementation:** Ingest design PUE from DCIM lookup. Alert when rolling PUE exceeds target band. Seasonally adjust expected range.
- **Visualization:** Line chart (PUE vs target band), Gauge (delta from design), Single value (30-day avg PUE).
- **CIM Models:** N/A

---

### UC-15.1.16 · Breaker Panel Load Balancing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Uneven loading across panel phases causes neutral current and premature breaker wear.
- **App/TA:** Panelboard metering, PQ analyzer
- **Data Sources:** `sourcetype="panel:phase"` (phase_a_amps, phase_b_amps, phase_c_amps)
- **SPL:**
```spl
index=power sourcetype="panel:phase"
| eval max_p=max(phase_a_amps, phase_b_amps, phase_c_amps), min_p=min(phase_a_amps, phase_b_amps, phase_c_amps), imbalance=max_p-min_p
| where imbalance > rated_amps*0.15
| table panel_id, phase_a_amps, phase_b_amps, phase_c_amps, imbalance
```
- **Implementation:** Define max phase imbalance (e.g., 15% of frame). Alert and schedule load moves. Common with single-phase dense racks.
- **Visualization:** Bar chart (phase amps), Table (panels with imbalance), Heatmap (panel × phase).
- **CIM Models:** N/A

---

### UC-15.1.17 · UPS Self-Test Failure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed self-tests indicate battery or inverter faults before a real outage.
- **App/TA:** UPS SNMP (upsTestResultsSummary)
- **Data Sources:** `sourcetype="snmp:ups:selftest"`
- **SPL:**
```spl
index=power sourcetype="snmp:ups:selftest"
| where test_result!="passed" OR upsTestResultsSummary!="donePass"
| table _time, ups_name, test_type, test_result, upsTestResultsSummary
```
- **Implementation:** Ingest results from scheduled and manual tests. Alert on any failure. Force battery replacement workflow per vendor guidance.
- **Visualization:** Table (failed tests), Timeline (self-test history), Single value (UPS with last fail).
- **CIM Models:** N/A

---

### UC-15.1.18 · Generator Start Failure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed cranks or inability to reach rated speed leave the site on battery-only until resolved.
- **App/TA:** Generator controller
- **Data Sources:** `sourcetype="generator:events"` (start_result, crank_count, fault_code)
- **SPL:**
```spl
index=power sourcetype="generator:events"
| search start_result IN ("fail","abort") OR crank_count > 3
| table _time, generator_id, start_result, crank_count, fault_code
| sort -_time
```
- **Implementation:** Alert immediately on failed start during tests or utility loss. Track battery, starter, and fuel subsystem codes.
- **Visualization:** Table (start failures), Single value (failed starts 90d), Timeline (events).
- **CIM Models:** N/A

---

### UC-15.1.19 · Power Redundancy Compliance (N+1)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Proves both A/B feeds and redundant UPS paths are energized and within load limits for loss-of-one scenarios.
- **App/TA:** PDU/ATS telemetry, DCIM rules
- **Data Sources:** `sourcetype="power:redundancy"` (feed_a_ok, feed_b_ok, load_on_loss_of_one_pct)
- **SPL:**
```spl
index=power sourcetype="power:redundancy"
| where feed_a_ok=0 OR feed_b_ok=0 OR load_on_loss_of_one_pct > 100
| table _time, pdu_id, feed_a_ok, feed_b_ok, load_on_loss_of_one_pct
```
- **Implementation:** Model expected load after single failure from DCIM. Alert when any feed is down or modeled headroom <0%. Pair with physical walk-through audits.
- **Visualization:** Status grid (feed × PDU), Gauge (headroom %), Table (non-compliant PDUs).
- **CIM Models:** N/A

---

### UC-15.1.20 · PDU Branch Circuit Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Branch breakers trip before mains; per-branch monitoring catches overload before rack outage.
- **App/TA:** Smart PDU branch monitoring
- **Data Sources:** `sourcetype="snmp:pdu:branch"` (branch_id, branch_amps, branch_rated_amps)
- **SPL:**
```spl
index=power sourcetype="snmp:pdu:branch"
| eval pct=round(branch_amps/branch_rated_amps*100,1)
| where pct > 80 OR branch_status="alarm"
| table pdu_id, branch_id, branch_amps, branch_rated_amps, pct
| sort -pct
```
- **Implementation:** Map branches to rack groups. Alert at 80% sustained. Correlate with planned equipment adds.
- **Visualization:** Bar chart (branch load %), Table (branches at risk).
- **CIM Models:** N/A

---

### UC-15.1.21 · Electrical Panel Phase Balancing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Panel-level phase balance differs from rack PDU balance; both matter for neutral harmonics and breaker life.
- **App/TA:** Main distribution panel meters
- **Data Sources:** `sourcetype="panel:phase"` (main_l1_a, main_l2_a, main_l3_a)
- **SPL:**
```spl
index=power sourcetype="panel:phase" panel_type="main"
| eval avg_a=(main_l1_a+main_l2_a+main_l3_a)/3
| eval dev=max(abs(main_l1_a-avg_a), abs(main_l2_a-avg_a), abs(main_l3_a-avg_a))
| where dev > avg_a*0.2
| table panel_id, main_l1_a, main_l2_a, main_l3_a, dev
```
- **Implementation:** Alert when any phase deviates >20% from mean. Schedule rebalancing with facilities during maintenance.
- **Visualization:** Line chart (phase currents), Gauge (max deviation), Table (panels out of balance).
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

### UC-15.2.7 · APC InRow / CRAC Unit Temperature Differential
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Inlet/outlet delta-T indicating cooling effectiveness; low delta-T suggests bypass airflow or undersized cooling; high delta-T indicates effective heat removal.
- **App/TA:** SNMP modular input
- **Data Sources:** APC AirIR-MIB (airIRSupplyAirTemperature, airIRReturnAirTemperature)
- **SPL:**
```spl
index=cooling sourcetype="snmp:apc:inrow"
| eval delta_t=airIRReturnAirTemperature - airIRSupplyAirTemperature
| where delta_t < 5 OR delta_t > 25
| table _time, unit_name, zone, airIRSupplyAirTemperature as supply_f, airIRReturnAirTemperature as return_f, delta_t
| sort -delta_t
```
- **Implementation:** Poll APC AirIR-MIB for airIRSupplyAirTemperature and airIRReturnAirTemperature. Calculate delta-T (return minus supply). Typical effective range 10–20°F. Alert on delta-T <5°F (ineffective cooling) or >25°F (possible airflow restriction). Poll every 5 minutes. Correlate with unit runtime and fan status.
- **Visualization:** Line chart (delta-T trend per unit), Table (units outside range), Gauge (current delta-T), Heatmap (zone × delta-T).
- **CIM Models:** N/A


---

### UC-15.2.8 · CRAC Unit Failure and Alarm State
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Explicit CRAC fault/alarm bits catch compressor and fan failures not visible in temperature alone.
- **App/TA:** BMS, SNMP (Liebert/Vertiv MIBs)
- **Data Sources:** `sourcetype="bms:crac"` (unit_alarm, compressor_fault, fan_fault)
- **SPL:**
```spl
index=cooling sourcetype="bms:crac"
| where unit_alarm=1 OR compressor_fault=1 OR fan_fault=1 OR unit_status="fault"
| table _time, unit_name, unit_alarm, compressor_fault, fan_fault, alarm_text
```
- **Implementation:** Map vendor alarm codes to plain text. Page on any fault. Track MTTR for CRAC repairs.
- **Visualization:** Status grid (unit × fault class), Timeline (alarms), Single value (units in fault).
- **CIM Models:** N/A

---

### UC-15.2.9 · Hot/Cold Aisle Temperature Delta
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low ΔT across containment indicates bypass airflow or insufficient airflow; high ΔT may signal restricted return.
- **App/TA:** Environmental sensors
- **Data Sources:** `sourcetype="sensor:temperature"` position IN ("hot_aisle","cold_aisle")
- **SPL:**
```spl
index=environment sourcetype="sensor:temperature" row_id=*
| stats avg(eval(if(position="cold_aisle",temp_c,null()))) as cold_c, avg(eval(if(position="hot_aisle",temp_c,null()))) as hot_c by row_id, _time span=5m
| eval delta_t=hot_c-cold_c
| where delta_t < 8 OR delta_t > 22
| table row_id, cold_c, hot_c, delta_t
```
- **Implementation:** Pair sensors per row. Baseline expected ΔT for your containment design. Alert outside band.
- **Visualization:** Line chart (ΔT by row), Heatmap (row × time), Gauge (current ΔT).
- **CIM Models:** N/A

---

### UC-15.2.10 · Humidity Threshold Exceedance (ASHRAE)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Stricter alerting for short excursions supports tape media and corrosion-sensitive gear beyond static high/low limits.
- **App/TA:** SNMP sensors
- **Data Sources:** `sourcetype="sensor:humidity"`
- **SPL:**
```spl
index=environment sourcetype="sensor:humidity"
| where humidity_pct > 60 OR humidity_pct < 40
| eval duration_bucket=if(humidity_pct>60,"high","low")
| stats count by zone, duration_bucket
```
- **Implementation:** Use sliding windows to alert only if out of 40–60% RH for >15 minutes. Pair with dew point for condensation risk.
- **Visualization:** Line chart (RH with bands), Table (zones in excursion), Single value (max excursion minutes).
- **CIM Models:** N/A

---

### UC-15.2.11 · Chiller Plant Efficiency (kW/ton)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Elevated kW/ton indicates fouling, low refrigerant, or poor tower performance.
- **App/TA:** BMS chiller plant
- **Data Sources:** `sourcetype="bms:chiller"` (tons, kw, cop)
- **SPL:**
```spl
index=cooling sourcetype="bms:chiller"
| eval kw_per_ton=round(kw/tons,3)
| where kw_per_ton > design_kw_per_ton * 1.15
| timechart span=15m avg(kw_per_ton) by chiller_id
```
- **Implementation:** Baseline design kW/ton from commissioning. Alert on sustained degradation. Schedule tube cleaning on trend.
- **Visualization:** Line chart (kW/ton trend), Gauge (current vs design), Table (chillers degraded).
- **CIM Models:** N/A

---

### UC-15.2.12 · Liquid Cooling Loop Pressure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Leak or pump failure shows first as pressure loss or delta-P across strainers.
- **App/TA:** CDU / in-rack liquid cooling
- **Data Sources:** `sourcetype="liquid_cool:loop"` (supply_kpa, return_kpa, flow_lpm)
- **SPL:**
```spl
index=cooling sourcetype="liquid_cool:loop"
| eval delta_p=supply_kpa-return_kpa
| where supply_kpa < min_supply_kpa OR delta_p < min_delta_p OR flow_lpm < min_flow
| table _time, rack_id, supply_kpa, return_kpa, flow_lpm, delta_p
```
- **Implementation:** Define min pressure and flow per vendor. Alert on any breach. Integrate leak-detection rope under manifolds.
- **Visualization:** Line chart (pressure and flow), Gauge (delta-P), Table (loops at risk).
- **CIM Models:** N/A

---

### UC-15.2.13 · Air Handler Filter Differential Pressure
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** High ΔP across filters increases fan energy and reduces airflow; indicates change-out due.
- **App/TA:** BMS AHU points
- **Data Sources:** `sourcetype="bms:ahu"` (filter_dp_pa, fan_speed_pct)
- **SPL:**
```spl
index=cooling sourcetype="bms:ahu"
| where filter_dp_pa > max_filter_dp_pa * 0.85
| table ahu_id, filter_dp_pa, max_filter_dp_pa, fan_speed_pct
```
- **Implementation:** Set change-out threshold at ~85% of max rated ΔP. Correlate rising ΔP with fan speed increases.
- **Visualization:** Line chart (filter ΔP), Table (AHUs due for filter change), Gauge (ΔP % of limit).
- **CIM Models:** N/A

---

### UC-15.2.14 · Cooling Capacity vs IT Load
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Compares available tons to IT heat load (from power meters) to expose margin before next summer.
- **App/TA:** BMS + IT power feeds
- **Data Sources:** `sourcetype="bms:cooling_capacity"` `sourcetype="power:it_heat"`
- **SPL:**
```spl
index=cooling sourcetype="bms:cooling_capacity"
| eval it_heat_tons=it_load_kw * 0.284345
| eval margin_tons=cooling_capacity_tons - cooling_output_tons
| where margin_tons < it_heat_tons * 0.15
| table zone, cooling_capacity_tons, cooling_output_tons, it_heat_tons, margin_tons
```
- **Implementation:** Convert IT kW to tons (approx). Alert when margin <15% of peak load forecast. Feed capacity planning.
- **Visualization:** Area chart (load vs capacity), Gauge (margin tons), Table (zones tight).
- **CIM Models:** N/A

---

### UC-15.2.15 · Economizer Mode Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low economizer hours may indicate stuck dampers or bad enthalpy programming—wasting energy.
- **App/TA:** BMS
- **Data Sources:** `sourcetype="bms:economizer"` (mode, oa_temp_f, enthalpy_ok)
- **SPL:**
```spl
index=cooling sourcetype="bms:economizer"
| timechart span=1d sum(eval(if(mode="economizer",1,0))) as econ_hours by ahu_id
| where econ_hours < 4
```
- **Implementation:** Compare economizer hours to weather bin data. Investigate AHU with low free-cooling in mild weather.
- **Visualization:** Bar chart (econ hours by month), Line chart (OA temp vs mode), Table (AHUs underutilizing economizer).
- **CIM Models:** N/A

---

### UC-15.2.16 · Condensation Risk Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Surface temp below dew point risks water on equipment and slip hazards near chilled doors.
- **App/TA:** RH + surface temp sensors
- **Data Sources:** `sourcetype="sensor:condensation"` (surface_temp_c, dew_point_c)
- **SPL:**
```spl
index=environment sourcetype="sensor:condensation"
| where surface_temp_c <= dew_point_c + 1
| table _time, location, surface_temp_c, dew_point_c, rh_pct
```
- **Implementation:** Compute dew point from RH and air temp or ingest BMS dew point. Alert when within 1°C of condensation.
- **Visualization:** Table (at-risk locations), Line chart (surface temp vs dew), Single value (active condensation risk).
- **CIM Models:** N/A

---

### UC-15.2.17 · Cooling Redundancy Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** N+1 cooling requires knowing when one CRAC is down and remaining capacity still covers peak IT load.
- **App/TA:** BMS, cooling plant model
- **Data Sources:** `sourcetype="bms:cooling_redundancy"` (online_tons, required_tons, units_down)
- **SPL:**
```spl
index=cooling sourcetype="bms:cooling_redundancy"
| where online_tons < required_tons * 1.1 OR units_down > 0
| table _time, zone, online_tons, required_tons, units_down, unit_list
```
- **Implementation:** Set `required_tons` from peak IT load × safety factor. Alert when redundancy lost. Block new installs if margin negative.
- **Visualization:** Gauge (redundancy margin), Table (zones without N+1), Status grid (unit × online).
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
- **CIM Models:** N/A
- **CIM SPL:**
```
No CIM model available for physical access control data.
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
- **CIM Models:** N/A
- **CIM SPL:**
```
No CIM model available for physical access control data.
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
- **CIM Models:** N/A
- **CIM SPL:**
```
No CIM model available for physical access control data.
```

---

### UC-15.3.6 · Rack PDU Load and Phase Balance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** PDU overload or phase imbalance risks circuit trips and equipment failure. Monitoring supports capacity planning and safe load distribution.
- **App/TA:** PDU SNMP or API, DCIM
- **Data Sources:** PDU current/load per phase, per outlet
- **SPL:**
```spl
index=physical sourcetype="pdu:metrics"
| stats latest(current_a) as current, latest(kw) as load by pdu_id, phase
| eval imbalance=abs(current - avg(current) over (partition by pdu_id))
| where load > 80 OR imbalance > 10
| table pdu_id, phase, current, load, imbalance
```
- **Implementation:** Poll PDU metrics via SNMP or API. Alert when load exceeds 80% or phase imbalance exceeds threshold. Report on load trend and top-loaded PDUs. Balance loads across phases as needed.
- **Visualization:** Table (PDU load by phase), Bar chart (phase balance), Line chart (load trend).
- **CIM Models:** N/A

---

### UC-15.3.7 · Fire Suppression and Detection System Alarms
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Fire and gas detection events require immediate response. Centralized alarm monitoring ensures rapid escalation and audit trail.
- **App/TA:** Fire alarm panel integration, BMS
- **Data Sources:** Fire detection, suppression system status, alarm events
- **SPL:**
```spl
index=physical sourcetype="fire:alarm"
| search (status="alarm" OR status="trouble" OR type="suppression")
| table _time, zone, type, status, description
| sort -_time
```
- **Implementation:** Integrate fire panel or BMS for alarm events. Alert immediately on any alarm or suppression activation. Log all events for compliance. Report on alarm history and trouble events.
- **Visualization:** Table (alarms), Timeline (events), Single value (active alarms).
- **CIM Models:** N/A

---

### UC-15.3.8 · Raised Floor and Cable Management Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Floor tile removal or cable strain events can indicate unauthorized work or trip hazards. Monitoring supports physical security and change audit.
- **App/TA:** Floor/cable sensors, DCIM
- **Data Sources:** Tile position, cable tension or movement sensors
- **SPL:**
```spl
index=physical sourcetype="floor:sensor"
| search (tile_removed="true" OR cable_strain > 80)
| table _time, location, tile_id, cable_strain, operator
| sort -_time
```
- **Implementation:** Deploy sensors for critical floor tiles and cable runs. Forward events to Splunk. Alert on tile removal or strain above threshold. Correlate with change tickets. Report on access and strain history.
- **Visualization:** Table (events), Timeline (tile/cable events), Floor plan (locations).
- **CIM Models:** N/A

---

### UC-15.3.9 · Generator Run Hours and Maintenance Due
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Generator maintenance based on run hours ensures reliability during outages. Tracking run hours and maintenance due dates avoids missed service.
- **App/TA:** Generator controller, BMS
- **Data Sources:** Run hours, last maintenance date, next due
- **SPL:**
```spl
index=physical sourcetype="generator:status"
| stats latest(run_hours) as run_hrs, latest(maintenance_due_hrs) as due_hrs by generator_id
| eval remaining_hrs=due_hrs-run_hrs
| where remaining_hrs < 100
| table generator_id, run_hrs, due_hrs, remaining_hrs
```
- **Implementation:** Ingest generator run hours and maintenance schedule. Alert when remaining hours until next service is below threshold. Report on run hour trend and overdue maintenance.
- **Visualization:** Table (generators due for service), Gauge (remaining hours), Bar chart (run hours by unit).
- **CIM Models:** N/A

---

### UC-15.3.10 · Data Center Capacity Headroom by Zone
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracking power, cooling, and space headroom by zone supports capacity planning and prevents over-provisioning in hot spots.
- **App/TA:** DCIM, PDU/CRAC metrics
- **Data Sources:** Power capacity vs used, cooling capacity vs load, rack U available
- **SPL:**
```spl
index=dcim sourcetype="capacity:zone"
| eval power_headroom_pct=((capacity_kw - used_kw)/capacity_kw)*100
| eval cooling_headroom_pct=((capacity_tons - load_tons)/capacity_tons)*100
| where power_headroom_pct < 20 OR cooling_headroom_pct < 20
| table zone, power_headroom_pct, cooling_headroom_pct, u_available
```
- **Implementation:** Aggregate capacity and usage by zone from DCIM or meters. Alert when headroom drops below 20%. Report on trend and zones with least headroom. Use for placement and expansion planning.
- **Visualization:** Table (zones with low headroom), Bar chart (headroom by zone), Heatmap (zone capacity).
- **CIM Models:** N/A

---

### UC-15.3.11 · CCTV / IP Camera Health Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Security
- **Value:** Camera online/offline, storage utilization, recording status ensures continuous surveillance coverage and prevents blind spots during security incidents.
- **App/TA:** Custom (NVR API, ONVIF, Hikvision ISAPI)
- **Data Sources:** NVR API (camera status, storage), ONVIF device management
- **SPL:**
```spl
index=physical sourcetype="nvr:camera_status"
| where connection_status!="online" OR recording_status!="recording" OR storage_util_pct > 90
| table camera_id, location, connection_status, recording_status, storage_util_pct, last_frame_time
| sort connection_status
```
- **Implementation:** Poll NVR API (Hikvision ISAPI, Milestone, Genetec) or ONVIF for camera status. Ingest connection_status, recording_status, storage_util_pct. Poll every 5–15 minutes. Alert on camera offline, recording stopped, or storage >90%. Track camera uptime percentage. Report on coverage gaps by zone.
- **Visualization:** Status grid (camera × status), Table (offline or degraded cameras), Gauge (storage utilization), Floor plan (camera locations with status).
- **CIM Models:** N/A

---

### UC-15.3.12 · Fire Suppression System Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Safety, Availability
- **Value:** Pre-action system armed/disarmed, agent levels (FM-200/Novec) ensure fire suppression readiness; disarmed or low-agent systems leave the data center unprotected.
- **App/TA:** Custom (BMS integration, SNMP)
- **Data Sources:** Fire suppression panel telemetry (system_armed, agent_level_pct, alarm_active)
- **SPL:**
```spl
index=physical sourcetype="fire:suppression_status"
| where system_armed!="armed" OR agent_level_pct < 95 OR alarm_active="true"
| table _time, zone, system_armed, agent_level_pct, alarm_active, last_inspection_date
| sort -_time
```
- **Implementation:** Integrate fire suppression panel via BMS, SNMP, or vendor API. Ingest system_armed (armed/disarmed), agent_level_pct, alarm_active. Poll every 15–30 minutes. Alert immediately on disarmed state, low agent (<95%), or active alarm. Track inspection dates. Report on system readiness for compliance.
- **Visualization:** Status grid (zone × armed/agent status), Table (zones needing attention), Gauge (agent level %), Single value (systems disarmed).
- **CIM Models:** N/A

---

### UC-15.3.13 · Environmental Sensor Battery Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Wireless environmental sensor battery health; dead batteries create monitoring gaps and risk undetected temperature or humidity exceedances.
- **App/TA:** SNMP modular input, custom (sensor API)
- **Data Sources:** Sensor management interface (battery_level_pct, last_report_time)
- **SPL:**
```spl
index=environment sourcetype="sensor:battery_status"
| eval hours_since_report=round((now()-last_report_time)/3600,1)
| where battery_level_pct < 20 OR hours_since_report > 24
| table sensor_id, zone, sensor_type, battery_level_pct, last_report_time, hours_since_report
| sort battery_level_pct
```
- **Implementation:** Poll sensor management interface (SNMP, API) for battery_level_pct and last_report_time. Poll daily or every 6 hours. Alert on battery <20% or no report in 24+ hours (possible dead battery). Maintain sensor inventory with battery replacement schedule. Report on sensors due for battery change.
- **Visualization:** Table (low battery sensors), Gauge (lowest battery %), Bar chart (sensors by battery level), Single value (sensors needing battery replacement).
- **CIM Models:** N/A

---

---

### UC-15.3.14 · Badge Tailgating and Anti-Passback Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Tracks piggyback events where anti-passback rules fire or two entries occur without intermediate exit—stronger signal than generic door events alone.
- **App/TA:** Access control system
- **Data Sources:** `sourcetype="access_control"` (event_subtype=tailgate, apb_violation)
- **SPL:**
```spl
index=physical sourcetype="access_control"
| where match(event_subtype,"(?i)tailgate|apb|anti.passback")
| stats count by door, badge_holder, reader_id
| sort -count
```
- **Implementation:** Enable anti-passback on mantraps where supported. Correlate with video analytics if available. Escalate repeat doors.
- **Visualization:** Table (tailgate events), Bar chart (by door), Timeline.
- **CIM Models:** N/A

---

### UC-15.3.15 · After-Hours Access Without Active Work Order
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Correlates physical entry with ITSM change/work order to catch unauthorized after-hours presence.
- **App/TA:** Access control + ServiceNow CMDB
- **Data Sources:** `sourcetype="access_control"`, `sourcetype="servicenow:change"`
- **SPL:**
```spl
index=physical sourcetype="access_control" result="granted"
| eval hour=strftime(_time,"%H")
| where (hour < 6 OR hour > 22)
| join type=left badge_id [
  search index=itsm sourcetype="servicenow:change" state="Implement"
  | eval wo_open=if(now() > planned_start AND now() < planned_end,1,0)
  | table badge_id, wo_open, change_number
]
| where wo_open=0 OR isnull(wo_open)
| table _time, badge_holder, door, badge_id
```
- **Implementation:** Map badge IDs to enterprise IDs in CMDB. Tune join window for active changes. Alert on access with no matching WO.
- **Visualization:** Table (unapproved after-hours), Bar chart (by person).
- **CIM Models:** N/A

---

### UC-15.3.16 · Camera Feed Loss and Recording Gap Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Detects loss of RTSP/HLS stream and gaps in NVR recording separately from generic camera “offline” pings.
- **App/TA:** VMS API, stream health probes
- **Data Sources:** `sourcetype="vms:stream_health"` (fps, keyframes, recording_continuity)
- **SPL:**
```spl
index=physical sourcetype="vms:stream_health"
| where fps=0 OR recording_gap_sec > 60 OR stream_state="lost"
| stats latest(recording_gap_sec) as gap by camera_id, site
| sort -gap
```
- **Implementation:** Poll VMS for per-camera FPS and last recorded frame time. Alert on stream loss or gap >1 min for critical zones.
- **Visualization:** Table (cameras with feed loss), Timeline (gaps), Floor plan overlay.
- **CIM Models:** N/A

---

### UC-15.3.17 · Visitor Badge Expiry Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Expired visitor badges that remain active create audit findings and tailgating risk.
- **App/TA:** Visitor management system API
- **Data Sources:** `sourcetype="vms:visitor"` (visitor_id, badge_expiry, status)
- **SPL:**
```spl
index=physical sourcetype="vms:visitor"
| eval days_to_exp=round((strptime(badge_expiry,"%Y-%m-%d")-now())/86400,0)
| where status="active" AND (days_to_exp < 0 OR days_to_exp < 1)
| table visitor_id, host_employee, badge_expiry, days_to_exp
```
- **Implementation:** Sync visitor system daily. Auto-disable badges on expiry in PACS where API allows. Alert on active badge past expiry.
- **Visualization:** Table (expired active badges), Single value (count), Timeline.
- **CIM Models:** N/A

---

### UC-15.3.18 · Cabinet Intrusion and Forced Rack Door Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Lateral contact/forced-open sensors on colo cabinets detect physical tampering faster than walk-through audits.
- **App/TA:** Smart cabinet PDU/door sensors
- **Data Sources:** `sourcetype="cabinet:intrusion"` (door_state, force_detect)
- **SPL:**
```spl
index=physical sourcetype="cabinet:intrusion"
| where force_detect=1 OR door_state="forced" OR (door_state="open" AND authorized=0)
| table _time, rack_id, cabinet_id, door_state, user, ticket_id
```
- **Implementation:** Require ticket_id or approved user for opens in secure suites. Page on forced events immediately.
- **Visualization:** Timeline (intrusion events), Table (racks), Map of data hall.
- **CIM Models:** N/A

---

### UC-15.3.19 · Water Leak Sensor Zone Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Correlates multiple rope sensors to localize leak source and trigger EPO workflows under raised floor.
- **App/TA:** Leak detection panel → Splunk
- **Data Sources:** `sourcetype="leak_detection"` (zone, sensor_id, conductivity)
- **SPL:**
```spl
index=environment sourcetype="leak_detection"
| where leak_detected=1
| stats count by zone, crac_id
| sort -count
```
- **Implementation:** On any leak, show adjacent zones and nearest CRAC/isolation valve. Integrate with facilities runbook.
- **Visualization:** Floor plan (zones), Table (active leaks), Single value (leak count).
- **CIM Models:** N/A

---

### UC-15.3.20 · Fire Suppression System Health and Supervisory Signals
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Safety
- **Value:** Supervisory off-normal (low air, pre-action valve trouble) precedes full alarm; distinct from agent level alone.
- **App/TA:** Fire panel BMS integration
- **Data Sources:** `sourcetype="fire:supervisory"` (signal_type, zone, ack_state)
- **SPL:**
```spl
index=physical sourcetype="fire:supervisory"
| where signal_type IN ("trouble","supervisory","preaction_air_low") AND ack_state="unack"
| table _time, zone, signal_type, description
| sort -_time
```
- **Implementation:** Map all supervisory points per NFPA 72. Page on any unacknowledged supervisory >5 min.
- **Visualization:** Timeline (supervisory events), Table (unacked), Status grid (zone × signal).
- **CIM Models:** N/A

---

### UC-15.3.21 · Access Control Panel Tamper and Line Fault
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Enclosure tamper, RS-485 ground faults, or DC line faults may precede bypass or sabotage.
- **App/TA:** Access panel diagnostics
- **Data Sources:** `sourcetype="access_control:panel"` (tamper, line_fault, power_state)
- **SPL:**
```spl
index=physical sourcetype="access_control:panel"
| where tamper=1 OR line_fault=1 OR power_state!="normal"
| stats count by panel_id, fault_type
| sort -count
```
- **Implementation:** Alert at critical on tamper. Dispatch security to site. Log for forensic chain of custody.
- **Visualization:** Table (panels in fault), Timeline (tamper), Single value (panels compromised).
- **CIM Models:** N/A
