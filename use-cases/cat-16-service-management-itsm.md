## 16. Service Management & ITSM

### 16.1 Ticketing Systems

**Primary App/TA:** Splunk Add-on for ServiceNow (`Splunk_TA_snow`), Splunk Add-on for Jira, custom API inputs.

---

### UC-16.1.1 · Incident Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **Monitoring type:** Compliance
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
- **Monitoring type:** Performance
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
- **Monitoring type:** Configuration
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
- **Monitoring type:** Configuration
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
- **Monitoring type:** Capacity
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
- **Monitoring type:** Performance
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
- **Monitoring type:** Performance
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
- **Monitoring type:** Configuration
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
- **Monitoring type:** Performance
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

### UC-16.1.11 · Problem Ticket Reopening Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Tickets closed then reopened indicate poor resolution quality, incomplete fixes, or inadequate testing. Tracking reopening rate drives resolution discipline and reduces repeat work.
- **App/TA:** Custom (ITSM API — ServiceNow, Jira Service Management)
- **Data Sources:** ITSM ticket state change history
- **SPL:**
```spl
index=itsm sourcetype="snow:incident:audit" field_name="state"
| eval reopened=if(match(old_value,"closed|6") AND not(match(new_value,"closed|6")), 1, 0)
| where reopened=1
| stats count as reopened_count by number
| eval metric="reopened"
| append [| search index=itsm sourcetype="snow:incident" state="closed" earliest=-30d | stats count as total_closed | eval metric="total"]
| stats sum(reopened_count) as reopened, sum(total_closed) as total by metric
| stats sum(reopened) as reopened, sum(total_closed) as total
| eval reopen_rate=round(reopened/total*100, 1)
```
- **Implementation:** Ingest ITSM audit/history tables capturing state transitions. For ServiceNow, use `sys_audit` or `incident_state_history`; for Jira, use `changelog` or REST API history. Identify incidents with state sequence: closed → reopened (or new/in_progress). Calculate reopening rate as reopened / total closed over rolling 30 days. Alert when rate exceeds 5%. Break down by assignment group and category to target improvement. Correlate with resolution notes to identify patterns (e.g., "workaround" vs "root cause fixed").
- **Visualization:** Single value (reopen rate %), Bar chart (reopen rate by assignment group), Line chart (reopen rate trend), Table (reopened tickets with resolution notes).
- **CIM Models:** N/A

---

### UC-16.1.12 · Incident Priority Distribution Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operational
- **Value:** Are P1/P2 incidents increasing? Trend analysis for management reporting reveals workload shifts, infrastructure degradation, or seasonal patterns. Supports staffing and capacity planning.
- **App/TA:** Custom (ITSM API)
- **Data Sources:** ITSM incident records (priority, created_date)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| eval priority_label=case(priority=1,"P1", priority=2,"P2", priority=3,"P3", priority=4,"P4", priority=5,"P5", true(),"Other")
| timechart span=1d count by priority_label
| addtotals
| eval p1_p2_pct=round(('P1'+'P2')/Total*100, 1)
```
- **Implementation:** Ingest incident creation events with priority and created timestamp. Normalize priority values (ServiceNow: 1–5; Jira: Critical/High/Medium/Low). Run daily timechart by priority. Compute P1+P2 share of total for executive summary. Alert when P1/P2 percentage exceeds 7-day rolling average by >20%. Export weekly/monthly reports for management. Compare against previous quarter for trend narrative.
- **Visualization:** Stacked area chart (priority distribution over time), Line chart (P1+P2 count trend), Single value (P1/P2 % this week), Table (priority counts by week).
- **CIM Models:** N/A

---

### UC-16.1.13 · On-Call Escalation Frequency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Rising escalation rate indicates team capacity or knowledge gaps. Unacknowledged or escalated incidents signal burnout risk and process bottlenecks. Supports on-call rotation tuning and training.
- **App/TA:** Custom (PagerDuty API, Opsgenie API, ITSM)
- **Data Sources:** On-call platform API (incidents, escalations, acknowledgment times)
- **SPL:**
```spl
index=oncall sourcetype IN ("pagerduty:incidents","opsgenie:alerts")
| eval escalated=if(escalation_count>0 OR escalation_policy_used=1, 1, 0)
| eval ack_delay_mins=round((acknowledged_at-triggered_at)/60, 0)
| timechart span=1d count as total, sum(escalated) as escalated
| eval escalation_rate=round(escalated/total*100, 1)
| where total>0
```
- **Implementation:** Ingest PagerDuty or Opsgenie incidents via REST API (scheduled input or scripted input). Map fields: `escalation_count`, `escalation_policy_used`, `acknowledged_at`, `triggered_at`. Compute escalation rate (escalated / total) per day or per service. Alert when escalation rate exceeds 15% over 7 days. Track acknowledgment time (SLA); alert when avg ack time exceeds 15 minutes for P1. Report by service and escalation policy to identify overloaded rotations.
- **Visualization:** Line chart (escalation rate trend), Bar chart (escalations by service), Single value (escalation rate %), Table (slowest-acknowledged incidents).
- **CIM Models:** N/A

---

### 16.2 Configuration Management (CMDB)

**Primary App/TA:** ServiceNow CMDB integration, custom API inputs.

---

### UC-16.2.1 · CMDB Data Quality Score
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **Monitoring type:** Performance
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
- **Monitoring type:** Performance
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
- **Monitoring type:** Performance
- **Value:** Accurate CI relationships enable impact analysis during incidents. Incomplete relationships undermine service mapping.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB relationship data
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" ci_class IN ("cmdb_ci_server","cmdb_ci_app_server")
| join type=left sys_id [search index=itsm sourcetype="snow:cmdb_rel_ci" | stats count as rel_count by child | rename child as sys_id]
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
- **Monitoring type:** Compliance
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
- **Monitoring type:** Availability
- **Value:** Individual component alerts do not communicate business impact. A BPI model aggregates the health of all components that together constitute a business capability (e.g., "Order Processing = web tier + database + payment gateway + message queue"). When any essential member fails, the business process is immediately flagged as degraded or down — mirroring Nagios BPI groups with essential member logic. Operations teams see business impact, not raw host counts.
- **App/TA:** Splunk IT Service Intelligence (ITSI), or custom KV Store + scheduled searches
- **Premium Apps:** Splunk ITSI
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
- **Monitoring type:** Availability
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

### UC-16.3.3 · First Contact Resolution Rate by Group
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** FCR indicates support efficiency and customer satisfaction. Tracking by group and category supports staffing and process improvement.
- **App/TA:** ServiceNow/Service Desk TA, ITSM API
- **Data Sources:** Incident resolution, first-contact resolution flag
- **SPL:**
```spl
index=itsm sourcetype="incident"
| where is_open=0
| stats count, sum(eval(if(first_contact_resolution=1,1,0))) as fcr_count by assignment_group, category
| eval fcr_rate=round((fcr_count/count)*100, 1)
| sort -count
| table assignment_group, category, count, fcr_count, fcr_rate
```
- **Implementation:** Ingest incident closure data with FCR flag. Compute FCR rate by group and category. Report on trend and groups below target. Use for training and process review.
- **Visualization:** Bar chart (FCR rate by group), Table (group × category FCR), Line chart (FCR trend).
- **CIM Models:** N/A

---

### UC-16.3.4 · Escalation and Handoff Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long escalation or handoff times delay resolution. Monitoring handoff duration supports SLA and identifies bottlenecks.
- **App/TA:** ITSM workflow logs, incident history
- **Data Sources:** Assignment change events, timestamps per group
- **SPL:**
```spl
index=itsm sourcetype="incident:history"
| search type=assignment_change
| eval handoff_hrs=(next_assignment_time - prev_assignment_time)/3600
| stats avg(handoff_hrs) as avg_handoff, max(handoff_hrs) as max_handoff by from_group, to_group
| where avg_handoff > 2
```
- **Implementation:** Ingest assignment and state change history. Compute time between assignments. Alert when average handoff exceeds threshold. Report on escalation paths and slow handoffs.
- **Visualization:** Table (handoff latency by path), Bar chart (avg handoff by group), Sankey (escalation flow).
- **CIM Models:** N/A

---

### UC-16.3.5 · Knowledge Article Usage and Gap Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low article use or repeated incidents without matching KB may indicate content gaps. Analytics support knowledge management and deflection.
- **App/TA:** ITSM knowledge base, search logs
- **Data Sources:** Article views, incident–KB linkage, search terms
- **SPL:**
```spl
index=itsm sourcetype="kb:usage"
| stats count as views, dc(incident_id) as linked_incidents by article_id, title
| where views < 10 AND linked_incidents > 0
| sort -linked_incidents
| table article_id, title, views, linked_incidents
```
- **Implementation:** Ingest KB view and incident–article link data. Identify articles with many linked incidents but few views (potential discovery gap). Report on top articles and unused content. Suggest new articles from frequent incident categories.
- **Visualization:** Table (articles by usage), Bar chart (linked incidents vs views), Pie chart (top articles).
- **CIM Models:** N/A

---

### UC-16.3.6 · Major Incident and Post-Mortem Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracking major incidents and post-mortem completion ensures learning and accountability. Supports compliance and continuous improvement.
- **App/TA:** ITSM major incident, post-mortem records
- **Data Sources:** Major incident flag, post-mortem due and completed dates
- **SPL:**
```spl
index=itsm sourcetype="incident"
| where major_incident=1 AND is_open=0
| eval pm_due=closed_time + (7*86400)
| where now() > pm_due AND post_mortem_completed=0
| table number, short_description, closed_time, pm_due, post_mortem_completed
```
- **Implementation:** Ingest major incident and post-mortem status. Alert when post-mortem is overdue. Report on major incident count, MTTR, and post-mortem completion rate. Track root cause categories.
- **Visualization:** Table (overdue post-mortems), Single value (major incidents this month), Line chart (post-mortem completion rate).
- **CIM Models:** N/A

---

### UC-16.3.7 · Request Fulfillment and Approval Cycle Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long approval or fulfillment times delay service delivery. Monitoring cycle time supports process optimization and SLA for requests.
- **App/TA:** ITSM request, approval workflow logs
- **Data Sources:** Request submitted, approval, and fulfillment timestamps
- **SPL:**
```spl
index=itsm sourcetype="request"
| where state="fulfilled"
| eval approval_hrs=(approval_time - submitted_time)/3600
| eval fulfill_hrs=(fulfilled_time - approval_time)/3600
| stats avg(approval_hrs) as avg_approval, avg(fulfill_hrs) as avg_fulfill by catalog_item, approval_group
| table catalog_item, approval_group, avg_approval, avg_fulfill
```
- **Implementation:** Ingest request and approval lifecycle events. Compute approval and fulfillment duration. Alert when average exceeds target. Report on slow catalog items and approvers.
- **Visualization:** Table (cycle time by catalog item), Bar chart (approval vs fulfillment time), Line chart (trend).
- **CIM Models:** N/A

---

### UC-16.3.8 · Knowledge Article Usage vs. Ticket Volume
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Self-service effectiveness measurement; are KB articles deflecting tickets? Correlating article views with ticket creation reveals deflection ROI and content gaps.
- **App/TA:** Custom (ITSM API, KB platform analytics)
- **Data Sources:** KB article view counts, ticket creation rates
- **SPL:**
```spl
index=itsm (sourcetype="kb:views" OR sourcetype="snow:incident")
| bin _time span=1d
| eval kb_views=if(sourcetype="kb:views",coalesce(views,1),0)
| eval ticket_count=if(sourcetype="snow:incident",1,0)
| stats sum(kb_views) as kb_views, sum(ticket_count) as ticket_count by _time
| eval deflection_ratio=round(kb_views/ticket_count, 2)
| streamstats window=7 avg(deflection_ratio) as avg_ratio
| eval trend=if(deflection_ratio>avg_ratio,"improving","declining")
```
- **Implementation:** Ingest KB view events (ServiceNow KB, Confluence, SharePoint) and incident creation events. Normalize to daily buckets. Compute deflection ratio (views / tickets) — higher ratio suggests effective self-service. Track 7-day rolling average; alert when ratio drops >20% vs prior week. Segment by category: compare KB views for "password reset" vs ticket volume for same category. Identify high-ticket categories with low KB coverage for content creation prioritization.
- **Visualization:** Line chart (KB views vs ticket volume over time), Single value (deflection ratio), Bar chart (ratio by category), Table (top-deflecting articles).
- **CIM Models:** N/A

---

### UC-16.3.9 · Mean Time Between Failures (MTBF) per CI
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Operational, Capacity
- **Value:** Reliability trending per configuration item for replacement planning. CIs with declining MTBF indicate aging hardware or recurring issues; supports proactive replacement and warranty decisions.
- **App/TA:** Custom (ITSM API, CMDB)
- **Data Sources:** Incident records linked to CIs, CI lifecycle data
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="closed" cmdb_ci=*
| eval resolved_epoch=resolved_at
| sort cmdb_ci resolved_epoch
| streamstats current=f last(resolved_epoch) as prev_resolved by cmdb_ci
| eval mtbf_hours=round((resolved_epoch-prev_resolved)/3600, 1)
| where isnotnull(prev_resolved) AND mtbf_hours>0
| stats avg(mtbf_hours) as avg_mtbf_hours, count as incident_count, min(_time) as first_incident, max(_time) as last_incident by cmdb_ci
| lookup cmdb_ci_details name AS cmdb_ci OUTPUT ci_class, install_date, warranty_expires
| eval avg_mtbf_days=round(avg_mtbf_hours/24, 1)
| sort avg_mtbf_hours
| head 50
```
- **Implementation:** Ingest incidents with `cmdb_ci` (or equivalent CI linkage). Ensure resolved timestamps are indexed. For each CI, compute time between consecutive incident resolutions (MTBF). Exclude same-incident reopen/resolve cycles. Join CMDB for CI metadata (class, age, warranty). Alert when MTBF for critical CIs drops below 30-day baseline by >30%. Report top 50 lowest-MTBF CIs for replacement planning. Segment by CI class (server, network device, storage) for fleet-level reliability comparison.
- **Visualization:** Table (CI, MTBF days, incident count, warranty), Bar chart (MTBF by CI class), Line chart (MTBF trend per CI), Heatmap (CI × time, color = MTBF).
- **CIM Models:** N/A

---
