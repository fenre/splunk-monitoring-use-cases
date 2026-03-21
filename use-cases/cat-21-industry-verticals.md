## 21. Industry Verticals

### 21.1 Energy and Utilities

**Primary App/TA:** Splunk OT Intelligence (Splunkbase 5180), OT Security Add-on (Splunkbase 5151), Splunk Edge Hub, custom HEC inputs from SCADA/EMS/DMS systems.

**Data Sources:** SCADA alarm logs, AMI smart meter data, OMS outage records, PI historian via HEC, DNP3/IEC 104 protocol data, power quality monitors, energy trading systems.

---

### UC-21.1.1 · SCADA Alarm Rate Monitoring and Alarm Flooding Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Alarm storms mask genuine faults and exhaust operator attention; detecting flood rates and shelved alarm backlog prevents missed trips and unsafe operating conditions during grid events.
- **App/TA:** Splunk OT Intelligence, OT Security Add-on
- **Data Sources:** `index=scada` `sourcetype="scada:alarm"` (alarm_id, priority, shelved flag, substation_id)
- **SPL:**
```spl
index=scada sourcetype="scada:alarm"
| bin _time span=5m
| stats count as alarm_count, dc(alarm_id) as distinct_alarms, sum(eval(if(shelved=="true" OR shelved=="1",1,0))) as shelved_count by substation_id, _time
| eventstats avg(alarm_count) as baseline_avg, stdev(alarm_count) as baseline_stdev by substation_id
| eval z_score=if(baseline_stdev>0, (alarm_count-baseline_avg)/baseline_stdev, null)
| where alarm_count > 50 OR z_score > 3 OR shelved_count > 20
| table _time, substation_id, alarm_count, distinct_alarms, shelved_count, z_score
```
- **Implementation:** Ingest SCADA alarm events via HEC from the EMS or alarm management system; normalize shelved and priority fields in props/transforms. Schedule saved searches for 5-minute windows and route alerts to the control room. Optionally join with OT Intelligence asset context for substation names.
- **Visualization:** Line chart (alarm rate by substation), Single value (stations in flood state), Area chart (shelved alarm accumulation), Table (top substations by alarm count).
- **CIM Models:** N/A

---

### UC-21.1.2 · Substation RTU Communication Failure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** Silent RTU loss leaves operators blind to field conditions; rapid detection of polling gaps avoids delayed switching decisions and compliance exposure for unmetered assets.
- **App/TA:** Splunk Edge Hub, Splunk OT Intelligence
- **Data Sources:** `index=scada` `sourcetype="scada:rtu"` (rtu_id, poll_status, response_ms, substation_id)
- **SPL:**
```spl
index=scada sourcetype="scada:rtu"
| stats latest(_time) as last_poll, latest(poll_status) as last_status, latest(response_ms) as last_ms by rtu_id, substation_id
| eval age_sec=now()-last_poll
| where lower(last_status)!="ok" OR last_ms>5000 OR age_sec>600
| table substation_id, rtu_id, last_status, last_ms, age_sec
```
- **Implementation:** Forward RTU poll logs from the SCADA front end or protocol gateway (DNP3/IEC 104) via Edge Hub syslog or file monitor. Map poll success, timeout, and RTU identifiers. Alert when no successful poll is seen for longer than the expected scan period or when consecutive failures exceed threshold.
- **Visualization:** Status grid (RTU × health), Timeline (poll failures), Table (silent RTUs), Line chart (response time trend).
- **CIM Models:** N/A

---

### UC-21.1.3 · Smart Meter Data Gap Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Capacity
- **Value:** Missing AMI intervals skew billing determinants and load research; finding meters with systematic gaps protects revenue and supports voltage conservation programs.
- **App/TA:** Custom HEC (MDMS/AMI head-end export)
- **Data Sources:** `index=ami` `sourcetype="ami:meter"` (meter_id, read_timestamp, interval_end, kwh)
- **SPL:**
```spl
index=ami sourcetype="ami:meter"
| eval read_epoch=strptime(read_timestamp,"%Y-%m-%d %H:%M:%S")
| sort 0 meter_id, read_epoch
| streamstats current=f window=1 last(read_epoch) as prev_epoch by meter_id
| eval gap_sec=read_epoch-prev_epoch
| where isnotnull(gap_sec) AND gap_sec > 900
| stats count as gap_events, max(gap_sec) as max_gap_sec, avg(gap_sec) as avg_gap_sec by meter_id
| where gap_events>=3
| sort - gap_events
| table meter_id, gap_events, max_gap_sec, avg_gap_sec
```
- **Implementation:** Load 15-minute (or hourly) register reads from the MDMS into Splunk via HEC with consistent timestamps. Use a lookup for meter service territory if needed. Schedule daily to flag meters exceeding expected inter-read gap; integrate with work management for field verification.
- **Visualization:** Bar chart (gaps per meter), Map (if lat/long in data), Table (worst meters), Single value (meters with gaps %).
- **CIM Models:** N/A

---

### UC-21.1.4 · Power Quality Event Correlation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault
- **Value:** Voltage sags, swells, and harmonic distortion drive equipment trips and customer complaints; correlating PQ monitors with SCADA helps prioritize capacitor banks and feeder upgrades.
- **App/TA:** Splunk OT Intelligence, custom HEC (PQ analyzer)
- **Data Sources:** `index=power` `sourcetype="power:quality"` (site_id, event_type, duration_ms, v_rms, thd_pct)
- **SPL:**
```spl
index=power sourcetype="power:quality"
| where event_type IN ("sag","swell","harmonic_limit")
| bin _time span=1m
| stats count as event_count, values(event_type) as types, max(thd_pct) as max_thd, min(v_rms) as min_v, max(v_rms) as max_v by site_id, _time
| where event_count>=2 OR max_thd>8 OR min_v < 0.9*120 OR max_v > 1.1*120
| eval severity=case(max_thd>10,"high", event_count>=5,"high", true(),"medium")
| table _time, site_id, event_count, types, max_thd, min_v, max_v, severity
```
- **Implementation:** Stream PQ event records from fixed analyzers or smart relays through HEC; normalize nominal voltage per site via lookup. Use transactions or `stats` by feeder if `feeder_id` is present. Dashboard overlays with SCADA breaker operations for root-cause sessions.
- **Visualization:** Timeline (PQ events), Line chart (THD and RMS by site), Heatmap (site × hour event count), Table (severe events).
- **CIM Models:** N/A

---

### UC-21.1.5 · Renewable Generation Forecast vs Actual Deviation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** Forecast error increases imbalance costs and reserve deployment; tracking solar and wind deltas supports trading desks and dispatch in markets with renewable penetration.
- **App/TA:** Splunk OT Intelligence, PI historian HEC
- **Data Sources:** `index=generation` `sourcetype="pi:historian"` (asset_id, mw_actual, mw_forecast, fuel_type)
- **SPL:**
```spl
index=generation sourcetype="pi:historian" fuel_type IN ("solar","wind")
| eval delta_mw=mw_actual-mw_forecast, abs_error_mw=abs(delta_mw), pct_error=if(mw_forecast!=0 AND abs(mw_forecast)>0.01, 100*delta_mw/mw_forecast, null)
| bin _time span=1h
| stats avg(mw_actual) as avg_actual, avg(mw_forecast) as avg_fcst, avg(abs_error_mw) as mae_mw, stdev(delta_mw) as delta_stdev by asset_id, fuel_type, _time
| eval mape_pct=if(avg_fcst!=0, 100*mae_mw/abs(avg_fcst), null)
| where mape_pct>15 OR mae_mw>5
| table _time, asset_id, fuel_type, avg_actual, avg_fcst, mae_mw, mape_pct
```
- **Implementation:** Ingest both forecast (day-ahead or hour-ahead) and telemetered MW from PI or EMS via HEC with aligned timestamps. Tag fuel type for filtering. Alert when MAPE or absolute error exceeds trading/risk thresholds; feed back to forecasting vendor with Splunk export.
- **Visualization:** Line chart (forecast vs actual), Area chart (error envelope), Bar chart (MAPE by plant), Single value (portfolio forecast error).
- **CIM Models:** N/A

---

### UC-21.1.6 · Distribution Feeder Load Imbalance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Phase imbalance causes neutral current, transformer heating, and voltage quality issues; early detection guides switching operations and load redistribution on rural feeders.
- **App/TA:** Splunk Edge Hub, PI historian HEC
- **Data Sources:** `index=scada` `sourcetype="pi:historian"` (feeder_id, ia_amps, ib_amps, ic_amps)
- **SPL:**
```spl
index=scada sourcetype="pi:historian"
| eval avg_phase=(ia_amps+ib_amps+ic_amps)/3
| eval max_i=max(ia_amps, ib_amps, ic_amps), min_i=min(ia_amps, ib_amps, ic_amps)
| eval imbalance_pct=if(avg_phase>0, 100*(max_i-min_i)/avg_phase, null)
| where imbalance_pct>10
| bin _time span=15m
| stats max(imbalance_pct) as peak_imbalance_pct, latest(ia_amps) as ia, latest(ib_amps) as ib, latest(ic_amps) as ic by feeder_id, _time
| table _time, feeder_id, peak_imbalance_pct, ia, ib, ic
```
- **Implementation:** Ingest per-phase current from DMS or AMI aggregation via historian tags mapped to feeder IDs. Schedule near-real-time checks during peak load. Combine with OMS for customer complaints on the same feeder. Use lookups for feeder voltage class and limits.
- **Visualization:** Line chart (imbalance % over time), Bar chart (feeders over threshold), Gauge (worst feeder imbalance), Table (phase currents).
- **CIM Models:** N/A

---

### UC-21.1.7 · Transformer Dissolved Gas Analysis (DGA) Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Compliance
- **Value:** Rising H₂, CH₄, and C₂H₂ indicate insulation breakdown; trending DGA against IEEE/IEC limits prioritizes transformer replacement and avoids in-service failures.
- **App/TA:** Custom HEC (lab LIMS / asset management)
- **Data Sources:** `index=assets` `sourcetype="pi:historian"` (transformer_id, h2_ppm, ch4_ppm, c2h2_ppm, sample_date)
- **SPL:**
```spl
index=assets sourcetype="pi:historian"
| eval sample_epoch=if(isnotnull(sample_date), strptime(sample_date,"%Y-%m-%d"), _time)
| sort 0 transformer_id, sample_epoch
| streamstats current=f window=1 last(ch4_ppm) as prev_ch4 last(h2_ppm) as prev_h2 by transformer_id
| eval ch4_rate=if(isnotnull(prev_ch4), ch4_ppm-prev_ch4, null)
| where ch4_ppm>100 OR c2h2_ppm>1 OR h2_ppm>500 OR ch4_rate>50
| stats latest(ch4_ppm) as ch4, latest(c2h2_ppm) as c2h2, latest(h2_ppm) as h2, latest(ch4_rate) as ch4_delta by transformer_id
| sort - ch4
| table transformer_id, ch4, c2h2, h2, ch4_delta
```
- **Implementation:** Load lab DGA results via HEC from LIMS or manual CSV ingestion; align `sample_date` with asset IDs. Maintain lookup tables for IEEE/IEC thresholds by oil type if required. Quarterly dashboards for reliability planning; alerts on sudden gas generation rates.
- **Visualization:** Line chart (gas PPM trends per transformer), Table (units exceeding limits), Scatter (CH₄ vs C₂H₂), Single value (transformers in alert).
- **CIM Models:** N/A

---

### UC-21.1.8 · Generator Trip Event Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault, Availability
- **Value:** Linking generator trips to relay targets and SCADA analogs shortens root-cause analysis and supports NERC event reporting with defensible timelines.
- **App/TA:** Splunk OT Intelligence, OT Security Add-on
- **Data Sources:** `index=scada` `sourcetype="scada:alarm"` OR `sourcetype="scada:rtu"` (unit_id, trip, relay_element, mw, hz)
- **SPL:**
```spl
index=scada sourcetype="scada:alarm" (match(_raw,"(?i)trip|generator"))
| bin _time span=1m
| stats values(relay_element) as relays by unit_id, _time
| join type=left unit_id _time [
    search index=scada sourcetype="scada:rtu"
    | bin _time span=1m
    | stats avg(mw) as mw_at_event, avg(hz) as hz_at_event by unit_id, _time
]
| eval trip_time=strftime(_time,"%Y-%m-%d %H:%M:%S")
| table unit_id, trip_time, relays, mw_at_event, hz_at_event
```
- **Implementation:** Normalize unit and breaker IDs across alarm and RTU streams. Prefer `transaction` or `stats` with `maxspan=120s` on `unit_id` if join cardinality is high. Store NERC reportable fields in summary indexing for audit. Edge Hub can timestamp-align IEC 61850 GOOSE if available.
- **Visualization:** Timeline (trip and relay sequence), Table (correlated events), Line chart (MW and Hz around trip), Sankey (optional cause paths).
- **CIM Models:** N/A

---

### UC-21.1.9 · Energy Trading Position Reconciliation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Change
- **Value:** Position mismatches against ISO settlement expose mark-to-market errors and credit risk; automated reconciliation catches booking and tag errors before invoice disputes.
- **App/TA:** Custom HEC (ETRM / settlement system)
- **Data Sources:** `index=trading` `sourcetype="energy:trade"` (trade_id, product, mw, side, position_internal, position_settlement, trade_date)
- **SPL:**
```spl
index=trading sourcetype="energy:trade"
| eval diff_mw=abs(position_internal-position_settlement)
| where diff_mw>0.1
| stats sum(diff_mw) as total_abs_diff_mw, count as mismatch_trades, values(trade_id) as trade_ids by product, trade_date
| sort - total_abs_diff_mw
| table trade_date, product, mismatch_trades, total_abs_diff_mw, trade_ids
```
- **Implementation:** Ingest internal ETRM positions and ISO/utility settlement extracts on the same schedule via HEC. Use lookups for product naming alignment. Alert on any non-zero difference above tolerance; restrict dashboards to trading operations roles.
- **Visualization:** Table (mismatches by product), Bar chart (diff MW by day), Single value (open reconciliation count), Line chart (reconciliation trend).
- **CIM Models:** N/A

---

### UC-21.1.10 · AMI Mesh Network Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Mesh degradation increases latency and packet loss for critical reads and firmware campaigns; proactive node health reduces truck rolls and extends network life.
- **App/TA:** Custom HEC (RF mesh head-end)
- **Data Sources:** `index=ami` `sourcetype="ami:mesh"` (node_id, parent_id, rssi_dbm, hop_count, latency_ms, online)
- **SPL:**
```spl
index=ami sourcetype="ami:mesh"
| where online="false" OR latency_ms>2000 OR hop_count>8 OR rssi_dbm<-115
| bin _time span=15m
| stats dc(node_id) as degraded_nodes, avg(latency_ms) as avg_latency, avg(rssi_dbm) as avg_rssi by parent_id, _time
| where degraded_nodes>=5 OR avg_latency>800
| table _time, parent_id, degraded_nodes, avg_latency, avg_rssi
```
- **Implementation:** Export mesh diagnostics from the RF network manager via scheduled JSON to HEC. Baseline RSSI and hop count per region. Alert on concentration of offline nodes under a collector; map to GIS if coordinates are loaded as lookup.
- **Visualization:** Network graph (optional with app), Table (degraded parents), Heatmap (hour × region latency), Line chart (average hops).
- **CIM Models:** N/A

---

### UC-21.1.11 · Demand Response Event Compliance Verification
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Performance
- **Value:** Program penalties apply when committed load reductions are not achieved; verifying kW response against baselines protects program revenue and customer satisfaction.
- **App/TA:** Custom HEC (DRMS / DERMS)
- **Data Sources:** `index=dr` `sourcetype="dr:event"` (program_id, site_id, event_start, event_end, baseline_kw, actual_kw)
- **SPL:**
```spl
index=dr sourcetype="dr:event"
| eval achieved_reduction_kw=baseline_kw-actual_kw
| eval compliance_pct=if(baseline_kw>0, 100*achieved_reduction_kw/baseline_kw, null)
| where achieved_reduction_kw < 0 OR compliance_pct < 80
| stats min(compliance_pct) as min_compliance_pct, avg(achieved_reduction_kw) as avg_reduction_kw by program_id, site_id
| table program_id, site_id, min_compliance_pct, avg_reduction_kw
```
- **Implementation:** Ingest DR event windows and interval load from MDMS or AMI aggregated by site. Align timestamps to local timezone of the program. Use summary indexing for monthly compliance scorecards. HEC from DRMS for event definitions is preferred over manual CSV.
- **Visualization:** Bar chart (compliance % by program), Table (non-compliant sites), Line chart (load during event), Gauge (portfolio compliance).
- **CIM Models:** N/A

---

### UC-21.1.12 · Outage Management System vs SCADA State Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault, Change
- **Value:** Disconnected OMS tickets and energized SCADA devices delay restoration and confuse customers; alignment checks improve switching safety and SAIDI/SAIFI reporting quality.
- **App/TA:** Splunk OT Intelligence, custom HEC (OMS)
- **Data Sources:** `index=oms` `sourcetype="oms:outage"` (device_id, status), `index=scada` `sourcetype="scada:alarm"` or `sourcetype="scada:rtu"` (device_id, breaker_state)
- **SPL:**
```spl
index=oms sourcetype="oms:outage" status="open"
| fields device_id, _time, outage_id
| join type=inner device_id [
    search index=scada (sourcetype="scada:rtu" OR sourcetype="scada:alarm")
    | eval breaker_state=coalesce(breaker_state, device_state)
    | where lower(breaker_state) IN ("closed","energized","1")
    | stats latest(breaker_state) as scada_state by device_id
]
| table outage_id, device_id, scada_state
```
- **Implementation:** Maintain a canonical `device_id` lookup between OMS and SCADA naming. Schedule frequent correlation; handle multiphase devices with MVLV mapping table. Alert ETRM/OMS when mismatches exceed zero for active outages. Use Edge Hub only for SCADA side if needed.
- **Visualization:** Table (mismatched devices), Single value (mismatch count), Timeline (OMS vs SCADA changes), Map (optional).
- **CIM Models:** N/A

---

### UC-21.1.13 · Vegetation Management Work Order Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Fault
- **Value:** Unexecuted clearance work correlates with repeat outages; tying work orders to feeder outage history prioritizes trims and documents regulatory readiness.
- **App/TA:** Custom HEC (GIS / work management)
- **Data Sources:** `index=oms` `sourcetype="oms:outage"` (feeder_id, outage_cause, work_order_id, work_type, completed_date)
- **SPL:**
```spl
index=oms sourcetype="oms:outage"
| where work_type="vegetation" OR match(lower(outage_cause),"veg|tree|limb")
| eval completed=if(isnotnull(completed_date) AND completed_date!="",1,0)
| stats count as related_events, sum(completed) as completed_orders, dc(feeder_id) as feeders_affected by work_order_id
| eval completion_rate=if(related_events>0, 100*completed_orders/related_events, 0)
| where completed_orders < related_events
| table work_order_id, related_events, completed_orders, feeders_affected, completion_rate
```
- **Implementation:** Ingest vegetation work orders and outage records with shared feeder and span identifiers via HEC from the enterprise work system. Use lookups for span-to-feeder if needed. Monthly reporting for regulatory vegetation cycles; optional join with `fleet:gps` for crew verification.
- **Visualization:** Table (open vegetation orders), Bar chart (outages vs completed trims by feeder), Timeline (work order lifecycle), Map (feeder segments).
- **CIM Models:** N/A

---

### UC-21.1.14 · Utility Fleet GPS and Dispatch Optimization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** During storms, knowing crew proximity to open tickets reduces travel time and improves ETR accuracy for public communications and mutual aid billing.
- **App/TA:** Custom HEC (AVL / dispatch)
- **Data Sources:** `index=fleet` `sourcetype="fleet:gps"` (vehicle_id, crew_id, lat, lon, speed_mph, ticket_id)
- **SPL:**
```spl
index=fleet sourcetype="fleet:gps"
| eval gps_missing=if(isnull(lat) OR isnull(lon),1,0), speed_anomaly=if(speed_mph>85,1,0)
| where gps_missing=1 OR speed_anomaly=1
| bin _time span=1h
| stats sum(gps_missing) as missing_reports, sum(speed_anomaly) as speed_flags by vehicle_id, crew_id, _time
| eval issues=missing_reports+speed_flags
| where issues>=3
| table _time, vehicle_id, crew_id, missing_reports, speed_flags, issues
```
- **Implementation:** Stream AVL points from telematics vendor to HEC with API key authentication. Join to open OMS tickets in a separate search or data model for dispatch boards. Alert on GPS gaps during active storm windows. Respect privacy policies for off-duty masking if required.
- **Visualization:** Map (vehicle positions), Table (crews with stale GPS), Line chart (fleet utilization), Bar chart (response time by district).
- **CIM Models:** N/A

---

### UC-21.1.15 · Customer Billing Exception Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Fault
- **Value:** Estimated reads and bill spikes drive complaints and regulatory inquiries; catching exceptions before invoice release protects customer trust and reduces rework.
- **App/TA:** Custom HEC (CIS/billing)
- **Data Sources:** `index=billing` `sourcetype="billing:exception"` (account_id, bill_cycle, read_type, variance_pct, amount_due, flag_estimated)
- **SPL:**
```spl
index=billing sourcetype="billing:exception"
| eval estimated=if(lower(flag_estimated) IN ("true","1","y"),1,0)
| where estimated=1 OR abs(variance_pct)>30 OR amount_due>10000
| stats count as exception_count, sum(amount_due) as total_at_risk by bill_cycle, read_type
| sort - exception_count
| table bill_cycle, read_type, exception_count, total_at_risk
```
- **Implementation:** CIS exports exception flags and variance versus prior period to Splunk nightly via HEC. Join AMI gap detection (UC-21.1.3) for upstream cause analysis. Route alerts to billing operations before print/mail. Mask PII in dashboards using Splunk field filters or role-based search filters.
- **Visualization:** Bar chart (exceptions by cycle), Table (top accounts — masked), Line chart (estimated read rate trend), Single value (exceptions pending review).
- **CIM Models:** N/A

---

### 21.2 Manufacturing and Process Industry

**Primary App/TA:** Splunk OT Intelligence (Splunkbase 5180), Splunk Edge Hub, custom HEC inputs from MES/ERP/SCADA systems.

**Data Sources:** OPC-UA tags via Edge Hub/OTI, MES production logs, ERP event logs, quality management system, CMMS work orders, energy meters.

---

### UC-21.2.1 · Overall Equipment Effectiveness (OEE) Calculation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** OEE exposes hidden capacity losses across availability, speed, and quality; plant leadership uses it to prioritize capital and lean projects on the constraint line.
- **App/TA:** Splunk OT Intelligence, Splunk Edge Hub
- **Data Sources:** `index=mfg` `sourcetype="mes:production"` (line_id, planned_time_min, run_time_min, ideal_cycle_sec, units_good, units_total)
- **SPL:**
```spl
index=mfg sourcetype="mes:production"
| eval availability=if(planned_time_min>0, run_time_min/planned_time_min, null)
| eval performance=if(run_time_min>0 AND ideal_cycle_sec>0 AND units_total>0, (units_total*ideal_cycle_sec/60)/run_time_min, null)
| eval quality=if(units_total>0, units_good/units_total, null)
| eval oee=availability*performance*quality
| bin _time span=1h
| stats avg(availability) as avg_a, avg(performance) as avg_p, avg(quality) as avg_q, avg(oee) as avg_oee by line_id, _time
| where avg_oee < 0.65 OR avg_a < 0.9 OR avg_q < 0.95
| table _time, line_id, avg_a, avg_p, avg_q, avg_oee
```
- **Implementation:** Ingest MES counters from each line via HEC; validate ideal cycle time from routing master data lookup. Edge Hub can supply machine states if MES gaps exist. Schedule hourly OEE and daily rollups for plant reviews.
- **Visualization:** Line chart (OEE trend), Breakdown bar (A, P, Q), Table (line ranking), Single value (plant OEE).
- **CIM Models:** N/A

---

### UC-21.2.2 · Unplanned Downtime Root Cause Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault, Availability
- **Value:** Shortening mean time to repair for unplanned stops protects customer OTIF; correlating alarms, work orders, and environmental data speeds RCA across shifts.
- **App/TA:** Splunk OT Intelligence, CMMS integration
- **Data Sources:** `index=mfg` `sourcetype="mes:production"` (line_id, state), `index=mfg` `sourcetype="cmms:workorder"` (asset_id, wo_id, priority), `index=ot` `sourcetype="opc:tag"` (asset_id, alarm_text)
- **SPL:**
```spl
(index=mfg sourcetype="mes:production" state="down") OR (index=mfg sourcetype="cmms:workorder" priority="emergency") OR (index=ot sourcetype="opc:tag" match(alarm_text,"(?i)fault|alarm|trip"))
| eval key=coalesce(line_id, asset_id)
| transaction key maxspan=30m maxevents=50
| eval duration_sec=duration
| where duration_sec>60
| table _time, key, duration_sec, state, wo_id, alarm_text
```
- **Implementation:** Normalize asset and line keys across MES, CMMS, and OPC-UA. Use `transaction` or `stats` with `maxspan` tuned to line stop characteristics. Ingest OPC alarms via Edge Hub. Store exemplar searches in OT Intelligence workbench for engineers.
- **Visualization:** Timeline (downtime episodes), Table (correlated WO and alarms), Sankey (cause categories), Bar chart (duration by line).
- **CIM Models:** N/A

---

### UC-21.2.3 · Production Batch Yield Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Batch yield ties material usage to quality outcomes; sustained loss trends trigger recipe or supplier investigations before customer rejects accumulate.
- **App/TA:** Custom HEC (MES)
- **Data Sources:** `index=mfg` `sourcetype="mes:production"` (batch_id, sku, input_kg, good_kg, scrap_kg)
- **SPL:**
```spl
index=mfg sourcetype="mes:production"
| eval yield_pct=if((good_kg+scrap_kg)>0, 100*good_kg/(good_kg+scrap_kg), null), loss_pct=100-yield_pct
| bin _time span=1d
| stats avg(yield_pct) as avg_yield, stdev(yield_pct) as yield_jitter by sku, batch_id, _time
| eventstats median(avg_yield) as sku_median by sku
| where avg_yield < sku_median*0.95 OR yield_jitter>5
| table _time, sku, batch_id, avg_yield, sku_median, yield_jitter
```
- **Implementation:** MES batch completion records to HEC with weights from scales integrated via OPC if needed. Maintain golden batch yield per SKU in a lookup for static targets. Alert on statistically significant drops; integrate with QMS for hold codes.
- **Visualization:** Line chart (yield by batch), Bar chart (yield by SKU), Table (worst batches), Control chart (yield with limits).
- **CIM Models:** N/A

---

### UC-21.2.4 · Quality SPC Chart Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Performance
- **Value:** Western Electric rules catch process shifts before out-of-spec product is made, supporting ISO 9001 and automotive PPAP evidence.
- **App/TA:** Custom HEC (QMS/LIMS)
- **Data Sources:** `index=quality` `sourcetype="qms:inspection"` (part_id, characteristic, measured_value, lsl, usl)
- **SPL:**
```spl
index=quality sourcetype="qms:inspection"
| sort 0 part_id, characteristic, _time
| streamstats window=20 global=f avg(measured_value) as ma20, stdev(measured_value) as ms20 by part_id, characteristic
| eval rule1=if(measured_value>usl OR measured_value<lsl,1,0)
| eval rule2=if(ms20>0 AND (measured_value > ma20+3*ms20 OR measured_value < ma20-3*ms20),1,0)
| where rule1=1 OR rule2=1
| table _time, part_id, characteristic, measured_value, lsl, usl, ma20, ms20, rule1, rule2
```
- **Implementation:** Stream inspection measurements from CMM or inline gauges via QMS API to HEC. Tune window (e.g., 20 subgroups) per characteristic. Alert quality engineers on rule breaches; archive results for audit. Optional `predict` for advanced drift on stable lines.
- **Visualization:** Control chart (X-bar style), Table (rule violations), Line chart (measurement trend), Heatmap (characteristic × line).
- **CIM Models:** N/A

---

### UC-21.2.5 · Predictive Maintenance Vibration Baseline Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance
- **Value:** Rising RMS velocity or envelope demodulation on rotating assets precedes bearing failure; early warning avoids unplanned line stops and secondary damage.
- **App/TA:** Splunk Edge Hub, Splunk OT Intelligence
- **Data Sources:** `index=ot` `sourcetype="opc:tag"` (asset_id, vibration_rms, temperature_c)
- **SPL:**
```spl
index=ot sourcetype="opc:tag"
| bin _time span=5m
| stats avg(vibration_rms) as v_rms, avg(temperature_c) as temp by asset_id, _time
| sort 0 asset_id, _time
| streamstats window=288 global=f avg(v_rms) as baseline_v, stdev(v_rms) as baseline_sd by asset_id
| eval z=if(baseline_sd>0, (v_rms-baseline_v)/baseline_sd, null)
| where z>3 OR v_rms>7.1 OR temp>85
| table _time, asset_id, v_rms, baseline_v, z, temp
```
- **Implementation:** Sample vibration tags from Edge Hub OPC-UA at 1 Hz aggregated to 5-minute RMS in Splunk or at the edge. Establish baselines per asset with seasonal retuning. Integrate CMMS to auto-create work orders when z-score exceeds policy.
- **Visualization:** Line chart (RMS vs baseline), Heatmap (asset × week), Table (assets in alert), Gauge (worst z-score).
- **CIM Models:** N/A

---

### UC-21.2.6 · Energy Consumption Per Unit Produced
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Specific energy consumption (kWh per unit) links sustainability KPIs to operations; spikes reveal compressed air leaks, idle equipment, or recipe drift.
- **App/TA:** Splunk Edge Hub (energy meters), MES HEC
- **Data Sources:** `index=mfg` `sourcetype="energy:meter"` (line_id, kwh), `sourcetype="mes:production"` (line_id, units_good)
- **SPL:**
```spl
index=mfg (sourcetype="energy:meter" OR sourcetype="mes:production")
| bin _time span=1h
| stats sum(kwh) as kwh by line_id, _time
| join type=inner line_id _time [
    search index=mfg sourcetype="mes:production"
    | bin _time span=1h
    | stats sum(units_good) as units by line_id, _time
]
| eval sec_kwh=if(units>0, kwh/units, null)
| where sec_kwh>0
| eventstats median(sec_kwh) as med_sec by line_id
| where sec_kwh > med_sec*1.15
| table _time, line_id, kwh, units, sec_kwh, med_sec
```
- **Implementation:** Align meter rollups to MES production intervals using common `line_id` and time bucketing. Calibrate meters annually and store correction factors in lookup. Dashboard SEC for sustainability reporting and cost per unit.
- **Visualization:** Line chart (SEC trend), Bar chart (SEC by line), Table (outliers), Single value (plant kWh per unit).
- **CIM Models:** N/A

---

### UC-21.2.7 · MES Order Completion Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Stalled manufacturing orders threaten delivery dates and WIP cash; milestone visibility enables planner intervention before the constraint is starved.
- **App/TA:** Custom HEC (MES)
- **Data Sources:** `index=mfg` `sourcetype="mes:production"` (order_id, sku, milestone, status, due_date)
- **SPL:**
```spl
index=mfg sourcetype="mes:production"
| eval due_epoch=strptime(due_date,"%Y-%m-%d")
| eval late_risk=if(lower(status)!="complete" AND _time>due_epoch-86400,1,0)
| where late_risk=1 OR lower(status) IN ("held","blocked")
| stats latest(status) as status, latest(milestone) as milestone, min(due_epoch) as due by order_id, sku
| sort due
| table order_id, sku, milestone, status, due
```
- **Implementation:** Ingest order status transitions from MES via HEC with full milestone model. Join to ERP promise date if synced through nightly batch. Alert planners when orders approach due window without final completion event.
- **Visualization:** Gantt-style table (milestones), Bar chart (orders by status), Timeline (order events), Single value (orders at risk).
- **CIM Models:** N/A

---

### UC-21.2.8 · Supply Chain EDI Message Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** AS2/EDI failures delay ASNs and invoices, disrupting JIT lines and payment cycles; monitoring failure rates protects supplier scorecards and customer OTIF.
- **App/TA:** Custom HEC (B2B gateway)
- **Data Sources:** `index=edi` `sourcetype="edi:message"` (partner_id, direction, status, message_type, mdn_status)
- **SPL:**
```spl
index=edi sourcetype="edi:message"
| eval ok=if(lower(status)="success" AND (isnull(mdn_status) OR lower(mdn_status)="processed"),1,0)
| bin _time span=1h
| stats count as total, sum(eval(if(ok=0,1,0))) as fail by partner_id, message_type, _time
| eval fail_rate=if(total>0, 100*fail/total, null)
| where fail_rate>2 OR fail>10
| table _time, partner_id, message_type, total, fail, fail_rate
```
- **Implementation:** Export gateway logs with MDN and ACK status to HEC; mask payload content. Per-partner SLOs in lookup table. Page integrations team when failure rate exceeds threshold for two consecutive intervals.
- **Visualization:** Line chart (failure rate by partner), Table (top failing partners), Bar chart (failures by message type), Single value (global EDI health).
- **CIM Models:** N/A

---

### UC-21.2.9 · Bill of Materials (BOM) Discrepancy Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Change
- **Value:** Wrong component consumption breaks costing and traceability; catching BOM mismatches early avoids recalls and ERP reconciliation fire drills.
- **App/TA:** ERP HEC, MES integration
- **Data Sources:** `index=erp` `sourcetype="erp:event"` (order_id, material_id, qty_planned), `index=mfg` `sourcetype="mes:production"` (order_id, material_id, qty_consumed)
- **SPL:**
```spl
index=erp sourcetype="erp:event" event_type="bom"
| rename qty_planned as qty_plan
| join type=outer order_id material_id [
    search index=mfg sourcetype="mes:production"
    | stats sum(qty_consumed) as qty_cons by order_id, material_id
]
| fillnull value=0 qty_cons
| eval delta=qty_plan-qty_cons
| where abs(delta)>0.5*qty_plan OR abs(delta)>5
| table order_id, material_id, qty_plan, qty_cons, delta
```
- **Implementation:** Publish planned BOM lines from ERP and consumption from MES on shared keys. Schedule hourly reconciliation; handle unit of measure conversion via lookup. Route discrepancies to production control before period close.
- **Visualization:** Table (BOM variances), Bar chart (variance by material), Line chart (discrepancy count over time), Heatmap (SKU × material).
- **CIM Models:** N/A

---

### UC-21.2.10 · Warehouse Pick-Pack-Ship Cycle Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Long cycle times miss carrier cutoffs and inflate labor cost; SLA dashboards drive slotting and staffing decisions in peak seasons.
- **App/TA:** Custom HEC (WMS)
- **Data Sources:** `index=wms` `sourcetype="wms:order"` (order_id, pick_start, pack_end, ship_confirm, sla_minutes)
- **SPL:**
```spl
index=wms sourcetype="wms:order"
| eval pick_epoch=strptime(pick_start,"%Y-%m-%d %H:%M:%S"), ship_epoch=strptime(ship_confirm,"%Y-%m-%d %H:%M:%S")
| eval cycle_min=(ship_epoch-pick_epoch)/60
| where cycle_min > sla_minutes OR isnull(ship_confirm)
| stats avg(cycle_min) as avg_cycle, perc95(cycle_min) as p95_cycle, count as breach_count by order_id
| sort - breach_count
| table order_id, avg_cycle, p95_cycle, sla_minutes, breach_count
```
- **Implementation:** WMS event stream to HEC with timestamps at pick, pack, and ship scan. Define SLA per customer tier in lookup. Real-time panel for operations; weekly review of p95 versus staffing model.
- **Visualization:** Histogram (cycle time distribution), Line chart (p95 trend), Table (orders breaching SLA), Bar chart (breaches by dock).
- **CIM Models:** N/A

---

### UC-21.2.11 · Robotic Cell Cycle Time Deviation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Drift from takt-time signals tooling wear or program changes; catching deviation early avoids quality escapes and unplanned maintenance.
- **App/TA:** Splunk OT Intelligence, robot controller HEC
- **Data Sources:** `index=mfg` `sourcetype="robot:cycle"` (cell_id, program_id, cycle_sec, target_sec)
- **SPL:**
```spl
index=mfg sourcetype="robot:cycle"
| eval delta_sec=cycle_sec-target_sec, delta_pct=if(target_sec>0, 100*delta_sec/target_sec, null)
| bin _time span=15m
| stats avg(cycle_sec) as avg_cycle, avg(target_sec) as avg_target, stdev(cycle_sec) as cycle_jitter by cell_id, program_id, _time
| eval avg_delta_pct=if(avg_target>0, 100*(avg_cycle-avg_target)/avg_target, null)
| where avg_delta_pct>10 OR cycle_jitter>3
| table _time, cell_id, program_id, avg_cycle, avg_target, avg_delta_pct, cycle_jitter
```
- **Implementation:** Ingest cycle completion messages from robot OEM or PLC via Edge Hub syslog. Baseline `target_sec` per program revision in lookup when recipes change. Alert maintenance when sustained positive delta exceeds policy.
- **Visualization:** Line chart (cycle time vs target), Control chart, Table (cells in deviation), Bar chart (delta by program).
- **CIM Models:** N/A

---

### UC-21.2.12 · Conveyor Belt Speed and Jam Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Belt slowdowns and jams starve downstream stations and can damage product; fast detection limits cascade stops across the line.
- **App/TA:** Splunk Edge Hub
- **Data Sources:** `index=ot` `sourcetype="conveyor:sensor"` (line_id, belt_id, speed_fpm, motor_amps, jam_sensor)
- **SPL:**
```spl
index=ot sourcetype="conveyor:sensor"
| eval jam=if(lower(jam_sensor)="true" OR jam_sensor="1",1,0)
| bin _time span=1m
| stats avg(speed_fpm) as avg_speed, avg(motor_amps) as avg_amps, max(jam) as jam_flag by line_id, belt_id, _time
| where avg_speed < 10 OR jam_flag=1 OR avg_amps>25
| table _time, line_id, belt_id, avg_speed, avg_amps, jam_flag
```
- **Implementation:** Map photo-eye, encoder, and VFD feedback through OPC-UA into Edge Hub with 1-second sampling aggregated in Splunk. Set nominal speed per SKU from MES lookup if variable. Tie jam events to video timestamp if optional stream metadata is ingested.
- **Visualization:** Line chart (speed and amps), Status timeline (jam), Table (active issues), Single value (lines stopped).
- **CIM Models:** N/A

---

### UC-21.2.13 · Compressed Air System Leak Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Performance
- **Value:** Air leaks are a top energy waste in plants; abnormal specific power (kW per 100 cfm) during non-production indicates leakage or control issues.
- **App/TA:** Splunk Edge Hub, energy analytics
- **Data Sources:** `index=mfg` `sourcetype="air:compressor"` (plant_id, kw, cfm, run_state), `sourcetype="mes:production"` (plant_id, line_state)
- **SPL:**
```spl
index=mfg sourcetype="air:compressor"
| bin _time span=15m
| stats avg(kw) as avg_kw, avg(cfm) as avg_cfm, max(run_state) as run_state by plant_id, _time
| join type=left plant_id _time [
    search index=mfg sourcetype="mes:production"
    | bin _time span=15m
    | stats sum(units_good) as units by line_id, _time
    | rename line_id as plant_id
]
| eval idle_compressor=if(lower(run_state)="on" AND (isnull(units) OR units=0),1,0)
| eval specific_kw=if(avg_cfm>20, avg_kw/(avg_cfm/100), null)
| where idle_compressor=1 AND specific_kw>22
| table _time, plant_id, avg_kw, avg_cfm, specific_kw, units
```
- **Implementation:** Instrument compressors with power and flow meters; infer non-production from MES aggregate line state. Baseline specific power during known good weekends after leak surveys. Alert facilities when idle load exceeds threshold; track savings from repair campaigns.
- **Visualization:** Line chart (specific power trend), Bar chart (plant comparison), Table (suspect compressors), Single value (estimated wasted kW).
- **CIM Models:** N/A

---

### UC-21.2.14 · Clean-in-Place (CIP) Cycle Validation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Fault
- **Value:** Incomplete CIP risks product contamination and regulatory findings; verifying flow, temperature, and chemical concentration against the recipe protects brand and batch release.
- **App/TA:** Splunk OT Intelligence, Splunk Edge Hub
- **Data Sources:** `index=mfg` `sourcetype="cip:cycle"` (skid_id, step, flow_lpm, temp_c, conductivity_ms, duration_sec, recipe_id)
- **SPL:**
```spl
index=mfg sourcetype="cip:cycle"
| eval flow_ok=if(flow_lpm>=30 AND flow_lpm<=80,1,0), temp_ok=if(temp_c>=70 AND temp_c<=85,1,0), chem_ok=if(conductivity_ms>=1.2,1,0)
| eval step_pass=flow_ok*temp_ok*chem_ok
| stats min(step_pass) as cycle_pass, sum(duration_sec) as total_duration by skid_id, recipe_id, _time
| where cycle_pass=0 OR total_duration < 600 OR total_duration > 7200
| table _time, skid_id, recipe_id, cycle_pass, total_duration
```
- **Implementation:** Ingest skid PLC tags via Edge Hub with one event per step or minute rollups. Store recipe limits in lookup keyed by `recipe_id` and `step`. Electronic batch records can consume Splunk alerts for QA hold. Retain data for audit trail per 21 CFR Part 11 policy if applicable.
- **Visualization:** Timeline (CIP steps), Table (failed cycles), Line chart (temperature and conductivity), Gauge (cycle compliance %).
- **CIM Models:** N/A

---

### UC-21.2.15 · Production Shift Handover Report Generation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Change
- **Value:** Consistent shift reports reduce tacit knowledge loss and accelerate startup; KPI rollups improve accountability across crews on 24/7 lines.
- **App/TA:** Splunk OT Intelligence, MES HEC
- **Data Sources:** `index=mfg` `sourcetype="mes:production"` (line_id, units_good, downtime_min, scrap_units, shift_id)
- **SPL:**
```spl
index=mfg sourcetype="mes:production"
| eval shift=case(hour(_time)>=6 AND hour(_time)<14,"A", hour(_time)>=14 AND hour(_time)<22,"B", true(),"C")
| bin _time span=8h aligntime=@d+6h
| stats sum(units_good) as units, sum(downtime_min) as down_m, sum(scrap_units) as scrap by line_id, shift, _time
| eval scrap_rate=if(units+scrap>0, 100*scrap/(units+scrap), null)
| sort _time, line_id, shift
| table _time, line_id, shift, units, down_m, scrap, scrap_rate
```
- **Implementation:** Schedule a saved search at shift change to email PDF or post to Teams via alert action. Pull `shift_id` from MES when available instead of inferred buckets. Optional append subsearch for top downtime reasons from OPC alarms. Store outputs in summary index for trend comparison.
- **Visualization:** Table (shift KPI summary), Column chart (units by shift), Line chart (scrap rate trend), Single value (plant output per shift).
- **CIM Models:** N/A

---

### 21.3 Healthcare and Life Sciences

**Primary App/TA:** Custom HEC inputs from EHR systems (Epic, Cerner), HL7 interface engines, DICOM gateways, environmental monitoring (MQTT/Edge Hub), pharmacy systems, lab information systems.

**Data Sources:** EHR audit logs, HL7 v2 interface engine logs, DICOM DIMSE logs, environmental monitoring sensors, pharmacy system logs, LIS results, CMMS biomedical equipment records.

---

### UC-21.3.1 · EHR System Response Time Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow EHR response times directly impact clinical workflow and patient safety. Monitoring response latency enables proactive intervention before clinicians experience degradation.
- **App/TA:** Epic Hyperspace / Cerner application performance logs via HEC
- **Data Sources:** `index=healthcare` `sourcetype="ehr:audit"` fields `response_time_ms`, `transaction_type`, `server_node`
- **SPL:**
```spl
index=healthcare sourcetype="ehr:audit"
| bin _time span=5m
| stats avg(response_time_ms) as avg_rt, perc95(response_time_ms) as p95_rt, count by server_node, _time
| where p95_rt > 3000
| table _time, server_node, avg_rt, p95_rt, count
```
- **Implementation:** Ingest EHR application performance logs via HEC. Set thresholds based on clinical workflow requirements (typically p95 < 3 seconds). Alert on sustained degradation and correlate with infrastructure metrics.
- **Visualization:** Line chart (p95 response time by server), Heatmap (server × time), Single value (current p95).
- **CIM Models:** N/A

---

### UC-21.3.2 · Clinical Application Uptime SLA Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Clinical applications require 99.9%+ uptime for patient care continuity. Tracking SLA compliance ensures service-level commitments are met and documented.
- **App/TA:** Synthetic monitoring, application health checks via HEC
- **Data Sources:** `index=healthcare` `sourcetype="app:health"` fields `app_name`, `status`, `response_code`
- **SPL:**
```spl
index=healthcare sourcetype="app:health"
| eval up=if(status="ok" OR response_code=200, 1, 0)
| bin _time span=1h
| stats avg(up) as avail_pct by app_name, _time
| eval avail_pct=round(avail_pct*100,3)
| where avail_pct < 99.9
| table _time, app_name, avail_pct
```
- **Implementation:** Deploy health check probes against critical clinical applications. Calculate availability per hour and month. Generate SLA compliance reports for governance.
- **Visualization:** Line chart (availability over time), Gauge (monthly SLA %), Table (apps below target).
- **CIM Models:** N/A

---

### UC-21.3.3 · Nurse Call System Response Time
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Nurse call response time is a key patient satisfaction and safety metric. Monitoring enables staffing optimization and regulatory compliance.
- **App/TA:** Nurse call system integration via syslog or HEC
- **Data Sources:** `index=healthcare` `sourcetype="nursecall:event"` fields `call_id`, `call_time`, `response_time`, `unit`
- **SPL:**
```spl
index=healthcare sourcetype="nursecall:event"
| eval response_sec=response_time
| bin _time span=1h
| stats avg(response_sec) as avg_response, perc95(response_sec) as p95_response, count by unit, _time
| where p95_response > 300
| table _time, unit, avg_response, p95_response, count
```
- **Implementation:** Integrate nurse call system events via syslog or API. Track response times by unit and shift. Alert when p95 exceeds 5 minutes. Report for CMS quality metrics.
- **Visualization:** Bar chart (avg response by unit), Line chart (trend over shifts), Table (units exceeding threshold).
- **CIM Models:** N/A

---

### UC-21.3.4 · Blood Bank Refrigerator Temperature Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Blood products must be stored at 1-6°C per AABB standards. Temperature excursions require immediate action and documentation to prevent product waste and patient harm.
- **App/TA:** Environmental sensors via MQTT/Edge Hub
- **Data Sources:** `index=healthcare` `sourcetype="bloodbank:temp"` fields `unit_id`, `temp_c`, `alarm_status`
- **SPL:**
```spl
index=healthcare sourcetype="bloodbank:temp"
| where temp_c < 1 OR temp_c > 6
| stats earliest(_time) as excursion_start, latest(_time) as excursion_end, min(temp_c) as min_temp, max(temp_c) as max_temp by unit_id
| eval duration_min=round((excursion_end-excursion_start)/60,1)
| table unit_id, excursion_start, excursion_end, duration_min, min_temp, max_temp
```
- **Implementation:** Deploy temperature sensors on all blood storage units with 1-minute sampling. Alert immediately on out-of-range readings. Generate compliance documentation for AABB accreditation.
- **Visualization:** Line chart (temperature trend with range bands), Alert timeline, Table (excursions by unit).
- **CIM Models:** N/A

---

### UC-21.3.5 · Pharmaceutical Cold Chain Deviation Alerting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Many pharmaceuticals (vaccines, biologics) require strict temperature control. Excursions can render medications ineffective, creating patient safety and financial risk.
- **App/TA:** Cold chain monitoring sensors via MQTT/Edge Hub
- **Data Sources:** `index=healthcare` `sourcetype="coldchain:sensor"` fields `location`, `temp_c`, `setpoint_c`, `tolerance_c`
- **SPL:**
```spl
index=healthcare sourcetype="coldchain:sensor"
| eval low=setpoint_c-tolerance_c, high=setpoint_c+tolerance_c
| eval excursion=if(temp_c < low OR temp_c > high, 1, 0)
| where excursion=1
| stats earliest(_time) as start, latest(_time) as end, max(abs(temp_c-setpoint_c)) as max_deviation by location
| eval duration_min=round((end-start)/60,1)
| table location, start, end, duration_min, max_deviation
```
- **Implementation:** Integrate cold chain sensors across pharmacy, lab, and storage areas. Configure product-specific setpoints and tolerances. Alert pharmacy immediately on excursions for product assessment.
- **Visualization:** Time series (temperature vs bounds), Table (active excursions), Duration chart.
- **CIM Models:** N/A

---

### UC-21.3.6 · Lab Information System Result Turnaround Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Lab TAT directly impacts clinical decision-making and patient throughput. Tracking TAT by test type identifies bottlenecks in specimen processing and analysis.
- **App/TA:** LIS integration via HL7 or HEC
- **Data Sources:** `index=healthcare` `sourcetype="lis:result"` fields `order_id`, `test_type`, `collected_time`, `resulted_time`
- **SPL:**
```spl
index=healthcare sourcetype="lis:result"
| eval tat_min=round((resulted_time-collected_time)/60,1)
| where tat_min > 0
| stats avg(tat_min) as avg_tat, perc95(tat_min) as p95_tat, count by test_type
| sort - p95_tat
| table test_type, avg_tat, p95_tat, count
```
- **Implementation:** Parse HL7 ORM/ORU messages or LIS exports for specimen collection and result times. Track by test type and priority. Alert on stat tests exceeding critical TAT thresholds.
- **Visualization:** Bar chart (TAT by test type), Line chart (TAT trend), Table (tests exceeding target).
- **CIM Models:** N/A

---

### UC-21.3.7 · FDA 21 CFR Part 11 Electronic Signature Audit Trail
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** FDA regulations require audit trails for electronic records and signatures in pharmaceutical manufacturing and clinical systems. Monitoring ensures continuous compliance.
- **App/TA:** GxP system audit trail exports via HEC
- **Data Sources:** `index=healthcare` `sourcetype="esig:audit"` fields `system`, `user`, `action`, `record_id`, `signature_valid`
- **SPL:**
```spl
index=healthcare sourcetype="esig:audit"
| where action IN ("sign", "countersign", "approve", "reject")
| eval sig_issue=if(signature_valid="false" OR isnull(signature_valid), 1, 0)
| stats count as total_sigs, sum(sig_issue) as sig_issues by system, user
| where sig_issues > 0
| table system, user, total_sigs, sig_issues
```
- **Implementation:** Configure GxP systems to export electronic signature audit trails to Splunk. Track signature validity, sequential signing, and unauthorized signature attempts. Generate periodic compliance reports.
- **Visualization:** Table (signature audit), Bar chart (issues by system), Timeline (signature events).
- **CIM Models:** N/A

---

### UC-21.3.8 · GxP System Change Control Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Change, Compliance
- **Value:** Validated system changes must follow documented change control processes. Monitoring detects unauthorized changes and verifies proper approval workflows.
- **App/TA:** GxP system change logs via HEC
- **Data Sources:** `index=healthcare` `sourcetype="gxp:change"` fields `system`, `change_type`, `approved`, `approver`, `change_id`
- **SPL:**
```spl
index=healthcare sourcetype="gxp:change"
| where approved!="yes" OR isnull(approver)
| stats count by system, change_type, approved
| sort - count
| table system, change_type, approved, count
```
- **Implementation:** Ingest change control system events. Alert on unapproved changes to validated systems. Cross-reference with change advisory board records. Generate deviation reports for QA review.
- **Visualization:** Table (unapproved changes), Bar chart (changes by system), Timeline (change events).
- **CIM Models:** N/A

---

### UC-21.3.9 · Clinical Trial Data Integrity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Clinical trial data requires ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate). Monitoring audit trails ensures data integrity for regulatory submissions.
- **App/TA:** CTMS/EDC system audit exports via HEC
- **Data Sources:** `index=healthcare` `sourcetype="ctms:audit"` fields `study_id`, `site_id`, `user`, `action`, `field_changed`, `old_value`, `new_value`
- **SPL:**
```spl
index=healthcare sourcetype="ctms:audit"
| where action IN ("modify", "delete", "unblind")
| stats count as modifications, dc(field_changed) as fields_changed, dc(user) as users by study_id, site_id
| where modifications > 100 OR fields_changed > 20
| sort - modifications
| table study_id, site_id, modifications, fields_changed, users
```
- **Implementation:** Export EDC/CTMS audit trails to Splunk. Flag excessive modifications, unusual data patterns, and retrospective changes. Generate risk-based monitoring reports for clinical operations.
- **Visualization:** Table (sites by modification count), Bar chart (changes by study), Timeline (high-activity periods).
- **CIM Models:** N/A

---

### UC-21.3.10 · Radiology Reading Turnaround Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Radiology report TAT affects clinical decisions and patient discharge timing. Tracking by modality and priority ensures SLA compliance and identifies workflow bottlenecks.
- **App/TA:** RIS/PACS integration via HL7 or HEC
- **Data Sources:** `index=healthcare` `sourcetype="ris:report"` fields `accession`, `modality`, `priority`, `exam_complete_time`, `report_finalized_time`
- **SPL:**
```spl
index=healthcare sourcetype="ris:report"
| eval tat_min=round((report_finalized_time-exam_complete_time)/60,1)
| where tat_min > 0
| stats avg(tat_min) as avg_tat, perc95(tat_min) as p95_tat by modality, priority
| sort priority, -p95_tat
| table modality, priority, avg_tat, p95_tat
```
- **Implementation:** Parse RIS events for exam completion and report finalization timestamps. Track by modality (CT, MR, XR) and priority (stat, urgent, routine). Alert on stat studies exceeding 1-hour TAT.
- **Visualization:** Bar chart (TAT by modality), Line chart (TAT trend), Table (exams exceeding SLA).
- **CIM Models:** N/A

---

### UC-21.3.11 · Patient Flow and Bed Management Analytics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Real-time bed occupancy and patient flow data supports throughput optimization, reduces boarding, and improves patient placement decisions.
- **App/TA:** ADT feed via HL7 or HEC
- **Data Sources:** `index=healthcare` `sourcetype="adtflow:event"` fields `unit`, `event_type`, `bed_id`, `patient_class`
- **SPL:**
```spl
index=healthcare sourcetype="adtflow:event"
| where event_type IN ("admit", "transfer", "discharge")
| bin _time span=1h
| stats dc(bed_id) as beds_used, sum(if(event_type="admit",1,0)) as admits, sum(if(event_type="discharge",1,0)) as discharges by unit, _time
| eval net_flow=admits-discharges
| table _time, unit, beds_used, admits, discharges, net_flow
```
- **Implementation:** Ingest ADT (Admit-Discharge-Transfer) HL7 messages. Calculate real-time census by unit. Track length of stay distributions and boarding times. Support capacity planning.
- **Visualization:** Stacked area (census by unit), Line chart (admits vs discharges), Table (units at capacity).
- **CIM Models:** N/A

---

### UC-21.3.12 · Emergency Department Wait Time Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** ED wait times impact patient outcomes and satisfaction scores. Real-time tracking enables dynamic resource allocation and identifies systemic throughput issues.
- **App/TA:** EDIS integration via HEC
- **Data Sources:** `index=healthcare` `sourcetype="edis:event"` fields `visit_id`, `triage_time`, `provider_time`, `disposition_time`
- **SPL:**
```spl
index=healthcare sourcetype="edis:event"
| eval door_to_provider_min=round((provider_time-triage_time)/60,1)
| eval total_los_min=round((disposition_time-triage_time)/60,1)
| where door_to_provider_min > 0
| bin _time span=1h
| stats avg(door_to_provider_min) as avg_wait, perc95(door_to_provider_min) as p95_wait, avg(total_los_min) as avg_los by _time
| table _time, avg_wait, p95_wait, avg_los
```
- **Implementation:** Integrate EDIS timestamps for triage, provider evaluation, and disposition. Track door-to-provider time as key metric. Alert when wait times exceed CMS benchmarks. Correlate with arrival volume and staffing.
- **Visualization:** Line chart (wait time trend), Gauge (current avg wait), Bar chart (wait by acuity level).
- **CIM Models:** N/A

---

### UC-21.3.13 · Surgical Suite Utilization and Turnover Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** OR utilization and turnover time directly impact surgical throughput and revenue. Monitoring enables scheduling optimization and identifies delays.
- **App/TA:** OR scheduling system via HEC
- **Data Sources:** `index=healthcare` `sourcetype="or:schedule"` fields `or_room`, `case_start`, `case_end`, `turnover_start`, `turnover_end`
- **SPL:**
```spl
index=healthcare sourcetype="or:schedule"
| eval case_duration_min=round((case_end-case_start)/60,1)
| eval turnover_min=round((turnover_end-turnover_start)/60,1)
| stats avg(case_duration_min) as avg_case, avg(turnover_min) as avg_turnover, count as cases by or_room
| eval utilization_pct=round((avg_case*cases)/((avg_case+avg_turnover)*cases)*100,1)
| table or_room, cases, avg_case, avg_turnover, utilization_pct
```
- **Implementation:** Ingest OR scheduling and tracking data. Calculate prime time utilization and turnover metrics. Identify rooms with excessive turnover for process improvement. Report weekly for surgical services leadership.
- **Visualization:** Bar chart (utilization by room), Line chart (turnover trend), Table (room performance).
- **CIM Models:** N/A

---

### UC-21.3.14 · Biomedical Equipment Preventive Maintenance Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Joint Commission requires documented PM programs for medical equipment. Tracking compliance prevents accreditation findings and ensures equipment reliability.
- **App/TA:** CMMS biomedical module via HEC
- **Data Sources:** `index=healthcare` `sourcetype="cmms:biomed"` fields `asset_id`, `pm_due_date`, `pm_completed_date`, `risk_level`
- **SPL:**
```spl
index=healthcare sourcetype="cmms:biomed"
| where isnull(pm_completed_date) AND pm_due_date < now()
| eval days_overdue=round((now()-pm_due_date)/86400,0)
| stats count as overdue_count by risk_level
| sort - overdue_count
| table risk_level, overdue_count
```
- **Implementation:** Integrate CMMS biomedical work orders. Track PM completion rates by risk level and department. Alert on overdue high-risk equipment. Generate compliance dashboards for accreditation readiness.
- **Visualization:** Gauge (PM compliance %), Bar chart (overdue by risk level), Table (overdue equipment).
- **CIM Models:** N/A

---

### UC-21.3.15 · Medication Administration Record Reconciliation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Discrepancies between medication orders and administration records indicate potential medication errors, a leading cause of adverse events. Reconciliation supports patient safety.
- **App/TA:** EHR MAR/pharmacy integration via HL7 or HEC
- **Data Sources:** `index=healthcare` `sourcetype="mar:record"` fields `order_id`, `med_name`, `scheduled_time`, `admin_time`, `admin_status`
- **SPL:**
```spl
index=healthcare sourcetype="mar:record"
| eval late_min=round((admin_time-scheduled_time)/60,1)
| eval issue=case(
    admin_status="missed", "missed",
    admin_status="held", "held",
    late_min > 60, "late",
    late_min < -30, "early",
    true(), "on_time")
| where issue!="on_time"
| stats count by issue, med_name
| sort - count
| table issue, med_name, count
```
- **Implementation:** Parse MAR events from EHR. Compare scheduled vs actual administration times. Flag missed, held, and significantly late administrations. Report to nursing leadership and pharmacy for investigation.
- **Visualization:** Pie chart (issue distribution), Table (top discrepancies by medication), Timeline (missed doses).
- **CIM Models:** N/A

---

### UC-21.3.16 · Telehealth Session Quality Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Poor telehealth video/audio quality degrades clinical assessment and patient experience. Monitoring enables proactive intervention and platform optimization.
- **App/TA:** Telehealth platform API/logs via HEC
- **Data Sources:** `index=healthcare` `sourcetype="telehealth:session"` fields `session_id`, `provider_id`, `video_quality_score`, `audio_quality_score`, `disconnect_count`
- **SPL:**
```spl
index=healthcare sourcetype="telehealth:session"
| where video_quality_score < 3 OR audio_quality_score < 3 OR disconnect_count > 0
| stats count as poor_sessions, avg(video_quality_score) as avg_video, avg(audio_quality_score) as avg_audio by provider_id
| sort - poor_sessions
| table provider_id, poor_sessions, avg_video, avg_audio
```
- **Implementation:** Integrate telehealth platform quality metrics via API. Track session quality by provider and patient location. Correlate with network conditions. Alert on sustained quality degradation.
- **Visualization:** Line chart (quality scores over time), Bar chart (poor sessions by provider), Table (session details).
- **CIM Models:** N/A

---

### UC-21.3.17 · Clinical Decision Support Response Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** CDS alerts must fire in real-time during clinical workflows. Excessive latency causes clinicians to bypass alerts, reducing patient safety benefit.
- **App/TA:** CDS engine logs via HEC
- **Data Sources:** `index=healthcare` `sourcetype="cds:query"` fields `rule_id`, `query_time_ms`, `result`, `triggered_alert`
- **SPL:**
```spl
index=healthcare sourcetype="cds:query"
| bin _time span=1h
| stats avg(query_time_ms) as avg_ms, perc95(query_time_ms) as p95_ms, count by rule_id, _time
| where p95_ms > 500
| table _time, rule_id, avg_ms, p95_ms, count
```
- **Implementation:** Instrument CDS engine with response time logging. Track by rule type and clinical context. Optimize slow rules that impact order entry workflows. Alert when latency exceeds clinical usability thresholds.
- **Visualization:** Line chart (response time by rule), Heatmap (rule × time), Table (slowest rules).
- **CIM Models:** N/A

---

### 21.4 Transportation and Logistics

**Primary App/TA:** Custom HEC inputs from telematics/fleet systems, WMS/TMS application logs, IoT sensors via MQTT, GPS tracking platforms.

**Data Sources:** GPS telematics data, OBD-II diagnostic codes, WMS/TMS application logs, IoT sensors via MQTT, port management systems, rail signaling logs.

---

### UC-21.4.1 · Fleet Vehicle GPS Tracking and Geofence Alerting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance
- **Value:** Real-time vehicle tracking and geofence alerts enable theft prevention, route compliance, and efficient dispatch during emergency response.
- **App/TA:** GPS telematics platform via HEC
- **Data Sources:** `index=logistics` `sourcetype="gps:telematics"` fields `vehicle_id`, `lat`, `lon`, `speed_kmh`, `geofence_id`
- **SPL:**
```spl
index=logistics sourcetype="gps:telematics"
| lookup geofence_boundaries geofence_id OUTPUT boundary_name allowed
| where allowed=0 OR isnull(allowed)
| stats earliest(_time) as entered, latest(_time) as last_seen, avg(speed_kmh) as avg_speed by vehicle_id, boundary_name
| table vehicle_id, boundary_name, entered, last_seen, avg_speed
```
- **Implementation:** Ingest GPS data at 30-60 second intervals. Define geofences as lookup tables. Alert on boundary violations, after-hours movement, and unauthorized stops. Correlate with driver assignment.
- **Visualization:** Map (vehicle positions with geofences), Table (violations), Timeline (vehicle movements).
- **CIM Models:** N/A

---

### UC-21.4.2 · Driver Behavior Scoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Analyzing harsh braking, speeding, and excessive idling improves fleet safety, reduces fuel costs, and supports insurance and regulatory compliance.
- **App/TA:** Telematics platform via HEC
- **Data Sources:** `index=logistics` `sourcetype="gps:telematics"` fields `driver_id`, `harsh_brake`, `speed_kmh`, `speed_limit_kmh`, `idle_min`
- **SPL:**
```spl
index=logistics sourcetype="gps:telematics"
| eval speeding=if(speed_kmh > speed_limit_kmh*1.1, 1, 0)
| eval harsh=if(harsh_brake="true" OR harsh_brake=1, 1, 0)
| stats sum(speeding) as speed_events, sum(harsh) as harsh_events, sum(idle_min) as total_idle_min by driver_id
| eval score=100 - (speed_events*2 + harsh_events*5 + round(total_idle_min/60,0))
| eval score=if(score<0, 0, score)
| sort score
| table driver_id, score, speed_events, harsh_events, total_idle_min
```
- **Implementation:** Ingest telematics events with driving behavior flags. Calculate composite scores weekly. Provide driver coaching based on trends. Share top performers and improvement areas.
- **Visualization:** Bar chart (scores by driver), Line chart (score trend), Table (detailed events).
- **CIM Models:** N/A

---

### UC-21.4.3 · Fuel Consumption Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unusual fuel consumption patterns indicate theft, mechanical issues (injectors, tires), or inefficient routing. Early detection reduces operating costs.
- **App/TA:** Fuel management system / telematics via HEC
- **Data Sources:** `index=logistics` `sourcetype="fuel:consumption"` fields `vehicle_id`, `fuel_liters`, `distance_km`
- **SPL:**
```spl
index=logistics sourcetype="fuel:consumption"
| eval fuel_rate=fuel_liters/nullif(distance_km,0)*100
| eventstats avg(fuel_rate) as fleet_avg, stdev(fuel_rate) as fleet_stdev by vehicle_type
| eval z_score=abs(fuel_rate-fleet_avg)/nullif(fleet_stdev,0)
| where z_score > 2
| table vehicle_id, fuel_rate, fleet_avg, z_score, distance_km
```
- **Implementation:** Normalize fuel consumption by distance and load. Baseline per vehicle type. Alert on sustained deviations. Correlate with maintenance records and route data.
- **Visualization:** Scatter plot (fuel rate vs distance), Bar chart (outliers), Line chart (fuel rate trend).
- **CIM Models:** N/A

---

### UC-21.4.4 · Vehicle Diagnostic Trouble Code Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** OBD-II diagnostic trouble codes provide early warning of mechanical and emissions issues. Monitoring enables proactive maintenance and prevents roadside failures.
- **App/TA:** OBD-II / telematics via HEC
- **Data Sources:** `index=logistics` `sourcetype="obd2:dtc"` fields `vehicle_id`, `dtc_code`, `dtc_description`, `severity`
- **SPL:**
```spl
index=logistics sourcetype="obd2:dtc"
| stats count, latest(_time) as last_seen, values(dtc_description) as descriptions by vehicle_id, dtc_code, severity
| where severity IN ("critical", "warning")
| sort - count
| table vehicle_id, dtc_code, descriptions, severity, count, last_seen
```
- **Implementation:** Ingest DTC codes from fleet telematics. Prioritize by severity. Generate automated maintenance work orders for critical codes. Track recurring DTCs by vehicle and fleet-wide.
- **Visualization:** Table (active DTCs), Bar chart (DTCs by code), Timeline (DTC occurrences).
- **CIM Models:** N/A

---

### UC-21.4.5 · Port Container Crane Cycle Time Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Crane cycle time is a key productivity metric for port operations. Tracking enables operator performance comparison and equipment optimization.
- **App/TA:** Terminal operating system / crane PLC via HEC
- **Data Sources:** `index=logistics` `sourcetype="crane:cycle"` fields `crane_id`, `cycle_time_sec`, `move_type`, `operator_id`
- **SPL:**
```spl
index=logistics sourcetype="crane:cycle"
| bin _time span=1h
| stats avg(cycle_time_sec) as avg_cycle, perc95(cycle_time_sec) as p95_cycle, count as moves by crane_id, _time
| eval moves_per_hour=moves
| table _time, crane_id, avg_cycle, p95_cycle, moves_per_hour
```
- **Implementation:** Capture crane PLM (Position Location Measurement) data. Calculate gross and net crane rates. Compare operators and shifts. Identify delays from vessel configuration and weather.
- **Visualization:** Line chart (cycle time trend), Bar chart (MPH by crane), Table (shift performance).
- **CIM Models:** N/A

---

### UC-21.4.6 · Rail Signaling System Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Rail signaling failures cause service disruptions and safety incidents. Monitoring signal system health enables proactive maintenance and reduces delay minutes.
- **App/TA:** Signaling system logs via syslog/HEC
- **Data Sources:** `index=logistics` `sourcetype="rail:signal"` fields `signal_id`, `status`, `fault_code`, `location`
- **SPL:**
```spl
index=logistics sourcetype="rail:signal"
| where status!="normal" OR isnotnull(fault_code)
| stats count, latest(_time) as last_fault, values(fault_code) as fault_codes by signal_id, location
| sort - count
| table signal_id, location, fault_codes, count, last_fault
```
- **Implementation:** Integrate signaling system diagnostic logs. Alert on persistent faults and degraded modes. Track mean time between failures by signal type. Report for infrastructure maintenance planning.
- **Visualization:** Map (signal status by location), Table (faulted signals), Timeline (fault history).
- **CIM Models:** N/A

---

### UC-21.4.7 · Airport Baggage Handling System Throughput
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Baggage system throughput impacts flight departure times and passenger satisfaction. Monitoring identifies jams, diversions, and screening bottlenecks.
- **App/TA:** BHS SCADA / sortation system via HEC
- **Data Sources:** `index=logistics` `sourcetype="bhs:throughput"` fields `lane_id`, `bags_per_hour`, `jam_count`, `divert_count`
- **SPL:**
```spl
index=logistics sourcetype="bhs:throughput"
| bin _time span=15m
| stats sum(bags_per_hour) as total_bags, sum(jam_count) as jams, sum(divert_count) as diverts by lane_id, _time
| where jams > 0 OR diverts > 5
| table _time, lane_id, total_bags, jams, diverts
```
- **Implementation:** Ingest BHS SCADA events for bag counts, jams, and screening diversions. Track throughput by lane and terminal. Alert on sustained throughput drops or jam accumulation. Correlate with flight schedules.
- **Visualization:** Line chart (throughput trend), Bar chart (jams by lane), Table (performance summary).
- **CIM Models:** N/A

---

### UC-21.4.8 · Warehouse Management System Order Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Pick accuracy directly impacts customer satisfaction, returns, and operational costs. Tracking accuracy by zone and picker enables targeted training.
- **App/TA:** WMS application logs via HEC
- **Data Sources:** `index=logistics` `sourcetype="wms:order"` fields `order_id`, `pick_correct`, `zone`, `picker_id`
- **SPL:**
```spl
index=logistics sourcetype="wms:order"
| eval correct=if(pick_correct="true" OR pick_correct=1, 1, 0)
| stats avg(correct) as accuracy_pct, count as total_picks by zone, picker_id
| eval accuracy_pct=round(accuracy_pct*100,2)
| where accuracy_pct < 99.5
| sort accuracy_pct
| table zone, picker_id, accuracy_pct, total_picks
```
- **Implementation:** Capture pick confirmation events from WMS. Calculate accuracy rates by zone and picker. Alert on accuracy below threshold. Identify systemic issues vs individual training needs.
- **Visualization:** Bar chart (accuracy by zone), Table (picker performance), Gauge (overall accuracy).
- **CIM Models:** N/A

---

### UC-21.4.9 · Last-Mile Delivery SLA Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Last-mile delivery performance drives customer experience and contract compliance. Tracking on-time rates enables route optimization and exception management.
- **App/TA:** Delivery management platform via HEC
- **Data Sources:** `index=logistics` `sourcetype="delivery:event"` fields `delivery_id`, `promised_time`, `actual_time`, `status`
- **SPL:**
```spl
index=logistics sourcetype="delivery:event" status="delivered"
| eval on_time=if(actual_time <= promised_time, 1, 0)
| eval late_min=if(on_time=0, round((actual_time-promised_time)/60,1), 0)
| bin _time span=1d
| stats avg(on_time) as otd_rate, avg(late_min) as avg_late_min, count as deliveries by _time
| eval otd_pct=round(otd_rate*100,2)
| table _time, deliveries, otd_pct, avg_late_min
```
- **Implementation:** Integrate delivery completion events with promised timestamps. Calculate on-time delivery percentage daily. Alert on drops below SLA threshold. Analyze late deliveries by route and driver.
- **Visualization:** Line chart (OTD trend), Gauge (current OTD %), Bar chart (late deliveries by reason).
- **CIM Models:** N/A

---

### UC-21.4.10 · Cold Chain Temperature Excursion for Perishable Goods
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Temperature excursions during transport of perishable goods cause spoilage, regulatory violations, and customer claims. Real-time monitoring enables immediate corrective action.
- **App/TA:** Cold chain sensors via MQTT/HEC
- **Data Sources:** `index=logistics` `sourcetype="coldchain:transit"` fields `shipment_id`, `temp_c`, `setpoint_c`, `tolerance_c`
- **SPL:**
```spl
index=logistics sourcetype="coldchain:transit"
| eval low=setpoint_c-tolerance_c, high=setpoint_c+tolerance_c
| eval excursion=if(temp_c < low OR temp_c > high, 1, 0)
| where excursion=1
| stats earliest(_time) as start, latest(_time) as end, max(abs(temp_c-setpoint_c)) as max_dev by shipment_id
| eval duration_min=round((end-start)/60,1)
| table shipment_id, start, end, duration_min, max_dev
```
- **Implementation:** Tag readings with shipment and setpoint. Escalate by duration and deviation magnitude. Integrate with claims and receiver QA for traceability.
- **Visualization:** Time series (temp vs bounds), Table (excursions), Duration chart.
- **CIM Models:** N/A

---

### UC-21.4.11 · Intermodal Container Dwell Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Excessive container dwell time at terminals increases demurrage costs and reduces asset turns. Tracking dwell enables process improvements and better planning.
- **App/TA:** Terminal operating system via HEC
- **Data Sources:** `index=logistics` `sourcetype="container:dwell"` fields `container_id`, `dwell_hours`, `facility`
- **SPL:**
```spl
index=logistics sourcetype="container:dwell"
| where isnotnull(dwell_hours)
| stats avg(dwell_hours) as avg_dwell, perc95(dwell_hours) as p95_dwell, max(dwell_hours) as max_dwell by facility
| sort - p95_dwell
| table facility, avg_dwell, p95_dwell, max_dwell
```
- **Implementation:** Define dwell from ingate to outgate. Compare rail vs truck facilities. Target reduction projects at high-p95 sites.
- **Visualization:** Bar chart (p95 by facility), Histogram (dwell distribution), Trend of avg dwell.
- **CIM Models:** N/A

---

### UC-21.4.12 · Traffic Management System Sensor Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Roadside sensor availability impacts traffic management system accuracy. Monitoring sensor uptime enables proactive maintenance and reliable traffic data.
- **App/TA:** ATMS field device gateway via HEC
- **Data Sources:** `index=logistics` `sourcetype="tms:sensor"` fields `sensor_id`, `last_reading_epoch`, `status`
- **SPL:**
```spl
index=logistics sourcetype="tms:sensor"
| eval age_sec=now()-last_reading_epoch
| eval online=if(status="active" AND age_sec < 300, 1, 0)
| stats avg(online) as avail_frac by sensor_id
| eval avail_pct=round(avail_frac*100,2)
| where avail_pct < 95
| table sensor_id, avail_pct
```
- **Implementation:** Monitor sensor heartbeats. Tune stale threshold per sensor class. Alert maintenance when availability drops below target.
- **Visualization:** Map (sensor status), Table (offline sensors), Time chart (online %).
- **CIM Models:** N/A

---

### 21.5 Oil, Gas, and Mining

**Primary App/TA:** Splunk OT Intelligence (Splunkbase 5180), OT Security Add-on (Splunkbase 5151), Edge Hub, custom HEC inputs from SCADA/historians.

**Data Sources:** PI/OSIsoft historian via HEC, SCADA RTU data, OPC-UA tags, Edge Hub environmental sensors, fleet telematics, pipeline monitoring systems.

---

### UC-21.5.1 · Pipeline Pressure and Flow Rate Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Unusual pressure or flow patterns may indicate leaks, blockages, or instrument drift. Early detection prevents environmental incidents and costly shutdowns.
- **App/TA:** Splunk OT Intelligence, historian via HEC
- **Data Sources:** `index=ot` `sourcetype="pipeline:pressure"` fields `segment_id`, `pressure_psi`, `flow_bbl_h`
- **SPL:**
```spl
index=ot sourcetype="pipeline:pressure"
| eventstats median(pressure_psi) as med_p median(flow_bbl_h) as med_f by segment_id
| eval dev_p=abs(pressure_psi-med_p)
| where dev_p > 15 OR flow_bbl_h < med_f*0.5 OR flow_bbl_h > med_f*1.5
| stats latest(pressure_psi) as pressure, latest(flow_bbl_h) as flow, latest(med_p) as expected_p by segment_id
```
- **Implementation:** Ingest high-resolution historian samples. Tune thresholds per segment. Route findings to the control room. Do not use Splunk alone for automatic shutdown.
- **Visualization:** Time chart (pressure and flow), Anomaly overlay, Segment map.
- **CIM Models:** N/A

---

### UC-21.5.2 · Wellhead Telemetry Data Gap Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Missing wellhead measurements indicate communication failures. Quick detection ensures SCADA and field teams can restore data continuity.
- **App/TA:** Edge Hub / RTU feeds via HEC
- **Data Sources:** `index=ot` `sourcetype="wellhead:telemetry"` fields `well_id`, `expected_interval_sec`
- **SPL:**
```spl
index=ot sourcetype="wellhead:telemetry"
| stats latest(_time) as last_seen by well_id
| eval gap_sec=now()-last_seen
| where gap_sec > 900
| eval gap_min=round(gap_sec/60,1)
| sort - gap_sec
| table well_id, last_seen, gap_min
```
- **Implementation:** Include expected interval on each event or use 3x scan rate as threshold. Verify against planned shutdowns via a maintenance lookup.
- **Visualization:** Table (wells by gap), Single value (stale well count), Timeline (last seen).
- **CIM Models:** N/A

---

### UC-21.5.3 · Gas Compressor Vibration Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Vibration trending catches mechanical issues during planned outages rather than as unplanned failures, improving equipment reliability and reducing costs.
- **App/TA:** Vibration monitoring system / historian via HEC
- **Data Sources:** `index=ot` `sourcetype="compressor:vibration"` fields `asset_id`, `vibration_mm_s`, `bearing_location`
- **SPL:**
```spl
index=ot sourcetype="compressor:vibration"
| timechart span=1h avg(vibration_mm_s) as avg_vib, perc95(vibration_mm_s) as p95_vib by asset_id
```
- **Implementation:** Align units with your vibration program. Set rising-rate alerts against maintenance baselines. Compare bearing locations on the same train for imbalance context.
- **Visualization:** Multi-series time chart, Heatmap (asset × week), Threshold bands.
- **CIM Models:** N/A

---

### UC-21.5.4 · Flare Stack Event Correlation and Emissions Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Flare duration and intensity tracking supports environmental reporting and identifies operational events causing excessive flaring.
- **App/TA:** Flare meter / CEMS via HEC
- **Data Sources:** `index=ot` `sourcetype="flare:event"` fields `flare_id`, `duration_min`, `rate_mmscfd`, `site_id`
- **SPL:**
```spl
index=ot sourcetype="flare:event"
| eval day=strftime(_time,"%Y-%m-%d")
| stats sum(duration_min) as total_minutes, count as flare_events by site_id, day
| eval hours_flared=round(total_minutes/60,2)
| sort - hours_flared
| table site_id, day, flare_events, hours_flared
```
- **Implementation:** Normalize flare start/stop events. Validate volume methods against regulatory calculation approach. Join wind or process tags for correlation.
- **Visualization:** Time chart (flare hours), Stacked bar by site, Correlation panel with permit limits.
- **CIM Models:** N/A

---

### UC-21.5.5 · Mineral Processing Throughput Optimization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracking tons per hour against targets balances feed rate with crusher and mill constraints, improving yield and reducing energy waste.
- **App/TA:** DCS/historian via HEC
- **Data Sources:** `index=ot` `sourcetype="process:throughput"` fields `line_id`, `tph`, `target_tph`
- **SPL:**
```spl
index=ot sourcetype="process:throughput"
| eval rate_ratio=round(tph/nullif(target_tph,0)*100,1)
| timechart span=15m avg(tph) as avg_tph, avg(rate_ratio) as pct_of_target by line_id
```
- **Implementation:** Align tph with shift plans. Alert when sustained underperformance indicates blockage or wear. Share outputs with metallurgy and maintenance planning.
- **Visualization:** Time chart (tph vs target), Gauge (utilization), Bar by shift.
- **CIM Models:** N/A

---

### UC-21.5.6 · Haul Truck Fleet Utilization and Payload Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Measuring truck active hours and payload improves fleet sizing, load-pass matching, and reduces per-ton haulage costs.
- **App/TA:** Fleet management / onboard weighing via HEC
- **Data Sources:** `index=ot` `sourcetype="haultruck:telematics"` fields `truck_id`, `payload_ton`, `engine_hours`, `loaded`
- **SPL:**
```spl
index=ot sourcetype="haultruck:telematics"
| where loaded=1 OR lower(loaded)="true"
| stats sum(payload_ton) as total_payload, sum(engine_hours) as total_hours by truck_id
| eval tons_per_hour=round(total_payload/nullif(total_hours,0),1)
| sort - total_payload
| table truck_id, total_payload, total_hours, tons_per_hour
```
- **Implementation:** Ingest load cycles with valid payload. Reconcile with scale house periodically. Use engine hours for maintenance scheduling alongside production KPIs.
- **Visualization:** Bar chart (payload by truck), Scatter (hours vs tons), Fleet summary.
- **CIM Models:** N/A

---

### UC-21.5.7 · Drill Rig Sensor Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Drill instrumentation must stay online for safe and efficient drilling. Monitoring channel health catches failures before they impact operations.
- **App/TA:** Rig data logger via HEC
- **Data Sources:** `index=ot` `sourcetype="drillrig:sensor"` fields `rig_id`, `channel`, `status`, `value_age_sec`
- **SPL:**
```spl
index=ot sourcetype="drillrig:sensor"
| eval ok=if(status="ok" AND value_age_sec < 30, 1, 0)
| stats avg(ok) as health_frac by rig_id, channel
| eval health_pct=round(health_frac*100,2)
| where health_pct < 99
| table rig_id, channel, health_pct
```
- **Implementation:** Tune value_age_sec threshold per channel type. Alert the rig supervisor when channels degrade. Align with planned rig maintenance.
- **Visualization:** Matrix (rig × channel), Time chart (stale count), Table (bad channels).
- **CIM Models:** N/A

---

### UC-21.5.8 · Safety Instrumented System Trip Event Analysis
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** SIS trip analysis distinguishes nuisance trips from genuine demand, supporting PHA/MOC review and improving safety system reliability metrics.
- **App/TA:** SIS / ESD logs via HEC
- **Data Sources:** `index=ot` `sourcetype="sis:trip"` fields `loop_id`, `trip_cause`, `demand_type`
- **SPL:**
```spl
index=ot sourcetype="sis:trip"
| stats count as trips, dc(loop_id) as loops_affected, values(trip_cause) as causes by demand_type
| sort - trips
| table demand_type, trips, loops_affected, causes
```
- **Implementation:** Apply strict change control on parsers. Use for post-event analysis and trending trip rates per loop. Never bypass safety systems from analytics.
- **Visualization:** Bar chart (trips by cause), Timeline, Pareto of loops.
- **CIM Models:** N/A

---

### UC-21.5.9 · Environmental Compliance Effluent Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracking effluent parameters against permit limits enables timely corrective action and audit-ready documentation for environmental regulations.
- **App/TA:** LIMS / online analyzer via HEC
- **Data Sources:** `index=ot` `sourcetype="effluent:monitor"` fields `outfall_id`, `parameter`, `value_mg_l`, `limit_mg_l`
- **SPL:**
```spl
index=ot sourcetype="effluent:monitor"
| eval exceed=if(value_mg_l > limit_mg_l, 1, 0)
| where exceed=1
| stats earliest(_time) as first_exceed, max(value_mg_l) as peak_value by outfall_id, parameter
| table outfall_id, parameter, first_exceed, peak_value, limit_mg_l
```
- **Implementation:** Align sampling frequency with permit requirements. Add separate searches for daily max vs monthly average if your permit uses both formats.
- **Visualization:** Time chart (value vs limit), Alert table, Gauge (margin to limit).
- **CIM Models:** N/A

---

### UC-21.5.10 · Tank Farm Level Monitoring and Overflow Prevention
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Tank overfills cause environmental incidents and safety hazards. Monitoring levels and fill rates enables proactive response and inventory reconciliation.
- **App/TA:** Tank gauging / DCS via HEC
- **Data Sources:** `index=ot` `sourcetype="tankfarm:level"` fields `tank_id`, `level_pct`, `high_alarm_pct`, `fill_rate_m3_h`
- **SPL:**
```spl
index=ot sourcetype="tankfarm:level"
| eval risk=if(level_pct >= high_alarm_pct OR (level_pct > 85 AND fill_rate_m3_h > 0), 1, 0)
| where risk=1
| stats latest(level_pct) as current_level, latest(fill_rate_m3_h) as fill_rate by tank_id
| sort - current_level
| table tank_id, current_level, fill_rate
```
- **Implementation:** Keep primary alarms in BPCS/SIS. Splunk provides visibility and trending. Add roof and temperature for floating-roof tanks if available.
- **Visualization:** Tank-style gauge, Time chart (level), Trend (fill rate).
- **CIM Models:** N/A

---

### UC-21.5.11 · Cathodic Protection System Integrity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Pipe-to-soil potentials and rectifier state indicate whether corrosion protection is effective along pipelines, supporting regulatory compliance and asset integrity.
- **App/TA:** CP remote monitoring via HEC
- **Data Sources:** `index=ot` `sourcetype="cp:reading"` fields `test_point_id`, `potential_v`, `min_protect_v`, `rectifier_on`
- **SPL:**
```spl
index=ot sourcetype="cp:reading"
| where rectifier_on=1
| eval protected=if(potential_v <= min_protect_v, 1, 0)
| stats avg(protected) as pct_protected by test_point_id
| eval pct_protected=round(pct_protected*100,2)
| where pct_protected < 95
| table test_point_id, pct_protected
```
- **Implementation:** Confirm sign convention for your CP system. Alert on sustained under-protection. Survey intervals may be daily.
- **Visualization:** Map (test points), Time chart (potential), Table (under-protected sites).
- **CIM Models:** N/A

---

### UC-21.5.12 · Seismic Monitoring Data Quality Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Verifying seismic trace completeness and signal-to-noise ratio ensures monitoring programs meet technical specifications for reliable subsurface analysis.
- **App/TA:** Seismic acquisition system via HEC
- **Data Sources:** `index=ot` `sourcetype="seismic:data"` fields `station_id`, `samples_expected`, `samples_received`, `snr_db`
- **SPL:**
```spl
index=ot sourcetype="seismic:data"
| eval completeness=round(samples_received/nullif(samples_expected,0)*100,2)
| eval quality_ok=if(completeness >= 99 AND snr_db >= 10, 1, 0)
| stats avg(quality_ok) as pass_rate by station_id
| eval pass_pct=round(pass_rate*100,2)
| where pass_pct < 98
| table station_id, pass_pct
```
- **Implementation:** Baseline SNR thresholds by site noise. Alert on missing traces or repeated gaps. Support field crew dispatch for sensor issues.
- **Visualization:** Time chart (completeness), SNR distribution, Station ranking table.
- **CIM Models:** N/A

---

### 21.6 Retail and E-Commerce Operations

**Primary App/TA:** Custom HEC inputs from POS systems, e-commerce platforms, retail IoT sensors, Wi-Fi controllers, digital signage systems.

**Data Sources:** POS transaction logs, e-commerce platform logs, retail IoT sensors (foot traffic, environmental), Wi-Fi controller logs, inventory management systems.

---

### UC-21.6.1 · POS Terminal Transaction Response Time Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Slow POS responses frustrate customers and extend queue times; tracking latency by terminal and store helps isolate network, host, or payment-processor issues before they impact peak-hour throughput.
- **App/TA:** Custom HEC (POS gateway / payment middleware)
- **Data Sources:** `index=retail` `sourcetype="pos:transaction"` (store_id, terminal_id, response_ms, txn_status)
- **SPL:**
```spl
index=retail sourcetype="pos:transaction"
| bin _time span=5m
| stats avg(response_ms) as avg_ms, perc95(response_ms) as p95_ms, count as txn_count by store_id, terminal_id, _time
| where avg_ms > 800 OR p95_ms > 2000
| eval breach=if(p95_ms>2000,"p95","avg")
| table _time, store_id, terminal_id, avg_ms, p95_ms, txn_count, breach
```
- **Implementation:** Ingest authorization round-trip times from the POS middleware or switch logs via HEC; normalize milliseconds and exclude void-only events. Schedule alerts for sustained breaches and drill down by VLAN or terminal firmware version using optional lookups.
- **Visualization:** Time chart (avg vs p95 by terminal), Heatmap (store × hour), Table (worst terminals).
- **CIM Models:** N/A

---

### UC-21.6.2 · Self-Checkout Lane Availability and Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** High self-checkout error rates drive attendant interventions and shrink throughput; correlating lane state with error codes prioritizes hardware refresh and software fixes.
- **App/TA:** Custom HEC (SCO application / kiosk telemetry)
- **Data Sources:** `index=retail` `sourcetype="selfcheckout:event"` (store_id, lane_id, event_type, error_code)
- **SPL:**
```spl
index=retail sourcetype="selfcheckout:event"
| bin _time span=15m
| stats count as total_ev, sum(eval(if(event_type="error" OR (isnotnull(error_code) AND error_code!="" AND error_code!="-"),1,0))) as err_ev by store_id, lane_id, _time
| eval error_rate=round(100*err_ev/nullif(total_ev,0),2)
| where error_rate > 8 OR total_ev < 5
| table _time, store_id, lane_id, total_ev, err_ev, error_rate
```
- **Implementation:** Map kiosk heartbeat and transaction error streams into a single sourcetype; use `error_code` only when present. Tune thresholds by store format (grocery vs big-box). Route alerts to store ops and vendor support queues.
- **Visualization:** Bar chart (error rate by lane), Stacked area (errors vs total events), Single value (lanes over threshold).
- **CIM Models:** N/A

---

### UC-21.6.3 · In-Store Wi-Fi and Network Infrastructure Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Performance
- **Value:** mPOS, guest Wi-Fi, and IoT rely on store LAN/WLAN; tracking AP association failures and controller health prevents silent outages during promotions.
- **App/TA:** Wi-Fi controller syslog / SNMP trap HEC
- **Data Sources:** `index=retail` `sourcetype="wifi:controller"` (store_id, ap_name, client_count, assoc_failures, cpu_pct)
- **SPL:**
```spl
index=retail sourcetype="wifi:controller"
| bin _time span=5m
| stats sum(assoc_failures) as fails, avg(client_count) as avg_clients, max(cpu_pct) as max_cpu by store_id, ap_name, _time
| eval fail_rate=if(avg_clients>0, round(100*fails/avg_clients,2), fails)
| where fails > 20 OR max_cpu > 85 OR fail_rate > 2
| table _time, store_id, ap_name, fails, avg_clients, max_cpu, fail_rate
```
- **Implementation:** Normalize vendor-specific fields in props/transforms; retain `ap_name` and `store_id` on every sample. Alert on controller CPU and on APs with repeated association failures compared to peers in the same store.
- **Visualization:** Time chart (assoc failures), Status grid (AP health), Line chart (controller CPU).
- **CIM Models:** N/A

---

### UC-21.6.4 · Foot Traffic Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** People-counting trends validate staffing and layout changes; anomaly detection on ingress rates highlights sensor drift or blocked entrances.
- **App/TA:** Retail IoT / people-counting platform via HEC
- **Data Sources:** `index=retail` `sourcetype="foottraffic:sensor"` (store_id, zone_id, inbound_count, outbound_count)
- **SPL:**
```spl
index=retail sourcetype="foottraffic:sensor"
| eval net_flow=inbound_count-outbound_count
| bin _time span=1h
| stats sum(inbound_count) as entries, sum(outbound_count) as exits by store_id, zone_id, _time
| eval dow=strftime(_time,"%w"), hr=strftime(_time,"%H")
| eventstats median(entries) as med_ent by store_id, zone_id, dow, hr
| eval ratio=if(med_ent>0, entries/med_ent, null)
| where ratio < 0.5 OR ratio > 1.8
| table _time, store_id, zone_id, entries, exits, med_ent, ratio
```
- **Implementation:** Align counts to store local time and exclude maintenance windows via a lookup. Compare same day-of-week baselines; investigate zones with sudden drops (blocked sensor) or spikes (configuration error).
- **Visualization:** Time chart (entries by zone), Heatmap (store × hour), Bar chart (week-over-week delta).
- **CIM Models:** N/A

---

### UC-21.6.5 · Click-and-Collect Order Fulfillment Cycle Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** BOPIS promises a pickup window; measuring pick-to-ready time exposes backlog in back-of-house systems and reduces customer wait complaints.
- **App/TA:** OMS / store fulfillment app via HEC
- **Data Sources:** `index=retail` `sourcetype="bopis:order"` (order_id, store_id, placed_epoch, ready_epoch, status)
- **SPL:**
```spl
index=retail sourcetype="bopis:order" status="fulfilled"
| eval cycle_sec=ready_epoch-placed_epoch
| where isnotnull(cycle_sec) AND cycle_sec > 0
| bin _time span=1h
| stats avg(cycle_sec) as avg_sec, perc95(cycle_sec) as p95_sec, count as orders by store_id, _time
| eval sla_breach=if(p95_sec > 3600 OR avg_sec > 2400, 1, 0)
| where sla_breach=1
| eval avg_min=round(avg_sec/60,1), p95_min=round(p95_sec/60,1)
| table _time, store_id, orders, avg_min, p95_min
```
- **Implementation:** Ensure `placed_epoch` and `ready_epoch` share a common clock (UTC). Join `order_id` to cancellation reasons in a separate search if needed. Tune SLA minutes per retail banner; alert operations when p95 exceeds the published pickup promise.
- **Visualization:** Histogram (cycle time distribution), Time chart (avg vs p95), Table (stores breaching SLA).
- **CIM Models:** N/A

---

### UC-21.6.6 · E-Commerce Platform Checkout Funnel Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Checkout step latency directly impacts cart abandonment; segmenting by step isolates payment gateway, tax service, or session store delays.
- **App/TA:** E-commerce APM / web tier logs via HEC
- **Data Sources:** `index=retail` `sourcetype="ecom:checkout"` (session_id, step_name, latency_ms, http_status)
- **SPL:**
```spl
index=retail sourcetype="ecom:checkout"
| where http_status < 400
| bin _time span=5m
| stats avg(latency_ms) as avg_ms, perc95(latency_ms) as p95_ms, count as n by step_name, _time
| where p95_ms > 1500 OR avg_ms > 800
| sort step_name, _time
| table _time, step_name, n, avg_ms, p95_ms
```
- **Implementation:** Instrument each funnel step with consistent `step_name` values. Filter bots via a flag if present. Use side-by-side panels for web vs mobile app sessions if `channel` exists.
- **Visualization:** Time chart (p95 by step), Bar chart (step ranking), Funnel diagram (conversion counts, separate panel).
- **CIM Models:** N/A

---

### UC-21.6.7 · Inventory Replenishment Trigger Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Reorder points that fire too late cause stockouts; false triggers inflate carrying costs. Comparing suggested orders to actual on-hand movement validates replenishment rules.
- **App/TA:** IMS / replenishment engine via HEC
- **Data Sources:** `index=retail` `sourcetype="inventory:reorder"` (sku_id, store_id, on_hand_qty, reorder_point, suggested_qty, trigger_time)
- **SPL:**
```spl
index=retail sourcetype="inventory:reorder"
| eval at_or_below=if(on_hand_qty <= reorder_point, 1, 0)
| eval overshoot=if(on_hand_qty > reorder_point*1.5 AND suggested_qty > 0, 1, 0)
| stats sum(at_or_below) as hits, sum(overshoot) as bad_triggers, count as evals by store_id
| eval hit_rate=round(100*hits/nullif(evals,0),2), bad_pct=round(100*bad_triggers/nullif(evals,0),2)
| where bad_pct > 10 OR hit_rate < 60
| table store_id, evals, hits, hit_rate, bad_triggers, bad_pct
```
- **Implementation:** Snapshot replenishment evaluations daily or per batch run. Join promotional calendars to explain expected volatility. Feed findings to supply-chain analysts to tune safety stock parameters.
- **Visualization:** Scatter (on_hand vs reorder_point), Bar chart (bad trigger % by store), Table (SKUs with repeated misfires).
- **CIM Models:** N/A

---

### UC-21.6.8 · Store HVAC and Energy Consumption Optimization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** HVAC anomalies increase energy spend and affect cold-chain adjacent zones; trending kWh against occupancy and outdoor air temperature supports sustainability KPIs.
- **App/TA:** BMS / smart meter HEC
- **Data Sources:** `index=retail` `sourcetype="store:energy"` (store_id, kwh, zone_temp_f, hvac_mode, oa_temp_f)
- **SPL:**
```spl
index=retail sourcetype="store:energy"
| bin _time span=1h
| stats sum(kwh) as kwh_h, avg(zone_temp_f) as avg_temp, values(hvac_mode) as modes by store_id, _time
| eval wday=strftime(_time,"%w"), hour=strftime(_time,"%H")
| eventstats median(kwh_h) as med_kwh by store_id, wday, hour
| eval energy_ratio=if(med_kwh>0, round(kwh_h/med_kwh,2), null)
| where energy_ratio > 1.35 OR avg_temp < 65 OR avg_temp > 78
| table _time, store_id, kwh_h, med_kwh, energy_ratio, avg_temp, modes
```
- **Implementation:** Align BMS points to store open hours via lookup. Exclude demand-response events if tagged. Pair with foot traffic from `foottraffic:sensor` in a dashboard for joint review.
- **Visualization:** Time chart (kWh vs baseline), Line chart (zone temp vs OA temp), Bar chart (energy ratio by store).
- **CIM Models:** N/A

---

### UC-21.6.9 · Digital Signage Content Delivery Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Failed content pulls leave blank or stale screens during campaigns; monitoring download success and player heartbeat protects brand and promotional compliance.
- **App/TA:** Digital signage CMS / player agent via HEC
- **Data Sources:** `index=retail` `sourcetype="signage:health"` (store_id, player_id, content_id, download_status, last_sync_epoch)
- **SPL:**
```spl
index=retail sourcetype="signage:health"
| eval sync_age_sec=now()-last_sync_epoch
| eval healthy=if(lower(download_status)="ok" AND sync_age_sec < 900, 1, 0)
| stats avg(healthy) as ok_frac by store_id, player_id
| eval health_pct=round(ok_frac*100,2)
| where health_pct < 95
| table store_id, player_id, health_pct
```
- **Implementation:** Standardize `download_status` across vendors. Alert when players miss sync for longer than the campaign refresh interval. Group by region for NOC-style triage.
- **Visualization:** Status grid (player × store), Single value (unhealthy %), Timeline (failed downloads).
- **CIM Models:** N/A

---

### UC-21.6.10 · Mobile POS Device Battery and Connectivity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** mPOS devices that drop offline or run low on battery interrupt line-busting during peaks; proactive swaps reduce abandoned transactions.
- **App/TA:** MDM / mPOS telemetry via HEC
- **Data Sources:** `index=retail` `sourcetype="mpos:device"` (device_id, store_id, battery_pct, rssi_dbm, last_seen_epoch)
- **SPL:**
```spl
index=retail sourcetype="mpos:device"
| eval age_sec=now()-last_seen_epoch
| eval at_risk=if(battery_pct < 20 OR rssi_dbm < -80 OR age_sec > 300, 1, 0)
| where at_risk=1
| stats latest(battery_pct) as batt, latest(rssi_dbm) as rssi, max(age_sec) as max_age by store_id, device_id
| sort store_id, - max_age
| table store_id, device_id, batt, rssi, max_age
```
- **Implementation:** Ingest periodic telemetry from MDM or the payment app SDK. Map `device_id` to assigned associate in a lookup for dispatch. Exclude devices in charging cradles if `docked` is available.
- **Visualization:** Table (at-risk devices), Histogram (battery distribution), Map (store locations if lat/long present).
- **CIM Models:** N/A

---

### UC-21.6.11 · Loss Prevention Camera System Uptime
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Operational visibility into VMS/NVR stream health supports store safety and incident review workflows without duplicating fraud analytics covered elsewhere.
- **App/TA:** VMS health feed via HEC
- **Data Sources:** `index=retail` `sourcetype="camera:status"` (store_id, camera_id, stream_state, bitrate_kbps, last_frame_epoch)
- **SPL:**
```spl
index=retail sourcetype="camera:status"
| eval frame_age=now()-last_frame_epoch
| eval up=if(lower(stream_state)="up" AND frame_age < 60 AND bitrate_kbps > 100, 1, 0)
| stats avg(up) as up_frac by store_id, camera_id
| eval uptime_pct=round(up_frac*100,2)
| where uptime_pct < 99
| table store_id, camera_id, uptime_pct
```
- **Implementation:** Poll or stream VMS health every minute; normalize `stream_state` vocabulary. Exclude planned maintenance windows via lookup. Escalate to LP and facilities when entire aisles show degraded uptime.
- **Visualization:** Heatmap (camera × hour uptime), Table (worst cameras), Single value (stores below target).
- **CIM Models:** N/A

---

### UC-21.6.12 · Multi-Location Store Infrastructure Comparison
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Benchmarking composite health scores across stores highlights underperforming sites for capital planning and regional support prioritization.
- **App/TA:** Aggregated retail operations index
- **Data Sources:** `index=retail` `sourcetype="store:infra"` (store_id, health_score, pos_latency_ms, wifi_issue_count, energy_kwh_day)
- **SPL:**
```spl
index=retail sourcetype="store:infra"
| bin _time span=1d
| stats latest(health_score) as health, avg(pos_latency_ms) as avg_pos, sum(wifi_issue_count) as wifi_issues, latest(energy_kwh_day) as kwh by store_id, _time
| eventstats median(health) as med_health, median(avg_pos) as med_pos by _time
| eval pos_delta=avg_pos-med_pos
| where health < med_health*0.9 OR pos_delta > 200 OR wifi_issues > 15
| sort health
| table _time, store_id, health, med_health, avg_pos, pos_delta, wifi_issues, kwh
```
- **Implementation:** Populate `store:infra` from nightly ETL that rolls up POS, Wi-Fi, and energy KPIs per store. Keep scoring methodology documented for audit. Use for regional scorecards rather than real-time alerting unless scores refresh hourly.
- **Visualization:** Bar chart (health score by store), Box plot (score distribution), Table (bottom quartile stores).
- **CIM Models:** N/A

---

### 21.7 Aviation and Airport Operations

**Primary App/TA:** Airport Ground Operations App (Splunkbase 7793), Airport CIM for Splunk (GitHub splunk/airport_cim_for_splunk), custom HEC inputs from A-CDM, BHS, and airport SCADA.

**Data Sources:** A-CDM feeds, baggage BRS messages, airport SCADA alarms, queue camera systems, FIDS data, airfield vehicle tracking, gate management systems.

---

### UC-21.7.1 · Baggage Handling System Throughput and Misroute Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault
- **Value:** Low BHS throughput and rising misroutes delay connections and drive mishandled-bag metrics; correlating belt rates with sort errors focuses maintenance on diverters and scanners.
- **App/TA:** Airport Ground Operations App, BHS message feed via HEC
- **Data Sources:** `index=airport` `sourcetype="airport:baggage"` (flight_id, bag_tag, sort_destination, actual_destination, belt_id, scan_time)
- **SPL:**
```spl
index=airport sourcetype="airport:baggage"
| eval misroute=if(sort_destination!=actual_destination,1,0)
| bin _time span=15m
| stats count as bags, sum(misroute) as misroutes, dc(bag_tag) as unique_bags by belt_id, _time
| eval misroute_pct=round(100*misroutes/nullif(bags,0),2)
| where misroute_pct > 2 OR bags < 50
| table _time, belt_id, bags, misroutes, misroute_pct
```
- **Implementation:** Parse BSM/BUM messages or vendor XML into normalized fields. Validate `sort_destination` against flight plan lookups when available. Alert BHS control for sustained misroute rates above SLA.
- **Visualization:** Time chart (bags per belt), Bar chart (misroute %), Sankey (planned vs actual sort, if supported).
- **CIM Models:** N/A

---

### UC-21.7.2 · Security Lane Processing Time and Queue Length
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Passenger screening wait times drive missed flights and terminal congestion; monitoring queue depth and lane throughput supports dynamic staffing.
- **App/TA:** Queue analytics / security lane sensors via HEC
- **Data Sources:** `index=airport` `sourcetype="airport:security"` (terminal_id, lane_id, queue_depth, wait_time_sec, throughput_pph)
- **SPL:**
```spl
index=airport sourcetype="airport:security"
| bin _time span=5m
| stats avg(wait_time_sec) as avg_wait, max(queue_depth) as max_q, avg(throughput_pph) as avg_thr by lane_id, terminal_id, _time
| where avg_wait > 600 OR max_q > 80 OR avg_thr < 120
| eval avg_wait_min=round(avg_wait/60,1)
| table _time, terminal_id, lane_id, avg_wait_min, max_q, avg_thr
```
- **Implementation:** Ingest lidar or camera analytics exports with consistent `lane_id`. Align with airport peak bank schedules via CSV lookup. Coordinate alerts with security operations, not for access control decisions alone.
- **Visualization:** Time chart (wait time by lane), Area chart (queue depth), Heatmap (terminal × hour).
- **CIM Models:** N/A

---

### UC-21.7.3 · Aircraft Turnaround Time Monitoring (A-CDM)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** A-CDM milestones expose ground-handling delays that compress departure slots; tracking block-on to off-block variance improves OTP and stand utilization.
- **App/TA:** A-CDM feed via HEC, Airport CIM for Splunk
- **Data Sources:** `index=airport` `sourcetype="acdm:turnaround"` (flight_id, stand_id, block_on, target_off, actual_off, milestone_name, milestone_time)
- **SPL:**
```spl
index=airport sourcetype="acdm:turnaround" milestone_name="ACTUAL_OFF_BLOCK"
| eval turnaround_sec=actual_off-block_on
| eval target_turn_sec=target_off-block_on
| eval variance_sec=turnaround_sec-target_turn_sec
| where variance_sec > 900
| stats avg(variance_sec) as avg_var, count as late_turns by stand_id
| eval avg_var_min=round(avg_var/60,1)
| sort - avg_var
| table stand_id, late_turns, avg_var_min
```
- **Implementation:** Normalize all timestamps to UTC with clear time zone fields in raw data. Join to airline handler codes if present for accountability. Use for operational review; validate calculations against the airport CDM tool of record.
- **Visualization:** Gantt-style timeline (per flight), Histogram (turnaround distribution), Table (stands with chronic variance).
- **CIM Models:** N/A

---

### UC-21.7.4 · Airfield Ground Vehicle Tracking and Geofencing
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Fault
- **Value:** Vehicles breaching movement area boundaries create runway incursion risk; monitoring GPS tracks against geofences supports safety management and audit evidence.
- **App/TA:** Airfield vehicle telematics via HEC
- **Data Sources:** `index=airport` `sourcetype="airfield:vehicle"` (vehicle_id, lat, lon, speed_kph, geofence_id, breach_flag)
- **SPL:**
```spl
index=airport sourcetype="airfield:vehicle"
| where breach_flag=1 OR speed_kph > 40
| bin _time span=1m
| stats count as events, values(geofence_id) as zones by vehicle_id, _time
| where events >= 2
| table _time, vehicle_id, events, zones
```
- **Implementation:** Stream or batch position fixes; compute `breach_flag` at the edge if possible for lower latency. Use Splunk for trending and investigation; pair with SMS alerts for real-time incursion systems. Retain maps for post-incident review only with proper access controls.
- **Visualization:** Map (vehicle positions), Timeline (breach events), Table (repeat offenders).
- **CIM Models:** N/A

---

### UC-21.7.5 · Flight Information Display System (FIDS) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Blank or stale FIDS erode passenger trust and increase gate crowding; heartbeat and content sync monitoring ensures displays match the operational data feed.
- **App/TA:** FIDS CMS / player health via HEC
- **Data Sources:** `index=airport` `sourcetype="fids:status"` (display_id, terminal_id, sync_lag_sec, content_version, online_flag)
- **SPL:**
```spl
index=airport sourcetype="fids:status"
| eval healthy=if(online_flag=1 AND sync_lag_sec < 120, 1, 0)
| stats avg(healthy) as ok_frac, max(sync_lag_sec) as max_lag by terminal_id, display_id
| eval uptime_pct=round(ok_frac*100,2)
| where uptime_pct < 99 OR max_lag > 300
| table terminal_id, display_id, uptime_pct, max_lag
```
- **Implementation:** Ingest per-display polls every minute; join `content_version` to the master feed version from a KV store or lookup. Page duty manager when entire banks of displays degrade together (network path issue).
- **Visualization:** Status grid (display × terminal), Time chart (sync lag), Single value (offline count).
- **CIM Models:** N/A

---

### UC-21.7.6 · Airport Wi-Fi Capacity and Congestion Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Passenger Wi-Fi saturation during banks degrades airline apps and airport services; tracking airtime utilization and retries guides AP density and backhaul upgrades.
- **App/TA:** WLAN controller syslog via HEC
- **Data Sources:** `index=airport` `sourcetype="airport:wifi"` (ap_name, terminal_id, channel_util_pct, client_count, retry_rate_pct)
- **SPL:**
```spl
index=airport sourcetype="airport:wifi"
| bin _time span=5m
| stats avg(channel_util_pct) as avg_util, max(client_count) as max_clients, avg(retry_rate_pct) as avg_retry by ap_name, terminal_id, _time
| where avg_util > 75 OR avg_retry > 15 OR max_clients > 200
| table _time, terminal_id, ap_name, avg_util, max_clients, avg_retry
```
- **Implementation:** Normalize vendor metrics to `channel_util_pct` and `retry_rate_pct`. Compare concourse peers; exclude maintenance SSIDs. Correlate with passenger counts from `terminal:flow` when available.
- **Visualization:** Heatmap (AP × hour utilization), Line chart (client count), Bar chart (top congested APs).
- **CIM Models:** N/A

---

### UC-21.7.7 · Runway and Taxiway Lighting System Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Lighting circuit faults affect night and low-visibility operations; consolidating SCADA alarms with last-known good states speeds electrical maintenance dispatch.
- **App/TA:** Airfield lighting SCADA via HEC
- **Data Sources:** `index=airport` `sourcetype="airfield:lighting"` (circuit_id, runway_id, intensity_pct, comm_ok, alarm_state)
- **SPL:**
```spl
index=airport sourcetype="airfield:lighting"
| eval fault=if(comm_ok=0 OR lower(alarm_state)!="normal" OR intensity_pct < 50, 1, 0)
| where fault=1
| stats latest(intensity_pct) as intensity, latest(alarm_state) as alarm, latest(comm_ok) as comm_ok by runway_id, circuit_id
| sort runway_id, circuit_id
| table runway_id, circuit_id, intensity, alarm, comm_ok
```
- **Implementation:** Map SCADA points to runway/taxi identifiers used in NOTAM workflows. Do not replace airfield lighting control systems; Splunk is for visibility and trending. Filter planned test events via maintenance tags.
- **Visualization:** Single value (circuits in fault), Table (runway × circuit), Timeline (alarm transitions).
- **CIM Models:** N/A

---

### UC-21.7.8 · Gate Allocation Optimization Analytics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Gate churn and long towing distances waste ground time; analyzing assigned vs actual gate usage supports stand planning and reduces conflicts.
- **App/TA:** AODB / gate management via HEC
- **Data Sources:** `index=airport` `sourcetype="gate:allocation"` (flight_id, gate_id, planned_gate, actual_gate, change_count, tow_required_flag)
- **SPL:**
```spl
index=airport sourcetype="gate:allocation"
| eval gate_mismatch=if(planned_gate!=actual_gate,1,0)
| stats sum(gate_mismatch) as changes, sum(tow_required_flag) as tows, count as flights by gate_id
| eval change_rate=round(100*changes/nullif(flights,0),2)
| where change_rate > 25 OR tows > 10
| sort - change_rate
| table gate_id, flights, changes, change_rate, tows
```
- **Implementation:** Refresh from AODB snapshots or event stream on gate changes. Join aircraft size class if available to explain constraints. Use monthly reports for planning rather than minute-by-minute alerts.
- **Visualization:** Bar chart (change rate by gate), Stacked bar (tows vs no tow), Table (top volatile gates).
- **CIM Models:** N/A

---

### UC-21.7.9 · Passenger Flow and Terminal Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Understanding dwell and flow between checkpoints and gates helps prevent overcrowding and supports staffing during irregular operations.
- **App/TA:** Wi-Fi probe / Bluetooth / lidar analytics via HEC
- **Data Sources:** `index=airport` `sourcetype="terminal:flow"` (terminal_id, zone_id, occupancy_est, flow_rate_ppm)
- **SPL:**
```spl
index=airport sourcetype="terminal:flow"
| bin _time span=5m
| stats avg(occupancy_est) as occ, max(flow_rate_ppm) as peak_flow by terminal_id, zone_id, _time
| eval date_hour=strftime(_time,"%H"), date_wday=strftime(_time,"%w")
| eventstats median(occ) as med_occ by terminal_id, zone_id, date_hour, date_wday
| eval occ_ratio=if(med_occ>0, round(occ/med_occ,2), null)
| where occ > 5000 OR occ_ratio > 1.4 OR peak_flow > 120
| table _time, terminal_id, zone_id, occ, med_occ, occ_ratio, peak_flow
```
- **Implementation:** Calibrate occupancy models against manual counts quarterly. Mask precise sensor locations in dashboards if required by security. Combine with `airport:security` wait times for holistic terminal health.
- **Visualization:** Heatmap (zone × time occupancy), Line chart (flow rate), Area chart (terminal totals).
- **CIM Models:** N/A

---

### UC-21.7.10 · Airport SCADA Alarm Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Airports rely on SCADA for jet bridges, baggage power, and utilities; alarm floods and unacked critical points risk missed responses during IROPS.
- **App/TA:** Airport SCADA historian / alarm export via HEC
- **Data Sources:** `index=airport` `sourcetype="airport:scada"` (subsystem, alarm_id, priority, ack_state, description)
- **SPL:**
```spl
index=airport sourcetype="airport:scada"
| where lower(ack_state)!="acked" AND priority IN ("1","2","critical","high")
| bin _time span=5m
| stats count as open_alarms, dc(alarm_id) as distinct_points by subsystem, _time
| where open_alarms > 10
| table _time, subsystem, open_alarms, distinct_points
```
- **Implementation:** Normalize priority enumerations across subsystems. Route critical unacked alarms to facilities NOC; use dedup keys on `alarm_id` to avoid double counting. Pair with maintenance windows lookup to suppress expected noise.
- **Visualization:** Timeline (alarm bursts), Bar chart (open alarms by subsystem), Single value (unacked critical count).
- **CIM Models:** N/A

---
### 21.8 Telecommunications Operations

**Primary App/TA:** Custom HEC/syslog inputs from network elements, OSS/BSS systems, SNMP from core/RAN equipment, CDN logs.

**Data Sources:** SNMP from network elements, syslog from core/RAN, OSS/BSS application logs, CDN logs, performance counters, provisioning systems.

---

### UC-21.8.1 · RAN Cell Site Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Cell site outages directly impact subscriber coverage and handover success; tracking up/down transitions and sustained downtime focuses radio access field teams before KPIs degrade across the footprint.
- **App/TA:** Custom HEC (RAN EMS / element manager export)
- **Data Sources:** `index=telecom` `sourcetype="ran:cellsite"` (site_id, cell_id, operational_state, last_transition_epoch)
- **SPL:**
```spl
index=telecom sourcetype="ran:cellsite"
| eval up=if(lower(operational_state) IN ("up","enabled","on"),1,0)
| bin _time span=5m
| stats avg(up) as avail_frac, min(up) as min_state by site_id, cell_id, _time
| eval avail_pct=round(avail_frac*100,2)
| where min_state=0 OR avail_pct < 99.5
| table _time, site_id, cell_id, avail_pct, min_state
```
- **Implementation:** Ingest periodic SNMP or EMS polls with normalized `operational_state` strings. Align site identifiers with inventory CMDB. Alert on sustained down segments and flapping (multiple transitions per hour) using a follow-on search on `last_transition_epoch`.
- **Visualization:** Time chart (availability % by site), Status grid (cell × site), Single value (sites below SLA).
- **CIM Models:** N/A

---

### UC-21.8.2 · Core Network Element Health (MME, SGW, PGW)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Core packet gateways and mobility management anchor subscriber sessions; correlating CPU, session load, and alarm states helps capacity and incident teams isolate a degrading blade before mass detach.
- **App/TA:** Custom HEC (EPC/5GC performance counters)
- **Data Sources:** `index=telecom` `sourcetype="core:element"` (element_id, element_type, cpu_pct, active_sessions, alarm_severity)
- **SPL:**
```spl
index=telecom sourcetype="core:element"
| eval sev_score=case(lower(alarm_severity) IN ("critical","1"),4, lower(alarm_severity) IN ("major","2"),3, lower(alarm_severity) IN ("minor","3"),2, true(),0)
| where cpu_pct > 85 OR active_sessions > 800000 OR sev_score >= 3
| bin _time span=5m
| stats max(cpu_pct) as max_cpu, max(active_sessions) as max_sess, max(sev_score) as max_alarm by element_id, element_type, _time
| table _time, element_id, element_type, max_cpu, max_sess, max_alarm
```
- **Implementation:** Map vendor counter names into `cpu_pct` and `active_sessions` in transforms. Exclude planned maintenance windows via lookup on `element_id`. Thresholds vary by platform—tune per NE class and license limits.
- **Visualization:** Line chart (CPU and sessions by element), Table (top loaded nodes), Single value (elements in alarm).
- **CIM Models:** N/A

---

### UC-21.8.3 · Subscriber Provisioning Workflow Completion Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Failed SIM activation or profile pushes strand subscribers on support calls; measuring end-to-end workflow success by step exposes orchestration, HLR/HSS, and BSS handoffs without CDR-volume analytics.
- **App/TA:** OSS provisioning orchestrator via HEC
- **Data Sources:** `index=telecom` `sourcetype="provisioning:workflow"` (workflow_id, msisdn, step_name, status, duration_ms)
- **SPL:**
```spl
index=telecom sourcetype="provisioning:workflow"
| eval ok=if(lower(status) IN ("success","completed","ok"),1,0)
| stats count as total, sum(ok) as ok_n by step_name
| eval success_pct=round(100*ok_n/nullif(total,0),2)
| where success_pct < 98 OR total < 10
| sort success_pct
| table step_name, total, ok_n, success_pct
```
- **Implementation:** Emit one event per workflow step completion with consistent `workflow_id` for optional transaction tracing. Schedule hourly; drill into `status` values for failure taxonomy. Keep separate from mediation latency (UC-21.8.5).
- **Visualization:** Bar chart (success % by step), Time chart (daily success trend), Table (worst steps).
- **CIM Models:** N/A

---

### UC-21.8.4 · Network Capacity Planning (Spectrum Utilization Trending)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Performance
- **Value:** Rising PRB or downlink utilization trends drive sector splits and carrier adds; long-window trending supports RF engineering without duplicating CDR-based traffic analytics (Cat 5.12).
- **App/TA:** RAN performance management feed via HEC
- **Data Sources:** `index=telecom` `sourcetype="spectrum:utilization"` (site_id, cell_id, dl_prb_util_pct, ul_prb_util_pct, sample_period_sec)
- **SPL:**
```spl
index=telecom sourcetype="spectrum:utilization"
| eval peak_util=max(dl_prb_util_pct, ul_prb_util_pct)
| bin _time span=1d
| stats avg(peak_util) as avg_peak, perc95(peak_util) as p95_peak by site_id, cell_id, _time
| eventstats median(avg_peak) as med_site by site_id
| eval growth_ratio=if(med_site>0, round(avg_peak/med_site,2), null)
| where p95_peak > 85 OR growth_ratio > 1.15
| table _time, site_id, cell_id, avg_peak, p95_peak, growth_ratio
```
- **Implementation:** Aggregate busy-hour samples per operator policy; store `sample_period_sec` for weighting. Join sector metadata (band, azimuth) via lookup for planning reports. Use weekly baselines to smooth day-of-week noise.
- **Visualization:** Line chart (PRB util trend), Heatmap (cell × week), Bar chart (sectors over 85% p95).
- **CIM Models:** N/A

---

### UC-21.8.5 · Service Activation and Billing Mediation Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Mediation pipelines must deliver rated records to billing within windows; end-to-end latency and backlog depth prevent revenue leakage and rating disputes distinct from raw CDR analytics use cases.
- **App/TA:** Mediation platform logs via HEC
- **Data Sources:** `index=telecom` `sourcetype="mediation:event"` (batch_id, records_in, records_out, latency_ms, queue_depth)
- **SPL:**
```spl
index=telecom sourcetype="mediation:event"
| bin _time span=5m
| stats avg(latency_ms) as avg_lat, perc95(latency_ms) as p95_lat, max(queue_depth) as max_q, sum(records_in) as vol by _time
| where avg_lat > 120000 OR p95_lat > 300000 OR max_q > 500000
| eval avg_min=round(avg_lat/60000,2), p95_min=round(p95_lat/60000,2)
| table _time, avg_min, p95_min, max_q, vol
```
- **Implementation:** Normalize timestamps to when batches complete, not file arrival. Alert on sustained queue growth with derivative search on `queue_depth`. Coordinate thresholds with billing close calendar.
- **Visualization:** Time chart (latency and queue depth), Area chart (records processed), Single value (backlog breach).
- **CIM Models:** N/A

---

### UC-21.8.6 · OSS/BSS System Integration Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** API and message bus integrations between CRM, inventory, and activation systems fail silently under load; HTTP error rates and timeout counts isolate brittle adapters before orders stall.
- **App/TA:** API gateway / ESB logs via HEC
- **Data Sources:** `index=telecom` `sourcetype="ossbss:integration"` (interface_id, http_status, latency_ms, error_code)
- **SPL:**
```spl
index=telecom sourcetype="ossbss:integration"
| eval fail=if(http_status>=500 OR isnotnull(error_code),1,0)
| bin _time span=5m
| stats count as calls, sum(fail) as fails, avg(latency_ms) as avg_ms by interface_id, _time
| eval fail_pct=round(100*fails/nullif(calls,0),2)
| where fail_pct > 2 OR avg_ms > 3000
| table _time, interface_id, calls, fails, fail_pct, avg_ms
```
- **Implementation:** Tag interfaces in the gateway; exclude health-check paths. Add optional `partner_system` field for drilldown. Pair with synthetic probes where logs alone miss silent drops.
- **Visualization:** Time chart (fail % and latency), Bar chart (worst interfaces), Table (error_code top values).
- **CIM Models:** N/A

---

### UC-21.8.7 · Customer Trouble Ticket Mean Time to Resolution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** MTTR for access and core tickets reflects operational maturity; trending resolution intervals by category and region highlights training gaps and vendor SLA performance.
- **App/TA:** ITSM / trouble ticket export via HEC
- **Data Sources:** `index=telecom` `sourcetype="troubleticket:event"` (ticket_id, category, region, created_epoch, resolved_epoch, status)
- **SPL:**
```spl
index=telecom sourcetype="troubleticket:event" lower(status)="resolved"
| eval mtr_h=(resolved_epoch-created_epoch)/3600
| where isnotnull(mtr_h) AND mtr_h >= 0
| bin _time span=1d
| stats avg(mtr_h) as avg_mtr, perc90(mtr_h) as p90_mtr, count as tickets by category, region, _time
| where avg_mtr > 24 OR p90_mtr > 72
| eval avg_mtr_r=round(avg_mtr,2), p90_mtr_r=round(p90_mtr,2)
| table _time, category, region, tickets, avg_mtr_r, p90_mtr_r
```
- **Implementation:** Ensure `created_epoch`/`resolved_epoch` are UTC. Exclude cancelled tickets in a separate clause if needed. Refresh from ITSM nightly or near-real-time for NOC dashboards.
- **Visualization:** Box plot (MTTR distribution), Line chart (trend by region), Bar chart (category comparison).
- **CIM Models:** N/A

---

### UC-21.8.8 · 5G NR gNodeB Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault
- **Value:** gNodeB throughput, latency, and drop metrics expose RF and transport issues before subscriber experience scores fall; focuses on RAN KPIs rather than core signaling traces (Cat 5.11).
- **App/TA:** 5G DU/CU performance export via HEC
- **Data Sources:** `index=telecom` `sourcetype="gnodeb:metrics"` (gnb_id, cell_id, dl_throughput_mbps, ul_throughput_mbps, rlc_drop_pct, latency_ms)
- **SPL:**
```spl
index=telecom sourcetype="gnodeb:metrics"
| bin _time span=15m
| stats avg(dl_throughput_mbps) as avg_dl, avg(ul_throughput_mbps) as avg_ul, avg(rlc_drop_pct) as avg_drop, avg(latency_ms) as avg_lat by gnb_id, cell_id, _time
| eventstats median(avg_dl) as med_dl by cell_id
| eval thr_ratio=if(med_dl>0, round(avg_dl/med_dl,2), null)
| where avg_drop > 1 OR avg_lat > 40 OR thr_ratio < 0.7
| table _time, gnb_id, cell_id, avg_dl, avg_ul, avg_drop, avg_lat, thr_ratio
```
- **Implementation:** Align PM file periods (15m/5m) and handle DST in `_time`. Use cell-level baselines for `thr_ratio`. Optional: join transport path ID if backhaul congestion is suspected.
- **Visualization:** Time chart (throughput and drops), Heatmap (cell × hour), Table (worst cells).
- **CIM Models:** N/A

---

### UC-21.8.9 · Network Slice Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Performance
- **Value:** Slices carry differentiated QoS commitments; monitoring allocated vs used bandwidth and session counts per slice supports enterprise SLAs and slice redesign.
- **App/TA:** 5GC NSSF/NSMF metrics via HEC
- **Data Sources:** `index=telecom` `sourcetype="slice:utilization"` (slice_id, dnn, committed_mbps, used_mbps, active_sessions)
- **SPL:**
```spl
index=telecom sourcetype="slice:utilization"
| eval util_pct=if(committed_mbps>0, round(100*used_mbps/committed_mbps,2), null)
| bin _time span=5m
| stats avg(util_pct) as avg_util, max(active_sessions) as peak_sess by slice_id, dnn, _time
| where avg_util > 90 OR peak_sess > 50000
| table _time, slice_id, dnn, avg_util, peak_sess
```
- **Implementation:** Normalize `committed_mbps` from slice templates; refresh when contracts change via KV. Alert enterprise account teams when sustained util > 90%. Distinct from generic core health (UC-21.8.2).
- **Visualization:** Line chart (util % by slice), Stacked area (sessions), Table (slices near exhaustion).
- **CIM Models:** N/A

---

### UC-21.8.10 · Content Delivery Network Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Low cache hit ratios increase origin load and subscriber latency; trending hit ratio by POP and content type guides cache sizing and TTL policy without analyzing subscriber CDRs.
- **App/TA:** CDN raw logs / analytics API via HEC
- **Data Sources:** `index=telecom` `sourcetype="cdn:performance"` (pop_id, cache_status, bytes_served, request_count)
- **SPL:**
```spl
index=telecom sourcetype="cdn:performance"
| eval hit=if(lower(cache_status) IN ("hit","tcp_hit","mem_hit"),1,0)
| bin _time span=1h
| stats sum(request_count) as reqs, sum(eval(if(hit=1,request_count,0))) as hit_reqs by pop_id, _time
| eval hit_ratio=round(100*hit_reqs/nullif(reqs,0),2)
| where hit_ratio < 85 AND reqs > 1000
| table _time, pop_id, reqs, hit_reqs, hit_ratio
```
- **Implementation:** Map vendor cache hit tokens to `cache_status` in props. Exclude purge and error responses from denominator if tagged. Compare POPs to identify misconfigured origins.
- **Visualization:** Line chart (hit ratio by POP), Bar chart (worst POPs), Map (if geo coordinates available).
- **CIM Models:** N/A

---

### 21.9 Water and Wastewater Utilities

**Primary App/TA:** Splunk Edge Hub, custom HEC inputs from SCADA/RTU systems, environmental sensors (MQTT), lab information management systems (LIMS).

**Data Sources:** SCADA/RTU data via Edge Hub or HEC, environmental sensors (MQTT), LIMS results, GIS/hydraulic model outputs, pump station PLCs.

---

### UC-21.9.1 · Treatment Plant Process Parameter Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Fault
- **Value:** pH, turbidity, and chlorine residual excursions threaten regulatory permits and public health; continuous trending flags filter or chemical feed issues before grab samples fail.
- **App/TA:** Splunk Edge Hub, SCADA HEC
- **Data Sources:** `index=water` `sourcetype="treatment:process"` (plant_id, basin_id, ph, turbidity_ntu, chlorine_mg_l, ph_min, ph_max, turbidity_max, chlorine_min)
- **SPL:**
```spl
index=water sourcetype="treatment:process"
| eval ph_breach=if(ph < ph_min OR ph > ph_max, 1, 0)
| eval turb_breach=if(turbidity_ntu > turbidity_max, 1, 0)
| eval chlorine_breach=if(chlorine_mg_l < chlorine_min, 1, 0)
| where ph_breach=1 OR turb_breach=1 OR chlorine_breach=1
| stats latest(ph) as ph, latest(turbidity_ntu) as turb, latest(chlorine_mg_l) as cl2, max(ph_breach) as ph_br, max(turb_breach) as tb_br, max(chlorine_breach) as cl_br by plant_id, basin_id
| table plant_id, basin_id, ph, turb, cl2, ph_br, tb_br, cl_br
```
- **Implementation:** Ingest DCS/PLC tags at 1–5 minute intervals; align limits per permit in fields or lookup. Route alerts to plant operators; retain Splunk as supervisory visibility alongside SCADA alarms.
- **Visualization:** Time chart (pH, turbidity, chlorine), Gauge (distance to limit), Table (active breaches).
- **CIM Models:** N/A

---

### UC-21.9.2 · Pump Station Run Time and Efficiency Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Excessive run hours or kWh per volume pumped signals impeller wear, valve issues, or wet-well setpoint drift; trending supports maintenance scheduling and energy cost control.
- **App/TA:** Pump station PLC via Edge Hub
- **Data Sources:** `index=water` `sourcetype="pump:station"` (station_id, pump_id, run_state, flow_m3h, power_kw, runtime_hr_day)
- **SPL:**
```spl
index=water sourcetype="pump:station" run_state=1
| eval kwh_per_m3=if(flow_m3h>0 AND power_kw>0, power_kw/flow_m3h, null)
| bin _time span=1d
| stats sum(runtime_hr_day) as run_hrs, avg(kwh_per_m3) as avg_intensity by station_id, pump_id, _time
| eventstats median(avg_intensity) as med_int by station_id, pump_id
| eval ratio=if(med_int>0, round(avg_intensity/med_int,2), null)
| where run_hrs > 20 OR ratio > 1.2
| table _time, station_id, pump_id, run_hrs, avg_intensity, ratio
```
- **Implementation:** Normalize `run_state` (1=on). Fill gaps in flow with null checks to avoid divide-by-zero. Baseline `kwh_per_m3` seasonally for irrigation-influenced stations.
- **Visualization:** Line chart (run hours and intensity), Bar chart (stations over baseline), Table (worst pumps).
- **CIM Models:** N/A

---

### UC-21.9.3 · Distribution System Pressure Zone Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Low pressure risks contamination and service complaints; high pressure stresses mains. Zone-level analytics isolate PRV faults and demand spikes faster than single-point alarms.
- **App/TA:** SCADA pressure telemetry via HEC
- **Data Sources:** `index=water` `sourcetype="pressure:zone"` (zone_id, pressure_psi, min_target_psi, max_target_psi, sensor_id)
- **SPL:**
```spl
index=water sourcetype="pressure:zone"
| eval breach=if(pressure_psi < min_target_psi OR pressure_psi > max_target_psi, 1, 0)
| bin _time span=5m
| stats min(pressure_psi) as min_p, max(pressure_psi) as max_p, max(breach) as any_breach by zone_id, _time
| where any_breach=1
| table _time, zone_id, min_p, max_p, any_breach
```
- **Implementation:** Multiple sensors per zone—use `stats` to aggregate. Join PRV asset IDs via lookup for work orders. Pair with demand forecasts during fire flow tests.
- **Visualization:** Time chart (pressure by zone), Single value (zones in breach), Map (zone centroids if GIS joined).
- **CIM Models:** N/A

---

### UC-21.9.4 · Sewer Overflow Early Warning
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Compliance
- **Value:** Rising wet-well levels during rainfall indicate capacity or blockage risk before SSO events; correlating level rise rate with rain intensity prioritizes inspections.
- **App/TA:** Sewer SCADA + weather feed via HEC
- **Data Sources:** `index=water` `sourcetype="sewer:level"` (structure_id, level_ft, high_alarm_ft, rainfall_in_hr)
- **SPL:**
```spl
index=water sourcetype="sewer:level"
| sort 0 structure_id, _time
| streamstats window=2 global=f current=f last(level_ft) as prev_level last(_time) as prev_t by structure_id
| eval dt_sec=_time-prev_t
| eval rise_ft_hr=if(dt_sec>0 AND isnotnull(prev_level), (level_ft-prev_level)*3600/dt_sec, null)
| eval risk=if(level_ft >= 0.9*high_alarm_ft OR (rainfall_in_hr > 0.5 AND rise_ft_hr > 0.5), 1, 0)
| where risk=1
| table _time, structure_id, level_ft, high_alarm_ft, rainfall_in_hr, rise_ft_hr
```
- **Implementation:** Align rain gauge timestamps to SCADA time zone. Tune `rise_ft_hr` using 1-minute samples if available. Integrate with CMMS for crew dispatch; document for NPDES reporting workflows.
- **Visualization:** Combo chart (level vs rainfall), Timeline (risk flags), Map (structures at risk).
- **CIM Models:** N/A

---

### UC-21.9.5 · Water Quality Compliance Sampling Automation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracking scheduled vs completed samples and lab receipt timestamps ensures permit coverage and reduces missed-route findings during audits.
- **App/TA:** LIMS / field sampling app via HEC
- **Data Sources:** `index=water` `sourcetype="water:compliance"` (sample_id, site_id, scheduled_epoch, collected_epoch, lab_received_epoch, parameter_set)
- **SPL:**
```spl
index=water sourcetype="water:compliance"
| eval collected_lag_h=(collected_epoch-scheduled_epoch)/3600
| eval lab_lag_h=(lab_received_epoch-collected_epoch)/3600
| where isnull(collected_epoch) OR collected_lag_h > 48 OR lab_lag_h > 72
| stats count as issues, dc(site_id) as sites_affected by parameter_set
| table parameter_set, issues, sites_affected
```
- **Implementation:** Ingest lifecycle events from LIMS and field mobile apps. Handle partial collections with status fields. Dashboard for compliance team; not a substitute for chain-of-custody systems.
- **Visualization:** Table (overdue samples), Bar chart (issues by parameter set), Calendar heatmap (collection completion).
- **CIM Models:** N/A

---

### UC-21.9.6 · SCADA RTU Communication Health Across Remote Sites
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Silent RTU loss leaves operators blind at lift stations and remote wells; age since last good poll drives prioritized truck rolls before overflows.
- **App/TA:** Splunk Edge Hub, SCADA front-end logs
- **Data Sources:** `index=water` `sourcetype="scada:rtu"` (rtu_id, site_id, poll_ok, response_ms)
- **SPL:**
```spl
index=water sourcetype="scada:rtu"
| stats latest(_time) as last_ok, latest(response_ms) as last_ms, latest(poll_ok) as last_poll by rtu_id, site_id
| eval age_sec=now()-last_ok
| where last_poll=0 OR age_sec > 900 OR last_ms > 5000
| table site_id, rtu_id, last_poll, last_ms, age_sec
```
- **Implementation:** Map protocol timeouts to `poll_ok=0`. Set `age_sec` threshold to 3× expected scan period. Exclude maintenance windows via site lookup.
- **Visualization:** Status grid (RTU × site), Table (oldest staleness), Line chart (response time trend).
- **CIM Models:** N/A

---

### UC-21.9.7 · Water Loss and Non-Revenue Water Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault
- **Value:** Comparing master meter inflows to zone consumption and night minimum flows highlights leaks, unauthorized use, and meter drift—supporting NRW reduction programs.
- **App/TA:** AMI + district meter HEC
- **Data Sources:** `index=water` `sourcetype="water:flow"` (zone_id, supply_m3_day, billed_m3_day, min_night_flow_m3h)
- **SPL:**
```spl
index=water sourcetype="water:flow"
| eval nrw_pct=if(supply_m3_day>0, round(100*(supply_m3_day-billed_m3_day)/supply_m3_day,2), null)
| where nrw_pct > 25 OR min_night_flow_m3h > 10
| bin _time span=1d
| stats latest(nrw_pct) as nrw_pct, latest(min_night_flow_m3h) as mnf by zone_id, _time
| sort - nrw_pct
| table _time, zone_id, nrw_pct, mnf
```
- **Implementation:** Align daily rollups to billing cycles. Use minimum night flow from 2–4 AM window. Join pipe age and material via GIS for remediation prioritization.
- **Visualization:** Choropleth or map (NRW % by zone), Time chart (NRW trend), Bar chart (zones over threshold).
- **CIM Models:** N/A

---

### UC-21.9.8 · Lift Station Failure Prediction
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance
- **Value:** Rising vibration with stable level, or current draw creep before thermal trip, predicts pump bearing wear and wet-well pump failures—reducing emergency callouts.
- **App/TA:** Vibration and motor VFD telemetry via Edge Hub
- **Data Sources:** `index=water` `sourcetype="liftstation:sensor"` (station_id, pump_id, vibration_mm_s, motor_amps, wet_well_level_ft, running_flag)
- **SPL:**
```spl
index=water sourcetype="liftstation:sensor" running_flag=1
| bin _time span=1h
| stats avg(vibration_mm_s) as vib, avg(motor_amps) as amps, avg(wet_well_level_ft) as lvl by station_id, pump_id, _time
| eventstats median(vib) as med_vib, median(amps) as med_amp by pump_id
| eval vib_ratio=if(med_vib>0, round(vib/med_vib,2), null), amp_ratio=if(med_amp>0, round(amps/med_amp,2), null)
| where vib_ratio > 1.5 OR amp_ratio > 1.25
| table _time, station_id, pump_id, vib, amps, lvl, vib_ratio, amp_ratio
```
- **Implementation:** Baseline per pump when healthy; exclude dry-run periods with `running_flag`. Optional: send features to ML Toolkit for supervised models. Maintain safety interlocks in PLC, not Splunk.
- **Visualization:** Time chart (vibration and current), Scatter (vibration vs level), Table (pumps flagged).
- **CIM Models:** N/A

---

### 21.10 Insurance and Claims Processing

**Primary App/TA:** Splunk App for Fraud Analytics, Behavioral Profiling App, custom HEC inputs from claims management and policy administration systems.

**Data Sources:** Claims management system logs, policy administration system, fraud analytics platform, behavioral profiling app, underwriting systems.

---

### UC-21.10.1 · Claims Processing Cycle Time Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** End-to-end cycle time from FNOL to settlement drives customer satisfaction and loss adjustment expense; segmenting by line of business exposes bottlenecks in adjuster queues and vendor turnaround.
- **App/TA:** Claims management system via HEC
- **Data Sources:** `index=insurance` `sourcetype="claims:lifecycle"` (claim_id, lob, opened_epoch, settled_epoch, status)
- **SPL:**
```spl
index=insurance sourcetype="claims:lifecycle" lower(status)="settled"
| eval cycle_d=(settled_epoch-opened_epoch)/86400
| where isnotnull(cycle_d) AND cycle_d >= 0
| bin _time span=1w
| stats avg(cycle_d) as avg_days, perc90(cycle_d) as p90_days, count as claims by lob, _time
| where avg_days > 30 OR p90_days > 60
| eval avg_days_r=round(avg_days,1), p90_days_r=round(p90_days,1)
| table _time, lob, claims, avg_days_r, p90_days_r
```
- **Implementation:** Normalize epoch fields from the claims platform; exclude reopened claims with a flag if present. Tune SLAs by LOB. Pair with staffing dashboards for operational planning—not banking fraud (Cat 10.12).
- **Visualization:** Line chart (cycle time trend), Box plot (by LOB), Table (breaches).
- **CIM Models:** N/A

---

### UC-21.10.2 · First Notice of Loss Channel Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Shifts in FNOL volume by web, mobile, IVR, or agent channel indicate digital adoption issues or contact center strain after catastrophe or product changes.
- **App/TA:** FNOL ingestion service via HEC
- **Data Sources:** `index=insurance` `sourcetype="fnol:event"` (fnol_id, channel, region, ingest_latency_ms, success_flag)
- **SPL:**
```spl
index=insurance sourcetype="fnol:event"
| eval ok=if(success_flag=1 OR lower(success_flag)="true",1,0)
| bin _time span=1d
| stats count as fnols, sum(ok) as ok_n, avg(ingest_latency_ms) as avg_lat by channel, region, _time
| eval success_pct=round(100*ok_n/nullif(fnols,0),2)
| where success_pct < 95 OR avg_lat > 3000
| table _time, channel, region, fnols, success_pct, avg_lat
```
- **Implementation:** Map vendor channel codes to a canonical list. Filter bot traffic if tagged. Useful for post-mortems after marketing pushes to digital FNOL.
- **Visualization:** Stacked bar (FNOL volume by channel), Line chart (success %), Heatmap (region × channel).
- **CIM Models:** N/A

---

### UC-21.10.3 · Claims Adjuster Workload Balancing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Uneven open-claim counts per adjuster drive delays and quality variance; workload panels support fair distribution and surge staffing during CAT events.
- **App/TA:** Claims assignment system via HEC
- **Data Sources:** `index=insurance` `sourcetype="adjuster:workload"` (adjuster_id, team, open_claims, new_assignments_day, capacity_target)
- **SPL:**
```spl
index=insurance sourcetype="adjuster:workload"
| eval load_ratio=if(capacity_target>0, round(open_claims/capacity_target,2), null)
| where open_claims > capacity_target*1.2 OR load_ratio > 1.3
| stats max(open_claims) as max_open, avg(load_ratio) as avg_ratio by team, adjuster_id
| sort team, - max_open
| table team, adjuster_id, max_open, avg_ratio
```
- **Implementation:** Refresh snapshot frequency aligned to work management (hourly/daily). Join `team` to supervisor roster via lookup. Use for operations review; respect labor agreements on monitoring scope.
- **Visualization:** Bar chart (open claims by adjuster), Box plot (team distribution), Single value (adjusters over capacity).
- **CIM Models:** N/A

---

### UC-21.10.4 · Subrogation Recovery Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Subrogation dollars recovered reduce net loss ratio; tracking recovery rate and aging by claim type validates vendor performance and statute-of-limitations risk.
- **App/TA:** Subrogation module via HEC
- **Data Sources:** `index=insurance` `sourcetype="subrogation:recovery"` (claim_id, demand_amt, recovered_amt, opened_epoch, closed_epoch, outcome)
- **SPL:**
```spl
index=insurance sourcetype="subrogation:recovery"
| eval recovery_pct=if(demand_amt>0, round(100*recovered_amt/demand_amt,2), null)
| eval age_days=round((now()-opened_epoch)/86400,1)
| where recovery_pct < 30 AND age_days > 180 AND lower(outcome)!="closed_no_recovery"
| table claim_id, demand_amt, recovered_amt, recovery_pct, age_days, outcome
```
- **Implementation:** Clarify accounting for partial payments in `recovered_amt`. Schedule weekly for aged inventory. Legal holds may restrict fields—mask PII per policy.
- **Visualization:** Line chart (recovery rate trend), Bar chart (aging buckets), Table (low-recovery claims).
- **CIM Models:** N/A

---

### UC-21.10.5 · Policy Underwriting Decision Audit Trail
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Immutable-style audit of quote, risk tier, and bind decisions supports regulatory exams and disputes; Splunk supplements the system of record for search and dashboards.
- **App/TA:** Policy administration / underwriting engine via HEC
- **Data Sources:** `index=insurance` `sourcetype="underwriting:audit"` (policy_id, decision_id, user_id, decision, risk_score, rule_id, epoch)
- **SPL:**
```spl
index=insurance sourcetype="underwriting:audit"
| eval bind=if(lower(decision) IN ("bind","approved","accept"),1,0)
| bin _time span=1d
| stats count as decisions, sum(bind) as binds, dc(rule_id) as rules_fired by user_id, _time
| eval bind_ratio=round(100*binds/nullif(decisions,0),2)
| where decisions > 50 AND bind_ratio > 85 AND rules_fired < 2
| table _time, user_id, decisions, binds, bind_ratio, rules_fired
```
- **Implementation:** Ingest append-only decision events with tamper-evident hashing if required by compliance. Tune alert for unusual auto-approval patterns; investigate false positives with underwriting leadership. Not a replacement for GRC workflow.
- **Visualization:** Timeline (decision volume), Table (suspicious users), Bar chart (bind ratio by rule).
- **CIM Models:** N/A

---

### UC-21.10.6 · Insurance Fraud Ring Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Fault
- **Value:** Graph-style links among claimants, body shops, and payees reveal staged-loss rings distinct from generic payment fraud in banking; supports SIU prioritization when combined with Fraud Analytics scores.
- **App/TA:** Splunk App for Fraud Analytics, graph enrichment via HEC
- **Data Sources:** `index=insurance` `sourcetype="fraud:network"` (claim_id, entity_id, entity_type, edge_type, related_claim_id)
- **SPL:**
```spl
index=insurance sourcetype="fraud:network"
| stats dc(claim_id) as claim_cnt, dc(related_claim_id) as rel_cnt, values(entity_type) as types by entity_id
| eval fanout=claim_cnt+rel_cnt
| where fanout >= 5 AND mvcount(types) >= 2
| sort - fanout
| table entity_id, fanout, claim_cnt, rel_cnt, types
```
- **Implementation:** Build nightly entity extracts from claims and vendor data; load into Splunk or external graph with summaries back. Coordinate with legal for PII handling. Pair with Behavioral Profiling App scores for triage.
- **Visualization:** Node-link diagram (external viz or custom), Table (high-fanout entities), Bar chart (claims per entity).
- **CIM Models:** N/A

---

### UC-21.10.7 · Workers Compensation Return-to-Work Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** RTW milestones reduce indemnity spend and improve outcomes; monitoring days lost and RTW status by employer class highlights case management gaps.
- **App/TA:** Workers comp claims system via HEC
- **Data Sources:** `index=insurance` `sourcetype="workcomp:rtw"` (claim_id, employer_class, injury_date_epoch, rtw_date_epoch, lost_time_flag)
- **SPL:**
```spl
index=insurance sourcetype="workcomp:rtw" lost_time_flag=1
| eval days_lost=if(isnotnull(rtw_date_epoch), (rtw_date_epoch-injury_date_epoch)/86400, (now()-injury_date_epoch)/86400)
| where days_lost > 45
| stats avg(days_lost) as avg_lost, perc90(days_lost) as p90_lost, count as claims by employer_class
| eval avg_lost_r=round(avg_lost,1), p90_lost_r=round(p90_lost,1)
| sort - avg_lost_r
| table employer_class, claims, avg_lost_r, p90_lost_r
```
- **Implementation:** De-identify claimants in dashboards. Handle jurisdictional differences in reporting latency. Integrate with nurse case management milestones if available.
- **Visualization:** Histogram (days lost), Bar chart (by employer class), Line chart (RTW trend).
- **CIM Models:** N/A

---

### UC-21.10.8 · Catastrophe Event Claims Surge Capacity Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Performance
- **Value:** During hurricanes or wildfires, FNOL and assignment rates can overwhelm contact centers and field adjusters; real-time intake vs staffed capacity guides IVR messaging and temporary adjuster pools.
- **App/TA:** Claims platform + workforce management via HEC
- **Data Sources:** `index=insurance` `sourcetype="cat:surge"` (cat_event_id, fnol_per_hr, active_adjusters, queue_depth, p95_handle_sec)
- **SPL:**
```spl
index=insurance sourcetype="cat:surge"
| bin _time span=1h
| eval capacity_est=active_adjusters*4
| eval surge_ratio=if(capacity_est>0, round(fnol_per_hr/capacity_est,2), null)
| stats max(surge_ratio) as max_surge, max(queue_depth) as max_q, max(p95_handle_sec) as max_p95 by cat_event_id, _time
| where max_surge > 1.2 OR max_q > 500 OR max_p95 > 600
| table _time, cat_event_id, max_surge, max_q, max_p95
```
- **Implementation:** Parameterize `capacity_est` from actual handles-per-hour by channel. Tag `cat_event_id` from peril models. Coordinate with BCP playbooks; thresholds are scenario-specific.
- **Visualization:** Time chart (FNOL vs capacity), Area chart (queue depth), Single value (surge ratio).
- **CIM Models:** N/A

---
