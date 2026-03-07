## 10. Security Infrastructure

### 10.1 Next-Gen Firewalls (Security-Focused)

**Primary App/TA:** Palo Alto Networks Add-on (`Splunk_TA_paloalto`), Cisco Firepower TA, Fortinet FortiGate TA.

---

### UC-10.1.1 · Threat Prevention Event Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Trending threat detections reveals attack campaigns, persistent threats, and the effectiveness of security controls.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_cisco-firepower
- **Data Sources:** Threat logs (IPS, AV, anti-spyware detections)
- **SPL:**
```spl
index=pan sourcetype="pan:threat" severity IN ("critical","high")
| timechart span=1h count by subtype
```
- **Implementation:** Forward NGFW threat logs to Splunk via syslog or API. Parse severity, threat name, source/destination, and action. Track by severity and type over time. Alert on critical severity detections. Correlate with endpoint data.
- **Visualization:** Line chart (threat events by severity), Bar chart (top threats), Table (critical events), Stacked area (threat types over time).
- **CIM Models:** Network_Traffic, Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.1.2 · Wildfire / Sandbox Verdicts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Tracks zero-day and unknown malware detection effectiveness. Malicious verdicts require immediate investigation of affected hosts.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** Wildfire submission logs, sandbox analysis results
- **SPL:**
```spl
index=pan sourcetype="pan:wildfire"
| stats count by verdict, filetype
| eval verdict_label=case(verdict=0,"benign", verdict=1,"malware", verdict=2,"grayware", verdict=4,"phishing")
```
- **Implementation:** Enable Wildfire logging on NGFW. Forward submission results to Splunk. Alert immediately on malware verdicts. Track affected users/hosts for investigation. Report on submission volumes and malicious file types.
- **Visualization:** Pie chart (verdict distribution), Table (malware verdicts with details), Line chart (submissions over time), Bar chart (by file type).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-10.1.3 · C2 Communication Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Command-and-control communication indicates active compromise. Detection enables containment before data exfiltration or lateral movement.
- **App/TA:** `Splunk_TA_paloalto`, threat intel feeds
- **Data Sources:** Threat logs (C2 signatures), URL filtering (malware/C2 categories), DNS logs
- **SPL:**
```spl
index=pan sourcetype="pan:threat" category="command-and-control"
| stats count, values(dest_ip) as c2_servers by src_ip, src_user
| sort -count
```
- **Implementation:** Enable URL filtering and threat prevention with C2 categories. Forward to Splunk. Alert immediately on any C2 detection. Integrate with threat intel feeds for IP/domain enrichment. Trigger automated containment via SOAR.
- **Visualization:** Table (C2 detections with source/dest), Geo map (C2 server locations), Timeline (C2 events), Network diagram.
- **CIM Models:** Network_Traffic, Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.1.4 · DNS Sinkhole Hits
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** DNS sinkhole hits confirm infected endpoints attempting to reach malicious domains. Each hit is a confirmed compromise indicator.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** DNS proxy logs (sinkhole action), threat logs
- **SPL:**
```spl
index=pan sourcetype="pan:threat" action="sinkhole"
| stats count by src_ip, domain, threat_name
| sort -count
```
- **Implementation:** Configure DNS sinkhole on NGFW. Forward threat logs with sinkhole actions to Splunk. Alert on each unique source IP hitting sinkhole. Trigger automated endpoint investigation. Track resolution status.
- **Visualization:** Table (sinkholed hosts with domains), Single value (compromised hosts count), Bar chart (top sinkholed domains).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-10.1.5 · SSL Decryption Coverage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Encrypted traffic that isn't inspected creates a blind spot. Measuring decryption coverage ensures security visibility.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** Decryption statistics, traffic logs (encrypted vs decrypted flags)
- **SPL:**
```spl
index=pan sourcetype="pan:traffic"
| eval decrypted=if(flags LIKE "%decrypt%",1,0)
| stats sum(decrypted) as decrypted_sessions, count as total_sessions
| eval coverage_pct=round(decrypted_sessions/total_sessions*100,1)
```
- **Implementation:** Enable decryption logging on NGFW. Track percentage of HTTPS traffic being decrypted. Identify exempted destinations and evaluate risk. Report coverage to security leadership. Target >80% coverage.
- **Visualization:** Single value (decryption coverage %), Pie chart (decrypted vs bypassed), Bar chart (top bypassed destinations).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### 10.2 Intrusion Detection/Prevention (IDS/IPS)

**Primary App/TA:** Vendor-specific TAs, Snort/Suricata syslog parsing.

---

### UC-10.2.1 · Alert Severity Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Trending IDS alerts reveals attack patterns, campaign surges, and tuning opportunities. Supports SOC workload planning.
- **App/TA:** TA-suricata, Splunk_TA_cisco-firepower
- **Data Sources:** IDS/IPS alert logs
- **SPL:**
```spl
index=ids sourcetype="snort:alert"
| timechart span=1h count by priority
```
- **Implementation:** Forward IDS alerts to Splunk via syslog. Normalize severity/priority fields. Track alert volume by severity over time. Identify noisy signatures for tuning. Alert on sudden spikes in high-severity events.
- **Visualization:** Stacked area (alerts by severity), Line chart (alert volume trend), Table (top alerts today).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.2.2 · Top Targeted Hosts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Identifies the most-attacked internal hosts, prioritizing vulnerability remediation and incident investigation.
- **App/TA:** IDS/IPS TA
- **Data Sources:** IDS/IPS alert logs (destination host)
- **SPL:**
```spl
index=ids sourcetype="snort:alert" priority<=2
| stats count, dc(signature) as unique_sigs by dest_ip
| sort -count
| head 20
```
- **Implementation:** Parse destination IP from IDS alerts. Aggregate by target host. Enrich with CMDB data (asset owner, criticality). Alert when a single host receives multiple high-severity alerts. Trigger vulnerability scan for top targets.
- **Visualization:** Table (top targeted hosts), Bar chart (alerts by host), Geo map (source attackers).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.2.3 · Signature Coverage Gaps
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Identifying network segments without IDS coverage ensures comprehensive threat detection across the infrastructure.
- **App/TA:** IDS sensor health monitoring
- **Data Sources:** Sensor health reports, network segment inventory
- **SPL:**
```spl
| inputlookup network_segments.csv
| join type=left segment_name
    [search index=ids sourcetype="snort:alert" earliest=-7d
     | stats count by sensor, segment_name]
| where isnull(count) OR count=0
| table segment_name, expected_sensor, count
```
- **Implementation:** Maintain network segment inventory with expected IDS sensor mapping. Compare against actual alert data. Alert when a segment has no IDS events for >7 days (sensor may be down or misconfigured).
- **Visualization:** Table (uncovered segments), Status grid (segment × coverage), Single value (coverage %).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.2.4 · False Positive Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** High false positive rates waste analyst time and cause alert fatigue. Systematic tracking drives tuning improvements.
- **App/TA:** IDS TA + analyst workflow
- **Data Sources:** IDS alerts + analyst disposition data (true/false positive)
- **SPL:**
```spl
index=ids sourcetype="snort:alert"
| join signature [| inputlookup signature_dispositions.csv]
| stats count(eval(disposition="false_positive")) as fp, count as total by signature
| eval fp_rate=round(fp/total*100,1)
| where fp_rate > 50
| sort -fp_rate
```
- **Implementation:** Track analyst dispositions for IDS alerts (true positive, false positive, benign). Calculate false positive rate per signature. Flag signatures with >50% FP rate for tuning. Report on overall alert quality metrics.
- **Visualization:** Bar chart (FP rate by signature), Line chart (FP rate trend), Table (signatures needing tuning).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### UC-10.2.5 · Lateral Movement Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** IDS detections on internal network segments indicate an attacker has breached the perimeter and is moving laterally.
- **App/TA:** IDS TA (internal sensors)
- **Data Sources:** IDS alerts from internal/east-west sensors
- **SPL:**
```spl
index=ids sourcetype="snort:alert" sensor_zone="internal"
| search category IN ("attempted-admin","trojan-activity","policy-violation","misc-attack")
| stats count by src_ip, dest_ip, signature
| sort -count
```
- **Implementation:** Deploy IDS sensors on internal network segments (not just perimeter). Forward alerts to Splunk. Alert on any high-severity internal detections. Correlate with AD authentication events and endpoint data for full attack chain visibility.
- **Visualization:** Network diagram (lateral movement paths), Table (internal IDS alerts), Timeline (attack progression).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h
| sort -count
```

---

### 10.3 Endpoint Detection & Response (EDR)

**Primary App/TA:** CrowdStrike TA (`TA-crowdstrike-falcon-event-streams`), Microsoft Defender TA, Cisco Secure Endpoint TA, SentinelOne TA.

---

### UC-10.3.1 · Malware Detection Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detection trends reveal campaign targeting, endpoint hygiene, and control effectiveness. Spikes indicate active incidents.
- **App/TA:** TA-crowdstrike-falcon-event-streams, TA-microsoft-defender
- **Data Sources:** EDR detection events
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| timechart span=1d count by severity
```
- **Implementation:** Ingest EDR detection events via TA or API. Normalize detection severity. Track daily detection rates by severity, type, and business unit. Alert on spikes exceeding 2× daily baseline. Report on detection-to-response times.
- **Visualization:** Line chart (detections over time), Bar chart (detections by type), Pie chart (severity distribution).
- **CIM Models:** Malware, Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Malware.Malware_Attacks
  by Malware_Attacks.dest Malware_Attacks.signature Malware_Attacks.action span=1h
| sort -count
```

---

### UC-10.3.2 · Quarantine Action Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed quarantine means malware remains active on the endpoint. Monitoring ensures automated remediation is working.
- **App/TA:** EDR TA
- **Data Sources:** EDR remediation/action logs
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| stats count(eval(action="quarantined")) as quarantined, count(eval(action="allowed")) as allowed by severity
| eval quarantine_rate=round(quarantined/(quarantined+allowed)*100,1)
```
- **Implementation:** Track EDR remediation actions (quarantine, kill process, isolate). Calculate quarantine success rate. Alert on failed quarantine actions. Follow up on "allowed" malware detections to ensure analyst review.
- **Visualization:** Pie chart (action distribution), Single value (quarantine success %), Table (failed quarantine events).
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-10.3.3 · Agent Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Endpoints without healthy EDR agents are blind spots. Gap detection ensures comprehensive coverage.
- **App/TA:** EDR TA, scripted input
- **Data Sources:** EDR agent status API, last check-in timestamps
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:sensor_health"
| eval hours_since_checkin=round((now()-last_seen_epoch)/3600,1)
| where hours_since_checkin > 24 OR sensor_version < "6.50"
| table hostname, os, sensor_version, hours_since_checkin, status
```
- **Implementation:** Poll EDR agent status API daily. Identify agents offline >24 hours, outdated versions, or degraded status. Cross-reference with CMDB for full coverage analysis. Alert on critical servers with unhealthy agents.
- **Visualization:** Table (unhealthy agents), Single value (% healthy), Pie chart (agent version distribution), Bar chart (offline by OS).
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-10.3.4 · Behavioral Detection Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Behavioral detections catch attacks that bypass signatures (fileless malware, LOLBins, living-off-the-land). These are high-fidelity signals.
- **App/TA:** EDR TA
- **Data Sources:** EDR behavioral/heuristic alerts
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection" technique_id="T*"
| stats count by technique_id, tactic, hostname
| sort -count
```
- **Implementation:** Ingest behavioral detection data. Map to MITRE ATT&CK framework (technique_id, tactic). Alert on high-confidence behavioral detections. Track most common techniques for threat intelligence and red team exercises.
- **Visualization:** MITRE ATT&CK heatmap, Table (behavioral detections), Bar chart (top techniques).
- **CIM Models:** Malware, Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Malware.Malware_Attacks
  by Malware_Attacks.dest Malware_Attacks.signature Malware_Attacks.action span=1h
| sort -count
```

---

### UC-10.3.5 · Endpoint Isolation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Isolation events indicate active incident response. Tracking ensures isolation is maintained and properly lifted when resolved.
- **App/TA:** EDR TA
- **Data Sources:** EDR containment/isolation logs
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:containment"
| table _time, hostname, action, initiated_by, reason
| sort -_time
```
- **Implementation:** Track all isolation events (isolate, un-isolate). Alert on isolation events for awareness. Track isolation duration. Alert when endpoints remain isolated >24 hours without resolution. Maintain isolation audit trail.
- **Visualization:** Table (isolated endpoints), Timeline (isolation events), Single value (currently isolated count).
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-10.3.6 · Threat Hunting Indicators
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Proactive threat hunting using EDR telemetry detects stealthy threats that evade automated detection.
- **App/TA:** EDR TA (telemetry data)
- **Data Sources:** EDR process telemetry, file events, network connections
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:events"
| search (process_name="powershell.exe" AND command_line="*-enc*")
    OR (process_name="rundll32.exe" AND parent_process_name!="explorer.exe")
    OR (process_name="certutil.exe" AND command_line="*-urlcache*")
| table _time, hostname, user, process_name, command_line, parent_process_name
```
- **Implementation:** Ingest EDR telemetry (process creation, network connections, file writes). Create hunting queries for LOLBin usage, encoded PowerShell, suspicious parent-child process relationships. Schedule as recurring searches for continuous hunting.
- **Visualization:** Table (suspicious indicators), Timeline (hunting hits), Bar chart (indicators by technique).
- **CIM Models:** Malware, Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Malware.Malware_Attacks
  by Malware_Attacks.dest Malware_Attacks.signature Malware_Attacks.action span=1h
| sort -count
```

---

### UC-10.3.7 · EDR Coverage Gaps
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Identifies endpoints without EDR protection, closing blind spots that attackers exploit.
- **App/TA:** EDR API + CMDB lookup
- **Data Sources:** EDR agent inventory, CMDB/asset inventory
- **SPL:**
```spl
| inputlookup cmdb_endpoints.csv WHERE os_type IN ("Windows","Linux","macOS")
| join type=left hostname [search index=edr sourcetype="crowdstrike:sensor_health" | stats latest(status) as edr_status by hostname]
| where isnull(edr_status) OR edr_status!="active"
| table hostname, os_type, department, edr_status
```
- **Implementation:** Export EDR agent inventory and cross-reference with CMDB/AD computer accounts. Identify systems without agents. Report coverage percentage. Alert when coverage drops below target (e.g., <98%). Prioritize critical servers.
- **Visualization:** Single value (coverage %), Table (uncovered endpoints), Pie chart (covered vs uncovered), Bar chart (gaps by department).
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-10.3.8 · Ransomware Canary Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** EDR-detected mass file encryption patterns provide earliest possible ransomware detection, enabling automated containment.
- **App/TA:** EDR TA
- **Data Sources:** EDR behavioral detection (mass file modification patterns)
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| search tactic="impact" technique_id="T1486"
| table _time, hostname, user, process_name, severity, description
```
- **Implementation:** Ensure EDR has behavioral ransomware detection enabled. Alert at critical priority on any ransomware behavioral detection. Integrate with SOAR for automated endpoint isolation. Track affected file scope from EDR telemetry.
- **Visualization:** Single value (ransomware detections — target: 0), Table (detection details), Timeline (ransomware events).
- **CIM Models:** Malware, Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Malware.Malware_Attacks
  by Malware_Attacks.dest Malware_Attacks.signature Malware_Attacks.action span=1h
| sort -count
```

---

### 10.4 Email Security

**Primary App/TA:** Splunk Add-on for Microsoft Office 365 (`Splunk_TA_MS_O365`), Proofpoint TA, vendor-specific email security TAs.

---

### UC-10.4.1 · Phishing Detection Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures email security effectiveness. Increasing phishing volumes or declining detection rates indicate evolving threats.
- **App/TA:** Splunk_TA_MS_O365, TA-proofpoint
- **Data Sources:** Email security gateway logs, EOP message trace
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| eval is_phish=if(match(FilteringResult,"Phish") OR match(FilteringResult,"Spoof"),1,0)
| stats sum(is_phish) as phishing_caught, count as total_messages
| eval phish_rate=round(phishing_caught/total_messages*100,4)
```
- **Implementation:** Ingest email security logs (EOP message trace, gateway logs). Track phishing detections over time. Calculate detection rate vs total messages. Alert on spikes in phishing volume. Report on phishing types and targeted users.
- **Visualization:** Line chart (phishing volume trend), Single value (phishing rate %), Bar chart (phishing by type), Table (top targeted users).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  where All_Email.action=blocked
  by All_Email.src_user All_Email.recipient All_Email.message_type span=1h
| sort -count
```

---

### UC-10.4.2 · Malicious Attachment Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Attachment-based threats bypass URL filtering. Tracking by file type reveals attack vectors and informs policy decisions.
- **App/TA:** Email security TA
- **Data Sources:** Email gateway attachment scanning logs, safe attachments logs
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| search FilteringResult="*malware*" OR FilteringResult="*SafeAttachment*"
| stats count by SenderAddress, Subject, FilteringResult
| sort -count
```
- **Implementation:** Enable attachment scanning in email gateway. Ingest scanning results. Track detections by file type, sender domain, and verdict. Alert on malicious attachments reaching users (detection after delivery). Report on blocked attachment statistics.
- **Visualization:** Bar chart (detections by file type), Table (malicious attachments), Line chart (detection trend), Pie chart (verdict distribution).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  where All_Email.action=blocked
  by All_Email.src_user All_Email.recipient All_Email.message_type span=1h
| sort -count
```

---

### UC-10.4.3 · URL Click Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks which users click malicious URLs in emails — the moment a phishing email becomes an active incident.
- **App/TA:** Splunk_TA_MS_O365 (Safe Links), Proofpoint URL Defense
- **Data Sources:** URL rewrite/protection logs, click tracking events
- **SPL:**
```spl
index=email sourcetype="ms:o365:dlp" OR sourcetype="proofpoint:click"
| search verdict="malicious" AND action="allowed"
| table _time, userPrincipalName, url, verdict, action
```
- **Implementation:** Enable Safe Links (M365) or URL Defense (Proofpoint). Ingest click tracking data. Alert immediately when a user clicks a malicious URL. Trigger automated password reset and endpoint scan. Track click-through rates for security awareness metrics.
- **Visualization:** Table (malicious URL clicks), Bar chart (clicks by user), Timeline (click events), Single value (clicks on malicious URLs today).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-10.4.4 · DLP Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Email DLP violations indicate potential data exfiltration or policy non-compliance. Monitoring supports regulatory compliance.
- **App/TA:** Splunk_TA_MS_O365
- **Data Sources:** M365 DLP logs, email gateway DLP events
- **SPL:**
```spl
index=email sourcetype="ms:o365:dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInformationType
| sort -count
```
- **Implementation:** Configure M365 DLP policies for sensitive data types (SSN, credit card, etc.). Ingest DLP violation events. Alert on high-severity violations. Track violation trends per policy and user for compliance reporting.
- **Visualization:** Bar chart (violations by policy), Table (top violators), Line chart (violation trend), Pie chart (by data type).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-10.4.5 · Spoofed Email Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** DMARC/SPF/DKIM failures indicate email spoofing attempts. Monitoring validates email authentication configuration.
- **App/TA:** Email security TA
- **Data Sources:** DMARC aggregate reports, email authentication logs
- **SPL:**
```spl
index=email sourcetype="dmarc:aggregate"
| where dkim_result!="pass" OR spf_result!="pass"
| stats count by source_ip, header_from, dkim_result, spf_result, disposition
| sort -count
```
- **Implementation:** Configure DMARC reporting (aggregate to a designated mailbox). Ingest DMARC XML reports. Track authentication failures by sending domain. Alert on spoofing of your own domains. Move toward DMARC p=reject for full protection.
- **Visualization:** Table (authentication failures), Bar chart (failures by domain), Pie chart (pass vs fail), Line chart (spoofing trend).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-10.4.6 · Email Volume Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual outbound email volumes may indicate compromised accounts used for spam/phishing or mass data exfiltration via email.
- **App/TA:** Splunk_TA_MS_O365, Splunk_TA_microsoft-exchange
- **Data Sources:** Email message tracking logs (outbound)
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace" Direction="Outbound"
| stats count by SenderAddress
| eventstats avg(count) as avg_sent, stdev(count) as stdev_sent
| where count > avg_sent + 3*stdev_sent
| table SenderAddress, count, avg_sent
```
- **Implementation:** Track outbound email volume per sender. Baseline normal patterns. Alert when any sender exceeds 3× standard deviation. Correlate with sign-in events to detect compromised accounts. Report on top senders for capacity planning.
- **Visualization:** Bar chart (top senders), Line chart (outbound volume trend), Table (anomalous senders).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  by All_Email.src_user All_Email.recipient All_Email.action span=1h
| sort -count
```

---

### UC-10.4.7 · Quarantine Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks quarantine effectiveness and user release requests to balance security with user productivity.
- **App/TA:** Splunk_TA_MS_O365, email gateway TA
- **Data Sources:** Email quarantine logs, release request logs
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| search FilteringResult="*Quarantine*"
| stats count by FilteringResult, SenderAddress
| sort -count
```
- **Implementation:** Track quarantine volumes, reasons, and user release requests. Alert on unusual quarantine rates (may indicate new phishing campaign). Monitor false positive rate (legitimate emails quarantined) for policy tuning.
- **Visualization:** Bar chart (quarantine reasons), Line chart (quarantine volume trend), Table (release requests), Single value (quarantine rate %).
- **CIM Models:** Email
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Email.All_Email
  where All_Email.action=blocked
  by All_Email.src_user All_Email.recipient All_Email.message_type span=1h
| sort -count
```

---

### 10.5 Web Security / Secure Web Gateway

**Primary App/TA:** Cisco Umbrella TA (`Splunk_TA_cisco-umbrella`), Zscaler TA, Netskope TA, vendor-specific SWG TAs.

---

### UC-10.5.1 · Blocked Category Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Trending blocked categories reveals user behavior patterns and informs acceptable use policy. Spikes may indicate infections.
- **App/TA:** Splunk Add-on for Cisco Umbrella, TA-zscaler
- **Data Sources:** SWG/proxy logs (URL category, action)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella" action="Blocked"
| top limit=20 categories
```
- **Implementation:** Forward SWG logs to Splunk. Track blocked requests by category over time. Identify trending categories. Alert on spikes in malware/phishing categories. Report on policy effectiveness.
- **Visualization:** Bar chart (top blocked categories), Line chart (blocks over time), Pie chart (block distribution).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action=blocked
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| sort -count
```

---

### UC-10.5.2 · Shadow IT Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unapproved SaaS usage creates data security risks and compliance gaps. Discovery enables governance and risk assessment.
- **App/TA:** SWG/CASB TA
- **Data Sources:** SWG logs (application identification), CASB logs
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella"
| stats dc(src_ip) as unique_users, sum(bytes) as total_bytes by app_name
| lookup approved_apps.csv app_name OUTPUT approved
| where isnull(approved) OR approved="No"
| sort -unique_users
```
- **Implementation:** Enable application identification in SWG. Maintain lookup of approved SaaS applications. Identify unapproved apps by user count and data volume. Report to IT governance for risk assessment. Track adoption of approved alternatives.
- **Visualization:** Table (unapproved apps with user counts), Bar chart (top shadow IT apps), Pie chart (approved vs unapproved traffic).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-10.5.3 · Malware Download Blocks
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Each blocked malware download represents a prevented infection. Tracking reveals targeted users and attack vectors.
- **App/TA:** SWG TA
- **Data Sources:** SWG threat logs (malware blocks)
- **SPL:**
```spl
index=proxy sourcetype="zscaler:web" action="Blocked" threat_category="Malware"
| stats count by src_user, url, threat_name
| sort -count
```
- **Implementation:** Enable threat scanning in SWG. Forward threat events to Splunk. Alert on malware download blocks for user awareness. Track targeted users for phishing correlation. Report on malware types and delivery methods.
- **Visualization:** Bar chart (malware blocks by type), Table (blocked downloads), Line chart (block rate trend), Single value (blocks today).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action=blocked
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| sort -count
```

---

### UC-10.5.4 · DLP over Web Traffic
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Web DLP events indicate sensitive data being uploaded to unauthorized destinations. Critical for compliance.
- **App/TA:** SWG/CASB TA
- **Data Sources:** SWG DLP logs (file uploads, paste detection)
- **SPL:**
```spl
index=proxy sourcetype="netskope:events" alert_type="DLP"
| stats count by user, app, policy_name, file_type
| sort -count
```
- **Implementation:** Configure DLP policies in SWG/CASB for sensitive data patterns. Ingest DLP violation events. Alert on high-severity violations. Track by user, destination app, and data type. Report for compliance audits.
- **Visualization:** Table (DLP violations), Bar chart (violations by policy), Line chart (violation trend), Pie chart (by data type).
- **CIM Models:** Web, Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-10.5.5 · DNS Security Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Blocked DNS queries to malicious domains indicate infection attempts or active compromise. Each block is a security win.
- **App/TA:** Splunk Add-on for Cisco Umbrella
- **Data Sources:** Umbrella/DNS security logs
- **SPL:**
```spl
index=dns_security sourcetype="cisco:umbrella" action="Blocked"
| stats count by internalIp, domain, categories
| where match(categories,"Malware|Command and Control|Phishing")
| sort -count
```
- **Implementation:** Deploy DNS security (Umbrella, Zscaler). Forward blocked query logs to Splunk. Alert on blocks in malware/C2/phishing categories. Track affected internal IPs for investigation. Report on DNS security effectiveness.
- **Visualization:** Table (blocked domains with sources), Bar chart (blocks by category), Single value (unique blocked domains today).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-10.5.6 · Bandwidth Abuse Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Excessive bandwidth on non-business sites impacts network performance and productivity. Detection supports acceptable use enforcement.
- **App/TA:** SWG TA
- **Data Sources:** SWG traffic logs (bytes transferred, URL category)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella"
| stats sum(bytes) as total_bytes by src_user, categories
| where match(categories,"Streaming|Gaming|Social") AND total_bytes > 1073741824
| eval gb=round(total_bytes/1073741824,2)
| table src_user, categories, gb
```
- **Implementation:** Track bandwidth usage per user by URL category. Alert when individual users exceed thresholds on non-business categories (>1GB/day on streaming). Report top bandwidth consumers for management review.
- **Visualization:** Bar chart (bandwidth by user/category), Table (top consumers), Pie chart (bandwidth by category).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-10.5.7 · Unencrypted Traffic Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Sensitive data transmitted over HTTP is vulnerable to interception. Detection ensures encryption compliance.
- **App/TA:** SWG TA
- **Data Sources:** SWG traffic logs (protocol, URL)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella" protocol="HTTP"
| search NOT url="http://ocsp.*" NOT url="http://crl.*"
| stats count by src_user, domain
| sort -count
```
- **Implementation:** Monitor HTTP (non-HTTPS) traffic in SWG logs. Filter out legitimate HTTP uses (OCSP, CRL). Alert when sensitive applications are accessed over HTTP. Report unencrypted traffic percentage as a security metric.
- **Visualization:** Table (HTTP traffic by destination), Pie chart (HTTP vs HTTPS), Line chart (unencrypted traffic trend).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### 10.6 Vulnerability Management

**Primary App/TA:** Tenable TA (`TA-tenable`), Qualys TA, Rapid7 TA.

---

### UC-10.6.1 · Critical Vulnerability Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracking critical vulnerabilities over time measures security posture improvement and identifies remediation stalls.
- **App/TA:** TA-tenable, TA-QualysCloudPlatform
- **Data Sources:** Vulnerability scan results (severity, CVE, affected asset)
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln"
| where severity IN ("Critical","High")
| timechart span=1d dc(cve_id) as unique_vulns by severity
```
- **Implementation:** Ingest scan results from vulnerability management platform. Track unique vulnerabilities by severity over time. Alert when critical count exceeds threshold or increases. Report on remediation progress weekly.
- **Visualization:** Line chart (vuln count trend by severity), Single value (critical vuln count), Bar chart (top CVEs), Table (critical vulnerabilities).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.2 · Mean Time to Remediation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** MTTR measures remediation efficiency. Long MTTR indicates process bottlenecks or resource constraints requiring management attention.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results with first_seen and last_seen dates
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" state="Fixed"
| eval mttr_days=round((fixed_date-first_seen)/86400)
| stats avg(mttr_days) as avg_mttr, median(mttr_days) as median_mttr by severity
```
- **Implementation:** Track first_seen and fixed_date for each vulnerability. Calculate MTTR by severity. Report against SLA targets (Critical: 7d, High: 30d, Medium: 90d). Identify teams with consistently high MTTR for process improvement.
- **Visualization:** Bar chart (MTTR by severity), Line chart (MTTR trend), Table (SLA compliance by team).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.3 · Scan Coverage Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Assets not scanned are unknown risks. Coverage monitoring ensures comprehensive vulnerability assessment.
- **App/TA:** Vuln management TA + CMDB
- **Data Sources:** Scan activity, asset inventory
- **SPL:**
```spl
| inputlookup cmdb_assets.csv
| join type=left hostname [search index=vulnerability sourcetype="tenable:vuln" | stats latest(_time) as last_scan by hostname]
| eval days_since_scan=round((now()-last_scan)/86400)
| where isnull(last_scan) OR days_since_scan > 30
| table hostname, os, department, last_scan, days_since_scan
```
- **Implementation:** Cross-reference scan targets with CMDB. Identify assets not scanned in 30 days. Alert on scan failures. Track coverage percentage as a KPI. Report on uncovered assets for remediation.
- **Visualization:** Single value (scan coverage %), Table (unscanned assets), Pie chart (scanned vs unscanned), Bar chart (gaps by department).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.4 · Patch Compliance by Team/BU
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Per-team compliance views drive accountability and enable targeted remediation efforts where they're most needed.
- **App/TA:** Vuln management TA + CMDB
- **Data Sources:** Scan results enriched with CMDB ownership data
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity IN ("Critical","High")
| lookup cmdb_assets.csv hostname OUTPUT department, owner
| stats dc(cve_id) as open_vulns, dc(hostname) as affected_hosts by department
| sort -open_vulns
```
- **Implementation:** Enrich vulnerability data with asset ownership from CMDB. Aggregate by team/business unit. Create weekly compliance scorecard. Share with leadership for accountability. Track improvement trends per team.
- **Visualization:** Bar chart (vulns by team), Table (team compliance scorecard), Line chart (compliance trend by team).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.5 · Exploitable Vulnerability Prioritization
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Not all vulnerabilities are equal — those with known exploits pose immediate risk. Prioritization focuses remediation on the highest-risk items.
- **App/TA:** Vuln management TA + threat intel
- **Data Sources:** Scan results + CISA KEV catalog + EPSS scores
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity="Critical"
| lookup cisa_kev.csv cve_id OUTPUT known_exploited, ransomware_associated
| lookup epss_scores.csv cve_id OUTPUT epss_score
| where known_exploited="Yes" OR epss_score > 0.5
| table hostname, cve_id, severity, epss_score, known_exploited, ransomware_associated
| sort -epss_score
```
- **Implementation:** Maintain CISA KEV and EPSS lookup tables (update weekly). Enrich vulnerability data with exploit intelligence. Prioritize vulnerabilities with known exploits and high EPSS scores. Alert immediately on new KEV vulnerabilities found in environment.
- **Visualization:** Table (exploitable vulns prioritized), Single value (KEV vulns in environment), Bar chart (EPSS distribution), Scatter plot (severity × EPSS).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.6 · Vulnerability SLA Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** SLA tracking ensures vulnerabilities are remediated within policy timeframes. Non-compliance creates audit findings.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results with detection timestamps, SLA policy lookup
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" state="Active"
| eval age_days=round((now()-first_seen)/86400)
| eval sla_days=case(severity="Critical",7, severity="High",30, severity="Medium",90, 1=1,180)
| eval sla_status=if(age_days>sla_days,"Overdue","Compliant")
| stats count by severity, sla_status
```
- **Implementation:** Define SLA targets per severity. Calculate vulnerability age against SLA. Track compliance percentage. Alert when critical/high vulns approach SLA deadline. Produce compliance reports for audit evidence.
- **Visualization:** Gauge (SLA compliance %), Table (overdue vulnerabilities), Bar chart (compliance by severity), Line chart (compliance trend).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### UC-10.6.7 · New Vulnerability Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Newly discovered critical vulnerabilities require immediate triage. Alerting ensures rapid response to emerging risks.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results (first_seen within last scan window)
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity="Critical"
| where first_seen > relative_time(now(), "-24h")
| table hostname, cve_id, plugin_name, severity, first_seen
| sort -first_seen
```
- **Implementation:** After each scan, identify new critical/high vulnerabilities (first_seen within scan window). Alert immediately on new critical findings. Include CVE details and affected hosts. Integrate with ticketing for automated remediation tracking.
- **Visualization:** Table (new vulnerabilities), Single value (new criticals today), Timeline (discovery events).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Vulnerabilities.Vulnerabilities
  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve
| search Vulnerabilities.severity IN ("critical","high")
| sort -count
```

---

### 10.7 SIEM & SOAR

**Primary App/TA:** Splunk Enterprise Security (Premium), Splunk SOAR (Premium). Internal Splunk metrics (`_internal`, `_audit`).

---

### UC-10.7.1 · Alert Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Alert volume trends reveal SOC workload, detection rule effectiveness, and potential alert fatigue risks.
- **App/TA:** Splunk Enterprise Security
- **Data Sources:** ES notable events (`notable` index)
- **SPL:**
```spl
index=notable
| timechart span=1d count by source
| sort -count
```
- **Implementation:** Track notable event volume from ES over time. Break down by source (correlation search). Identify noisy rules for tuning. Alert when daily volume exceeds analyst capacity thresholds. Report on volume trends.
- **Visualization:** Stacked area (alerts by source), Line chart (total alert volume), Bar chart (top alerting rules).
- **CIM Models:** N/A

---

### UC-10.7.2 · Analyst Workload Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uneven workload distribution leads to analyst burnout and inconsistent response times. Monitoring enables fair distribution.
- **App/TA:** Splunk ES
- **Data Sources:** ES investigation/ownership logs, notable event audit
- **SPL:**
```spl
index=notable
| stats count, avg(time_to_close) as avg_close_time by owner
| sort -count
```
- **Implementation:** Track alert assignment and closure by analyst. Calculate workload distribution and average handling time. Report to SOC management. Identify training needs based on handling time variations.
- **Visualization:** Bar chart (alerts per analyst), Table (workload summary), Pie chart (distribution).
- **CIM Models:** N/A

---

### UC-10.7.3 · MTTD and MTTR Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** MTTD and MTTR are the primary metrics for SOC effectiveness. Tracking drives process improvement and justifies investment.
- **App/TA:** Splunk ES
- **Data Sources:** ES notable events (detection time, response time, closure time)
- **SPL:**
```spl
index=notable status="Closed"
| eval mttd_hours=round((detection_time-event_time)/3600,1)
| eval mttr_hours=round((closure_time-detection_time)/3600,1)
| stats avg(mttd_hours) as avg_mttd, avg(mttr_hours) as avg_mttr, perc95(mttr_hours) as p95_mttr
```
- **Implementation:** Ensure ES workflows capture detection, triage, and resolution timestamps. Calculate MTTD (event to detection) and MTTR (detection to resolution). Track by severity, type, and analyst. Report weekly/monthly to leadership.
- **Visualization:** Single value (avg MTTD/MTTR), Line chart (MTTD/MTTR trends), Bar chart (by incident type), Gauge (vs target).
- **CIM Models:** N/A

---

### UC-10.7.4 · Playbook Execution Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** SOAR playbook failures leave incidents unhandled. Monitoring ensures automation reliability and identifies integration issues.
- **App/TA:** Splunk SOAR
- **Data Sources:** SOAR execution logs, playbook run results
- **SPL:**
```spl
index=soar sourcetype="phantom:playbook_run"
| stats count(eval(status="success")) as success, count(eval(status="failed")) as failed by playbook_name
| eval success_rate=round(success/(success+failed)*100,1)
| where success_rate < 95
```
- **Implementation:** Ingest SOAR execution logs into Splunk. Track playbook success/failure rates. Alert on failures for critical playbooks. Identify failing action steps for debugging. Report on automation coverage and time savings.
- **Visualization:** Table (playbook success rates), Bar chart (failure rate by playbook), Line chart (execution trend), Single value (overall success %).
- **CIM Models:** N/A

---

### UC-10.7.5 · Correlation Search Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow or resource-intensive correlation searches degrade ES performance and may miss detections if they timeout.
- **App/TA:** Splunk internal metrics
- **Data Sources:** `_internal` scheduler logs
- **SPL:**
```spl
index=_internal sourcetype=scheduler savedsearch_name="*Correlation*"
| stats avg(run_time) as avg_runtime, max(run_time) as max_runtime by savedsearch_name
| where avg_runtime > 60
| sort -avg_runtime
```
- **Implementation:** Monitor ES correlation search run times from `_internal`. Alert when searches exceed their schedule interval (running longer than they should). Identify skipped searches. Optimize SPL for slow searches.
- **Visualization:** Table (search performance), Bar chart (avg runtime by search), Line chart (runtime trend), Single value (skipped searches).
- **CIM Models:** N/A

---

### UC-10.7.6 · False Positive Rate Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High false positive rates cause alert fatigue, leading analysts to miss real threats. Tracking drives detection rule optimization.
- **App/TA:** Splunk ES
- **Data Sources:** ES notable events with analyst disposition
- **SPL:**
```spl
index=notable status="Closed"
| stats count(eval(disposition="True Positive")) as tp, count(eval(disposition="False Positive")) as fp by source
| eval fp_rate=round(fp/(tp+fp)*100,1)
| where fp_rate > 30
| sort -fp_rate
```
- **Implementation:** Ensure analysts set dispositions when closing notables (TP, FP, Benign). Calculate FP rate per detection rule. Flag rules with >30% FP rate for tuning. Track overall FP rate as a SOC quality metric. Target <20% FP rate.
- **Visualization:** Bar chart (FP rate by rule), Line chart (overall FP trend), Table (rules needing tuning), Gauge (overall FP rate).
- **CIM Models:** N/A

---

### 10.8 Certificate & PKI Management

**Primary App/TA:** Custom scripted inputs (certificate scanning scripts), CA server log forwarding.

---

### UC-10.8.1 · Certificate Expiry Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Expired certificates cause service outages, authentication failures, and security warnings. Proactive monitoring is the simplest prevention.
- **App/TA:** Custom scripted input
- **Data Sources:** Certificate inventory scans (openssl, certutil, CT logs)
- **SPL:**
```spl
index=certificates sourcetype="cert_inventory"
| eval days_to_expiry=round((cert_not_after_epoch-now())/86400)
| where days_to_expiry < 90
| table cn, san, issuer, days_to_expiry, host, port
| sort days_to_expiry
```
- **Implementation:** Deploy scripted input scanning all known endpoints (HTTPS, LDAPS, SMTPS, etc.) daily. Parse certificate metadata. Alert at 90/60/30/7 day thresholds with escalating severity. Maintain endpoint inventory for comprehensive coverage.
- **Visualization:** Table (certs with expiry countdown), Single value (certs expiring within 30d), Status grid (cert × expiry status), Bar chart (certs by expiry bucket).
- **CIM Models:** N/A

---

### UC-10.8.2 · Certificate Issuance Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Unauthorized certificate issuance from internal CAs can enable man-in-the-middle attacks. Audit trail supports compliance.
- **App/TA:** CA server log forwarding
- **Data Sources:** CA audit logs (Microsoft AD CS, EJBCA, HashiCorp Vault PKI)
- **SPL:**
```spl
index=pki sourcetype="adcs:audit"
| search EventCode=4887
| table _time, RequesterName, CertificateTemplate, SerialNumber, SubjectCN
| sort -_time
```
- **Implementation:** Forward CA server audit logs to Splunk (Event ID 4887 for AD CS). Track all certificate issuance events. Alert on issuance from non-standard templates or by unauthorized requesters. Report on issuance volume and template usage.
- **Visualization:** Table (issued certificates), Timeline (issuance events), Bar chart (by template), Line chart (issuance volume trend).
- **CIM Models:** N/A

---

### UC-10.8.3 · Weak Cipher / Key Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Certificates using weak algorithms (SHA-1, RSA <2048-bit) are vulnerable to attack. Detection ensures cryptographic standards compliance.
- **App/TA:** Custom scripted input
- **Data Sources:** Certificate scan results
- **SPL:**
```spl
index=certificates sourcetype="cert_inventory"
| where key_size < 2048 OR signature_algorithm LIKE "%sha1%" OR signature_algorithm LIKE "%md5%"
| table cn, host, port, key_size, signature_algorithm, issuer
```
- **Implementation:** Include key size and signature algorithm in certificate scans. Flag certificates using SHA-1, MD5, or RSA <2048-bit. Alert on new weak certificates. Track remediation progress as a compliance metric.
- **Visualization:** Table (weak certificates), Pie chart (algorithm distribution), Single value (weak cert count), Bar chart (by weakness type).
- **CIM Models:** N/A

---

### UC-10.8.4 · Certificate Revocation Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Revocation activity indicates compromised or misused certificates. Tracking ensures revocations are processed and CRLs distributed.
- **App/TA:** CA server logs
- **Data Sources:** CA audit logs (revocation events), CRL distribution point monitoring
- **SPL:**
```spl
index=pki sourcetype="adcs:audit" EventCode=4889
| table _time, RequesterName, SerialNumber, RevokeReason, SubjectCN
| sort -_time
```
- **Implementation:** Forward CA revocation events (Event ID 4889). Monitor CRL publication and OCSP responder health. Alert on revocations for investigation. Track revocation reasons for security program improvement.
- **Visualization:** Table (revoked certificates), Timeline (revocation events), Bar chart (revocation reasons).
- **CIM Models:** N/A

---

### UC-10.8.5 · CT Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Certificate Transparency logs reveal all publicly-issued certificates for your domains. Detects unauthorized issuance by rogue or compromised CAs.
- **App/TA:** Custom API input (crt.sh, CT log APIs)
- **Data Sources:** Certificate Transparency log API
- **SPL:**
```spl
index=certificates sourcetype="ct_log"
| search NOT issuer IN ("DigiCert*","Let's Encrypt*","Sectigo*")
| table _time, cn, issuer, serial, not_before, not_after
| sort -_time
```
- **Implementation:** Poll CT log aggregators (crt.sh) for your domains daily. Maintain whitelist of approved issuers. Alert on certificates from unexpected CAs. Track issuance patterns for certificate lifecycle management.
- **Visualization:** Table (CT log entries), Timeline (issuance events), Bar chart (certs by issuer), Single value (unauthorized issuances).
- **CIM Models:** N/A

---

