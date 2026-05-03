<!-- AUTO-GENERATED from UC-5.2.3.json — DO NOT EDIT -->

---
id: "5.2.3"
title: "Threat Detection Events"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.3 · Threat Detection Events

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We catch serious threat alerts on the firewall early so the team can stop malicious traffic before it reaches important systems.*

---

## Description

IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.

## Value

Security teams analyze multi-vendor firewall threat/IPS events by severity and enforcement action, prioritizing unblocked critical threats targeting internal assets.

## Implementation

Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.

## Detailed Implementation

### Prerequisites
* Firewall threat/IPS logs in `index=firewall`. Sourcetypes: Palo Alto `pan:threat`, Fortinet `fgt_utm`, Cisco FTD `cisco:firepower:syslog`, Juniper SRX `juniper:junos:idp`. Key fields: `threat_name`/`attack`/`signature`, `severity`, `action` (alert/block/drop/reset), `src_ip`, `dest_ip`, `category`.
* Threat detection engines: Palo Alto Threat Prevention (vulnerability protection, anti-spyware, antivirus), Fortinet IPS/AV/Application Control, Cisco Snort/IPS, Juniper IDP.

### Step 1 — - Configure data collection
**Palo Alto:**
```
# Objects > Security Profiles > Anti-Spyware, Vulnerability Protection
# Attach profiles to security policies
# Device > Log Settings > Threat: forward via syslog
```
Verify:
```spl
index=firewall (sourcetype="pan:threat" OR sourcetype="fgt_utm" OR sourcetype="cisco:firepower:syslog" type="IPS") earliest=-4h
| stats count by sourcetype, severity
```

### Step 2 — - Create the search and alert

**Primary search -- Threat detection event analysis:**
```spl
index=firewall (sourcetype="pan:threat" OR sourcetype="fgt_utm" OR sourcetype="cisco:firepower:syslog" OR sourcetype="juniper:junos:idp") earliest=-4h
| eval threat=coalesce(threat_name, attack, signature, attack_name)
| eval sev=lower(coalesce(severity, threat_severity))
| eval act=lower(coalesce(action, policy_action))
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| eval cat=coalesce(category, threat_category, attack_category)
| stats count as hits dc(src) as unique_sources dc(dst) as unique_targets values(act) as actions by threat, sev, cat
| eval blocked=if(match(mvjoin(actions, ","), "(?i)block|drop|reset|deny"), "YES", "ALERT ONLY")
| eval severity_rank=case(sev="critical", 1, sev="high", 2, sev="medium", 3, 1==1, 4)
| sort severity_rank, -hits
```

**High-severity threats targeting internal assets:**
```spl
index=firewall (sourcetype="pan:threat" OR sourcetype="fgt_utm" OR sourcetype="cisco:firepower:syslog") earliest=-4h
| eval sev=lower(coalesce(severity, threat_severity))
| where sev="critical" OR sev="high"
| eval dst=coalesce(dest_ip, dest)
| eval threat=coalesce(threat_name, attack, signature)
| eval act=lower(coalesce(action, policy_action))
| stats count as hits values(threat) as threats values(act) as actions by dst
| where match(dst, "^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)")
| sort -hits
```

### Step 3 — - Validate
(a) Compare threat events with firewall threat log viewer (Panorama Monitor > Logs > Threat, FMC Analysis > Intrusion Events).
(b) Trigger a test signature (e.g., EICAR antivirus test) and verify it appears.
(c) Verify action mapping: `alert-only` means the threat was detected but not blocked -- these require investigation.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Threat Detection"):
* Row 1 -- Single-value: "Critical threats", "High threats", "Blocked %", "Alert-only threats".
* Row 2 -- Threat events by severity and category.
* Row 3 -- Internal assets targeted by high-severity threats.

Alerting:
* Critical (critical-severity threat targeting internal asset): immediate investigation.
* High (high-severity with action=alert-only): threat detected but NOT blocked.
* Warning (new threat signature with > 10 hits): emerging threat.

### Step 5 — - Troubleshooting

* **Threat detected but not blocked (alert-only)** -- Security profile is in detect mode, not prevent. Change to blocking: Palo Alto: set action to "reset-both" in Vulnerability/Anti-Spyware profile. Fortinet: set IPS action to "block" instead of "monitor".

* **No threat events at all** -- Check: (1) threat prevention license is active, (2) security profiles are attached to firewall policies, (3) signature databases are up to date. Run: `show system info` (PA) or `get system performance status` (Fortinet).

* **High false positive rate on specific signature** -- Create an exception for the specific signature + source/dest pair. Document the exception with justification.

## SPL

```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src, dest, threat_name, severity, action | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Table (source, dest, threat, action), Bar chart by threat type, Map.

## Known False Positives

Authorized vulnerability scanners (Tenable, Qualys, Rapid7) and security tests trigger many threat signatures by design.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
