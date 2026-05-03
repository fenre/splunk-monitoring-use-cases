<!-- AUTO-GENERATED from UC-5.2.18.json — DO NOT EDIT -->

---
id: "5.2.18"
title: "Threat Prevention Signature Coverage"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.18 · Threat Prevention Signature Coverage

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We track when threat and content packs update on the firewall so you know the box is on a current brain, not a stale one.*

---

## Description

Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.

## Value

Security teams track firewall threat prevention signature update freshness across all devices, detecting stale databases and failed updates that leave the network exposed to new threats.

## Implementation

Forward system logs. Alert when signature updates are >7 days old. Compare across firewalls to detect update failures. Schedule weekly compliance reports.

## Detailed Implementation

### Prerequisites
* Firewall threat prevention logs and signature database version information. Key data: signature update timestamps, threat prevention signature coverage, vulnerability signatures applied, anti-spyware signatures active.
* Threat prevention coverage gaps: (1) outdated signature databases, (2) signatures in detect-only mode, (3) critical signatures disabled by exceptions, (4) signature categories not enabled.

### Step 1 — - Configure data collection
**Palo Alto:**
```
show system info | match content  # shows content version and update time
show system info | match threat    # threat signature version
request content upgrade check      # check for updates
```
Verify:
```spl
index=firewall earliest=-7d
| where match(_raw, "(?i)content.*update|signature.*update|threat.*update|av.*update|antivirus.*update|database.*update")
| stats count latest(_time) as last_update by host
| eval days_since_update=round((now()-last_update)/86400, 1)
```

### Step 2 — - Create the search and alert

**Primary search -- Signature coverage and update status:**
```spl
index=firewall earliest=-7d
| where match(_raw, "(?i)content.*update|signature.*update|threat.*update|av.*update|database.*update|dynamic.*update")
| eval update_type=case(match(_raw, "(?i)threat|ips|vulnerability"), "THREAT_PREVENTION", match(_raw, "(?i)antivirus|av"), "ANTIVIRUS", match(_raw, "(?i)wildfire|sandbox"), "WILDFIRE", match(_raw, "(?i)url|pandb|fortiguard"), "URL_DATABASE", match(_raw, "(?i)app.*id|application"), "APP_SIGNATURES", 1==1, "OTHER")
| eval update_status=case(match(_raw, "(?i)success|complete|installed"), "SUCCESS", match(_raw, "(?i)fail|error|timeout"), "FAILURE", match(_raw, "(?i)download|checking|start"), "IN_PROGRESS", 1==1, "UNKNOWN")
| stats latest(_time) as last_update values(update_status) as statuses by host, update_type
| eval days_since_update=round((now()-last_update)/86400, 1)
| eval severity=case(match(mvjoin(statuses, ","), "FAILURE"), "CRITICAL -- update failed", days_since_update > 7, "HIGH -- signatures >7 days old", days_since_update > 3, "WARNING -- signatures >3 days old", 1==1, "OK")
| where severity != "OK"
| table host, update_type, days_since_update, statuses, last_update, severity
| sort severity, -days_since_update
```

### Step 3 — - Validate
(a) Palo Alto: Device > Dynamic Updates -- shows last update time and version.
(b) Fortinet: `get system auto-update status` -- shows FortiGuard update status.
(c) Compare signature version with vendor's latest published version.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Threat Signature Coverage"):
* Row 1 -- Single-value: "Outdated firewalls", "Failed updates", "Avg days since update".
* Row 2 -- Signature update status per firewall.

Alerting:
* Critical (update failed): signatures not updating -- new threats unprotected.
* High (signatures > 7 days old): investigate update mechanism.
* Warning (signatures > 3 days old): may miss latest threats.

### Step 5 — - Troubleshooting

* **Update failures** -- Check: (1) internet connectivity from firewall management plane, (2) DNS resolution for update servers (updates.paloaltonetworks.com, update.fortiguard.net), (3) proxy configuration for updates, (4) support/maintenance license is valid.

* **Signatures old despite scheduled updates** -- Verify: (1) automatic update schedule is configured, (2) update download completes but install fails, (3) disk space on firewall for content packages.

* **Specific signature disabled** -- Security exceptions may have disabled critical signatures. Audit: PA `show running security-profile` to list active signatures and exceptions.

## SPL

```spl
index=network sourcetype="pan:system" "threat version" OR "content update"
| rex "installed (?<content_type>threats|antivirus|wildfire) version (?<version>\S+)"
| stats latest(version) as current_version, latest(_time) as last_update by dvc, content_type
| eval days_since_update=round((now()-last_update)/86400,0)
| where days_since_update > 7
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (firewall, content type, version, days since update), Single value (outdated count).

## Known False Positives

Regular vendor content and signature updates are expected; they should not be confused with on-box edits.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
