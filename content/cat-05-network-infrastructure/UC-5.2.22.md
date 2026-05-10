<!-- AUTO-GENERATED from UC-5.2.22.json — DO NOT EDIT -->

---
id: "5.2.22"
title: "Malware Detection and AMP File Reputation Events (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.22 · Malware Detection and AMP File Reputation Events (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We follow malware and reputation flags from the same edge so the team can quarantine a bad file before it moves deeper inside.*

---

## Description

Detects and tracks file-based threats to respond quickly to potential malware infections.

## Value

Security teams monitor Meraki MX AMP file reputation events, prioritizing retrospective malware alerts where previously allowed files are reclassified as malicious.

## Implementation

Enable AMP on MX appliance. Ingest malware detection events.

## Detailed Implementation

### Prerequisites
* Meraki MX Advanced Malware Protection (AMP) events via syslog. Data in `index=meraki` with `sourcetype=meraki`. Key fields: `file_hash`, `file_name`, `disposition` (clean/malicious/unknown), `action` (allow/block), `src`, `dest`, `file_type`.
* Meraki AMP: MX appliances use Cisco AMP cloud file reputation to check downloaded files against a known threat database. Files are checked by SHA-256 hash. Retrospective alerts notify when a previously clean file is later reclassified as malicious.

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Threat protection
# Advanced Malware Protection: Enabled
# Syslog > Roles: Security events
```
Verify:
```spl
index=meraki sourcetype="meraki" earliest=-24h
| where match(_raw, "(?i)malware|amp|file.*reputation|file.*disposition|file.*hash")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- Malware detection and AMP events:**
```spl
index=meraki sourcetype="meraki" earliest=-24h
| where match(_raw, "(?i)malware|amp|file.*reputation|file.*block|malicious")
| eval disposition=lower(coalesce(disposition, file_disposition))
| eval file=coalesce(file_name, filename)
| eval hash=coalesce(file_hash, sha256)
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip)
| eval event_type=case(match(_raw, "(?i)retrospective|reclassif"), "RETROSPECTIVE -- previously clean file now malicious", disposition="malicious" AND match(action, "(?i)block"), "BLOCKED_MALWARE", disposition="malicious" AND NOT match(action, "(?i)block"), "DETECTED_NOT_BLOCKED", 1==1, "AMP_EVENT")
| stats count as events dc(hash) as unique_hashes values(file) as filenames by event_type, src
| eval severity=case(event_type="RETROSPECTIVE", "CRITICAL -- retrospective malware (file was allowed, now known malicious)", match(event_type, "NOT_BLOCKED"), "CRITICAL -- malware detected but not blocked", match(event_type, "BLOCKED"), "HIGH -- malware blocked", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Threat protection > AMP section.
(b) Download the EICAR test file through the MX and verify blocking/detection.
(c) Check for retrospective alerts in Dashboard.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Malware Detection"):
* Row 1 -- Single-value: "Malware blocked", "Retrospective alerts", "Unique malware hashes".
* Row 2 -- Malware event table.

Alerting:
* Critical (retrospective alert): a file that was allowed is now confirmed malicious -- investigate all hosts that downloaded it.
* Critical (malware detected not blocked): AMP may be in monitor mode.

### Step 5 — - Troubleshooting

* **Retrospective malware alert** -- A file previously classified as clean was reclassified. Action: (1) identify all hosts that downloaded the file (search by hash), (2) run endpoint AV/EDR scan on affected hosts, (3) check if file was executed.

* **AMP not blocking malware** -- Check: (1) AMP is enabled in Security & SD-WAN settings, (2) mode is set to block (not just detect), (3) HTTPS inspection is enabled (required for AMP to inspect HTTPS downloads).

* **No AMP events** -- Verify: (1) AMP license is active, (2) traffic flows through MX, (3) file types being downloaded are supported for AMP inspection.

## SPL

```spl
index=meraki sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src, threat_name, file_name
| where malware_count > 0
| sort - malware_count
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

Threat timeline; infected hosts table; file reputation detail; incident dashboard.

## Known False Positives

Quarantine, cleanup tools, and rescanning the same file can repeat malware events without a new infection.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
