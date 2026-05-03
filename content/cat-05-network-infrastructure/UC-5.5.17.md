<!-- AUTO-GENERATED from UC-5.5.17.json — DO NOT EDIT -->

---
id: "5.5.17"
title: "Security Policy Violations (UTD)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.5.17 · Security Policy Violations (UTD)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

SD-WAN edges running Unified Threat Defense (UTD) perform IPS, URL filtering, and AMP inline. Monitoring these events at the WAN edge catches threats that bypass centralized firewalls, especially for direct internet access (DIA) traffic that never traverses the data center.

## Value

Security operations teams detect and analyze SD-WAN UTD security policy violations including IPS/IDS alerts, URL filtering blocks, and malware detections to identify threats traversing the WAN fabric and validate security policy enforcement.

## Implementation

Enable UTD (IPS/URL filtering/AMP) on SD-WAN edges handling DIA traffic. Collect security events via vManage. Alert on critical/high severity IPS signatures and malware detections. Correlate with Umbrella/Secure Access if deployed for layered defense. Track blocked URL categories to refine acceptable-use policies.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for UTD (Unified Threat Defense) security events. Data in `index=sdwan` with `sourcetype=cisco:sdwan:utd` or `sourcetype=cisco:sdwan:security`. Key fields: `site_id`, `system_ip`, `action` (permit/deny/drop/alert), `threat_type` (intrusion/malware/url-filtering), `src_ip`, `dest_ip`, `dest_port`, `signature_id`, `signature_name`, `severity`, `url_category`, `file_name`, `file_hash`.
- UTD is the security stack embedded in SD-WAN edge devices: IPS/IDS (Snort-based), URL filtering (Talos categories), DNS security, and Advanced Malware Protection (AMP). Security policy violations indicate: attempted attacks, policy-violating user behavior, or misconfigured security rules.
- Build `sdwan_security_policies.csv` lookup: `url_category,action,business_justification` (e.g., `malware,block,Mandatory`, `social-networking,alert,Acceptable use`, `gambling,block,Policy violation`).

### Step 1 — Configure data collection
Verify UTD security events:
```spl
index=sdwan (sourcetype="cisco:sdwan:utd" OR sourcetype="cisco:sdwan:security") earliest=-1h
| stats count by threat_type, action, severity
```

### Step 2 — Create the search and alert

**Primary search — Security policy violations by severity:**
```spl
index=sdwan (sourcetype="cisco:sdwan:utd" OR sourcetype="cisco:sdwan:security") earliest=-1h
| where action IN ("deny", "drop", "alert")
| stats count as violations dc(src_ip) as unique_sources dc(dest_ip) as unique_destinations values(signature_name) as signatures by site_id, threat_type, severity, action
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval priority=case(severity="critical" AND action="alert", "CRITICAL_NOT_BLOCKED", severity="critical", "CRITICAL", severity="high", "HIGH", severity="medium", "MEDIUM", 1==1, "LOW")
| where priority IN ("CRITICAL_NOT_BLOCKED", "CRITICAL", "HIGH")
| sort priority, -violations
```

#### Understanding this SPL: The most dangerous finding is "CRITICAL_NOT_BLOCKED" — a critical severity event that was only alerted on, not blocked. This means the security policy is in detection mode for a critical threat, or the signature matched but the policy action was "alert" instead of "drop." These require immediate security policy review.

**Top attack sources and targets:**
```spl
index=sdwan (sourcetype="cisco:sdwan:utd" OR sourcetype="cisco:sdwan:security") action IN ("deny", "drop") earliest=-4h
| stats count as attacks dc(signature_id) as unique_sigs values(threat_type) as threat_types by src_ip, dest_ip
| eval direction=case(cidrmatch("10.0.0.0/8", src_ip) OR cidrmatch("172.16.0.0/12", src_ip) OR cidrmatch("192.168.0.0/16", src_ip), "OUTBOUND", 1==1, "INBOUND")
| sort -attacks
| head 20
```

**URL filtering violations by category:**
```spl
index=sdwan (sourcetype="cisco:sdwan:utd" OR sourcetype="cisco:sdwan:security") threat_type="url-filtering" earliest=-24h
| stats count as hits dc(src_ip) as users by url_category, action
| lookup sdwan_security_policies.csv url_category OUTPUT business_justification
| sort -hits
```

**Malware detection events:**
```spl
index=sdwan (sourcetype="cisco:sdwan:utd" OR sourcetype="cisco:sdwan:security") threat_type="malware" earliest=-24h
| stats count as detections by site_id, src_ip, file_name, file_hash, action
| lookup sdwan_sites.csv site_id OUTPUT site_name
| sort -detections
```

### Step 3 — Validate
(a) In vManage: Monitor > Security. Compare UTD event counts and categories with Splunk results.
(b) Trigger a test IPS signature (e.g., EICAR test file) and verify it appears in Splunk.
(c) Verify URL filtering: attempt to access a known-blocked category and confirm the event logs.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Security Policy"):
- Row 1 — Single-value tiles: "Critical events (1h)", "Blocked attacks", "URL violations", "Malware detections".
- Row 2 — Security events by severity and type: table with drill-down.
- Row 3 — Top attack sources and targets: table with direction (inbound/outbound).
- Row 4 — URL filtering category breakdown: bar chart.
- Row 5 — Malware detection details: file name, hash, action, affected site.

Alerting:
- Critical (critical severity event in alert-only mode): security gap — the threat was detected but not blocked.
- Critical (malware detection): endpoint may be compromised — investigate immediately.
- High (> 100 IPS events from single source in 1 hour): possible attack — investigate source.
- Warning (URL policy violation trending upward): policy awareness training needed.

### Step 5 — Troubleshooting

- **UTD events not appearing** — UTD may not be enabled on the device template. Check vManage: Configuration > Templates > Security Policy. Also verify that the UTD container is running on the device: `show utd engine standard status`.

- **All events showing action=alert, none blocked** — The security policy may be in detection-only mode (IPS in "detect" mode vs. "prevent" mode). Check the security policy configuration in vManage.

- **High false positive rate on IPS** — Tune IPS signatures: disable signatures that trigger on legitimate traffic, or adjust the policy to alert (not block) on medium-severity signatures while blocking high/critical.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:utd"
| stats count by event_type, signature, severity, src_ip, dst_ip, site_id
| where severity IN ("critical","high")
| sort -count
| table event_type signature severity src_ip dst_ip site_id count
```

## Visualization

Table (signature, severity, source, destination), Bar chart (events by category), Timeline (event frequency).

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
