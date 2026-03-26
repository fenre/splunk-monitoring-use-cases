## 22. Regulatory and Compliance Frameworks

### 22.1 GDPR

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110), Splunk Add-on for Stream (Splunkbase 1809), Splunk Add-on for Microsoft SQL Server (Splunkbase 2648), Splunk Add-on for Oracle Database (Splunkbase 1910), Splunk DB Connect (Splunkbase 2686), Splunk Edge Processor (Splunk Cloud Platform), Splunk Common Information Model Add-on (Splunkbase 1621).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities, Certificates, Change), database audit logs (`mssql:audit`, `oracle:audit`, `postgres:csv`), TLS/certificate metadata (Splunk Stream), consent management platform events (HEC), automated decision system audit logs (HEC), Splunk audit logs (`_audit`, `_internal`), GDPR register lookups (`gdpr_ropa_register.csv`, `gdpr_dpia_register.csv`, `gdpr_processor_register.csv`, `gdpr_lia_register.csv`).

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

**Primary App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk Add-on for Microsoft Windows (Splunkbase 742), Splunk Add-on for Microsoft Office 365 (Splunkbase 4055), Tenable Add-On for Splunk (Splunkbase 4060), Splunk Add-on for AWS (Splunkbase 1876), Splunk Add-on for Microsoft Cloud Services (Splunkbase 3110).

**Data Sources:** ES Notable events (`` `notable` `` macro), ES Risk framework (`index=risk`), ITSI service health (`index=itsi_summary`), Windows Security Event Logs (`WinEventLog:Security`), ServiceNow ITSM records (`snow:sc_req_item`), Tenable vulnerability scans (`tenable:vuln`), AWS CloudTrail (`aws:cloudtrail`), Microsoft 365 DLP (`ms:o365:management`), CIM data models (Authentication, Network_Traffic, Vulnerabilities), Splunk audit logs (`_audit`, `_internal`).

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
