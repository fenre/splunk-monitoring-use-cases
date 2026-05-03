<!-- AUTO-GENERATED from UC-5.2.21.json — DO NOT EDIT -->

---
id: "5.2.21"
title: "IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.21 · IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We add up intrusion system alerts on small office gear so the team can tell real break-in attempts from normal internet noise faster.*

---

## Description

Identifies and prioritizes intrusion detection alerts for investigation and threat response.

## Value

Security teams analyze Meraki MX IDS/IPS alerts with threat scoring, prioritizing high-priority detection-only alerts where threats are logged but not blocked.

## Implementation

Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.

## Detailed Implementation

### Prerequisites
* Meraki MX IDS/IPS events via syslog or API. Data in `index=meraki` with `sourcetype=meraki:events` (syslog). Key fields: `signature`, `priority` (1=high, 2=medium, 3=low), `action` (block/alert), `src`, `dest`, `protocol`.
* Meraki MX uses Snort-based IDS/IPS (Sourcefire). In "Prevention" mode, MX blocks threats. In "Detection" mode, threats are logged but not blocked. Ruleset modes: Connectivity, Balanced, Security (increasing strictness).

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Threat protection
# Mode: Prevention (recommended)
# Ruleset: Balanced or Security
# Syslog > Roles: IDS alerts
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)ids.*alert|intrusion|snort|signature|threat.*detect")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- IDS/IPS alert analysis with threat scoring:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)ids.*alert|intrusion|snort|signature")
| eval signature=coalesce(signature, message, alert_name)
| eval priority=tonumber(coalesce(priority, severity))
| eval act=lower(coalesce(action, disposition))
| eval src=coalesce(src, src_ip, srcaddr)
| eval dst=coalesce(dest, dest_ip, dstaddr)
| eval threat_score=case(priority=1, 10, priority=2, 5, priority=3, 2, 1==1, 1)
| eval is_blocked=if(match(act, "(?i)block|drop|prevent"), 1, 0)
| stats count as alerts sum(threat_score) as total_score sum(is_blocked) as blocked dc(src) as unique_sources dc(dst) as unique_targets by signature, priority
| eval detection_only=alerts - blocked
| eval severity=case(priority=1 AND detection_only > 0, "CRITICAL -- high-priority threat NOT blocked", priority=1, "HIGH -- high-priority threat (blocked)", total_score > 100, "WARNING -- high aggregate threat score", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -total_score
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Threat protection -- check IDS events.
(b) Trigger a test signature (EICAR through HTTP) and verify the alert.
(c) Verify mode: if "Detection", alerts are logged but traffic is NOT blocked.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- IDS/IPS"):
* Row 1 -- Single-value: "High-priority alerts", "Total alerts", "Detection-only alerts", "Threat score".
* Row 2 -- Alert breakdown by priority and action.
* Row 3 -- Top threat signatures.

Alerting:
* Critical (high-priority alert not blocked): IPS in detection mode for this threat.
* High (high-priority alert blocked): threat detected and prevented.

### Step 5 — - Troubleshooting

* **Alerts in detection mode** -- Switch to "Prevention" mode in Dashboard > Security & SD-WAN > Threat protection. Note: this may block false positives.

* **High false positive rate** -- Adjust ruleset from "Security" to "Balanced" or "Connectivity". Whitelist specific signatures for known safe traffic.

* **No IDS alerts** -- Check: (1) Threat protection is enabled, (2) mode is not set to "Off", (3) syslog is configured with IDS role, (4) traffic is flowing through the MX.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src, dest
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
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

Alert timeline; severity breakdown pie chart; alert detail table; threat map.

## Known False Positives

Vulnerability scans, security tools, and mis-segmented lab traffic can raise IDS rates without a live intrusion.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
