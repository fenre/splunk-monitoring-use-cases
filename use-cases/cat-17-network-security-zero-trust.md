## 17. Network Security & Zero Trust

### 17.1 Network Access Control (NAC)

**Primary App/TA:** Cisco ISE TA (`Splunk_TA_cisco-ise`), Aruba ClearPass TA, Forescout TA.

---

### UC-17.1.1 · NAC Authentication Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Authentication success/failure trends reveal infrastructure issues (certificate problems, RADIUS outages) and security events.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** RADIUS/ISE authentication logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth"
| eval status=if(match(message,"PASS"),"success","failure")
| timechart span=1h count by status
```
- **Implementation:** Forward ISE syslog to Splunk. Parse authentication results, methods, and endpoints. Track success/failure rates per location and SSID. Alert on spike in failures (>10% rate). Report on authentication method adoption.
- **Visualization:** Line chart (auth success/failure rates), Bar chart (failures by location), Pie chart (auth method distribution).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.2 · Endpoint Posture Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Non-compliant endpoints accessing the network pose security risks. Posture tracking ensures endpoint hygiene enforcement.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE posture assessment logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:posture"
| where posture_status="NonCompliant"
| stats count by endpoint_mac, posture_policy, failure_reason
| sort -count
```
- **Implementation:** Ingest ISE posture assessment results. Track compliance rates per policy (AV status, patch level, disk encryption). Alert on critical endpoints failing posture (exec laptops, admin workstations). Report on remediation effectiveness.
- **Visualization:** Pie chart (compliant vs non-compliant), Bar chart (failure reasons), Table (non-compliant endpoints), Line chart (compliance trend).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-17.1.3 · VLAN Assignment Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Dynamic VLAN assignments reflect authorization decisions. Anomalous placements may indicate policy misconfiguration or attacks.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE authorization logs (VLAN assignment)
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth"
| where assigned_vlan!=expected_vlan
| table _time, endpoint_mac, username, assigned_vlan, expected_vlan, authorization_policy
```
- **Implementation:** Track VLAN assignments per endpoint. Maintain expected VLAN lookup by user role/device type. Alert on unexpected VLAN placements. Audit authorization policy effectiveness.
- **Visualization:** Table (VLAN assignments), Pie chart (assignments by VLAN), Bar chart (unexpected placements).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.4 · Guest Network Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Guest network monitoring ensures acceptable use and identifies capacity needs. Unusual patterns may indicate abuse.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE guest portal logs, RADIUS accounting
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:guest"
| stats count, sum(session_duration_min) as total_min by sponsor, guest_type
| sort -count
```
- **Implementation:** Track guest portal registrations, sponsor activity, and session durations. Alert on excessive guest registrations from single sponsors. Monitor guest bandwidth usage. Report on guest network utilization.
- **Visualization:** Bar chart (guest registrations by sponsor), Line chart (guest sessions trend), Table (active guests).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.5 · BYOD Onboarding Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** BYOD onboarding metrics inform mobile device management strategy and user experience optimization.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE BYOD portal logs, certificate provisioning
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:byod"
| stats count by device_type, os_type, onboarding_status
| sort -count
```
- **Implementation:** Track BYOD registrations, device types, and onboarding success/failure rates. Alert on onboarding failures. Report on device type distribution for MDM policy planning.
- **Visualization:** Pie chart (device types), Bar chart (onboarding status), Line chart (BYOD enrollment trend).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.6 · MAC Authentication Bypass (MAB)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** MAB devices bypass 802.1X and rely on MAC address only. Monitoring for unauthorized MACs prevents rogue device access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE MAB authentication logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth" auth_method="MAB"
| lookup approved_mab_devices.csv mac_address OUTPUT device_description, approved
| where isnull(approved) OR approved!="Yes"
| table _time, endpoint_mac, switch, port, location
```
- **Implementation:** Maintain whitelist of approved MAB devices (printers, IP phones, IoT). Alert on unknown MAC addresses authenticating via MAB. Track MAB device population. Report on MAB vs 802.1X ratio for security posture.
- **Visualization:** Table (unapproved MAB devices), Pie chart (MAB vs 802.1X), Bar chart (MAB by device type).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.7 · Profiling Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Accurate device profiling enables correct authorization policies. Misprofiled devices may get inappropriate access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE profiler logs, re-profiling events
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:profiler"
| search "re-profiled" OR "profile changed"
| stats count by endpoint_mac, old_profile, new_profile
| sort -count
```
- **Implementation:** Monitor profiling events and profile changes. Track devices that are frequently re-profiled (indicates ambiguous profiling rules). Validate profiling accuracy against known device inventory. Tune profiling policies.
- **Visualization:** Table (profiling changes), Sankey diagram (old→new profiles), Bar chart (re-profiling frequency).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.8 · NAC Policy Change Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** NAC policy changes affect network access for all devices. Unauthorized changes can create security gaps or disrupt access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE admin audit logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:admin"
| search "PolicySet" OR "AuthorizationRule" OR "AuthenticationRule"
| table _time, admin_user, action, object_name, details
```
- **Implementation:** Forward ISE admin audit logs. Alert on any policy change. Track changes by administrator. Correlate with change management tickets. Report on policy change frequency.
- **Visualization:** Table (policy changes), Timeline (change events), Bar chart (changes by admin).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### 17.2 VPN & Remote Access

**Primary App/TA:** Cisco ASA/AnyConnect TA, Palo Alto GlobalProtect TA, vendor syslog.

---

### UC-17.2.1 · VPN Concurrent Sessions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** VPN capacity planning prevents remote workers from being locked out. Trending identifies peak usage and growth patterns.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto (GlobalProtect)
- **Data Sources:** VPN concentrator session logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| where action="session_connect" OR action="session_disconnect"
| timechart span=15m dc(user) as concurrent_users
```
- **Implementation:** Track VPN session connects/disconnects. Calculate concurrent users over time. Alert when approaching license or capacity limits. Report on peak usage patterns for capacity planning. Track growth trends.
- **Visualization:** Line chart (concurrent sessions), Gauge (% of capacity), Single value (current active sessions), Area chart (sessions over time).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.2 · VPN Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Repeated VPN auth failures indicate credential attacks against the remote access perimeter, a primary attack vector.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto (GlobalProtect)
- **Data Sources:** VPN authentication logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="authentication_failed"
| stats count by user, src_ip
| where count > 5
| sort -count
```
- **Implementation:** Track VPN authentication failures by user and source IP. Alert on >5 failures per user per 15 minutes. Correlate with AD lockout events. Block source IPs with excessive failures. Report on attack patterns.
- **Visualization:** Table (failed auth events), Bar chart (failures by user), Geo map (source IPs), Line chart (failure rate trend).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.3 · Geo-Location Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** VPN connections from unexpected countries may indicate compromised credentials being used from attacker infrastructure.
- **App/TA:** VPN TA + GeoIP lookup
- **Data Sources:** VPN session logs with source IP
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| iplocation src_ip
| search NOT Country IN ("United States","Canada","United Kingdom")
| table _time, user, src_ip, Country, City
```
- **Implementation:** Enrich VPN connections with GeoIP data. Maintain whitelist of expected countries. Alert on connections from unexpected locations. Correlate with user travel records if available. Block sanctioned countries.
- **Visualization:** Geo map (VPN connections), Table (anomalous locations), Bar chart (connections by country).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.4 · Split-Tunnel Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Split-tunnel configurations affect security visibility. Ensuring compliance with tunnel policy maintains security posture.
- **App/TA:** VPN TA
- **Data Sources:** VPN session attributes (tunnel type, group policy)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| stats count by user, tunnel_type, group_policy
| where tunnel_type="split"
| table user, tunnel_type, group_policy, count
```
- **Implementation:** Track VPN tunnel configuration per session. Verify users are connecting with the correct group policy (full-tunnel for high-risk, split-tunnel for standard). Alert on policy violations. Report on tunnel type distribution.
- **Visualization:** Pie chart (full vs split tunnel), Table (sessions by policy), Bar chart (tunnel type by department).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.5 · VPN Tunnel Stability
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Frequent disconnects indicate network issues, client problems, or infrastructure instability affecting user productivity.
- **App/TA:** VPN TA
- **Data Sources:** VPN session logs (connect/disconnect events)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| where action IN ("session_connect","session_disconnect")
| transaction user maxspan=1h
| where eventcount > 4
| table user, eventcount, duration
| sort -eventcount
```
- **Implementation:** Track connect/disconnect patterns per user. Identify users with >4 reconnections per hour. Correlate with network quality metrics. Alert on widespread instability (multiple users affected simultaneously). Report for helpdesk.
- **Visualization:** Table (unstable connections), Bar chart (reconnects by user), Line chart (reconnection rate trend).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.6 · Off-Hours VPN Access
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** VPN access at unusual hours may indicate compromised credentials or unauthorized activity. Alerting supports investigation.
- **App/TA:** VPN TA + user context
- **Data Sources:** VPN session logs, HR data (department, role)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| eval hour=strftime(_time,"%H")
| where (hour < 5 OR hour > 23)
| lookup user_roles.csv user OUTPUT department, role
| where role!="on_call" AND role!="sysadmin"
| table _time, user, department, src_ip, hour
```
- **Implementation:** Define normal hours per user role/department. Alert on VPN connections outside hours for roles that don't require it. Whitelist on-call and sysadmin roles. Review weekly for patterns.
- **Visualization:** Heatmap (user × hour of day), Table (off-hours access), Bar chart (off-hours by department).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.7 · VPN Bandwidth Consumption
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Per-user bandwidth tracking identifies heavy users, guides capacity planning, and detects potential data exfiltration.
- **App/TA:** VPN TA, RADIUS accounting
- **Data Sources:** VPN session accounting (bytes in/out)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| stats sum(bytes_in) as bytes_in, sum(bytes_out) as bytes_out by user
| eval total_gb=round((bytes_in+bytes_out)/1073741824,2)
| sort -total_gb
| head 20
```
- **Implementation:** Track VPN session byte counters per user. Alert on users with excessive upload (potential data exfiltration). Report on bandwidth distribution for capacity planning. Identify optimization opportunities (video offload, split-tunnel).
- **Visualization:** Bar chart (bandwidth by user), Pie chart (upload vs download), Line chart (total bandwidth trend), Table (top bandwidth consumers).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### UC-17.2.8 · Simultaneous Session Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** A single user with simultaneous VPN sessions from different locations strongly indicates credential compromise.
- **App/TA:** VPN TA
- **Data Sources:** VPN session logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| stats dc(src_ip) as unique_ips, values(src_ip) as ips by user
| where unique_ips > 1
```
- **Implementation:** Track active VPN sessions per user. Alert when a user has concurrent sessions from different IPs. Whitelist known scenarios (multiple devices). Trigger automated investigation including password reset.
- **Visualization:** Table (users with multiple sessions), Single value (simultaneous sessions detected), Timeline (detection events).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
         sum(Network_Sessions.bytes_in) as bytes_in
         sum(Network_Sessions.bytes_out) as bytes_out
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h
| sort -count
```

---

### 17.3 Zero Trust / SASE

**Primary App/TA:** Zscaler TA, Netskope TA, Palo Alto Prisma Access TA.

---

### UC-17.3.1 · Conditional Access Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks zero-trust policy enforcement decisions, ensuring consistent security without creating user friction.
- **App/TA:** SASE TA, Entra ID
- **Data Sources:** SASE/ZT policy decision logs
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa"
| stats count by policy_action, application, user
| eval pct=round(count/sum(count)*100,1)
```
- **Implementation:** Ingest SASE/ZTNA policy decision logs. Track allow/block/step-up-auth decisions per application and user. Alert on policy blocks for critical applications. Report on policy effectiveness and user experience impact.
- **Visualization:** Pie chart (policy decisions), Bar chart (blocks by application), Line chart (enforcement trend), Table (blocked users).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.3.2 · Device Trust Scoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Device trust scores drive access decisions in zero-trust architecture. Monitoring ensures devices maintain compliance.
- **App/TA:** ZT platform TA
- **Data Sources:** ZT device compliance/trust data
- **SPL:**
```spl
index=zt sourcetype="zscaler:device_posture"
| where trust_score < 50 OR compliance_status!="compliant"
| table user, device_id, os, trust_score, compliance_status, non_compliant_checks
```
- **Implementation:** Ingest device trust score data from ZT platform. Track compliance rates per OS and department. Alert when critical devices become non-compliant. Report on fleet trust posture for security leadership.
- **Visualization:** Gauge (fleet compliance %), Table (non-compliant devices), Pie chart (compliance distribution), Line chart (trust score trend).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.3.3 · Micro-Segmentation Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Micro-segmentation limits lateral movement. Audit logs validate policy enforcement and detect bypasses.
- **App/TA:** SDN/ZT policy logs
- **Data Sources:** Micro-segmentation policy logs (allow/deny events)
- **SPL:**
```spl
index=zt sourcetype="microseg:policy"
| where action="deny"
| stats count by src_workload, dest_workload, dest_port, policy_name
| sort -count
```
- **Implementation:** Ingest micro-segmentation policy enforcement logs. Track allowed and denied traffic between workloads. Alert on unexpected denials (may indicate misconfiguration) and unexpected allows (policy gaps). Report on segmentation coverage.
- **Visualization:** Heatmap (workload × workload traffic), Table (policy violations), Sankey diagram (traffic flows).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.3.4 · ZTNA Application Access
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Per-application access patterns in ZTNA reveal usage trends, security risks, and application performance issues.
- **App/TA:** SASE TA
- **Data Sources:** ZTNA access logs (application, user, device, action)
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa"
| stats dc(user) as unique_users, count as total_access by application
| sort -unique_users
```
- **Implementation:** Track application access through ZTNA per user and device. Identify unused applications for decommissioning. Monitor access patterns for anomalies. Report on application adoption and usage.
- **Visualization:** Bar chart (top applications by users), Table (application access summary), Line chart (access trends per app).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.3.5 · Posture Assessment Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Endpoint posture compliance rates over time measure security improvement and identify persistent non-compliance areas.
- **App/TA:** ZT platform TA
- **Data Sources:** ZT posture assessment data
- **SPL:**
```spl
index=zt sourcetype="zt:posture"
| timechart span=1d avg(compliance_pct) as compliance by check_type
```
- **Implementation:** Track posture assessment results over time by check type (AV, encryption, OS patch, firewall). Report on compliance improvement trends. Alert when compliance drops below target. Identify persistent non-compliance patterns.
- **Visualization:** Line chart (compliance trend by check), Bar chart (compliance by OS), Single value (overall compliance %), Table (non-compliant checks).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.3.6 · Policy Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Zero-trust policies require continuous validation. Drift from baseline configuration introduces security gaps.
- **App/TA:** ZT platform audit logs
- **Data Sources:** ZT policy audit logs, configuration snapshots
- **SPL:**
```spl
index=zt sourcetype="zt:admin_audit"
| search action IN ("policy_modified","rule_added","rule_deleted","rule_disabled")
| table _time, admin, action, policy_name, details
| sort -_time
```
- **Implementation:** Track all ZT policy changes via audit logs. Compare current configuration against approved baseline. Alert on unauthorized modifications. Require change management approval for policy changes. Report on policy change frequency.
- **Visualization:** Table (policy changes), Timeline (modification events), Bar chart (changes by admin), Single value (changes this week).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

