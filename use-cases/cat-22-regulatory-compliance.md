## 22. Regulatory and Compliance Frameworks

### 22.1 GDPR

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk Add-on for Stream (Splunkbase 1809), Splunk Add-on for Microsoft SQL Server (Splunkbase 2648), Splunk Add-on for Oracle Database (Splunkbase 1910), Splunk DB Connect (Splunkbase 2686), Splunk Edge Processor (Splunk Cloud Platform), Splunk Common Information Model Add-on (Splunkbase 1621).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities, Certificates, Change), database audit logs (`mssql:audit`, `oracle:audit`, `postgres:csv`), TLS/certificate metadata (Splunk Stream), consent management platform events (HEC), automated decision system audit logs (HEC), Splunk audit logs (`_audit`, `_internal`), GDPR register lookups (`gdpr_ropa_register.csv`, `gdpr_dpia_register.csv`, `gdpr_processor_register.csv`, `gdpr_lia_register.csv`).

---

### UC-22.1.1 · GDPR PII Detection in Application Log Data (Art. 5/6)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1005
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
- **MITRE ATT&CK:** T1048
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
- **MITRE ATT&CK:** T1005
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
- **MITRE ATT&CK:** T1048, T1530
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Highlights outbound traffic volumes to destinations outside the approved EEA/adequacy footprint so transfers can be gated by SCCs, BCRs, TIAs, or blocking controls.
- **App/TA:** Splunk Common Information Model Add-on (Splunkbase 1621), `Splunk_TA_paloalto` (Splunkbase 2757), `TA-fortinet_fortigate`, `Splunk_TA_cisco-asa`, or equivalent firewall TA populating Network_Traffic data model
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

### UC-22.1.7 · GDPR Security of Processing — Encryption and Pseudonymisation Coverage (Art. 32)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1005, T1562
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 32 requires controllers and processors to implement measures ensuring confidentiality, integrity, availability and resilience of processing systems — explicitly calling out pseudonymisation and encryption. This use case continuously monitors encryption-at-rest status for databases holding personal data, TLS enforcement on processing systems, and pseudonymisation coverage — providing the technical evidence that Art. 32 controls are operational, not just documented.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for Stream (Splunkbase 1809), Tenable Add-On for Splunk (Splunkbase 4060)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Certificates data model, `index=vulnerability` (crypto-related findings), `index=network` (TLS metadata), database audit logs
- **SPL:**
```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as ports, count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.app IN ("http","ftp","telnet","smtp") NOT All_Traffic.app IN ("https","ftps","smtps","ssh")
  by All_Traffic.dest All_Traffic.app
| rename All_Traffic.* as *
| lookup gdpr_personal_data_systems.csv dest OUTPUT system_name, data_category, contains_pii
| where contains_pii="true"
| sort - count
| table dest, system_name, data_category, app, count
```
- **Implementation:** (1) Create `gdpr_personal_data_systems.csv` listing all systems processing personal data (from Art. 30 register); (2) detect unencrypted protocols (HTTP, FTP, Telnet) to those systems; (3) monitor TLS certificate health for personal data endpoints; (4) track pseudonymisation implementation via application audit logs; (5) alert on any unencrypted connection to PII-bearing systems.
- **Visualization:** Table (PII systems with unencrypted connections), Pie chart (encrypted vs unencrypted traffic to PII systems), Bar chart (unencrypted protocols by system), Single value (% PII systems fully encrypted).
- **CIM Models:** Network_Traffic, Certificates

---

### UC-22.1.8 · GDPR Records of Processing Activities Completeness (Art. 30)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 30 requires controllers to maintain documented records of processing activities including purposes, data categories, recipients, transfers, retention periods, and technical measures. This use case validates that the processing register (ROPA) is complete and current by cross-referencing it against observed data flows and systems, surfacing systems that process personal data but are not in the register — a gap regulators frequently cite during inspections.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Common Information Model Add-on (Splunkbase 1621)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Network_Traffic and Authentication data models, `gdpr_ropa_register.csv` (processing activities register), ES Asset Framework
- **SPL:**
```spl
| tstats `summariesonly` dc(Authentication.user) as users, count
  from datamodel=Authentication.Authentication
  by Authentication.dest
| rename Authentication.dest as dest
| lookup gdpr_ropa_register.csv system_name AS dest OUTPUT processing_activity, data_category, legal_basis, retention_period, last_review_date
| eval in_register=if(isnotnull(processing_activity), "Yes", "NOT_IN_ROPA")
| eval review_overdue=if(isnotnull(last_review_date) AND (now()-strptime(last_review_date,"%Y-%m-%d"))/86400 > 365, "OVERDUE", "OK")
| where in_register="NOT_IN_ROPA" OR review_overdue="OVERDUE"
| sort - users
| table dest, users, count, in_register, processing_activity, legal_basis, review_overdue
```
- **Implementation:** (1) Maintain `gdpr_ropa_register.csv` from your DPO's Article 30 register (exported from OneTrust, DataGrail, or manual spreadsheet); (2) compare active systems receiving authentication events against registered systems; (3) alert on systems with user activity not in the ROPA; (4) flag entries with reviews older than 12 months; (5) schedule quarterly for ROPA completeness auditing.
- **Visualization:** Table (unregistered systems), Single value (ROPA coverage %), Bar chart (users by unregistered system), Timeline (review dates).
- **CIM Models:** Authentication

---

### UC-22.1.9 · GDPR Data Protection by Design — Data Minimisation Validation (Art. 25)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 25 requires data protection by design and by default — meaning only personal data necessary for each purpose should be collected. This use case detects systems collecting more personal data fields than their declared purpose requires (over-collection), identifies databases storing data categories beyond their ROPA scope, and monitors for new data collection endpoints appearing without DPIA coverage — catching data minimisation violations before regulators do.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Edge Processor (Splunk Cloud Platform)
- **Data Sources:** Application logs, API access logs, database audit logs, `gdpr_ropa_register.csv`
- **SPL:**
```spl
(index=app OR index=web OR index=api) earliest=-7d
| rex field=_raw "(?i)(?:email|e-mail)[\s=:\"]+(?<pii_email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
| rex field=_raw "(?i)(?:phone|mobile|tel)[\s=:\"]+(?<pii_phone>[\+]?\d[\d\s\-\(\)]{7,})"
| rex field=_raw "(?i)(?:dob|birth|born|birthday)[\s=:\"]+(?<pii_dob>\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})"
| rex field=_raw "(?i)(?:address|street|postcode|zip)[\s=:\"]+(?<pii_address>[^\",}{]{5,})"
| eval pii_fields_found=mvappend(
    if(isnotnull(pii_email),"email",null()),
    if(isnotnull(pii_phone),"phone",null()),
    if(isnotnull(pii_dob),"date_of_birth",null()),
    if(isnotnull(pii_address),"address",null()))
| where isnotnull(pii_fields_found)
| stats dc(mvjoin(pii_fields_found,",")) as pii_type_count, values(pii_fields_found) as pii_types, count by sourcetype, host
| lookup gdpr_ropa_register.csv system_name AS host OUTPUT data_category, processing_activity
| eval excess_collection=if(pii_type_count > 2 AND isnull(processing_activity), "POSSIBLE_OVER_COLLECTION", "Review")
| sort - pii_type_count
| table host, sourcetype, pii_types, pii_type_count, processing_activity, data_category, excess_collection
```
- **Implementation:** (1) Run weekly against application and API logs; (2) tune PII detection regex patterns for your data formats; (3) compare detected PII field types against declared ROPA data categories per system; (4) escalate systems collecting PII categories not in their declared purpose; (5) integrate with Edge Processor for ingest-time PII masking on confirmed over-collection sources.
- **Visualization:** Table (systems with excess PII collection), Bar chart (PII types by system), Heatmap (PII density across sourcetypes), Single value (systems flagged for review).
- **CIM Models:** N/A

---

### UC-22.1.10 · GDPR Privileged Access to Personal Data Stores (Art. 5(1)(f) / Art. 32)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1078, T1098
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Articles 5(1)(f) and 32 require integrity and confidentiality of personal data. Privileged access to databases and file stores containing personal data is the highest-risk vector for both accidental exposure and malicious exfiltration. This use case monitors DBA/admin access to personal data stores, detects bulk data exports, and identifies access outside approved change windows — providing the accountability evidence regulators expect.
- **App/TA:** Splunk Add-on for Microsoft SQL Server (Splunkbase 2648), Splunk Add-on for Oracle Database (Splunkbase 1910), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** Database audit logs (`sourcetype="mssql:audit"`, `sourcetype="oracle:audit"`, `sourcetype="postgres:csv"`), `index=dbaudit`
- **SPL:**
```spl
index=dbaudit sourcetype IN ("mssql:audit","oracle:audit","postgres:csv","mysql:audit") earliest=-24h
| eval user=coalesce(server_principal_name, os_username, user_name, db_user)
| eval action=lower(coalesce(action_id, action_name, statement_type, command_tag))
| eval is_bulk=if(match(action,"(?i)select.*into|bulk|export|dump|copy|backup") OR match(_raw,"(?i)rows_affected.*[5-9]\d{3}|rows_affected.*\d{5,}"), 1, 0)
| eval after_hours=if(tonumber(strftime(_time,"%H"))<7 OR tonumber(strftime(_time,"%H"))>19, 1, 0)
| lookup gdpr_personal_data_systems.csv dest AS database_name OUTPUT data_category, contains_pii
| where contains_pii="true" AND (is_bulk=1 OR after_hours=1 OR match(action,"(?i)grant|alter|drop|truncate|delete"))
| table _time, user, database_name, data_category, action, is_bulk, after_hours
| sort - _time
```
- **Implementation:** (1) Enable database audit logging on all systems in the ROPA that contain personal data; (2) forward audit logs via Splunk DB Connect or syslog; (3) create `gdpr_personal_data_systems.csv` with database names, data categories, and PII flags; (4) alert on bulk exports, DDL changes, and after-hours access to personal data stores; (5) require change tickets for planned administrative operations and correlate against change window lookups.
- **Visualization:** Table (privileged access events), Timeline (access patterns), Bar chart (actions by user), Single value (after-hours access count), Heatmap (user × hour).
- **CIM Models:** Change, Authentication

---

### UC-22.1.11 · GDPR Right to Erasure Verification (Art. 17)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 17 gives data subjects the right to erasure ("right to be forgotten"). While UC-22.1.2 tracks the DSAR ticket lifecycle, this use case verifies that erasure was actually executed across all systems by searching for residual data subject identifiers after the erasure deadline — catching incomplete deletions before they become regulatory violations.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` (completed erasure requests), all indexed data (post-erasure verification scan)
- **SPL:**
```spl
| inputlookup gdpr_completed_erasures.csv WHERE status="completed"
| eval erasure_date=strptime(completion_date, "%Y-%m-%d")
| eval days_since_erasure=round((now()-erasure_date)/86400, 0)
| where days_since_erasure >= 7 AND days_since_erasure <= 90
| map maxsearches=50 search="search index=* earliest=-90d \"$$subject_identifier$$\" | head 1 | eval subject_id=\"$$subject_identifier$$\", request_id=\"$$request_id$$\""
| where isnotnull(subject_id)
| table subject_id, request_id, index, sourcetype, host, _time
```
- **Implementation:** (1) Export completed erasure requests to `gdpr_completed_erasures.csv` with subject identifiers (hashed email, user ID, etc.) and completion dates; (2) run weekly to search for residual occurrences; (3) alert the DPO on any matches — these indicate incomplete erasure; (4) track remediation tickets for each residual finding; (5) exclude Splunk indexes with legitimate legal-hold retention from the scan and document the exception.
- **Visualization:** Table (residual data findings), Single value (incomplete erasures), Bar chart (residual data by system), Timeline (findings over time).
- **CIM Models:** N/A

---

### UC-22.1.12 · GDPR Breach Scope and Affected Data Subject Quantification (Art. 33(3))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048, T1005
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 33(3) requires breach notifications to include the categories and approximate number of affected data subjects. This use case automates breach scoping by correlating incident indicators (compromised hosts, accounts, or data stores) with the personal data register to estimate the number and categories of affected individuals — accelerating the breach assessment that must be completed within the 72-hour notification window.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, ES Asset Framework, `gdpr_ropa_register.csv`, CIM Authentication data model
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status!="Closed" earliest=-7d
| eval compromised_systems=mvappend(src, dest)
| mvexpand compromised_systems
| lookup gdpr_ropa_register.csv system_name AS compromised_systems OUTPUT data_category, processing_activity, estimated_data_subjects
| where isnotnull(data_category)
| stats sum(estimated_data_subjects) as total_affected_subjects, values(data_category) as data_categories, dc(compromised_systems) as systems_affected by rule_name, urgency
| eval notification_required=if(total_affected_subjects > 0, "LIKELY — Art. 33 notification to DPA", "Assess further")
| eval individual_notification=if(total_affected_subjects > 0 AND match(mvjoin(data_categories,","),"(?i)health|financial|special_category|biometric"), "LIKELY — Art. 34 notification to subjects", "Assess further")
| table rule_name, urgency, systems_affected, total_affected_subjects, data_categories, notification_required, individual_notification
```
- **Implementation:** (1) Add `estimated_data_subjects` field to `gdpr_ropa_register.csv` (approximate count of records/individuals per system); (2) tag ES notables that represent personal data breaches with relevant compromised hosts; (3) auto-calculate affected scope within minutes of breach detection; (4) use output to pre-populate Art. 33 notification forms; (5) flag incidents involving special category data (Art. 9) for Art. 34 direct notification to affected individuals.
- **Visualization:** Single value (estimated affected subjects), Table (breach scope by incident), Bar chart (data categories involved), Map (affected systems).
- **CIM Models:** N/A

---

### UC-22.1.13 · GDPR High-Risk Breach Communication to Data Subjects (Art. 34)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1048
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 34 requires controllers to communicate personal data breaches directly to affected data subjects "without undue delay" when the breach is likely to result in a high risk to their rights and freedoms. While Art. 33 covers DPA notification, Art. 34 addresses the often-overlooked obligation to notify individuals. This use case tracks whether high-risk breaches have triggered individual notification workflows and monitors their completion.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, `index=itsm` (notification workflow tickets), `gdpr_breach_notifications.csv` (KV store)
- **SPL:**
```spl
`notable` urgency="critical" earliest=-30d
| lookup gdpr_breach_notifications.csv notable_id AS event_id OUTPUT art33_notified, art34_required, art34_notified, art34_date, subjects_notified_count
| eval art34_status=case(
    art34_required="yes" AND art34_notified="yes", "COMPLETE",
    art34_required="yes" AND isnull(art34_notified), "PENDING — notify subjects",
    art34_required="no", "Not required",
    isnull(art34_required), "ASSESS — determine if Art.34 applies",
    1=1, "Unknown")
| where art34_status IN ("PENDING — notify subjects", "ASSESS — determine if Art.34 applies")
| table _time, rule_name, urgency, owner, art33_notified, art34_required, art34_status
| sort - _time
```
- **Implementation:** (1) Create `gdpr_breach_notifications.csv` KV store linking notable IDs to notification status; (2) when a breach involves special category data, financial data, or affects >1000 subjects, default `art34_required` to "yes"; (3) alert the DPO on pending Art. 34 notifications; (4) track notification method (email, letter, public notice) and completion dates; (5) document Art. 34(3) exceptions (encrypted data, mitigation applied, disproportionate effort requiring public communication).
- **Visualization:** Table (pending individual notifications), Single value (breaches requiring Art. 34 notification), Bar chart (notification status distribution), Timeline (notification lifecycle).
- **CIM Models:** N/A

---

### UC-22.1.14 · GDPR Data Protection Impact Assessment Coverage (Art. 35)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 35 requires a Data Protection Impact Assessment (DPIA) for processing likely to result in high risk — including systematic monitoring of public areas, large-scale processing of special categories, and automated decision-making with legal effects. This use case tracks DPIA completion against processing activities identified in the ROPA, flags high-risk processing without DPIA coverage, and monitors for new processing activities that may require a DPIA.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** `gdpr_ropa_register.csv`, `gdpr_dpia_register.csv` (DPIA records), ES Asset Framework
- **SPL:**
```spl
| inputlookup gdpr_ropa_register.csv
| eval high_risk=case(
    match(lower(processing_activity),"(?i)profil|automat|scoring|systematic.monitor|biometric|genetic|health|ethnic|political|religious|trade.union|criminal"), "HIGH_RISK",
    match(lower(data_category),"(?i)special_category|sensitive|health|biometric|genetic"), "HIGH_RISK",
    match(lower(scale),"(?i)large"), "HIGH_RISK",
    1=1, "Standard")
| where high_risk="HIGH_RISK"
| lookup gdpr_dpia_register.csv processing_activity OUTPUT dpia_status, dpia_date, dpia_reviewer, residual_risk
| eval dpia_coverage=case(
    dpia_status="completed", "COVERED",
    dpia_status="in_progress", "IN_PROGRESS",
    isnull(dpia_status), "MISSING — DPIA REQUIRED")
| eval review_overdue=if(isnotnull(dpia_date) AND (now()-strptime(dpia_date,"%Y-%m-%d"))/86400 > 730, "REVIEW_DUE", "OK")
| where dpia_coverage="MISSING — DPIA REQUIRED" OR review_overdue="REVIEW_DUE"
| table processing_activity, system_name, data_category, high_risk, dpia_coverage, dpia_date, review_overdue
| sort dpia_coverage
```
- **Implementation:** (1) Maintain `gdpr_dpia_register.csv` with DPIA records linked to ROPA processing activities; (2) auto-classify high-risk processing using Art. 35(3) criteria and DPA guidance lists; (3) alert the DPO on processing activities lacking DPIA coverage; (4) flag DPIAs not reviewed in >2 years; (5) when new systems appear in authentication logs without ROPA entries (UC-22.1.8), flag them for DPIA assessment.
- **Visualization:** Table (DPIA coverage gaps), Pie chart (covered vs missing vs in-progress), Single value (missing DPIAs count), Bar chart (high-risk processing by category).
- **CIM Models:** N/A

---

### UC-22.1.15 · GDPR Third-Party Processor Compliance Monitoring (Art. 28)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 28 requires controllers to use only processors providing sufficient guarantees and to monitor their compliance. This use case tracks data flows to processors, monitors their security posture indicators, detects data transfers exceeding agreed scope, and flags processors with overdue security assessments — providing continuous evidence that processor oversight is active, not just contractual.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Common Information Model Add-on (Splunkbase 1621)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Network_Traffic data model, proxy/firewall logs, `gdpr_processor_register.csv`
- **SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as sources
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="allowed"
  by All_Traffic.dest
| rename All_Traffic.* as *
| lookup gdpr_processor_register.csv dest_domain AS dest OUTPUT processor_name, dpa_signed, last_audit_date, approved_data_categories, sub_processors
| where isnotnull(processor_name)
| eval days_since_audit=if(isnotnull(last_audit_date), round((now()-strptime(last_audit_date,"%Y-%m-%d"))/86400,0), 9999)
| eval audit_status=case(days_since_audit > 365, "OVERDUE", days_since_audit > 270, "DUE_SOON", 1=1, "CURRENT")
| eval bytes_gb=round(bytes_out/1073741824, 2)
| sort - bytes_gb
| table dest, processor_name, dpa_signed, bytes_gb, sources, audit_status, days_since_audit, sub_processors
```
- **Implementation:** (1) Build `gdpr_processor_register.csv` from your Art. 28 processor inventory with destination domains/IPs, DPA status, and audit dates; (2) monitor actual data transfer volumes to each processor; (3) alert on processors with overdue audits or unsigned DPAs; (4) detect unexpected volume spikes indicating scope creep; (5) track sub-processor changes reported by primary processors.
- **Visualization:** Table (processor compliance status), Bar chart (data transfer by processor), Single value (overdue audits count), Timeline (transfer volume trends).
- **CIM Models:** Network_Traffic

---

### UC-22.1.16 · GDPR Consent Withdrawal Processing Enforcement (Art. 7(3))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 7(3) requires that withdrawal of consent be as easy as giving consent, and processing based on consent must stop after withdrawal. While UC-22.1.5 tracks the consent audit trail, this use case verifies that processing actually ceases after a data subject withdraws consent — detecting systems that continue sending marketing communications, tracking cookies, or processing data for purposes that relied on the withdrawn consent.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), HTTP Event Collector (HEC)
- **Data Sources:** `index=consent` (consent management platform events), `index=email` (marketing automation logs), `index=web` (tracking/analytics events), application audit logs
- **SPL:**
```spl
| inputlookup gdpr_consent_withdrawals.csv WHERE withdrawal_date!=""
| eval withdrawal_epoch=strptime(withdrawal_date, "%Y-%m-%d")
| eval subject_hash=subject_identifier
| join type=left subject_hash [
    search (index=email OR index=marketing) earliest=-30d
    | eval subject_hash=coalesce(recipient_hash, subscriber_id, user_hash)
    | where isnotnull(subject_hash)
    | stats count as post_withdrawal_events, latest(_time) as last_processing_time by subject_hash
]
| where isnotnull(post_withdrawal_events) AND last_processing_time > withdrawal_epoch
| eval days_processing_after_withdrawal=round((last_processing_time - withdrawal_epoch)/86400, 1)
| sort - days_processing_after_withdrawal
| table subject_hash, withdrawal_date, consent_purpose, post_withdrawal_events, days_processing_after_withdrawal
```
- **Implementation:** (1) Export consent withdrawal events from your CMP (OneTrust, Cookiebot, custom) to `gdpr_consent_withdrawals.csv` with hashed subject identifiers and consent purposes; (2) search marketing automation and tracking systems for activity after withdrawal dates; (3) alert on any processing found after withdrawal; (4) escalate to marketing operations for immediate suppression; (5) document remediation for accountability evidence.
- **Visualization:** Table (subjects with post-withdrawal processing), Single value (violations found), Bar chart (violations by consent purpose), Timeline (violation discovery).
- **CIM Models:** N/A

---

### UC-22.1.17 · GDPR Audit Log Integrity and Tamper Protection (Art. 5(2))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1070, T1562
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 5(2) requires controllers to demonstrate compliance (accountability principle). Audit logs are the primary evidence mechanism, but logs that can be tampered with have no evidentiary value. This use case monitors Splunk's internal audit trail for suspicious activities — index deletions, user-capability changes, search-time data manipulation, and modifications to retention settings — ensuring the integrity of the very evidence used to prove GDPR compliance.
- **App/TA:** Splunk Enterprise / Splunk Cloud Platform (native audit capabilities)
- **Data Sources:** `index=_audit` (Splunk audit logs), `index=_internal` (Splunk internal logs)
- **SPL:**
```spl
index=_audit earliest=-24h
| where match(action,"(?i)delete|edit_user|change_own_password|edit_roles|search")
  AND (match(info,"(?i)index.*delete|frozen|retire|capabilities|admin")
       OR match(action,"(?i)delete_index_data|edit_index"))
| eval risk_signal=case(
    match(action,"(?i)delete_index_data"), "INDEX_DATA_DELETION",
    match(info,"(?i)capabilities.*admin|role.*admin"), "PRIVILEGE_ESCALATION",
    match(info,"(?i)frozen|retire|retention"), "RETENTION_CHANGE",
    1=1, "AUDIT_MODIFICATION")
| stats count by user, action, risk_signal, info
| sort - count
| table _time, user, action, risk_signal, info, count
```
- **Implementation:** (1) Enable Splunk audit logging (enabled by default); (2) forward `_audit` events to a separate, restricted index with extended retention; (3) alert on index data deletions, retention setting changes, and admin privilege modifications; (4) restrict `_audit` index access to compliance/security teams only; (5) consider Splunk Cloud's immutable audit trail as the source of truth for regulatory evidence.
- **Visualization:** Table (suspicious audit events), Timeline (audit modifications), Bar chart (events by risk signal), Single value (high-risk events today).
- **CIM Models:** Change

---

### UC-22.1.18 · GDPR Automated Decision-Making and Profiling Transparency (Art. 22)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1565, T1005
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 22 gives data subjects the right not to be subject to decisions based solely on automated processing that produce legal or similarly significant effects. This use case monitors automated decision-making systems (credit scoring, fraud detection, HR screening, insurance pricing) for transparency — tracking decision volumes, override rates, and appeal/challenge requests to ensure human review is available and exercised.
- **App/TA:** HTTP Event Collector (HEC — structured decision logs)
- **Data Sources:** `index=decisions` (automated decision system audit logs via HEC), `index=itsm` (appeal/challenge tickets)
- **SPL:**
```spl
index=decisions sourcetype="automated_decision" earliest=-30d
| eval decision_type=coalesce(decision_type, model_name, system_name)
| eval human_reviewed=if(match(lower(_raw),"(?i)manual.*review|human.*override|appeal.*granted|escalat"), 1, 0)
| eval adverse=if(match(lower(outcome),"(?i)denied|rejected|declined|flagged|high.risk"), 1, 0)
| stats count as total_decisions, sum(adverse) as adverse_decisions, sum(human_reviewed) as reviewed_by_human by decision_type
| eval adverse_pct=round(100*adverse_decisions/total_decisions, 1)
| eval human_review_pct=round(100*reviewed_by_human/total_decisions, 1)
| eval compliance_risk=if(adverse_pct > 10 AND human_review_pct < 5, "HIGH — low human review of adverse decisions", "Monitor")
| table decision_type, total_decisions, adverse_decisions, adverse_pct, reviewed_by_human, human_review_pct, compliance_risk
```
- **Implementation:** (1) Instrument automated decision systems to emit structured audit logs via HEC with decision type, outcome, data inputs used, and human review flags; (2) track Art. 22(3) challenge/appeal requests through ITSM; (3) alert when adverse decision rates are high but human review rates are low; (4) report on decision transparency for DPO annual review; (5) ensure data subjects are informed about automated decision-making per Art. 13(2)(f) and Art. 14(2)(g).
- **Visualization:** Bar chart (decisions by type and outcome), Table (low human review systems), Single value (overall human review rate), Line chart (adverse decision trends).
- **CIM Models:** N/A

---

### UC-22.1.19 · GDPR Data Subject Rights Response SLA Dashboard (Art. 12)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Article 12 requires controllers to respond to data subject rights requests "without undue delay and in any event within one month," extendable by two months for complex requests with explanation to the data subject. While UC-22.1.2 focuses on DSARs specifically, this use case provides an executive dashboard across all rights (access, rectification, erasure, restriction, portability, objection) with SLA tracking, volume trends, and cost-per-request metrics — the compliance KPI view that DPOs and boards need.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (all data subject rights requests)
- **SPL:**
```spl
index=itsm (sourcetype="snow:sc_req_item" OR sourcetype="snow:incident")
    (cat_item="*Subject*" OR short_description="*DSAR*" OR short_description="*data subject*" OR short_description="*erasure*" OR short_description="*rectification*" OR short_description="*portability*" OR short_description="*objection*" OR short_description="*restriction*")
| eval right_type=case(
    match(lower(short_description),"(?i)access|dsar|subject.access"), "Access (Art.15)",
    match(lower(short_description),"(?i)erasure|forget|deletion"), "Erasure (Art.17)",
    match(lower(short_description),"(?i)rectif"), "Rectification (Art.16)",
    match(lower(short_description),"(?i)portab"), "Portability (Art.20)",
    match(lower(short_description),"(?i)object"), "Objection (Art.21)",
    match(lower(short_description),"(?i)restrict"), "Restriction (Art.18)",
    1=1, "Other")
| eval opened_epoch=strptime(opened_at,"%Y-%m-%d %H:%M:%S")
| eval closed_epoch=if(isnotnull(closed_at), strptime(closed_at,"%Y-%m-%d %H:%M:%S"), null())
| eval response_days=if(isnotnull(closed_epoch), round((closed_epoch-opened_epoch)/86400,1), round((now()-opened_epoch)/86400,1))
| eval sla_status=case(
    isnotnull(closed_epoch) AND response_days<=30, "Met",
    isnotnull(closed_epoch) AND response_days<=90, "Extended (Art.12(3))",
    isnotnull(closed_epoch) AND response_days>90, "BREACHED",
    isnull(closed_epoch) AND response_days>25, "AT_RISK",
    1=1, "In Progress")
| stats count by right_type, sla_status
| chart sum(count) by right_type, sla_status
```
- **Implementation:** (1) Standardise ServiceNow catalog items or incident categories for each GDPR right type; (2) train intake teams to classify correctly; (3) schedule daily; (4) alert on AT_RISK requests approaching 30-day deadline; (5) report monthly on volume trends, SLA compliance rates, and average response times by right type.
- **Visualization:** Stacked bar chart (rights by SLA status), Single value (overall SLA compliance %), Table (at-risk requests), Line chart (monthly volume trend by right type), Pie chart (requests by right type).
- **CIM Models:** N/A

---

### UC-22.1.20 · GDPR Legitimate Interest Balancing Test Evidence (Art. 6(1)(f))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** GDPR
- **Value:** Legitimate interest (Art. 6(1)(f)) is the most commonly misused legal basis — regulators have fined LinkedIn €310M and others hundreds of millions for relying on legitimate interest without proper balancing tests. This use case tracks which processing activities use legitimate interest as their legal basis, monitors whether balancing test documentation exists and is current, and detects processing scope creep beyond the original legitimate interest assessment — addressing the enforcement area that generates the highest fines in 2025-2026.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** `gdpr_ropa_register.csv`, `gdpr_lia_register.csv` (Legitimate Interest Assessments), CIM Network_Traffic data model
- **SPL:**
```spl
| inputlookup gdpr_ropa_register.csv WHERE legal_basis="legitimate_interest"
| lookup gdpr_lia_register.csv processing_activity OUTPUT lia_status, lia_date, lia_reviewer, lia_outcome, data_subject_objections
| eval lia_coverage=case(
    lia_status="completed" AND lia_outcome="justified", "JUSTIFIED",
    lia_status="completed" AND lia_outcome="not_justified", "STOP_PROCESSING",
    lia_status="in_progress", "IN_PROGRESS",
    isnull(lia_status), "MISSING — LIA REQUIRED")
| eval review_overdue=if(isnotnull(lia_date) AND (now()-strptime(lia_date,"%Y-%m-%d"))/86400 > 365, "REVIEW_DUE", "OK")
| eval objection_rate=if(isnotnull(data_subject_objections) AND data_subject_objections > 10, "HIGH_OBJECTIONS — reassess", "Normal")
| where lia_coverage IN ("MISSING — LIA REQUIRED", "STOP_PROCESSING") OR review_overdue="REVIEW_DUE" OR objection_rate="HIGH_OBJECTIONS — reassess"
| table processing_activity, system_name, lia_coverage, lia_date, review_overdue, data_subject_objections, objection_rate
| sort lia_coverage
```
- **Implementation:** (1) Tag ROPA entries using legitimate interest as legal basis; (2) maintain `gdpr_lia_register.csv` linking processing activities to Legitimate Interest Assessments; (3) alert on processing activities relying on legitimate interest without a completed LIA; (4) track data subject objections (Art. 21) per processing activity — high objection rates signal the balancing test may be failing; (5) flag LIAs not reviewed in >12 months; (6) stop processing immediately for any activity where LIA concludes "not justified."
- **Visualization:** Table (LIA coverage gaps), Pie chart (LIA status distribution), Bar chart (objections by processing activity), Single value (missing LIAs count).
- **CIM Models:** N/A

---

### 22.2 NIS2

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk Add-on for Okta Identity Cloud (Splunkbase 6056), Splunk Add-on for Stream (Splunkbase 1809), Splunk Add-on for CyberArk (Splunkbase 2891), Splunk Add-on for Qualys (Splunkbase 2964), Splunk Add-on for Veeam (Splunkbase 7173), Splunk Add-on for GitHub (Splunkbase 5596), Splunk Add-on for Jira (Splunkbase 1438).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), Azure AD sign-ins (`ms:aad:signin`), Okta system logs (`OktaIM2:log`), CIM data models (Authentication, Network_Traffic, Vulnerabilities, Certificates, Risk), TLS/certificate metadata (Splunk Stream), backup software logs (Veeam, Commvault, Rubrik, AWS Backup), CI/CD pipeline events (GitHub Actions, GitLab CI, Jenkins), LMS training exports (CSV/HEC), PAM session logs (`cyberark:session`), Splunk audit logs (`_audit`, `_internal`).

---

### UC-22.2.1 · NIS2 Incident Detection and 24-Hour Early Warning Reporting (Art. 23)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048, T1562
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
- **MITRE ATT&CK:** T1078, T1048
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
- **MITRE ATT&CK:** T1562
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
- **MITRE ATT&CK:** T1078, T1098
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

### UC-22.2.6 · NIS2 Risk Analysis and Information System Security Policy Evidence (Art. 21(2)(a))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(a) requires documented risk analysis and information security policies. This use case continuously validates that organisational risk posture is tracked, risk treatments are assigned owners, and security policy coverage aligns with critical asset inventory — producing auditable evidence that risk management is an operational process, not a one-time exercise.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Common Information Model Add-on (Splunkbase 1621)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=risk` `sourcetype="stash"` (risk_object, risk_object_type, risk_score, source), asset/identity lookups, `_audit` index
- **SPL:**
```spl
index=risk sourcetype="stash" earliest=-30d@d
| stats latest(risk_score) as current_risk, max(risk_score) as peak_risk, dc(source) as contributing_detections by risk_object, risk_object_type
| lookup asset_lookup_by_str key AS risk_object OUTPUT category, priority, owner
| fillnull value="UNASSIGNED" owner category
| where owner="UNASSIGNED" OR current_risk > 50
| sort - current_risk
| table risk_object, risk_object_type, category, owner, current_risk, peak_risk, contributing_detections
```
- **Implementation:** (1) Populate ES asset and identity frameworks with NIS2-scoped systems; (2) ensure risk-generating correlation searches are active for all critical asset categories; (3) flag `UNASSIGNED` owners as governance gaps requiring remediation; (4) schedule weekly to generate evidence of continuous risk monitoring; (5) export as PDF for audit evidence pack.
- **Visualization:** Table (risk objects without owners), Bar chart (risk by category), Single value (unassigned assets), Line chart (risk trend over 30 days).
- **CIM Models:** Risk

---

### UC-22.2.7 · NIS2 72-Hour Incident Notification Readiness (Art. 23(2))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048, T1562
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** After the 24-hour early warning (UC-22.2.1), Article 23(2) requires a more detailed incident notification within 72 hours containing initial severity assessment, impact analysis, and indicators of compromise. This use case tracks whether significant incidents have the required enrichment fields populated within the filing window, ensuring the 72-hour notification is substantive rather than a rehash of the early warning.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro (urgency, severity, status, owner, status_description, _time, src, dest, signature)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") earliest=-7d
| eval hours_elapsed=round((now()-_time)/3600, 2)
| eval has_ioc=if(isnotnull(src) AND isnotnull(dest) AND isnotnull(signature), 1, 0)
| eval has_severity_assessment=if(isnotnull(status_description) AND len(status_description)>20, 1, 0)
| eval filing_72h_breach=if(hours_elapsed>72 AND status!="Closed" AND (has_ioc=0 OR has_severity_assessment=0), 1, 0)
| eval approaching_72h=if(hours_elapsed>=48 AND hours_elapsed<72 AND (has_ioc=0 OR has_severity_assessment=0), 1, 0)
| where filing_72h_breach=1 OR approaching_72h=1
| table _time, rule_name, urgency, status, owner, hours_elapsed, has_ioc, has_severity_assessment, filing_72h_breach, approaching_72h
| sort - filing_72h_breach, - hours_elapsed
```
- **Implementation:** (1) Define mandatory enrichment fields for NIS2-classified incidents (IOCs, severity assessment narrative, impact scope); (2) alert at 48h for incidents missing required fields; (3) integrate with SOAR to auto-populate IOCs from investigation; (4) export completed notifications as structured reports matching CSIRT templates.
- **Visualization:** Table (incidents approaching/breaching 72h), Single value (count missing IOCs), Timeline (enrichment progress).
- **CIM Models:** N/A

---

### UC-22.2.8 · NIS2 One-Month Final Incident Report Tracking (Art. 23(4))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 23(4) requires a comprehensive final report within one month of the incident notification, containing root cause analysis, detailed description, mitigation measures applied, and cross-border impact assessment. This use case tracks whether closed significant incidents have completed post-incident reviews within the mandated timeframe.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, `index=itsm` `sourcetype="snow:incident"` (PIR/RCA records)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status="Closed" earliest=-60d
| eval days_since_close=round((now()-_time)/86400, 1)
| eval final_report_due=if(days_since_close>=30, 1, 0)
| eval final_report_approaching=if(days_since_close>=21 AND days_since_close<30, 1, 0)
| lookup pir_completion_lookup notable_id AS event_id OUTPUT pir_status, pir_date, root_cause_documented
| fillnull value="NOT_SUBMITTED" pir_status
| where (final_report_due=1 AND pir_status!="Complete") OR final_report_approaching=1
| table _time, rule_name, urgency, owner, days_since_close, pir_status, root_cause_documented, final_report_due
| sort - final_report_due, - days_since_close
```
- **Implementation:** (1) Create `pir_completion_lookup` linking notable IDs to post-incident review (PIR) records from ServiceNow or Confluence; (2) alert at 21 days for incidents without started PIRs; (3) escalate at 30 days for overdue final reports; (4) require root cause analysis, timeline, mitigation actions, and cross-border assessment fields before marking PIR as complete.
- **Visualization:** Table (overdue final reports), Single value (PIRs due this week), Bar chart (PIR status distribution), Timeline (incident-to-PIR lifecycle).
- **CIM Models:** N/A

---

### UC-22.2.9 · NIS2 Effectiveness Assessment of Cybersecurity Measures (Art. 21(2)(f))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(f) requires policies and procedures to assess the effectiveness of cybersecurity risk-management measures. This use case creates a KPI dashboard tracking operational evidence across all NIS2 control areas — MFA coverage, patch SLA compliance, backup restore success, training completion, and detection efficacy — providing continuous proof that controls work rather than just exist.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Tenable Add-On for Splunk (Splunkbase 4060)
- **Premium Apps:** Splunk Enterprise Security, Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=risk`, `index=vulnerability`, `index=itsi_summary`, `_audit`, `_internal`, CIM data models
- **SPL:**
```spl
| makeresults
| eval measure="MFA_Coverage"
| append [
    search index=_internal sourcetype=splunk_web_access earliest=-24h
    | stats dc(user) as total_users dc(eval(if(match(_raw,"(?i)mfa|2fa|totp"),user,null()))) as mfa_users
    | eval measure="MFA_Coverage", pct=round(100*mfa_users/total_users,1), target=95
]
| append [
    search index=vulnerability sourcetype="tenable:vuln" state="Active" earliest=-30d
    | eval sla_days=case(severity="Critical",7, severity="High",30, 1=1,90)
    | eval age_days=round((now()-first_found)/86400,1)
    | eval in_sla=if(age_days<=sla_days,1,0)
    | stats avg(in_sla) as pct_raw
    | eval measure="Patch_SLA_Compliance", pct=round(pct_raw*100,1), target=90
]
| append [
    search index=itsi_summary is_service_in_maintenance=0 earliest=-7d
    | stats avg(eval(if(health_score>=70,1,0))) as pct_raw by service_name
    | stats avg(pct_raw) as pct_raw
    | eval measure="Service_Availability", pct=round(pct_raw*100,1), target=99
]
| where isnotnull(pct)
| eval status=if(pct>=target,"PASS","FAIL")
| table measure, pct, target, status
```
- **Implementation:** (1) Define target KPIs for each NIS2 Article 21 measure area; (2) populate data sources (vulnerability scanner, identity provider MFA reports, ITSI services, training LMS exports); (3) schedule monthly for board/audit reporting; (4) add pen test and tabletop exercise results as manual KV store entries; (5) trend quarter-over-quarter to demonstrate improvement.
- **Visualization:** KPI tiles (pass/fail per measure), Gauge charts (% vs target), Table (failing measures), Line chart (effectiveness trend).
- **CIM Models:** Risk, Vulnerabilities

---

### UC-22.2.10 · NIS2 Cyber Hygiene and Training Compliance (Art. 21(2)(g))
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(g) requires basic cyber hygiene practices and cybersecurity training for all staff. This use case tracks training completion rates, identifies overdue personnel, and correlates training gaps with security incident involvement — proving that awareness is delivered, measured, and effective.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), CSV lookup (LMS export)
- **Data Sources:** `index=training` (LMS completion records via CSV/HEC), `index=email` `sourcetype="ms:o365:management"` (phishing simulation results), `` `notable` `` macro
- **SPL:**
```spl
| inputlookup nis2_training_completion.csv
| eval days_since_training=round((now()-strptime(completion_date,"%Y-%m-%d"))/86400, 0)
| eval overdue=if(days_since_training > 365 OR isnull(completion_date), 1, 0)
| stats count as total_staff, sum(overdue) as overdue_count, avg(days_since_training) as avg_days_since
| eval compliance_pct=round(100*(total_staff-overdue_count)/total_staff, 1)
| table total_staff, overdue_count, compliance_pct, avg_days_since
```
- **Implementation:** (1) Export LMS completion data to `nis2_training_completion.csv` via scheduled script or HEC; (2) include all NIS2-scope employees (not just IT); (3) alert when compliance drops below 90%; (4) correlate training-overdue users with notable events to demonstrate risk-based prioritisation; (5) track phishing simulation click rates as effectiveness evidence.
- **Visualization:** Single value (compliance %), Bar chart (completion by department), Table (overdue staff), Line chart (compliance trend quarterly).
- **CIM Models:** N/A

---

### UC-22.2.11 · NIS2 Cryptography and Encryption Policy Monitoring (Art. 21(2)(h))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1562, T1005
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(h) requires policies and procedures for cryptography and encryption. This use case monitors TLS certificate health, identifies weak cipher usage, detects unencrypted protocols on NIS2-scoped networks, and tracks encryption-at-rest status — providing continuous evidence that cryptographic controls are operational and current.
- **App/TA:** Splunk Add-on for Stream (Splunkbase 1809), Splunk Enterprise Security (Splunkbase 263), Tenable Add-On for Splunk (Splunkbase 4060)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Certificate data model, `index=network` (TLS metadata), `index=vulnerability` (crypto-related findings)
- **SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Certificates.All_Certificates
  where All_Certificates.ssl_end_time < relative_time(now(), "+30d")
  by All_Certificates.ssl_subject_common_name All_Certificates.ssl_end_time All_Certificates.ssl_issuer_common_name
| rename All_Certificates.* as *
| eval days_until_expiry=round((ssl_end_time - now())/86400, 0)
| eval status=case(days_until_expiry < 0, "EXPIRED", days_until_expiry < 14, "CRITICAL", days_until_expiry < 30, "WARNING")
| sort days_until_expiry
| table ssl_subject_common_name, ssl_issuer_common_name, days_until_expiry, status
```
- **Implementation:** (1) Ingest TLS handshake metadata from Splunk Stream or proxy logs; (2) monitor for deprecated protocols (TLS 1.0/1.1, SSLv3) and weak ciphers (RC4, DES, 3DES, export ciphers); (3) track certificate expiry for NIS2-scoped services; (4) correlate vulnerability scanner findings for crypto weaknesses; (5) report encryption-at-rest coverage for databases and file stores.
- **Visualization:** Table (expiring/expired certificates), Pie chart (TLS version distribution), Bar chart (weak ciphers by host), Single value (% services using TLS 1.2+).
- **CIM Models:** Certificates

---

### UC-22.2.12 · NIS2 Multi-Factor Authentication and Secure Communications (Art. 21(2)(j))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1078, T1556
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(j) requires MFA or continuous authentication, secured voice/video/text communications, and emergency communication systems. This use case monitors MFA enforcement across critical systems, detects authentication bypasses, and validates that administrative and emergency access channels are secured — providing evidence of the strongest authentication controls NIS2 mandates.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk Add-on for Okta Identity Cloud (Splunkbase 6056)
- **Data Sources:** `index=auth` (IdP authentication logs), `index=azure` `sourcetype="ms:aad:signin"` (Azure AD sign-ins), `index=okta` `sourcetype="OktaIM2:log"` (Okta system logs)
- **SPL:**
```spl
index=auth OR index=azure OR index=okta earliest=-24h
  sourcetype IN ("ms:aad:signin","OktaIM2:log","linux:auth","WinEventLog:Security")
| eval user=coalesce(userPrincipalName, actor.alternateId, Account_Name, user)
| eval mfa_used=case(
    match(lower(_raw),"(?i)mfa|multifactor|two.?factor|2fa|totp|fido|webauthn|push.*approve"), 1,
    match(lower(authenticationRequirement),"(?i)multi"), 1,
    match(lower(factor),"(?i)push|totp|sms|call|webauthn"), 1,
    1=1, 0)
| eval is_admin=if(match(lower(user),"(?i)admin|svc-|service|root|system") OR match(lower(_raw),"(?i)privileged|admin.*role"), 1, 0)
| stats count sum(mfa_used) as mfa_count by user, is_admin, sourcetype
| eval mfa_pct=round(100*mfa_count/count, 1)
| where (is_admin=1 AND mfa_pct < 100) OR (is_admin=0 AND mfa_pct < 80)
| sort is_admin, mfa_pct
| table user, is_admin, count, mfa_count, mfa_pct, sourcetype
```
- **Implementation:** (1) Ingest IdP authentication logs (Azure AD, Okta, or on-prem AD with ADFS); (2) require 100% MFA for administrative access and 80%+ for general users; (3) alert on admin authentications without MFA; (4) track break-glass account usage separately; (5) validate secure communications by checking Teams/Webex/Signal usage for emergency channels; (6) document emergency communication drill results in a KV store for audit evidence.
- **Visualization:** Single value (MFA coverage %), Table (users without MFA), Bar chart (MFA by authentication type), Gauge (admin MFA compliance).
- **CIM Models:** Authentication

---

### UC-22.2.13 · NIS2 Asset Management and Configuration Baseline (Art. 21(2)(i))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(i) includes asset management alongside access control and HR security. This use case validates that the ES asset framework is populated and current for NIS2-scoped systems, detects unknown or unmanaged assets communicating on critical networks, and tracks configuration baseline drift — ensuring the asset inventory that underpins all other NIS2 controls is reliable.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for Qualys (Splunkbase 2964)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** ES Asset Framework (`asset_lookup_by_str`, `asset_lookup_by_cidr`), CIM Network_Traffic data model, `index=vulnerability` (asset discovery scans)
- **SPL:**
```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as ports, sum(All_Traffic.bytes) as total_bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src
| rename All_Traffic.src as src
| lookup asset_lookup_by_str key AS src OUTPUT category, priority, owner, nt_host
| where isnull(category) OR category="unknown"
| sort - total_bytes
| head 100
| table src, nt_host, category, owner, ports, total_bytes
```
- **Implementation:** (1) Populate ES asset framework from CMDB, vulnerability scanners, and network discovery tools; (2) schedule this search daily to find active IPs not in the asset inventory; (3) classify discovered assets by NIS2 criticality (essential service vs supporting); (4) alert on high-traffic unknown assets; (5) track asset inventory completeness as a NIS2 KPI in UC-22.2.9 effectiveness dashboard.
- **Visualization:** Table (unknown active assets), Single value (% assets classified), Bar chart (assets by category), Map (asset locations if geo data available).
- **CIM Models:** Network_Traffic

---

### UC-22.2.14 · NIS2 Human Resources Security — Joiner/Mover/Leaver Process (Art. 21(2)(i))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1078, T1098
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(i) requires human resources security controls including lifecycle-managed access. This use case detects accounts that remain active after employee departure, identifies access rights that persist after role changes, and monitors onboarding completeness — providing evidence that joiner/mover/leaver (JML) processes are enforced and auditable.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Security"` (account disable/delete events), `index=itsm` (ServiceNow HR case records), HR system exports (CSV/HEC), `index=auth` (authentication after termination)
- **SPL:**
```spl
| inputlookup terminated_employees.csv
| eval term_date=strptime(termination_date, "%Y-%m-%d")
| eval days_since_term=round((now()-term_date)/86400, 0)
| join type=left user [
    search index=auth OR index=windows OR index=azure earliest=-30d
    | eval user=coalesce(Account_Name, userPrincipalName, user)
    | stats latest(_time) as last_auth count as auth_count by user
]
| where isnotnull(last_auth) AND last_auth > term_date
| eval days_active_after_term=round((last_auth - term_date)/86400, 0)
| sort - days_active_after_term
| table user, termination_date, days_since_term, days_active_after_term, auth_count
```
- **Implementation:** (1) Export HR termination data to `terminated_employees.csv` via scheduled integration or HEC; (2) run daily to detect orphaned accounts; (3) alert on any authentication activity after termination date; (4) escalate accounts active >3 days post-termination as potential compliance violations; (5) extend to movers by comparing current role vs granted access groups; (6) integrate with ServiceNow for automated deprovisioning ticket creation.
- **Visualization:** Table (active terminated accounts), Single value (orphaned accounts count), Bar chart (days active after termination), Timeline (post-termination activity).
- **CIM Models:** Authentication

---

### UC-22.2.15 · NIS2 Secure System Acquisition and Development Lifecycle (Art. 21(2)(e))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(e) extends beyond vulnerability management to require security in system acquisition, development, and maintenance lifecycles. This use case monitors CI/CD pipeline security gates, tracks code scanning results, and validates that change management processes include security review — demonstrating that security is embedded in the development lifecycle rather than bolted on after deployment.
- **App/TA:** Splunk Add-on for GitHub (Splunkbase 5596), Splunk Add-on for Jira (Splunkbase 1438)
- **Data Sources:** `index=devops` (CI/CD pipeline events from GitHub Actions, GitLab CI, Jenkins), `index=codescan` (SAST/SCA scan results), `index=itsm` (change management records)
- **SPL:**
```spl
index=devops sourcetype IN ("github:webhook","gitlab:pipeline","jenkins:build") earliest=-30d
| eval has_security_scan=if(match(lower(_raw),"(?i)sast|sca|snyk|sonar|trivy|semgrep|security.scan|code.scan"), 1, 0)
| eval deployment=if(match(lower(_raw),"(?i)deploy|release|prod|production"), 1, 0)
| stats count as total_builds, sum(has_security_scan) as scanned_builds, sum(deployment) as deployments by repository
| eval scan_coverage=round(100*scanned_builds/total_builds, 1)
| where scan_coverage < 80 OR (deployments > 0 AND scanned_builds = 0)
| sort scan_coverage
| table repository, total_builds, scanned_builds, scan_coverage, deployments
```
- **Implementation:** (1) Forward CI/CD pipeline events to Splunk via webhooks or HEC; (2) define minimum security gate requirements (SAST scan, dependency check, container image scan); (3) alert on deployments to production without security scan evidence; (4) track scan coverage percentage as a NIS2 KPI; (5) correlate with change management tickets to verify security review sign-off.
- **Visualization:** Table (repos without scans), Bar chart (scan coverage by repo), Single value (overall scan coverage %), Line chart (coverage trend).
- **CIM Models:** N/A

---

### UC-22.2.16 · NIS2 Supply Chain Third-Party Risk Continuous Monitoring (Art. 21(2)(d))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1078, T1048
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Beyond vendor session monitoring (UC-22.2.2), Article 21(2)(d) requires continuous security assessment of direct suppliers and service providers. This use case tracks third-party SaaS and API dependency health, monitors supplier security posture indicators, and detects anomalous data flows to supplier networks — providing broader supply chain risk visibility than PAM session monitoring alone.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for AWS (Splunkbase 1876)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Network_Traffic data model, `index=proxy` (web proxy logs), DNS logs, threat intelligence lookups, `index=cloud` (SaaS audit logs)
- **SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as internal_sources
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.dest_category="supplier"
  by All_Traffic.dest All_Traffic.app span=1d
| rename All_Traffic.* as *
| lookup supplier_risk_lookup dest OUTPUT supplier_name, risk_tier, last_assessment_date
| eval days_since_assessment=round((now()-strptime(last_assessment_date,"%Y-%m-%d"))/86400, 0)
| eval assessment_overdue=if(days_since_assessment > 365, 1, 0)
| where bytes_out > 1073741824 OR assessment_overdue=1 OR internal_sources > 50
| sort - bytes_out
| table dest, supplier_name, risk_tier, bytes_out, internal_sources, days_since_assessment, assessment_overdue
```
- **Implementation:** (1) Tag supplier destination IPs/domains in ES asset framework with `category=supplier`; (2) maintain `supplier_risk_lookup` with vendor names, risk tiers, and last assessment dates; (3) alert on large data transfers to suppliers (potential exfiltration vector); (4) flag suppliers with overdue security assessments; (5) correlate supplier domains with threat intelligence feeds; (6) report on supply chain risk posture for board-level NIS2 compliance evidence.
- **Visualization:** Table (supplier risk overview), Bar chart (data transfer by supplier), Single value (overdue assessments), Heatmap (supplier access patterns).
- **CIM Models:** Network_Traffic

---

### UC-22.2.17 · NIS2 Backup Management and Disaster Recovery Verification (Art. 21(2)(c))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Splunk Pillar:** IT Operations
- **Regulations:** EU NIS2
- **Value:** While UC-22.2.4 monitors live service health during crises, Article 21(2)(c) specifically requires backup management and disaster recovery capabilities. This use case tracks backup job success/failure, validates restore test completion, and monitors RTO/RPO target adherence — providing the operational evidence that NIS2 auditors specifically ask for: "show me your last successful restore test."
- **App/TA:** Splunk Add-on for Veeam (Splunkbase 7173), Splunk ITSI (Splunkbase 1841)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=backup` (backup software logs — Veeam, Commvault, Rubrik, AWS Backup), `index=itsi_summary` (service recovery KPIs)
- **SPL:**
```spl
index=backup sourcetype IN ("veeam:backup","commvault:job","rubrik:event","aws:backup") earliest=-7d
| eval job_status=lower(coalesce(status, result, job_result, state))
| eval success=if(match(job_status,"(?i)success|completed|ok"), 1, 0)
| eval failed=if(match(job_status,"(?i)fail|error|warning|missed"), 1, 0)
| stats sum(success) as successful, sum(failed) as failed, latest(_time) as last_backup by job_name, target_system
| eval days_since_backup=round((now()-last_backup)/86400, 1)
| eval backup_gap=if(days_since_backup > 1, "OVERDUE", "OK")
| where failed > 0 OR backup_gap="OVERDUE"
| sort - days_since_backup
| table target_system, job_name, successful, failed, days_since_backup, backup_gap
```
- **Implementation:** (1) Forward backup software logs via syslog or HEC; (2) define RTO/RPO targets per NIS2-scoped service and validate against actual backup frequency; (3) alert on any failed backup for critical systems; (4) track restore test completion in a KV store (date, system, result, duration); (5) schedule monthly restore tests and report results; (6) include restore test evidence in Article 21(2)(f) effectiveness assessment (UC-22.2.9).
- **Visualization:** Table (failed/overdue backups), Single value (backup success rate %), Bar chart (failures by system), Timeline (backup history).
- **CIM Models:** N/A

---

### UC-22.2.18 · NIS2 Network Security Monitoring and Anomaly Detection (Art. 21(2)(a))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048, T1562
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 21(2)(a) requires information system security policies to be operational, not just documented. This use case provides continuous network security monitoring — detecting lateral movement, unauthorized network segments, protocol anomalies, and traffic patterns that deviate from baseline — serving as the core evidence that network security policies are enforced through technical controls.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for Stream (Splunkbase 1809)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Network_Traffic data model, firewall logs, IDS/IPS events, DNS logs
- **SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as total_bytes dc(All_Traffic.dest_port) as dest_ports
  from datamodel=Network_Traffic.All_Traffic
  where NOT All_Traffic.dest_category IN ("internal_server","dns","ntp")
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| rename All_Traffic.* as *
| where dest_ports > 20 OR (action="blocked" AND count > 100) OR total_bytes > 10737418240
| lookup asset_lookup_by_str key AS src OUTPUT category as src_category, priority as src_priority
| eval risk_signal=case(
    dest_ports > 50, "port_scan",
    action="blocked" AND count > 500, "brute_force",
    total_bytes > 10737418240, "data_exfiltration",
    isnull(src_category), "unknown_asset",
    1=1, "anomaly")
| sort - count
| table _time, src, dest, src_category, risk_signal, dest_ports, count, total_bytes, action
```
- **Implementation:** (1) Ensure CIM Network_Traffic data model is populated from firewall, proxy, and IDS sources; (2) define network segmentation zones and tag in asset framework; (3) alert on port scanning, brute force patterns, and large data transfers; (4) baseline normal traffic patterns and detect deviations; (5) integrate with ES Risk framework to aggregate network anomalies into risk scores for NIS2-scoped assets.
- **Visualization:** Table (anomalies), Bar chart (risk signals by type), Map (traffic flows), Timeline (blocked connections), Sankey diagram (source to destination flows).
- **CIM Models:** Network_Traffic, Intrusion_Detection

---

### UC-22.2.19 · NIS2 Cross-Border Incident Impact Assessment (Art. 23(3))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 23(3) requires entities to determine whether significant incidents have cross-border impact and to notify CSIRTs in all affected Member States. This use case identifies whether incident-related traffic, compromised assets, or affected users span multiple countries — automating the cross-border impact assessment that NIS2 makes mandatory for multi-jurisdictional operations.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, CIM Network_Traffic, ES Asset Framework (with geo/country tags), Authentication CIM
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status!="Closed" earliest=-7d
| eval incident_assets=mvappend(src, dest, src_ip, dest_ip)
| mvexpand incident_assets
| lookup asset_lookup_by_str key AS incident_assets OUTPUT country, business_unit, category
| iplocation incident_assets
| eval asset_country=coalesce(country, Country)
| where isnotnull(asset_country)
| stats dc(asset_country) as countries_affected, values(asset_country) as affected_countries, dc(incident_assets) as assets_involved by rule_name, urgency
| where countries_affected > 1
| eval cross_border_notification="REQUIRED — notify CSIRT in: " . mvjoin(affected_countries, ", ")
| table rule_name, urgency, countries_affected, affected_countries, assets_involved, cross_border_notification
```
- **Implementation:** (1) Tag assets in ES asset framework with `country` field for all NIS2-scoped systems; (2) enrich IP-based assets with `iplocation`; (3) run against all high/critical notables to assess cross-border scope; (4) auto-generate notification lists for multi-CSIRT reporting; (5) integrate with legal/compliance workflow for mandatory parallel notifications; (6) document cross-border assessment in final report (UC-22.2.8).
- **Visualization:** Table (cross-border incidents), Map (affected countries), Single value (incidents requiring multi-CSIRT notification), Bar chart (countries involved).
- **CIM Models:** N/A

---

### UC-22.2.20 · NIS2 Management Body Accountability and Governance Evidence (Art. 20)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Splunk Pillar:** Security
- **Regulations:** EU NIS2
- **Value:** Article 20 requires management bodies to approve and oversee cybersecurity risk-management measures, undergo training, and be personally accountable. This use case aggregates evidence of management engagement — board-level security report generation, policy approval timestamps, executive training completion, and risk acceptance decisions — into a single governance compliance dashboard.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** KV stores (manual governance records), `_audit` (scheduled report execution), `index=training` (executive training records)
- **SPL:**
```spl
| inputlookup nis2_governance_evidence.csv
| eval evidence_date=strptime(date, "%Y-%m-%d")
| eval days_since=round((now()-evidence_date)/86400, 0)
| eval status=case(
    days_since > 365, "OVERDUE",
    days_since > 270, "DUE_SOON",
    1=1, "CURRENT")
| sort - days_since
| table evidence_type, description, responsible_person, date, days_since, status
```
- **Implementation:** (1) Create `nis2_governance_evidence.csv` KV store with evidence types: board_security_briefing, policy_approval, executive_training, risk_acceptance, audit_review, tabletop_exercise; (2) populate manually or via ServiceNow integration; (3) alert when any evidence type is overdue by >365 days; (4) generate quarterly governance report for board; (5) include training completion certificates for management body members.
- **Visualization:** Table (governance evidence status), Traffic light indicators (current/due/overdue), Timeline (governance activities), Single value (overdue items).
- **CIM Models:** N/A

---

### 22.3 DORA

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for Qualys (Splunkbase 2964), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk Add-on for Veeam (Splunkbase 7173), Splunk Synthetic Monitoring, Splunk Common Information Model Add-on (Splunkbase 1621).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:change_request`, `snow:incident`), Tenable/Qualys vulnerability scans (`tenable:vuln`, `qualys:hostdetection`), AWS CloudTrail (`aws:cloudtrail`), Azure Activity (`mscs:azure:auditlog`), backup software logs (Veeam, Commvault, Rubrik, AWS Backup), CIM data models (Authentication, Network_Traffic, Vulnerabilities, Change), Splunk audit logs (`_audit`, `_internal`), DORA register lookups (`dora_critical_systems.csv`, `dora_ict_provider_register.csv`, `dora_testing_schedule.csv`, `dora_governance_evidence.csv`).

---

### UC-22.3.1 · DORA ICT Risk Management Dashboard (Art. 5-16)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Compliance
- **Industry:** Financial Services
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
- **MITRE ATT&CK:** T1048, T1562
- **Industry:** Financial Services
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
- **Industry:** Financial Services
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
- **Industry:** Financial Services
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
- **Industry:** Financial Services
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

### UC-22.3.6 · DORA ICT Change Management and Patch Compliance (Art. 9(4)(e))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 9(4)(e) requires documented ICT change management policies that are risk-assessed and approved before deployment. This use case tracks change ticket compliance for ICT systems supporting critical functions — detecting unauthorized changes, changes without approval, and emergency changes without post-implementation review — providing evidence that protection and prevention controls are operational.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `index=itsm` `sourcetype="snow:change_request"`, `index=windows` `sourcetype="WinEventLog:System"`, CIM Change data model
- **SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.command All_Changes.change_type _time span=1d
| rename All_Changes.* as *
| lookup dora_critical_systems.csv object AS object OUTPUT critical_function, business_service
| where isnotnull(critical_function)
| lookup change_ticket_lookup object AS object, _time OUTPUT ticket_number, approval_status, risk_assessment
| eval unauthorized=if(isnull(ticket_number), 1, 0)
| eval unapproved=if(isnotnull(ticket_number) AND approval_status!="approved", 1, 0)
| stats count, sum(unauthorized) as unauthorized_changes, sum(unapproved) as unapproved_changes by object, critical_function, business_service
| where unauthorized_changes > 0 OR unapproved_changes > 0
| sort - unauthorized_changes
| table object, critical_function, business_service, count, unauthorized_changes, unapproved_changes
```
- **Implementation:** (1) Create `dora_critical_systems.csv` mapping ICT assets to critical/important business functions; (2) correlate CIM Change events with ServiceNow change tickets; (3) alert on any change to critical systems without an approved ticket; (4) track emergency changes separately and verify post-implementation review within 5 business days; (5) report change compliance rate as DORA governance KPI.
- **Visualization:** Table (unauthorized changes), Bar chart (changes by approval status), Single value (change compliance %), Timeline (changes to critical systems).
- **CIM Models:** Change

---

### UC-22.3.7 · DORA ICT Anomaly Detection Capabilities (Art. 10)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 10 requires financial entities to have mechanisms to promptly detect anomalous activities including ICT network performance issues and ICT-related incidents. This use case monitors the health and coverage of detection capabilities themselves — ensuring that correlation searches are running, data sources are flowing, and detection coverage spans all critical ICT systems — proving that detection infrastructure meets DORA requirements.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `_audit` (correlation search execution), `_internal` (data ingestion), ES Content Management
- **SPL:**
```spl
| rest /services/saved/searches splunk_server=local count=0
| search disabled=0 is_scheduled=1 action.correlationsearch.enabled=1
| eval last_run=strftime(strptime(next_scheduled_time,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%d %H:%M")
| table title, cron_schedule, next_scheduled_time, action.correlationsearch.label
| append [
    search index=_internal sourcetype=splunkd group=per_index_thruput earliest=-4h
    | stats latest(ev) as last_events by series
    | where last_events=0
    | eval title="DATA_GAP: ".series, status="NO_DATA_4H"
    | table title, status
]
| sort title
```
- **Implementation:** (1) Verify all ES correlation searches for critical ICT functions are enabled and running; (2) monitor data source health — alert when indexes supporting critical detection go silent for >4 hours; (3) map detection coverage against DORA critical functions to identify blind spots; (4) report detection coverage percentage and data source health as DORA Art. 10 evidence.
- **Visualization:** Table (detection coverage and data gaps), Single value (active correlation searches), Bar chart (data gaps by index), Gauge (detection coverage %).
- **CIM Models:** N/A

---

### UC-22.3.8 · DORA ICT Incident Response and Recovery Time Tracking (Art. 11)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **MITRE ATT&CK:** T1048, T1562
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 11 requires financial entities to put in place ICT response and recovery plans for critical functions, including estimated recovery times. This use case measures actual response and recovery times against defined RTO/RPO targets for DORA-regulated services, tracking mean-time-to-detect (MTTD), mean-time-to-respond (MTTR), and mean-time-to-recover (MTTRC) — the operational evidence that response and recovery capabilities are tested and effective.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841)
- **Premium Apps:** Splunk Enterprise Security, Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `` `notable` `` macro (incident lifecycle), `index=itsi_summary` (service recovery KPIs)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status="Closed" earliest=-90d
| eval detect_time=_time
| eval respond_time=if(isnotnull(status_description) AND match(status_description,"(?i)acknowledged|triaged|investigating"), strptime(status_description,"%Y-%m-%d %H:%M:%S"), null())
| eval close_time=if(status="Closed", now(), null())
| eval mttd_h=round((detect_time - info_min_time)/3600, 2)
| eval mttr_h=round((close_time - detect_time)/3600, 2)
| lookup dora_critical_systems.csv dest AS dest OUTPUT critical_function, rto_hours, rpo_hours
| eval rto_breach=if(isnotnull(rto_hours) AND mttr_h > rto_hours, 1, 0)
| stats avg(mttd_h) as avg_mttd, avg(mttr_h) as avg_mttr, sum(rto_breach) as rto_breaches, count by critical_function
| table critical_function, count, avg_mttd, avg_mttr, rto_breaches
| sort - rto_breaches
```
- **Implementation:** (1) Define RTO/RPO per critical function in `dora_critical_systems.csv`; (2) instrument incident workflow to capture timestamps at detection, acknowledgement, containment, and resolution; (3) compare actual recovery times against defined targets; (4) alert on RTO breaches for critical functions; (5) report MTTD/MTTR trends quarterly for management body oversight.
- **Visualization:** Bar chart (avg MTTR by function), Single value (avg MTTD), Table (RTO breaches), Line chart (MTTR trend over 90 days).
- **CIM Models:** N/A

---

### UC-22.3.9 · DORA Backup Completeness and Restoration Testing (Art. 12)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** IT Operations
- **Regulations:** DORA
- **Value:** Article 12 requires documented backup policies specifying scope and frequency based on criticality, with backup systems physically and logically segregated. Restoration procedures must be periodically tested. This use case tracks backup job success/failure for DORA-regulated systems, validates segregation requirements, and monitors restoration test completion — going beyond cloud DR replication (UC-22.3.5) to cover the full backup lifecycle.
- **App/TA:** Splunk Add-on for Veeam (Splunkbase 7173), Splunk ITSI (Splunkbase 1841)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=backup` (backup software logs), `dora_backup_schedule.csv` (expected backup frequency per system)
- **SPL:**
```spl
index=backup sourcetype IN ("veeam:backup","commvault:job","rubrik:event","aws:backup") earliest=-7d
| eval status=lower(coalesce(status, result, state))
| eval success=if(match(status,"(?i)success|completed|ok"), 1, 0)
| eval failed=if(match(status,"(?i)fail|error|warning"), 1, 0)
| stats sum(success) as successes, sum(failed) as failures, latest(_time) as last_backup by job_name, target_system
| lookup dora_critical_systems.csv system_name AS target_system OUTPUT critical_function, backup_frequency_hours
| where isnotnull(critical_function)
| eval hours_since_backup=round((now()-last_backup)/3600, 1)
| eval backup_overdue=if(isnotnull(backup_frequency_hours) AND hours_since_backup > backup_frequency_hours, "OVERDUE", "OK")
| eval backup_success_rate=round(100*successes/(successes+failures), 1)
| where failures > 0 OR backup_overdue="OVERDUE" OR backup_success_rate < 95
| sort - failures
| table target_system, critical_function, successes, failures, backup_success_rate, hours_since_backup, backup_overdue
```
- **Implementation:** (1) Forward backup software logs via syslog or HEC; (2) define expected backup frequency per DORA-critical system in `dora_backup_schedule.csv`; (3) alert on failed backups for critical functions immediately; (4) track restoration test completion in a KV store — DORA requires periodic testing; (5) validate physical/logical segregation by confirming backup destinations differ from source infrastructure.
- **Visualization:** Table (backup status per critical system), Single value (backup success rate %), Bar chart (failures by system), Timeline (backup history).
- **CIM Models:** N/A

---

### UC-22.3.10 · DORA Post-Incident Review and Learning (Art. 13)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 13 requires financial entities to have capabilities and staff to learn from ICT-related incidents, share lessons, and evolve their ICT risk management framework. This use case tracks whether major incidents result in completed post-incident reviews (PIRs), that root causes are documented, and that improvement actions are implemented — providing the "learning and evolving" evidence DORA specifically mandates.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, `index=itsm` (PIR/RCA records), `dora_pir_completion.csv` (KV store)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status="Closed" earliest=-180d
| lookup dora_pir_completion.csv notable_id AS event_id OUTPUT pir_status, pir_date, root_cause, improvement_actions, actions_completed
| eval pir_due=if(isnull(pir_status), "MISSING", pir_status)
| eval actions_closed=if(isnotnull(actions_completed) AND actions_completed="yes", "DONE", "OPEN")
| stats count by pir_due, actions_closed
| append [
    search `notable` urgency IN ("high","critical") status="Closed" earliest=-180d
    | lookup dora_pir_completion.csv notable_id AS event_id OUTPUT pir_status, improvement_actions, actions_completed
    | where pir_status!="completed" OR isnull(pir_status) OR actions_completed!="yes"
    | table _time, rule_name, urgency, pir_status, improvement_actions, actions_completed
    | sort - _time
]
```
- **Implementation:** (1) Create `dora_pir_completion.csv` KV store linking ES notable IDs to PIR records; (2) require PIR completion within 30 days of incident closure; (3) track root cause categories for trend analysis; (4) monitor improvement action implementation status; (5) report on learning cycle completion rates to management body; (6) share anonymised lessons across business units as Art. 13 requires.
- **Visualization:** Pie chart (PIR completion status), Table (incidents without PIR), Bar chart (root cause categories), Single value (PIR completion rate %), Timeline (PIR lifecycle).
- **CIM Models:** N/A

---

### UC-22.3.11 · DORA Major ICT Incident 7-Criteria Classification (Art. 18)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1048
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** DORA Article 18 and RTS 2024/1772 define seven classification criteria for determining whether an ICT incident is "major" — an incident meeting two or more criteria thresholds triggers mandatory reporting. This use case automates the classification assessment against all seven criteria, replacing manual spreadsheet-based classification and accelerating the 4-hour initial notification deadline.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841)
- **Premium Apps:** Splunk Enterprise Security, Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `` `notable` `` macro, `index=itsi_summary`, CIM Authentication and Network_Traffic data models, `dora_service_client_mapping.csv`
- **SPL:**
```spl
`notable` urgency IN ("high","critical") status!="Closed" earliest=-48h
| eval affected_systems=mvappend(src, dest)
| mvexpand affected_systems
| lookup dora_service_client_mapping.csv system_name AS affected_systems OUTPUT service_name, client_count, client_pct, countries_served, data_classification
| stats dc(affected_systems) as systems_hit, max(client_count) as max_clients_affected, max(client_pct) as max_client_pct,
        dc(countries_served) as geo_spread, values(data_classification) as data_types by rule_name, urgency
| eval c1_clients=if(max_client_pct > 10 OR max_clients_affected > 500, 1, 0)
| eval c2_geographic=if(geo_spread > 1, 1, 0)
| eval c3_duration="ASSESS_MANUALLY"
| eval c4_data_loss=if(match(mvjoin(data_types,","),"(?i)confidential|restricted|pii|financial"), 1, 0)
| eval criteria_met=c1_clients + c2_geographic + c4_data_loss
| eval classification=if(criteria_met >= 2, "MAJOR — mandatory reporting", "Significant or below — assess remaining criteria")
| eval reporting_deadline=if(classification="MAJOR — mandatory reporting", "4h initial + 72h intermediate + 1mo final", "Monitor")
| table rule_name, urgency, systems_hit, max_clients_affected, max_client_pct, geo_spread, data_types, criteria_met, classification, reporting_deadline
| sort - criteria_met
```
- **Implementation:** (1) Build `dora_service_client_mapping.csv` mapping ICT systems to business services, client counts/percentages, geographic reach, and data classifications; (2) automate criteria 1 (clients), 2 (geographic), and 4 (data loss) — criteria 3 (duration), 5-7 require manual assessment initially; (3) alert immediately when criteria_met >= 2 — the 4-hour reporting clock starts; (4) integrate with SOAR for automated notification workflow; (5) document classification rationale for each incident.
- **Visualization:** Table (incident classification results), Single value (major incidents requiring reporting), Bar chart (criteria met per incident), Traffic light (classification status).
- **CIM Models:** N/A

---

### UC-22.3.12 · DORA ICT Incident Intermediate and Final Report Tracking (Art. 19)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 19 mandates a three-report lifecycle for major ICT incidents: initial notification (4h), intermediate report (72h), and final report (1 month). UC-22.3.2 covers the initial classification, but this use case tracks the full reporting lifecycle — ensuring intermediate reports include quantified impact, preliminary root cause, and remediation status, and that final reports contain complete root cause analysis, corrective actions, and lessons learned.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `` `notable` `` macro, `dora_incident_reports.csv` (KV store tracking report submissions)
- **SPL:**
```spl
`notable` urgency IN ("high","critical") earliest=-60d
| lookup dora_incident_reports.csv notable_id AS event_id OUTPUT dora_classification, initial_report_time, intermediate_report_time, final_report_time, initial_submitted, intermediate_submitted, final_submitted
| where dora_classification="major"
| eval hours_since_detection=round((now()-_time)/3600, 2)
| eval initial_status=case(initial_submitted="yes","SUBMITTED", hours_since_detection<=4,"WITHIN_WINDOW", 1=1,"OVERDUE")
| eval intermediate_status=case(intermediate_submitted="yes","SUBMITTED", hours_since_detection<=72,"WITHIN_WINDOW", 1=1,"OVERDUE")
| eval final_status=case(final_submitted="yes","SUBMITTED", hours_since_detection<=(30*24),"WITHIN_WINDOW", 1=1,"OVERDUE")
| where initial_status="OVERDUE" OR intermediate_status="OVERDUE" OR final_status="OVERDUE" OR intermediate_status="WITHIN_WINDOW" OR final_status="WITHIN_WINDOW"
| table _time, rule_name, urgency, hours_since_detection, initial_status, intermediate_status, final_status, owner
| sort - hours_since_detection
```
- **Implementation:** (1) Create `dora_incident_reports.csv` KV store linking classified major incidents to their three report submission timestamps; (2) alert at 3h for initial report, at 48h for intermediate report, and at 21 days for final report; (3) validate intermediate report contains quantified impact and preliminary root cause; (4) validate final report contains complete root cause, corrective actions, and medium/long-term plan; (5) submit to competent authority using mandated templates.
- **Visualization:** Table (report status per major incident), Traffic lights (report deadlines), Single value (overdue reports), Timeline (reporting lifecycle).
- **CIM Models:** N/A

---

### UC-22.3.13 · DORA Register of Information for ICT Third-Party Arrangements (Art. 28(3))
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 28(3) requires financial entities to maintain and update a register of information on all contractual arrangements with ICT third-party service providers, distinguishing those supporting critical or important functions. This use case validates register completeness by comparing actual ICT provider traffic against the register and detecting unregistered providers or stale entries.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for AWS (Splunkbase 1876)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Network_Traffic data model, DNS logs, `dora_ict_provider_register.csv`
- **SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as total_bytes dc(All_Traffic.src) as internal_sources
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="allowed" NOT All_Traffic.dest_category IN ("internal","internal_server")
  by All_Traffic.dest
| rename All_Traffic.* as *
| iplocation dest
| lookup dora_ict_provider_register.csv dest_domain AS dest OUTPUT provider_name, contract_id, criticality, exit_plan_status, last_review_date
| eval in_register=if(isnotnull(provider_name), "REGISTERED", "NOT_IN_REGISTER")
| eval review_overdue=if(isnotnull(last_review_date) AND (now()-strptime(last_review_date,"%Y-%m-%d"))/86400 > 365, "OVERDUE", "OK")
| eval bytes_gb=round(total_bytes/1073741824, 2)
| where (in_register="NOT_IN_REGISTER" AND bytes_gb > 0.1) OR review_overdue="OVERDUE"
| sort - bytes_gb
| table dest, Country, provider_name, in_register, bytes_gb, internal_sources, criticality, exit_plan_status, review_overdue
```
- **Implementation:** (1) Maintain `dora_ict_provider_register.csv` with all ICT third-party arrangements per Art. 28(3) requirements; (2) include contract IDs, criticality flags, exit plan status, and review dates; (3) compare actual network traffic destinations against registered providers; (4) flag unregistered high-volume destinations for procurement review; (5) submit register to competent authorities upon request; (6) review annually with management body approval.
- **Visualization:** Table (unregistered providers), Single value (register coverage %), Bar chart (traffic to unregistered destinations), Pie chart (registered vs unregistered by volume).
- **CIM Models:** Network_Traffic

---

### UC-22.3.14 · DORA ICT Third-Party SLA Performance Monitoring (Art. 30)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** IT Operations
- **Regulations:** DORA
- **Value:** Article 30 requires contractual arrangements to include precise quantitative and qualitative performance targets for services supporting critical functions. This use case monitors actual ICT provider performance against SLA targets — availability, response time, throughput — detecting SLA breaches that may indicate degraded operational resilience and trigger contractual remediation or exit procedures.
- **App/TA:** Splunk ITSI (Splunkbase 1841), Splunk Synthetic Monitoring
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=itsi_summary` (service/KPI data for provider-dependent services), synthetic monitoring results, `dora_provider_slas.csv`
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0 earliest=-30d
| lookup dora_provider_slas.csv service_name OUTPUT provider_name, sla_availability_pct, sla_response_ms, contract_id, criticality
| where isnotnull(provider_name)
| stats avg(health_score) as avg_health, count(eval(severity_value>=4)) as critical_breaches, count as total_observations by service_name, provider_name, sla_availability_pct, criticality
| eval actual_availability=round(100*(total_observations - critical_breaches)/total_observations, 2)
| eval sla_met=if(actual_availability >= sla_availability_pct, "MET", "BREACHED")
| where sla_met="BREACHED" OR avg_health < 80
| sort actual_availability
| table service_name, provider_name, criticality, sla_availability_pct, actual_availability, sla_met, critical_breaches, avg_health
```
- **Implementation:** (1) Map ITSI services to ICT providers and their SLA targets in `dora_provider_slas.csv`; (2) include availability, response time, and throughput SLAs; (3) alert on SLA breaches for critical function providers; (4) escalate repeated breaches for exit strategy activation; (5) report provider performance to management body quarterly.
- **Visualization:** Table (provider SLA compliance), Gauge (availability per provider), Bar chart (SLA breaches by provider), Line chart (provider health trend).
- **CIM Models:** N/A

---

### UC-22.3.15 · DORA ICT Access Control and Authentication Monitoring (Art. 9(4)(c))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1078, T1110, T1098
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 9(4)(c) requires policies for digital identity management, access control limiting physical and logical access to ICT assets and data, and strong authentication mechanisms. This use case monitors authentication patterns across DORA-regulated ICT systems — detecting shared accounts, weak authentication, privilege escalation, and access from unauthorized locations — providing the access control evidence DORA mandates for protection and prevention.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** CIM Authentication data model, `index=auth`, `index=windows`, `index=azure`
- **SPL:**
```spl
| tstats `summariesonly` count dc(Authentication.src) as src_count dc(Authentication.dest) as dest_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user Authentication.app span=1d
| rename Authentication.* as *
| lookup dora_critical_systems.csv system_name AS dest OUTPUT critical_function
| where isnotnull(critical_function)
| eval risk_signals=mvappend(
    if(src_count > 5, "MULTI_LOCATION", null()),
    if(match(lower(user),"(?i)shared|generic|test|admin[0-9]"), "SHARED_ACCOUNT", null()),
    if(match(lower(app),"(?i)password|basic|ntlm") AND NOT match(lower(app),"(?i)mfa|2fa|cert|kerberos"), "WEAK_AUTH", null()))
| where isnotnull(risk_signals)
| table user, app, critical_function, count, src_count, dest_count, risk_signals
| sort - count
```
- **Implementation:** (1) Ensure CIM Authentication data model is populated from domain controllers, IdPs, and cloud auth sources; (2) tag critical ICT systems in `dora_critical_systems.csv`; (3) alert on shared accounts accessing critical functions; (4) detect authentication without MFA for privileged operations; (5) report access control compliance to management body; (6) correlate with HR data for joiner/mover/leaver validation.
- **Visualization:** Table (access control risks), Bar chart (risks by type), Single value (shared account usage), Heatmap (user × critical system access).
- **CIM Models:** Authentication

---

### UC-22.3.16 · DORA Vulnerability Assessment and Penetration Test Tracking (Art. 25)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1562
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 25 requires vulnerability assessments, network security assessments, source code reviews, scenario-based tests, and penetration testing for all ICT systems supporting critical functions. This use case tracks test execution, coverage, and finding remediation — ensuring the full testing program required by DORA is executed on schedule and that identified vulnerabilities are remediated within defined SLAs.
- **App/TA:** Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for Qualys (Splunkbase 2964)
- **Data Sources:** `index=vulnerability` (scan results), `dora_testing_schedule.csv` (planned test calendar), `index=itsm` (remediation tickets)
- **SPL:**
```spl
| inputlookup dora_testing_schedule.csv
| eval planned_date=strptime(scheduled_date, "%Y-%m-%d")
| eval days_until_due=round((planned_date - now())/86400, 0)
| eval test_status=case(
    completed="yes", "COMPLETED",
    days_until_due < 0, "OVERDUE",
    days_until_due <= 30, "DUE_SOON",
    1=1, "SCHEDULED")
| append [
    search index=vulnerability sourcetype IN ("tenable:vuln","qualys:hostdetection") state="Active" earliest=-90d
    | lookup dora_critical_systems.csv system_name AS host OUTPUT critical_function
    | where isnotnull(critical_function)
    | eval sla_days=case(severity="Critical",7, severity="High",30, severity="Medium",90, 1=1,180)
    | eval age_days=round((now()-first_found)/86400,1)
    | eval sla_breach=if(age_days > sla_days, 1, 0)
    | stats sum(sla_breach) as overdue_vulns, count as total_vulns by critical_function
    | eval test_type="Vulnerability_Remediation", test_status=if(overdue_vulns > 0, "REMEDIATION_OVERDUE", "ON_TRACK")
    | table test_type, critical_function, total_vulns, overdue_vulns, test_status
]
| table test_type, critical_function, scheduled_date, test_status, total_vulns, overdue_vulns
| sort test_status
```
- **Implementation:** (1) Create `dora_testing_schedule.csv` with all planned vulnerability assessments, pen tests, source code reviews, and scenario tests per Art. 25 requirements; (2) alert when tests are overdue; (3) track vulnerability remediation SLAs for DORA-critical systems; (4) report testing coverage and finding trends to management body; (5) for central securities depositories and central counterparties, ensure pre-deployment vulnerability assessments per Art. 25(2).
- **Visualization:** Table (test schedule with status), Bar chart (overdue tests by type), Single value (testing coverage %), Pie chart (test status distribution).
- **CIM Models:** Vulnerabilities

---

### UC-22.3.17 · DORA Threat-Led Penetration Testing (TLPT) Lifecycle (Art. 26)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **MITRE ATT&CK:** T1562
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 26 requires financial entities identified by competent authorities to conduct TLPT at least every three years, following TIBER-EU methodology with qualified external testers. This use case tracks the TLPT lifecycle — from threat intelligence scoping through red team execution to remediation of findings — ensuring the advanced testing programme that DORA mandates for systemically important entities is completed and acted upon.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** `dora_tlpt_register.csv` (TLPT engagement tracking), `index=itsm` (remediation tickets), ES Notable events (from purple team exercises)
- **SPL:**
```spl
| inputlookup dora_tlpt_register.csv
| eval last_tlpt_date=strptime(completion_date, "%Y-%m-%d")
| eval months_since_tlpt=round((now()-last_tlpt_date)/(86400*30), 0)
| eval next_due=if(months_since_tlpt >= 36, "OVERDUE", if(months_since_tlpt >= 30, "DUE_WITHIN_6_MONTHS", "ON_TRACK"))
| eval findings_remediated=if(isnotnull(total_findings) AND isnotnull(findings_closed), round(100*findings_closed/total_findings,1), 0)
| table scope, tester_organization, completion_date, months_since_tlpt, next_due, total_findings, findings_closed, findings_remediated, critical_findings_open
| sort next_due
```
- **Implementation:** (1) Create `dora_tlpt_register.csv` with TLPT engagement records (scope, tester, completion date, finding counts); (2) track three-year cycle per Art. 26; (3) monitor finding remediation — critical findings should be remediated within 90 days; (4) validate tester qualifications per Art. 27; (5) coordinate pooled TLPT with entities sharing the same ICT provider where applicable; (6) report TLPT status to competent authority.
- **Visualization:** Table (TLPT status), Single value (months since last TLPT), Gauge (finding remediation %), Bar chart (open findings by severity).
- **CIM Models:** N/A

---

### UC-22.3.18 · DORA ICT Third-Party Exit Strategy Readiness (Art. 28(8))
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 28(8) requires exit strategies for all ICT arrangements supporting critical or important functions, with tested transition plans. This use case monitors exit strategy readiness by tracking whether exit plans exist, are tested, and have viable alternatives identified — combined with operational dependency metrics showing how deeply the entity relies on each provider, informing realistic transition timelines.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for AWS (Splunkbase 1876)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `dora_ict_provider_register.csv`, CIM Network_Traffic data model, cloud provider audit logs
- **SPL:**
```spl
| inputlookup dora_ict_provider_register.csv WHERE criticality IN ("critical","important")
| eval exit_plan_exists=if(isnotnull(exit_plan_status) AND exit_plan_status!="none", 1, 0)
| eval exit_plan_tested=if(exit_plan_status="tested", 1, 0)
| eval alternative_identified=if(isnotnull(alternative_provider), 1, 0)
| eval last_test_date_epoch=if(isnotnull(exit_plan_test_date), strptime(exit_plan_test_date,"%Y-%m-%d"), null())
| eval months_since_test=if(isnotnull(last_test_date_epoch), round((now()-last_test_date_epoch)/(86400*30),0), 999)
| eval readiness=case(
    exit_plan_tested=1 AND alternative_identified=1 AND months_since_test<=12, "READY",
    exit_plan_exists=1 AND alternative_identified=1, "PARTIAL — test overdue",
    exit_plan_exists=1, "PARTIAL — no alternative",
    1=1, "NOT_READY — plan required")
| stats count by readiness
| append [
    search | inputlookup dora_ict_provider_register.csv WHERE criticality IN ("critical","important")
    | where exit_plan_status IN ("none","") OR isnull(exit_plan_status) OR isnull(alternative_provider)
    | table provider_name, contract_id, criticality, exit_plan_status, alternative_provider
    | sort criticality
]
```
- **Implementation:** (1) Extend `dora_ict_provider_register.csv` with exit plan status, test dates, and alternative provider fields; (2) alert on critical function providers without exit plans; (3) require annual exit plan testing; (4) combine with concentration risk data (UC-22.3.4) — providers with high concentration AND no exit plan represent highest risk; (5) report exit strategy readiness to management body annually; (6) validate data return/portability capabilities per Art. 30 contractual requirements.
- **Visualization:** Pie chart (exit readiness distribution), Table (providers without exit plans), Bar chart (readiness by criticality), Single value (% providers with tested exit plans).
- **CIM Models:** N/A

---

### UC-22.3.19 · DORA Management Body ICT Governance and Oversight (Art. 5)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 5 places ultimate accountability for ICT risk management on the management body, requiring members to maintain sufficient knowledge and skills, undergo training, and actively oversee the ICT risk framework. This use case aggregates governance evidence — board ICT risk briefings, framework approval dates, training completion, and risk acceptance decisions — into a compliance dashboard proving management body engagement.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** `dora_governance_evidence.csv` (KV store), `_audit` (scheduled report execution)
- **SPL:**
```spl
| inputlookup dora_governance_evidence.csv
| eval evidence_date=strptime(date, "%Y-%m-%d")
| eval days_since=round((now()-evidence_date)/86400, 0)
| eval status=case(
    evidence_type="board_ict_risk_briefing" AND days_since > 90, "OVERDUE",
    evidence_type="framework_approval" AND days_since > 365, "OVERDUE",
    evidence_type="member_training" AND days_since > 365, "OVERDUE",
    evidence_type="risk_appetite_review" AND days_since > 365, "OVERDUE",
    evidence_type="provider_register_review" AND days_since > 365, "OVERDUE",
    days_since > 270, "DUE_SOON",
    1=1, "CURRENT")
| sort - days_since
| table evidence_type, description, responsible_person, date, days_since, status
```
- **Implementation:** (1) Create `dora_governance_evidence.csv` KV store with evidence types: board_ict_risk_briefing (quarterly), framework_approval (annual), member_training (annual), risk_appetite_review (annual), provider_register_review (annual), budget_allocation (annual); (2) populate manually or via board secretary integration; (3) alert when any evidence type is overdue; (4) generate quarterly governance report for competent authorities; (5) document management body decisions on ICT risk tolerance and budget.
- **Visualization:** Table (governance evidence status), Traffic light indicators (current/due/overdue), Timeline (governance activities), Single value (overdue items).
- **CIM Models:** N/A

---

### UC-22.3.20 · DORA ICT Crisis Communication Readiness (Art. 14)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** DORA
- **Value:** Article 14 requires financial entities to have communication plans for ICT-related incidents and vulnerabilities, including disclosure to clients and counterparts, and internal escalation. This use case tracks crisis communication readiness — ensuring communication plans are documented, tested, contact lists are current, and that during active incidents, stakeholder notifications are timely and documented.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** `dora_comms_readiness.csv` (KV store), `` `notable` `` macro, `index=itsm` (communication records)
- **SPL:**
```spl
| inputlookup dora_comms_readiness.csv
| eval last_update=strptime(last_updated, "%Y-%m-%d")
| eval days_since_update=round((now()-last_update)/86400, 0)
| eval freshness=case(
    days_since_update > 180, "STALE — update required",
    days_since_update > 90, "REVIEW_DUE",
    1=1, "CURRENT")
| table component, description, owner, last_updated, days_since_update, freshness, last_drill_date
| sort freshness
```
- **Implementation:** (1) Create `dora_comms_readiness.csv` with components: stakeholder_contact_list, client_notification_template, regulator_notification_template, internal_escalation_matrix, media_holding_statement, crisis_call_bridge_details; (2) update at least every 6 months; (3) track communication drill completion; (4) during active major incidents, verify that client and counterparty notifications are sent and documented; (5) validate contact list accuracy by comparing against HR/CRM data.
- **Visualization:** Table (communication readiness status), Traffic lights (component freshness), Single value (stale components count), Timeline (drill history).
- **CIM Models:** N/A

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
- **MITRE ATT&CK:** T1048, T1530
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
- **MITRE ATT&CK:** T1005, T1530
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

### UC-22.4.4 · CCPA Right to Correct Inaccurate Personal Information (§1798.106)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Businesses must use commercially reasonable efforts to correct inaccurate personal information upon a verifiable request. This search tracks correction tickets from intake through closure so you can prove timely handling and reduce risk of complaints to the California Attorney General for mishandled consumer rights workflows.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, opened_at, closed_at, state, cat_item, short_description, assignment_group)
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_req_item" earliest=-90d
    (short_description="*correct*" OR short_description="*inaccurate*" OR cat_item="*CCPA*Correct*")
| eval opened_epoch=strptime(opened_at, "%Y-%m-%d %H:%M:%S")
| eval closed_epoch=if(isnotnull(closed_at), strptime(closed_at, "%Y-%m-%d %H:%M:%S"), null())
| eval age_days=round((now()-opened_epoch)/86400, 1)
| eval sla_days=45
| eval at_risk=if(isnull(closed_epoch) AND age_days>(sla_days-7), 1, 0)
| stats count as requests, sum(at_risk) as nearing_breach by assignment_group, state
| sort - requests
```
- **Implementation:** (1) Align `cat_item` and keyword filters with your ServiceNow CCPA correction catalog items; (2) route agent queues into `assignment_group` for accountability dashboards; (3) join optional `consumer_id_hash` field if present for deduplication; (4) schedule daily and alert when `nearing_breach>0`; (5) export monthly evidence for privacy counsel.
- **Visualization:** Table (open corrections with age), Bar chart (volume by assignment_group), Single value (requests past 38 days open).
- **CIM Models:** N/A

---

### UC-22.4.5 · CCPA Data Broker Sale Disclosure and Third-Party Sharing Audit (§1798.99.80, §1798.115)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1048, T1530
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Consumers must receive meaningful notice about categories of personal information sold or shared and the categories of third parties. Monitoring structured “sale/share” pipeline logs shows operational alignment with disclosure obligations and supports rapid investigation if downstream systems process opted-out households.
- **App/TA:** Splunk HTTP Event Collector (core platform), Splunk Add-on for AWS (Splunkbase 1876) (optional archive path)
- **Data Sources:** `index=privacy` `sourcetype="_json"` `source="http:ccpa_sale_share"` (event_type, consumer_opted_out, data_category, third_party_id, contract_id, _time)
- **SPL:**
```spl
index=privacy sourcetype="_json" source="http:ccpa_sale_share" earliest=-7d
| where event_type IN ("sale_batch","share_batch","broker_feed")
| eval violation=if(consumer_opted_out="true" AND match(event_type,"sale|share|broker"), 1, 0)
| stats count as events, sum(violation) as potential_violations, dc(third_party_id) as third_parties by data_category, event_type
| sort - potential_violations
```
- **Implementation:** (1) Instrument CRM, CDP, or data-broker connectors to POST JSON batches to HEC with `consumer_opted_out` resolved from your consent store; (2) map `data_category` labels to your external privacy notice; (3) block or alert on `violation=1`; (4) retain five years or per records-management policy; (5) correlate with web `dnsmpi` hits from UC-22.4.2 for end-to-end proof.
- **Visualization:** Table (categories x third parties), Column chart (events by event_type), Single value (potential_violations).
- **CIM Models:** N/A

---

### UC-22.4.6 · CCPA Global Privacy Control and “Do Not Sell or Share” Signal Enforcement (§1798.120, §1798.135(b))
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1565, T1078
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Opt-out preference signals including GPC must be honored where required. Aggregating API-side opt-out application outcomes demonstrates that technical controls downstream of the browser actually suppress sale/share processing, not only that marketing pages were visited.
- **App/TA:** Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=privacy` `sourcetype="_json"` `source="http:ccpa_optout_apply"` (profile_id, channel, gpc_received, opt_out_applied, failure_reason, _time)
- **SPL:**
```spl
index=privacy sourcetype="_json" source="http:ccpa_optout_apply" earliest=-24h
| eval failed=if(opt_out_applied="false" OR isnotnull(failure_reason), 1, 0)
| stats count as attempts, sum(failed) as failures, sum(eval(gpc_received="true")) as gpc_context by channel
| eval fail_rate=round(100*failures/attempts, 2)
| sort - failures
```
- **Implementation:** (1) Emit one event per profile/channel when consent middleware finishes applying opt-out; (2) set `gpc_received` from upstream headers; (3) alert if `fail_rate>1` percent for any `channel`; (4) join failures to application logs via `profile_id`; (5) document rollback procedures for bad releases.
- **Visualization:** Timechart (attempts vs failures), Table (channel, fail_rate), Pie chart (gpc_context ratio).
- **CIM Models:** N/A

---

### UC-22.4.7 · CCPA Financial Incentive Program Consent and Withdrawal Monitoring (§1798.125)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Financial incentive programs require good-faith estimates of program value, clear opt-in, and easy withdrawal without discriminatory treatment. This use case audits incentive enrollments and withdrawals to evidence fair process and support inquiries about material terms.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186) or Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (method, uri, status, clientip); OR `index=marketing` `sourcetype="_json"` `source="http:loyalty_ccpa"` (action, program_id, material_terms_version, _time)
- **SPL:**
```spl
(index=web sourcetype="access_combined" earliest=-30d uri="*/loyalty/ccpa-consent*" OR uri="*/financial-incentive*")
OR (index=marketing sourcetype="_json" source="http:loyalty_ccpa" earliest=-30d)
| eval evt=coalesce(action, method)
| eval ok=if(status IN ("200","201","204") OR match(_raw,"\"success\"\\s*:\\s*true"), 1, 0)
| stats count as hits, sum(ok) as successful by uri, program_id, material_terms_version
| fillnull value="web" program_id
| sort - hits
```
- **Implementation:** (1) Log consent, withdrawal, and material-terms acknowledgment with version IDs in JSON or stable URI patterns; (2) map `program_id` to written estimate documents; (3) alert on spikes in non-200 responses; (4) exclude bot user agents via lookup; (5) quarterly export for legal review of `material_terms_version` mix.
- **Visualization:** Bar chart (hits by program_id), Table (terms version adoption), Line chart (daily successful consents).
- **CIM Models:** Web

---

### UC-22.4.8 · CCPA Authorized Agent Request Verification and Fulfillment (§1798.140(ah), §1798.145)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1078, T1110
- **Splunk Pillar:** Security
- **Regulations:** CCPA
- **Value:** Businesses may require authorized agents to submit proof of signing authority. Tracking agent-submitted tickets with verification outcomes reduces fraud risk and demonstrates consistent authentication before disclosing or deleting consumer data.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, short_description, u_agent_verified, u_power_of_attorney_on_file, state, opened_at)
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_req_item" earliest=-90d
    (short_description="*authorized agent*" OR short_description="*power of attorney*")
| eval verified=coalesce(u_agent_verified, "unknown")
| eval fulfilled=if(match(state,"(?i)closed|resolved|complete"),1,0)
| stats count as tickets,
        sum(eval(verified="false" OR verified="unknown")) as not_verified,
        sum(fulfilled) as closed
    by verified
| eval risk_pct=round(100*not_verified/tickets,1)
| sort - tickets
```
- **Implementation:** (1) Add custom fields on the privacy request form for agent verification and PoA storage references; (2) block fulfillment workflows until `u_agent_verified=true` except where statute allows; (3) schedule weekly review of `not_verified`; (4) integrate DocuSign webhook optional second sourcetype; (5) redact attachments from Splunk—index metadata only.
- **Visualization:** Table (verification state x counts), Donut chart (verified vs not), Timeline (median days to close by verified).
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
- **Industry:** Financial Services
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
- **Industry:** Financial Services
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
- **Industry:** Financial Services
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

### UC-22.5.4 · MiFID II Transaction Reporting Timeliness and Rejection Root-Cause (RTS 22, Art. 26)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Competent authorities expect complete, accurate, and timely transaction reports. Measuring submit-to-acknowledgement latency and clustering rejection codes supports proactive fixes before regulatory breaches and demonstrates surveillance over ARM/APA gateway health.
- **App/TA:** Splunk HTTP Event Collector (core platform) with JSON parsing
- **Data Sources:** `index=trading` `sourcetype="_json"` `source="http:trx_reporting"` (transaction_report_id, submit_epoch_ms, ack_epoch_ms, reject_code, venue, instrument_id)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:trx_reporting" earliest=-7d
| eval latency_ms=ack_epoch_ms-submit_epoch_ms
| eval late=if(latency_ms>600000 OR isnull(ack_epoch_ms), 1, 0)
| stats count as reports, sum(late) as late_or_open, dc(reject_code) as distinct_reject_codes by venue, reject_code
| sort - late_or_open
```
- **Implementation:** (1) Normalize clocks with NTP on reporting hosts and store epoch milliseconds; (2) treat missing `ack_epoch_ms` after T+1 as open submissions; (3) maintain `reject_code_meanings.csv` lookup for narrative dashboards; (4) alert if `late_or_open/reports>0.01`; (5) feed monthly summary to compliance committee.
- **Visualization:** Histogram (latency_ms), Table (venue, reject_code, counts), Single value (late_or_open).
- **CIM Models:** N/A

---

### UC-22.5.5 · MiFID II Product Governance and Target Market Appropriateness Evidence (Art. 9(3) MiFIR, Art. 16(3) MiFID II)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Manufacturers and distributors must maintain product-approval processes and identify target markets. Tracking workflow completion for new product launches evidences governance discipline and helps detect rushed approvals or missing distributor notifications.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, cat_item, state, opened_at, closed_at, u_product_isin, u_target_market_signed_off)
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_req_item" earliest=-365d
    (cat_item="*Product Governance*" OR cat_item="*MiFID Product*")
| eval signed_off=coalesce(u_target_market_signed_off, "false")
| eval is_closed=if(match(state,"(?i)closed|resolved|complete"),1,0)
| stats count as launches,
        sum(eval(is_closed=0)) as open_approvals,
        sum(eval(signed_off="false" AND is_closed=1)) as closed_without_signoff
    by cat_item
| where open_approvals>0 OR closed_without_signoff>0
| sort - open_approvals
```
- **Implementation:** (1) Model ServiceNow catalog items for product approval with mandatory `u_target_market_signed_off`; (2) require `u_product_isin` or internal SKU; (3) alert on `closed_without_signoff>0`; (4) join marketing distribution lists optional via lookup; (5) archive closed items quarterly for NCAs.
- **Visualization:** Table (catalog item health), Bar chart (open_approvals), Single value (closed_without_signoff).
- **CIM Models:** N/A

---

### UC-22.5.6 · MiFID II Order and Decision Data Record Integrity (Art. 25)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1565, T1005
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Investment firms must keep orderly records of services and transactions. Detecting gaps or duplicate order IDs in OMS/EMS journals supports defensible reconstruction of the decision chain during regulatory reconstruction exercises.
- **App/TA:** Financial Information eXchange (FIX) Log Parsing (Splunkbase 431), Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=trading` `sourcetype="_json"` `source="http:order_lifecycle"` (order_id, cl_ord_id, event_type, venue, decision_time_ms, _time)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:order_lifecycle" earliest=-1d
| where event_type IN ("NewOrderSingle","OrderCancelReplaceRequest","ExecutionReport","OrderCancelRequest")
| stats min(_time) as first_seen, max(_time) as last_seen, dc(event_type) as event_types, count as events by order_id
| eval span_sec=last_seen-first_seen
| eventstats dc(order_id) as total_orders
| eventstats sum(events) as sum_events
| eval dup_ratio=round(events/sum_events, 6)
| where events<2 OR span_sec<0.001
| sort order_id
```
- **Implementation:** (1) Ensure every order emits at least creation and terminal state events; (2) hash sensitive client fields before indexing; (3) alert on `events<2` for statuses that should be terminal within T day; (4) tune `span_sec` threshold for high-frequency desks; (5) export samples for internal audit replay tools.
- **Visualization:** Table (suspect orders), Column chart (events per order_id distribution via `bin events`), Single value (count of orders with events<2).
- **CIM Models:** N/A

---

### UC-22.5.7 · MiFID II Clock Synchronization and Timestamp Quality for Reporting (RTS 25)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Compliance, Security
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** RTS 25 mandates traceable UTC synchronization for algorithmic and high-frequency activity reporting. Comparing application-reported event time to Splunk ingestion `_time` highlights skewed hosts or malformed timestamps that could invalidate best execution and transaction reports.
- **App/TA:** Splunk Universal Forwarder (core platform), Splunk Add-on for Unix and Linux (Splunkbase 833)
- **Data Sources:** `index=os` `sourcetype="Unix:Version"` OR `sourcetype="chrony:tracking"` (host, SystemTime, LeapStatus, LastOffset, RMSOffset); `index=trading` `sourcetype="_json"` `source="http:order_lifecycle"` (host, reported_event_epoch_ms, _time)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:order_lifecycle" earliest=-4h isnotnull(reported_event_epoch_ms)
| eval skew_ms=abs((reported_event_epoch_ms/1000)-_time)*1000
| stats median(skew_ms) as p50_skew, perc95(skew_ms) as p95_skew, max(skew_ms) as max_skew by host
| where p95_skew>250 OR max_skew>1000
| sort - p95_skew
```
- **Implementation:** (1) Forward `chrony` or `ntpq` telemetry from trading servers; (2) align JSON `reported_event_epoch_ms` with exchange event time definitions; (3) alert on hosts breaching your documented max skew (e.g. 250 ms); (4) exclude batch backfills with a `ingest_mode` flag; (5) document remediation in runbooks tied to RTS 25 testing.
- **Visualization:** Table (host skew stats), Timechart (median skew by host), Single value (hosts breaching threshold).
- **CIM Models:** N/A

---

### UC-22.5.8 · MiFID II Algorithmic Trading Strategy Limits and Kill-Switch Audit (Art. 17)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1562, T1078
- **Industry:** Financial Services
- **Splunk Pillar:** Security
- **Regulations:** MiFID II
- **Value:** Firms must have effective systems and risk controls for algorithmic trading, including thresholds and kill switches. Auditing throttle breaches and manual halts evidences governance and supports supervisory questions after market stress events.
- **App/TA:** Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=trading` `sourcetype="_json"` `source="http:algo_controls"` (strategy_id, event_type, notional_limit_usd, notional_observed_usd, kill_switch_actor, _time)
- **SPL:**
```spl
index=trading sourcetype="_json" source="http:algo_controls" earliest=-30d
| where event_type IN ("limit_breach","kill_switch_activated","kill_switch_reset","parameter_change")
| eval breach=if(event_type="limit_breach" OR (isnotnull(notional_observed_usd) AND notional_observed_usd>notional_limit_usd), 1, 0)
| stats count as events, sum(breach) as breaches, dc(strategy_id) as strategies_affected by event_type, kill_switch_actor
| sort - breaches
```
- **Implementation:** (1) Emit structured events from risk gateways when limits are approached, breached, or when kill switches fire; (2) require `kill_switch_actor` for manual actions; (3) correlate with market data halts optional; (4) retain immutable copy to WORM storage per policy; (5) quarterly tabletop review of top `strategies_affected`.
- **Visualization:** Timeline (events by strategy_id), Table (event_type totals), Bar chart (breaches by strategy).
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
- **MITRE ATT&CK:** T1078, T1098
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

### UC-22.6.4 · ISO 27001 Information Labelling and Media Handling via DLP (A.8.2.3)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1005, T1048
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Annex A expects procedures for labelling information according to protection needs and handling removable media and transfers consistently. Microsoft 365 DLP events evidence that confidentiality labels and policies are enforced in practice, not only in the ISMS manual.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055)
- **Data Sources:** `index=o365` `sourcetype="ms:o365:management"` (Workload, PolicyName, Operation, UserPrincipalName, SensitiveInfoType, FileName, Severity)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp" earliest=-7d
| where Operation IN ("DlpRuleMatch","DlpRuleUndo") OR match(PolicyName,"(?i)label|confidential|restricted")
| stats count by PolicyName, Operation, SensitiveInfoType, Severity
| sort - count
```
- **Implementation:** (1) Map `PolicyName` to your classification scheme in `info_classification_lookup.csv`; (2) exclude benign test accounts; (3) alert on high-severity outbound matches to personal domains if field present; (4) align retention with A.18.1 legal holds; (5) include panel in annual internal audit evidence pack.
- **Visualization:** Heatmap (PolicyName x SensitiveInfoType), Table (top users optional via `stats by UserPrincipalName`), Bar chart (count by Severity).
- **CIM Models:** N/A

---

### UC-22.6.5 · ISO 27001 Cryptographic Key and Certificate Lifecycle Monitoring (A.10.1.2)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1098, T1562
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Key management requires defined lifecycles and protection of secret keys. Tracking upcoming TLS certificate expirations and vault key-rotation events demonstrates operational control over cryptography supporting confidentiality and integrity commitments.
- **App/TA:** Splunk Add-on for OpenTelemetry (Splunkbase 6238) or certificate scan TA, Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=security` `sourcetype="cert:inventory"` (cn, san, not_after, issuer, host); `index=secrets` `sourcetype="_json"` `source="http:vault_audit"` (path, operation, _time) for asymmetric key rotations
- **SPL:**
```spl
index=security sourcetype="cert:inventory" earliest=-1d
| eval exp_epoch=coalesce(
    strptime(not_after,"%Y-%m-%dT%H:%M:%SZ"),
    strptime(not_after,"%Y-%m-%d %H:%M:%S"))
| eval days_to_exp=round((exp_epoch-now())/86400,1)
| where isnotnull(days_to_exp) AND days_to_exp<45
| stats values(host) as hosts, min(days_to_exp) as min_days by cn, issuer
| sort min_days
```
```spl
index=secrets sourcetype="_json" source="http:vault_audit" operation="rotate" earliest=-30d
| stats count as rotations by path
| sort - rotations
```
- **Implementation:** (1) Ingest nightly cert inventory from ACM or Venafi with `not_after` in consistent UTC format; (2) forward HashiCorp Vault audit or cloud KMS rotation webhooks to `index=secrets` for signing keys; (3) alert at 30/14/7 days on TLS `min_days`; (4) document owners in lookup `cert_owner.csv`; (5) tie renewals to change tickets for A.12.1.
- **Visualization:** Table (expiring certs), Timeline (rotation events), Single value (count expiring <14 days).
- **CIM Models:** N/A

---

### UC-22.6.6 · ISO 27001 Network Security — Segmentation and Firewall Deny Baseline (A.13.1.1)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1562.007
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Networks must be segregated and filtered according to business requirements. Trending denied flows against approved baselines highlights misconfigurations or lateral movement precursors, supporting Annex A evidence for technical network controls.
- **App/TA:** Splunk Add-on for Palo Alto Networks (Splunkbase 2757) or vendor firewall TA
- **Data Sources:** `index=network` `sourcetype="pan:traffic"` (action, src, dest, dest_port, rule, app)
- **SPL:**
```spl
index=network sourcetype="pan:traffic" action=deny earliest=-24h
| stats count as denies, dc(src) as sources, values(dest_port) as ports by dest, rule
| lookup expected_perimeter_denies.csv dest dest_port OUTPUT is_expected
| where isnull(is_expected) OR is_expected="false"
| sort - denies
```
- **Implementation:** (1) Normalize firewall CIM or vendor fields to `action`, `src`, `dest`, `dest_port`; (2) seed `expected_perimeter_denies.csv` with known scanner noise; (3) alert on sudden `denies` spikes vs 30-day baseline using `anomalydetection` optional; (4) map `rule` to change records; (5) monthly review with network architecture team.
- **Visualization:** Map or table (top denied dest), Timechart (denies by rule), Bar chart (sources).
- **CIM Models:** Network_Traffic

---

### UC-22.6.7 · ISO 27001 Supplier IAM and SaaS Integration Change Surveillance (A.15.1.2)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1098, T1078
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Supplier relationships must address information security in agreements and monitor service changes. Cloud IAM audit logs for OAuth app consent and service principal changes surface high-risk supplier integrations that could bypass on-prem controls.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Data Sources:** `index=azure` `sourcetype="mscs:azure:auditlog"` (activityDisplayName, initiatedBy, targetResources, result, _time)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:auditlog" earliest=-30d
    (activityDisplayName="*consent*" OR activityDisplayName="*Add app*" OR activityDisplayName="*service principal*")
| eval actor=coalesce(initiatedBy.user.userPrincipalName, initiatedBy.app.displayName, "unknown")
| stats count by activityDisplayName, actor, result
| sort - count
```
- **Implementation:** (1) Scope to tenant IDs for production directories; (2) enrich with `saas_vendor_risk.csv` keyed on `targetResources{}.displayName`; (3) alert on failed `result` spikes or new high-risk vendors; (4) require CAB reference in ServiceNow optional via lookup; (5) quarterly supplier review slide export.
- **Visualization:** Table (activity x actor), Bar chart (consent events by vendor), Single value (distinct actors).
- **CIM Models:** Change

---

### UC-22.6.8 · ISO 27001 Segregation of Duties — Privileged Splunk Knowledge Object Changes (A.5.3)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1098, T1078
- **Splunk Pillar:** Security
- **Regulations:** ISO 27001
- **Value:** Conflicting duties must be separated to reduce fraud and error. Auditing edits to high-risk Splunk objects by the same accounts that can execute destructive searches evidences compensating detective controls where native SoD is limited.
- **App/TA:** Splunk Enterprise core auditing (`_audit` index)
- **Data Sources:** `index=_audit` (object_type, action, user, object, info)
- **SPL:**
```spl
index=_audit object_type IN ("savedsearch","alert_actions","transforms","props","authorize") action IN ("create","update","delete") earliest=-30d
| eval object_name=coalesce(object, info)
| stats count as changes, values(action) as actions, dc(object_type) as object_types by user
| lookup splunk_privileged_users.csv user OUTPUT is_breakglass
| where is_breakglass="true" OR changes>25
| sort - changes
```
- **Implementation:** (1) Maintain `splunk_privileged_users.csv` for admin and break-glass IDs; (2) forward `_audit` from all search heads in the cluster; (3) alert on deletes to `authorize` or `props`; (4) pair with change tickets via `user`→`snow_sys_id` lookup; (5) include in role recertification for A.9.2.5.
- **Visualization:** Table (user, changes, actions), Timeline (edits by object_type), Single value (delete actions count).
- **CIM Models:** N/A

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

### UC-22.7.3 · NIST CSF Identify — Asset Inventory Coverage and Shadow SaaS Signals (ID.AM-2)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** The Identify function requires software platforms and applications to be inventoried. Comparing cloud audit OAuth consent events against an approved SaaS catalog highlights shadow applications that consume corporate identity before they appear in the CMDB.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Data Sources:** `index=azure` `sourcetype="mscs:azure:auditlog"` (activityDisplayName, targetResources, initiatedBy, _time); `approved_saas_apps.csv` lookup (app_display_name, approved_tier)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:auditlog" earliest=-30d activityDisplayName="Add OAuth2PermissionGrant"
| eval app=mvindex(targetResources{}.displayName,0)
| lookup approved_saas_apps.csv app AS app_display_name OUTPUT approved_tier
| eval shadow=if(isnull(approved_tier), 1, 0)
| stats count as grants, sum(shadow) as unapproved_app_hits by app, approved_tier
| sort - unapproved_app_hits
```
- **Implementation:** (1) Build `approved_saas_apps.csv` from enterprise architecture; (2) tune `activityDisplayName` for your IdP (Google Workspace equivalent sourcetype optional); (3) alert when `unapproved_app_hits>0` for production tenants; (4) feed discoveries into asset intake workflow; (5) refresh catalog monthly.
- **Visualization:** Table (app, grants, approved_tier), Bar chart (shadow vs approved), Pie chart (grant volume).
- **CIM Models:** Change

---

### UC-22.7.4 · NIST CSF Protect — Identity Authentication Hardening and MFA Gaps (PR.AC-1)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1078, T1556
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** PR.AC-1 expects identities and credentials to be managed for authorized devices and users. Surfacing interactive logons without MFA claim presence from Windows or Entra sign-in logs supports remediation of weak authentication before credential attacks succeed.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110)
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Security"` (EventCode, TargetUserName, WorkstationName, AuthenticationPackageName); `index=azure` `sourcetype="mscs:azure:signinlog"` (userPrincipalName, authenticationRequirement, conditionalAccessStatus, appDisplayName, status.errorCode)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:signinlog" earliest=-24h status.errorCode=0
| where isnull(authenticationRequirement) OR lower(authenticationRequirement)!="multifactorauthentication"
| stats count by userPrincipalName, authenticationRequirement, conditionalAccessStatus, appDisplayName
| sort - count
```
- **Implementation:** (1) Ingest Entra ID sign-in logs with Microsoft Cloud Services TA; (2) exclude break-glass accounts via lookup; (3) correlate with Conditional Access policy changes; (4) drive remediation tickets to IAM; (5) track rolling MFA coverage percent in executive dashboard.
- **Visualization:** Table (users and apps lacking MFA), Bar chart (count by appDisplayName), Single value (events last 24h).
- **CIM Models:** Authentication

---

### UC-22.7.5 · NIST CSF Detect — Continuous Vulnerability Exposure Drift on Critical Servers (DE.CM-7)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1562
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** DE.CM-7 expects monitoring that surfaces unauthorized or risky software and configuration states, including exploitable weaknesses. Tracking critical and high CVE counts on in-scope assets over time demonstrates that vulnerability findings are continuously visible—not only during annual scan windows—and drives timely remediation aligned to risk tolerance.
- **App/TA:** Tenable Add-On for Splunk (Splunkbase 4060)
- **Data Sources:** `index=vuln` `sourcetype="tenable:vuln"` (host, plugin_id, severity, first_seen, last_seen, cve)
- **SPL:**
```spl
index=vuln sourcetype="tenable:vuln" earliest=-14d severity IN ("Critical","High")
| lookup pci_in_scope_hosts.csv host OUTPUT in_scope
| where in_scope="true"
| stats dc(cve) as distinct_cves, dc(plugin_id) as distinct_plugins, values(severity) as severities by host
| sort - distinct_cves
```
- **Implementation:** (1) Maintain `pci_in_scope_hosts.csv` or generic `critical_asset_hosts.csv`; (2) normalize `host` to FQDN used in CMDB; (3) alert when `distinct_cves` increases week over week; (4) join patch tickets from ServiceNow optional; (5) document SLAs in CSF tier narrative.
- **Visualization:** Table (host exposure), Column chart (distinct_cves), Line chart (weekly trend via appendcols or summary index).
- **CIM Models:** Vulnerabilities

---

### UC-22.7.6 · NIST CSF Respond — Incident Response Playbook Execution and Stage Timestamps (RS.RP-1)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1048, T1070
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** RS.RP-1 requires response processes to be executed during and after an incident. Measuring Splunk SOAR incident-response playbook success rates alongside ServiceNow security-incident stage timing proves that documented response procedures actually run and that closure timelines are measurable for after-action review.
- **App/TA:** Splunk SOAR, Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=soar` `sourcetype="phantom:playbook_run"` (playbook_name, status, _time); `index=itsm` `sourcetype="snow:incident"` (number, u_ir_stage, state, work_start, resolved_at, short_description)
- **SPL:**
```spl
index=soar sourcetype="phantom:playbook_run" earliest=-90d playbook_name="*IR*"
| stats count as runs,
        count(eval(status="success")) as successes,
        count(eval(status="failed")) as failures
    by playbook_name
| eval success_pct=if(runs>0, round(100*successes/runs,1), null())
| where failures>0 OR success_pct<95
| sort playbook_name
```
```spl
index=itsm sourcetype="snow:incident" earliest=-90d short_description="*security incident*"
| eval start_epoch=strptime(work_start, "%Y-%m-%d %H:%M:%S")
| eval end_epoch=strptime(resolved_at, "%Y-%m-%d %H:%M:%S")
| eval duration_sec=if(isnotnull(start_epoch) AND isnotnull(end_epoch), end_epoch-start_epoch, null())
| stats count as incidents, median(duration_sec) as median_duration_sec by u_ir_stage, state
| eval median_duration_h=round(median_duration_sec/3600,2)
| sort - incidents
```
- **Implementation:** (1) Standardize Splunk SOAR playbook names for major incident classes and map `status` vocabulary to success/failed; (2) if using ServiceNow, map `u_ir_stage` values to NIST IR phases and require `work_start`/`resolved_at` for MTTR; (3) alert on SOAR `status` failure spikes; (4) exclude test containers with non-prod labels; (5) quarterly export for tabletop lessons learned.
- **Visualization:** Table (playbook_name, runs, successes, failures, success_pct), Bar chart (failures by playbook), Table (ServiceNow stages with median_duration_h).
- **CIM Models:** N/A

---

### UC-22.7.7 · NIST CSF Recover — Backup Job Success and RTO Readiness for Critical Databases (RC.RP-1)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** NIST CSF
- **Value:** RC.RP-1 expects recovery planning and improvements after incidents. Monitoring backup completion for databases tied to RTO tiers evidences that restoration inputs are healthy and flags silent failures that would block ransomware recovery.
- **App/TA:** Splunk Add-on for NetBackup (Splunkbase 2185) or Commvault/Cohesity TA, Splunk DB Connect (Splunkbase 1556) optional
- **Data Sources:** `index=backup` `sourcetype="netbackup:job"` (client_name, policy_name, status, kb_written, _time); `rto_tier_lookup.csv` (client_name, rto_hours)
- **SPL:**
```spl
index=backup sourcetype="netbackup:job" earliest=-7d
| lookup rto_tier_lookup.csv client_name OUTPUT rto_hours
| where isnotnull(rto_hours)
| eval failed=if(match(status,"(?i)fail|error|partial"),1,0)
| stats count as jobs, sum(failed) as failed_jobs by client_name, policy_name, rto_hours
| eval fail_pct=round(100*failed_jobs/jobs,2)
| where fail_pct>0 OR failed_jobs>0
| sort - failed_jobs
```
- **Implementation:** (1) Ingest backup product logs with stable `status` vocabulary; (2) align `client_name` to database hostnames; (3) alert on any failed job for tier-0; (4) validate against storage dedupe errors in secondary sourcetype; (5) tie to BC/DR test calendar for RC.IM improvements.
- **Visualization:** Table (client, fail_pct), Single value (failed_jobs), Timechart (daily success rate by tier).
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
- **MITRE ATT&CK:** T1005, T1048
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

### UC-22.8.4 · SOC 2 Control Environment and Board-Level Attestation Workflow (CC1.2, CC2.1)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** CC1 and CC2 require communication and information about roles, responsibilities, and performance to support functioning of internal control. Tracking completion of quarterly control-owner attestations in ITSM demonstrates tone-at-the-top processes are operationalized with timestamps.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:sc_req_item"` (number, cat_item, state, closed_at, opened_at, assigned_to, u_control_id)
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_req_item" earliest=-120d (cat_item="*SOC2*Attestation*" OR short_description="*control owner attestation*")
| eval is_closed=if(match(state,"(?i)closed|resolved|complete"),1,0)
| stats count as tasks, sum(is_closed) as completed, dc(assigned_to) as owners by u_control_id, cat_item
| eval completion_pct=round(100*completed/tasks,1)
| where completion_pct<100
| sort u_control_id
```
- **Implementation:** (1) Create catalog items per SOC2 control family with `u_control_id` matching your CCM matrix; (2) schedule quarterly auto-open tasks; (3) escalate open items after 14 days; (4) export CSV for external auditors; (5) map `assigned_to` to job titles for CC1.3 HR evidence optional.
- **Visualization:** Table (control completion), Bar chart (open vs closed), Single value (tasks past due).
- **CIM Models:** N/A

---

### UC-22.8.5 · SOC 2 Risk Assessment — Change-Induced Emergency Pattern Monitoring (CC3.2, CC3.3)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** CC3 expects risk identification and analysis, including changes that significantly affect the system. Correlating production emergency changes with recent deployments highlights process breakdowns where velocity outpaces risk assessment.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:change_request"` (number, type, risk, start_date, end_date, state, short_description, u_emergency_flag)
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" earliest=-90d state="Closed"
| eval emergency=coalesce(u_emergency_flag, if(match(type,"(?i)emergency"),"true","false"))
| where emergency="true"
| eval duration_h=(strptime(end_date,"%Y-%m-%d %H:%M:%S")-strptime(start_date,"%Y-%m-%d %H:%M:%S"))/3600
| stats count as emergency_changes, median(duration_h) as median_duration by risk, cmdb_ci
| sort - emergency_changes
```
- **Implementation:** (1) Ensure `u_emergency_flag` or `type` differentiates emergencies; (2) join `cmdb_ci` to service tier lookup; (3) alert when `emergency_changes` spikes vs baseline; (4) require post-implementation review field completeness; (5) feed results into quarterly risk committee deck.
- **Visualization:** Bar chart (emergency_changes by service), Table (risk, median_duration), Timechart (weekly emergency volume).
- **CIM Models:** Change

---

### UC-22.8.6 · SOC 2 Processing Integrity — Financial Batch Job Reconciliation Exceptions (PI1.3)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1565
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** Processing integrity criteria require system processing to be complete, valid, accurate, timely, and authorized. Monitoring ETL or billing batch exception counts versus totals provides continuous evidence that automated controls detect and surface out-of-balance conditions.
- **App/TA:** Splunk HTTP Event Collector (core platform), Splunk DB Connect (Splunkbase 1556) optional
- **Data Sources:** `index=finance` `sourcetype="_json"` `source="http:batch_recon"` (batch_id, records_total, records_failed, amount_total, amount_exception, pipeline, _time)
- **SPL:**
```spl
index=finance sourcetype="_json" source="http:batch_recon" earliest=-7d
| eval fail_rate=round(100*records_failed/records_total,4)
| eval amt_exc_rate=if(amount_total>0, round(100*amount_exception/amount_total,4), 0)
| stats sum(records_total) as rows, sum(records_failed) as failed_rows, max(fail_rate) as peak_fail_rate by pipeline, batch_id
| where failed_rows>0 OR peak_fail_rate>0.01
| sort - failed_rows
```
- **Implementation:** (1) Publish one JSON event per batch completion from orchestration (Airflow, Control-M, mainframe bridge); (2) define materiality thresholds per `pipeline`; (3) alert on `peak_fail_rate` breaches; (4) retain hash of source file name for audit trail; (5) map `pipeline` to SOC subservice description in the system description.
- **Visualization:** Table (batch exceptions), Line chart (fail_rate over time by pipeline), Single value (failed_rows).
- **CIM Models:** N/A

---

### UC-22.8.7 · SOC 2 Privacy — Consent Log Integrity and Downstream Propagation Checks (P4.2, P4.3)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1565, T1005
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** Privacy criteria expect notices about processing and consent to be accurate and current. Comparing consent-store updates to marketing execution logs detects cases where email or SMS campaigns run after withdrawal timestamps—an integrity failure with reputational and regulatory impact.
- **App/TA:** Splunk HTTP Event Collector (core platform)
- **Data Sources:** `index=privacy` `sourcetype="_json"` `source="http:consent_store"` (profile_id, consent_email_marketing, updated_epoch_ms); `index=marketing` `sourcetype="_json"` `source="http:campaign_send"` (profile_id, channel, send_epoch_ms, campaign_id)
- **SPL:**
```spl
index=marketing sourcetype="_json" source="http:campaign_send" earliest=-7d channel IN ("email","sms")
| join type=left profile_id [
    search index=privacy sourcetype="_json" source="http:consent_store" earliest=-30d
    | eval withdraw=if(consent_email_marketing="false", updated_epoch_ms, null())
    | stats latest(withdraw) as last_withdraw_ms by profile_id
  ]
| eval send_ms=send_epoch_ms
| where isnotnull(last_withdraw_ms) AND send_ms>last_withdraw_ms
| stats count as sends_after_withdrawal by campaign_id, channel
| sort - sends_after_withdrawal
```
- **Implementation:** (1) Ensure epoch fields share UTC basis; (2) use `profile_id` as stable key; (3) alert on any `sends_after_withdrawal>0`; (4) cap join window for performance using `subsearch` time range; (5) document corrective action in privacy incident register.
- **Visualization:** Table (violating campaigns), Bar chart (sends_after_withdrawal), Single value (distinct profiles affected).
- **CIM Models:** N/A

---

### UC-22.8.8 · SOC 2 Fraud Risk and Anomalous Privileged Activity Correlation (CC9.2)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1078, T1048
- **Splunk Pillar:** Security
- **Regulations:** SOC 2
- **Value:** CC9.2 addresses risks of fraud, including fraud due to management override. Correlating after-hours privileged logons with Splunk `_audit` searches touching high-sensitivity indexes surfaces potential override paths for investigator review without presuming guilt.
- **App/TA:** Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Enterprise core auditing (`_audit` index)
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Security"` (EventCode, TargetUserName, _time, LogonType); `index=_audit` `action=search` (user, search, _time)
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Security" EventCode=4624 LogonType=10 earliest=-7d
| eval hour=strftime(_time,"%H")
| where hour<6 OR hour>22
| lookup domain_admins.csv TargetUserName OUTPUT is_privileged
| where is_privileged="true"
| stats earliest(_time) as first_priv, latest(_time) as last_priv by TargetUserName
| join type=left max=0 TargetUserName [
    search index=_audit action=search info=completed earliest=-7d
    | where match(search, "(?i)index\\s*=\\s*(pci|hr|finance)")
    | stats earliest(_time) as first_search by user
    | rename user as TargetUserName
  ]
| eval suspicious=if(isnotnull(first_search) AND first_search>=first_priv AND first_search<=relative_time(last_priv,"+2h"), 1, 0)
| where suspicious=1
| table TargetUserName, first_priv, first_search, suspicious
```
- **Implementation:** (1) Tune RDP (`LogonType=10`) vs your jump host patterns; (2) maintain `domain_admins.csv`; (3) adjust sensitive index regex to your taxonomy; (4) route hits to SOC insider-threat queue; (5) document investigation outcomes for CC4 monitoring activities.
- **Visualization:** Table (correlated events), Timeline (first_priv vs first_search), Single value (suspicious sessions).
- **CIM Models:** Authentication

---

### 22.9 Compliance Trending

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk Add-on for ServiceNow (Splunkbase 1928), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Splunk DB Connect (Splunkbase 1556) for GRC database pulls.

**Data Sources:** `index=compliance` / `index=grc` (framework scores, control tests, audit findings), `sourcetype="compliance:framework_score"`, `sourcetype="grc:audit_finding"`, `sourcetype="compliance:control_test"`, `` `notable` `` (compliance-tagged incidents), `sourcetype="dlp:violation"` / `sourcetype="policy:enforcement"`, `sourcetype="qualys:policy"`, `sourcetype="nessus:sc:compliance"`, CIM (Authentication, Change) where policy events are normalized.

---

### UC-22.9.1 · Compliance Posture Score Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Rolling quarterly posture scores across NIST CSF, ISO 27001, and SOC 2 show whether investments in controls are improving measurable outcomes—not just checkbox activity—so executives and regulators see trajectory, not a one-time snapshot.
- **App/TA:** Splunk DB Connect (GRC export), custom HTTP poller, or indexed CSV from Archer/ServiceNow GRC
- **Data Sources:** `index=compliance` OR `index=grc` `sourcetype IN ("compliance:framework_score","grc:posture")` — fields `framework`, `overall_score`, `_time`
- **SPL:**
```spl
index=compliance OR index=grc sourcetype IN ("compliance:framework_score","grc:posture") earliest=-730d
| eval fw=case(
    like(framework,"%NIST%"),"NIST_CSF",
    like(framework,"%ISO%"),"ISO27001",
    like(framework,"%SOC%"),"SOC2",
    1=1,framework)
| where isnum(overall_score)
| bin _time span=90d
| stats avg(overall_score) as avg_score by _time, fw
| stats avg(avg_score) as portfolio_score by _time
| timechart span=90d avg(portfolio_score) as avg_portfolio_score
| trendline sma3(avg_portfolio_score) as sma_posture
| predict avg_portfolio_score as posture_forecast algorithm=LLP future_timespan=2 period=4
```
```spl
index=compliance OR index=grc sourcetype IN ("compliance:framework_score","grc:posture") earliest=-730d
| eval fw=case(like(framework,"%NIST%"),"NIST_CSF",like(framework,"%ISO%"),"ISO27001",like(framework,"%SOC%"),"SOC2",1=1,framework)
| timechart span=3mon avg(overall_score) as avg_score by fw
| trendline sma2(NIST_CSF) as roll_NIST_CSF sma2(ISO27001) as roll_ISO27001 sma2(SOC2) as roll_SOC2
```
- **Implementation:** (1) Land GRC or continuous-control scores into `compliance` or `grc` with stable `framework` labels and numeric `overall_score` (0–100); (2) align calendar quarters to your audit cycle (`span=90d` vs fiscal); (3) schedule weekly and snapshot results to a summary index for year-over-year evidence; (4) validate `predict` against low-volume series—disable or widen `period` if confidence bands explode; (5) pair the portfolio panel with the by-framework panel for board-ready trending.
- **Visualization:** Line or area chart (portfolio score, `sma_posture`, `posture_forecast`), multiseries line (scores by `fw`), overlay confidence bands from `predict`.
- **CIM Models:** N/A

---

### UC-22.9.2 · Audit Finding Closure Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Trending open versus closed audit findings over ninety days makes backlog and closure velocity visible before external audits, while mean time to remediate highlights whether remediation playbooks and ownership are working.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk DB Connect for GRC findings, or custom `grc:audit_finding` HEC
- **Data Sources:** `index=grc` OR `index=compliance` `sourcetype="grc:audit_finding"` — `finding_id`, `status`, `closed_time` or `remediated_time`, `_time`
- **SPL:**
```spl
index=grc OR index=compliance sourcetype="grc:audit_finding" earliest=-90d
| eval is_closed=if(match(status,"(?i)closed|resolved|verified"),1,0)
| eval finding_key=coalesce(finding_id,uuid,ticket_id,number)
| timechart span=1d dc(eval(if(is_closed=0,finding_key,null()))) as open_findings
    dc(eval(if(is_closed=1,finding_key,null()))) as distinct_closed_entities
| trendline sma7(open_findings) as open_smoothed
| predict open_findings as open_forecast algorithm=LLP future_timespan=14
```
```spl
index=grc OR index=compliance sourcetype="grc:audit_finding" earliest=-90d
| eval is_closed=if(match(status,"(?i)closed|resolved|verified"),1,0)
| where is_closed=1
| eval mttr_days=if(isnotnull(closed_time),(closed_time-_time)/86400,
    if(isnotnull(remediated_time),(remediated_time-_time)/86400,null()))
| where isnum(mttr_days) AND mttr_days>=0 AND mttr_days<365
| timechart span=1w avg(mttr_days) as mean_mttr_days perc95(mttr_days) as p95_mttr_days
| trendline sma4(mean_mttr_days) as mttr_trend
| streamstats window=2 global=f first(mean_mttr_days) as prev_w_mttr
| eval wow_mttr_pct=if(isnotnull(prev_w_mttr) AND prev_w_mttr>0,round(100*(mean_mttr_days-prev_w_mttr)/prev_w_mttr,1),null())
| predict mean_mttr_days as mttr_forecast algorithm=LLP future_timespan=2
```
- **Implementation:** (1) Ensure each finding emits at least one event with stable `finding_key` and transition events or daily snapshots for `status`; (2) normalize `closed_time` to epoch seconds; (3) if only snapshot data exists, switch `dc()` panels to `latest()` by key in a summary index; (4) alert when `open_forecast` rises week over week or when `mean_mttr_days` exceeds your SLA; (5) export MTTR trend for audit workpapers.
- **Visualization:** Dual-axis line (open vs closed counts), area chart (`open_smoothed`), line chart (`mean_mttr_days`, `mttr_trend`, `mttr_forecast`), single value (`wow_mttr_pct`).
- **CIM Models:** N/A

---

### UC-22.9.3 · Control Effectiveness Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** A ninety-day pass ratio by control domain exposes domains where tests are failing more often or trending down—so you prioritize control owners, evidence collection, and automation before a failed external assessment.
- **App/TA:** Splunk Add-on for Tenable (Splunkbase 4060) for scan-based control checks, DB Connect for ITGC spreadsheets, or `compliance:control_test` automation feeds
- **Data Sources:** `index=compliance` `sourcetype IN ("compliance:control_test","nessus:sc:compliance","qualys:policy")` — `control_domain`, `test_result` or `status`, `_time`
- **SPL:**
```spl
index=compliance sourcetype IN ("compliance:control_test","nessus:sc:compliance","qualys:policy") earliest=-90d
| eval outcome=if(match(coalesce(test_result,status,result),"(?i)pass|passed|success|green"),1,0)
| eval domain=coalesce(control_domain,pluginFamily,"UNCLASSIFIED")
| bin _time span=7d
| stats count as tests, sum(outcome) as passes by _time, domain
| eval pass_ratio=if(tests>0, round(100*passes/tests, 2), null())
| sort domain, _time
| streamstats window=4 avg(pass_ratio) as eff_trend by domain
| table _time, domain, tests, pass_ratio, eff_trend
```
```spl
index=compliance sourcetype IN ("compliance:control_test","nessus:sc:compliance") earliest=-90d
| eval outcome=if(match(coalesce(test_result,status),"(?i)pass|passed|success"),1,0)
| bin _time span=7d
| stats count as tests, sum(outcome) as passes by _time
| eval org_pass_ratio=if(tests>0, round(100*passes/tests,2), null())
| sort _time
| trendline sma3(org_pass_ratio) as ratio_trend
| eventstats mean(org_pass_ratio) as portfolio_mean
| eval gap=round(org_pass_ratio-portfolio_mean,2)
| predict org_pass_ratio as ratio_forecast algorithm=LLP future_timespan=2 period=6
```
- **Implementation:** (1) Map vendor fields (`pluginFamily`, Qualys title) to internal `control_domain` via lookup `control_domain_map.csv`; (2) dedupe repeated tests per asset/control daily to avoid skew; (3) review domains where `eff_*` slopes negative for four consecutive buckets; (4) tune `span=7d` to match test frequency; (5) store weekly CSV exports for assessors.
- **Visualization:** Multiseries line or area (pass_ratio by domain), heatmap (domain x week), line (`org_pass_ratio`, `ratio_trend`, `ratio_forecast`).
- **CIM Models:** Vulnerabilities (when Tenable/Qualys maps to CIM); otherwise N/A

---

### UC-22.9.4 · Regulatory Incident Response Time Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1048, T1562
- **Value:** Mean time to resolve compliance-tagged incidents by quarter proves that regulatory and policy breaches are handled with discipline—supporting supervisory expectations and internal KPIs beyond generic IT MTTR.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263)
- **Data Sources:** `` `notable` `` — filter with `tag`/`category`/`rule_name` for compliance/regulatory work; fields `closed_time`, `_time`
- **SPL:**
```spl
`notable` earliest=-730d (tag="compliance" OR category="*compliance*" OR rule_name="*regulatory*" OR like(rule_name,"%compliance%"))
| eval mttr_sec=if(isnotnull(closed_time) AND closed_time>_time, closed_time-_time, null())
| where isnotnull(mttr_sec)
| timechart span=90d avg(mttr_sec) as avg_mttr_sec perc95(mttr_sec) as p95_mttr_sec
| eval avg_mttr_h=avg_mttr_sec/3600
| trendline sma2(avg_mttr_sec) as mttr_trend
| streamstats window=2 global=f first(avg_mttr_sec) as prev_q_mttr
| eval vs_prev_q_pct=if(isnotnull(prev_q_mttr) AND prev_q_mttr>0,round(100*(avg_mttr_sec-prev_q_mttr)/prev_q_mttr,1),null())
| predict avg_mttr_sec as mttr_forecast algorithm=LLP future_timespan=2 period=4
```
- **Implementation:** (1) Define a consistent ES tag or naming convention for regulatory notables; (2) confirm `closed_time` population for closed incidents (`| fieldsummary closed_time`); (3) exclude false positives with a lookup of excluded `rule_name` values; (4) compare quarterly MTTR to IT-wide MTTR in a separate panel for context; (5) document scope (which jurisdictions or policies) in the dashboard subtitle.
- **Visualization:** Line chart (`avg_mttr_h` or `avg_mttr_sec`, `mttr_trend`, `mttr_forecast`), column chart (`p95_mttr_sec` by quarter), single value (`vs_prev_q_pct`).
- **CIM Models:** N/A

---

### UC-22.9.5 · Policy Violation Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **MITRE ATT&CK:** T1078, T1562
- **Value:** Quarterly violation counts by category—data handling, access, encryption—show whether policy drift, training gaps, or technical misconfigurations are improving or worsening, which steers awareness campaigns and control investments.
- **App/TA:** Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Splunk Add-on for Windows (Splunkbase 742), Enterprise Security data models
- **Data Sources:** `index=compliance` OR `index=sec` `sourcetype IN ("dlp:violation","policy:enforcement","ms:o365:management")` — `violation_category`, `PolicyName`, `Workload`; optional `sourcetype="qualys:*"` / `sourcetype="nessus:*"` for encryption posture drift correlated to policy
- **SPL:**
```spl
index=compliance OR index=sec sourcetype IN ("dlp:violation","policy:enforcement") earliest=-730d
| eval cat=case(
    match(_raw,"(?i)encrypt|crypto|tls|bitlocker"),"encryption",
    match(_raw,"(?i)access|privileged|login|permission"),"access",
    match(_raw,"(?i)dlp|classification|label"),"data_handling",
    1=1,coalesce(violation_category,"other"))
| bin _time span=90d
| stats count by _time, cat
| sort cat, _time
| streamstats window=2 avg(count) as cat_trend by cat
| eventstats sum(count) as quarter_total by _time
| sort _time, cat
| table _time, cat, count, cat_trend, quarter_total
```
```spl
index=o365 sourcetype="ms:o365:management" Workload IN ("Dlp","Security") earliest=-730d
| eval cat=case(
    like(Operation,"%encryption%") OR like(SensitiveInfoType,"%encryption%"),"encryption",
    match(Operation,"(?i)login|access|role"),"access",
    1=1,"data_handling")
| bin _time span=90d
| stats count by _time, cat
| sort cat, _time
| streamstats window=2 avg(count) as o365_trend by cat
| table _time, cat, count, o365_trend
```
```spl
index=o365 sourcetype="ms:o365:management" Workload IN ("Dlp","Security") earliest=-730d
| timechart span=90d count as o365_violation_total
| trendline sma2(o365_violation_total) as o365_trend
| predict o365_violation_total as o365_fcst algorithm=LLP future_timespan=2
```
```spl
index=vm OR index=compliance sourcetype IN ("nessus:sc:*","qualys:host") earliest=-730d
| eval enc_gap=if(match(_raw,"(?i)ssl|tls|cipher|encrypt") AND match(_raw,"(?i)fail|weak|deprecated"),1,0)
| timechart span=90d sum(enc_gap) as encryption_policy_gaps
| trendline sma3(encryption_policy_gaps) as enc_trend
| predict encryption_policy_gaps as enc_fcst algorithm=LLP future_timespan=2
```
- **Implementation:** (1) Normalize DLP and CASB events into shared `violation_category` values via `case` or lookup; (2) align `span=90d` to fiscal or regulatory reporting quarters; (3) correlate spikes with change tickets (`index=itsm`) using `join` on `_time` windows; (4) use the total-violations panel (`o365_violation_total`) when category columns are too sparse for `predict`; (5) retain quarterly PDF snapshots for compliance archives.
- **Visualization:** Stacked column or area (counts by `cat` over time), line (`o365_violation_total`, `o365_trend`, `o365_fcst`), line (`encryption_policy_gaps`, `enc_trend`), heatmap (category x quarter).
- **CIM Models:** N/A

---
