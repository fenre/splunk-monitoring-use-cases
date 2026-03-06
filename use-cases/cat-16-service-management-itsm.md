## 16. Service Management & ITSM

### 16.1 Ticketing Systems

**Primary App/TA:** Splunk Add-on for ServiceNow (`Splunk_TA_snow`), Splunk Add-on for Jira, custom API inputs.

---

### UC-16.1.1 · Incident Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Incident trends reveal infrastructure stability, staffing needs, and the effectiveness of problem management.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow incident table
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| timechart span=1d count by priority
```
- **Implementation:** Ingest ServiceNow incidents via TA. Track creation rates by category, priority, and assignment group. Alert on volume spikes. Compare against historical baselines. Report on trending categories for problem management input.
- **Visualization:** Line chart (incident volume trend), Stacked bar (by priority), Pie chart (by category), Table (today's incidents).
- **CIM Models:** N/A

---

### UC-16.1.2 · SLA Compliance Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** SLA breaches affect customer satisfaction and contractual obligations. Real-time monitoring enables intervention before breaches occur.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow SLA records (response, resolution)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| eval response_met=if(response_time<=response_sla,"Yes","No")
| eval resolution_met=if(resolution_time<=resolution_sla,"Yes","No")
| stats count(eval(response_met="Yes")) as met, count as total by priority
| eval compliance_pct=round(met/total*100,1)
```
- **Implementation:** Track response and resolution times against SLA targets per priority. Alert when tickets approach SLA breach. Report on compliance percentage per priority and assignment group. Identify teams with consistent breaches.
- **Visualization:** Gauge (SLA compliance %), Bar chart (compliance by priority), Table (tickets approaching breach), Line chart (compliance trend).
- **CIM Models:** N/A

---

### UC-16.1.3 · MTTR by Category
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** MTTR per category identifies where process improvements or automation would have the greatest impact.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident lifecycle data (open, assigned, resolved timestamps)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="resolved"
| eval mttr_hours=round((resolved_at-opened_at)/3600,1)
| stats avg(mttr_hours) as avg_mttr, median(mttr_hours) as median_mttr by category
| sort -avg_mttr
```
- **Implementation:** Calculate MTTR from incident open to resolution timestamps. Break down by category, subcategory, and assignment group. Track trends over time. Set MTTR targets per category and report on achievement.
- **Visualization:** Bar chart (MTTR by category), Line chart (MTTR trend), Table (category MTTR summary), Histogram (resolution time distribution).
- **CIM Models:** N/A

---

### UC-16.1.4 · Change Success Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Failed changes are the leading cause of incidents. Tracking success rate drives improvement in change management practices.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow change records
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request"
| stats count(eval(close_code="successful")) as success, count(eval(close_code="failed")) as failed, count as total by type
| eval success_rate=round(success/total*100,1)
```
- **Implementation:** Ingest change request records. Track outcomes (successful, failed, backed out). Calculate success rate by change type (standard, normal, emergency). Alert on failed changes. Report on DORA change failure rate metric.
- **Visualization:** Pie chart (change outcomes), Bar chart (success rate by type), Line chart (success rate trend), Single value (overall success rate).
- **CIM Models:** N/A

---

### UC-16.1.5 · Change Collision Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Overlapping changes on related systems increase outage risk. Detection enables coordination and conflict resolution.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Change calendar, CI relationships
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state="scheduled"
| eval change_window_start=start_date, change_window_end=end_date
| join type=inner cmdb_ci [| search index=itsm sourcetype="snow:change_request" state="scheduled"]
| where change_window_start < end_date AND change_window_end > start_date AND change_id!=other_change_id
```
- **Implementation:** Analyze scheduled change windows for overlapping CIs. Cross-reference CI relationships for dependent systems. Alert when changes to related systems overlap. Create change calendar view for CAB review.
- **Visualization:** Calendar view (change windows), Table (colliding changes), Gantt chart (change timeline).
- **CIM Models:** N/A

---

### UC-16.1.6 · Problem Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Identifying recurring incident patterns that should become problems drives root cause resolution and reduces incident volume.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident categorization data, problem records
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| stats count by category, subcategory, cmdb_ci
| where count > 5
| sort -count
| head 20
```
- **Implementation:** Analyze incident patterns by category, CI, and assignment group. Identify recurring incidents (>5 in 30 days). Flag candidates for problem record creation. Track problem management effectiveness (repeat incidents after RCA).
- **Visualization:** Table (top recurring incidents), Bar chart (repeat incidents by category), Line chart (repeat rate trend).
- **CIM Models:** N/A

---

### UC-16.1.7 · Ticket Reassignment Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** High reassignment rates indicate poor routing or skills gaps. Reduction improves MTTR and customer satisfaction.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident audit trail (assignment changes)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| stats dc(assignment_group) as group_count, count as reassignments by number
| where group_count > 2
| sort -group_count
```
- **Implementation:** Track assignment group changes per ticket. Calculate average reassignments. Identify tickets with >2 reassignments (ping-pong tickets). Report on routing accuracy by category. Improve auto-routing rules.
- **Visualization:** Bar chart (avg reassignments by category), Table (most-reassigned tickets), Line chart (reassignment rate trend), Single value (avg reassignments).
- **CIM Models:** N/A

---

### UC-16.1.8 · Aging Ticket Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Aging tickets indicate stuck processes or forgotten issues. Alerts ensure nothing falls through the cracks.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Open incident data
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state IN ("new","in_progress","on_hold")
| eval age_days=round((now()-opened_at)/86400)
| eval age_threshold=case(priority=1,1, priority=2,3, priority=3,7, 1=1,14)
| where age_days > age_threshold
| table number, short_description, priority, assignment_group, age_days
| sort -age_days
```
- **Implementation:** Calculate ticket age against priority-based thresholds. Alert when tickets exceed expected resolution time. Escalate automatically via workflow rules. Report on aging ticket inventory daily.
- **Visualization:** Table (aging tickets), Bar chart (aging by priority), Single value (total aging tickets), Line chart (aging trend).
- **CIM Models:** N/A

---

### UC-16.1.9 · Change-Incident Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Correlating incidents with recent changes is the fastest path to root cause. Automated correlation accelerates MTTR.
- **App/TA:** `Splunk_TA_snow` + monitoring data
- **Data Sources:** Change records + incident records + monitoring events
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" priority IN (1,2)
| join type=left cmdb_ci
    [search index=itsm sourcetype="snow:change_request" close_code="successful" earliest=-24h
     | table cmdb_ci, number as change_number, short_description as change_desc, end_date]
| where isnotnull(change_number)
| table number, short_description, cmdb_ci, change_number, change_desc
```
- **Implementation:** When high-priority incidents are created, automatically search for changes completed in the last 24 hours on related CIs. Present correlation to incident team. Track change-related incident percentage. Feed back to change management.
- **Visualization:** Table (incident-change correlation), Single value (% incidents with recent change), Timeline (changes + incidents overlaid).
- **CIM Models:** N/A

---

### UC-16.1.10 · Service Request Fulfillment Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Fulfillment time metrics drive service catalog optimization and customer satisfaction. Slow fulfillment reduces adoption.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Service request data
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_request"
| eval fulfillment_hours=round((closed_at-opened_at)/3600,1)
| stats avg(fulfillment_hours) as avg_hours, median(fulfillment_hours) as median_hours by cat_item
| sort -avg_hours
```
- **Implementation:** Track service request lifecycle from submission to fulfillment. Calculate fulfillment time per catalog item. Identify items with slow fulfillment for automation opportunities. Report on catalog efficiency.
- **Visualization:** Bar chart (avg fulfillment by item), Table (catalog item performance), Line chart (fulfillment time trend).
- **CIM Models:** N/A

---

### 16.2 Configuration Management (CMDB)

**Primary App/TA:** ServiceNow CMDB integration, custom API inputs.

---

### UC-16.2.1 · CMDB Data Quality Score
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Poor CMDB data quality undermines all ITSM processes. Scoring and trending drives data quality improvement initiatives.
- **App/TA:** `Splunk_TA_snow`, custom metrics
- **Data Sources:** CMDB CI data (completeness, accuracy, freshness)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci"
| eval complete=if(isnotnull(owner) AND isnotnull(support_group) AND isnotnull(environment),1,0)
| eval fresh=if(last_discovered > relative_time(now(),"-30d"),1,0)
| stats avg(complete) as completeness, avg(fresh) as freshness
| eval quality_score=round((completeness*50+freshness*50),1)
```
- **Implementation:** Define CMDB quality dimensions (completeness, accuracy, freshness, relationships). Score each dimension. Calculate composite quality score. Track trend over time. Set improvement targets. Report to CMDB governance board.
- **Visualization:** Gauge (quality score), Line chart (quality trend), Bar chart (quality by dimension), Table (worst-scoring CIs).
- **CIM Models:** N/A

---

### UC-16.2.2 · CI Discovery Reconciliation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CIs in the network but not in the CMDB are unmanaged risks. Reconciliation ensures CMDB completeness.
- **App/TA:** Discovery tools + CMDB
- **Data Sources:** Discovery scan results, CMDB CI records
- **SPL:**
```spl
| inputlookup discovered_assets.csv
| join type=left hostname [search index=itsm sourcetype="snow:cmdb_ci" | table hostname, sys_id, ci_class]
| where isnull(sys_id)
| table hostname, ip_address, os, discovered_date
```
- **Implementation:** Compare auto-discovered assets (ServiceNow Discovery, SCCM, network scans) with CMDB records. Identify CIs found by discovery but absent from CMDB. Create workflow to review and add missing CIs. Track gap closure over time.
- **Visualization:** Table (unmatched discovered assets), Single value (CMDB gap count), Pie chart (matched vs unmatched), Line chart (gap trend).
- **CIM Models:** N/A

---

### UC-16.2.3 · Orphaned CI Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** CIs without owners or service mappings aren't managed during incidents, creating accountability gaps and shadow infrastructure.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB CI attributes
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" operational_status="operational"
| where isnull(assigned_to) OR isnull(support_group) OR isnull(u_service)
| table name, ci_class, assigned_to, support_group, u_service
```
- **Implementation:** Query CMDB for operational CIs missing key attributes (owner, support group, service mapping). Report on orphaned CI inventory. Assign ownership through automated or manual workflow. Track orphan reduction over time.
- **Visualization:** Table (orphaned CIs), Pie chart (by CI class), Bar chart (orphans by missing attribute), Single value (total orphaned CIs).
- **CIM Models:** N/A

---

### UC-16.2.4 · Relationship Integrity Check
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Accurate CI relationships enable impact analysis during incidents. Incomplete relationships undermine service mapping.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB relationship data
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" ci_class IN ("cmdb_ci_server","cmdb_ci_app_server")
| join type=left sys_id [search index=itsm sourcetype="snow:cmdb_rel_ci" | stats count as rel_count by child]
| where isnull(rel_count) OR rel_count=0
| table name, ci_class, rel_count
```
- **Implementation:** Validate CI relationships are present and bidirectional. Identify servers with no application relationships, applications with no infrastructure dependencies. Report on relationship completeness. Use for impact analysis validation.
- **Visualization:** Table (CIs without relationships), Network graph (CI dependency map), Single value (% CIs with relationships).
- **CIM Models:** N/A

---

### UC-16.2.5 · CMDB Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking all CI attribute changes supports compliance auditing and helps detect unauthorized configuration changes.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB audit trail (sys_audit)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_audit"
| table _time, ci_name, field_name, old_value, new_value, changed_by
| sort -_time
```
- **Implementation:** Ingest CMDB audit records. Track all CI attribute changes. Alert on changes to critical CIs outside change windows. Report on change volume by CI class and source (manual vs discovery). Validate accuracy of discovery updates.
- **Visualization:** Table (CI changes), Timeline (change events), Bar chart (changes by CI class), Line chart (change volume trend).
- **CIM Models:** N/A

---


### 16.3 Business Process & Availability Intelligence

Covers Nagios Business Process Intelligence (BPI)-style monitoring: aggregating component health into logical service status, and cross-infrastructure availability heatmaps.

---

### UC-16.3.1 · Cross-Service Business Process Health Score
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Individual component alerts do not communicate business impact. A BPI model aggregates the health of all components that together constitute a business capability (e.g., "Order Processing = web tier + database + payment gateway + message queue"). When any essential member fails, the business process is immediately flagged as degraded or down — mirroring Nagios BPI groups with essential member logic. Operations teams see business impact, not raw host counts.
- **App/TA:** Splunk IT Service Intelligence (ITSI), or custom KV Store + scheduled searches
- **Data Sources:** All existing monitoring indexes (`index=os`, `index=network`, `index=app`, `index=db`), ITSI entity/service model
- **SPL:**
```spl
index=monitoring sourcetype IN (server_health, app_health, db_health, network_health)
| eval component_status=case(
    status="critical", 0,
    status="high",     1,
    status="medium",   2,
    status="ok",       3,
    true(),            3)
| lookup business_process_components.csv component_name AS service OUTPUT process_name, is_essential
| stats min(component_status) as essential_min
       avg(component_status) as avg_status
  by process_name, _time
| eval bpi_score=round((avg_status / 3) * 100, 1)
| eval bpi_state=case(
    essential_min=0, "DOWN",
    bpi_score < 50,  "DEGRADED",
    bpi_score < 80,  "AT RISK",
    true(),          "HEALTHY")
| table _time, process_name, bpi_score, bpi_state, essential_min
```
- **Implementation:** Build a lookup (`business_process_components.csv`) mapping infrastructure components to business processes, with an `is_essential` flag (essential = single point of failure). Run as a scheduled search every 5 minutes. Feed results into a KV Store for dashboard consumption. For full capability, use ITSI Service Analyzer with KPI threshold-based health scores — ITSI natively implements BPI-equivalent logic with adaptive thresholding and episode-based alerting. Alert when `bpi_state=DOWN` (essential member failed) or `bpi_score` drops below 60 for >10 minutes.
- **Visualization:** Service Analyzer glass table (ITSI), Radial gauge (health score per process), Sankey diagram (component → process → business unit), Single value tiles (one per business process with color coding).

---

### UC-16.3.2 · Infrastructure Service Availability Heatmap
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Provides a Nagios-style tactical overview — at a glance, which hosts and services have been available vs down, when, and for how long. Operations teams use this for SLA evidence, post-incident review, and capacity risk communication. Unlike individual alerts, the heatmap reveals systemic patterns: recurring daily outage windows, hosts with chronic flapping, services that always fail together.
- **App/TA:** `Splunk_TA_nix`, `Splunk_TA_windows`, all existing monitoring TAs
- **Data Sources:** Consolidated availability events from all infrastructure monitoring indexes
- **SPL:**
```spl
index=monitoring sourcetype IN (server_health, service_check, network_health)
| bin _time span=1h
| eval hour=strftime(_time, "%Y-%m-%d %H:00")
| eval avail=if(status="ok" OR status="up", 1, 0)
| stats avg(avail) as availability_ratio by host, service, hour
| eval avail_pct=round(availability_ratio * 100, 1)
| eval color=case(
    avail_pct=100,    "green",
    avail_pct >= 99,  "lightgreen",
    avail_pct >= 95,  "yellow",
    avail_pct >= 90,  "orange",
    true(),           "red")
| table host, service, hour, avail_pct, color
```
- **Implementation:** Normalize availability data from all sources (server, network, app) into a shared `index=monitoring` with a standardized `status` field. Schedule this search hourly. Store results in a summary index or KV Store for long-term retention. Build a Dashboard Studio heatmap visualization with host on the Y-axis and time on the X-axis, color-coded by availability percentage. Implement drilldown to raw events for any red cell. Export monthly availability reports per host/service for SLA documentation. Filter by host group (infrastructure, application, network) using tokens.
- **Visualization:** Heatmap (host × time, color = availability%), Table (hosts sorted by lowest monthly availability), Single value (fleet-wide availability %), Line chart (fleet availability trend), Bar chart (downtime hours by host).

---
