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
- **Visualization:** Timechart of `runtime_min` and `charge_pct` by `ups_name` for battery health trending; table sorted by `runtime_min` ascending to surface units needing replacement; single-value gauge for fleet-wide minimum runtime as the critical KPI.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---


### UC-15.1.22 · UPS Battery Monitoring
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-15.1.23 · Power Consumption Trending
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-15.1.24 · Rack PDU Load and Phase Balance
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-15.1.25 · Generator Run Hours and Maintenance Due
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| bin _time span=5m
| stats avg(eval(if(position="cold_aisle",temp_c,null()))) as cold_c, avg(eval(if(position="hot_aisle",temp_c,null()))) as hot_c by row_id, _time
| eval delta_t=hot_c-cold_c
| where delta_t < 8 OR delta_t > 22
| table row_id, cold_c, hot_c, delta_t
```
- **Implementation:** Pair sensors per row. Baseline expected ΔT for your containment design. Alert outside band.
- **Visualization:** Line chart (ΔT by row), Heatmap (row × time), Gauge (current ΔT).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---


### UC-15.2.18 · Data Center Humidity & Condensation Risk
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

---

### UC-15.2.19 · Water Leak Sensor Zone Correlation
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| join type=left max=1 badge_id [
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-15.3.22 · Camera Uptime and Availability Tracking (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors video surveillance system availability to ensure continuous monitoring coverage.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MV sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(status) as camera_status, latest(last_status_change) as status_change by camera_name, location
| where camera_status="offline"
```
- **Implementation:** Monitor MV camera status via device API. Alert on offline cameras.
- **Visualization:** Camera status map; offline camera list; availability percentage gauge.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.23 · Video Retention and Cloud Archive Storage Utilization (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks cloud storage usage for video archives to manage costs and ensure retention SLA.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" storage_usage=*
| stats sum(storage_usage) as total_storage_gb by camera_id, retention_days
| eval storage_pct=round(total_storage_gb*100/1000, 2)
| where storage_pct > 80
```
- **Implementation:** Query camera API for storage metrics. Alert on >80% utilization.
- **Visualization:** Storage utilization gauge; retention timeline; storage trend chart.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.24 · Motion Detection Events and Alert Volume Analysis (Meraki MV)
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Analyzes motion detection event patterns to optimize camera sensitivity and reduce false alerts.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*motion*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*motion*"
| timechart count as motion_events by camera_name
| eval daily_avg=round(motion_events/1440, 2)
```
- **Implementation:** Ingest motion detection events. Track volume and patterns.
- **Visualization:** Motion detection timeline; heat map by time of day; camera comparison chart.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.25 · Camera Video Quality Score and Stream Health (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors video quality metrics to identify network or hardware issues affecting video feeds.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" quality_score=*
| stats avg(quality_score) as avg_quality, min(quality_score) as min_quality by camera_name
| where avg_quality < 80
| sort avg_quality
```
- **Implementation:** Query camera API for quality_score metric. Alert on <80 average.
- **Visualization:** Quality score gauge per camera; quality trend line; affected camera list.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.26 · Cloud Archive Status and Backup Validation (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures video archives are successfully uploaded to cloud and backup integrity is maintained.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api archive_status=*`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" archive_status=*
| stats latest(archive_status) as backup_status, latest(last_archive_time) as last_backup by camera_id
| where archive_status != "success"
```
- **Implementation:** Check camera API archive status. Alert on failures.
- **Visualization:** Archive status table; last backup time timeline; failure alert dashboard.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.27 · Video Stream Connection Errors and Quality Issues (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detects video stream connection failures that prevent remote viewing or recording.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*stream*" OR signature="*connection*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*stream*" OR signature="*connection*")
| stats count as error_count by camera_name, error_type
| where error_count > 10
```
- **Implementation:** Monitor stream connection events. Alert on error spikes.
- **Visualization:** Connection error timeline; affected camera list; error type breakdown.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.28 · Camera Firmware Compliance and Update Management (Meraki MV)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all cameras run current firmware with security patches.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MV`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(firmware_version) as camera_fw, count as camera_count
| lookup recommended_camera_fw.csv camera_model OUTPUTNEW recommended_version
| where camera_fw != recommended_version
```
- **Implementation:** Query MV device API for firmware. Compare to recommended baseline.
- **Visualization:** Firmware version table; compliance percentage gauge; outdated camera list.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.29 · Night Mode Effectiveness and Low-Light Performance (Meraki MV)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors camera performance in low-light conditions to ensure night surveillance effectiveness.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api night_mode=true`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" night_mode=true
| stats avg(quality_score) as night_quality, count as night_mode_events by camera_name
| where night_quality < 75
```
- **Implementation:** Track camera performance during night mode. Monitor quality metrics.
- **Visualization:** Night mode quality gauge; low-light performance timeline; affected camera list.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.30 · People Counting Trends and Occupancy Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses camera people counting to track foot traffic trends for space utilization and facility planning.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api people_count=*`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" people_count=*
| timechart avg(people_count) as avg_occupancy by location
```
- **Implementation:** Extract people_count metrics from camera API. Aggregate by location and time.
- **Visualization:** Occupancy heat map by time of day; location comparison bar chart; trend sparkline.
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---


### UC-15.3.31 · Building Occupancy Trending and Capacity Planning
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Provides real-time and historical people counts per building, floor, and zone using data from Meraki APs and cameras. Supports compliance with fire safety capacity limits, energy management optimization (HVAC scheduling based on actual occupancy), and real estate planning. Trending data reveals patterns — which floors are overcrowded on Tuesdays, which buildings are underused on Fridays — enabling data-driven workplace strategy decisions.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Cisco Spaces Firehose API
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Meraki MV Smart Cameras
- **Data Sources:** Cisco Spaces Firehose API (COUNT events — device counts, camera people counts)
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:occupancy"
| bin _time span=15m
| stats max(deviceCount) as occupancy by _time, building, floor
| eventstats avg(occupancy) as avg_occupancy, max(occupancy) as peak_occupancy by building, floor
| eval capacity_pct=round(occupancy/max_capacity*100, 1)
| where capacity_pct > 80
| table _time, building, floor, occupancy, avg_occupancy, peak_occupancy, capacity_pct
```
- **Implementation:** Deploy the Spaces Add-On for Splunk (Splunkbase app 8485) and configure it with your Cisco Spaces API credentials. Enable the Firehose API with COUNT event types in Cisco Spaces dashboard. Floor capacity limits should be maintained in a lookup table (`building_capacity.csv`) with building, floor, and max_capacity columns. Set alerts at 80% capacity for warning and 95% for critical. Schedule daily and weekly reports for facilities management.
- **Visualization:** Floor plan heat maps (occupancy by zone), Line chart (occupancy trend by floor), Column chart (peak occupancy by day of week), Single value panels (current building occupancy, % of capacity).
- **CIM Models:** N/A

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485), [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.32 · Visitor Dwell Time and Movement Flow Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Measures how long visitors and employees spend in specific zones and tracks movement patterns between areas. For corporate campuses, this optimizes cafeteria layouts, identifies bottleneck corridors, and improves wayfinding. For retail environments, it measures engagement with displays and optimizes store layouts. For healthcare, it tracks patient flow through departments to reduce wait times. Dwell time analysis reveals which spaces create value and which are passed through without engagement.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), Cisco Spaces Location Analytics
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86
- **Data Sources:** Cisco Spaces Firehose API (DEVICE_LOCATION_UPDATE, DEVICE_PRESENCE events — entry, exit, dwell)
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:location"
| search eventType="DEVICE_PRESENCE"
| eval dwell_min=round((exitTime-entryTime)/60, 1)
| where isnotnull(dwell_min) AND dwell_min > 0
| stats avg(dwell_min) as avg_dwell, median(dwell_min) as median_dwell, max(dwell_min) as max_dwell, count as visits by zoneName, building, floor
| eval engagement=case(avg_dwell>30, "High", avg_dwell>10, "Medium", avg_dwell>2, "Low", 1==1, "Pass-through")
| sort -visits
| table zoneName, building, floor, visits, avg_dwell, median_dwell, max_dwell, engagement
```
- **Implementation:** Enable location analytics in Cisco Spaces with zone definitions mapped to your floor plans. Configure the Firehose API to stream DEVICE_PRESENCE and DEVICE_LOCATION_UPDATE events. Define meaningful zones in Cisco Spaces (lobbies, meeting areas, cafeterias, collaboration spaces). Device presence events fire at entry, after 10 minutes of inactivity, and at exit. Filter out devices with dwell times under 2 minutes to exclude pass-throughs. Build movement flow analysis by sequencing location updates per device MAC.
- **Visualization:** Sankey diagram (movement flows between zones), Heat map (dwell time by zone and time of day), Bar chart (visits and avg dwell by zone), Table (zone engagement ranking).
- **CIM Models:** N/A

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485)

---

### UC-15.3.33 · Environmental Sensor Monitoring (Temperature, Humidity, Air Quality)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Performance
- **Value:** Monitors environmental conditions using Meraki MT sensors — temperature, humidity, air quality (PM2.5, TVOC, CO2), and water leaks. Protects server rooms and network closets from overheating, monitors warehouse cold-chain compliance, detects water leaks before they cause damage, and ensures office air quality meets health standards. Sensor data with five days of onboard storage survives network outages. Threshold-based alerting enables immediate response to environmental hazards.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), Cisco Spaces IoT Explorer, Meraki Dashboard API
- **Equipment Models:** Cisco Meraki MT10 (temperature/humidity), MT11 (temperature probe), MT12 (water leak), MT14 (air quality — PM2.5, TVOC, noise, temp, humidity), MT15 (CO2, PM2.5, TVOC, noise, temp, humidity), MT20 (open/close door sensor), MT30 (smart automation button)
- **Data Sources:** Cisco Spaces Firehose API (IOT_TELEMETRY events), Meraki sensor API
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:sensors"
| eval alert=case(temperature>28, "High Temperature", temperature<16, "Low Temperature", humidity>70, "High Humidity", humidity<20, "Low Humidity", pm25>35, "Poor Air Quality (PM2.5)", co2>1000, "High CO2", tvoc>500, "High TVOC", waterDetected="true", "Water Leak Detected", 1==1, null())
| where isnotnull(alert)
| stats latest(temperature) as temp, latest(humidity) as humidity, latest(pm25) as pm25, latest(co2) as co2, values(alert) as alerts by sensorName, sensorModel, location, building
| sort -temp
| table sensorName, sensorModel, location, building, temp, humidity, pm25, co2, alerts
```
- **Implementation:** Deploy Meraki MT sensors and associate them with Meraki MR access points as BLE gateways. Configure sensor thresholds in Meraki Dashboard for local alerting. Stream telemetry to Splunk via the Spaces Add-On or direct Meraki webhook integration to HEC. Define location-specific thresholds (server rooms: 18-27°C; offices: 20-24°C; cold storage: 2-8°C). Create severity tiers: warning (approaching threshold), critical (exceeding threshold), emergency (water leak, extreme temperature). MT sensors have five-year battery life and five days of onboard data storage.
- **Visualization:** Gauge panels (current temp/humidity per zone), Line chart (environmental trends over 7 days), Map (sensor locations with color-coded status), Alert table (active environmental alerts).
- **CIM Models:** N/A

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485)

---

### UC-15.3.34 · Asset Tracking and Geofencing Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** Tracks the real-time location of high-value assets (medical equipment, network gear, tools, laptops, carts) using BLE tags and Cisco Spaces IoT Explorer. Geofencing alerts notify when assets leave designated zones — preventing theft, loss, and misplacement. In healthcare, this tracks infusion pumps and wheelchairs across departments. In manufacturing, it ensures tools return to storage after shifts. Historical location data supports asset utilization analysis and procurement decisions.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), Cisco Spaces IoT Explorer
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86 (as BLE gateways), BLE asset tags (various vendors)
- **Data Sources:** Cisco Spaces Firehose API (IOT_TELEMETRY, DEVICE_LOCATION_UPDATE events for BLE tags)
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:assets"
| eval zone_violation=if(currentZone!=assignedZone AND isnotnull(assignedZone), "Out of Zone", null())
| eval missing=if(_time-lastSeenTime>3600, "Not Seen >1hr", null())
| where isnotnull(zone_violation) OR isnotnull(missing)
| stats latest(currentZone) as current_zone, latest(assignedZone) as assigned_zone, latest(building) as building, latest(floor) as floor, latest(lastSeenTime) as last_seen by assetName, assetTag, assetCategory
| eval status=case(isnotnull(zone_violation), "GEOFENCE ALERT", isnotnull(missing), "MISSING", 1==1, "Unknown")
| table assetName, assetTag, assetCategory, status, current_zone, assigned_zone, building, floor, last_seen
```
- **Implementation:** Register assets in Cisco Spaces IoT Explorer with BLE tags. Define geofence zones matching building floor plans. Configure the Firehose API to stream asset location updates. Maintain a lookup table of asset assignments (asset_tag, assigned_zone, asset_category, asset_value). Alert immediately on high-value assets leaving their zone. For lower-value assets, alert after 30 minutes outside zone. Track "last seen" timestamps and flag assets not seen for >1 hour during business hours. Generate weekly utilization reports (time in zone vs. time out of zone) to optimize asset distribution.
- **Visualization:** Floor plan map (asset locations with icons), Table (geofence violations and missing assets), Bar chart (assets by zone), Timeline (asset movement history).
- **CIM Models:** N/A

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485)

---

### UC-15.3.35 · After-Hours Wireless Presence Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects Wi-Fi-connected devices present in buildings or restricted zones outside of business hours. Correlates with badge access data and employee schedules to identify unauthorized presence — potential tailgating, after-hours theft, or social engineering. Unlike badge-only systems which only detect entry, wireless presence confirms ongoing physical presence. Supports investigations by providing device MAC, location, and duration of after-hours presence. Particularly valuable for facilities with sensitive areas (data centers, labs, executive floors).
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), Cisco Spaces Firehose API
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86
- **Data Sources:** Cisco Spaces Firehose API (DEVICE_PRESENCE events — entry/exit with timestamps)
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:presence" eventType="DEVICE_ENTRY"
| eval hour=strftime(_time, "%H")
| eval day=strftime(_time, "%u")
| where (hour<6 OR hour>20) OR day>5
| lookup known_devices.csv macAddress OUTPUT owner, department, authorized_afterhours
| where authorized_afterhours!="yes" OR isnull(authorized_afterhours)
| stats count as entries, earliest(_time) as first_seen, latest(_time) as last_seen by macAddress, owner, department, building, floor, zoneName
| sort -count
| table macAddress, owner, department, building, floor, zoneName, first_seen, last_seen, entries
```
- **Implementation:** Configure Cisco Spaces Firehose API to stream DEVICE_PRESENCE events with entry/exit notifications. Build a known devices lookup by correlating MAC addresses with user identities from ISE or Active Directory (via 802.1X authentication records). Define business hours per building/zone (some facilities operate 24/7). Maintain an authorized_afterhours list for security, janitorial, and operations staff. Alert on unknown devices or unauthorized users detected after hours in sensitive zones. Integrate with badge access logs for cross-validation.
- **Visualization:** Floor plan map (after-hours device locations), Timeline (presence events outside business hours), Table (unauthorized after-hours presence), Bar chart (after-hours detections by zone).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-15.3.36 · Workspace Utilization and Ghost Booking Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Combines room booking data with actual physical occupancy from Cisco Spaces and Webex device sensors to calculate true workspace utilization. Identifies "ghost bookings" — rooms reserved but never occupied — which waste available space and frustrate employees searching for rooms. Reveals which rooms are most/least popular, optimal room sizes for actual group sizes, and peak usage patterns. Directly supports real estate cost reduction by providing evidence-based recommendations for space consolidation, redesign, or expansion.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), `ta_cisco_webex_add_on_for_splunk` (GitHub), calendar integration
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Webex Room Kit, Room Bar, Room Navigator, Webex Board
- **Data Sources:** Cisco Spaces occupancy data, Webex device people count (RoomAnalytics), calendar/booking system data
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:workspace"
| join type=left max=0 workspaceId [search index=webex sourcetype="webex:workspace_bookings" | fields workspaceId, bookingStart, bookingEnd, organizer]
| eval booked=if(isnotnull(bookingStart), 1, 0)
| eval occupied=if(peopleCount>0, 1, 0)
| eval ghost_booking=if(booked=1 AND occupied=0, 1, 0)
| eval unbooked_usage=if(booked=0 AND occupied=1, 1, 0)
| stats sum(booked) as total_bookings, sum(ghost_booking) as ghost_bookings, sum(unbooked_usage) as walk_ins, avg(peopleCount) as avg_occupants, max(roomCapacity) as capacity by workspaceName, building, floor
| eval ghost_rate=if(total_bookings>0, round(ghost_bookings/total_bookings*100, 1), 0)
| eval avg_fill=if(capacity>0, round(avg_occupants/capacity*100, 1), 0)
| sort -ghost_rate
| table workspaceName, building, floor, capacity, total_bookings, ghost_bookings, ghost_rate, walk_ins, avg_occupants, avg_fill
```
- **Implementation:** Enable Webex RoomAnalytics people counting on all room devices (`xConfiguration RoomAnalytics PeopleCountOutOfCall: On`). Ingest room booking data from your calendar system (Google Calendar, Microsoft 365, or Webex Workspaces API). Stream occupancy data from Cisco Spaces. Correlate bookings with actual occupancy using workspace IDs and time windows. Define ghost booking as: room booked but no occupancy detected within 10 minutes of booking start. Generate weekly facility reports showing: ghost booking rate per floor/building, rooms with avg occupancy below 25% of capacity, and peak vs. off-peak usage patterns.
- **Visualization:** Heat map (utilization by room and time slot), Bar chart (ghost booking rate by floor), Table (workspace utilization summary), Scatter plot (room capacity vs. actual avg occupants).
- **CIM Models:** N/A

- **References:** [Splunkbase app 8485](https://splunkbase.splunk.com/app/8485), [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.37 · Access Control Event Audit
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-15.3.38 · Cisco Spaces Wayfinding and Path Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** Understanding how people physically move through a building reveals traffic bottlenecks, dead zones, and inefficient layouts invisible to static occupancy sensors. Cisco Spaces path analytics tracks visitor movement between zones over time — showing that 80% of foot traffic funnels through one corridor, or that a key amenity is consistently bypassed because signage directs people the wrong way. This data drives floor plan optimization, signage placement, and emergency egress planning with evidence rather than guesswork.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase #8485), `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), `TA-cisco_ios` (Catalyst), Cisco Spaces API
- **Equipment Models:** Cisco Meraki MR series (Wi-Fi location), Cisco Catalyst 9100 series (Wi-Fi), Cisco Spaces IoT Services
- **Data Sources:** `sourcetype=cisco:spaces:location`, `sourcetype=cisco:spaces:path_analytics`
- **SPL:**
```spl
index=spaces sourcetype="cisco:spaces:location"
| sort 0 device_mac, _time
| streamstats current=f last(zone_name) as prev_zone, last(_time) as prev_time by device_mac
| where zone_name!=prev_zone AND isnotnull(prev_zone)
| eval transition=prev_zone." → ".zone_name
| eval transit_sec=_time - prev_time
| where transit_sec < 1800
| bin _time span=1h
| stats count as transitions, avg(transit_sec) as avg_transit_sec, dc(device_mac) as unique_visitors by _time, transition, prev_zone, zone_name
| eval avg_transit_min=round(avg_transit_sec/60, 1)
| sort -transitions
| table _time, transition, transitions, unique_visitors, avg_transit_min
```
- **Implementation:** Cisco Spaces uses Wi-Fi probe requests and connected client location data from Meraki or Catalyst APs to track device movement across defined zones (floors, wings, departments, amenities). Ingest location updates via the Spaces Add-On. Define zones in Cisco Spaces matching physical areas (lobby, cafeteria, elevator bank, parking, conference wing). Track zone transitions per device to build path flows. Filter out transitions longer than 30 minutes (device likely stationary, then moved). Aggregate by transition pair to identify the highest-traffic paths. Overlay with building floor plans to visualize traffic flow. Compare weekday vs weekend patterns and identify peak congestion hours. Use findings to optimize signage placement, adjust security checkpoint locations, and validate emergency egress route capacity.
- **Visualization:** Sankey diagram (zone-to-zone flow), Floor plan overlay (traffic density by path), Bar chart (top 20 transitions by volume), Line chart (traffic volume by hour), Heatmap (zone × hour congestion).
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.39 · Cisco Spaces Proximity and Engagement Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** For corporate campuses, retail environments, and visitor centers, understanding how people engage with specific zones — reception desks, demo areas, retail displays, cafeterias, wellness rooms — transforms facility management from guesswork to data-driven optimization. Cisco Spaces dwell time and repeat visit analytics quantify engagement intensity: a demo area where visitors average 30 seconds of dwell time needs redesign, while a breakout space with 45-minute average dwell validates the investment. Repeat visit patterns reveal which spaces become habit destinations vs one-time curiosities.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase #8485), `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), `TA-cisco_ios` (Catalyst), Cisco Spaces API
- **Equipment Models:** Cisco Meraki MR series, Cisco Catalyst 9100 series, Cisco Spaces IoT Services
- **Data Sources:** `sourcetype=cisco:spaces:occupancy`, `sourcetype=cisco:spaces:dwell_time`
- **SPL:**
```spl
index=spaces sourcetype="cisco:spaces:dwell_time"
| eval dwell_bucket=case(
    dwell_min < 5, "Passerby (<5min)",
    dwell_min < 15, "Brief (5-15min)",
    dwell_min < 30, "Moderate (15-30min)",
    dwell_min < 60, "Engaged (30-60min)",
    1==1, "Extended (60min+)")
| bin _time span=1d
| stats count as visits, avg(dwell_min) as avg_dwell, dc(device_mac) as unique_visitors, sum(eval(if(repeat_visit=="Yes",1,0))) as repeat_visits by _time, zone_name, zone_type
| eval engagement_score=round((avg_dwell * 0.4) + (repeat_visits/unique_visitors * 100 * 0.3) + (unique_visitors * 0.3 / 10), 1)
| eval repeat_pct=round(repeat_visits*100/visits, 1)
| table _time, zone_name, zone_type, unique_visitors, visits, avg_dwell, repeat_pct, engagement_score
| sort -engagement_score
```
- **Implementation:** Ingest Cisco Spaces dwell time data via the Spaces Add-On. Cisco Spaces calculates dwell time by tracking how long a device's Wi-Fi probe requests are detected within a zone boundary. Configure zone types (amenity, collaboration, retail, reception, demo) to enable category-level analysis. Track unique visitors (distinct device MACs), average dwell time, and repeat visit rate (same device returning within 7 days). Build a composite engagement score combining dwell time, repeat rate, and visitor volume. Compare engagement across similar zone types (e.g., all breakout spaces) to identify high-performing and underperforming spaces. Provide monthly reports to facilities and real estate teams. For retail environments, correlate engagement with point-of-sale data to measure conversion.
- **Visualization:** Bar chart (engagement score by zone), Bubble chart (zones by visitor volume, dwell time, repeat rate), Line chart (engagement trend per zone over 90 days), Table (zone performance details), Heatmap (zone × day-of-week engagement).
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

### UC-15.3.40 · Cisco Spaces IoT Sensor Alert Correlation with Building Management
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance
- **Value:** Environmental sensor alerts (temperature excursion, humidity spike, poor air quality) are only half the story — the other half is whether the building management system (BMS) responded correctly. Correlating Cisco Spaces IoT sensor alerts with HVAC events, BMS actions, and occupancy patterns validates automated response effectiveness. When a temperature alert fires and the HVAC doesn't respond within 15 minutes, that's an automation failure. When air quality degrades only in occupied zones during peak hours, that's a ventilation capacity issue. This correlation turns isolated alerts into actionable facility intelligence.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase #8485), `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), BMS/BACnet integration, Cisco Spaces IoT Services
- **Equipment Models:** Cisco Spaces IoT sensors (temperature, humidity, air quality, CO2), Cisco Meraki MT sensors, BMS/HVAC systems
- **Data Sources:** `sourcetype=cisco:spaces:iot_sensors`, `sourcetype=bacnet:events` or `sourcetype=bms:events`, `sourcetype=cisco:spaces:occupancy`
- **SPL:**
```spl
index=spaces sourcetype="cisco:spaces:iot_sensors" alert_active=true
| eval sensor_alert=sensor_type.": ".alert_reason
| join type=left zone_id [search index=building sourcetype="bms:events" action_type="HVAC*"
    | stats latest(action) as bms_action, latest(_time) as bms_response_time by zone_id]
| join type=left zone_id [search index=spaces sourcetype="cisco:spaces:occupancy"
    | stats latest(occupancy_count) as current_occupancy by zone_id]
| eval response_delay_min=if(isnotnull(bms_response_time), round((_time - bms_response_time)/60, 1), null())
| eval bms_responded=if(isnotnull(bms_action), "Yes", "No")
| eval assessment=case(
    bms_responded=="No", "BMS Non-Response - Investigate",
    response_delay_min > 15, "Slow Response (".response_delay_min." min)",
    response_delay_min <= 15, "Timely Response",
    1==1, "Unknown")
| table _time, zone_id, sensor_alert, current_occupancy, bms_responded, bms_action, response_delay_min, assessment
| sort -_time
```
- **Implementation:** Ingest Cisco Spaces IoT sensor data (temperature, humidity, air quality index, CO2 levels) via the Spaces Add-On. Configure sensor alert thresholds in Cisco Spaces (e.g., temperature >27°C, CO2 >1000ppm, humidity >65%). Separately ingest BMS/HVAC event logs via BACnet gateway, Modbus, or BMS API integration. Correlate by zone ID and time window: when a sensor alert fires, check whether a corresponding BMS action occurred within 15 minutes. Track BMS non-responses to identify automation failures or disconnected zones. Layer in occupancy data to distinguish capacity-driven environmental issues (crowded meeting room overheating) from equipment failures (empty room overheating). Provide weekly reports to facilities management showing alert count, BMS response rate, and average response time by building zone.
- **Visualization:** Table (active alerts with BMS response status), Gauge (BMS response rate %), Line chart (daily alert count and response rate trend), Bar chart (alerts by sensor type and zone), Floor plan overlay (alert locations with severity coloring).
- **CIM Models:** N/A

- **References:** [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

---

