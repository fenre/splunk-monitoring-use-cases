## 11. Email & Collaboration

### 11.1 Microsoft 365 / Exchange

**Primary App/TA:** Splunk Add-on for Microsoft Office 365 (`Splunk_TA_MS_O365`), Splunk Add-on for Microsoft Exchange.

---

### UC-11.1.1 · Mail Flow Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Deferred or failed message traces directly hit revenue-dependent communications and support SLAs. Sustained delivery failure spikes should drive incident severity classification and trigger customer communication templates before users report the issue.
- **App/TA:** `Splunk_TA_MS_O365`, Exchange message tracking
- **Data Sources:** Exchange message tracking logs, O365 message trace
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:messageTrace"
| timechart span=1h count by Status
```
- **Implementation:** Ingest O365 message trace data via the Splunk Add-on for Microsoft Cloud Services (`sourcetype=ms:o365:messageTrace`). Key fields: `Status`, `RecipientStatus`, `SenderAddress`. Alert when the Failed/Deferred percentage exceeds the 14-day same-hour median, split by connector vs DNS vs policy rejection for targeted triage.
- **Visualization:** Line chart (message volume by status), Single value (delivery success rate), Bar chart (top NDR reasons).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-11.1.2 · Mailbox Audit Logging
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks who accesses what mailboxes, including delegate and admin access. Essential for insider threat detection and compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 unified audit log (ExchangeItem events)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Exchange" Operation IN ("MailItemsAccessed","Send","SendAs")
| stats count by UserId, Operation, MailboxOwnerUPN
| where UserId!=MailboxOwnerUPN
```
- **Implementation:** Enable mailbox audit logging in Exchange Online. Ingest via O365 Management Activity API. Alert on non-owner access to sensitive mailboxes. Track delegate activity. Monitor SendAs events for potential impersonation.
- **Visualization:** Table (non-owner mailbox access), Bar chart (access by user), Timeline (audit events).
- **CIM Models:** N/A

---

### UC-11.1.3 · Exchange Online Protection Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** EOP filtering metrics show email threat landscape and security control effectiveness.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** EOP message trace, threat protection status
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:messageTrace"
| eval threat_type=case(match(FilteringResult,"Spam"),"Spam", match(FilteringResult,"Phish"),"Phishing", match(FilteringResult,"Malware"),"Malware", 1=1,"Clean")
| stats count by threat_type
```
- **Implementation:** Ingest O365 message trace data. Classify messages by EOP verdict. Track filtering rates over time. Report on threat types and volumes. Alert on phishing/malware volume spikes.
- **Visualization:** Pie chart (message classification), Line chart (threat volume trend), Bar chart (top blocked senders).
- **CIM Models:** N/A

---

### UC-11.1.4 · Teams Usage Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Teams adoption and quality metrics inform collaboration strategy and help identify user experience issues.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** M365 Teams activity reports, Teams call quality data
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="MicrosoftTeams"
| stats count by Operation
| sort -count
```
- **Implementation:** Ingest Teams activity reports via Graph API. Track meetings, messages, calls, and file sharing volumes. Monitor call quality metrics (jitter, packet loss). Report on adoption trends per department.
- **Visualization:** Line chart (Teams activity trend), Bar chart (activity by type), Table (call quality issues).
- **CIM Models:** N/A

---

### UC-11.1.5 · SharePoint/OneDrive Sharing Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** External sharing can expose sensitive data. Audit trail ensures data protection and compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (SharingSet, AnonymousLinkCreated)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="SharePoint" Operation IN ("SharingSet","AnonymousLinkCreated","CompanyLinkCreated")
| where TargetUserOrGroupType="Guest" OR Operation="AnonymousLinkCreated"
| table _time, UserId, Operation, ObjectId, TargetUserOrGroupName
```
- **Implementation:** Ingest SharePoint/OneDrive audit events. Alert on external sharing (guest users, anonymous links). Track sharing activity per user. Flag sharing of sensitive files or sites. Report for data governance reviews.
- **Visualization:** Table (external sharing events), Bar chart (sharing by user), Line chart (sharing trend), Pie chart (sharing type distribution).
- **CIM Models:** N/A

---

### UC-11.1.6 · DLP Policy Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** M365 DLP policy matches across email, Teams, SharePoint identify sensitive data exposure. Centralized tracking supports compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 DLP logs
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInfoType
| sort -count
```
- **Implementation:** Configure M365 DLP policies. Ingest DLP events. Track violations by policy, user, and data type. Alert on high-severity matches. Produce compliance reports for regulated data (PII, PCI, HIPAA).
- **Visualization:** Bar chart (violations by policy), Table (top violators), Line chart (violation trend).
- **CIM Models:** N/A

---

### UC-11.1.7 · Admin Activity Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** M365 admin actions (user creation, license changes, policy modifications) need audit trails for compliance and security.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (admin operations)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" RecordType=1
| table _time, UserId, Operation, ObjectId, ResultStatus
| sort -_time
```
- **Implementation:** Ingest O365 admin audit log. Track admin operations by administrator. Alert on sensitive operations (user creation, role changes, policy modifications). Correlate with change management tickets.
- **Visualization:** Table (admin activities), Timeline (admin events), Bar chart (actions by admin).
- **CIM Models:** N/A

---

### UC-11.1.8 · Inbox Rule Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Malicious inbox rules (auto-forward to external, auto-delete) are a key post-compromise technique for data exfiltration.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (New-InboxRule, Set-InboxRule)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Operation IN ("New-InboxRule","Set-InboxRule")
| spath output=forward Parameters{}.Value
| search forward="*@*" NOT forward="*@yourdomain.com"
| table _time, UserId, Operation, forward
```
- **Implementation:** Monitor inbox rule creation events. Alert on rules that forward to external addresses, delete messages, or move to uncommon folders. These are high-confidence indicators of account compromise. Trigger immediate investigation.
- **Visualization:** Table (suspicious inbox rules), Single value (external forwarding rules — target: 0), Timeline (rule creation events).
- **CIM Models:** N/A

---

### UC-11.1.9 · Service Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** M365 service incidents affect all users. Early awareness from API enables proactive communication and workaround planning.
- **App/TA:** Custom API input (M365 Service Health API)
- **Data Sources:** M365 Service Health API
- **SPL:**
```spl
index=m365 sourcetype="m365:servicehealth"
| where status!="ServiceOperational"
| table _time, service, status, title, classification
```
- **Implementation:** Poll M365 Service Health API every 5 minutes. Alert on service degradations and incidents. Track incident duration and frequency. Correlate with internal ticket volumes to measure user impact.
- **Visualization:** Status grid (service × health), Table (active incidents), Timeline (incident history).
- **CIM Models:** N/A

---

### UC-11.1.10 · License Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** M365 license costs are significant. Tracking utilization identifies unused licenses for reallocation and cost savings.
- **App/TA:** Custom API input (M365 Reports API)
- **Data Sources:** M365 license assignment and usage reports
- **SPL:**
```spl
index=m365 sourcetype="m365:licenses"
| stats sum(assigned) as assigned, sum(consumed) as consumed by sku_name
| eval utilization_pct=round(consumed/assigned*100,1)
| table sku_name, assigned, consumed, utilization_pct
```
- **Implementation:** Poll M365 license reports via Graph API weekly. Track assigned vs consumed licenses per SKU. Identify inactive users (no activity in 90 days with assigned license). Report on cost optimization opportunities.
- **Visualization:** Table (license utilization), Gauge (% utilized per SKU), Bar chart (unused licenses by SKU).
- **CIM Models:** N/A

---

### UC-11.1.11 · Exchange Message Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Hub transport queue length indicates mail flow issues. Messages stuck in queue cause delivery delays, NDRs, and user complaints. Growing queues often precede transport service failures.
- **App/TA:** `Splunk_TA_windows` (perfmon), custom scripted input
- **Data Sources:** Exchange Transport Queue counters (MSExchangeTransport Queues), Get-Queue PowerShell output
- **SPL:**
```spl
(index=perfmon object="MSExchangeTransport Queues") OR (index=exchange sourcetype="exchange:queue_depth")
| eval queue_depth=coalesce(QueueLength, MessageCount, 0)
| where queue_depth > 0
| bin _time span=15m
| stats latest(queue_depth) as current_depth, max(queue_depth) as peak_depth, avg(queue_depth) as avg_depth by _time, host, QueueName
| where current_depth > 100 OR peak_depth > 500
| sort -current_depth
| table _time, host, QueueName, current_depth, peak_depth, avg_depth
```
- **Implementation:** Configure Splunk_TA_windows to collect MSExchangeTransport Queues perfmon counters (QueueLength, MessageCount) from Exchange servers every 60 seconds. Alternatively, run a scheduled script that executes `Get-Queue` and outputs JSON to Splunk via HEC or scripted input. Map QueueName to delivery type (Submission, Poison, Unreachable). Alert when any queue exceeds 100 messages (warning) or 500 (critical). Correlate queue spikes with transport service restarts and network issues.
- **Visualization:** Line chart (queue depth over time by queue), Single value (max queue depth), Table (queues exceeding threshold), Bar chart (peak depth by server).
- **CIM Models:** N/A

---

### UC-11.1.12 · Exchange Database Copy Queue Length
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** DAG replication lag measured in number of log files. Growing copy queue risks data loss on failover and indicates replication or disk I/O issues. Replay queue lag affects failover time.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** Get-MailboxDatabaseCopyStatus (CopyQueueLength, ReplayQueueLength)
- **SPL:**
```spl
index=exchange sourcetype="exchange:dag_status"
| eval copy_queue=coalesce(CopyQueueLength, copyQueueLength, 0), replay_queue=coalesce(ReplayQueueLength, replayQueueLength, 0)
| where copy_queue > 10 OR replay_queue > 50
| bin _time span=15m
| stats latest(copy_queue) as copy_queue_len, latest(replay_queue) as replay_queue_len, latest(Status) as status by _time, host, DatabaseName, MailboxServer
| where copy_queue_len > 10 OR replay_queue_len > 50
| sort -copy_queue_len
| table _time, host, DatabaseName, MailboxServer, copy_queue_len, replay_queue_len, status
```
- **Implementation:** Run a PowerShell script every 5–15 minutes that executes `Get-MailboxDatabaseCopyStatus | Select-Object DatabaseName, MailboxServer, CopyQueueLength, ReplayQueueLength, Status` and forwards results to Splunk via HEC. Normalize field names (CopyQueueLength vs copyQueueLength). Alert when CopyQueueLength > 10 (warning) or > 50 (critical), or ReplayQueueLength > 50. Track per-database and per-server. Correlate with disk latency and network metrics.
- **Visualization:** Line chart (copy/replay queue over time by database), Table (lagging copies), Single value (max copy queue), Heat map (database × server queue status).
- **CIM Models:** N/A

---

### 11.2 Google Workspace

**Primary App/TA:** Splunk Add-on for Google Workspace (`Splunk_TA_GoogleWorkspace`).

---

### UC-11.2.1 · Admin Console Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Admin actions in Google Workspace affect all users. Audit trail supports compliance and detects unauthorized changes.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace Admin audit log
- **SPL:**
```spl
index=gws sourcetype="gws:admin" event_name IN ("CREATE_USER","DELETE_USER","CHANGE_ADMIN_ROLE")
| table _time, actor.email, event_name, target_user
```
- **Implementation:** Configure Google Workspace TA to ingest admin audit logs via Reports API. Track user management, policy changes, and configuration modifications. Alert on sensitive operations (role changes, 2FA disablement).
- **Visualization:** Table (admin events), Timeline (admin activity), Bar chart (events by admin).
- **CIM Models:** N/A

---

### UC-11.2.2 · Gmail Message Flow
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Email delivery monitoring and DLP enforcement protects sensitive data and ensures business communication reliability.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Gmail logs via BigQuery export or Reports API
- **SPL:**
```spl
index=gws sourcetype="gws:gmail"
| stats count by message_info.disposition
| eval pct=round(count/sum(count)*100,1)
```
- **Implementation:** Ingest Gmail logs. Track message delivery rates, spam filtering effectiveness, and DLP triggers. Alert on delivery failures or increased spam rates. Report on email security posture.
- **Visualization:** Pie chart (message disposition), Line chart (message volume), Table (DLP triggers).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-11.2.3 · Drive Sharing Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Unusual file sharing patterns may indicate data exfiltration or accidental exposure of sensitive documents.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Drive audit log
- **SPL:**
```spl
index=gws sourcetype="gws:drive" event_name="change_user_access"
| where new_value="people_with_link" OR target_user_email NOT LIKE "%@yourdomain.com%"
| table _time, actor.email, doc_title, target_user_email, new_value
```
- **Implementation:** Ingest Drive audit logs. Alert on external sharing, "anyone with link" sharing, and bulk sharing events. Track sharing patterns per user. Flag sharing of sensitive folders or documents.
- **Visualization:** Table (sharing events), Bar chart (external sharing by user), Line chart (sharing activity trend).
- **CIM Models:** N/A

---

### UC-11.2.4 · Login Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Suspicious login activity (new device, unusual location, failed MFA) indicates potential account compromise.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace login audit log
- **SPL:**
```spl
index=gws sourcetype="gws:login" event_name="login_failure"
| stats count by actor.email, ip_address
| where count > 5
```
- **Implementation:** Ingest login audit logs. Track failed logins, new device registrations, and unusual locations. Alert on multiple failures, suspicious activity events, and login from new countries. Correlate with Google's built-in risk signals.
- **Visualization:** Table (suspicious logins), Geo map (login locations), Line chart (failure rate), Bar chart (failures by user).
- **CIM Models:** N/A

---

### UC-11.2.5 · Meet Quality Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Poor meeting quality impacts productivity and user satisfaction. Monitoring enables network/infrastructure optimization.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Meet quality logs
- **SPL:**
```spl
index=gws sourcetype="gws:meet"
| where video_recv_jitter_ms > 30 OR audio_recv_jitter_ms > 30
| stats count, avg(video_recv_jitter_ms) as avg_jitter by organizer_email, meeting_code
```
- **Implementation:** Ingest Meet quality data. Track jitter, latency, and packet loss per meeting. Alert on recurring poor quality for specific users or locations. Correlate with network performance data.
- **Visualization:** Table (poor quality meetings), Line chart (quality metrics trend), Bar chart (issues by location).
- **CIM Models:** N/A

---

### UC-11.2.6 · Third-Party App Access
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** OAuth app grants to third-party applications create data access risks. Monitoring enables governance and risk assessment.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace token audit log
- **SPL:**
```spl
index=gws sourcetype="gws:token" event_name="authorize"
| stats dc(actor.email) as unique_users by app_name, scope
| sort -unique_users
```
- **Implementation:** Ingest token audit logs. Track OAuth grants by application and scope. Identify high-risk scopes (full Drive access, Gmail read). Alert on new third-party apps accessing sensitive scopes. Report for governance review.
- **Visualization:** Table (third-party apps with scope), Bar chart (apps by user count), Pie chart (scope distribution).
- **CIM Models:** N/A

---

### UC-11.2.7 · Drive External Sharing Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Alerts on files and folders shared outside the primary domain or with `anyone with link`—complements anomaly baselines (UC-11.2.3).
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Drive audit log (`change_user_access`, `shared_drive_settings_change`)
- **SPL:**
```spl
index=gws sourcetype="gws:drive" event_name="change_user_access"
| where new_value="people_with_link" OR NOT match(target_user_email, ".*@yourdomain\\.com")
| table _time, actor.email, doc_title, target_user_email, new_value
| sort -_time
```
- **Implementation:** Tune domain pattern via lookup. Alert on shares to competitor domains or public links on confidential folders (path regex).
- **Visualization:** Table (external shares), Bar chart (domains), Timeline.
- **CIM Models:** N/A

---

### UC-11.2.8 · Admin Console Audit (Security Settings)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Focused on security-sensitive admin events (2SV, SSO, API keys)—extends general admin audit (UC-11.2.1).
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Admin audit (`CHANGE_APPLICATION_SETTING`, `CHANGE_TWO_STEP_VERIFICATION_ENROLLMENT`, `CREATE_ROLE`, `ASSIGN_ROLE`)
- **SPL:**
```spl
index=gws sourcetype="gws:admin"
| search event_name IN ("CHANGE_APPLICATION_SETTING","CHANGE_TWO_STEP_VERIFICATION_ENROLLMENT","CREATE_ROLE","ASSIGN_ROLE","AUTHORIZE_API_CLIENT_ACCESS")
| table _time, actor.email, event_name, target_user, setting_name
| sort -_time
```
- **Implementation:** Alert on SSO IdP changes, 2SV exemptions, and new OAuth client authorizations. Correlate actor with known break-glass accounts.
- **Visualization:** Timeline (security admin events), Table (actor, event), Single value (critical events 24h).
- **CIM Models:** Change

---

### UC-11.2.9 · Gmail Suspicious Forwarding
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects auto-forwarding and delegation to external addresses—common post-compromise behavior.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Email settings audit (`CHANGE_EMAIL_SETTING`, Gmail routing / forwarding flags in Reports API export)
- **SPL:**
```spl
index=gws sourcetype="gws:admin" event_name="CHANGE_EMAIL_SETTING"
| search forward OR delegate OR filter
| where NOT match(setting_value, ".*@yourdomain\\.com")
| table _time, actor.email, target_user, setting_name, setting_value
```
- **Implementation:** Ingest email settings changes. Alert on new forwarding to non-corporate domains. Weekly report of active forwards from `gmail:user_settings` export.
- **Visualization:** Table (forwarding changes), Single value (external forwards), Timeline.
- **CIM Models:** N/A

---

### UC-11.2.10 · Chrome Management Policy Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Managed Chrome browsers should enforce updates, extensions allowlists, and safe browsing; drift indicates unmanaged or tampered clients.
- **App/TA:** `Splunk_TA_GoogleWorkspace`, Chrome Browser Cloud Management events
- **Data Sources:** Chrome policy audit events, device reports (`chromeosdevices` / `managed_browser`)
- **SPL:**
```spl
index=gws sourcetype="gws:chrome_management" OR sourcetype="gws:admin" event_name="CHROME_DEVICES_POLICY_UPDATE"
| stats latest(policy_version) as ver, latest(compliance_state) as state by device_id, org_unit
| where state!="COMPLIANT" OR isnull(ver)
| table device_id, org_unit, state, ver
```
- **Implementation:** Ingest Chrome Enterprise Connector or admin audit for policy pushes. Alert on devices not checking in >7 days. Map OUs to sensitivity.
- **Visualization:** Table (non-compliant browsers), Bar chart (by OU), Line chart (compliance %).
- **CIM Models:** Endpoint

---

### UC-11.2.11 · Google Vault Hold Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Hold creation, release, and matter changes affect legal preservation; errors risk spoliation findings.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Vault audit (`CREATE_HOLD`, `DELETE_HOLD`, `UPDATE_HOLD`, `CREATE_MATTER`)
- **SPL:**
```spl
index=gws sourcetype="gws:vault" OR (sourcetype="gws:admin" event_name="VAULT_*")
| table _time, actor.email, event_name, matter_id, hold_name
| sort -_time
```
- **Implementation:** Forward Vault audit to Splunk. Restrict alerts to legal-team actors; flag hold deletions without ticket ID in custom field.
- **Visualization:** Timeline (hold changes), Table (matters affected), Single value (hold deletions 90d).
- **CIM Models:** N/A

---

### UC-11.2.12 · Workspace Marketplace App Review
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** New marketplace app installs can expose Drive/Gmail data; tracks installs and OAuth scopes.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Token audit (`authorize`), admin audit (`ADD_APPLICATION`, `INSTALL_MARKETPLACE_APP`)
- **SPL:**
```spl
index=gws sourcetype="gws:token" event_name="authorize"
| stats values(scope) as scopes by app_name, actor.email
| mvexpand scopes limit=500
| search scopes="https://www.googleapis.com/auth/drive*" OR scopes="*gmail*"
| sort app_name
```
- **Implementation:** Maintain allowlist of approved apps. Alert on new apps with sensitive scopes. Quarterly access review with app owners.
- **Visualization:** Table (high-risk grants), Bar chart (apps by user count), Pie chart (scope categories).
- **CIM Models:** N/A

---

### UC-11.2.13 · Groups Membership Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Sensitive Google Groups (all-staff, external partners) membership changes can broadly expose mail and Drive.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Groups audit (`ADD_GROUP_MEMBER`, `REMOVE_GROUP_MEMBER`, `CREATE_GROUP`)
- **SPL:**
```spl
index=gws sourcetype="gws:groups" OR (sourcetype="gws:admin" event_name="GROUP_*")
| search event_name IN ("ADD_GROUP_MEMBER","REMOVE_GROUP_MEMBER","CREATE_GROUP")
| lookup sensitive_groups.csv group_email OUTPUT tier
| where tier="high" OR like(group_email,"*external*")
| table _time, actor.email, event_name, group_email, member_email
```
- **Implementation:** Tag high-impact groups in lookup. Alert on adds to groups with external posting or shared drives.
- **Visualization:** Table (membership changes), Timeline, Bar chart (changes by group).
- **CIM Models:** Change

---

### UC-11.2.14 · Cloud Identity Device Management
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Endpoint visibility for mobile and desktop enrolled in Endpoint Verification / MDM—lost devices and OS drift.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Endpoint audit (`REGISTER_DEVICE`, `SYNC_DEVICE`), Reports API mobile devices
- **SPL:**
```spl
index=gws sourcetype="gws:endpoint" OR sourcetype="gws:mobile"
| where compliance_state!="COMPLIANT" OR device_compromised="true" OR status="LOST"
| stats count by device_id, user_email, compliance_state
| sort -count
```
- **Implementation:** Ingest device inventory daily. Alert on lost/stolen, rooted/jailbroken, or encryption-off. Integrate with Chrome management (UC-11.2.10).
- **Visualization:** Table (non-compliant devices), Map (last sync location if available), Line chart (fleet compliance %).
- **CIM Models:** Endpoint

---

### UC-11.2.15 · Google Meet Quality Metrics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Meet quality telemetry (packet loss, jitter, RTT) for troubleshooting conferencing issues—extends UC-11.2.5 with org-level rollups.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Meet quality tool export / BigQuery (`conference_records`, participant `score` metrics)
- **SPL:**
```spl
index=gws sourcetype="gws:meet_quality"
| where packet_loss_pct > 2 OR round_trip_time_ms > 300 OR jitter_ms > 35
| stats avg(packet_loss_pct) as avg_loss, avg(round_trip_time_ms) as avg_rtt by conference_id, organizer_email
| sort -avg_loss
```
- **Implementation:** Enable Meet quality logging in Admin. Ingest via BigQuery export or Reports API. Baseline per office ASN. Alert when median MOS proxy metrics exceed SLA.
- **Visualization:** Table (worst conferences), Line chart (loss/jitter trend), Bar chart (by network location).
- **CIM Models:** N/A

---

### UC-11.2.16 · Gmail Phishing Report Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** User-reported phishing provides ground-truth for tuning secure links and awareness; volume spikes indicate campaigns.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Email log (`PHISHING_REPORT`, user report button events in audit)
- **SPL:**
```spl
index=gws sourcetype="gws:gmail" event_name="PHISHING_REPORT"
| bin _time span=1h
| stats count by reporter, _time
| where count > 5
| sort -count
```
- **Implementation:** Ingest reported-message metadata (no body in Splunk if policy requires). Correlate with Postini/Workspace security dashboards. Feed SOC for IOC extraction.
- **Visualization:** Line chart (reports per hour), Table (top reporters), Bar chart (campaign hash if extracted).
- **CIM Models:** N/A

---

### UC-11.2.17 · Workspace DLP Rule Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Value:** Google Workspace DLP incidents for Drive, Gmail, Chat—centralized for compliance trending.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** DLP incident export (`rule_name`, `triggered_action`, `resource_type`)
- **SPL:**
```spl
index=gws sourcetype="gws:dlp"
| stats count by rule_name, severity, actor_email, data_source
| where severity IN ("HIGH","CRITICAL") OR count > 3
| sort -count
```
- **Implementation:** Schedule DLP API or BigQuery export of incidents. Map rules to data classes. Alert on exfiltration-blocked events to external domains.
- **Visualization:** Bar chart (violations by rule), Table (repeat offenders), Line chart (incident trend).
- **CIM Models:** DLP

---

### UC-11.2.18 · Google Takeout Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Takeout requests export large user datasets—strong indicator of insider risk or compromised account.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Admin audit (`REQUEST_DATA_EXPORT`, `DOWNLOAD_DATA_EXPORT`), login audit for takeout.google.com
- **SPL:**
```spl
index=gws sourcetype="gws:admin" event_name="REQUEST_DATA_EXPORT"
| table _time, actor.email, target_user, export_size_bytes, services_included
| sort -_time
```
- **Implementation:** Alert on any Takeout request for privileged users. Require HR/legal approval lookup for departing employees. Block self-service takeout for high-risk OUs via policy.
- **Visualization:** Table (export requests), Single value (exports 7d), Timeline.
- **CIM Models:** N/A

---

### 11.3 Unified Communications

**Primary App/TA:** Cisco UCM TA, Webex TA, custom CDR/CMR inputs for voice platforms.

---

### UC-11.3.1 · Call Quality Monitoring (MOS)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** MOS scores directly measure voice quality experience. Degradation impacts business communication and customer service.
- **App/TA:** Cisco UCM CDR/CMR, Webex API
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series, Cisco Webex Calling, Webex Meetings, Webex Room Kit, Webex Board, Webex Desk
- **Data Sources:** Call Detail Records (CDR), Call Management Records (CMR)
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cmr"
| where MOS < 3.5
| stats count, avg(MOS) as avg_mos by origDeviceName, destDeviceName
| sort avg_mos
```
- **Implementation:** Ingest CDR/CMR from UCM or cloud UC platform. Parse MOS, jitter, latency, and packet loss. Alert when MOS drops below 3.5 (fair quality). Correlate with network metrics to identify root cause. Track per-site quality.
- **Visualization:** Gauge (average MOS), Line chart (MOS trend), Table (poor quality calls), Heatmap (site × quality).
- **CIM Models:** N/A

---

### UC-11.3.2 · Call Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Call volume patterns support capacity planning and detect anomalies (toll fraud, system issues).
- **App/TA:** UCM CDR input
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** CDR records
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| timechart span=1h count as calls
| predict calls as predicted
```
- **Implementation:** Ingest CDR data. Track call volumes by hour, day, site. Baseline normal patterns. Alert on significant drops (possible outage) or spikes (possible toll fraud). Report on peak hour utilization.
- **Visualization:** Line chart (call volume with prediction), Bar chart (calls by site), Area chart (hourly distribution).
- **CIM Models:** N/A

---

### UC-11.3.3 · VoIP Jitter/Latency/Packet Loss
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Transport quality metrics identify network issues affecting voice quality before users report problems.
- **App/TA:** UCM CMR, RTCP data
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** CMR records (jitter, latency, packet loss), RTCP reports
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cmr"
| where jitter > 30 OR latency > 150 OR packet_loss_pct > 1
| stats count by origDeviceName, destDeviceName, jitter, latency, packet_loss_pct
```
- **Implementation:** Parse transport quality metrics from CMR. Alert on jitter >30ms, latency >150ms, or packet loss >1%. Correlate with WAN/LAN performance metrics. Track per-site to identify network segments needing attention.
- **Visualization:** Multi-metric chart (jitter, latency, packet loss), Table (calls with poor transport), Heatmap (site × metric).
- **CIM Models:** N/A

---

### UC-11.3.4 · Trunk Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Trunk capacity limits cause busy signals and missed calls. Monitoring prevents capacity-related service degradation.
- **App/TA:** UCM CDR, gateway logs
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** CDR records, gateway/trunk metrics
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| bin _time span=15m
| stats dc(globalCallID_callId) as concurrent_calls by _time, trunk_group
| where concurrent_calls > 20
```
- **Implementation:** Track concurrent calls per trunk group from CDR data. Alert when utilization exceeds 80% of capacity. Monitor for trunk failures and failover events. Report on peak utilization for capacity planning.
- **Visualization:** Line chart (trunk utilization), Gauge (% capacity per trunk), Table (trunk utilization summary).
- **CIM Models:** N/A

---

### UC-11.3.5 · Conference Bridge Capacity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Conference bridge resource exhaustion prevents users from joining meetings. Monitoring ensures adequate capacity.
- **App/TA:** Webex API, UCM conference bridge metrics
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series, Cisco Webex Calling, Webex Meetings, Webex Room Kit, Webex Board, Webex Desk
- **Data Sources:** Conference bridge utilization, Webex meeting data
- **SPL:**
```spl
index=voip sourcetype="webex:meetings"
| timechart span=1h max(concurrent_participants) as max_participants
| where max_participants > 500
```
- **Implementation:** Track conference bridge resource utilization and concurrent participant counts. Alert when approaching capacity limits. Monitor meeting quality metrics at scale. Report on peak usage patterns for capacity planning.
- **Visualization:** Line chart (concurrent participants), Single value (peak participants today), Bar chart (meetings by size).
- **CIM Models:** N/A

---

### UC-11.3.6 · Toll Fraud Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Toll fraud causes significant financial loss. International premium-rate calls from compromised systems can cost thousands per hour.
- **App/TA:** UCM CDR analysis
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** CDR records (called party number, duration, time of day)
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| where match(calledPartyNumber,"^011|^00") AND duration > 60
| stats count, sum(duration) as total_min by callingPartyNumber, calledPartyNumber
| where count > 10
| sort -total_min
```
- **Implementation:** Monitor CDR for international calls, premium-rate numbers (900, 976), and calls outside business hours. Baseline normal international calling patterns. Alert on anomalous patterns. Block suspicious numbers in real-time.
- **Visualization:** Table (suspicious calls), Bar chart (international calls by destination), Timeline (unusual calling activity), Geo map (call destinations).
- **CIM Models:** N/A

---

### UC-11.3.7 · Phone Registration Status
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Mass phone de-registration indicates network or UCM issues affecting the entire communications infrastructure.
- **App/TA:** UCM syslog, RISPORT API
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** UCM device status, RISPORT real-time data
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:syslog"
| search "DeviceUnregistered" OR "StationDeregister"
| timechart span=5m count as deregistrations
| where deregistrations > 10
```
- **Implementation:** Poll UCM RISPORT API for device registration status or forward UCM syslog. Alert on mass de-registrations (>10 devices in 5 minutes). Track registration counts per site. Monitor SRST fallback activations.
- **Visualization:** Single value (registered phones), Line chart (registration count trend), Table (recently de-registered devices).
- **CIM Models:** N/A

---

### UC-11.3.8 · Webex Meeting Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Meeting analytics support collaboration optimization, license management, and quality improvement initiatives.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub)
- **Equipment Models:** Cisco Webex Calling, Webex Meetings, Webex Room Kit, Webex Board, Webex Desk
- **Data Sources:** Webex meeting/participant data via API
- **SPL:**
```spl
index=webex sourcetype="webex:meetings"
| stats count as meetings, avg(participant_count) as avg_participants, avg(duration_min) as avg_duration by organizerEmail
| sort -meetings
```
- **Implementation:** Poll Webex API for meeting data. Track meeting counts, participants, duration, and quality. Report on adoption metrics per department. Identify power users and underutilized licenses.
- **Visualization:** Bar chart (meetings by department), Line chart (meeting volume trend), Table (usage summary), Pie chart (meeting types).
- **CIM Models:** N/A

---

### UC-11.3.9 · Mailbox Size and Quota Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Mailbox growth and quota usage help plan storage and avoid user lockouts. Trending supports capacity planning and proactive quota increases.
- **App/TA:** Exchange Online / M365 reporting, mailbox stats API
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** Mailbox size and quota metrics
- **SPL:**
```spl
index=o365 sourcetype="exchange:mailbox_stats"
| stats latest(mailbox_size_mb) as size_mb, latest(quota_mb) as quota_mb by user, mailbox_type
| eval used_pct=round((size_mb/quota_mb)*100, 1)
| where used_pct >= 80
| sort -used_pct
```
- **Implementation:** Ingest mailbox size and quota from Graph API or Exchange reporting. Alert when usage exceeds 80% of quota. Report on top consumers and growth rate by department.
- **Visualization:** Table (mailboxes near quota), Bar chart (size by user), Line chart (growth trend).
- **CIM Models:** N/A

---

### UC-11.3.10 · Email Forwarding Rule and Auto-Reply Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Unauthorized forwarding rules can exfiltrate mail; auto-replies may leak sensitive info. Auditing rule changes supports security and compliance.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services, Exchange audit
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** Exchange/M365 mailbox rule and forwarding audit logs
- **SPL:**
```spl
index=o365 sourcetype="o365:audit"
| search (Operation="New-InboxRule" OR Operation="Set-Mailbox" OR Message="ForwardingRule")
| table _time, UserId, Operation, Parameters, ClientIP
| sort -_time
```
- **Implementation:** Ingest mailbox rule and forwarding change events from M365/Exchange. Alert on new forwarding rules or external redirects. Report on rule changes by user and time.
- **Visualization:** Table (rule changes), Timeline (events), Bar chart (changes by user).
- **CIM Models:** N/A

---

### UC-11.3.11 · Collaboration App Permission and Consent Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Third-party app consent and OAuth grants can expose data. Auditing consent and permission changes reduces shadow IT and abuse risk.
- **App/TA:** Entra ID / Azure AD audit logs, M365 audit
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** App consent, OAuth grant, and permission change events
- **SPL:**
```spl
index=o365 sourcetype="azure:audit"
| search (ActivityType="Consent to application" OR ActivityType="Add app role assignment")
| stats count by ApplicationId, ResourceDisplayName, UserPrincipalName
| sort -count
```
- **Implementation:** Ingest Entra ID consent and app role assignment events. Alert on new high-privilege consents or consent by non-admin. Report on app usage and permission scope.
- **Visualization:** Table (consent events), Bar chart (apps by consent count), Timeline (consent over time).
- **CIM Models:** N/A

---

### UC-11.3.12 · Voicemail and Call Recording Retention Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Voicemail and call recordings may be subject to retention and deletion policies. Monitoring supports compliance and storage management.
- **App/TA:** UCM/Teams Call Quality, voicemail system logs
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** Voicemail and recording metadata, retention policy events
- **SPL:**
```spl
index=ucm sourcetype="voicemail:metadata"
| eval age_days=floor((now()-_time)/86400)
| where age_days > 365
| stats count by mailbox_id, retention_policy
| sort -count
```
- **Implementation:** Ingest voicemail and recording metadata. Compare against retention policy (e.g., 1 year). Alert on items past retention. Report on storage by policy and cleanup actions.
- **Visualization:** Table (items past retention), Single value (total over-retained), Bar chart (by mailbox).
- **CIM Models:** N/A

---

### UC-11.3.13 · Outbound Email Volume and Domain Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Spike in outbound volume or new recipient domains can indicate compromise or data exfiltration. Baseline comparison supports early detection.
- **App/TA:** Exchange/M365 message trace, email gateway logs
- **Equipment Models:** Cisco Unified Communications Manager (CUCM), Unity Connection, IP Phone 7800 series, IP Phone 8800 series
- **Data Sources:** Outbound message counts, recipient domains
- **SPL:**
```spl
index=mail sourcetype="exchange:message_trace" direction=outbound
| stats count by user, recipient_domain, _time span=1h
| eventstats avg(count) as avg_count by user
| where count > (avg_count * 3)
| sort -count
```
- **Implementation:** Ingest message trace or gateway logs for outbound mail. Baseline volume per user and domain. Alert on volume spike or high volume to new domains. Correlate with DLP and sign-in data.
- **Visualization:** Line chart (outbound volume by user), Table (anomalous senders), Bar chart (recipient domains).
- **CIM Models:** N/A

---

### UC-11.3.14 · Webex Meeting Quality Degradation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Proactively detects poor meeting experiences by monitoring MOS scores, packet loss, jitter, and latency per participant. Enables IT to identify network segments, ISPs, or locations that consistently deliver degraded quality — before users start complaining. Supports SLA reporting and vendor accountability for Webex Calling and Meetings.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Meeting Qualities API (Pro Pack required)
- **Equipment Models:** Cisco Webex Meetings, Webex Calling, Webex Room Kit, Webex Room Kit Pro, Webex Board 55/70/85, Webex Desk, Webex Desk Pro
- **Data Sources:** Webex Meeting Qualities API (audio/video/sharing quality per participant)
- **SPL:**
```spl
index=webex sourcetype="webex:meeting_quality"
| eval quality_issue=case(audioMOS<3.5, "Poor Audio MOS", videoPacketLoss>5, "High Video Packet Loss", audioJitter>30, "High Audio Jitter", audioLatency>300, "High Audio Latency", 1==1, null())
| where isnotnull(quality_issue)
| stats count as incidents, avg(audioMOS) as avg_mos, avg(videoPacketLoss) as avg_pkt_loss, avg(audioJitter) as avg_jitter by meetingId, participantEmail, quality_issue
| sort -incidents
| table meetingId, participantEmail, quality_issue, incidents, avg_mos, avg_pkt_loss, avg_jitter
```
- **Implementation:** Configure a modular input to poll the Webex Meeting Qualities API every 10 minutes (the minimum interval allowed). Requires Pro Pack licensing and an integration with the `analytics:read_all` scope. Quality data is available 10 minutes after a meeting starts and up to 7 days after. Set alert thresholds: MOS < 3.5, packet loss > 5%, jitter > 30 ms, latency > 300 ms. Correlate with participant location and network data to pinpoint root causes.
- **Visualization:** Line chart (MOS trend over time), Heat map (quality by location/building), Table (worst participants by avg MOS), Single value panels (current avg MOS, packet loss).
- **CIM Models:** N/A

---

### UC-11.3.15 · Webex Calling CDR and Call Flow Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Provides full call detail records for Webex Calling, enabling cost analysis, trunk utilization tracking, call flow optimization, and identification of failed or abandoned calls. Unlike on-premise UCM CDRs, this covers cloud-native Webex Calling deployments. Supports chargebacks, capacity planning, and troubleshooting call routing issues through auto-attendants and call queues.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Detailed Call History API (Pro Pack required)
- **Equipment Models:** Cisco Webex Calling, Webex Desk Phone, IP Phone 8800 series (MPP), IP Phone 6800 series (MPP)
- **Data Sources:** Webex Detailed Call History API (caller, callee, duration, type, disposition, call legs)
- **SPL:**
```spl
index=webex sourcetype="webex:calling_cdr"
| eval call_duration_min=round(duration/60, 1)
| stats count as total_calls, avg(call_duration_min) as avg_duration, sum(call_duration_min) as total_minutes, count(eval(disposition="FAILURE")) as failed_calls by callingLineId, direction
| eval failure_rate=round(failed_calls/total_calls*100, 1)
| where failure_rate > 5 OR total_calls > 100
| sort -total_calls
| table callingLineId, direction, total_calls, avg_duration, total_minutes, failed_calls, failure_rate
```
- **Implementation:** Configure the Webex Detailed Call History API integration with Pro Pack licensing. Poll at hourly intervals (data available within 24 hours of call completion). Map calling line IDs to users and departments via lookup tables. Create separate dashboards for inbound vs. outbound analysis, PSTN vs. on-net call distribution, and per-location breakdowns.
- **Visualization:** Timechart (call volume by hour/day), Sankey diagram (call routing flow), Table (CDR detail with filters), Bar chart (calls by location/department).
- **CIM Models:** N/A

---

### UC-11.3.16 · Webex Calling Queue Performance and SLA
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors call queue health metrics that directly impact customer experience: average wait time, abandon rate, SLA compliance, and agent availability. Enables real-time staffing decisions and long-term workforce planning. High abandon rates or long wait times indicate understaffing or routing problems that need immediate attention.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Calling Analytics API
- **Equipment Models:** Cisco Webex Calling, Webex Contact Center
- **Data Sources:** Webex Calling Queue Analytics API (queue stats, agent stats, wait times)
- **SPL:**
```spl
index=webex sourcetype="webex:calling_queue"
| bin _time span=15m
| stats avg(avgWaitTimeSec) as avg_wait, sum(abandonedCalls) as abandoned, sum(answeredCalls) as answered, sum(totalCalls) as total by _time, queueName
| eval abandon_rate=if(total>0, round(abandoned/total*100, 1), 0)
| eval sla_met=if(avg_wait<=30, "Yes", "No")
| where abandon_rate > 10 OR avg_wait > 60
| table _time, queueName, total, answered, abandoned, abandon_rate, avg_wait, sla_met
```
- **Implementation:** Integrate with the Webex Calling Analytics API to retrieve queue statistics. Poll every 15 minutes for near-real-time monitoring. Define SLA thresholds per queue (e.g., 80% of calls answered within 30 seconds). Alert when abandon rate exceeds 10% or average wait time exceeds 60 seconds. Create wallboard-style dashboards for supervisors showing live queue status.
- **Visualization:** Real-time single value panels (current queue depth, avg wait), Line chart (abandon rate over time), Column chart (calls by queue), Table (SLA compliance by queue and time).
- **CIM Models:** N/A

---

### UC-11.3.17 · Webex Admin Audit Trail
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Provides full accountability for administrative changes in Webex Control Hub — user provisioning, policy changes, license assignments, security settings, and integration modifications. Required for compliance audits (SOX, HIPAA, ISO 27001) and security investigations. Detects unauthorized admin actions or compromised admin accounts through anomaly detection on change volume and timing.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Admin Audit Events API via HEC webhook
- **Equipment Models:** Cisco Webex Control Hub
- **Data Sources:** Webex Admin Audit Events API (admin actions, actor, target, timestamp)
- **SPL:**
```spl
index=webex sourcetype="webex:admin_audit"
| stats count as changes by actorEmail, actionType, targetType
| eventstats sum(changes) as total_by_admin by actorEmail
| sort -total_by_admin
| table actorEmail, actionType, targetType, changes, total_by_admin
```
- **Implementation:** Register a Webex integration with the `audit:events_read` scope and full admin credentials. Poll the Admin Audit Events API every 5 minutes. Enrich events with admin role information from the People API. Alert on: changes outside business hours, bulk user deletions (>10 in 1 hour), security policy modifications, and admin actions from new IP addresses or locations.
- **Visualization:** Timeline (admin changes over time), Table (audit log with filters), Bar chart (changes by admin), Pie chart (change types).
- **CIM Models:** Change

---

### UC-11.3.18 · Webex DLP and File Compliance Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Monitors real-time file sharing across Webex spaces for data loss prevention violations. Files are scanned before becoming accessible to other members, preventing sensitive data exposure. Tracks DLP approval/rejection decisions, identifies repeat offenders, and provides evidence for compliance investigations. Critical for organizations handling PII, PHI, financial data, or intellectual property in Webex.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Compliance webhooks via HEC (Pro Pack required)
- **Equipment Models:** Cisco Webex Messaging, Webex Control Hub
- **Data Sources:** Webex Compliance Events API, Real-time File DLP webhook events
- **SPL:**
```spl
index=webex sourcetype="webex:compliance"
| search eventType="file_*" OR eventType="dlp_*"
| eval outcome=case(dlpAction="approved", "Approved", dlpAction="rejected", "Blocked", dlpAction="default_approved", "Default Approved", 1==1, "Unknown")
| stats count as total_files, count(eval(outcome="Blocked")) as blocked, count(eval(outcome="Approved")) as approved by actorEmail, spaceName
| where blocked > 0
| eval block_rate=round(blocked/total_files*100, 1)
| sort -blocked
| table actorEmail, spaceName, total_files, approved, blocked, block_rate
```
- **Implementation:** Enable real-time file DLP in Webex Control Hub (requires Pro Pack and Compliance Officer role). Configure organization-level webhooks with `ownedBy=org` to receive file events. Integrate with your DLP provider (Cisco Cloudlock, Microsoft DLP, Symantec, etc.) for policy enforcement. Forward webhook events to Splunk via HEC. Alert on: any blocked file, users with >3 violations per day, and DLP bypasses (default approved when DLP scanner is unreachable).
- **Visualization:** Table (DLP violations with file type and actor), Bar chart (violations by user), Timechart (violation trend), Single value (total blocks today).
- **CIM Models:** DLP

---

### UC-11.3.19 · Webex Device Health and Environmental Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Monitors the health and environmental conditions of Webex room devices (Room Kit, Board, Desk series). RoomOS devices report temperature, humidity, ambient noise, air quality, and occupancy data via RoomAnalytics. Detecting devices that go offline, run outdated firmware, or operate in poor environmental conditions prevents meeting disruptions and protects hardware investments. Occupancy data from room sensors supports real estate optimization.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Devices API via HEC or custom modular input
- **Equipment Models:** Cisco Webex Room Kit, Room Kit Mini, Room Kit Pro, Room Kit EQ, Webex Board 55/70/85, Webex Desk, Webex Desk Pro, Webex Room Bar, Room Navigator
- **Data Sources:** Webex Devices API (device status, software), RoomAnalytics xAPI (temperature, humidity, noise, air quality, people count)
- **SPL:**
```spl
index=webex sourcetype="webex:devices"
| eval status_issue=case(connectionStatus="disconnected", "Offline", softwareCurrent!=softwareAvailable, "Firmware Outdated", temperature>35, "High Temperature", humidity>70, "High Humidity", ambientNoise>65, "Noisy Environment", 1==1, null())
| where isnotnull(status_issue)
| stats count by displayName, workspaceName, product, connectionStatus, status_issue, softwareCurrent
| sort -count
| table displayName, workspaceName, product, status_issue, connectionStatus, softwareCurrent
```
- **Implementation:** Register a Webex integration with `spark-admin:devices_read` and `spark-admin:workspaces_read` scopes. Poll device status every 5 minutes. Enable RoomAnalytics on devices via Control Hub or xAPI (`xConfiguration RoomAnalytics PeoplePresenceDetector: On`). For environmental data, enable `xConfiguration RoomAnalytics AmbientNoise` and temperature/humidity reporting. Historical environmental data is available for up to 30 days. Alert on devices offline >15 minutes, firmware more than one version behind, or temperature/humidity outside safe ranges.
- **Visualization:** Map (device locations with status), Table (offline/unhealthy devices), Line chart (environmental trends by room), Single value panels (devices online, firmware compliance %).
- **CIM Models:** N/A

---

### UC-11.3.20 · Webex License Utilization and Adoption Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Compares assigned Webex licenses against actual usage to identify wasted spend. Organizations often over-provision Meetings, Calling, and Messaging licenses. Tracking adoption rates by department and user helps right-size license allocations, reclaim unused seats, and justify renewals. Combines license inventory data with meeting/calling activity to calculate true utilization rates.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Licenses API via HEC or custom modular input
- **Equipment Models:** Cisco Webex Meetings, Webex Calling, Webex Messaging
- **Data Sources:** Webex Licenses API (assigned/consumed counts), People API (user status), Meeting Summary Reports (active users)
- **SPL:**
```spl
index=webex sourcetype="webex:licenses"
| stats latest(totalUnits) as total, latest(consumedUnits) as consumed by licenseName
| eval available=total-consumed
| eval utilization_pct=round(consumed/total*100, 1)
| sort -utilization_pct
| table licenseName, total, consumed, available, utilization_pct
```
- **Implementation:** Poll the Webex Licenses API daily to track assigned vs. consumed license counts. Cross-reference with meeting and calling activity data to identify users who have licenses but haven't used them in 30/60/90 days. Create a lookup mapping users to departments for group-level reporting. Flag users inactive for >60 days as reclamation candidates. Report license utilization weekly to finance and IT leadership.
- **Visualization:** Bar chart (license utilization by type), Table (inactive users with assigned licenses), Timechart (license consumption trend), Single value panels (total cost, waste estimate).
- **CIM Models:** N/A

---

### UC-11.3.21 · Webex Messaging Activity and Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance
- **Value:** Tracks messaging volume, file sharing, and space activity across Webex Messaging. Establishes baselines per user to detect anomalous bulk messaging that could indicate a compromised account, bot abuse, or policy violation. Also measures collaboration adoption and engagement trends across departments. Identifies inactive spaces consuming storage and active spaces that may need governance controls.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk` (GitHub), Webex Events/Compliance API via HEC
- **Equipment Models:** Cisco Webex Messaging, Webex App
- **Data Sources:** Webex Events API (messages created/deleted, files shared, memberships changed)
- **SPL:**
```spl
index=webex sourcetype="webex:events" resource="messages"
| bin _time span=1h
| stats count as msg_count, dc(roomId) as active_spaces by actorEmail, _time
| eventstats avg(msg_count) as avg_msgs, stdev(msg_count) as stdev_msgs by actorEmail
| eval upper_bound=avg_msgs+(3*stdev_msgs)
| where msg_count > upper_bound AND msg_count > 50
| table _time, actorEmail, msg_count, active_spaces, avg_msgs, upper_bound
```
- **Implementation:** Register a Webex Compliance integration with the `spark-compliance:events_read` scope to access organization-wide message events. Poll the Events API every 5 minutes for near-real-time visibility. Build user activity baselines over 30 days before enabling anomaly alerting. Alert on: message volume exceeding 3 standard deviations from baseline, bulk file uploads (>20 files in 1 hour), and messages containing URLs to known-bad domains (cross-reference with threat intel). Combine with DLP data for comprehensive messaging security.
- **Visualization:** Timechart (message volume by department), Table (anomalous users), Bar chart (top active spaces), Line chart (adoption trend over 90 days).
- **CIM Models:** N/A

---

### UC-11.3.22 · SharePoint Site Storage Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Site collections approaching quota block uploads and disrupt teams. Proactive monitoring enables quota increases or content archival before users hit limits.
- **App/TA:** Custom (SharePoint REST API, PowerShell)
- **Data Sources:** SharePoint REST API (/_api/site/usage), Get-SPOSite (SharePoint Online)
- **SPL:**
```spl
index=sharepoint sourcetype="sharepoint:site_usage"
| eval used_mb=coalesce(StorageUsageCurrent/1024, StorageUsageCurrentMB, 0), quota_mb=coalesce(StorageQuota/1024, StorageQuotaMB, 0)
| eval used_pct=if(quota_mb>0, round(used_mb/quota_mb*100, 1), 0)
| where used_pct >= 70
| bin _time span=1d
| stats latest(used_mb) as used_mb, latest(quota_mb) as quota_mb, latest(used_pct) as used_pct by _time, SiteUrl, SiteName
| where used_pct >= 70
| sort -used_pct
| table SiteUrl, SiteName, used_mb, quota_mb, used_pct
```
- **Implementation:** For SharePoint Online, use `Get-SPOSite -IncludePersonalSite $false | Select-Object Url, StorageUsageCurrent, StorageQuota` via a scheduled PowerShell script; for on-prem, call `/_api/site/usage` with app-only or user credentials. Forward JSON to Splunk via HEC. Run daily or every 6 hours. Alert when used_pct >= 80 (warning) or >= 95 (critical). Maintain a lookup of site owners for notification. Report on growth rate and projected quota exhaustion.
- **Visualization:** Table (sites near quota), Bar chart (usage by site), Gauge (overall tenant usage %), Line chart (storage growth trend).
- **CIM Models:** N/A

---

### UC-11.3.23 · SharePoint Search Crawl Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Crawl errors, stale content, and index freshness affect findability. Failed crawls leave content undiscoverable; slow crawls delay new content visibility.
- **App/TA:** Custom (SharePoint Search Admin API)
- **Data Sources:** Search Administration crawl logs, Get-SPEnterpriseSearchCrawlContentSource (on-prem), Search & Intelligence admin reports (M365)
- **SPL:**
```spl
index=sharepoint sourcetype="sharepoint:search_crawl"
| eval error_type=case(match(ErrorLevel, "Error|Critical|Failure"), "Error", match(ErrorLevel, "Warning"), "Warning", 1==1, "Info")
| where error_type="Error" OR error_type="Warning"
| bin _time span=1h
| stats count as crawl_errors, dc(ItemId) as unique_items, latest(LastCrawlTime) as last_crawl by _time, ContentSource, error_type
| where crawl_errors > 0
| sort -crawl_errors
| table _time, ContentSource, error_type, crawl_errors, unique_items, last_crawl
```
- **Implementation:** For on-prem SharePoint, query crawl logs via Search Admin API or `Get-SPEnterpriseSearchCrawlLog` and stream to Splunk. For M365, use Search & Intelligence admin center APIs or export crawl health reports. Ingest crawl start/end, error count, item count, and last successful crawl per content source. Alert on error count spike (>10 errors in 1 hour) or last successful crawl >24 hours ago for critical sources. Track crawl duration and index freshness.
- **Visualization:** Line chart (crawl errors over time), Table (content sources with errors), Single value (sources with stale index), Bar chart (errors by content source).
- **CIM Models:** N/A

---

### 11.3.TE Cisco ThousandEyes — Voice & Collaboration Monitoring

---

### UC-11.3.25 · SIP Server Availability Monitoring (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors SIP server reachability from ThousandEyes agents, ensuring voice and unified communications infrastructure is responsive from the network path perspective. SIP server failures directly impact call setup for all users.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (SIP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="sip-server"
| stats avg(sip.server.request.availability) as avg_availability by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Create SIP Server tests in ThousandEyes targeting your SIP proxy, session border controllers, or CUCM servers. The OTel metric `sip.server.request.availability` reports 100% when the SIP OPTIONS request succeeds. The `sip.response.status_code` attribute provides the SIP response code. The Splunk App Voice dashboard includes a "SIP Availability (%)" panel.
- **Visualization:** Line chart (availability % over time), Single value (current availability), Table (test, server, agent, availability).
- **CIM Models:** N/A

---

### UC-11.3.26 · SIP Registration Time Tracking (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Slow SIP registration or response times indicate server overload, network congestion, or infrastructure issues that delay call setup and affect voice quality perception.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (SIP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="sip-server"
| timechart span=5m avg(sip.client.request.duration) as avg_ttfb_s avg(sip.client.request.total_time) as avg_total_s by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1), avg_total_ms=round(avg_total_s*1000,1)
```
- **Implementation:** The OTel metric `sip.client.request.duration` reports TTFB (time to first SIP response) in seconds, and `sip.client.request.total_time` reports total SIP transaction time. The Splunk App Voice dashboard includes a "SIP Request Duration (s)" line chart. Alert when SIP response time consistently exceeds 500 ms — this adds noticeable delay to call setup.
- **Visualization:** Line chart (TTFB and total time over time), Table (test, TTFB, total time), Single value.
- **CIM Models:** N/A

---

### UC-11.3.27 · RTP MOS Score Monitoring (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Mean Opinion Score (MOS) is the standard measure of voice call quality on a scale of 1 to 5. ThousandEyes RTP tests provide MOS alongside packet loss, discards, and delay variation, enabling continuous voice quality assurance from the network perspective.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (RTP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="rtp"
| stats avg(rtp.client.request.mos) as avg_mos avg(rtp.client.request.loss) as avg_loss avg(rtp.client.request.pdv) as avg_pdv_s avg(rtp.client.request.discards) as avg_discards by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_pdv_ms=round(avg_pdv_s*1000,1)
| where avg_mos < 3.5
| sort avg_mos
```
- **Implementation:** Create RTP (Voice Layer) tests in ThousandEyes targeting voice infrastructure. RTP tests are paired with SIP Server tests. The OTel metric `rtp.client.request.mos` reports MOS (1-5), `rtp.client.request.loss` reports packet loss percentage, `rtp.client.request.pdv` reports Packet Delay Variation in seconds, and `rtp.client.request.discards` reports discarded packets percentage. The Splunk App Voice dashboard includes "RTP MOS" and "RTP Loss (%)" panels. MOS below 3.5 indicates poor call quality.
- **Visualization:** Line chart (MOS over time), Single value (current MOS), Table (test, agent, MOS, loss, PDV, discards).
- **CIM Models:** N/A

---

### UC-11.3.28 · Webex Meeting Quality Assurance via ThousandEyes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors the network path from offices to Webex data centers using ThousandEyes agents, providing proactive visibility into network conditions that degrade meeting quality — before users file tickets. Correlate with Webex quality data (UC-11.3.6) for end-to-end troubleshooting.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Agent-to-Server and HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*Webex*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_latency_ms > 150 OR avg_loss > 1 OR avg_jitter > 30
| sort -avg_latency_ms
```
- **Implementation:** Create Agent-to-Server tests in ThousandEyes targeting Webex media and signaling endpoints (e.g., *.webex.com, Webex data center IPs). Name tests with "Webex" for filtering. ThousandEyes provides Webex-specific monitoring guides with recommended test configurations. Correlate network path quality with Webex meeting quality metrics from the Webex APIs for end-to-end root cause analysis.
- **Visualization:** Line chart (latency to Webex over time), Table (agent, latency, loss, jitter), Dashboard combining TE network data with Webex meeting quality.
- **CIM Models:** N/A

---

### UC-11.3.29 · Microsoft Teams Network Readiness (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Validates that each office location meets Microsoft's network quality requirements for Teams calls and meetings (latency <50ms, loss <1%, jitter <30ms). ThousandEyes tests the actual network path to Microsoft 365 endpoints.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Agent-to-Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*Teams*" OR thousandeyes.test.name="*M365*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| eval teams_ready=if(avg_latency_ms<50 AND avg_loss<1 AND avg_jitter<30, "Ready", "Not Ready")
| sort teams_ready, -avg_latency_ms
```
- **Implementation:** Create Agent-to-Server tests targeting Microsoft Teams media relay IPs and Microsoft 365 front-door endpoints from each office Enterprise Agent. Microsoft publishes recommended network requirements: latency <50ms, loss <1%, jitter <30ms for optimal Teams quality. ThousandEyes provides Microsoft 365 monitoring best practices. Name tests with "Teams" or "M365" for easy filtering.
- **Visualization:** Table (agent, latency, loss, jitter, readiness status), Single value (sites meeting requirements), Map (readiness by location).
- **CIM Models:** N/A

---

### UC-11.3.30 · Zoom Collaboration Performance (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors network path quality to Zoom data centers from office locations, ensuring the network supports high-quality video conferencing. Helps distinguish between Zoom platform issues and local network problems.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Agent-to-Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*Zoom*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_latency_ms > 150 OR avg_loss > 1 OR avg_jitter > 30
| sort -avg_latency_ms
```
- **Implementation:** Create Agent-to-Server tests targeting Zoom data center endpoints from each office Enterprise Agent. Zoom publishes recommended network requirements similar to Microsoft Teams. Name tests with "Zoom" for filtering. Correlate with Zoom Dashboard API data (if available) for end-to-end quality analysis.
- **Visualization:** Line chart (latency to Zoom over time), Table (agent, latency, loss, jitter), Comparison dashboard across collaboration platforms.
- **CIM Models:** N/A

---

### UC-11.3.31 · RoomOS Device Network Health via ThousandEyes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** ThousandEyes agents can be enabled on Cisco RoomOS devices (Room Kit, Board, Desk), monitoring the network path from the conference room to cloud meeting services. This provides per-room visibility into network conditions affecting meeting quality.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Enterprise Agent tests from RoomOS)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.source.agent.name="RoomOS*" OR thousandeyes.source.agent.name="Room-*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_latency_ms > 100 OR avg_loss > 0.5
| sort -avg_latency_ms
```
- **Implementation:** Enable ThousandEyes agent on Cisco RoomOS devices via Webex Control Hub or xAPI. The agent runs integrated tests from the room device itself, providing true end-to-end network quality measurement from the meeting room. Name agents with a "RoomOS-" or "Room-" prefix for filtering. Tests run from RoomOS devices provide the exact network perspective of the video endpoint.
- **Visualization:** Table (room device, target, latency, loss, jitter), Map (room locations with quality indicators), Dashboard per building/floor.
- **CIM Models:** N/A

---

### UC-11.3.32 · Wire-Level VoIP Quality (MOS from RTP Stream)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Industry:** Telecommunications
- **Value:** Captures Mean Opinion Score (MOS) and R-Factor directly from RTP packets on the wire, providing platform-independent voice quality measurement. Unlike UC-11.3.1 which uses Cisco CUCM CMR data (application-level), this use case captures quality at the network level regardless of the call platform — covering third-party PBX, SIP trunking providers, and carrier interconnects.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Contact Center Analytics (50 Ways #7)
- **Data Sources:** `sourcetype=stream:rtp`
- **SPL:**
```spl
sourcetype="stream:rtp"
| stats avg(mos_session) as avg_mos, avg(rfactor) as avg_rfactor, avg(lost) as avg_loss_pct, avg(unseq) as avg_unseq, count as streams by codec_name
| eval quality=case(avg_mos>=4.0, "Good", avg_mos>=3.5, "Acceptable", avg_mos>=3.0, "Poor", 1==1, "Unacceptable")
| sort avg_mos
```
- **Implementation:** Install Splunk App for Stream and configure it to capture RTP traffic on voice network segments. Enable the RTP protocol for full field extraction including `mos_session`, `rfactor`, `lost`, `unseq`, and `codec_name`. The MOS is calculated by Stream from RTP statistics (jitter, loss, codec type) per session. Deploy Stream forwarders on network taps or SPAN ports that see voice traffic. Alert when average MOS drops below 3.5 (ITU-T G.107 threshold for acceptable quality). Segment analysis by `codec_name` to identify if codec choice affects quality.
- **Visualization:** Gauge (average MOS score with thresholds: green >4.0, yellow 3.5-4.0, red <3.5), Line chart (MOS trend over 24h in 15-min buckets), Table (codec_name, avg_mos, avg_rfactor, avg_loss_pct, streams — sortable), Bar chart (stream count by quality category).
- **CIM Models:** N/A

---

### UC-11.3.33 · Emergency Call (E911/E112) Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Security
- **Industry:** Telecommunications
- **Value:** Tracks all emergency calls (911, 933 test, 112) through the telephony system to ensure regulatory compliance and rapid response. Monitors call completion rate, answer time, and any failed emergency calls — a regulatory requirement in many jurisdictions.
- **App/TA:** `TA for Cisco CDR Reporting and Analytics` (Splunkbase #4434), or `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Emergency Services Monitoring (50 Ways #11)
- **Data Sources:** `sourcetype=cisco:ucm:cdr` or `sourcetype=stream:sip`
- **SPL:**
```spl
sourcetype="cisco:ucm:cdr"
| where match(calledPartyNumber, "^(911|933|112)$")
| eval answer_time=dateTimeConnect-dateTimeOrigination
| eval completed=if(destCause_value==16, "Yes", "No")
| stats count as total_calls, sum(eval(if(completed=="Yes", 1, 0))) as answered, avg(answer_time) as avg_answer_sec, avg(duration) as avg_duration_sec by calledPartyNumber
| eval answer_rate=round(answered*100/total_calls, 1)
| table calledPartyNumber, total_calls, answered, answer_rate, avg_answer_sec, avg_duration_sec
```
- **Implementation:** Ingest Cisco UCM CDR data using the TA for Cisco CDR Reporting and Analytics. Emergency numbers are identified by `calledPartyNumber` matching 911 (US), 933 (US test), or 112 (EU). The `destCause_value=16` indicates normal call clearing (answered and completed). Calculate answer rate as the percentage of calls that were connected. For SIP-based tracking via Stream, filter `sourcetype="stream:sip"` where `callee_e164` matches emergency numbers and check `reply_code=200`. Create real-time alerts for ANY failed emergency call (non-16 cause value). Generate compliance reports monthly.
- **Visualization:** Single value (emergency call answer rate — target: 100%, red if <99%), Table (calledPartyNumber, total_calls, answered, answer_rate, avg_answer_sec), Timeline (emergency calls over 30 days), Bar chart (emergency calls by hour of day).
- **CIM Models:** N/A

---

### UC-11.3.34 · Answer Seizure Ratio (ASR) by Route Group
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Industry:** Telecommunications
- **Value:** Calculates Answer Seizure Ratio — the percentage of call attempts that are successfully answered — by route group or trunk. ASR is the primary KPI for voice service quality in carrier networks. Low ASR indicates trunk failures, destination unreachable, or capacity exhaustion.
- **App/TA:** `TA for Cisco CDR Reporting and Analytics` (Splunkbase #4434), or `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Voice/VoIP Revenue Assurance (50 Ways #30), Real-Time Service Reporting (50 Ways #33)
- **Data Sources:** `sourcetype=cisco:ucm:cdr` or `sourcetype=stream:sip`
- **SPL:**
```spl
sourcetype="cisco:ucm:cdr"
| eval answered=if(destCause_value==16, 1, 0)
| stats count as total_attempts, sum(answered) as answered_calls by destDeviceName
| eval ASR=round(answered_calls*100/total_attempts, 2)
| where total_attempts>10
| sort ASR
```
- **Implementation:** Ingest Cisco UCM CDR data. The `destCause_value=16` (Normal Call Clearing) indicates a successfully answered call. Group by `destDeviceName` (which represents the route group or gateway) to calculate ASR per trunk. Industry standard ASR benchmarks: >50% is acceptable for international routes, >70% is good for domestic routes. For SIP-based tracking via Stream, use `sourcetype="stream:sip"` with `method=INVITE` and calculate the ratio of `reply_code=200` to total INVITEs per `dest`. Alert when ASR drops below historical baseline by more than 10 percentage points.
- **Visualization:** Gauge (overall ASR with thresholds: green >70%, yellow 50-70%, red <50%), Column chart (ASR by destDeviceName/trunk), Line chart (ASR trend over 7 days), Table (destDeviceName, total_attempts, answered_calls, ASR — sortable, highlighted red below 50%).
- **CIM Models:** N/A

---

### 11.4 Mail Transport & Relay Infrastructure

**Primary App/TA:** Postfix, Sendmail, Microsoft Exchange, Cisco Email Security Appliance (ESA), generic SMTP/MTA logs

---


### UC-11.4.1 · SMTP Service Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Distinct from mail queue depth monitoring — this checks whether the SMTP daemon is accepting TCP connections and responding to EHLO. A crashed postfix or sendmail process stops inbound/outbound mail entirely without generating queue entries. Nagios `check_smtp` verifies this at the connection layer; Splunk replicates it via daemon-level log monitoring.
- **App/TA:** `Splunk_TA_syslog`, `Splunk_TA_postfix` (community)
- **Data Sources:** `sourcetype=syslog` (postfix, sendmail, exim logs), `sourcetype=postfix:syslog`
- **SPL:**
```spl
index=mail (sourcetype=syslog process=postfix* OR sourcetype="postfix:syslog")
| bucket _time span=5m
| stats count as smtp_events by host, _time
| streamstats window=3 min(smtp_events) as min_events by host
| where min_events=0
| eval status="SMTP_DOWN"
| table _time, host, status
```
- **Implementation:** Ingest Postfix/Sendmail syslog output via Universal Forwarder. Under normal operation, an active MTA generates constant log activity (queue manager, cleanup, smtp/smtpd). Absence of events for 5–10 minutes on an expected mail host indicates SMTP process death or service failure. Alert after 2 consecutive empty windows. Complement with a scripted input: `echo QUIT | nc -w5 host 25` — log exit code as synthetic probe result. Monitor separately for TLS handshake failures (port 587/465) as distinct service checks.
- **Visualization:** Single value (SMTP hosts down), Timeline (downtime events), Line chart (event rate per mail host), Table (host, MTA type, last event timestamp).
- **CIM Models:** N/A

---

### UC-11.4.2 · POP3 / IMAP Mail Retrieval Service Availability
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** POP3 and IMAP services allow mail clients to retrieve messages. Even when delivery works correctly, a crashed Dovecot or Cyrus daemon prevents users from reading email, appearing as a total mail outage. Nagios `check_pop` and `check_imap` monitor these ports directly; Splunk replicates availability detection through daemon log analysis.
- **App/TA:** `Splunk_TA_syslog`
- **Data Sources:** `sourcetype=syslog` (dovecot, cyrus-imapd logs), Dovecot authentication log
- **SPL:**
```spl
index=mail sourcetype=syslog (process=dovecot OR process=imap OR process=pop3)
| bucket _time span=5m
| stats count as imap_events by host, _time
| where isnull(imap_events) OR imap_events=0
| eval status="IMAP_POP3_DOWN"
| table _time, host, status
```
- **Implementation:** Forward Dovecot or Cyrus IMAP logs via Universal Forwarder. Dovecot logs login events, failed auth, and daemon lifecycle events continuously during normal operation. Zero events for >10 minutes on a mail host indicates a process crash or service failure. Alert after 2 consecutive empty windows. Cross-correlate with auth failures (could indicate process restart loops). For comprehensive coverage, deploy a scripted TCP probe on ports 143 (IMAP), 993 (IMAPS), 110 (POP3), 995 (POP3S).
- **Visualization:** Table (host, protocol, port, status), Timeline (downtime events), Single value (services down count), Line chart (login event rate as proxy for service health).
- **CIM Models:** N/A

---

### UC-11.4.3 · Mail Queue Depth and Deferred Message Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Growing mail queue (deferred, hold) indicates delivery failures, recipient issues, or abuse. Detecting backlog early prevents bounce storms and blacklisting.
- **App/TA:** `Splunk_TA_syslog`, custom scripted input (mailq, postqueue)
- **Data Sources:** Postfix `mailq`, Sendmail queue, Exchange queue length
- **SPL:**
```spl
index=mail sourcetype=mail_queue host=*
| stats latest(queue_depth) as depth, latest(deferred_count) as deferred, latest(_time) as last_seen by host
| where depth > 100 OR deferred > 50
| table host depth deferred last_seen
```
- **Implementation:** Run `mailq` or equivalent every 5 minutes. Parse queue depth and deferred count. Alert when queue exceeds 100 or deferred exceeds 50. Correlate with rejection logs and recipient domains.
- **Visualization:** Line chart (queue depth over time), Table (host, queue, deferred), Single value (max queue).
- **CIM Models:** N/A

---

### UC-11.4.4 · SMTP Authentication and Relay Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed SMTP auth or unauthorized relay attempts may indicate credential stuffing or abuse. Monitoring supports security and ensures relay policy is enforced.
- **App/TA:** `Splunk_TA_syslog`, mail server logs
- **Data Sources:** Postfix maillog, Sendmail logs, Exchange SMTP receive connector logs
- **SPL:**
```spl
index=mail sourcetype=syslog (process=postfix OR process=sendmail) ("authentication failed" OR "relay denied" OR "reject")
| rex "user=(?<sasl_user>\S+)"
| stats count by src, sasl_user, action
| where count > 10
| sort -count
```
- **Implementation:** Forward mail server logs. Extract auth and relay outcomes. Alert on high volume of auth failures from single IP or relay denied for internal IPs (possible misconfiguration).
- **Visualization:** Table (IP, user, action, count), Timechart of failures, Map (GeoIP).
- **CIM Models:** Authentication

---

### UC-11.4.5 · Mail Delivery Rate and Bounce Rate by Domain
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sudden drop in delivery rate or spike in bounces for a domain indicates reputation or configuration issues. Trending supports deliverability and capacity planning.
- **App/TA:** Mail server logs, bounce logs
- **Data Sources:** Postfix/Sendmail delivery status, bounce messages, Exchange tracking logs
- **SPL:**
```spl
index=mail sourcetype=mail_delivery
| stats count(eval(status="delivered")) as delivered, count(eval(status="bounce")) as bounces by domain, _time span=1h
| eval bounce_rate=round(bounces/(delivered+bounces)*100, 2)
| where bounce_rate > 5 OR delivered < 10
| table domain delivered bounces bounce_rate
```
- **Implementation:** Parse delivery and bounce events by recipient domain. Compute hourly delivery and bounce rate. Alert when bounce rate exceeds 5% or delivery volume drops significantly for critical domains.
- **Visualization:** Line chart (delivery and bounce rate by domain), Table (domain, delivered, bounces, %), Bar chart (bounce rate by domain).
- **CIM Models:** N/A

---

### UC-11.4.6 · Outbound Mail Volume and Recipient Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual outbound volume or new bulk recipients may indicate compromised account or phishing campaign. Baseline and anomaly detection support incident response.
- **App/TA:** Mail server logs
- **Data Sources:** Postfix/Sendmail/Exchange outbound logs
- **SPL:**
```spl
index=mail sourcetype=mail_send
| stats dc(recipient) as recipients, count as msg_count by sender, _time span=1h
| eventstats avg(msg_count) as avg_count, stdev(msg_count) as std_count by sender
| eval z_score=if(std_count>0, (msg_count-avg_count)/std_count, 0)
| where z_score > 3 OR recipients > 100
| table _time sender msg_count recipients z_score
```
- **Implementation:** Ingest outbound send events. Baseline message count and unique recipients per sender (hourly). Alert when volume or recipient count exceeds 3 standard deviations or recipient count >100 in one hour.
- **Visualization:** Table (sender, count, recipients, z-score), Line chart (volume by sender), Bar chart (top senders).
- **CIM Models:** N/A

---

### UC-11.4.7 · Mail Server TLS and Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Security
- **Value:** Expired or expiring TLS certificates on SMTP/IMAP/POP break encryption and can cause delivery failures. Proactive monitoring prevents outages.
- **App/TA:** Custom scripted input (openssl s_client)
- **Data Sources:** TLS handshake to mail server ports (25, 465, 587, 993, 995)
- **SPL:**
```spl
index=mail sourcetype=mail_tls host=*
| eval days_left=round((expiry_epoch-now())/86400, 0)
| where days_left < 30
| table host port days_left subject
| sort days_left
```
- **Implementation:** Script that connects to mail server ports and extracts certificate expiry (e.g. `openssl s_client -connect host:25 -starttls smtp`). Ingest daily. Alert when expiry is within 30 days.
- **Visualization:** Table (host, port, days left), Single value (soonest expiry), Gauge (days remaining).
- **CIM Models:** N/A

---

### UC-11.4.8 · SMTP Relay Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Availability
- **Value:** Tracks messages relayed through internal SMTP gateways vs policy — unexpected relay volume or open relay abuse paths.
- **App/TA:** `Splunk_TA_syslog`, Postfix/Exchange logs
- **Data Sources:** `postfix:syslog` `relay=`, `status=sent`, `reject` relay attempts
- **SPL:**
```spl
index=mail sourcetype="postfix:syslog" OR sourcetype=syslog process=postfix
| search relay=* OR "relay access denied"
| stats count by relay_domain, action, src
| where count > 500
```
- **Implementation:** Parse relay lines for authorized vs denied. Alert on high relay denied from single IP (scanning) or high accepted relay to external domains (misconfiguration).
- **Visualization:** Table (relay domain, count), Line chart (relay attempts), Single value (relay denied rate).
- **CIM Models:** N/A

---

### 11.5 Video Conferencing & Collaboration Analytics

**Primary App/TA:** Splunk Connect for Zoom, `ta_cisco_webex_add_on_for_splunk` (Webex TA), Splunk Add-on for Microsoft Cloud Services / Microsoft 365 Add-on for Teams meeting quality.

---

### UC-11.5.1 · Zoom Meeting Quality Metrics (Jitter, Packet Loss, Latency)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Poor jitter, loss, or latency directly degrades audio/video MOS and drives support tickets; trending these metrics isolates client, ISP, or Zoom POP issues before executive calls fail.
- **App/TA:** Splunk Connect for Zoom
- **Data Sources:** `sourcetype=zoom:metrics`, Zoom dashboard quality API / meeting QoS events
- **SPL:**
```spl
index=zoom sourcetype="zoom:metrics"
| where avg_jitter_ms > 30 OR packet_loss_pct > 2 OR avg_rtt_ms > 300
| timechart span=5m avg(avg_jitter_ms) as jitter_ms, avg(packet_loss_pct) as loss_pct, avg(avg_rtt_ms) as rtt_ms by meeting_id
```
- **Implementation:** Ingest Zoom meeting quality or participant QoS feeds via the official connector. Normalize per-participant jitter, loss, and RTT. Baseline by region and device type. Alert when thresholds exceed SLA for sustained intervals. Correlate with ISP and VPN indicators.
- **Visualization:** Line chart (jitter, loss, RTT over time), Heatmap (participant × metric), Table (worst meetings in window).
- **CIM Models:** N/A

---

### UC-11.5.2 · Zoom Call Drop Rate Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Elevated drop rates signal network instability, client bugs, or capacity limits; tracking drops by geography and client version prioritizes fixes.
- **App/TA:** Splunk Connect for Zoom
- **Data Sources:** `sourcetype=zoom:meetings`, meeting end / participant disconnect events
- **SPL:**
```spl
index=zoom sourcetype="zoom:meetings"
| eval er=lower(end_reason)
| eval dropped=if(like(er,"%drop%") OR like(er,"%disconnect%") OR like(er,"%lost%"),1,0)
| bin _time span=1h
| stats sum(dropped) as drops, count as meetings by _time
| eval drop_rate_pct=if(meetings>0, round(drops/meetings*100,2), 0)
| where drop_rate_pct > 5
```
- **Implementation:** Ingest meeting lifecycle events with end reason and duration. Compute hourly drop rate = meetings ended abnormally / total meetings. Segment by account, data center, or client version. Alert when drop rate exceeds baseline (e.g., >5%).
- **Visualization:** Line chart (drop rate % over time), Bar chart (drops by region), Single value (drop rate last hour).
- **CIM Models:** N/A

---

### UC-11.5.3 · Zoom Participant Join Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Join failures block users from hearings and classes; clustering failures by error code reveals SSO, licensing, or capacity misconfigurations.
- **App/TA:** Splunk Connect for Zoom
- **Data Sources:** `sourcetype=zoom:participant`, join attempt logs
- **SPL:**
```spl
index=zoom sourcetype="zoom:participant" join_result!="success"
| stats count by error_code, join_result, client_type
| sort -count
```
- **Implementation:** Capture join attempts with result, error code, meeting type, and IdP correlation if SAML. Alert on spikes in specific codes (e.g., 3000-series). Compare with Okta/Azure AD sign-in success for the same window.
- **Visualization:** Table (error_code, count), Line chart (failed joins over time), Bar chart (failures by client type).
- **CIM Models:** N/A

---

### UC-11.5.4 · Webex Device Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Room devices with high CPU, thermal, or firmware errors degrade meetings; proactive health reduces onsite truck rolls and VIP room incidents.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk`
- **Data Sources:** `sourcetype=webex:device`, Webex Control Hub device telemetry
- **SPL:**
```spl
index=webex sourcetype="webex:device"
| where health_state!="ok" OR cpu_pct > 85 OR temperature_c > 45
| stats latest(health_state) as state, max(cpu_pct) as max_cpu, max(temperature_c) as max_temp by device_id, product
| sort -max_cpu
```
- **Implementation:** Ingest Control Hub device inventory and health APIs. Poll or stream alerts for offline, warning, or error states. Track firmware version drift. Alert on sustained high CPU or temperature before automatic thermal throttling.
- **Visualization:** Status grid (device × health), Table (devices over threshold), Line chart (CPU/temperature trend).
- **CIM Models:** N/A

---

### UC-11.5.5 · Webex Room System Uptime
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Room system availability underpins executive and boardroom SLAs; uptime trending supports hardware refresh and network path decisions.
- **App/TA:** `ta_cisco_webex_add_on_for_splunk`
- **Data Sources:** `sourcetype=webex:device`, device online/offline events
- **SPL:**
```spl
index=webex sourcetype="webex:device"
| eval up=if(connection_state="connected",1,0)
| timechart span=1h avg(up) as uptime_ratio by device_id
| where uptime_ratio < 0.99
```
- **Implementation:** Derive online state from heartbeat or Control Hub connectivity. Compute rolling uptime per room vs. expected business hours. Alert on devices below 99% weekly uptime or prolonged offline spans.
- **Visualization:** Line chart (uptime ratio by room), Single value (fleet uptime %), Table (rooms below SLA).
- **CIM Models:** N/A

---

### UC-11.5.6 · Video Conferencing License Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Underused licenses waste budget; near-capacity entitlements risk meeting blocks during peaks—utilization guides true-up and consolidation across Zoom/Webex/Teams.
- **App/TA:** Splunk Connect for Zoom, Webex TA, Microsoft 365 licensing inputs
- **Data Sources:** `sourcetype=zoom:account`, `sourcetype=webex:license`, `sourcetype=m365:license`
- **SPL:**
```spl
index=saas (sourcetype="zoom:account" OR sourcetype="webex:license" OR sourcetype="m365:license")
| eval used_pct=round(assigned_licenses/nullif(total_licenses,0)*100,1)
| where used_pct > 90 OR used_pct < 60
| table platform, sku, assigned_licenses, total_licenses, used_pct
```
- **Implementation:** Ingest license counts and active assignments from each vendor’s admin API on a daily schedule. Map SKUs to collaboration products. Alert above 90% utilization and report under-60% for reclamation. Normalize multi-platform duplicates where possible via email identity.
- **Visualization:** Bar chart (utilization % by platform), Table (SKU detail), Line chart (assigned licenses over time).
- **CIM Models:** N/A

---

### UC-11.5.7 · Meeting Recording Storage Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Cloud recording storage grows with retention policies; trending consumption avoids surprise overages and informs lifecycle rules for compliance vs. cost.
- **App/TA:** Splunk Connect for Zoom, Webex TA, Microsoft Graph / Teams recording metadata
- **Data Sources:** `sourcetype=zoom:recording`, `sourcetype=webex:recording`, `sourcetype=m365:teams_recording`
- **SPL:**
```spl
index=saas (sourcetype="zoom:recording" OR sourcetype="webex:recording" OR sourcetype="m365:teams_recording")
| eval size_gb=round(storage_bytes/1073741824,2)
| timechart span=1d sum(size_gb) as daily_gb by platform
```
- **Implementation:** Ingest recording completion events with byte size and retention class. Sum daily growth per platform. Project growth with linear regression or `predict` on a single series for 30-day forecast. Alert when projected storage crosses budget tiers. Pair with legal hold tags where applicable.
- **Visualization:** Area chart (storage growth by platform), Line chart (daily_gb trend), Table (largest tenants or sites).
- **CIM Models:** N/A

---

### UC-11.5.8 · Teams Meeting Quality Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Teams Call Quality Dashboard (CQD) data exposes poor Wi‑Fi, VPN, or PSTN legs; Splunk rollups unify CQD with org context for targeted network fixes.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services, Microsoft 365 Add-on
- **Data Sources:** `sourcetype=m365:teams_cqd`, Call Records / CQD feed
- **SPL:**
```spl
index=m365 sourcetype="m365:teams_cqd"
| where avg_video_frame_loss_pct > 5 OR avg_round_trip_time_ms > 300 OR poor_stream_pct > 10
| stats avg(avg_video_frame_loss_pct) as avg_loss, avg(avg_round_trip_time_ms) as avg_rtt, avg(poor_stream_pct) as poor_pct by user_principal_name, building_name
| sort -poor_pct
```
- **Implementation:** Ingest CQD or Call Records via Graph / data export. Join subnet or building names from network inventory. Baseline per site. Alert when poor stream percentage or packet loss exceeds SLA. Feed top offenders to network ops.
- **Visualization:** Table (users/sites with worst quality), Line chart (poor stream % trend), Map or bar chart (quality by building).
- **CIM Models:** N/A
