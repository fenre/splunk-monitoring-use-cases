## 9. Identity & Access Management

### 9.1 Active Directory / Entra ID

**Primary App/TA:** Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) for Entra ID.

---

### UC-9.1.1 · Brute-Force Login Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Windows Security Event Log (Event ID 4625 — failed logon)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| stats count by Account_Name, Source_Network_Address
| where count > 10
| sort -count
```
- **Implementation:** Deploy the Universal Forwarder on all Domain Controllers with `[WinEventLog://Security]` enabled. Ensure the GPO enables Audit Logon Success and Failure. Alert with `stats count by Account_Name, src span=15m` when count exceeds 10. Suppress break-glass and service accounts via a `privileged_accounts` lookup to reduce false positives.
- **Visualization:** Table (accounts with failure counts), Line chart (failure rate over time), Geo map (source IPs).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-9.1.2 · Account Lockout Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (Event ID 4740 — account locked out)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time, Account_Name, CallerComputerName
| sort -_time
```
- **Implementation:** Forward DC Security logs. Alert on each lockout with source workstation included. Create report of recurring lockouts for proactive investigation. Correlate with 4625 events to find the failing source.
- **Visualization:** Table (lockouts with source), Bar chart (top locked accounts), Line chart (lockout trend).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-9.1.3 · Privileged Group Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Adding accounts to Domain Admins or Enterprise Admins (EventCode 4728/4732/4756) in minutes limits blast radius from stolen Tier-0 credentials. Immediate detection supports audit evidence for privileged access changes and enables rapid containment before lateral movement escalates.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4728 — member added to security-enabled global group, 4732 — local group, 4756 — universal group)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4728,4732,4756)
| search TargetUserName IN ("Domain Admins","Enterprise Admins","Schema Admins","Administrators")
| table _time, MemberName, TargetUserName, SubjectUserName
```
- **Implementation:** Forward DC Security logs. Create alert for any membership change to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Backup Operators). Integrate with change management for validation.
- **Visualization:** Table (membership changes), Timeline (change events), Single value (changes this week).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-9.1.4 · Service Account Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4624 — successful logon, Logon Type field)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624
| lookup service_accounts.csv Account_Name OUTPUT expected_hosts, account_type
| where account_type="service" AND (Logon_Type=2 OR Logon_Type=10 OR NOT match(src_host, expected_hosts))
| table _time, Account_Name, Logon_Type, src_host
```
- **Implementation:** Maintain lookup of service accounts with expected Logon Types and source hosts. Alert on interactive logon (Type 2, 10) or unexpected source. Regularly audit service account inventory with AD queries.
- **Visualization:** Table (anomalous service account usage), Timeline (events), Bar chart (anomalies by account).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.5 · Kerberos Ticket Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4768 — TGT request, 4769 — TGS request)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count by Account_Name, Service_Name
| where count > 5
| sort -count
```
- **Implementation:** Forward 4768/4769 events from DCs. Detect Kerberoasting by filtering for RC4 encryption (0x17) on TGS requests. Detect Golden Ticket by looking for TGT requests with unusual encryption types or from non-DC sources.
- **Visualization:** Table (suspicious Kerberos requests), Bar chart (requests by encryption type), Timeline (anomalous events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.6 · Password Policy Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4723 — password change attempt, 4724 — password reset attempt)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4723, 4724)
| stats count(eval(Keywords="Audit Failure")) as failures, count(eval(Keywords="Audit Success")) as successes by Account_Name
| where failures > 3
```
- **Implementation:** Forward DC Security logs. Track password change success/failure rates. Alert on excessive failures per user. Monitor 4724 (admin resets) separately as these bypass self-service and may indicate social engineering.
- **Visualization:** Table (users with failures), Bar chart (failure rate by user), Pie chart (change vs reset).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.7 · GPO Modification Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (5136 — directory service object modified)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectClass="groupPolicyContainer"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
```
- **Implementation:** Enable "Audit Directory Service Changes" via GPO. Forward DC Security logs. Alert on any GPO modification. Correlate with change management tickets. Track which GPOs are modified most frequently.
- **Visualization:** Table (GPO changes with details), Timeline (modification events), Bar chart (changes by admin).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.8 · AD Replication Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Replication failures cause authentication issues, stale group memberships, and inconsistent policy application across sites.
- **App/TA:** `Splunk_TA_windows`, `repadmin` scripted input
- **Data Sources:** Directory Service event log, `repadmin /showrepl` output
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (1864,1865,2042,2087)
| table _time, ComputerName, EventCode, Message
| sort -_time
```
- **Implementation:** Forward Directory Service event logs from DCs. Run `repadmin /showrepl` via scripted input daily. Alert on replication failures (Event IDs 1864, 2042, 2087). Track replication latency between sites.
- **Visualization:** Table (replication status by DC pair), Status grid (DC × replication health), Timeline (failure events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.9 · LDAP Query Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Expensive LDAP queries degrade DC performance affecting authentication for all users. Detection enables query optimization.
- **App/TA:** `Splunk_TA_windows`, Directory Service diagnostics
- **Data Sources:** Directory Service event log (Event ID 1644 — expensive search), Field Engineering diagnostics
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=1644
| rex "Entries Visited\s+:\s+(?<entries_visited>\d+)"
| where entries_visited > 10000
| table _time, ComputerName, entries_visited, Message
```
- **Implementation:** Enable LDAP search diagnostics (registry key: "15 Field Engineering" value "Expensive Search Results Threshold" = 10000). Forward Directory Service logs. Alert on queries visiting >10K entries. Identify and optimize expensive applications.
- **Visualization:** Table (expensive queries), Bar chart (queries by source application), Line chart (expensive query frequency).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.10 · Stale Account Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Stale accounts are an attack surface — unused accounts may be compromised without detection. Regular cleanup reduces risk.
- **App/TA:** Scripted input (PowerShell AD query)
- **Data Sources:** AD attributes (lastLogonTimestamp, pwdLastSet) via scripted input
- **SPL:**
```spl
index=ad sourcetype="ad:accounts"
| eval days_inactive=round((now()-lastLogon)/86400)
| where days_inactive > 90 AND enabled="True"
| table samAccountName, displayName, days_inactive, ou, lastLogon
| sort -days_inactive
```
- **Implementation:** Run PowerShell script querying AD for lastLogonTimestamp weekly. Export to CSV/JSON and ingest. Flag accounts inactive >90 days. Cross-reference with HR systems for departed employees. Report for access review.
- **Visualization:** Table (stale accounts), Bar chart (stale accounts by OU), Single value (total stale accounts), Pie chart (by account type).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.11 · Entra ID Risky Sign-Ins
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID sign-in logs, risk detection events (via Graph API)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin"
| where riskLevelDuringSignIn IN ("high","medium")
| table _time, userPrincipalName, ipAddress, location, riskLevelDuringSignIn, riskDetail
| sort -_time
```
- **Implementation:** Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Filter for medium/high risk detections. Alert on high-risk sign-ins. Correlate with on-prem AD events for hybrid investigations.
- **Visualization:** Table (risky sign-ins), Geo map (sign-in locations), Line chart (risk events over time), Bar chart (risk types).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.1.12 · Conditional Access Policy Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID sign-in logs (conditionalAccessStatus field)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin" conditionalAccessStatus="failure"
| stats count by userPrincipalName, appDisplayName, conditionalAccessPolicies{}.displayName
| sort -count
```
- **Implementation:** Ingest Entra ID sign-in logs. Filter for Conditional Access failures. Track failure rates per policy and per user. Alert on sudden spikes indicating policy misconfiguration. Report on most-blocked policies and applications.
- **Visualization:** Bar chart (failures by policy), Table (blocked users), Line chart (failure rate trend), Pie chart (failures by application).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-9.1.13 · AD Certificate Services Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** Internal CA-issued certificates approaching expiry; missed renewals cause outages.
- **App/TA:** `Splunk_TA_windows`, custom scripted input (certutil)
- **Data Sources:** ADCS issued certificates database (certutil -view), Certificate Services logs
- **SPL:**
```spl
index=adcs sourcetype="adcs:cert_inventory"
| eval days_to_expiry=round((expiry_epoch-now())/86400)
| where days_to_expiry < 30 AND days_to_expiry > 0
| table _time, subject, issuer, days_to_expiry, serial_number
| sort days_to_expiry
```
- **Implementation:** Run `certutil -view -restrict "Disposition=20"` (issued certs) on CA servers via scripted input daily. Parse output and compute days until expiry. Alert on certificates expiring within 30 days. Include Certificate Services event logs (Event ID 100–107) for issuance/renewal events. Maintain lookup of critical certs (e.g., LDAPS, VPN) for prioritized alerts.
- **Visualization:** Table (expiring certificates), Single value (certs expiring in 30 days), Gauge (days until next expiry), Bar chart (expiry by issuer).
- **CIM Models:** N/A

---

### UC-9.1.14 · Service Account Password Age
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Service accounts with passwords older than policy permits increase risk exposure.
- **App/TA:** `Splunk_TA_windows` (AD inventory), SA-ldapsearch
- **Data Sources:** AD attribute pwdLastSet on service accounts
- **SPL:**
```spl
index=ad sourcetype="ad:accounts"
| search objectClass=serviceAccount OR samAccountName=svc_* OR samAccountName=*_svc
| eval days_since_pwd=round((now()-(pwdLastSet/10000000-11644473600))/86400)
| where days_since_pwd > 90 AND enabled="True"
| table samAccountName, displayName, days_since_pwd, ou
| sort -days_since_pwd
```
- **Implementation:** Run PowerShell or ldapsearch script querying AD for service accounts (filter by naming convention or OU). Export pwdLastSet and convert to days. Ingest via scripted input. Alert on accounts exceeding policy (e.g., >90 days). Maintain lookup of accounts with approved exceptions. Report for quarterly access reviews.
- **Visualization:** Table (overdue service accounts), Bar chart (password age by OU), Single value (accounts over policy limit), Gauge (compliance %).
- **CIM Models:** N/A

---

### UC-9.1.15 · Kerberoasting Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Attackers request weakly encrypted TGS tickets for service accounts to crack passwords offline. Focused Kerberoasting detection complements generic Kerberos monitoring.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4769 — Kerberos service ticket requested)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count, values(Service_Name) as spns by Account_Name
| where count >= 5
| sort -count
```
- **Implementation:** Forward 4769 from DCs. Flag RC4 (0x17) TGS requests in bulk per user; tune thresholds for service accounts that legitimately use RC4. Enforce AES for sensitive SPNs in AD and rotate krbtgt on schedule.
- **Visualization:** Table (user, SPN, request count), Bar chart (Kerberoasting candidates by OU), Timeline (spikes).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src span=1h
| where count > 50
```

---

### UC-9.1.16 · Golden Ticket Indicators
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Forged TGTs often produce anomalous ticket lifetimes, encryption types, or DC sourcing. Heuristic alerts support hunt teams when krbtgt may be compromised.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4768 — Kerberos authentication ticket requested), 4624 (logon type 10 with Kerberos)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768
| eval ticket_life_h=(Ticket_Lifetime/3600)
| where ticket_life_h > 10 OR Ticket_Encryption_Type IN ("0xffffffff","0x12")
| table _time, Account_Name, Ticket_Encryption_Type, ticket_life_h, IpAddress
```
- **Implementation:** Baseline normal TGT lifetimes and encryption types per domain. Alert on unusual lifetimes, unknown ETYPE, or TGT requests not originating from expected workstations. Correlate with 4624 type 10 and lateral movement analytics.
- **Visualization:** Table (suspicious TGT events), Timeline, Single value (anomalies per day).
- **CIM Models:** Authentication

---

### UC-9.1.17 · Entra Conditional Access Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Policy edits can weaken MFA, device compliance, or location controls org-wide. Auditing changes supports SOC2/ISO and incident response.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID audit logs (`DirectoryAudit` — Conditional Access policy create/update/delete)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:audit"
| search "Conditional Access" OR activityDisplayName="Update conditional access policy"
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, activityDisplayName, result
| sort -_time
```
- **Implementation:** Ingest Entra audit logs via Graph. Alert on any CA policy lifecycle change; require change ticket correlation. Snapshot policy IDs in lookups for crown-jewel apps.
- **Visualization:** Timeline (policy changes), Table (actor, policy, result), Bar chart (changes by admin).
- **CIM Models:** Change

---

### UC-9.1.18 · Hybrid Join Device Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Hybrid Azure AD join state and Intune compliance gate access; drift from compliant blocks users and signals stale or tampered endpoints.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Microsoft Intune / Graph scripted input
- **Data Sources:** Entra ID device objects (`trustType`, `isCompliant`, `profileType`), Intune compliance reports
- **SPL:**
```spl
index=azure sourcetype="azure:intune:devices" OR sourcetype="azure:aad:devices"
| where trustType="ServerAd" AND (isCompliant="false" OR isCompliant="False")
| stats latest(_time) as last_seen by deviceId, displayName, managementType, isCompliant
| sort -last_seen
```
- **Implementation:** Ingest device inventory from Graph/Intune on a schedule. Join with sign-in logs for non-compliant hybrid devices. Alert on compliance flip from true to false or long-running non-compliance.
- **Visualization:** Table (non-compliant hybrid devices), Pie chart (compliant vs not), Line chart (non-compliance trend).
- **CIM Models:** Endpoint

---

### UC-9.1.19 · LAPS Password Rotation Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Security
- **Value:** Failed LAPS rotations leave predictable local admin passwords; attackers target stale LAPS attributes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Operational log `Microsoft-Windows-LAPS/Operational` (Event IDs 10023, 10024, 10025, 10026), or legacy CSE events
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-LAPS/Operational" EventCode IN (10023,10024,10025,10026)
| stats count by ComputerName, EventCode, Message
| where count > 0
| sort -count
```
- **Implementation:** Forward LAPS Operational log from all domain-joined clients that use LAPS. Map Event IDs to rotation success/failure. Alert on repeated failures per OU or GPO scope. Correlate with GPO and network issues.
- **Visualization:** Table (hosts with failures), Bar chart (failures by OU), Single value (failed rotations 24h).
- **CIM Models:** N/A

---

### UC-9.1.20 · AD Replication Topology Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Configuration
- **Value:** New connections, site link, or bridgehead changes can indicate persistence or misconfiguration affecting auth paths.
- **App/TA:** `Splunk_TA_windows`, `repadmin` / scripted input
- **Data Sources:** Directory Service events (KCC topology), scripted `repadmin /showconn` / `nltest`
- **SPL:**
```spl
index=wineventlog (sourcetype="WinEventLog:Directory Service" EventCode IN (1308,1311,1394)) OR sourcetype="ad:topology"
| table _time, host, EventCode, Message, connection_from, connection_to
| sort -_time
```
- **Implementation:** Enable KCC and replication diagnostics. Ingest periodic topology snapshots. Alert on new unexpected replication partners or disabled site links outside change windows.
- **Visualization:** Timeline (topology events), Table (connection changes), Diagram export (optional via lookup).
- **CIM Models:** N/A

---

### UC-9.1.21 · AdminSDHolder Modification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Changes to AdminSDHolder or SDProp timing can preserve attacker persistence on privileged accounts.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (5136 — directory service object modified), object DN containing AdminSDHolder
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectDN="*CN=AdminSDHolder,CN=System*"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```
- **Implementation:** Enable DS change auditing on DCs. Alert on any modification to AdminSDHolder ACL or attributes. Review regularly for expected adminSDHolder propagation delays.
- **Visualization:** Table (changes), Timeline, Single value (changes per quarter — expect near zero).
- **CIM Models:** Change

---

### UC-9.1.22 · GPO Tampering Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Tampering via SYSVOL (file-level) may bypass 5136-only monitoring. File integrity on GPO paths catches unauthorized edits.
- **App/TA:** `Splunk_TA_windows`, FIM TA (e.g., Splunk FIM or OSSEC)
- **Data Sources:** GPO change events (5136), SYSVOL file integrity events, DFS-R replication errors for SYSVOL
- **SPL:**
```spl
index=ossec sourcetype="ossec:fim" OR index=fim sourcetype="fim:change"
| search path="*\\SYSVOL\\*\\Policies\\*"
| stats count by path, user, action
| sort -count
```
- **Implementation:** Deploy FIM on DCs or SYSVOL replica members. Alert on new/modified GPO files outside change windows. Correlate with 5136 and DFS-R 4412/5004 events.
- **Visualization:** Table (file paths changed), Timeline, Bar chart (changes by DC).
- **CIM Models:** Change

---

### UC-9.1.23 · Entra PIM Activation Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Privileged Identity Management activations grant time-bound admin roles; auditing ensures approvals and detects abuse.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra audit logs (`Add member to role completed`, PIM `RequestApproved` / `RoleAssignmentSchedule`)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:audit"
| search "PIM" OR activityDisplayName IN ("Add member to role in PIM completed","Add member to role completed")
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, result, activityDisplayName
| sort -_time
```
- **Implementation:** Ingest PIM-related audit events. Alert on activations outside business hours, without ticket ID (custom field), or for highly privileged roles. Report monthly for access reviews.
- **Visualization:** Table (activations), Bar chart (role activations by user), Timeline.
- **CIM Models:** Authentication

---

### UC-9.1.24 · Stale Computer Account Cleanup
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Stale computer objects enable rogue domain joins and clutter access reviews. Tracking supports automated disable/delete workflows.
- **App/TA:** Scripted input (PowerShell `Get-ADComputer`)
- **Data Sources:** AD computer attributes (`lastLogonTimestamp`, `pwdLastSet`, `whenCreated`)
- **SPL:**
```spl
index=ad sourcetype="ad:computers"
| eval days_stale=round((now()-lastLogonTimestamp)/86400)
| where days_stale > 90 AND Enabled="True"
| table samAccountName, operatingSystem, days_stale, distinguishedName
| sort -days_stale
```
- **Implementation:** Export computer inventory weekly. Join with DHCP/DNS for false positives. Feed cleanup automation; exclude known appliance OUs via lookup.
- **Visualization:** Table (stale computers), Bar chart (stale count by OU), Single value (candidates for cleanup).
- **CIM Models:** N/A

---

### UC-9.1.25 · AD Forest Trust Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Trust direction and selective authentication changes alter cross-forest attack surface; distinct from one-off session events.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4706 — trust modified, 4713 — trust deleted, 4716 — trusted domain information modified)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706,4713,4716)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection, SidFiltering
| sort -_time
```
- **Implementation:** Forward all DC Security logs. Require CAB approval for trust changes. Alert on selective auth disablement or inbound trust creation.
- **Visualization:** Table (trust changes), Timeline, Single value (changes per year).
- **CIM Models:** Change

---

### UC-9.1.26 · Certificate Template Abuse (ESC Attacks)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Misconfigured templates (ESC1/ESC8) allow domain escalation via certificate requests. Monitoring issuance and template edits reduces exposure.
- **App/TA:** `Splunk_TA_windows`, AD CS logs
- **Data Sources:** Certificate Services (4886, 4887, 4888), AD CS template change auditing (5136 on `CN=Certificate Templates`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4886
| search Requester!="" Template_OID=*
| lookup cert_template_risk Template_OID OUTPUT risk_esc
| where risk_esc IN ("ESC1","ESC8")
| table _time, Requester, Template_OID, risk_esc, ComputerName
```
- **Implementation:** Enable CA and template auditing. Maintain lookup mapping template OIDs to ESC categories (per SpecterOps research). Alert on enrollment to high-risk templates and on template ACL/schema changes.
- **Visualization:** Table (risky enrollments), Bar chart (requests by template), Timeline.
- **CIM Models:** N/A

---


### UC-9.1.27 · Active Directory Replication
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Directory Service`, custom scripted input (`repadmin /replsummary`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" (EventCode=1864 OR EventCode=1865 OR EventCode=2042 OR EventCode=1388 OR EventCode=1988)
| table _time host EventCode Message
| sort -_time

| comment "Replication health from scripted input"
index=ad sourcetype=repadmin_replsummary
| where failures > 0
| table source_dc dest_dc failures last_failure last_success
```
- **Implementation:** Collect Directory Service event log from all DCs. Create scripted input running `repadmin /replsummary /csv` daily. Alert on any replication failure events. Critical alert on EventCode 2042 (tombstone lifetime exceeded).
- **Visualization:** Table of replication partners with status, Events timeline, Network diagram of DC replication.
- **CIM Models:** N/A

---

### UC-9.1.28 · AD Certificate Services (ADCS) Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** ADCS misconfigurations enable privilege escalation (ESC1-ESC8 attacks). Monitoring certificate requests catches unauthorized certificate enrollment for domain admin impersonation.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4886, 4887, 4888)
| eval action=case(EventCode=4886,"Request received",EventCode=4887,"Certificate issued",EventCode=4888,"Certificate denied")
| stats count by Requester, CertificateTemplate, SubjectName, action
| where CertificateTemplate IN ("User","SmartcardLogon","Machine") AND NOT match(Requester, "(?i)(SYSTEM|machine\\$)")
| sort -count
```
- **Implementation:** Enable Certificate Services auditing on CA servers. EventCode 4887=certificate issued — track who requested which template. Alert on certificates with Subject Alternative Names (SANs) containing admin usernames (ESC1 attack). Monitor for certificate requests from non-standard templates. Track enrollment agent certificates (ESC3). Audit CA configuration for overly permissive templates with `certutil -v -template`.
- **Visualization:** Table (certificate issuances), Bar chart (requests by template), Timeline, Alert on SAN mismatches.
- **CIM Models:** N/A

---

### 9.2 LDAP Directories

**Primary App/TA:** Syslog inputs, custom scripted inputs for LDAP server stats.

---

### UC-9.2.1 · Bind Failure Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.
- **App/TA:** Syslog, LDAP server logs
- **Data Sources:** OpenLDAP syslog, 389 Directory access log
- **SPL:**
```spl
index=ldap sourcetype="syslog" "BIND" "err=49"
| stats count by src, bind_dn
| where count > 10
| sort -count
```
- **Implementation:** Forward LDAP server syslog to Splunk. Parse bind operations and result codes (err=49 = invalid credentials). Alert on >10 failures per source per 15 minutes. Correlate with application health monitoring.
- **Visualization:** Table (bind failures by source/DN), Line chart (failure rate), Bar chart (top failing sources).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-9.2.2 · Search Performance Degradation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Slow LDAP searches impact all applications relying on directory services for authentication and authorization.
- **App/TA:** LDAP access log parsing
- **Data Sources:** OpenLDAP access log (search duration), 389 Directory access log
- **SPL:**
```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| where elapsed_ms > 1000
| stats count, avg(elapsed_ms) as avg_ms by base_dn, filter
| sort -avg_ms
```
- **Implementation:** Enable LDAP access logging with timing information. Parse search operations with duration. Alert on searches exceeding 1 second. Identify expensive filters (unindexed attributes, broad base DN). Recommend index creation.
- **Visualization:** Table (slow searches), Bar chart (avg duration by filter), Line chart (search latency trend).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.2.3 · Schema Modification Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.
- **App/TA:** LDAP audit log
- **Data Sources:** LDAP server audit log (schema modification events)
- **SPL:**
```spl
index=ldap sourcetype="openldap:audit"
| search "cn=schema" ("add:" OR "delete:" OR "replace:")
| table _time, modifier_dn, changetype, modification
```
- **Implementation:** Enable LDAP audit logging (overlay in OpenLDAP, audit log in 389 DS). Forward to Splunk. Alert on any schema modification. These should be extremely rare and always correlated with change tickets.
- **Visualization:** Timeline (schema changes), Table (change details), Single value (schema changes this month).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.2.4 · Replication Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** LDAP replication failures cause authentication inconsistencies and stale directory data across sites.
- **App/TA:** Scripted input, LDAP server logs
- **Data Sources:** LDAP replication logs, `ldapsearch` monitoring attributes (contextCSN)
- **SPL:**
```spl
index=ldap sourcetype="openldap:syncrepl"
| search "syncrepl" ("ERROR" OR "RETRY" OR "failed")
| stats count by host, provider
| where count > 0
```
- **Implementation:** Monitor LDAP replication status via scripted input querying contextCSN or replication agreements. Forward syncrepl logs. Alert on replication failures or increasing lag between providers and consumers.
- **Visualization:** Status grid (provider × consumer health), Table (replication status), Timeline (failure events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.2.5 · Azure AD / Entra ID Conditional Access Policy Evaluation Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Operational
- **Value:** Policy conflicts causing access denials; helps fine-tune conditional access and reduce user friction.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`)
- **Data Sources:** Azure AD Sign-in logs (conditionalAccessStatus, appliedConditionalAccessPolicies)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin"
| where conditionalAccessStatus="failure" OR conditionalAccessStatus="reportOnlyNotApplied"
| spath path=conditionalAccessPolicies{}
| mvexpand conditionalAccessPolicies{} limit=500
| spath input=conditionalAccessPolicies{} path=displayName
| spath input=conditionalAccessPolicies{} path=result
| where result="failure" OR result="reportOnlyNotApplied"
| stats count by displayName, result
| sort -count
```
- **Implementation:** Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Parse appliedConditionalAccessPolicies array for policy names and results. Alert on spikes in failures per policy. Track reportOnlyNotApplied for policy tuning. Correlate with userPrincipalName and appDisplayName to identify affected users and apps.
- **Visualization:** Bar chart (failures by policy), Table (blocked users with policy details), Line chart (failure rate trend), Pie chart (failures by application).
- **CIM Models:** Authentication

---

### UC-9.2.6 · LDAP Query Volume Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Performance
- **Value:** Sudden spikes in LDAP searches may indicate reconnaissance, brute enumeration, or misbehaving applications hammering directory services.
- **App/TA:** LDAP access log parsing, `Splunk_TA_windows` (Directory Service 1644)
- **Data Sources:** OpenLDAP access log (SEARCH count), AD DS expensive search / query stats
- **SPL:**
```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| bin _time span=15m
| stats count by src, _time
| eventstats median(count) as med by src
| where count > med*10 AND count > 100
| sort -count
```
- **Implementation:** Baseline searches per source per interval. Alert on statistical outliers. Correlate with known ETL jobs via lookup. On AD, combine with 1644 expensive search events.
- **Visualization:** Line chart (query volume by source), Table (spikes), Bar chart (top talkers).
- **CIM Models:** Authentication

---

### UC-9.2.7 · Bind Failure Rate Spikes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Fault
- **Value:** Elevated invalid credential rates often precede password spraying or application misconfiguration; complements per-event bind failure monitoring.
- **App/TA:** Syslog, LDAP server logs
- **Data Sources:** OpenLDAP syslog (err=49), AD DS LDAP interface events
- **SPL:**
```spl
index=ldap sourcetype="syslog" "BIND" ("err=49" OR "data 52e")
| bin _time span=15m
| stats count by src, _time
| where count > 50
| sort -count
```
- **Implementation:** Tune threshold to environment. Whitelist scanners and load balancers. Correlate with account lockouts and Entra hybrid sign-in failures if applicable.
- **Visualization:** Line chart (bind failure rate), Table (source IP, window count), Single value (spikes per day).
- **CIM Models:** Authentication

---

### UC-9.2.8 · Active Directory Schema Modification Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Compliance
- **Value:** Schema changes in AD (classes/attributes) are rare and high impact; complements generic LDAP schema logging for OpenLDAP/389.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (5136 — directory service object modified under `CN=Schema,CN=Configuration`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectDN="*CN=Schema,CN=Configuration*"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName
| sort -_time
```
- **Implementation:** Enable auditing on schema partition. Alert on any schema object add/modify. Require schema admin CAB approval for all changes.
- **Visualization:** Timeline (schema changes), Table (detail), Single value (changes per year).
- **CIM Models:** Change

---

### UC-9.2.9 · LDAP Signing Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Unsigned LDAP binds expose credentials to interception. Tracking enforcement and bind failures ensures GPO and domain controller settings are effective.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Directory Service event log (2886 — unsigned LDAP bind, 2887 — unsigned SASL)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (2886,2887)
| stats count by ComputerName, EventCode, Client_IP
| where count > 10
| sort -count
```
- **Implementation:** Enable LDAP signing requirements via GPO. Alert on sustained unsigned binds from specific apps; work with owners to enable signing/TLS. Do not alert on one-off legacy until remediated.
- **Visualization:** Table (clients with unsigned binds), Bar chart (by subnet), Line chart (trend toward zero).
- **CIM Models:** Authentication

---

### UC-9.2.10 · LDAPS Certificate Validation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** LDAPS clients failing TLS handshakes or cert validation indicate expired CAs, hostname mismatches, or MITM attempts.
- **App/TA:** Windows Schannel, OpenLDAP TLS logs
- **Data Sources:** System log Schannel errors (36870, 36866), slapd TLS errors
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName="Schannel" EventCode IN (36870,36866)
| stats count by ComputerName, EventCode, Message
| sort -count
```
- **Implementation:** Forward Schannel and LDAP server TLS logs. Map to cert renewal runbook. Alert on spike in handshake failures after cert rotation.
- **Visualization:** Table (hosts with TLS errors), Timeline, Single value (LDAPS errors 24h).
- **CIM Models:** N/A

---

### UC-9.2.11 · LDAP Channel Binding Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Channel binding tokens for LDAP/SASL mitigate relay attacks; monitoring confirms clients meet `ldapEnforceChannelBinding` policy.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Directory Service (3039 — rejected bind missing channel binding tokens when required)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=3039
| stats count by ComputerName, Client_IP
| where count > 5
| sort -count
```
- **Implementation:** Phase enforcement with reporting mode first. Identify legacy apps from Client_IP. Alert when moving to enforced mode and failures persist.
- **Visualization:** Table (clients failing channel binding), Bar chart (by application owner), Line chart (remediation trend).
- **CIM Models:** Authentication

---

### UC-9.2.12 · LDAP Referral Chaining Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Security
- **Value:** Excessive or looping referrals degrade auth and may indicate misconfigured base DNs or cross-domain abuse.
- **App/TA:** OpenLDAP / 389 DS access logs, AD debug (optional)
- **Data Sources:** LDAP access log lines containing `REFERRAL` or `v3 referral`
- **SPL:**
```spl
index=ldap sourcetype="openldap:access" (message="REFERRAL" OR like(_raw,"%referral%"))
| stats count, values(dn) as refs by src, base
| where count > 20
| sort -count
```
- **Implementation:** Parse referral responses in access logs. Baseline per app. Alert on referral storms or new referral targets. Correlate with GSSAPI/SASL cross-realm issues in hybrid setups.
- **Visualization:** Table (referral chains), Line chart (referral volume), Bar chart (by base DN).
- **CIM Models:** Authentication

---

### 9.3 Identity Providers (IdP) & SSO

**Primary App/TA:** Splunk Add-on for Okta (`Splunk_TA_okta`), Duo TA, custom API inputs for other IdPs.

---

### UC-9.3.1 · MFA Challenge Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.
- **App/TA:** `Splunk_TA_okta`, `Cisco Security Cloud` app (Splunkbase, replaces Duo Splunk Connector)
- **Data Sources:** Okta system log, Duo authentication log
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count(eval(outcome.result="FAILURE")) as failures, count(eval(outcome.result="SUCCESS")) as successes by actor.displayName
| eval fail_rate=round(failures/(failures+successes)*100,1)
| where fail_rate > 20
```
- **Implementation:** Ingest IdP logs via API. Track MFA success/failure rates per user and per factor type. Alert on high failure rates (>20% per user). Detect MFA fatigue patterns (rapid repeated pushes). Report on factor type distribution.
- **Visualization:** Bar chart (failure rate by user), Pie chart (factor type distribution), Line chart (MFA success rate trend).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-9.3.2 · Impossible Travel Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.
- **App/TA:** `Splunk_TA_okta`, custom correlation
- **Data Sources:** IdP sign-in logs with IP geolocation
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.session.start"
| iplocation client.ipAddress
| sort actor.alternateId, _time
| streamstats window=2 earliest(_time) as prev_time, earliest(lat) as prev_lat, earliest(lon) as prev_lon by actor.alternateId
| eval distance_km=round(6371*2*asin(sqrt(pow(sin((lat-prev_lat)*pi()/360),2)+cos(lat*pi()/180)*cos(prev_lat*pi()/180)*pow(sin((lon-prev_lon)*pi()/360),2))),0) , time_diff_hr=((_time-prev_time)/3600)
| where distance_km > 500 AND time_diff_hr < 2
```
- **Implementation:** Ingest IdP sign-in logs. Enrich with GeoIP. Calculate distance and time between consecutive logins per user. Alert when distance/time ratio is impossible (>500km in <2 hours). Whitelist VPN exit IPs and known travel patterns.
- **Visualization:** Geo map (sign-in locations with lines), Table (impossible travel events), Timeline (flagged events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.3 · Token Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.
- **App/TA:** `Splunk_TA_okta`, IdP audit logs
- **Data Sources:** IdP token issuance logs, application token validation logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as unique_ips by actor.alternateId, target{}.displayName
| where unique_ips > 3
```
- **Implementation:** Monitor token issuance and usage patterns. Alert on tokens used from multiple IPs (potential replay). Track token lifetime and refresh patterns. Detect anomalous token requests outside normal application patterns.
- **Visualization:** Table (anomalous token usage), Timeline (suspicious events), Bar chart (tokens by application).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.4 · Application Access Patterns
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** IdP application access logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| stats dc(actor.alternateId) as unique_users, count as total_access by target{}.displayName
| sort -unique_users
```
- **Implementation:** Track SSO events per application. Build user-application access matrix. Detect users accessing applications outside their normal pattern. Report on application usage for license optimization and access reviews.
- **Visualization:** Bar chart (top applications by user count), Table (application usage summary), Heatmap (user × application access).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.5 · IdP Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** IdP outage blocks all SSO authentication across the organization. Rapid detection enables failover and communication.
- **App/TA:** Scripted input (HTTP check), `Splunk_TA_okta`
- **Data Sources:** IdP status API, synthetic monitoring, Okta system health
- **SPL:**
```spl
index=synthetic sourcetype="http_check" target="*.okta.com"
| timechart span=1m avg(response_time_ms) as rt, count(eval(status_code>=500)) as errors
| where rt > 5000 OR errors > 0
```
- **Implementation:** Set up synthetic HTTP checks against IdP login endpoints every minute. Track response time and availability. Alert on response time >5 seconds or any 5xx errors. Subscribe to vendor status page updates as secondary source.
- **Visualization:** Single value (IdP uptime %), Line chart (response time), Status indicator (available/degraded/down).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.6 · Phishing-Resistant MFA Adoption
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks migration from phishable factors (SMS, phone) to phishing-resistant factors (FIDO2, WebAuthn). Supports zero-trust maturity goals.
- **App/TA:** `Splunk_TA_okta`, IdP MFA enrollment data
- **Data Sources:** IdP MFA enrollment logs, factor type metadata
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count by debugContext.debugData.factor
| eval factor_type=case(match(factor,"FIDO"),"phishing_resistant", match(factor,"push"),"medium", 1=1,"phishable")
| stats sum(count) as total by factor_type
```
- **Implementation:** Track MFA factor types used in authentication events. Classify as phishing-resistant (FIDO2, WebAuthn) vs phishable (SMS, voice, email). Report adoption percentages. Set organizational targets for phishing-resistant adoption.
- **Visualization:** Pie chart (factor type distribution), Line chart (phishing-resistant adoption trend), Table (users still on SMS).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.7 · Session Hijacking Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.
- **App/TA:** `Splunk_TA_okta`, IdP session logs
- **Data Sources:** IdP session activity logs, application session logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log"
| stats dc(client.ipAddress) as unique_ips, values(client.ipAddress) as ips by authenticationContext.externalSessionId, actor.alternateId
| where unique_ips > 2
| table actor.alternateId, authenticationContext.externalSessionId, unique_ips, ips
```
- **Implementation:** Track session IDs across events. Alert when a single session is used from multiple IP addresses simultaneously (excluding known VPN/proxy IPs). Correlate with user agent changes for additional confidence.
- **Visualization:** Table (hijacked sessions), Timeline (suspicious session events), Bar chart (users with multi-IP sessions).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.3.8 · SAML Assertion Replay Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Replayed SAML assertions can grant access without fresh authentication. Correlating assertion IDs and NotOnOrAfter windows catches reuse.
- **App/TA:** IdP logs, application SAML trace (e.g., Shibboleth, Okta, ADFS)
- **Data Sources:** SAML response logs with `AssertionID`, `InResponseTo`, `NotOnOrAfter`
- **SPL:**
```spl
index=saml sourcetype="saml:assertion"
| stats count by assertion_id, sp_entity_id
| where count > 1
| table assertion_id, sp_entity_id, count
```
- **Implementation:** Ingest assertion IDs from IdP or SP debug logs (privacy-safe hashing if needed). Alert on duplicate assertion_id for same SP. Enforce short assertion lifetimes at IdP.
- **Visualization:** Table (duplicate assertions), Timeline, Single value (replay attempts).
- **CIM Models:** Authentication

---

### UC-9.3.9 · OAuth Token Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Excessive refresh grants, scope expansion, or token use from new ASNs indicates stolen refresh tokens or malicious OAuth clients.
- **App/TA:** `Splunk_TA_okta`, Entra sign-in + Graph audit, API gateway logs
- **Data Sources:** `app.oauth2.token.grant`, Entra `TokenIssuance` / `Update application` (consent)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as ips by actor.alternateId, client_id
| where count > 200 OR ips > 5
| sort -count
```
- **Implementation:** Baseline grants per user and client. Alert on burst refresh or grants from many IPs. Revoke client on anomaly. Mirror logic for `azure:aad:signin` with `tokenIssuerType`.
- **Visualization:** Table (abusive clients), Line chart (grants over time), Bar chart (by client_id).
- **CIM Models:** Authentication

---

### UC-9.3.10 · SSO Session Hijacking Indicators
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Complements session ID correlation with user-agent flips, ASN changes mid-session, and impossible concurrent SSO from IdP telemetry.
- **App/TA:** `Splunk_TA_okta`, Entra sign-in logs
- **Data Sources:** IdP `user.authentication.sso` with session correlation ID, device fingerprint fields
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| transaction authenticationContext.externalSessionId maxpause=300 maxevents=50
| eval ua_change=if(mvcount(client.userAgent.rawUserAgent)>2,1,0)
| where ua_change=1
| table authenticationContext.externalSessionId, actor.alternateId, client.userAgent.rawUserAgent
```
- **Implementation:** Flag sessions with multiple user agents or countries within short windows. Tune for corporate VPN that rotates egress. Pair with UC-9.3.7 for IP-based hijack detection.
- **Visualization:** Table (suspicious sessions), Timeline, Bar chart (sessions with UA churn).
- **CIM Models:** Authentication

---

### UC-9.3.11 · Federated Trust Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Adding SAML/OIDC federation to new domains or apps expands blast radius; auditing trust metadata changes is essential.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_okta`
- **Data Sources:** Entra `Add federation to domain`, Okta `trustedOrigin.*` / `idp.*` lifecycle events
- **SPL:**
```spl
index=azure sourcetype="azure:aad:audit" activityDisplayName="Add external user"
   OR activityDisplayName="Add federation to domain"
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, activityDisplayName
| sort -_time
```
- **Implementation:** Alert on new federation partners, domain verification, or IdP metadata uploads. Require security review for new trust relationships.
- **Visualization:** Timeline (trust changes), Table (actor, target), Single value (new trusts per quarter).
- **CIM Models:** Change

---

### UC-9.3.12 · Consent Grant Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Users granting excessive delegated permissions to malicious OAuth apps is a common attack; monitoring consent events enables revocation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra audit logs (`Consent to application`, `Add OAuth2PermissionGrant`)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:audit"
| search "Consent" OR activityDisplayName="Add OAuth2PermissionGrant"
| spath path=targetResources{}
| mvexpand targetResources{} limit=500
| spath input=targetResources{} path=displayName
| table _time, initiatedBy.user.userPrincipalName, displayName, activityDisplayName
| sort -_time
```
- **Implementation:** Ingest consent-related audit events. Alert on consent to apps with high privilege (`RoleManagement.ReadWrite.Directory`) or new publisher IDs. Integrate with admin consent workflow.
- **Visualization:** Table (consent events), Bar chart (apps by consent count), Pie chart (user vs admin consent).
- **CIM Models:** Change

---

### UC-9.3.13 · App Registration Secret Expiry
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Security
- **Value:** Expired client secrets break automation and encourage long-lived secrets; proactive alerting avoids outages and insecure workarounds.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Graph scripted input
- **Data Sources:** Application credential inventory (`passwordCredentials.endDateTime`), audit when secret added
- **SPL:**
```spl
index=azure sourcetype="azure:graph:applications"
| eval days_left=round((strptime(endDateTime,"%Y-%m-%dT%H:%M:%SZ")-now())/86400)
| where days_left < 30 AND days_left > 0
| table appId, displayName, days_left, endDateTime
| sort days_left
```
- **Implementation:** Schedule Graph export of app registrations with secrets/certificates. Alert at 30/14/7 days. Map apps to owners via lookup.
- **Visualization:** Table (expiring secrets), Single value (next expiry), Gauge (apps past due).
- **CIM Models:** N/A

---

### UC-9.3.14 · Multi-Tenant App Access Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unexpected tenants or guest users accessing multi-tenant apps may indicate consent phishing or lateral SaaS movement.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra sign-in logs (`resourceTenantId`, `crossTenantAccessType`, `homeTenantId`)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin"
| where crossTenantAccessType IN ("b2bCollaboration","passthrough") AND resourceTenantId!=homeTenantId
| stats count by userPrincipalName, appDisplayName, resourceTenantId
| where count > 10
| sort -count
```
- **Implementation:** Baseline B2B access patterns. Alert on new resource tenants for crown-jewel apps. Correlate with consent events (UC-9.3.12).
- **Visualization:** Table (cross-tenant access), Heatmap (user × tenant), Line chart (volume).
- **CIM Models:** Authentication

---

### UC-9.3.15 · OAuth Scope Creep Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Applications accumulating scopes over time violate least privilege; comparing current vs approved scopes finds drift.
- **App/TA:** Graph API inventory, Okta `app.oauth2.*` events
- **Data Sources:** OAuth scope grants per `client_id`, approved scope lookup CSV
- **SPL:**
```spl
index=oauth sourcetype="oauth:scope_inventory"
| lookup oauth_scope_approved client_id OUTPUT approved_scopes
| eval extra_scopes=mvfilter(NOT match(approved_scopes, scope))
| where mvcount(extra_scopes)>0
| table client_id, scope, approved_scopes, extra_scopes
```
- **Implementation:** Export delegated/app role assignments from Graph weekly. Join with approved baseline. Alert on new sensitive scopes (`Mail.ReadWrite`, `Directory.ReadWrite.All`).
- **Visualization:** Table (scope drift), Bar chart (apps with extra scopes), Timeline.
- **CIM Models:** N/A

---

### UC-9.3.16 · Token Endpoint Rate Limiting
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Security
- **Value:** Throttling at `/oauth2/token` breaks integrations and may indicate credential stuffing or runaway automation.
- **App/TA:** API gateway / WAF logs, Entra `SignInLogs` with error codes, custom HEC from reverse proxy
- **Data Sources:** HTTP 429, `AADSTS50196` / `invalid_client` bursts, `rateLimit` in response headers
- **SPL:**
```spl
index=proxy sourcetype="access_combined" uri_path="/oauth2/v2.0/token"
| search status=429 OR like(_raw,"%rate limit%")
| bin _time span=5m
| stats count by client_id, _time
| where count > 100
| sort -count
```
- **Implementation:** Log token endpoint from AAD Application Proxy or API Management. Alert on 429 spikes per client_id. Implement exponential backoff in callers.
- **Visualization:** Line chart (429 rate), Table (top clients), Single value (throttled requests/hour).
- **CIM Models:** N/A

---

### 9.4 Privileged Access Management (PAM)

**Primary App/TA:** Vendor-specific TAs — CyberArk TA (`TA-CyberArk`), BeyondTrust TA, Delinea (Thycotic) TA.

---

### UC-9.4.1 · Privileged Session Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.
- **App/TA:** Splunk_TA_cyberark, BeyondTrust TA for Splunk
- **Data Sources:** PAM session logs (session start/end, target system, user, protocol)
- **SPL:**
```spl
index=pam sourcetype="cyberark:session"
| table _time, user, target_host, target_account, protocol, duration_min, session_id
| sort -_time
```
- **Implementation:** Install vendor PAM TA. Forward PAM vault/session logs to Splunk. Track all privileged sessions with full metadata. Alert on sessions outside business hours or to unexpected targets. Retain logs per compliance requirements.
- **Visualization:** Table (session history), Bar chart (sessions by user), Timeline (privileged access events), Heatmap (user × time of day).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-9.4.2 · Password Checkout Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unusual checkout patterns may indicate misuse. Tracking ensures accountability and supports investigations.
- **App/TA:** Splunk_TA_cyberark
- **Data Sources:** PAM vault logs (password retrieve/checkin events)
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault"
| search action="Retrieve" OR action="Checkin"
| transaction user, account maxspan=8h
| eval checkout_duration_hr=duration/3600
| where checkout_duration_hr > 4
| table user, account, target, checkout_duration_hr
```
- **Implementation:** Track password checkout and checkin events. Calculate checkout duration. Alert on checkouts exceeding policy limits (e.g., >4 hours). Flag accounts checked out but never checked in (hoarding). Report on checkout frequency per user.
- **Visualization:** Table (active checkouts), Bar chart (checkout duration by user), Line chart (checkout frequency trend).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.4.3 · Break-Glass Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Break-glass accounts provide emergency access and should rarely be used. Any usage requires immediate investigation and documentation.
- **App/TA:** Splunk_TA_cyberark, custom alert
- **Data Sources:** PAM vault events for break-glass accounts
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault"
| search account_type="break_glass" OR account IN ("emergency_admin","firecall_*")
| table _time, user, account, target, action
| sort -_time
```
- **Implementation:** Tag break-glass accounts in PAM. Create critical alert for any break-glass access. Require documented reason within 24 hours. Send notifications to security team and management. Track usage frequency for trend reporting.
- **Visualization:** Single value (break-glass uses this month — target: 0), Table (usage history), Timeline (break-glass events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.4.4 · Credential Rotation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Overdue password rotations increase exposure window if credentials are compromised. Compliance tracking ensures policy adherence.
- **App/TA:** PAM TA, scripted input
- **Data Sources:** PAM vault credential metadata (last rotation date, policy)
- **SPL:**
```spl
index=pam sourcetype="cyberark:account_inventory"
| eval days_since_rotation=round((now()-last_rotation_epoch)/86400)
| eval overdue=if(days_since_rotation > rotation_policy_days, "Yes", "No")
| where overdue="Yes"
| table account, target, days_since_rotation, rotation_policy_days
| sort -days_since_rotation
```
- **Implementation:** Export credential inventory from PAM periodically. Calculate days since last rotation vs policy requirement. Alert on overdue rotations. Track compliance percentage over time. Report to management monthly.
- **Visualization:** Table (overdue credentials), Single value (compliance %), Gauge (% compliant), Bar chart (overdue by platform).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.4.5 · Suspicious Session Commands
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detecting dangerous commands during privileged sessions enables real-time intervention before damage occurs.
- **App/TA:** CyberArk PSM, BeyondTrust session monitoring
- **Data Sources:** PAM session recordings/keystroke logs
- **SPL:**
```spl
index=pam sourcetype="cyberark:psm_transcript"
| search command IN ("rm -rf","format","del /s","DROP DATABASE","shutdown","halt","init 0")
| table _time, user, target_host, command, session_id
```
- **Implementation:** Enable PAM session recording and command logging. Parse keystroke transcripts. Alert immediately on high-risk commands (rm -rf, format, DROP DATABASE, etc.). Integrate with SOAR for automated session termination on critical detections.
- **Visualization:** Table (suspicious commands), Timeline (command events), Single value (high-risk commands today).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.4.6 · Vault Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** PAM vault downtime prevents all privileged access, blocking critical operations. Health monitoring ensures continuous availability.
- **App/TA:** PAM infrastructure monitoring, SNMP
- **Data Sources:** PAM vault system logs, component health APIs
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault_health"
| stats latest(status) as status, latest(replication_lag) as lag by vault_server, component
| where status!="Running" OR lag > 300
```
- **Implementation:** Monitor PAM vault components (vault server, PVWA, PSM, CPM). Track service availability, replication between primary/DR vault, and component health. Alert on any component failure or replication lag >5 minutes.
- **Visualization:** Status grid (component × health), Single value (vault uptime %), Table (unhealthy components), Line chart (replication lag).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-9.4.7 · Federated Identity Provider Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** IdP outages block all federated application access. Health monitoring ensures SSO availability and rapid incident response.
- **App/TA:** IdP monitoring, SAML/OIDC audit logs
- **Data Sources:** IdP health endpoints, federation error logs
- **SPL:**
```spl
index=iam sourcetype="idp:health"
| stats latest(status) as status, latest(response_ms) as latency by idp_host, tenant
| where status!="healthy" OR latency > 5000
| table idp_host, tenant, status, latency
```
- **Implementation:** Poll IdP health endpoints (e.g., SAML metadata, OIDC discovery) every 60 seconds. Ingest federation errors from app and IdP logs. Alert on status unhealthy or latency >5s. Correlate with user-reported SSO issues.
- **Visualization:** Status grid (IdP × health), Single value (IdP uptime %), Line chart (latency trend).
- **CIM Models:** Authentication

---

### UC-9.4.8 · API Token Usage Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual API token usage may indicate token theft or abuse. Detection supports least-privilege and incident response.
- **App/TA:** Cloud identity TAs, API gateway logs
- **Data Sources:** Token audit logs, API request logs
- **SPL:**
```spl
index=iam sourcetype="api:token_audit"
| stats dc(ip) as unique_ips, count as requests by token_id, _time span=1h
| where unique_ips > 3 OR requests > 1000
| sort -requests
```
- **Implementation:** Ingest token usage from IdP and API gateways. Baseline normal usage per token. Alert on new IPs, high request volume, or off-hours spikes. Rotate tokens on anomaly.
- **Visualization:** Table (anomalous tokens), Line chart (requests by token), Bar chart (unique IPs per token).
- **CIM Models:** Authentication

---

### UC-9.4.9 · Cross-Domain Trust Change Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Trust relationship changes can enable cross-domain abuse. Early detection prevents privilege escalation across forests.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4706 — trust modified, 4714 — trust created)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4714)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection
| sort -_time
```
- **Implementation:** Forward DC Security logs. Alert on any trust creation or modification. Require change approval for trust changes. Report on trust topology for audit.
- **Visualization:** Table (trust changes), Timeline (events), Single value (changes this week).
- **CIM Models:** Authentication

---

### UC-9.4.10 · Just-in-Time Access Request Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** JIT access reduces standing privilege. Monitoring request and approval patterns ensures policy compliance and detects abuse.
- **App/TA:** PAM / JIT access system logs
- **Data Sources:** Access request and approval audit logs
- **SPL:**
```spl
index=pam sourcetype="jit:requests"
| stats count, values(approver) as approvers by requester, resource, action
| where count > 20
| sort -count
```
- **Implementation:** Ingest JIT request and approval events. Alert on excessive requests per user, self-approvals, or access outside business hours. Report on approval latency and denial rate.
- **Visualization:** Table (request summary), Bar chart (requests by requester), Line chart (approval latency).
- **CIM Models:** Authentication

---

### UC-9.4.11 · Identity Sync Failure Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Sync failures cause stale or missing identities in target systems, leading to access denials or orphaned accounts. Detection enables quick remediation.
- **App/TA:** Identity sync / SCIM connector logs
- **Data Sources:** Sync job logs, connector error logs
- **SPL:**
```spl
index=iam sourcetype="sync:job"
| where status="failed" OR error_count > 0
| stats latest(_time) as last_failure, values(error_message) as errors by connector, target_system
| table connector, target_system, last_failure, errors
```
- **Implementation:** Ingest sync job results from IdP and HR-driven connectors. Alert on any failed run or error count >0. Track sync latency and delta size. Report on sync health by target.
- **Visualization:** Table (failed syncs), Single value (sync success %), Timeline (failure events).
- **CIM Models:** Authentication

---

### UC-9.4.12 · RADIUS / TACACS+ Server Response Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Authentication server latency and availability for network device auth; slow or unavailable RADIUS/TACACS+ blocks admin access to routers and switches.
- **App/TA:** Custom scripted input (radtest, tacacs_plus probe), syslog from NAS devices
- **Data Sources:** RADIUS accounting logs, NAS syslog, synthetic probe results
- **SPL:**
```spl
index=radius sourcetype="radius:probe"
| stats avg(response_ms) as avg_ms, max(response_ms) as max_ms, count(eval(response_ms>2000)) as slow_count by server, _time span=5m
| where avg_ms > 500 OR max_ms > 2000 OR slow_count > 0
| table _time, server, avg_ms, max_ms, slow_count
```
- **Implementation:** Run radtest (FreeRADIUS) or equivalent probe against RADIUS servers every 60 seconds. For TACACS+, use tacacs_plus Python library or custom script. Ingest probe results with response time. Forward NAS syslog (e.g., Cisco, Arista) for accounting and auth events. Alert on avg response >500ms or any probe timeout. Correlate with NAS auth failures to distinguish server vs network issues.
- **Visualization:** Line chart (response time by server), Table (slow probes), Single value (current avg latency), Status grid (server × health).
- **CIM Models:** N/A

---

### UC-9.4.13 · Active Directory Domain Controller Response Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** LDAP bind time, DNS query time per DC — slow DCs cause auth delays and user lockouts.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** LDAP bind latency probes, DNS query timing, Windows DC perf counters
- **SPL:**
```spl
index=ad_perf sourcetype="ad:dc_probe"
| stats avg(ldap_bind_ms) as avg_ldap, avg(dns_query_ms) as avg_dns, count(eval(ldap_bind_ms>1000)) as slow_ldap by dc_host, _time span=5m
| where avg_ldap > 500 OR avg_dns > 200 OR slow_ldap > 0
| table _time, dc_host, avg_ldap, avg_dns, slow_ldap
```
- **Implementation:** Run scripted input from monitoring host: perform LDAP bind (e.g., ldapsearch -x -H ldap://dc:389 -b "" -s base) and measure elapsed time; run nslookup or Resolve-DnsName for _ldap._tcp.dc._msdcs.domain. Ingest Windows perf counters (NTDS, LDAP Client Sessions) via Splunk_TA_windows. Alert on LDAP bind >1s or DNS >200ms. Identify overloaded DCs for load balancing.
- **Visualization:** Line chart (LDAP/DNS latency by DC), Table (slow DCs), Status grid (DC × response time tier), Single value (worst DC latency).
- **CIM Models:** N/A

---

### UC-9.4.14 · CyberArk Session Recording Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Real-time alerts on PSM recordings—policy violations, blocked commands, or session anomalies—enable SOC response before logout.
- **App/TA:** Splunk TA for CyberArk
- **Data Sources:** PSM recording events, policy violation syslog from PSM
- **SPL:**
```spl
index=pam sourcetype="cyberark:psm" OR sourcetype="cyberark:psm_alert"
| search alert_level IN ("High","Critical") OR policy_violation="true"
| table _time, user, target_account, session_id, alert_reason
| sort -_time
```
- **Implementation:** Forward PSM alert stream to Splunk. Map vendor severity to SOC tiers. Integrate with SOAR for session kill on critical patterns.
- **Visualization:** Timeline (alerts), Table (session detail), Single value (critical alerts 24h).
- **CIM Models:** Authentication

---

### UC-9.4.15 · Privileged Session Duration Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Sessions far longer than peer baseline may indicate data exfiltration or abandoned hijacked sessions.
- **App/TA:** CyberArk / BeyondTrust session logs
- **Data Sources:** PAM session start/end with duration
- **SPL:**
```spl
index=pam sourcetype="cyberark:session"
| eval dur_min=duration_sec/60
| eventstats median(dur_min) as med by target_account
| where dur_min > med*3 AND dur_min > 60
| table _time, user, target_account, dur_min, med
```
- **Implementation:** Baseline duration per target system type. Exclude known maintenance windows via lookup. Pair with UC-9.4.1 audit trail.
- **Visualization:** Table (long sessions), Box plot (duration by target), Line chart (max duration trend).
- **CIM Models:** Authentication

---

### UC-9.4.16 · Vault Synchronization Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Vault replication or DR sync failures risk split-brain or stale credentials; distinct from generic component health.
- **App/TA:** CyberArk Vault DR logs, vendor HA APIs
- **Data Sources:** `VaultReplication`, `DR` sync job status, cluster replication lag metrics
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault_replication"
| where status!="Success" OR lag_seconds > 120
| stats latest(_time) as last_evt, values(error) as errs by primary_vault, dr_vault
| table primary_vault, dr_vault, lag_seconds, errs
```
- **Implementation:** Ingest replication job results every minute. Alert on lag > policy (e.g., 2 minutes) or failed sync. Page vault admins for DR sites.
- **Visualization:** Line chart (lag), Table (failed jobs), Status grid (primary × DR).
- **CIM Models:** N/A

---

### UC-9.4.17 · Just-in-Time Access Request Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Analytics on JIT volume, self-approval, and after-hours patterns complements simple volume alerts (UC-9.4.10).
- **App/TA:** PAM JIT / Entra PIM logs
- **Data Sources:** Request ID, requester, approver, time-to-approve, business justification field
- **SPL:**
```spl
index=pam sourcetype="jit:requests"
| eval same_approver=if(requester=approver,1,0)
| eval after_hours=if(hour(_time) < 6 OR hour(_time) > 22,1,0)
| stats count, sum(same_approver) as self_approvals, sum(after_hours) as off_hours by requester
| where self_approvals > 0 OR off_hours > 5
| sort -count
```
- **Implementation:** Require justification text; alert on empty justification with approval. Report monthly JIT metrics to IAM governance.
- **Visualization:** Table (risky patterns), Bar chart (self-approvals), Heatmap (hour × requester).
- **CIM Models:** Authentication

---

### UC-9.4.18 · Emergency Break-Glass Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Real-time paging for emergency-only vault accounts beyond standard break-glass (UC-9.4.3)—includes usage from non-SOC networks.
- **App/TA:** Splunk TA for CyberArk, AD Security logs
- **Data Sources:** PAM checkout for accounts tagged `emergency_only`, 4624 for same sAMAccountName
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault" account_tag="emergency_only"
| lookup soc_networks subnet OUTPUT network_name
| where isnull(network_name)
| table _time, user, account, client_ip, action
| sort -_time
```
- **Implementation:** Define emergency accounts in PAM and AD. Alert on any checkout or interactive logon; require post-incident report within SLA. Correlate with major incident tickets.
- **Visualization:** Timeline (emergency usage), Table (detail), Single value (events outside SOC net).
- **CIM Models:** Authentication

---

### UC-9.4.19 · Shared Account Concurrent Login Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Shared privileged accounts used from two locations simultaneously indicate credential sharing or theft.
- **App/TA:** PAM session logs, bastion logs
- **Data Sources:** Session start with same `target_account` and overlapping time ranges
- **SPL:**
```spl
index=pam sourcetype="cyberark:session"
| eval end_time=_time+duration_sec
| sort target_account, _time
| streamstats window=2 current(src) as ip1 next(src) as ip2 current(_time) as t1 next(_time) as t2 by target_account
| where ip1!=ip2 AND t2 < end_time
| table target_account, ip1, ip2, t1, t2
```
- **Implementation:** Tune for load-balanced egress using known NAT pools. Prefer per-user vaulted accounts to eliminate shared IDs.
- **Visualization:** Table (concurrent sessions), Timeline, Bar chart (accounts with overlap events).
- **CIM Models:** Authentication

---

### UC-9.4.20 · PAM Agent Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** CPM, PSM, and PVWA agents offline block rotation and session capture; distinct from vault binary health (UC-9.4.6).
- **App/TA:** CyberArk component monitoring, SNMP/HEARTBEAT logs
- **Data Sources:** Agent heartbeat, service status, `Get-PMPServerHealth`-style scripted input
- **SPL:**
```spl
index=pam sourcetype="cyberark:agent_heartbeat"
| stats latest(_time) as last_hb by agent_type, hostname
| eval secs_since=now()-last_hb
| where secs_since > 300
| table agent_type, hostname, secs_since
```
- **Implementation:** Agents send heartbeat every 60s. Alert if no heartbeat >5 minutes. Auto-ticket remediation for PSM in production zones.
- **Visualization:** Status grid (agent × host), Single value (unhealthy agents), Line chart (heartbeat age).
- **CIM Models:** N/A

---

### 9.5 Cloud Identity Providers — Okta & Duo

**Primary App/TA:** Splunk Add-on for Okta (`Splunk_TA_okta`), Cisco Duo TA (Splunk Add-on for Cisco Duo / Duo Authentication Proxy logs), optional Splunk Connect for Cisco Security Cloud for unified Duo telemetry.

---

### UC-9.5.1 · Okta Authentication Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Spikes in failed logins reveal credential attacks, misconfigured apps, or lockout conditions before accounts are fully compromised.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`user.authentication.sso`, `user.authentication.auth_via_*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" outcome.result="FAILURE"
| bin _time span=15m
| stats count by actor.alternateId, client.ipAddress, _time
| where count > 5
| sort -count
```
- **Implementation:** Ingest Okta System Log via the TA. Normalize `outcome.result` and actor fields. Baseline failures per user and IP; alert on threshold breaches and on impossible concurrent sources. Correlate with Duo denials if both are present.
- **Visualization:** Table (user, IP, failure count), Line chart (failures over time), Bar chart (top source IPs).
- **CIM Models:** Authentication

---

### UC-9.5.2 · Okta MFA Bypass Attempts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Attempts to skip or weaken MFA (policy gaps, risky grant flows) are a direct path to account takeover; monitoring policy evaluation outcomes closes that gap.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`policy.evaluate_sign_on`, `user.authentication`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="policy.evaluate_sign_on"
| where outcome.reason IN ("MFA_NOT_ENROLLED","FACTOR_NOT_USED","NONE")
| stats count by actor.alternateId, client.ipAddress, outcome.reason
| where count > 0
```
- **Implementation:** Track sign-on policy evaluations where MFA was not satisfied or only password was used. Tune to your org’s allowed “password-only” apps and break-glass accounts. Alert on unexpected ALLOW without MFA for protected apps. Review `policy.evaluate_sign_on` with `outcome.result` and debug fields.
- **Visualization:** Table (user, IP, reason), Timeline of policy events, Single value (bypass events per hour).
- **CIM Models:** Authentication

---

### UC-9.5.3 · Okta Suspicious Sign-In Activity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Okta threat signals and anomalous sessions (new device, new country, Tor) surface account takeovers before lateral movement.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`security.threat.detected`, `user.session.start`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" (eventType="security.threat.detected" OR severity="WARN")
| stats count by actor.alternateId, client.ipAddress, outcome.result, displayMessage
| where count > 0
| sort -count
```
- **Implementation:** Forward full threat and session events. Map `severity`, `outcome`, and Okta risk context. Create alerts for `security.threat.detected` and for sessions with risk scores above your baseline. Integrate with SOAR for step-up auth.
- **Visualization:** Table (user, IP, message), Map (sign-in geo), Line chart (threat events per day).
- **CIM Models:** Authentication

---

### UC-9.5.4 · Okta Admin Console Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Changes in the admin console affect global security posture; auditing who changed what supports SOC2/ISO investigations and insider-threat programs.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`system.*`, `user.session.access_admin_app`, `resource.*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" (eventType="user.session.access_admin_app" OR like(eventType,"system.org%"))
| stats count by actor.alternateId, eventType, client.ipAddress, displayMessage
| sort -count
```
- **Implementation:** Capture all admin app sessions and high-privilege system events. Restrict alerts to production Okta orgs; exclude known automation actors. Store lookups for approved admins and compare. Alert on first-time admin access from new ASN or country.
- **Visualization:** Timeline (admin actions), Table (actor, event, IP), Bar chart (events by admin user).
- **CIM Models:** Change

---

### UC-9.5.5 · Okta Policy Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Sign-on, MFA, and password policy edits can weaken security org-wide; detecting unauthorized or out-of-window changes is essential for governance.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`policy.*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"policy.lifecycle%") OR like(eventType,"policy.rule%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -count
```
- **Implementation:** Ingest policy lifecycle and rule events. Correlate with change tickets. Alert on any policy change outside maintenance windows or from non-admin service accounts. Snapshot policy names in a lookup for critical resources.
- **Visualization:** Table (policy, actor, target), Timeline (policy changes), Single value (changes in last 24h).
- **CIM Models:** Change

---

### UC-9.5.6 · Okta New Admin Creation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** New super-admin or role assignments are high-value targets for attackers; immediate notification enables rapid validation.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`user.privilege.grant`, `group.privilege*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log"
| where eventType="user.privilege.grant" OR like(eventType,"group.privilege%")
| eval tgt=lower(mvjoin('target{}.displayName'," "))
| where like(tgt,"%admin%") OR like(tgt,"%super%")
| table _time, actor.alternateId, target{}.displayName, target{}.type
```
- **Implementation:** Parse `target` for admin roles and groups. Use lookups for approved role-assignment paths. Alert on any new admin grant or role elevation. Include `actor` and `client.ipAddress` for triage.
- **Visualization:** Table (who, what role, when), Timeline, Single value (admin grants today).
- **CIM Models:** Change

---

### UC-9.5.7 · Duo Authentication Denials
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Denied logins (fraud, policy, or lockout) indicate attacks or misconfigurations; volume and user patterns guide response.
- **App/TA:** Cisco Duo TA
- **Data Sources:** `sourcetype=duo:authentication`
- **SPL:**
```spl
index=duo sourcetype="duo:authentication" result="deny"
| bin _time span=1h
| stats count by user, ip, application
| where count > 10
| sort -count
```
- **Implementation:** Ingest Duo Authentication API or proxy logs with the TA. Map `result`, `reason`, `factor`, and `application`. Baseline per-user and global deny rates. Alert on spikes and on denies from many IPs for one user.
- **Visualization:** Table (user, IP, count), Line chart (denials over time), Bar chart (denials by application).
- **CIM Models:** Authentication

---

### UC-9.5.8 · Duo Device Trust Posture
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Non-compliant or out-of-date devices that still attempt access signal policy gaps and endpoint risk exposure.
- **App/TA:** Cisco Duo TA
- **Data Sources:** `sourcetype=duo:authentication`, `sourcetype=duo:telephony` (device trust), Duo admin logs
- **SPL:**
```spl
index=duo sourcetype="duo:authentication"
| where device_trust_level!="trusted" OR like(lower(_raw),"%unmanaged%")
| stats count by user, device, device_trust_level, application
| where count > 0
| sort -count
```
- **Implementation:** Ensure device fields (OS, encryption, posture) are extracted from Duo or endpoint telemetry. Alert on repeated access from untrusted posture or when trust level changes. Pair with Duo Device Trust policies.
- **Visualization:** Table (user, device, trust level), Pie chart (trusted vs untrusted attempts), Line chart (untrusted attempts over time).
- **CIM Models:** Endpoint

---

### UC-9.5.9 · Duo Enrollment Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Sudden bulk enrollments or enrollments from unusual locations can indicate attacker-driven device registration or help-desk abuse.
- **App/TA:** Cisco Duo TA
- **Data Sources:** `sourcetype=duo:admin`, `sourcetype=duo:authentication` (enrollment events)
- **SPL:**
```spl
index=duo sourcetype="duo:admin" event_type="enrollment"
| bin _time span=15m
| stats dc(user) as new_users by _time
| where new_users > 20
```
- **Implementation:** Ingest Duo admin enrollment events. Baseline enrollment rate per hour per location. Alert on spikes and on enrollments outside business hours. Correlate with HR onboarding feeds when available.
- **Visualization:** Line chart (enrollments per hour), Table (spike windows), Bar chart (enrollments by integration).
- **CIM Models:** N/A

---

### UC-9.5.10 · Federated SSO Token Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Excessive OAuth/OIDC grants, refresh-token reuse, or token minting from new clients can indicate session theft or malicious automation.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`app.oauth2.*`, `app.oauth2.token.*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count by actor.alternateId, client.ipAddress
| where count > 100
| sort -count
```
- **Implementation:** Track token grants per user per IP and client. Use `transaction` or `streamstats` to detect rapid grants. Alert on unusual client IDs or scopes. Correlate with OAuth abuse detections from IdP.
- **Visualization:** Table (user, IP, grant count), Line chart (grants per minute), Bar chart (token grants by client).
- **CIM Models:** Authentication

---

### UC-9.5.11 · Impossible Travel Detection (Okta)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Two successful sessions from geolocations that cannot be reached in the elapsed time indicate credential theft or shared accounts.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`user.session.start`, `user.authentication.sso`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" outcome.result="SUCCESS" eventType="user.authentication.sso"
| sort 0 actor.alternateId _time
| streamstats window=1 last(client.geographicalContext.country) as prev_country last(_time) as prev_time last(client.ipAddress) as prev_ip current(client.geographicalContext.country) as country by actor.alternateId
| eval delta_sec=_time-prev_time
| where delta_sec > 0 AND delta_sec < 3600 AND country!=prev_country AND isnotnull(prev_country)
| table _time, actor.alternateId, prev_country, country, delta_sec, prev_ip, client.ipAddress
```
- **Implementation:** Use Okta geo fields (or enrich IP with `iplocation`). Tune minimum distance and maximum time windows. Exclude VPN and satellite egress via ASN lookups. Combine with Okta’s built-in impossible travel if licensed.
- **Visualization:** Table (user, country A → B, delta), Map (sequential points), Single value (impossible travel count per day).
- **CIM Models:** Authentication

---

### UC-9.5.12 · Okta API Rate Limit Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Availability
- **Value:** Hitting rate limits breaks automation, integrations, and provisioning; trending usage prevents surprise throttling during peak loads.
- **App/TA:** `Splunk_TA_okta`, custom HEC ingestion of API responses
- **Data Sources:** `sourcetype=OktaIM2:log` (`system.*rate*`), API response headers ingested via scripted input
- **SPL:**
```spl
index=okta (sourcetype="okta:api" OR sourcetype="OktaIM2:log")
| search http_status=429 OR like(lower(_raw),"%rate limit%")
| stats count by client_id, endpoint, http_status
| where count > 0
| sort -count
```
- **Implementation:** Log API calls from integrations with `X-Rate-Limit-*` headers or ingest Okta rate-limit system events. Alert on HTTP 429 or sustained high utilization. Work with app owners to add backoff and caching.
- **Visualization:** Line chart (429s over time), Table (client, endpoint), Gauge (rate limit remaining %).
- **CIM Models:** N/A

---

### UC-9.5.13 · Okta App Assignment Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** New access to sensitive SaaS apps is a common attack path; monitoring assignments supports least-privilege and access reviews.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`application.user_membership.*`, `group.user_membership.*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" (eventType="application.user_membership.add" OR eventType="group.user_membership.add")
| stats count by actor.alternateId, target{}.displayName, target{}.type
| sort -_time
```
- **Implementation:** Capture adds/removes for apps and groups tied to apps. Use lookups for crown-jewel applications. Alert on assignment to privileged groups. Include `actor` for service-account vs human.
- **Visualization:** Table (app, user, actor), Timeline (assignments), Bar chart (assignments by app).
- **CIM Models:** Change

---

### UC-9.5.14 · Duo Push Fraud Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Push bombing and fraudulent approve taps are common MFA bypass techniques; correlating push volume and user behavior stops approval fatigue attacks.
- **App/TA:** Cisco Duo TA
- **Data Sources:** `sourcetype=duo:authentication`
- **SPL:**
```spl
index=duo sourcetype="duo:authentication" factor="push"
| bin _time span=5m
| stats count by user, _time
| where count > 5
| sort -count
```
- **Implementation:** Track push attempts per user per short window. Alert on high-frequency pushes (fatigue) or pushes with `result="fraud"` or Duo fraud reasons. Integrate with Duo Risk-Based Authentication. Pair with Okta MFA events for dual IdP visibility.
- **Visualization:** Table (user, push count in window), Line chart (pushes per user), Timeline (fraud-marked events).
- **CIM Models:** Authentication

---

### UC-9.5.15 · Okta User Lifecycle Events (Provisioning / Deprovisioning)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Orphaned accounts, failed deprovisions, and unexpected creates drive audit findings and residual access after employee exit.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** `sourcetype=OktaIM2:log` (`user.lifecycle.*`, `user.account.*`)
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"user.lifecycle%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -_time
```
- **Implementation:** Align event types with HRIS-driven lifecycle (create, activate, deactivate). Alert on deactivations that fail or retry, and on manual creates outside HR correlation. Feed summaries to access reviews.
- **Visualization:** Table (event, target user, actor), Line chart (lifecycle events per day), Bar chart (events by type).
- **CIM Models:** Change


### 9.6 Endpoint & Mobile Device Management

**Primary App/TA:** Cisco Meraki Systems Manager, MDM API integrations

---

### UC-9.6.1 · Device Compliance Status and Policy Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all managed devices comply with security policies and configuration standards.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api compliance_status=*`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" (compliance_status="noncompliant" OR compliance_status="unknown")
| stats count as noncompliant_count by os_type, compliance_reason
| eval compliance_pct=round(noncompliant_count*100/total_devices, 2)
```
- **Implementation:** Query device compliance status from SM API. Alert on noncompliance.
- **Visualization:** Compliance status table; compliance percentage gauge; noncompliant device list.
- **CIM Models:** N/A

---

### UC-9.6.2 · Mobile Device Enrollment and MDM Status Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks device enrollment status to ensure mobile device management coverage.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api enrollment_status=*`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" enrollment_status IN ("enrolled", "pending", "failed")
| stats count as device_count by enrollment_status, os_type
| eval enrollment_pct=round(count*100/sum(count), 2)
```
- **Implementation:** Query device enrollment status. Track pending and failed enrollments.
- **Visualization:** Enrollment status pie chart; pending enrollment timeline; device count by OS.
- **CIM Models:** N/A

---

### UC-9.6.3 · Geofencing Alerts and Location-Based Policy Triggers
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses geofencing to detect when devices leave secure zones and trigger location-based policies.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*geofence*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*geofence*"
| stats count as geofence_event_count by device_id, zone_name, event_type
| where event_type="left_zone"
```
- **Implementation:** Monitor geofence event triggers. Track zone entry/exit by device.
- **Visualization:** Geofence event timeline; zone heat map; affected device list.
- **CIM Models:** N/A

---

### UC-9.6.4 · Mobile Security Policy Violations and App Restrictions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects policy violations and restricted app usage attempts.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*policy*" OR signature="*app*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*policy*" OR signature="*app*") violation="true"
| stats count as violation_count by device_id, policy_name, violation_type
| where violation_count > 5
```
- **Implementation:** Monitor security policy violation events. Alert on repeated violations.
- **Visualization:** Policy violation timeline; violation type breakdown; affected device list.
- **CIM Models:** N/A

---

### UC-9.6.5 · Lost Mode Device Activation and Recovery Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks activation of lost mode on devices to ensure recovery protocols are working.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*lost mode*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*lost mode*"
| stats count as lost_mode_count, latest(timestamp) as last_activation by device_id, activation_reason
```
- **Implementation:** Monitor lost mode activation events. Track recovery time.
- **Visualization:** Lost mode event timeline; affected device table; recovery status dashboard.
- **CIM Models:** N/A

---

### UC-9.6.6 · Mobile App Deployment Success Rate and Distribution Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks app deployment success and identifies devices with failed or incomplete deployments.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*app*deployment*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*app*deployment*"
| stats count as deployment_count, count(eval(status="success")) as success_count, count(eval(status="failed")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployment_count, 2)
| where success_rate < 95
```
- **Implementation:** Monitor app deployment status events. Alert on low success rates.
- **Visualization:** Deployment success rate gauge; app deployment timeline; failure detail table.
- **CIM Models:** N/A

---

