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
- **Implementation:** Enable the incident input in `Splunk_TA_snow` with a 300-second polling interval. Baseline incident volume by computing the median count per `assignment_group` by hour-of-week over 30 days. Alert when the current interval exceeds 2x the baseline for two consecutive intervals. Exclude known maintenance windows via a `change_windows` lookup.
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
| join type=inner max=1 cmdb_ci [| search index=itsm sourcetype="snow:change_request" state="scheduled"]
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
| join type=left max=1 cmdb_ci
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

### UC-16.1.14 · SLA Breach Prediction
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Predicting tickets likely to breach SLA before the deadline enables proactive reassignment, escalation, and automation — reducing contractual exposure and customer impact.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow incident + SLA task / task_sla (`sourcetype=snow:task_sla` or equivalent)
- **SPL:**
```spl
index=itsm sourcetype="snow:task_sla"
| where isnull(breach_time) OR breach_time=0
| eval pct_elapsed=if(isnotnull(planned_end_time) AND planned_end_time>sla_start_time,
    100*(now()-sla_start_time)/(planned_end_time-sla_start_time), null())
| where pct_elapsed>=80 AND pct_elapsed<100 AND isnotnull(pct_elapsed)
| table _time, parent, number, sla_type, pct_elapsed, planned_end_time
| sort -pct_elapsed
```
- **Implementation:** Ingest SLA task rows with `sla_start_time`, `planned_end_time` (or `due_at`), breach flag, and parent incident. Compute percent of SLA window consumed. Alert when elapsed ≥80% and breach has not occurred. Optionally blend with assignment group queue depth. Tune thresholds per priority and SLA definition.
- **Visualization:** Table (at-risk tickets), Single value (at-risk count), Gauge (% SLA time consumed), Timeline (SLA burn-down).
- **CIM Models:** N/A

---

### UC-16.1.15 · Incident Reassignment Frequency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operational
- **Value:** Trending reassignment frequency (per period and per group) exposes routing quality, skills gaps, and noisy categories — complementing per-ticket reassignment counts.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident audit / history (`sourcetype=snow:incident:audit` or `sys_audit` mapped)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident:audit" field_name="assignment_group"
| timechart span=1d count as reassign_events
| appendcols [ search index=itsm sourcetype="snow:incident:audit" field_name="assignment_group" earliest=-30d@d
  | stats count as events_30d ]
| eval daily_avg=round(events_30d/30,1)
| where reassign_events > daily_avg*1.5
```
- **Implementation:** Ingest audit rows where `assignment_group` changes; each row is one reassignment event. Timechart daily volume; compare to 30-day average to detect spikes. Break down by `category` and `assignment_group` with `stats count by _time, category` in a separate panel.
- **Visualization:** Line chart (reassignment events per day), Bar chart (events by category), Single value (30-day total).
- **CIM Models:** N/A

---

### UC-16.1.16 · Ticket Aging by Priority
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Distribution of open ticket age by priority highlights backlog imbalance (e.g., many old P3s) and supports capacity and escalation decisions.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Open incidents (`sourcetype=snow:incident`)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state IN ("new","in_progress","on_hold")
| eval age_days=round((now()-opened_at)/86400,1)
| eval bucket=case(age_days<=1,"0-1d", age_days<=7,"2-7d", age_days<=30,"8-30d", true(),"30d+")
| eval pri=case(priority=1,"P1", priority=2,"P2", priority=3,"P3", priority=4,"P4", true(),"Other")
| stats count by pri, bucket
| sort pri, bucket
```
- **Implementation:** Normalize priority labels. Bucket age for open tickets only. Report stacked bar or pivot table (priority × age bucket). Alert when count in `30d+` for P1/P2 exceeds policy.
- **Visualization:** Stacked bar (age buckets by priority), Heatmap (priority × bucket), Table (raw counts).
- **CIM Models:** N/A

---

### UC-16.1.17 · Auto-Close Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracks incidents resolved by auto-close rules vs manual closure; excess auto-close may indicate poor engagement or policy gaming; too few may mean workflows are not firing.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incidents with resolution code / close notes / `closed_by` / `close_code`
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="closed" earliest=-30d
| eval auto_closed=if(match(lower(close_notes),"auto[- ]?close") OR match(lower(resolution_code),"auto") OR lower(closed_by)="system",1,0)
| stats count as total, sum(auto_closed) as auto_closed by category
| eval auto_close_pct=round(100*auto_closed/total,1)
| sort -auto_close_pct
```
- **Implementation:** Map your ServiceNow fields: auto-close may appear as `resolution_code`, workflow user, or `sys_mod_count` patterns. Adjust `auto_closed` logic to match internal policy. Report fleet auto-close % and by category; investigate outliers.
- **Visualization:** Single value (auto-close %), Bar chart (auto-close % by category), Table (top auto-closed categories).
- **CIM Models:** N/A

---

### UC-16.1.18 · Recurring Incident Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Clusters of similar incidents within a short window signal candidates for problem records, known-error articles, or permanent fixes.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incidents (`sourcetype=snow:incident`)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" earliest=-30d
| eval key=coalesce(cmdb_ci, category."|".subcategory)
| bin _time span=24h
| stats count by _time, key, short_description
| where count >= 3
| sort -count
```
- **Implementation:** Group by CI and/or category hash; use `cluster` or `anomalydetection` for text similarity if needed. Alert when ≥N incidents per day on same key. Feed to problem management queue.
- **Visualization:** Table (recurring clusters), Bar chart (count by key), Timeline (spikes).
- **CIM Models:** N/A

---

### UC-16.1.19 · Problem Management Root Cause Linking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures resolved incidents are tied to problem records with root cause when repeat patterns exist — closing the loop for ITIL problem management.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:incident`, `sourcetype=snow:problem`
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="closed" earliest=-90d
| eval has_pr=if(isnotnull(problem_id) AND problem_id!="","1","0")
| stats count as closed_inc, sum(eval(if(has_pr="1",1,0))) as with_pr by category
| eval link_pct=round(100*with_pr/closed_inc,1)
| where closed_inc>20 AND link_pct < 30
| sort link_pct
```
- **Implementation:** Map `problem_id` or `caused_by` from incident to problem. Report link rate by category and assignment group. Alert when categories with high volume have low problem linkage. Exclude categories excluded by policy.
- **Visualization:** Bar chart (problem link % by category), Table (gaps), Single value (overall link %).
- **CIM Models:** N/A

---

### UC-16.1.20 · Major Incident Post-Mortem Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Verifies that major incidents have completed post-mortems within policy — extending generic PIR tracking with explicit compliance scoring for Sev1 programs.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incidents with `major_incident` or `u_major_incident`, post-mortem fields
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" u_major_incident=true state="closed" earliest=-90d
| eval pm_due=resolved_at + (7*86400)
| eval compliant=if(post_mortem_completed=true OR now() <= pm_due OR isnotnull(u_post_mortem_date),1,0)
| where post_mortem_completed=false AND now() > pm_due
| table number, short_description, resolved_at, pm_due, assignment_group
| sort resolved_at
```
- **Implementation:** Align field names with your form (`u_post_mortem_complete`, tasks, etc.). Use related task table if post-mortem is a child task. Weekly report of breaches; executive summary of compliance %.
- **Visualization:** Table (non-compliant MIs), Single value (compliance %), Line chart (compliance trend).
- **CIM Models:** N/A

---

### UC-16.1.21 · War Room Activation Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Tracks when bridge/war-room workflows activate (chat, conference bridges, tags) for major incidents — supporting governance and after-action metrics.
- **App/TA:** Custom (ServiceNow tags/tasks, Slack/Teams webhooks, Zoom API)
- **Data Sources:** Incident updates with war-room flag, collaboration events (`sourcetype=snow:incident:activity` or chat)
- **SPL:**
```spl
index=itsm (sourcetype="snow:incident:activity" OR sourcetype="chat:war_room")
| search war_room=true OR match(raw,"(?i)bridge|war room|command center")
| stats earliest(_time) as first_bridge by incident_number
| join max=1 incident_number [ search index=itsm sourcetype="snow:incident" u_major_incident=true | rename number as incident_number ]
| eval bridge_delay_mins=round((first_bridge-opened_at)/60,0)
| table incident_number, opened_at, first_bridge, bridge_delay_mins
```
- **Implementation:** Normalize on `incident_number`. Ingest chat or activity logs where bridges are declared. Measure delay from incident open to first war-room event. Report monthly activations and average delay.
- **Visualization:** Table (MI + bridge times), Line chart (activations per month), Histogram (bridge delay).
- **CIM Models:** N/A

---

### UC-16.1.22 · Escalation Path Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Audits whether incidents followed the documented escalation chain (L1→L2→vendor) for compliance and training.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident history / audit (`sourcetype=snow:incident:audit`)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident:audit" field_name="assignment_group"
| eval from_group=old_value, to_group=new_value
| eval step=from_group."->".to_group
| stats values(step) as escalation_path, count as hops by number
| join max=1 number [ search index=itsm sourcetype="snow:incident" priority IN (1,2) earliest=-90d | fields number, priority ]
| where hops>4
| table number, priority, escalation_path, hops
```
- **Implementation:** Build assignment hop strings from audit `old_value`/`new_value`. Flag incidents with excessive hops for P1/P2 (policy threshold). Optionally `lookup escalation_policy.csv` with first/last hop pairs for stricter audits. Adjust field names to match `sys_audit` extractions.
- **Visualization:** Table (unexpected paths), Sankey (escalation flow), Single value (audit exceptions).
- **CIM Models:** N/A

---

### UC-16.1.23 · Service Request Fulfillment Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Percentage of catalog requests fulfilled successfully within the reporting period — distinct from average fulfillment time (UC-16.1.10).
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:sc_request` or `snow:request`
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_request" earliest=-30d
| eval fulfilled=if(lower(state) IN ("closed","complete","fulfilled") AND lower(close_code)!="cancel",1,0)
| stats count as total, sum(fulfilled) as fulfilled by cat_item
| eval fulfill_rate=round(100*fulfilled/total,1)
| where total>=5
| sort fulfill_rate
| head 20
```
- **Implementation:** Map request `state` and `close_code` for cancelled vs fulfilled. Exclude duplicates. Report overall rate and bottom 20 catalog items by fulfill rate for remediation.
- **Visualization:** Bar chart (fulfill rate by catalog item), Single value (overall fulfill %), Table (bottom performers).
- **CIM Models:** N/A

---


### UC-16.1.24 · ServiceNow Bidirectional Incident Sync
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Bidirectional sync between ITSI episodes and ServiceNow incidents eliminates manual ticket creation and ensures incident status is consistent across platforms.
- **App/TA:** Splunk ITSI, Splunk Add-on for ServiceNow
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_grouped_alerts`, ServiceNow incident table
- **SPL:**
```spl
index=itsi_grouped_alerts status!=5
| eval has_snow_ticket=if(isnotnull(snow_incident_number), "synced", "unsynced")
| stats count by has_snow_ticket severity
| sort severity
```
- **Implementation:** Configure ServiceNow integration in ITSI: map episode severity to ServiceNow priority, define assignment groups, and enable bidirectional status updates. Episodes auto-create incidents; ServiceNow resolution closes episodes. Monitor sync latency and failure rate. Requires Splunk Add-on for ServiceNow 5.5+.
- **Visualization:** Table (sync status by severity), Single value (unsynced episode count), Time chart (sync latency).
- **CIM Models:** Change

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
| join type=left max=1 hostname [search index=itsm sourcetype="snow:cmdb_ci" | table hostname, sys_id, ci_class]
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
| join type=left max=1 sys_id [search index=itsm sourcetype="snow:cmdb_rel_ci" | stats count as rel_count by child | rename child as sys_id]
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

### UC-16.2.6 · CI Relationship Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Detects when CI relationships change unexpectedly versus a baseline — supporting impact analysis integrity and unauthorized dependency changes.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:cmdb_rel_ci` or relationship table snapshots
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_rel_ci" earliest=-7d@d
| bucket _time span=1d
| stats values(_time) as days by parent, child, relationship_type
| eval change_days=mvcount(days)
| where change_days>1
| table parent, child, relationship_type, change_days
```
- **Implementation:** Schedule a nightly `outputlookup cmdb_rel_baseline.csv` from `cmdb_rel_ci` and compare with `| diff` or `join` on parent+child+type for strict drift. The SPL above flags relationships with activity on multiple days in a week (churn). Alert on new parent/child pairs against a saved baseline lookup when available.
- **Visualization:** Table (drifted relationships), Single value (drift count), Timeline (relationship changes).
- **CIM Models:** N/A

---

### UC-16.2.7 · Asset Discovery Reconciliation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Reconciles discovery source of truth against CMDB for asset inventory — variance by source, age, and confidence.
- **App/TA:** ServiceNow Discovery, SCCM, or network scan feeds
- **Data Sources:** `sourcetype=snow:discovery_model` or custom `discovery:asset`, `sourcetype=snow:cmdb_ci`
- **SPL:**
```spl
index=discovery sourcetype="discovery:asset" earliest=-1d
| eval host_key=lower(mvindex(split(hostname,"."),0))
| stats latest(_time) as last_seen by host_key, serial_number
| join type=left max=1 host_key [ search index=itsm sourcetype="snow:cmdb_ci" | eval host_key=lower(mvindex(split(name,"."),0)) | table host_key, sys_id, last_discovered ]
| eval match_state=if(isnotnull(sys_id) AND abs(last_seen-last_discovered)<86400,"synced","stale_or_missing")
| stats count by match_state
```
- **Implementation:** Normalize hostnames (FQDN strip). Map discovery tool serial/IP to CMDB. Report `stale_or_missing` counts weekly. Drive CMDB update tasks for unmatched discovery rows.
- **Visualization:** Pie chart (synced vs stale), Table (unmatched assets), Single value (reconciliation gap %).
- **CIM Models:** N/A

---

### UC-16.2.8 · End-of-Life Hardware Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Surfaces CIs past vendor EOS/EOL dates for refresh planning and security risk reduction.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:cmdb_ci` (model, OS end dates, custom EOL fields)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" ci_class IN ("cmdb_ci_server","cmdb_ci_netgear")
| eval eol_epoch=strptime(u_eol_date,"%Y-%m-%d")
| where isnotnull(eol_epoch) AND eol_epoch < relative_time(now(),"+90d@d")
| eval days_to_eol=round((eol_epoch-now())/86400,0)
| table name, model_id, u_eol_date, days_to_eol, support_group
| sort days_to_eol
```
- **Implementation:** Populate `u_eol_date` from vendor feeds or CMDB enrichment. Alert at 90/30 days. Join model catalog for batch reporting by data center.
- **Visualization:** Table (upcoming EOL), Bar chart (EOL by quarter), Single value (CIs past EOL).
- **CIM Models:** N/A

---

### UC-16.2.9 · CMDB Accuracy Scoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Scores accuracy by sampling validation (discovery match, pingable, owner confirmed) — complements completeness-focused quality scores.
- **App/TA:** `Splunk_TA_snow` + discovery/network
- **Data Sources:** `snow:cmdb_ci`, validation job results (`cmdb:validation`)
- **SPL:**
```spl
index=cmdb sourcetype="cmdb:validation" earliest=-7d
| eval ok=if(match(lower(to_string(check_passed)),"(?i)true|1|pass|ok"),1,0)
| stats avg(ok) as accuracy_ratio by ci_class
| eval accuracy_pct=round(accuracy_ratio*100,1)
| sort accuracy_pct
```
- **Implementation:** Ingest periodic validation (e.g., “IP matches DNS,” “server responds to agent,” “owner replied”). Aggregate pass rate per class and region. Trend monthly for governance scorecards.
- **Visualization:** Bar chart (accuracy % by class), Gauge (fleet accuracy), Line chart (trend).
- **CIM Models:** N/A

---

### UC-16.2.10 · Undocumented Server Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Finds servers visible to monitoring or AD but missing from CMDB — classic gap for incident routing and security scope.
- **App/TA:** Splunk Universal Forwarder inventory, AD, vCenter
- **Data Sources:** `sourcetype=inventory` or `vmware:inv:vm`, `sourcetype=snow:cmdb_ci`
- **SPL:**
```spl
index=inventory sourcetype="vmware:inv:vm" earliest=-4h
| eval host_key=lower(mvindex(split(name,"."),0))
| stats latest(_time) as seen by host_key
| join type=left max=1 host_key [ search index=itsm sourcetype="snow:cmdb_ci" ci_class="cmdb_ci_server" | eval host_key=lower(mvindex(split(name,"."),0)) | table host_key, sys_id ]
| where isnull(sys_id)
| table host_key, seen
```
- **Implementation:** Compare monitored/VM inventory hostnames (lowercased, short name) to CMDB server CIs. Tune for naming conventions (strip domain). Feed gaps to CMDB onboarding queue.
- **Visualization:** Table (undocumented hosts), Single value (gap count), Line chart (gap trend).
- **CIM Models:** N/A

---

### UC-16.2.12 · Software Asset Management Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Measures install counts vs license entitlements for major publishers — SAM compliance for audits.
- **App/TA:** SCCM, Flexera, ServiceNow SAM
- **Data Sources:** `sourcetype=sam:install`, `sourcetype=snow:alm_license`
- **SPL:**
```spl
index=sam sourcetype="sam:install" product_name="Microsoft*Visio*"
| stats dc(host) as deployed by product_name
| join max=1 product_name [ search index=itsm sourcetype="snow:alm_license" | stats sum(entitlement) as entitled by product_name ]
| eval compliance_pct=if(entitled>0, round(min(deployed,entitled)/entitled*100, 1), null())
| eval over_deployed=if(deployed>entitled, deployed-entitled, 0)
| table product_name, deployed, entitled, compliance_pct, over_deployed
```
- **Implementation:** Normalize product SKUs. Join installs to entitlement table. Alert when `over_deployed>0` or compliance below policy. Refresh entitlements monthly.
- **Visualization:** Table (SKU compliance), Single value (non-compliant SKUs), Bar chart (overage).
- **CIM Models:** N/A

---

### UC-16.2.13 · Hardware Warranty Expiry
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operational
- **Value:** Tracks warranty end dates for hardware CIs to avoid unsupported break-fix gaps and budget surprises.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:cmdb_ci` (`warranty_expires`, `u_warranty_end`)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" operational_status="operational"
| eval w_end=strptime(warranty_expires,"%Y-%m-%d")
| where isnotnull(w_end) AND w_end < relative_time(now(),"+60d@d") AND w_end > now()
| eval days_left=round((w_end-now())/86400,0)
| table name, serial_number, warranty_expires, days_left, support_group
| sort days_left
```
- **Implementation:** Map OEM warranty fields from procurement or discovery. Alert at 60/30 days. Exclude disposed assets via `install_status`.
- **Visualization:** Table (warranty expiring), Timeline (expiry by month), Single value (CIs <30d).
- **CIM Models:** N/A

---

### UC-16.2.14 · CI Lifecycle Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Monitors CI lifecycle state transitions (ordered → received → in production → retired) for stuck states and policy compliance.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:cmdb_ci` (`install_status`, `operational_status`)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci"
| where match(lower(install_status),"on order|pending install|received")
| eval created_epoch=coalesce(sys_created_on, sys_updated_on, _time)
| eval age_days=round((now()-created_epoch)/86400,0)
| where age_days>90
| table name, install_status, operational_status, age_days, support_group
```
- **Implementation:** Adjust `install_status` values to your list. Flag CIs stuck in procurement or “pending install” beyond SLA. Report retired CIs still `operational` in error.
- **Visualization:** Table (stuck lifecycles), Bar chart (count by stuck state), Line chart (backlog trend).
- **CIM Models:** N/A

---

### UC-16.2.15 · Asset Decommission Verification
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Confirms decommissioned servers no longer appear in monitoring, AD, or hypervisor inventory — reducing zombie assets and license bleed.
- **App/TA:** Monitoring + CMDB
- **Data Sources:** Decommission change tickets, `snow:cmdb_ci`, `vmware:inv:vm`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state="Closed" earliest=-30d
| where match(lower(short_description),"(?i)decom|retire") OR lower(category)="retire"
| rename cmdb_ci as ci_sys_id
| join type=left max=1 ci_sys_id [ search index=itsm sourcetype="snow:cmdb_ci" | rename sys_id as ci_sys_id | table ci_sys_id, install_status, operational_status ]
| where install_status!="retired" AND lower(operational_status)!="retired" AND lower(operational_status)!="non-operational"
| table number, short_description, ci_sys_id, install_status, operational_status
```
- **Implementation:** Map `cmdb_ci` (or task CI list) from the change; normalize `install_status`/`operational_status` values to your CMDB. Optionally join inventory (`vmware:inv:vm`) on hostname to catch VMs still present. Drive cleanup when decom CHG is closed but CI not retired.
- **Visualization:** Table (failed decom verification), Single value (open exceptions), Bar chart (by team).
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
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
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
- **CIM Models:** N/A

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
- **CIM Models:** N/A

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

### UC-16.3.10 · Business Service Availability (Composite SLA)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Compliance
- **Value:** Rolls up component availability into a single business-service SLA percentage (weighted or “all essential up”) for customer-facing reporting — beyond host-level heatmaps.
- **App/TA:** Splunk ITSI, or custom lookups + summary indexing
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=monitoring` normalized health events, `business_service_map.csv`
- **SPL:**
```spl
index=monitoring sourcetype IN (server_health, app_health, db_health) earliest=-24h
| eval up=if(status="ok" OR status="up",1,0)
| stats latest(up) as up by component_name
| lookup business_service_map.csv component_name OUTPUT business_service, weight, is_essential
| eval w=coalesce(weight,1)
| stats max(eval(if((is_essential=1 OR lower(is_essential)="true") AND up=0,1,0))) as essential_down
       sum(eval(w*up)) as weighted_up
       sum(w) as total_weight by business_service
| eval composite_sla=if(essential_down>0, 0, round(100*weighted_up/total_weight,2))
| where composite_sla < 99.9 OR essential_down>0
| table business_service, composite_sla, essential_down
```
- **Implementation:** Define `business_service_map.csv` with components, optional weights, and `is_essential` (any essential down forces SLA=0 or “breach”). Ingest normalized availability per component every 5 minutes; backfill from summary index for monthly SLA. Align with contract SLAs (e.g., 99.9% monthly). ITSI can replace this with service KPIs and composite service health.
- **Visualization:** Single value (composite SLA % per service), Bar chart (SLA vs target), Table (breaching services), ITSI Service Analyzer (if licensed).
- **CIM Models:** N/A

---

### UC-16.3.11 · Batch Job Schedule Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Verifies scheduled batch jobs (ETL, billing, backups) started and finished within expected windows — catching silent scheduler failures before downstream SLAs break.
- **App/TA:** Control-M, Autosys, cron/syslog, mainframe SMF (custom)
- **Data Sources:** `sourcetype=controlm:job`, `sourcetype=autosys:job`, or `sourcetype=syslog` with scheduler tags
- **SPL:**
```spl
index=batch sourcetype="controlm:job" earliest=-7d@d
| eval day=strftime(_time,"%Y-%m-%d")
| eval ended_ok=if(match(lower(status),"(?i)ended ok|success"),1,0)
| stats max(ended_ok) as day_ok by job_name, day
| where day_ok=0
| table job_name, day
```
- **Implementation:** Map vendor fields: `scheduled_time`, end status, job name. For cron, ingest start/stop lines and compare to `batch_schedule.csv` lookup (job, expected cron, max duration). Alert when `ran_ok=0` for a calendar day. Tune time zones.
- **Visualization:** Table (missed jobs), Calendar (job success by day), Line chart (miss rate trend).
- **CIM Models:** N/A

---


### UC-16.3.12 · Control-M Job Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Batch job success/failure and SLA compliance are critical for data pipelines and scheduled workloads. Failed or late jobs can cascade to downstream systems and reporting.
- **App/TA:** Custom (Control-M Automation API)
- **Data Sources:** Control-M /run/jobs/status, job history
- **SPL:**
```spl
index=cicd sourcetype="controlm:job"
| where status="Failed" OR status="Ended Not OK" OR (sla_met="false" AND status="Ended OK")
| table _time, job_id, job_name, folder, status, order_date, run_as, end_time, sla_met
| sort -_time
```
- **Implementation:** Poll Control-M Automation API for job status and history. Ingest job_id, job_name, status, order_date, end_time, sla_met. Alert on Failed or Ended Not OK. Alert on SLA violations. Track success rate by folder and job. Report on batch job health and SLA compliance percentage.
- **Visualization:** Table (failed/late jobs), Single value (success rate %), Timeline (job outcomes), Bar chart (failures by folder).
- **CIM Models:** N/A

---

### 16.4 Change & Release Management

**Primary App/TA:** Splunk Add-on for ServiceNow (`Splunk_TA_snow`), Splunk Add-on for Jira Service Management (release data), optional CI/CD webhook correlation.

---

### UC-16.4.1 · Unauthorized Change Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Changes executed without approval or outside policy create audit exposure and outage risk; detecting them early supports SOC-2/ITIL controls and rapid rollback decisions.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request"
| eval approved=coalesce(approval,"") 
| where match(lower(u_authorization),"(?i)unauthorized|rejected") OR (isnull(cab_date) AND lower(type)!="standard" AND lower(category)!="routine")
| table _time, number, short_description, state, type, u_authorization, opened_by
| sort -_time
```
- **Implementation:** Ingest change_request with approval, CAB, and authorization fields mapped from ServiceNow. Build allowlists for standard/pre-approved change models. Alert when production-impacting changes lack `cab_date` or show `rejected`/`unauthorized` authorization. Correlate with CMDB and deployment tools for out-of-band activity.
- **Visualization:** Table (flagged changes), Single value (unauthorized count — target: 0), Timeline (violations).
- **CIM Models:** N/A

---

### UC-16.4.2 · Change Window Compliance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Change
- **Value:** Work performed outside agreed maintenance windows disrupts users and breaks SLAs; measuring compliance enforces scheduling discipline and supports customer communication.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state IN ("Closed","Implemented")
| eval start=strptime(start_date,"%Y-%m-%d %H:%M:%S"), end=strptime(end_date,"%Y-%m-%d %H:%M:%S")
| eval window_start=strptime(planned_start,"%Y-%m-%d %H:%M:%S"), window_end=strptime(planned_end,"%Y-%m-%d %H:%M:%S")
| eval outside_window=if(start<window_start OR end>window_end,1,0)
| stats sum(outside_window) as breaches count as total by assignment_group
| eval breach_pct=round(100*breaches/total,1)
| where breach_pct > 0
| sort -breach_pct
```
- **Implementation:** Map `planned_start`/`planned_end` and actual work `start_date`/`end_date` from the change record (field names vary—use transforms). Flag implementations that begin early or finish late versus the approved window. Report by assignment group and business service. Exclude emergency changes with documented extensions via change task.
- **Visualization:** Bar chart (breach % by team), Table (non-compliant CHGs), Line chart (weekly compliance %).
- **CIM Models:** N/A

---

### UC-16.4.3 · Failed Change Correlation with Incident Spikes
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Change
- **Value:** Linking unsuccessful changes to incident volume proves root cause for major reviews and helps tighten testing or rollback criteria for similar changes.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`, `sourcetype=snow:incident`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state="Closed"
| where lower(close_code)="unsuccessful"
| eval ci=cmdb_ci
| join type=left max=1 ci [
  search index=itsm sourcetype="snow:incident" earliest=-30d
  | rename cmdb_ci as ci
  | stats count as inc_count by ci
]
| where isnotnull(inc_count) AND inc_count>0
| table number, short_description, ci, inc_count
```
- **Implementation:** Align `cmdb_ci` on change and incident. Use `join` with time bounds via subsearch or `transaction` on `ci` plus `_time` window (e.g., 4h after change close). Prefer native `caused_by` or `problem_id` when populated. Dashboard: unsuccessful changes with related incident counts in the follow-up window. Use for PIR and change model updates.
- **Visualization:** Table (failed CHG + incident count), Timeline (CHG vs incidents), Sankey (change → CI → incidents).
- **CIM Models:** N/A

---

### UC-16.4.4 · Release Deployment Success Rate Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Change
- **Value:** Release success rate summarizes delivery health; sustained drops signal quality gaps in testing, automation, or release windows.
- **App/TA:** `Splunk_TA_snow`, CI/CD release tags (optional)
- **Data Sources:** `sourcetype=snow:change_request`, `sourcetype=snow:release`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" (category="Release" OR type="Release")
| eval success=if(lower(close_code)="successful" OR (state="Closed" AND lower(u_outcome)="success"),1,0)
| eval failed=if(lower(close_code)="unsuccessful" OR lower(u_outcome)="failed",1,0)
| timechart span=1w sum(success) as successes sum(failed) as failures
| eval success_rate=round(100*successes/(successes+failures),1)
```
- **Implementation:** Classify changes or release records that represent deployments (release catalog, RFC templates). Normalize `close_code`/`u_outcome`. Optionally join Jenkins/GitHub deployment events by `correlation_id`. Report weekly success rate by application and environment. Alert below target (e.g., 95%).
- **Visualization:** Line chart (success rate trend), Single value (rolling success %), Bar chart (by application).
- **CIM Models:** N/A

---

### UC-16.4.5 · Emergency Change Frequency Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operational, Risk
- **Value:** Chronic reliance on emergency changes indicates planning gaps or unstable platforms; trending frequency guides process improvement and capacity investments.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request"
| eval is_emergency=if(match(lower(type),"emergency") OR lower(u_change_model)="emergency",1,0)
| where is_emergency=1
| bin _time span=1w
| stats count by _time, assignment_group
| eventstats avg(count) as baseline by assignment_group
| where count > baseline*1.5
```
- **Implementation:** Tag emergency changes via `type`, model, or priority. Exclude duplicates from reopen workflows. Compare weekly counts to a rolling baseline per team. Alert on spikes; review in CAB for pattern (vendor defects, capacity, failed standard changes).
- **Visualization:** Line chart (emergency CHGs per week), Bar chart (by team), Table (recent emergencies with cause).
- **CIM Models:** N/A

---

### UC-16.4.6 · Change Advisory Board (CAB) Approval Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Governance
- **Value:** CAB sign-off for high-risk changes is a control point; measuring compliance before implementation reduces unauthorized production risk.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" u_risk IN ("High","1 - High")
| eval cab_ok=if(isnotnull(cab_date) AND cab_decision="Approved",1,0)
| where state IN ("Implement","Closed") AND cab_ok=0 AND lower(type)!="emergency"
| stats count by number, short_description, assignment_group, cab_decision
| sort -_time
```
- **Implementation:** Map risk, CAB meeting date, and decision fields from ServiceNow. Define policy: high-risk changes require CAB approval before `Implement`. Allow documented emergency exceptions with `CHG` tasks. Weekly report of violations; integrate with GRC dashboards.
- **Visualization:** Table (non-compliant CHGs), Single value (CAB compliance %), Pie chart (approved vs missing CAB).
- **CIM Models:** N/A

---

### UC-16.4.7 · Post-Implementation Review (PIR) Completion Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Quality
- **Value:** PIRs capture lessons from major incidents and failed changes; tracking completion closes the feedback loop and satisfies audit expectations after Sev1 events.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:problem`, `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" u_pir_required="true"
| eval pir_done=if(isnotnull(u_pir_completed) OR lower(u_pir_state)="closed",1,0)
| where pir_done=0
| eval age_days=round((now()-_time)/86400,0)
| where age_days>7
| stats latest(_time) as last_seen, values(number) as chg by problem_id, short_description
| sort last_seen
```
- **Implementation:** Use change fields or related problem tasks for PIR workflow (`u_pir_required`, completion date). For Sev1-linked changes, join `problem` records and PIR tasks. Alert when PIR is overdue (e.g., 7 days post closure). Escalate to problem management owner.
- **Visualization:** Table (open PIRs), Single value (overdue PIR count), Bar chart (PIR completion SLA by team).
- **CIM Models:** N/A

---

### UC-16.4.8 · Change Risk Assessment Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Quality, Risk
- **Value:** If “low risk” changes often fail or drive incidents, the risk model is miscalibrated; analytics improve scoring and reduce surprise outages.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** `sourcetype=snow:change_request`
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state="Closed"
| eval predicted=case(match(lower(u_risk),"low"),"Low",match(lower(u_risk),"medium"),"Medium",match(lower(u_risk),"high"),"High",true(),"Unknown")
| eval actual=if(lower(close_code)="unsuccessful" OR lower(u_customer_impact)="yes","Bad","Good")
| stats count by predicted, actual
| eventstats sum(count) as tot by predicted
| eval pct=round(100*count/tot,1)
| where predicted="Low" AND actual="Bad"
```
- **Implementation:** Compare `u_risk` at submission to outcomes (`close_code`, customer impact, related incident count within 24h). Build confusion-style matrix: predicted risk vs actual. Quarterly review with change managers; adjust questionnaires and automation gates. Requires consistent field extraction in the TA.
- **Visualization:** Matrix heatmap (predicted vs actual), Table (low-risk failures), Line chart (calibration trend quarter over quarter).
- **CIM Models:** N/A

