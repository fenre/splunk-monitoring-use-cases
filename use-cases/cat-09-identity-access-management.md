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
- **Implementation:** Forward Security logs from DCs via UF. Enable "Audit Logon Events" via GPO. Alert on >10 failures per account per 15 minutes. Correlate with lockout events (4740). Whitelist known service accounts with expected failures.
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
- **Value:** Unauthorized privilege escalation is a primary attack technique. Immediate detection is essential for security.
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
| stats count by src_ip, bind_dn
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
| mvexpand conditionalAccessPolicies{}
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

