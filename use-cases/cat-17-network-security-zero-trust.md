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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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

### UC-17.1.9 · 802.1X Supplicant Timeout Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Clients timing out during RADIUS authentication (common issue with Wi-Fi and wired NAC). Tracking timeouts helps identify supplicant misconfiguration, certificate issues, or network latency affecting authentication.
- **App/TA:** Splunk_TA_cisco-ise, RADIUS TA, NAS syslog
- **Equipment Models:** Cisco ISE, Windows NPS, FreeRADIUS, Cisco/Aruba switches and WLCs
- **Data Sources:** RADIUS server logs (FreeRADIUS, NPS, ISE), switch/WLC syslog (dot1x events)
- **SPL:**
```spl
index=nac (sourcetype="cisco:ise:auth" OR sourcetype="radius:auth" OR sourcetype="freeradius")
| search "timeout" OR "timed out" OR "EAP timeout" OR "supplicant" OR "no response"
| rex field=_raw "Calling-Station-Id=(?<mac>[^\s]+)"
| rex field=_raw "NAS-Identifier=(?<nas>[^\s,]+)"
| bin _time span=1h
| stats count by mac, nas, _time
| where count > 3
| sort -count
```
- **Implementation:** Forward RADIUS authentication logs and NAS (switch/WLC) syslog to Splunk. Configure sourcetypes for FreeRADIUS, NPS, or ISE. Extract Calling-Station-Id (MAC), NAS-Identifier, and timeout-related messages. Alert when timeout count exceeds 5 per NAS per hour. Correlate with switch port and SSID to identify problematic segments. Report on timeout trends by location and time of day.
- **Visualization:** Line chart (timeout rate over time), Bar chart (timeouts by NAS/switch), Table (affected MACs and NAS), Heatmap (NAS × hour of day).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-17.1.10 · RADIUS Accounting Discrepancies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Value:** Start/stop mismatches indicating dropped sessions or potential abuse. Accounting discrepancies can hide unauthorized access, session hijacking, or billing/audit gaps.
- **App/TA:** RADIUS server logs, RADIUS accounting TA
- **Equipment Models:** Cisco ISE, Windows NPS, FreeRADIUS
- **Data Sources:** RADIUS accounting records (Acct-Status-Type Start/Stop/Interim-Update)
- **SPL:**
```spl
index=nac sourcetype="radius:accounting"
| eval acct_status=case(
  match(_raw,"Acct-Status-Type.*Start"), "Start",
  match(_raw,"Acct-Status-Type.*Stop"), "Stop",
  match(_raw,"Acct-Status-Type.*Interim"), "Interim",
  1=1, "Unknown")
| rex field=_raw "Acct-Session-Id=(?<session_id>[^\s]+)"
| rex field=_raw "User-Name=(?<user>[^\s]+)"
| rex field=_raw "NAS-IP-Address=(?<nas>[^\s]+)"
| where acct_status!="Unknown" AND acct_status!="Interim"
| stats count(eval(acct_status="Start")) as starts, count(eval(acct_status="Stop")) as stops by session_id, user, nas
| eval discrepancy=abs(starts - stops)
| where discrepancy > 0
| sort -discrepancy
```
- **Implementation:** Ingest RADIUS accounting logs with Acct-Session-Id, Acct-Status-Type, User-Name, NAS-IP-Address. Build session state table: each Start should have exactly one Stop. Alert on sessions with Start but no Stop (orphaned sessions) or Stop without Start (potential replay). Report on discrepancy rate and top NAS/users. Use Interim-Update to validate long-running sessions.
- **Visualization:** Table (sessions with discrepancies), Bar chart (discrepancy count by NAS), Single value (orphaned sessions), Line chart (discrepancy trend).
- **CIM Models:** Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.src All_Sessions.user All_Sessions.dest span=1h
| where count > 10
```

---

### UC-17.1.11 · Posture Assessment Failure Trends
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Time-series view of posture failures by policy and reason — distinguishes one-off issues from worsening fleet hygiene or a bad policy rollout.
- **App/TA:** Splunk_TA_cisco-ise
- **Equipment Models:** Cisco ISE 3515–3695, ISE Virtual Appliance
- **Data Sources:** ISE posture assessment logs (`cisco:ise:posture`)
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:posture" earliest=-30d
| where posture_status="NonCompliant"
| timechart span=1d count by failure_reason
```
- **Implementation:** Normalize `failure_reason` from ISE. Alert when daily failures exceed 7-day baseline by >50%. Segment by AD group or location if extracted.
- **Visualization:** Line chart (failures over time by reason), Stacked area (failures by policy), Single value (failures vs prior week).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.src span=1d
```

---

### UC-17.1.12 · Rogue Device Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies MACs or devices that authenticate or probe but are not in the corporate device inventory — common NAC use case for unauthorized hardware.
- **App/TA:** Splunk_TA_cisco-ise
- **Equipment Models:** Cisco ISE, switch/WLC syslog
- **Data Sources:** ISE authentication logs, profiling
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth" earliest=-24h
| eval mac=upper(replace(endpoint_mac,":","-"))
| lookup corp_device_inventory.csv mac OUTPUT asset_tag
| where isnull(asset_tag) AND match(auth_status,"(?i)success|pass")
| stats count by mac, switch, location
| where count>=3
| sort -count
```
- **Implementation:** Maintain `corp_device_inventory.csv` from MDM/CMDB (MAC, owner). Tune minimum event count to reduce noise. Correlate with port-security and DHCP snooping if available.
- **Visualization:** Table (unknown MACs), Bar chart (rogue events by site), Timeline (first seen).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.src span=1h
| where count > 20
```

---

### UC-17.1.13 · 802.1X Authentication Failure Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Security
- **Value:** Breaks down 802.1X/EAP failures by method, failure reason, and NAS to pinpoint certificate rollout issues vs brute-force vs misconfigured supplicants.
- **App/TA:** Splunk_TA_cisco-ise, RADIUS TA
- **Equipment Models:** Cisco ISE, switches, WLCs
- **Data Sources:** `cisco:ise:auth`, `radius:auth`
- **SPL:**
```spl
index=nac (sourcetype="cisco:ise:auth" OR sourcetype="radius:auth") earliest=-7d
| search "802.1X" OR auth_method="EAP*" OR eap_method=*
| where match(lower(message),"(?i)fail|reject|denied")
| stats count by eap_method, failure_reason, nas_ip
| sort -count
| head 30
```
- **Implementation:** Extract `eap_method`, `failure_reason`, and `nas_ip` per your TA. Alert on spikes in a single failure bucket (e.g., TLS cert errors). Compare before/after cert updates.
- **Visualization:** Bar chart (failures by EAP method), Table (top NAS + reason), Line chart (daily failure rate).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.dest Authentication.src span=1h
| where count > 10
```

---

### UC-17.1.14 · Guest Network Abuse Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Flags excessive concurrent guest sessions, high bandwidth, or repeated sponsor abuse — beyond simple guest usage volume (UC-17.1.4).
- **App/TA:** Splunk_TA_cisco-ise, firewall logs
- **Equipment Models:** Cisco ISE guest, WLC
- **Data Sources:** `cisco:ise:guest`, NetFlow optional
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:guest" earliest=-24h
| stats dc(session_id) as concurrent_sessions, sum(bytes) as total_bytes by sponsor, guest_mac
| where concurrent_sessions>5 OR total_bytes>10737418240
| eval total_gb=round(total_bytes/1073741824,2)
| table sponsor, guest_mac, concurrent_sessions, total_gb
| sort -total_gb
```
- **Implementation:** Map `bytes` from ISE or join firewall `src_ip` for guest VLAN. Thresholds per org. Alert on sponsor accounts with many parallel guests.
- **Visualization:** Table (abuse candidates), Bar chart (bytes by sponsor), Single value (guests over threshold).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user span=1h
| where count > 100
```

---

### UC-17.1.15 · RADIUS Accounting NAS vs Session-ID Reconciliation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Value:** Complements UC-17.1.10 by flagging duplicate session IDs or mismatched NAS-IP between Start/Interim/Stop for the same `Acct-Session-Id` — catching replication and proxy issues.
- **App/TA:** RADIUS accounting TA
- **Equipment Models:** Cisco ISE, NPS, FreeRADIUS
- **Data Sources:** `sourcetype=radius:accounting`
- **SPL:**
```spl
index=nac sourcetype="radius:accounting" earliest=-24h
| rex field=_raw "Acct-Session-Id=(?<session_id>[^\s]+)"
| rex field=_raw "NAS-IP-Address=(?<nas>[^\s]+)"
| stats dc(nas) as nas_dc values(nas) as nas_list by session_id
| where nas_dc>1
| table session_id, nas_list
```
- **Implementation:** A given RADIUS session should map to one NAS-IP unless mobility events are logged; multiple NAS for one session ID often indicates misconfiguration or log duplication.
- **Visualization:** Table (conflicting sessions), Single value (conflict count).
- **CIM Models:** Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.dest span=1h
| where count > 50
```

---

### UC-17.1.16 · MAC Authentication Bypass Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Complements UC-17.1.6 whitelist checks with **volume and velocity** anomalies (sudden MAB spikes per port or site) that may indicate MAC spoofing or policy gaps.
- **App/TA:** Splunk_TA_cisco-ise
- **Equipment Models:** Cisco ISE, access switches
- **Data Sources:** `cisco:ise:auth` with MAB
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth" auth_method="MAB" earliest=-7d
| bin _time span=1h
| stats count by _time, switch, port
| eventstats avg(count) as baseline by switch
| where count > baseline*3 AND count>10
| sort -count
```
- **Implementation:** Baseline MAB events per switch/port; alert on spikes. Join UC-17.1.6 for unknown MAC focus.
- **Visualization:** Line chart (MAB rate per switch), Table (spike events), Heatmap (port × hour).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.dest span=1h
| where count > 500
```

---

### UC-17.1.17 · Network Quarantine Effectiveness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures how often quarantined endpoints reach compliant state (successful remediation vs repeat quarantine) — effectiveness of NAC remediation workflows.
- **App/TA:** Splunk_TA_cisco-ise, `nac:quarantine`
- **Equipment Models:** Cisco ISE, NAC vendors
- **Data Sources:** Quarantine assign/release, posture re-check
- **SPL:**
```spl
index=nac sourcetype="nac:quarantine" earliest=-30d
| eval released=if(match(lower(status),"(?i)released|cleared"),1,0)
| stats count as events, sum(released) as releases by endpoint_mac
| eval success_ratio=round(100*releases/events,1)
| where events>3 AND success_ratio < 40
| table endpoint_mac, events, releases, success_ratio
```
- **Implementation:** Map vendor status fields. Track repeat quarantines for same MAC within 7 days as “ineffective.” Feed to desktop engineering.
- **Visualization:** Table (low effectiveness MACs), Bar chart (success ratio by violation type), Line chart (fleet success ratio).
- **CIM Models:** N/A

---

### UC-17.1.18 · NAC Policy Compliance Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Daily percentage of authentications that receive “permit” vs “deny” vs “redirect” per authorization policy — trending for policy drift and rollout validation.
- **App/TA:** Splunk_TA_cisco-ise
- **Equipment Models:** Cisco ISE
- **Data Sources:** `cisco:ise:auth`
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth" earliest=-30d
| eval outcome=case(match(lower(authorization_result),"(?i)permit|access.accept"),"permit", match(lower(authorization_result),"(?i)deny|reject"),"deny", true(),"other")
| timechart span=1d count by outcome
```
- **Implementation:** Normalize `authorization_result` from your ISE field set. Alert when `deny` share increases >2× baseline week-over-week.
- **Visualization:** Stacked area (outcomes over time), Line chart (deny rate), Single value (deny % today).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.action span=1d
```

---

### UC-17.1.19 · Endpoint Compliance Scoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Composite score per endpoint from posture checks (AV, patch, encryption) for executive dashboards and exception reporting.
- **App/TA:** Splunk_TA_cisco-ise
- **Equipment Models:** Cisco ISE
- **Data Sources:** `cisco:ise:posture`
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:posture" earliest=-4h
| eval check_pass=if(match(lower(posture_status),"(?i)compliant"),1,0)
| stats avg(check_pass) as score by endpoint_mac
| eval compliance_pct=round(score*100,1)
| where compliance_pct < 80
| sort compliance_pct
| head 100
```
- **Implementation:** For multi-check rows per MAC, use `latest` per check name then average. Weight critical checks in `eval` if needed.
- **Visualization:** Table (lowest-scoring endpoints), Histogram (score distribution), Gauge (fleet average score).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.src span=1d
```

---

### UC-17.1.20 · Quarantine Release Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Audit trail of who released endpoints from quarantine and whether release matched policy (e.g., IT-only, ticket required).
- **App/TA:** Splunk_TA_cisco-ise, `nac:quarantine`
- **Equipment Models:** Cisco ISE
- **Data Sources:** Admin audit + quarantine logs
- **SPL:**
```spl
index=nac (sourcetype="nac:quarantine" OR sourcetype="cisco:ise:admin")
| search "quarantine" AND (released OR "cleared" OR "unquarantine")
| table _time, admin_user, endpoint_mac, action, ticket_id
| sort -_time
```
- **Implementation:** Map `ticket_id` from workflow; alert when `isnull(ticket_id)` and action is manual release. Join ServiceNow for approved changes.
- **Visualization:** Table (release audit), Timeline (releases), Bar chart (releases by admin).
- **CIM Models:** N/A

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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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
- **Equipment Models:** Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv
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

### UC-17.2.9 · VPN Split-Tunnel Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Verifying split-tunnel vs. full-tunnel adherence per user/group policy. Full-tunnel ensures all traffic is inspected; split-tunnel may bypass security controls for internet-bound traffic.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto (GlobalProtect), vendor VPN TA
- **Equipment Models:** Cisco ASA/AnyConnect, Palo Alto GlobalProtect, FortiGate SSL-VPN
- **Data Sources:** VPN session logs (tunnel_type, assigned_policy, routing_mode)
- **SPL:**
```spl
index=vpn (sourcetype="cisco:asa" OR sourcetype="pan:globalprotect")
| search action="session_connect" OR "tunnel established"
| rex field=_raw "Group Policy=(?<group_policy>[^\s]+)"
| rex field=_raw "tunnel_type=(?<tunnel_type>[^\s]+)"
| rex field=_raw "routing_mode=(?<routing_mode>[^\s]+)"
| lookup vpn_policy_requirements.csv group_policy OUTPUT required_tunnel
| eval actual_tunnel=coalesce(tunnel_type, routing_mode, group_policy)
| where required_tunnel!=actual_tunnel OR isnull(required_tunnel)
| table _time, user, group_policy, actual_tunnel, required_tunnel, src_ip
```
- **Implementation:** Ingest VPN session logs with tunnel configuration. Maintain lookup table mapping group policy to required tunnel type (full/split). For Cisco ASA, use Group-Policy; for GlobalProtect, use gateway-assigned policy. Alert when users connect with split-tunnel when policy requires full-tunnel (e.g., high-risk groups). Report on policy compliance rate by department and gateway.
- **Visualization:** Pie chart (full vs split by policy), Table (policy violations), Bar chart (compliance by group policy), Single value (% compliant).
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

### UC-17.2.10 · mTLS Certificate Rotation Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Availability
- **Value:** Mutual TLS certificates approaching expiry in zero-trust architectures (service-to-service auth). Expired certs cause service outages and authentication failures.
- **App/TA:** Custom (certificate inventory, service mesh telemetry)
- **Data Sources:** Certificate inventory scan (serial, subject, expiry), Istio/Linkerd cert rotation logs
- **SPL:**
```spl
index=certs (sourcetype="cert:inventory" OR sourcetype="istio:cert" OR sourcetype="linkerd:cert")
| eval expiry_epoch=if(isnum(expiry_time), expiry_time, strptime(expiry_time, "%Y-%m-%dT%H:%M:%SZ"))
| eval days_to_expiry=floor((expiry_epoch - now())/86400)
| where days_to_expiry < 60 OR days_to_expiry < 0
| eval status=case(days_to_expiry < 0, "EXPIRED", days_to_expiry < 14, "CRITICAL", days_to_expiry < 30, "WARNING", 1=1, "OK")
| table _time, subject, serial, expiry_epoch, days_to_expiry, status, workload, namespace
| sort days_to_expiry
```
- **Implementation:** Run periodic certificate inventory scans (OpenSSL, cert-manager, HashiCorp Vault) and forward to Splunk. Ingest Istio/Linkerd cert rotation logs for service mesh. Parse subject, serial, notAfter. Alert when cert expires in <30 days; critical alert at <14 days. Track rotation success/failure from mesh logs. Report on cert distribution by workload and expiry timeline. Integrate with automation for cert renewal.
- **Visualization:** Table (certs expiring soon), Single value (expired count), Bar chart (expiry by month), Timeline (rotation events).
- **CIM Models:** N/A

---

### UC-17.2.11 · Split Tunnel Violation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Flags sessions where observed routing or client flags indicate split tunnel when group policy mandates full tunnel — complements UC-17.2.4/17.2.9 with explicit **violation** logic.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto
- **Equipment Models:** Cisco ASA/AnyConnect, GlobalProtect
- **Data Sources:** VPN connect logs with `tunnel_type`, `split_include`, `default_gateway`
- **SPL:**
```spl
index=vpn (sourcetype="cisco:asa" OR sourcetype="pan:globalprotect") action="session_connect"
| lookup vpn_policy_requirements.csv group_policy OUTPUT required_tunnel
| eval violation=if(required_tunnel="full" AND (tunnel_type="split" OR match(lower(_raw),"(?i)split.?tunnel")),1,0)
| where violation=1
| stats count by user, group_policy, src_ip
| sort -count
```
- **Implementation:** Align lookup with security architecture. Some vendors expose only group name — normalize in transforms.
- **Visualization:** Table (violations), Bar chart (violations by group policy), Single value (violation sessions / day).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user span=1h
| where count > 100
```

---

### UC-17.2.12 · VPN Concentrator Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Tracks session count and CPU/memory against platform limits to avoid remote-access brownouts during peaks.
- **App/TA:** Splunk_TA_cisco-asa, SNMP TA
- **Equipment Models:** ASA, FTD, Palo Alto GlobalProtect
- **Data Sources:** SNMP OIDs, `cisco:asa` system events, vendor metrics API
- **SPL:**
```spl
index=snmp sourcetype="snmp:cpu" host="vpn-headend-*" earliest=-24h
| timechart span=15m avg(cpu_utilization) as avg_cpu by host
```
- **Implementation:** Prefer vendor metrics (e.g., AnyConnect session count OID). Alert when CPU >80% sustained or sessions >85% of license. Simplify if only session logs: use UC-17.2.1 trend + license field.
- **Visualization:** Line chart (CPU vs sessions), Gauge (capacity %), Table (headends).
- **CIM Models:** N/A

---

### UC-17.2.13 · Concurrent VPN Session Limits
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity, Security
- **Value:** Alerts when simultaneous sessions approach licensed or configured caps — same user or aggregate.
- **App/TA:** Splunk_TA_cisco-asa
- **Equipment Models:** Cisco ASA
- **Data Sources:** `cisco:asa` session events
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" earliest=-4h
| where action="session_connect" OR action="session_disconnect"
| eval delta=if(action="session_connect",1,-1)
| sort 0 _time
| streamstats global=f sum(delta) as concurrent by host
| where concurrent > 0
| stats max(concurrent) as peak_concurrent by host
| lookup vpn_license_limits.csv host OUTPUT max_sessions
| where peak_concurrent > max_sessions*0.85
```
- **Implementation:** If connect/disconnect deltas are incomplete, use vendor “show vpn-sessiondb summary” scripted input for authoritative count. Tune `max_sessions` from license CSV.
- **Visualization:** Single value (peak vs cap %), Line chart (concurrent sessions), Table (headends near limit).
- **CIM Models:** N/A

---

### UC-17.2.14 · Geo-Impossible VPN Connections
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects logins from two distant countries faster than plausible travel — complements static geo allowlists (UC-17.2.3).
- **App/TA:** VPN TA, GeoIP
- **Equipment Models:** Cisco ASA, GlobalProtect
- **Data Sources:** VPN session connect with `src_ip`, `user`
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect" earliest=-24h
| iplocation src_ip
| eval country=Country
| sort user _time
| streamstats current=f last(_time) as prev_time last(Country) as prev_country by user
| eval gap_hrs=round((_time-prev_time)/3600,2)
| where isnotnull(prev_country) AND country!=prev_country AND gap_hrs < 6
| table _time, user, prev_country, country, gap_hrs, src_ip
```
- **Implementation:** Tune time window (e.g., 4–8h) and distance (optional `haversine` if lat/long from enriched data). Whitelist mobile users and split tunnel carrier NAT.
- **Visualization:** Table (impossible travel), Map (prev vs new), Single value (alerts / day).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.src span=1h
| where count > 5
```

---

### UC-17.2.15 · VPN Tunnel Keepalive Failure Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks DPD/keepalive failures and tunnel teardown reasons for site-to-site and remote-access — isolates path MTU, NAT, and idle timeout issues.
- **App/TA:** Splunk_TA_cisco-asa, Palo Alto
- **Equipment Models:** ASA, Palo Alto IPsec
- **Data Sources:** VPN/IKE syslog (`cisco:asa`, `pan:system`)
- **SPL:**
```spl
index=vpn (sourcetype="cisco:asa" OR sourcetype="pan:system") earliest=-24h
| search "IKE" OR "keepalive" OR "DPD" OR "dead peer"
| stats count by tunnel_id, peer_ip, message_signature
| sort -count
| head 40
```
- **Implementation:** Normalize `message_signature` with `rex` or `cluster` on raw. Correlate with UC-17.2.5 stability metrics.
- **Visualization:** Bar chart (failures by peer), Table (top messages), Line chart (failure rate).
- **CIM Models:** N/A

---

### UC-17.2.16 · Remote Desktop Gateway Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors RD Gateway (HTTP/UDP) auth success, connection failures, and capacity for hybrid workers.
- **App/TA:** Windows TA, IIS TA
- **Equipment Models:** Windows Server RD Gateway
- **Data Sources:** `sourcetype=ms:iis`, `WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational`
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational" earliest=-24h
| where EventCode IN (200,201,300,302)
| eval outcome=if(EventCode IN (200,201),"success","failure")
| timechart span=15m count by outcome
```
- **Implementation:** Map Event IDs per OS version. Alert when failure ratio >10% over 1h. Add IIS logs for HTTP 503/502.
- **Visualization:** Line chart (success vs failure), Single value (failure %), Table (recent errors).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.dest span=1h
| where count > 5
```

---

### UC-17.2.17 · VPN Client Version Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Reports AnyConnect/GlobalProtect client versions against minimum supported builds.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto
- **Equipment Models:** ASA, GP portal
- **Data Sources:** VPN session logs with `client_version`
- **SPL:**
```spl
index=vpn (sourcetype="cisco:asa" OR sourcetype="pan:globalprotect") action="session_connect" earliest=-24h
| eval major_minor=replace(client_version,"^(\d+\.\d+).*","\1")
| lookup vpn_min_client.csv platform OUTPUT min_version
| eval compliant=if(major_minor>=min_version,1,0)
| where compliant=0
| stats count by user, client_version, platform
| sort -count
```
- **Implementation:** Use `ver` normalisation or `version` field if numeric. Block or warn via posture integration.
- **Visualization:** Pie chart (compliant vs not), Table (outdated clients), Bar chart (by version).
- **CIM Models:** Authentication, Network_Sessions
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user span=1d
```

---

### UC-17.2.18 · Site-to-Site Tunnel Flapping
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Counts IKE/IPsec up/down events per peer for unstable WAN or crypto issues.
- **App/TA:** Splunk_TA_cisco-asa, Palo Alto
- **Equipment Models:** Firewalls, routers
- **Data Sources:** VPN syslog tunnel events
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" earliest=-24h
| search "Tunnel is UP" OR "Tunnel is DOWN" OR "IPSEC.*DOWN"
| eval peer=coalesce(peer_ip, tunnel_group)
| stats count by peer
| where count>10
| sort -count
```
- **Implementation:** Vendor message strings vary — maintain `rex` extractions in props. Alert when transitions >N per hour per peer.
- **Visualization:** Line chart (transitions over time), Table (worst peers), Single value (flapping peers).
- **CIM Models:** N/A

---

### UC-17.2.19 · Always-On VPN Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Identifies corporate assets connecting without Always-On (pre-login) VPN when policy requires it.
- **App/TA:** Splunk_TA_cisco-asa, endpoint inventory
- **Equipment Models:** AnyConnect with Always-On
- **Data Sources:** VPN logs with `always_on` flag, MDM compliance
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect" earliest=-24h
| eval aov=if(match(lower(_raw),"(?i)always.?on|pre.?login"),1,0)
| lookup corp_laptops.csv hostname OUTPUT requires_aov
| where requires_aov=1 AND aov=0
| stats count by user, hostname, src_ip
```
- **Implementation:** Prefer explicit field from ASA if available. Join MDM “managed device” list for `requires_aov`.
- **Visualization:** Table (non-compliant hosts), Bar chart (violations by OU), Single value (violation count).
- **CIM Models:** N/A

---

### UC-17.2.20 · VPN Bandwidth Utilization Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Time-series bandwidth per headend and user cohort — complements UC-17.2.7 top talkers with **trend** and **gateway** dimension.
- **App/TA:** Splunk_TA_cisco-asa, NetFlow
- **Equipment Models:** ASA, routers
- **Data Sources:** VPN accounting, NetFlow from VPN interface
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" earliest=-7d
| bin _time span=1h
| stats sum(bytes_in) as in_b, sum(bytes_out) as out_b by _time, host
| eval gbps=round((in_b+out_b)*8/3600/1000000000,3)
| timechart span=1h avg(gbps) by host
```
- **Implementation:** If bytes not in syslog, use SNMP interface counters or NetFlow `exporter=VPN`. Alert on sustained >80% of circuit.
- **Visualization:** Line chart (Gbps per headend), Area chart (total VPN throughput), Table (peak hour).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Network_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.Network_Traffic
  by _time span=1h
```

---

### UC-17.2.21 · SSL VPN Certificate Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Availability
- **Value:** Tracks server certificate expiry and chain errors on SSL VPN / GlobalProtect portals from TLS handshake logs.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto
- **Equipment Models:** ASA, Palo Alto
- **Data Sources:** SSL/TLS syslog, management logs
- **SPL:**
```spl
index=vpn (sourcetype="cisco:asa" OR sourcetype="pan:system") earliest=-30d
| search "certificate" AND ("expired" OR "not trusted" OR "invalid")
| stats count by host, cert_cn, message
| sort -count
```
- **Implementation:** Prefer proactive cert inventory from PKI; this search catches client-reported errors. Alert on any `expired` match on production gateways.
- **Visualization:** Table (cert errors), Single value (error count), Timeline.
- **CIM Models:** N/A

---

### UC-17.2.22 · Remote Session Duration Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Statistical outliers in VPN session length — unusually short (brute probe) or long (unattended tunnel) vs UC-17.3.10 fixed thresholds.
- **App/TA:** VPN TA
- **Equipment Models:** Cisco ASA
- **Data Sources:** `vpn:session` or ASA with start/end
- **SPL:**
```spl
index=vpn sourcetype="vpn:session" earliest=-7d
| eval dur_hrs=(end_time-start_time)/3600
| eventstats median(dur_hrs) as med, stdev(dur_hrs) as sd by user
| eval z=if(sd>0, (dur_hrs-med)/sd, 0)
| where abs(z)>3 OR dur_hrs>48 OR dur_hrs<0.01
| table user, dur_hrs, med, z, src_ip
```
- **Implementation:** Requires reliable `start_time`/`end_time`. Tune z-score or use `anomalydetection`.
- **Visualization:** Scatter (duration vs time), Table (outliers), Histogram (duration).
- **CIM Models:** N/A

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

### UC-17.3.7 · Device Certificate Expiration and Renewal
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Expired device certificates break ZTNA and VPN access. Monitoring expiration and renewal success ensures continuous access and avoids outages.
- **App/TA:** PKI/certificate inventory, ZTNA device logs
- **Data Sources:** Certificate validity, renewal requests, enrollment events
- **SPL:**
```spl
index=zt sourcetype="device:cert"
| eval days_left=floor((expiry_time-now())/86400)
| where days_left < 30 OR renewal_status="failed"
| table device_id, cn, expiry_time, days_left, renewal_status
| sort days_left
```
- **Implementation:** Ingest device certificate inventory and renewal events. Alert when cert expires in <30 days or renewal fails. Report on cert distribution and renewal success rate. Automate renewal where possible.
- **Visualization:** Table (certs expiring soon), Single value (failed renewals), Bar chart (expiry by month).
- **CIM Models:** N/A

---

### UC-17.3.8 · Zero Trust Access Denial Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High denial rates may indicate policy misconfiguration or attacker probing. Trending supports tuning and security analysis.
- **App/TA:** ZTNA/access proxy logs
- **Data Sources:** Access decision logs (allow/deny), user, app, reason
- **SPL:**
```spl
index=zt sourcetype="zt:access"
| where decision="deny"
| stats count by user, application, deny_reason, _time span=1h
| where count > 20
| sort -count
```
- **Implementation:** Ingest access decision logs. Baseline denial rate by user and app. Alert on spike in denials or new deny reason. Report on top denied users and apps for policy review.
- **Visualization:** Line chart (denials over time), Table (denials by user/app), Bar chart (deny reasons).
- **CIM Models:** N/A

---

### UC-17.3.9 · NAC Quarantine and Remediation Duration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long quarantine or remediation times affect user productivity. Monitoring duration supports process improvement and exception handling.
- **App/TA:** NAC platform logs
- **Data Sources:** Quarantine start/end, remediation outcome
- **SPL:**
```spl
index=nac sourcetype="nac:quarantine"
| eval duration_min=(released_time - quarantine_time)/60
| stats avg(duration_min) as avg_mins, count by posture_violation, remediation_result
| where avg_mins > 60
| table posture_violation, remediation_result, count, avg_mins
```
- **Implementation:** Ingest NAC quarantine and release events. Compute time in quarantine and remediation success. Alert when average duration exceeds threshold. Report on violation types and remediation rate.
- **Visualization:** Table (quarantine duration by violation), Bar chart (avg duration), Pie chart (remediation outcome).
- **CIM Models:** N/A

---

### UC-17.3.10 · VPN Session Duration and Idle Timeout
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Anomalously long or short VPN sessions may indicate abuse or connectivity issues. Monitoring supports policy tuning and security review.
- **App/TA:** VPN gateway logs, RADIUS accounting
- **Data Sources:** Session start/end, duration, idle time
- **SPL:**
```spl
index=vpn sourcetype="vpn:session"
| eval duration_hrs=(end_time - start_time)/3600
| stats avg(duration_hrs) as avg_hrs, max(duration_hrs) as max_hrs, count by user
| where max_hrs > 24 OR avg_hrs > 12
| table user, count, avg_hrs, max_hrs
```
- **Implementation:** Ingest VPN session and accounting data. Compute session duration and idle time. Alert on sessions exceeding policy (e.g., >24h) or user with unusually long average. Report on session distribution.
- **Visualization:** Table (long sessions), Bar chart (avg duration by user), Line chart (session count trend).
- **CIM Models:** N/A

---

### UC-17.3.11 · Micro-Segment Traffic Baseline Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** New or unexpected traffic between segments may indicate lateral movement or misconfiguration. Anomaly detection supports Zero Trust enforcement.
- **App/TA:** Network flow logs, firewall/segment logs
- **Data Sources:** East-west traffic, segment IDs, flow counts
- **SPL:**
```spl
index=flows sourcetype="netflow"
| stats sum(bytes) as bytes, count by src_segment, dest_segment, _time span=1h
| eventstats avg(bytes) as avg_bytes by src_segment, dest_segment
| where bytes > (avg_bytes * 5)
| table src_segment, dest_segment, bytes, avg_bytes
```
- **Implementation:** Ingest segment-level or flow data. Baseline traffic between segment pairs. Alert when traffic exceeds baseline by threshold. Correlate with new connections and ZT policy. Report on segment traffic matrix.
- **Visualization:** Table (anomalous segment pairs), Heatmap (segment × segment traffic), Line chart (traffic trend).
- **CIM Models:** Network_Traffic

---

### UC-17.3.12 · Zscaler ZIA Policy Violation Trends
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Value:** Time-series of blocked violations per URL category and rule — tunes SWG policy and spots sudden policy drift.
- **App/TA:** Zscaler TA
- **Data Sources:** `sourcetype=zscaler:web` or `zscaler:zia`
- **SPL:**
```spl
index=proxy sourcetype="zscaler:web" earliest=-30d
| where action="blocked" OR threat_score>0
| timechart span=1d count by rule_name
```
- **Implementation:** Map `rule_name` / `policy` from ZIA. Alert when daily blocks for a rule exceed 2× 7-day average (possible mis-tuned category).
- **Visualization:** Line chart (blocks by rule), Stacked area (categories), Table (top rules).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.Network_Traffic
  where Network_Traffic.action=blocked
  by Network_Traffic.url span=1d
```

---

### UC-17.3.13 · ZPA Application Segment Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks connector health, app segment reachability, and error rates for ZPA-published apps.
- **App/TA:** Zscaler TA
- **Data Sources:** `sourcetype=zscaler:zpa`, connector telemetry
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa" earliest=-24h
| where match(lower(status),"(?i)fail|error|down") OR latency_ms>2000
| stats count by app_segment, connector_group, error_code
| sort -count
| head 30
```
- **Implementation:** Normalize `app_segment` and latency fields from your ZPA TA. Alert on connector group with >5% error rate vs prior week.
- **Visualization:** Table (unhealthy segments), Line chart (error rate), Single value (segments in alert).
- **CIM Models:** Authentication, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.dest span=1h
```

---

### UC-17.3.14 · Cisco Umbrella DNS Block Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Top blocked domains, identities, and policy hits for DNS-layer security tuning and threat hunting.
- **App/TA:** Cisco Umbrella TA
- **Data Sources:** `sourcetype=umbrella:dns`
- **SPL:**
```spl
index=dns sourcetype="umbrella:dns" earliest=-7d
| where action="blocked"
| stats count by domain, identity, categories
| sort -count
| head 50
```
- **Implementation:** Enrich with ASN or threat feed for rare domains. Alert on spike in blocks from single identity (possible compromise).
- **Visualization:** Bar chart (top domains), Table (identity × domain), Pie chart (categories).
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query span=1h
| where count > 100
```

---

### UC-17.3.15 · SASE Tunnel Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors IPSec/GRE/SSL tunnels from branch to SASE PoPs — packet loss, latency, and down events.
- **App/TA:** Zscaler, Prisma, vendor syslog
- **Data Sources:** `sourcetype=sase:tunnel`, SD-WAN to SASE
- **SPL:**
```spl
index=sase sourcetype="sase:tunnel" earliest=-24h
| eval healthy=if(match(lower(state),"(?i)up|active") AND packet_loss_pct < 2 AND latency_ms < 200,1,0)
| where healthy=0
| stats latest(latency_ms) as latency_ms latest(packet_loss_pct) as loss by tunnel_id, site
| sort loss
```
- **Implementation:** Field names vary (Zscaler GRE, Prisma IPSec). Use unified summary index if multi-vendor.
- **Visualization:** Table (unhealthy tunnels), Geo map (site), Line chart (loss trend).
- **CIM Models:** N/A

---

### UC-17.3.16 · Identity-Aware Proxy Access Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Baselines per-user access to internal apps via IAP/ZTNA; flags new apps, odd hours, or geos.
- **App/TA:** Google IAP, Azure AD App Proxy, ZPA
- **Data Sources:** `sourcetype=iap:access`, `zscaler:zpa`
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa" earliest=-30d
| eval day=strftime(_time,"%Y-%m-%d")
| stats dc(application) as apps_today by user, day
| eventstats avg(apps_today) as baseline by user
| where apps_today > baseline*3 AND apps_today>5
| table user, day, apps_today, baseline
```
- **Implementation:** Adapt to Google IAP JSON logs. Whitelist break-glass accounts.
- **Visualization:** Table (anomalies), Line chart (apps accessed per user), Heatmap (user × app).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.app span=1d
```

---

### UC-17.3.17 · Microsegmentation Policy Effectiveness
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Ratio of expected denies vs allows for critical segments — validates that “default deny” is actually enforced.
- **App/TA:** NSX, Illumio, Cisco Secure Workload
- **Data Sources:** `microseg:policy`
- **SPL:**
```spl
index=zt sourcetype="microseg:policy" earliest=-7d
| eval kind=if(action="deny","deny","allow")
| stats count as c by kind, policy_name
| eventstats sum(c) as tot by policy_name
| eval pct=round(100*c/tot,1)
| where kind="deny"
| table policy_name, pct, c
```
- **Implementation:** High deny % on locked-down segments is expected; unexpected **allow** spikes on deny-first policies warrant review (use companion search with `kind="allow"`).
- **Visualization:** Bar chart (deny % by policy), Table (policy mix), Line chart (deny trend).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.Network_Traffic
  where Network_Traffic.action=allowed
  by Network_Traffic.dest span=1h
```

---

### UC-17.3.18 · Device Trust Score Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Fleet-level and cohort trend of device trust scores — extends point-in-time UC-17.3.2.
- **App/TA:** Zscaler, Microsoft Entra, CrowdStrike ZTNA
- **Data Sources:** `zscaler:device_posture`, `zt:device_trust`
- **SPL:**
```spl
index=zt sourcetype="zscaler:device_posture" earliest=-30d
| timechart span=1d avg(trust_score) as avg_trust by os_type
```
- **Implementation:** Ensure `trust_score` is numeric 0–100. Alert when 7-day moving average drops >10 points for Windows corporate fleet.
- **Visualization:** Line chart (avg trust by OS), Single value (fleet avg), Area chart (distribution).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.src span=1d
```

---

### UC-17.3.19 · Continuous Authentication Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracks step-up auth, re-auth, and session risk evaluation outcomes for policies requiring continuous verification.
- **App/TA:** Microsoft Entra ID Protection, Okta, ZPA
- **Data Sources:** `sourcetype=azure:signin`, `okta:system`
- **SPL:**
```spl
index=identity sourcetype="azure:signin" earliest=-7d
| where risk_level!="none" OR authentication_requirement="multiFactorAuthentication"
| stats count by user, risk_detail, result
| sort -count
| head 40
```
- **Implementation:** Map Entra `riskLevelDuringSignIn` and CA grant controls. Report MFA completion rate when risk elevated.
- **Visualization:** Table (risky sign-ins), Bar chart (outcomes), Line chart (risk events / day).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user span=1h
```

---

### UC-17.3.20 · Browser Isolation Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Operational
- **Value:** Measures adoption of remote browser isolation (RBI) sessions vs direct access — for licensing and risky-site coverage.
- **App/TA:** Menlo, Zscaler RBI, Island
- **Data Sources:** `sourcetype=rbi:session`
- **SPL:**
```spl
index=zt sourcetype="rbi:session" earliest=-30d
| eval isolated=if(match(lower(session_type),"(?i)isolated|rbi"),1,0)
| timechart span=1d sum(isolated) as isolated_sessions, count as total_sessions
| eval isolation_rate=round(100*isolated_sessions/total_sessions,1)
```
- **Implementation:** Map vendor-specific session types. Alert when isolation_rate drops vs baseline for high-risk categories.
- **Visualization:** Line chart (isolation rate), Bar chart (sessions by app), Single value (% isolated).
- **CIM Models:** N/A

---

### UC-17.3.21 · SWG Bypass Attempt Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects attempts to reach direct IPs, misuse PAC files, or tunnel out of SWG inspection.
- **App/TA:** Zscaler, Netskope
- **Data Sources:** `zscaler:web`, endpoint proxy logs
- **SPL:**
```spl
index=proxy sourcetype="zscaler:web" earliest=-24h
| where match(lower(reason),"(?i)bypass|tunnel|direct|pac") OR match(lower(url),"(?i)proxy\.pac")
| stats count by user, src_ip, reason
| sort -count
```
- **Implementation:** Correlate with firewall deny for non-standard ports. Tune for false positives from dev tools.
- **Visualization:** Table (bypass attempts), Bar chart (by user), Timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.Network_Traffic
  by Network_Traffic.user span=1h
| where count > 200
```

---

### UC-17.3.22 · ZTNA Application Access Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** p95 latency per published application for user experience SLAs on ZTNA paths.
- **App/TA:** Zscaler ZPA, Cloudflare Access
- **Data Sources:** `zscaler:zpa` access logs with `latency_ms`
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa" earliest=-24h
| stats perc95(latency_ms) as p95_ms, count by application
| where p95_ms > 800
| sort -p95_ms
```
- **Implementation:** Segment by connector group and region. Compare before/after app migrations.
- **Visualization:** Bar chart (p95 by app), Line chart (p95 trend), Table (worst apps).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Network_Traffic.response_time) as rt
  from datamodel=Network_Traffic.Network_Traffic
  by Network_Traffic.url span=5m
```

---

### UC-17.3.23 · Prisma Access Tunnel Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** IPSec/SSL tunnel state, latency, and error codes for Palo Alto Prisma Access remote networks and mobile users.
- **App/TA:** Splunk_TA_paloalto, Prisma Access cloud logging
- **Data Sources:** `sourcetype=prisma:access:tunnel` or PAN-OS VPN logs
- **SPL:**
```spl
index=sase sourcetype="prisma:access:tunnel" earliest=-24h
| eval ok=if(match(lower(tunnel_state),"(?i)up|active") AND error_code=0,1,0)
| where ok=0
| stats latest(latency_ms) as latency_ms latest(error_code) as error_code by tunnel_name, site_id
| sort latency_ms
```
- **Implementation:** Map Prisma Remote Network vs Mobile User templates. Join SD-WAN site name from CMDB.
- **Visualization:** Table (down tunnels), Map (sites), Line chart (tunnel availability %).
- **CIM Models:** N/A

---

### UC-17.3.24 · Conditional Access Policy Enforcement (Entra ID)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Volume of grants vs blocks per named CA policy — complements generic UC-17.3.1 with Microsoft-specific policy dimension.
- **App/TA:** Azure / Entra TA
- **Data Sources:** `sourcetype=azure:signin` with `conditional_access_status`
- **SPL:**
```spl
index=identity sourcetype="azure:signin" earliest=-7d
| where isnotnull(conditional_access_policy_name)
| stats count by conditional_access_policy_name, conditional_access_status
| sort -count
```
- **Implementation:** Include `failureReason` for blocks. Alert when block rate for a policy jumps without change ticket.
- **Visualization:** Stacked bar (policy × status), Table (top blocks), Line chart (blocks / day per policy).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user span=1h
```

---
