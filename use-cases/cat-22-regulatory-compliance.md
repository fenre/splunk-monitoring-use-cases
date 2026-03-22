## 22. Regulatory and Compliance Frameworks

### 22.1 GDPR

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.1.1 · GDPR PII Detection in Application Log Data (Art. 5/6)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Detects email, phone, and SSN patterns in indexed application and web logs so controllers can prove technical measures for data minimisation and lawful processing under Arts. 5-6.
- **App/TA:** Splunk Edge Processor (Splunk Cloud Platform — ingest-time PII rules), Splunk Common Information Model Add-on (Splunkbase 1621)
- **Data Sources:** `index=main` OR `index=web` OR `index=app` — any high-volume text-bearing sourcetype such as `sourcetype="access_combined"`, `sourcetype="log4j"`, or custom application sourcetypes
- **SPL:**
```spl
(index=main OR index=web OR index=app) earliest=-24h
| regex _raw="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
| eval pii_type="email"
| append [
    search (index=main OR index=web OR index=app) earliest=-24h
    | regex _raw="\b\d{3}-\d{2}-\d{4}\b"
    | eval pii_type="ssn_pattern"
  ]
| stats count by index, sourcetype, host, pii_type
| sort - count
```
- **Implementation:** (1) In Splunk Cloud, configure Edge Processor pipelines with built-in PII detection rules for net-new data to mask at ingest; (2) run this SPL against existing indexes to find residual PII; (3) route hits to a restricted summary index for DPO review; (4) remediate at source (masking, log redaction, field drops in props.conf/transforms.conf) and re-run to verify reduction.
- **Visualization:** Bar chart (hits by sourcetype/host), Table (top offending sources by PII type), Single value (total PII pattern matches vs prior period).
- **CIM Models:** Web (for `access_combined` when CIM-tagged)

---

### UC-22.1.2 · GDPR Data Subject Access Request Fulfillment Tracking (Art. 15-22)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Performance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Measures DSAR ticket lifecycle from opened to closed against a 30-calendar-day SLA so privacy and audit teams can evidence timely handling of access, rectification, erasure, and portability requests.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, cat_item, opened_at, closed_at, state, short_description) or `sourcetype="snow:incident"` (number, category, opened_at, closed_at, short_description, priority)
- **SPL:**
```spl
index=itsm (sourcetype="snow:sc_req_item" OR sourcetype="snow:incident")
    (cat_item="*Subject Access*" OR short_description="*DSAR*" OR short_description="*data subject*")
| eval opened_epoch=strptime(opened_at, "%Y-%m-%d %H:%M:%S")
| eval closed_epoch=if(isnotnull(closed_at), strptime(closed_at, "%Y-%m-%d %H:%M:%S"), null())
| eval age_days=round((now()-opened_epoch)/86400, 1)
| eval sla_met=if(isnotnull(closed_epoch) AND (closed_epoch-opened_epoch)<=2592000, "Met", "Missed")
| eval open_breach=if(isnull(closed_epoch) AND age_days>30, "Open_SLA_Breach", null())
| table _time, number, sourcetype, state, age_days, sla_met, open_breach, short_description
| sort - age_days
```
- **Implementation:** (1) Install Splunk Add-on for ServiceNow (1928) with sc_req_item and incident inputs enabled; (2) align `cat_item`/`short_description` filters with your DSAR catalogue naming; (3) confirm timestamp format in `opened_at`/`closed_at` and adjust `strptime` format if needed; (4) schedule daily and alert on `open_breach`.
- **Visualization:** Column chart (Met vs Missed), Time chart (DSAR volume), Table (open breaches), Single value (% within 30 days).
- **CIM Models:** Ticket Management (ServiceNow TA mappings)

---

### UC-22.1.3 · GDPR Breach Notification Timeline Monitoring (Art. 33, 72-hour rule)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** The key GDPR Art. 33 evidence artifacts are time-to-DPO notification and time-to-supervisory authority filing, not just SOC notable age. This use case tracks both handoff milestones, preventing false compliance comfort from measuring queue time alone.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro (rule_name, urgency, status, owner, status_description, _time)
- **SPL:**
```spl
`notable` status IN ("New","In Progress","Pending") earliest=-7d
| eval hours_since_detection=round((now()-_time)/3600, 2)
| eval near_deadline=if(hours_since_detection>=60 AND hours_since_detection<72, 1, 0)
| eval breached_72h=if(hours_since_detection>72, 1, 0)
| table _time, rule_name, urgency, status, owner, status_description, hours_since_detection, near_deadline, breached_72h
| sort - breached_72h, - hours_since_detection
```
- **Implementation:** (1) Ensure Incident Review workflow populates `owner`, `status`, and `status_description` at each milestone; (2) tag correlation searches that represent personal-data breaches with a `gdpr_relevant` field or label; (3) schedule hourly with alert when `near_deadline=1` or `breached_72h=1`; (4) attach runbook linking to DPO/legal notification steps.
- **Visualization:** Timeline (notable aging milestones), Table (aging notables), Single value (count past 60h), Alert list (breach candidates).
- **CIM Models:** N/A

---

### UC-22.1.4 · GDPR Data Retention Policy Enforcement (Art. 5(1)(e))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Capacity
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Audits Splunk index-level retention settings against written data retention policy so personal data in logs is not kept longer than necessary under the storage limitation principle.
- **App/TA:** Splunk Enterprise / Splunk Cloud Platform (native `| rest` API, no separate TA required)
- **Data Sources:** REST endpoint: `/services/data/indexes` — fields: `title`, `frozenTimePeriodInSecs`, `maxTotalDataSizeMB`, `disabled`
- **SPL:**
```spl
| rest /services/data/indexes splunk_server=local count=0
| search disabled=0 NOT title IN ("_*", "history", "summary")
| eval retention_days=round(frozenTimePeriodInSecs/86400, 1)
| eval policy_max_days=case(
    match(title,"^(hr|pii|gdpr)"), 180,
    match(title,"^(security|sec)"), 365,
    1=1, 365)
| eval violation=if(retention_days>policy_max_days, "Exceeds_Policy", "OK")
| table title, retention_days, policy_max_days, frozenTimePeriodInSecs, maxTotalDataSizeMB, violation
| sort - retention_days
```
- **Implementation:** (1) Run from a scheduled search on the search head (requires admin capability for REST); (2) replace the `case()` block with a lookup `index_retention_policy.csv` mapping index names to required max retention days; (3) export results to GRC tickets when violations trigger; (4) pair with archive/freeze path review outside Splunk for complete retention evidence.
- **Visualization:** Table (index, retention, policy, violation), Bar chart (retention by index), Single value (violation count).
- **CIM Models:** N/A

---

### UC-22.1.5 · GDPR Consent Management Audit Trail (Art. 7)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Audit
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Preserves a searchable trail of consent grant, refuse, and withdraw events from web applications for accountability and consent withdrawal parity requirements.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), HTTP Event Collector (HEC — platform capability for structured JSON from consent APIs)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (clientip, uri, method, status, useragent) for consent page interactions; or custom HEC JSON events with explicit consent fields
- **SPL:**
```spl
index=web sourcetype="access_combined" earliest=-7d
    (uri="*/consent*" OR uri="*/privacy-preferences*")
| rex field=uri_query "action=(?<consent_action>[^&]+)"
| eval consent_event=coalesce(consent_action, if(status=200, "page_view", "error"))
| stats count by clientip, uri, consent_event, status
| sort - count
```
- **Implementation:** (1) Ingest Apache/nginx access logs via TA 3186 or Universal Forwarder file inputs; (2) for richer evidence, emit HEC JSON from the consent microservice with explicit `action`, `purpose_id`, and hashed subject ID fields; (3) map URIs to consent purposes via a lookup `consent_uri_map.csv`; (4) restrict index ACLs to privacy teams; (5) schedule weekly reporting for consent withdrawal ratio monitoring.
- **Visualization:** Time chart (consent page hits), Stacked bar (grant vs revoke/withdraw), Table (top consent events by URI).
- **CIM Models:** Web (when CIM-tagged via TA 3186)

---

### UC-22.1.6 · GDPR Cross-Border Data Transfer Monitoring (Art. 44-49)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Highlights outbound traffic volumes to destinations outside the approved EEA/adequacy footprint so transfers can be gated by SCCs, BCRs, TIAs, or blocking controls.
- **App/TA:** Splunk Common Information Model Add-on (Splunkbase 1621), Palo Alto Networks Add-on (Splunkbase 2757) or equivalent firewall TA populating Network_Traffic data model
- **Premium Apps:** Splunk Enterprise Security (optional, for asset/identity context)
- **Data Sources:** CIM `Network_Traffic` data model (`All_Traffic.dest`, `All_Traffic.bytes_out`, `All_Traffic.action`) — backed by sourcetypes such as `sourcetype="pan:traffic"`, `sourcetype="cisco:asa"`, or `sourcetype="fortigate_traffic"`
- **SPL:**
```spl
| tstats summariesonly=t sum(All_Traffic.bytes_out) as bytes_out
    from datamodel=Network_Traffic.All_Traffic
    where All_Traffic.action="allowed"
    by All_Traffic.dest
| rename All_Traffic.* as *
| iplocation dest
| lookup eea_and_adequate_countries.csv Country OUTPUT transfer_basis
| where isnull(transfer_basis) OR transfer_basis="restricted"
| eval bytes_gb=round(bytes_out/1073741824, 2)
| sort 100 - bytes_out
| head 100
| table dest, Country, bytes_gb, transfer_basis
```
- **Implementation:** (1) Accelerate `Network_Traffic` data model in Settings > Data Models; (2) create `eea_and_adequate_countries.csv` with `Country` values matching `iplocation` output (MaxMind) and your legal team's adequacy list (EEA + UK + other recognised adequacy decisions); (3) add a `transfer_basis` column (e.g. SCC, BCR, adequacy) for approved destinations; (4) tune with CDN/exception lookups by `dest`.
- **Visualization:** Choropleth (top non-EEA destinations), Bar chart (bytes by country), Table (restricted transfers).
- **CIM Models:** Network_Traffic

---

### 22.2 NIS2

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.2.1 · NIS2 Incident Detection and 24-Hour Early Warning Reporting (Art. 23)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Measures detection-to-response progress on high-urgency ES notables to support early-warning obligations and internal crisis reporting within the first 24 hours of awareness.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro (rule_name, urgency, status, owner, status_description, _time)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") earliest=-3d
| eval hours_open=round((now()-_time)/3600, 2)
| eval t_minus_4h=if(hours_open>=20 AND hours_open<24 AND status!="Closed", 1, 0)
| eval past_24h_open=if(hours_open>24 AND status!="Closed", 1, 0)
| table _time, rule_name, urgency, status, owner, status_description, hours_open, t_minus_4h, past_24h_open
| where t_minus_4h=1 OR past_24h_open=1
| sort - past_24h_open, - hours_open
```
- **Implementation:** (1) Map ES `urgency` values to your NIS2 incident classes; (2) require analysts to transition `status`/`status_description` at acknowledgement and containment; (3) alert on `t_minus_4h` for CSIRT/legal escalation; (4) export `past_24h_open` rows into crisis-management runbooks and regulatory reporting drafts.
- **Visualization:** Timeline (notable aging), Table (stale high-urgency items), Single value (count approaching 24h).
- **CIM Models:** N/A

---

### UC-22.2.2 · NIS2 Supply Chain Security Monitoring (Art. 21(2)(d))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Correlates vendor privileged access sessions (PAM) with threat intelligence on supplier domains to surface abnormal third-party activity affecting essential services.
- **App/TA:** Splunk Add-on for CyberArk (Splunkbase 2891), Splunk Enterprise Security (Splunkbase 263) for threat intelligence lookups
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=pam` `sourcetype="cyberark:session"` (user, target_host, target_account, protocol, duration_min, session_id); `index=pam` `sourcetype="cyberark:vault"` (user, account, action, target)
- **SPL:**
```spl
index=pam sourcetype="cyberark:session" earliest=-24h
| rex field=target_host "(?<target_domain>[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"
| stats sum(duration_min) as total_min, dc(session_id) as sessions by user, target_host, target_domain, target_account
| lookup threat_intel_domain_lookup domain AS target_domain OUTPUT description AS ti_description, weight AS ti_weight
| where isnotnull(ti_weight) OR total_min>120
| sort - total_min
```
- **Implementation:** (1) Deploy CyberArk TA 2891 and send Vault/PSM session logs to `index=pam`; (2) maintain `threat_intel_domain_lookup` from ES Threat Intelligence exports or STIX/TAXII feeds; (3) tag supplier-owned targets in `vendor_asset_lookup.csv` and join for baseline comparison; (4) alert on TI matches or unusually long sessions.
- **Visualization:** Table (sessions with TI hits), Bar chart (minutes by supplier), Heatmap (user x hour).
- **CIM Models:** Authentication (PAM sessions when CIM-mapped via TA)

---

### UC-22.2.3 · NIS2 Vulnerability Disclosure and Patch Management Tracking (Art. 21(2)(e))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Tracks CVE exposure and remediation latency from first detection to fix to demonstrate systematic vulnerability handling for essential and important entities.
- **App/TA:** Tenable Add-On for Splunk (Splunkbase 4060)
- **Data Sources:** `index=vulnerability` `sourcetype="tenable:vuln"` (cve, severity, plugin_name, host, first_found, last_fixed, state)
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" state="Active"
| eval host=coalesce(host, hostname, dns_name)
| eval first_found=coalesce(first_found, first_seen)
| eval age_days=round((now()-first_found)/86400, 1)
| eval sla_days=case(severity="Critical",7, severity="High",30, 1=1,90)
| eval sla_breach=if(age_days>sla_days, 1, 0)
| stats count as open_vulns, max(age_days) as max_age by host, severity
| where sla_breach=1
| sort - max_age
| table host, severity, open_vulns, max_age, sla_days
```
- **Implementation:** (1) Install Tenable Add-On (4060) and route data to `index=vulnerability`; (2) validate field names (`cve_id` vs `cve`, `first_seen` vs `first_found`) in Data Summary; (3) tune `sla_days` to your security policy; (4) integrate with change/patch tickets for exception tracking.
- **Visualization:** Table (over-SLA assets), Bar chart (count by severity), Line chart (open critical CVE trend).
- **CIM Models:** Vulnerabilities

---

### UC-22.2.4 · NIS2 Business Continuity and Crisis Management Monitoring (Art. 21(2)(c))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Uses ITSI service health and KPI breach signals as live evidence that continuity targets (RTO/RPO expressed as service KPIs) are monitored during incidents and crises.
- **App/TA:** Splunk IT Service Intelligence (Splunkbase 1841)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=itsi_summary` (health_score, service_name, kpi_name, severity_value, severity_label, is_service_in_maintenance)
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0 earliest=-24h
| eval rto_rpo_risk=if(severity_value>=3 OR health_score<70, 1, 0)
| stats avg(health_score) as avg_health,
        count(eval(rto_rpo_risk=1)) as breach_events
    by service_name, kpi_name
| where breach_events>0 OR avg_health<85
| sort - breach_events
| table service_name, kpi_name, avg_health, breach_events
```
- **Implementation:** (1) Model each regulated NIS2 service in ITSI with KPIs tied to RTO/RPO (e.g. availability, transaction success, replication lag); (2) set severity thresholds so `severity_value>=3` aligns with crisis playbooks; (3) display on Glass Table / Service Analyzer for NOC/C-level crisis calls; (4) attach episode workflows for major incidents.
- **Visualization:** Service Analyzer (ITSI), Glass Table, Line chart (health_score over time), Table (KPIs in breach).
- **CIM Models:** N/A

---

### UC-22.2.5 · NIS2 Network and Information Systems Access Control Audit (Art. 21(2)(i))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Audits interactive logon success/failure and special privilege assignment on Windows assets supporting essential services, including after-hours and non-interactive patterns, for access-control assurance.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742)
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Security"` (EventCode, Account_Name, Logon_Type, Workstation_Name, Status, dest)
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Security" EventCode IN (4624, 4625, 4672) earliest=-24h
| eval auth_result=case(EventCode=4624,"success", EventCode=4625,"failure", EventCode=4672,"special_privileges", 1=1,"other")
| eval after_hours=if(tonumber(strftime(_time,"%H"))<7 OR tonumber(strftime(_time,"%H"))>19, 1, 0)
| stats count by EventCode, auth_result, Account_Name, dest, Logon_Type, after_hours
| sort -count
```
- **Implementation:** (1) Deploy Splunk Add-on for Windows (742) with Security log collection from domain controllers and member servers; (2) enable Group Policy auditing for logon events and special privileges; (3) tune out known service accounts via `lookup service_accounts.csv`; (4) send high-value rows (4625 spikes, 4672 after-hours) to SOAR/ITSM; (5) map to Authentication CIM for ES content.
- **Visualization:** Time chart (failed logons 4625), Table (privileged logons 4672), Bar chart (after_hours vs business hours).
- **CIM Models:** Authentication

---

### 22.3 DORA

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.3.1 · DORA ICT Risk Management Dashboard (Art. 5-16)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Compliance
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Produces an auditable, continuously refreshed view of residual ICT risk by business entity using the ES risk scoring pipeline, so risk owners can evidence identification, assessment, and monitoring of ICT risk without manual spreadsheet rollups.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Common Information Model Add-on (Splunkbase 1621)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=risk` `sourcetype="stash"` (risk_object, risk_object_type, risk_score, source, _time)
- **SPL:**
```spl
index=risk sourcetype="stash" earliest=-30d@d
| stats latest(risk_score) as residual_risk, max(risk_score) as peak_risk, dc(source) as contributing_sources, values(source) as source_list by risk_object, risk_object_type
| lookup business_entity_lookup risk_object OUTPUT business_entity
| fillnull value="UNASSIGNED" business_entity
| stats avg(residual_risk) as avg_residual, max(residual_risk) as max_residual, sum(contributing_sources) as total_sources by business_entity
| sort - avg_residual
| table business_entity, avg_residual, max_residual, total_sources
```
- **Implementation:** (1) Ensure ES Risk Notable / risk scoring populates `index=risk`; (2) create KV lookup `business_entity_lookup` keyed by `risk_object` (hosts/users/identities) mapping to `business_entity` from CMDB/ServiceNow export; (3) schedule daily for management reporting; (4) drill down to `risk_object` detail in Dashboard Studio.
- **Visualization:** Bar chart (avg/max residual risk by entity), Single value KPI tiles (top entity risk), Table with drilldown.
- **CIM Models:** Risk

---

### UC-22.3.2 · DORA ICT Incident Classification and Reporting (Art. 17-23)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Maps ES notable urgency/severity to DORA major vs significant classification and computes filing deadline clocks (4h for major, 72h for others) for operational resilience incident workflows.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro (urgency, severity, rule_name, status, owner, _time)
- **SPL:**
```spl
`notable` status IN ("New","In Progress") earliest=-7d
| eval dora_class=case(
    urgency IN ("critical","high") OR severity IN ("critical","high"), "major",
    1=1, "significant_or_other")
| eval filing_deadline_h=if(dora_class="major", 4, 72)
| eval hours_elapsed=round((now()-_time)/3600, 2)
| eval filing_breach=if(hours_elapsed>filing_deadline_h, 1, 0)
| table _time, rule_name, urgency, severity, dora_class, filing_deadline_h, hours_elapsed, filing_breach, owner, status
| sort - filing_breach, - hours_elapsed
```
- **Implementation:** (1) Confirm ES notable ingestion and that `urgency`/`severity` are populated; (2) align `dora_class` thresholds to your legal/ops policy; (3) wire alerts for `filing_breach=1` to SOC + resilience comms queues; (4) attach runbook for DORA reporting to competent authority.
- **Visualization:** Table with conditional formatting on deadline breach, Timeline chart of notables by `dora_class`, Single value (count approaching deadline).
- **CIM Models:** N/A

---

### UC-22.3.3 · DORA Digital Operational Resilience Testing (Art. 24-27)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Tracks scheduled resilience test outcomes via ITSI KPI breaches and highlights testing gaps (missing runs, failed thresholds) for Board/ICT oversight reporting on digital resilience.
- **App/TA:** Splunk IT Service Intelligence (Splunkbase 1841)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=itsi_summary` (service_name, kpi_name, alert_value, severity_value, is_service_in_maintenance, _time)
- **SPL:**
```spl
index=itsi_summary earliest=-90d is_service_in_maintenance=0
| eval kpi_l=lower(kpi_name)
| where match(kpi_l,"(dr|disaster|resilience|failover|recovery|rto|rpo|backup|restore)")
| bin _time span=1d
| stats latest(alert_value) as last_value, latest(severity_value) as last_severity by _time, service_name, kpi_name
| eval test_fail=if(last_severity>=4 OR last_value>0, 1, 0)
| timechart span=7d sum(test_fail) as failed_observations, dc(service_name) as impacted_services
```
- **Implementation:** (1) Standardize KPI naming for resilience tests with tokens like `DR`, `Failover`, `Restore` in `kpi_name`; (2) ensure ITSI services represent regulated business services; (3) exclude maintenance noise via `is_service_in_maintenance`; (4) add a lookup of expected test windows and compare expected vs observed runs for gap detection.
- **Visualization:** Timechart (failed observations), Heatmap (service x week), Table (last failures with drilldown to deep dives).
- **CIM Models:** N/A

---

### UC-22.3.4 · DORA Third-Party ICT Provider Concentration Risk (Art. 28-44)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Risk, Compliance
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Quantifies operational dependency on specific cloud providers by measuring API activity concentration across accounts, regions, and services, supporting third-party risk assessments and exit planning.
- **App/TA:** Splunk Add-on for Amazon Web Services (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Data Sources:** `index=aws` `sourcetype="aws:cloudtrail"` (eventSource, eventName, awsRegion, userIdentity.arn, recipientAccountId); `index=azure` `sourcetype="mscs:azure:auditlog"` (operationName, resourceProvider, callerIpAddress, ResourceGroup)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudtrail") OR (index=azure sourcetype="mscs:azure:auditlog")
| eval provider=if(sourcetype=="aws:cloudtrail", "AWS", "Azure")
| eval service=coalesce(eventSource, resourceProvider)
| eval region=coalesce(awsRegion, ResourceGroup)
| stats count by provider, service, region
| eventstats sum(count) as total
| eval concentration_pct=round(100*count/total, 2)
| sort - concentration_pct
| head 50
| table provider, service, region, count, concentration_pct
```
- **Implementation:** (1) Ingest CloudTrail (org trail) into `index=aws` using AWS TA; (2) ingest Azure Activity via Event Hub using Microsoft Cloud Services TA; (3) create a saved search weekly for procurement/third-party governance dashboards; (4) enrich with cloud account tags via lookup (cost center, vendor name).
- **Visualization:** Treemap (share by service), Stacked bar by provider, Table of top (service, region) pairs.
- **CIM Models:** Change (CloudTrail often maps via TA)

---

### UC-22.3.5 · DORA Cross-Region Disaster Recovery Compliance (Art. 11-12)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Compliance
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Demonstrates ongoing cross-region replication and DR operations evidence from cloud provider audit trails combined with ITSI service health across regions.
- **App/TA:** Splunk Add-on for Amazon Web Services (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk IT Service Intelligence (Splunkbase 1841)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI) (optional but recommended)
- **Data Sources:** `index=aws` `sourcetype="aws:cloudtrail"` (eventName, awsRegion, requestParameters); `index=azure` `sourcetype="mscs:azure:auditlog"` (operationName, Category, ResourceGroup); `index=itsi_summary` (service_name, health_score, severity_value)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail"
    eventName IN ("PutBucketReplication","DeleteBucketReplication","ReplicateObject","StartDBInstanceAutomatedBackupsReplication")
| stats count by eventName, awsRegion, recipientAccountId
| sort - count
```
```spl
index=itsi_summary is_service_in_maintenance=0 earliest=-24h
| eval region_tag=coalesce(entity_key, service_name)
| stats avg(health_score) as avg_health, max(severity_value) as worst_severity by service_name
| where worst_severity>=3 OR avg_health<80
| table service_name, avg_health, worst_severity
```
- **Implementation:** (1) Ensure CloudTrail includes data-plane events for replication visibility; (2) for Azure, route Activity logs to Event Hub and confirm `mscs:azure:auditlog` parsing; (3) in ITSI, tag entities with `region` and bind KPIs representing DR readiness; (4) combine cloud evidence and ITSI health panels in a single DR compliance dashboard.
- **Visualization:** Timeline of replication events, Geographic map (counts by region), ITSI service health single values by region.
- **CIM Models:** Change (replication changes)

---

### 22.4 CCPA

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.4.1 · CCPA Consumer Data Access and Deletion Request Tracking (§1798.100-105)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Performance
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Tracks privacy request fulfillment work items end-to-end and flags requests at risk of missing the 45-day statutory response window.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, opened_at, closed_at, state, cat_item, short_description) or `sourcetype="snow:incident"` (number, opened_at, closed_at, state, short_description)
- **SPL:**
```spl
index=itsm (sourcetype="snow:sc_req_item" OR sourcetype="snow:incident")
    (cat_item="*CCPA*" OR cat_item="*Privacy*" OR short_description="*CCPA*" OR short_description="*Consumer Privacy*")
| eval opened_epoch=strptime(opened_at, "%Y-%m-%d %H:%M:%S")
| eval closed_epoch=if(isnotnull(closed_at), strptime(closed_at, "%Y-%m-%d %H:%M:%S"), null())
| eval age_days=round((now()-opened_epoch)/86400, 1)
| eval sla_days=45
| eval breach=if(isnull(closed_epoch) AND age_days>sla_days, 1, 0)
| eval days_remaining=if(isnull(closed_epoch), sla_days-age_days, null())
| table _time, number, state, age_days, days_remaining, breach, short_description
| sort - breach, days_remaining
```
- **Implementation:** (1) Configure ServiceNow inputs for sc_req_item and/or incidents; (2) normalize catalog item names to match the filter (adjust `cat_item` strings); (3) if CCPA allows extensions, add fields for `extension_days` and update `sla_days` logic; (4) schedule daily with alert on `breach=1`.
- **Visualization:** Table (open requests with SLA countdown), Histogram (age distribution), Single value (% within 45 days).
- **CIM Models:** Ticket Management

---

### UC-22.4.2 · CCPA Data Sale Opt-Out Enforcement Monitoring (§1798.120)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Measures consumer interaction with "Do Not Sell/Share" flows and detects Global Privacy Control (GPC) signal presence for downstream marketing-system enforcement evidence.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186) or equivalent web server TA
- **Data Sources:** `index=web` `sourcetype="access_combined"` (clientip, status, method, uri, useragent)
- **SPL:**
```spl
index=web sourcetype="access_combined" earliest=-24h
| eval uri_l=lower(uri)
| where match(uri_l, "/(do-not-sell|dnsmpi|privacy-rights|opt-out)(/|$|\?)")
| eval gpc=if(match(_raw, "(?i)sec-gpc:\\s*1"), "GPC_Present", "No_GPC")
| stats count as page_hits, dc(clientip) as unique_visitors by uri, status, gpc
| sort - page_hits
```
- **Implementation:** (1) Configure web servers to log the GPC header (Apache: `%{Sec-GPC}i` / nginx: `$http_sec_gpc`) in the access log format; (2) ensure load balancers preserve the header to origin logs; (3) schedule daily for privacy team dashboards; (4) create a downstream dataset join with marketing system logs to verify opt-out enforcement.
- **Visualization:** Timechart (opt-out page hits), Pie chart (GPC present vs not), Table (top URIs by visitor count).
- **CIM Models:** Web

---

### UC-22.4.3 · CCPA Sensitive Personal Information Processing Audit (§1798.121)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Surfaces DLP policy hits from Microsoft 365 to demonstrate monitoring and limitation controls around sensitive personal information processing.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055)
- **Data Sources:** `index=o365` `sourcetype="ms:o365:management"` (Workload, Operation, PolicyName, UserPrincipalName, SensitiveInfoType, Severity)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInfoType, Severity, Operation
| sort - count
| table PolicyName, UserPrincipalName, SensitiveInfoType, Severity, count, Operation
```
- **Implementation:** (1) Enable Office 365 Management Activity inputs in TA 4055 and confirm `Workload="Dlp"` events are ingested; (2) map `SensitiveInfoType` values to your CCPA SPI categories via lookup; (3) alert on high-severity exfil patterns; (4) retain per legal hold requirements.
- **Visualization:** Bar chart (events by PolicyName), Heatmap (user x SensitiveInfoType), Line chart (daily volume by Severity).
- **CIM Models:** N/A

---

### 22.5 MiFID II

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.5.1 · MiFID II Trade and Transaction Reporting Completeness (Art. 26)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Performance
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Detects reporting gaps (missing submissions vs expected trading-day volume) and ARM/APA rejection spikes to support completeness and accuracy controls for transaction reporting oversight.
- **App/TA:** Splunk HTTP Event Collector (core platform) with JSON parsing, Financial Information eXchange (FIX) Log Parsing (Splunkbase 431) (optional)
- **Data Sources:** `index=trading` `sourcetype="_json"` `source="http:trx_reporting"` (transaction_report_id, trade_date, venue, report_status, reject_code)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:trx_reporting" earliest=-30d@d
| eval rejected=if(isnotnull(reject_code) AND reject_code!="", 1, 0)
| eval accepted=if(report_status IN ("ACCEPTED","ACKED","CONFIRMED") AND rejected=0, 1, 0)
| bin _time span=1d
| stats count as sent, sum(accepted) as accepted, sum(rejected) as rejects, dc(transaction_report_id) as distinct_reports by _time, venue
| eventstats avg(sent) as baseline by venue
| eval volume_gap=if(sent<baseline*0.75, 1, 0)
| where volume_gap=1 OR rejects>0
| table _time, venue, sent, accepted, rejects, volume_gap
| sort _time, venue
```
- **Implementation:** (1) Send ARM/APA acknowledgements and gateway rejects to HEC with a dedicated token; (2) standardize JSON keys (`reject_code`, `report_status`); (3) baseline "expected volume" can be replaced with a lookup of expected daily counts by `venue` and instrument class; (4) schedule daily for compliance desk review.
- **Visualization:** Timechart (accepted vs rejects), Single value (gap days counter), Table (worst venues by reject rate).
- **CIM Models:** N/A

---

### UC-22.5.2 · MiFID II Communications Recording and Retention Audit (Art. 16(7))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Audit
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Correlates collaboration recording signals (Webex) with telephony metadata (CUCM CDR) to evidence recording coverage and catch missing/failed capture patterns across communication channels.
- **App/TA:** Cisco WebEx Meetings Add-on for Splunk (Splunkbase 4991), Cisco CDR Reporting and Analytics (Splunkbase 669)
- **Data Sources:** `index=collab` `sourcetype="cisco:webex:meetings:history:recordaccesshistory"` (creationTime, meetingId, hostWebexID); `index=voip` `sourcetype="cisco:ucm:cdr"` (callingPartyNumber, calledPartyNumber, duration, dateTimeOrigination, origCause_value)
- **SPL:**
```spl
(index=collab sourcetype="cisco:webex:meetings:history:recordaccesshistory" earliest=-30d)
| stats count as recording_events, dc(meetingId) as distinct_meetings by hostWebexID
| sort - recording_events
```
```spl
index=voip sourcetype="cisco:ucm:cdr" earliest=-30d
| eval call_duration_min=round(duration/60, 1)
| stats count as calls, avg(call_duration_min) as avg_duration, sum(eval(if(origCause_value!="0" AND origCause_value!="16", 1, 0))) as failed_calls by callingPartyNumber
| where failed_calls>0 OR calls>100
| sort - calls
```
- **Implementation:** (1) Install Webex Meetings inputs from TA 4991; (2) ingest CUCM CDR files into `index=voip` with `cisco:ucm:cdr` sourcetype via TA 669; (3) define retention dashboards using your legal minimum (e.g. 5 years for MiFID II) via lookups tied to meeting/call identifiers; (4) alert on recording failures or gaps.
- **Visualization:** Timechart (recording events), CDR duration distribution, Table (failed calls).
- **CIM Models:** N/A

---

### UC-22.5.3 · MiFID II Best Execution Monitoring (Art. 27)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Performance
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Compares execution quality and routing latency across venues (price improvement, fees, speed) using structured order/execution JSON from OMS/EMS to support best execution oversight.
- **App/TA:** Splunk HTTP Event Collector (core platform) with JSON parsing, Financial Information eXchange (FIX) Log Parsing (Splunkbase 431) (optional)
- **Data Sources:** `index=trading` `sourcetype="_json"` `source="http:bestex"` (order_id, exec_id, venue, symbol, last_px, effective_spread_bps, fee_bps, exec_latency_ms, decision_time, report_time)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:bestex" earliest=-7d
| eval all_in_bps=effective_spread_bps+fee_bps
| stats median(all_in_bps) as p50_cost, median(exec_latency_ms) as p50_latency, count as fills by venue, symbol
| eventstats median(p50_cost) as global_p50 by symbol
| eval venue_delta=round(p50_cost-global_p50, 2)
| sort symbol, venue_delta
| table symbol, venue, fills, p50_cost, p50_latency, venue_delta
```
- **Implementation:** (1) Publish execution reports to HEC with consistent timestamps and normalized units (`effective_spread_bps`, `fee_bps`); (2) refresh baselines weekly; (3) exclude auctions/halts using flags in the JSON; (4) quarterly export for RTS 28 reporting.
- **Visualization:** Scatter (latency vs cost), Leaderboard table by venue, Box-style panels via stats.
- **CIM Models:** N/A

---

### 22.6 ISO 27001

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.6.1 · ISO 27001 Annex A Control Effectiveness Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Proves that detective controls implemented as ES correlation searches actually execute, complete, and produce hits — mapped to Annex A control IDs — so auditors see operating effectiveness, not only documented intent.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=_internal` `source=*scheduler.log*` (savedsearch_name, run_time, status, skip_reason); `` `notable` `` macro (rule_name, urgency, _time); CSV lookup `iso27001_annex_a_es_rule_control_lookup` (correlation_search_short, annex_a_control_id, control_title)
- **SPL:**
```spl
index=_internal source=*scheduler.log* savedsearch_name="*Correlation*" earliest=-30d
| stats count as executions,
        avg(run_time) as avg_run_time_sec,
        sum(eval(if(status=="skipped",1,0))) as skipped_runs
    by savedsearch_name
| eval correlation_search_short=replace(savedsearch_name, "(?i)^.*Correlation Search\\s*-\\s*", "")
| lookup iso27001_annex_a_es_rule_control_lookup correlation_search_short OUTPUT annex_a_control_id, control_title
| join type=left max=0 correlation_search_short [
    search `notable` earliest=-90d
    | stats count as notable_hits by rule_name
    | rename rule_name as correlation_search_short
  ]
| eval reliability_pct=round(100*(executions-skipped_runs)/executions, 1)
| fillnull value=0 notable_hits
| table annex_a_control_id, control_title, savedsearch_name, executions, skipped_runs, reliability_pct, notable_hits
| sort annex_a_control_id
```
- **Implementation:** (1) Build `iso27001_annex_a_es_rule_control_lookup.csv` on the ES search head: `correlation_search_short` must match ES `rule_name` as shown in Incident Review; (2) map each row to `annex_a_control_id` (e.g. A.12.4.1) and `control_title`; (3) ensure `_internal` scheduler data is available on the SH; (4) schedule weekly for control-owner review; alert on `skipped_runs` spikes or zero `notable_hits` for critical controls.
- **Visualization:** Table (control x rule health), Column chart (reliability_pct by rule), Single value (total skipped runs).
- **CIM Models:** N/A

---

### UC-22.6.2 · ISO 27001 Information Security Event Log Review Compliance (A.12.4)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Produces auditor-ready evidence that named users routinely query security data in Splunk (log review activity), including who reviewed which index classes and how often — not merely that logs exist.
- **App/TA:** Splunk Enterprise core auditing (`_audit` index, no separate TA required)
- **Data Sources:** `index=_audit` `action=search` (user, search, info, result_count, total_run_time, _time)
- **SPL:**
```spl
index=_audit action=search info=completed user!="splunk-system-user" earliest=-30d
| where match(search, "(?i)index\\s*=\\s*(security|notable|wineventlog|proxy|dns|firewall|ids)")
| bucket _time span=1d as review_day
| stats dc(user) as distinct_reviewers,
        count as review_searches,
        sum(result_count) as rows_examined,
        values(user) as sample_users
    by review_day
| eval cadence_met=if(distinct_reviewers>=1 AND review_searches>=1, 1, 0)
| sort - review_day
```
- **Implementation:** (1) Confirm audit logging is enabled for search activity and `_audit` retention meets policy; (2) edit the `match()` index list to your real security index names; (3) exclude service accounts via `user!=` or lookup; (4) monthly PDF/CSV export for ISO evidence packs; (5) tune minimum thresholds to your documented log review frequency.
- **Visualization:** Time chart (review_searches by day), Table (review_day, reviewers, cadence_met), Single value (rolling 30d cadence percentage).
- **CIM Models:** N/A

---

### UC-22.6.3 · ISO 27001 Access Rights Review and Recertification (A.9.2.5)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Captures group membership changes (on-prem AD or Entra ID) for access recertification evidence and detective alerting on privileged group churn.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Security"` (EventCode, SubjectUserName, MemberName, Group_Name, ComputerName); `index=azure` `sourcetype="mscs:azure:auditlog"` (activityDisplayName, targetResources, initiatedBy)
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Security"
    EventCode IN ("4728","4729","4732","4733","4756","4757")
| eval access_change=case(
    EventCode IN ("4728","4732","4756"), "member_added",
    EventCode IN ("4729","4733","4757"), "member_removed",
    1=1, "other")
| table _time, ComputerName, SubjectUserName, MemberName, Group_Name, EventCode, access_change
| sort - _time
```
```spl
index=azure sourcetype="mscs:azure:auditlog"
    activityDisplayName IN ("Add member to group","Remove member from group")
| table _time, activityDisplayName, initiatedBy.user.userPrincipalName, targetResources{}.displayName
| sort - _time
```
- **Implementation:** (1) Install Splunk_TA_windows on DCs or use Windows Event Collector; enable Advanced Audit Policy for Security Group Management; (2) for cloud, configure Microsoft Cloud Services TA for Entra ID audit events; (3) maintain `privileged_ad_groups.csv` keyed on `Group_Name` and `lookup` to flag high-risk groups; (4) feed quarterly CSV to IAM recertification; (5) alert on changes to privileged groups outside CAB windows.
- **Visualization:** Table (evidence export), Time chart (changes per day), Bar chart (changes by Group_Name).
- **CIM Models:** Authentication, Change

---

### 22.7 NIST CSF

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.7.1 · NIST CSF Maturity Posture Dashboard (Identify/Protect/Detect/Respond/Recover)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** Maps enabled ES correlation searches and risk scoring volume to NIST CSF functions for a defensible, data-driven maturity snapshot rather than a static policy diagram.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), CIM Risk data model
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `| rest /services/saved/searches` (title, disabled, eai:acl.app); `| from datamodel Risk.All_Risk` (search_name, risk_score, _time); CSV lookup `nist_csf_es_function_mapping` (correlation_search_name, nist_csf_function)
- **SPL:**
```spl
| rest /services/saved/searches splunk_server=local count=0
| search disabled=0 eai:acl.app="SplunkEnterpriseSecuritySuite" title="*Correlation Search*"
| lookup nist_csf_es_function_mapping correlation_search_name AS title OUTPUT nist_csf_function
| stats count as enabled_detections by nist_csf_function
```
```spl
| from datamodel Risk.All_Risk
| timechart span=7d sum(risk_score) as weekly_risk_points, dc(search_name) as distinct_risk_rules
```
- **Implementation:** (1) Create `nist_csf_es_function_mapping.csv` with `correlation_search_name` = full saved-search title and `nist_csf_function` in {Identify, Protect, Detect, Respond, Recover}; (2) adjust `eai:acl.app` if your ES app name differs; (3) refresh the REST panel after content upgrades; (4) document CSF tier targets separately in narrative.
- **Visualization:** Bar chart (enabled_detections by CSF function), Area chart (weekly_risk_points), Table (raw mapping for assessors).
- **CIM Models:** Risk

---

### UC-22.7.2 · NIST CSF Detect Function Coverage Gap Analysis (MITRE ATT&CK)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** Highlights MITRE techniques with no mapped correlation search or no recent notable fires, focusing detection engineering on true gaps in the Detect function.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), ES MITRE ATT&CK lookups
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `| inputlookup mitre_attack_all_techniques` (technique_id, technique_name); `| rest /services/saved/searches`; `| inputlookup mitre_user_rule_technique_lookup` (correlation_search_name, technique_id); `` `notable` `` macro (rule_name, annotations.mitre_attack.mitre_attack_id)
- **SPL:**
```spl
| inputlookup mitre_attack_all_techniques
| fields technique_id, technique_name
| join type=left max=0 technique_id [
    | rest /services/saved/searches splunk_server=local count=0
    | search disabled=0 title="*Correlation Search*"
    | lookup mitre_user_rule_technique_lookup correlation_search_name AS title OUTPUT technique_id
    | stats dc(title) as enabled_rules by technique_id
  ]
| join type=left max=0 technique_id [
    search `notable` earliest=-90d
    | mvexpand annotations.mitre_attack.mitre_attack_id limit=500
    | rename annotations.mitre_attack.mitre_attack_id as technique_id
    | stats dc(rule_name) as rules_with_fires by technique_id
  ]
| fillnull value=0 enabled_rules, rules_with_fires
| eval gap=case(
    enabled_rules=0, "no_mapped_rule",
    enabled_rules>0 AND rules_with_fires=0, "no_recent_notable",
    1=1, "active_signal")
| where gap!="active_signal"
| sort technique_id
| table technique_id, technique_name, enabled_rules, rules_with_fires, gap
```
- **Implementation:** (1) Confirm lookup names on your ES build (`mitre_attack_all_techniques` vs `mitre_attack_techniques`); (2) populate `mitre_user_rule_technique_lookup` (ES documents user mapping of correlation searches to techniques); (3) review quarterly and export gap list to detection engineering backlog.
- **Visualization:** Table (technique, rules, fires, gap), Column chart (gap counts by category).
- **CIM Models:** N/A

---

### 22.8 SOC 2

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.8.1 · SOC 2 Trust Services Criteria Continuous Control Monitoring (CC6-CC8)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** Continuous evidence for logical access (CC6), security monitoring and incident handling (CC7), and change management visibility (CC8) using CIM-normalized authentication data, ES notables, and Splunk audit telemetry.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742) or identity TAs feeding CIM, Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM `Authentication` data model (user, action, src, app); `` `notable` `` macro (status, urgency, owner, rule_name); `index=_audit` (object_type, action, user)
- **SPL:**
```spl
| tstats summariesonly=false count from datamodel=Authentication.Authentication
    where nodename=Authentication.Authentication
    by Authentication.action _time span=1h
| timechart span=1d sum(count) by Authentication.action
```
```spl
`notable`
| stats count by status, urgency, rule_name, owner
| eval cc7_open=if(status!="Closed", 1, 0)
```
```spl
index=_audit object_type IN ("savedsearch","lookup") action IN ("edit","create","delete","update")
| stats count by user, object_type, action
```
- **Implementation:** (1) Ensure identity data (AD, IdP, VPN) is CIM-tagged to `Authentication`; (2) train analysts to set `status`/`owner` on notables for CC7 closure evidence; (3) scope `_audit` to production SHC for CC8 change evidence; (4) map panels explicitly to CC6.1-CC6.7, CC7.2-CC7.5, CC8.1 in your control matrix.
- **Visualization:** Area chart (Authentication volume/denied ratio), Bar chart (cc7_open by urgency), Table (CC8 changes by user).
- **CIM Models:** Authentication

---

### UC-22.8.2 · SOC 2 System Availability and Incident Response Evidence Collection (A1)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Compliance
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** Pairs ITSI service health KPI time series with ES notable closure MTTR for availability plus incident-response effectiveness in one evidence trail.
- **App/TA:** Splunk IT Service Intelligence (Splunkbase 1841), Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI), Splunk Enterprise Security
- **Data Sources:** `index=itsi_summary` (service_name, alert_value, health_score, severity_value, is_service_in_maintenance, _time); `` `notable` `` macro (status, closed_time, rule_name, _time)
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0 is_entity_in_maintenance=0
| bin _time span=5m
| stats avg(health_score) as health_score, max(severity_value) as peak_severity by _time, service_name
| timechart span=1h avg(health_score) by service_name
```
```spl
`notable` status="Closed" isnotnull(closed_time)
| eval mttr_sec=closed_time-_time
| stats avg(mttr_sec) as avg_mttr, perc95(mttr_sec) as p95_mttr, count as closed_incidents by rule_name
| eval avg_mttr_hours=round(avg_mttr/3600, 2)
| table rule_name, closed_incidents, avg_mttr_hours, p95_mttr
```
- **Implementation:** (1) Model production services in ITSI with KPIs tied to SLIs; (2) keep `itsi_summary` retention aligned with audit window; (3) validate `closed_time` field on notables (`| fieldsummary closed_time`); (4) pair A1 uptime panels with incident MTTR for the same services via lookup; (5) document maintenance windows with `is_service_in_maintenance`.
- **Visualization:** Line chart (health_score by service), Bar chart (avg_mttr_hours by rule), Single value (peak_severity), Table (closed incidents).
- **CIM Models:** N/A

---

### UC-22.8.3 · SOC 2 Confidentiality Classification and DLP Event Audit (C1)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** Audits Microsoft 365 DLP policy matches with actor, policy, and sensitive information types for confidentiality control testing and breach-readiness reporting.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055)
- **Data Sources:** `index=o365` `sourcetype="ms:o365:management"` (Workload, PolicyName, UserPrincipalName, SensitiveInfoType, Severity, Operation)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInfoType, Severity, Operation
| sort - count
| table PolicyName, UserPrincipalName, SensitiveInfoType, Severity, count, Operation
```
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp"
| timechart span=1d count by Severity
```
- **Implementation:** (1) Enable Office 365 Management Activity inputs in TA 4055 and confirm `Workload="Dlp"` events are ingested; (2) map `SensitiveInfoType` values to your data classification scheme via lookup `classification_tier.csv`; (3) alert on high-severity or high-volume exfil patterns; (4) retain per legal hold requirements; (5) optionally route to ES as correlation-search input.
- **Visualization:** Bar chart (events by PolicyName), Heatmap (user x SensitiveInfoType), Line chart (daily volume by Severity), Table (sample evidence).
- **CIM Models:** N/A

---
