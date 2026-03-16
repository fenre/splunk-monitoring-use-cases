## 11. Email & Collaboration

### 11.1 Microsoft 365 / Exchange

**Primary App/TA:** Splunk Add-on for Microsoft Office 365 (`Splunk_TA_MS_O365`), Splunk Add-on for Microsoft Exchange.

---

### UC-11.1.1 · Mail Flow Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Email is business-critical. Mail flow issues (queuing, NDRs) directly impact productivity and customer communication.
- **App/TA:** `Splunk_TA_MS_O365`, Exchange message tracking
- **Data Sources:** Exchange message tracking logs, O365 message trace
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:messageTrace"
| timechart span=1h count by Status
```
- **Implementation:** Ingest Exchange message tracking logs or O365 message trace via Management Activity API. Track delivery rates, queue lengths, and NDR volumes. Alert on delivery failures exceeding baseline. Monitor mail flow latency.
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

### UC-11.3.24 · Jira Data Center Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** JMX metrics, request duration, and attachment storage indicate Jira health. Slow requests frustrate users; disk usage growth risks outages. Enables capacity planning and performance tuning.
- **App/TA:** Custom JMX input (Jolokia), Jira REST API
- **Data Sources:** Jira JMX MBeans (heap, threads, request duration), /rest/api/2/serverInfo, Jira access logs
- **SPL:**
```spl
index=jira sourcetype="jira:jmx"
| eval heap_used_pct=if(HeapMemoryMax>0, round(HeapMemoryUsed/HeapMemoryMax*100, 1), null())
| where heap_used_pct > 85 OR ThreadCount > 500 OR RequestDurationP95 > 3000
| bin _time span=5m
| stats latest(HeapMemoryUsed) as heap_used, latest(HeapMemoryMax) as heap_max, latest(heap_used_pct) as heap_pct, latest(ThreadCount) as threads, latest(RequestDurationP95) as p95_ms by _time, host
| where heap_pct > 85 OR threads > 500 OR p95_ms > 3000
| table _time, host, heap_used, heap_max, heap_pct, threads, p95_ms
```
- **Implementation:** Deploy Jolokia agent on Jira application nodes and configure Splunk to poll JMX MBeans (java.lang:type=Memory, java.lang:type=Threading, com.atlassian.jira:type=RequestMetrics). Poll every 60 seconds. Ingest Jira access logs for request duration percentiles. Optionally poll /rest/api/2/serverInfo for version and build. Alert on heap >85%, thread count >500, or P95 request duration >3 seconds. Track attachment storage via JMX or filesystem metrics. Correlate with database and disk I/O.
- **Visualization:** Line chart (heap usage, thread count, P95 latency), Gauge (heap %), Table (performance metrics by node), Bar chart (request duration by endpoint).
- **CIM Models:** N/A

---

### 11.4 Cisco Spaces & Location Intelligence

### UC-11.4.1 · Building Occupancy Trending and Capacity Planning
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Provides real-time and historical people counts per building, floor, and zone using data from Meraki APs and cameras. Supports compliance with fire safety capacity limits, energy management optimization (HVAC scheduling based on actual occupancy), and real estate planning. Trending data reveals patterns — which floors are overcrowded on Tuesdays, which buildings are underused on Fridays — enabling data-driven workplace strategy decisions.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), Cisco Spaces Firehose API
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

---

### UC-11.4.2 · Visitor Dwell Time and Movement Flow Analysis
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

---

### UC-11.4.3 · Environmental Sensor Monitoring (Temperature, Humidity, Air Quality)
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

---

### UC-11.4.4 · Asset Tracking and Geofencing Alerts
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

---

### UC-11.4.5 · After-Hours Wireless Presence Detection
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

---

### UC-11.4.6 · Workspace Utilization and Ghost Booking Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Combines room booking data with actual physical occupancy from Cisco Spaces and Webex device sensors to calculate true workspace utilization. Identifies "ghost bookings" — rooms reserved but never occupied — which waste available space and frustrate employees searching for rooms. Reveals which rooms are most/least popular, optimal room sizes for actual group sizes, and peak usage patterns. Directly supports real estate cost reduction by providing evidence-based recommendations for space consolidation, redesign, or expansion.
- **App/TA:** `Spaces Add-On for Splunk` (Splunkbase 8485), `ta_cisco_webex_add_on_for_splunk` (GitHub), calendar integration
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Webex Room Kit, Room Bar, Room Navigator, Webex Board
- **Data Sources:** Cisco Spaces occupancy data, Webex device people count (RoomAnalytics), calendar/booking system data
- **SPL:**
```spl
index=cisco_spaces sourcetype="cisco:spaces:workspace"
| join type=left workspaceId [search index=webex sourcetype="webex:workspace_bookings" | fields workspaceId, bookingStart, bookingEnd, organizer]
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

---

