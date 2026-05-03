<!-- AUTO-GENERATED from UC-5.2.15.json — DO NOT EDIT -->

---
id: "5.2.15"
title: "Botnet/C2 Traffic Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.15 · Botnet/C2 Traffic Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We look for command-and-control style matches so we can stop callbacks and bot traffic that slip past simple allow lists.*

---

## Description

Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.

## Value

Security teams identify internal hosts communicating with known botnet/C2 servers, prioritizing unblocked C2 traffic and detecting beaconing patterns indicative of active compromise.

## Implementation

Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.

## Detailed Implementation

### Prerequisites
* Firewall threat/traffic logs with botnet/C2 indicators. Palo Alto: `sourcetype=pan:threat` (spyware/C2 detection), Fortinet: `sourcetype=fgt_utm` (botnet detection), Cisco FTD: Security Intelligence events. Key fields: `threat_name`, `category` (command-and-control/spyware/botnet), `action`, `src_ip` (internal compromised host), `dest_ip` (C2 server).
* C2 detection methods: (1) DNS-based (queries to known C2 domains), (2) URL-based (HTTP/HTTPS to C2 URLs), (3) IP-based (connections to known C2 IPs), (4) behavioral (periodic beaconing patterns).

### Step 1 — - Configure data collection
**Palo Alto:**
```
# Objects > Security Profiles > Anti-Spyware > configure DNS Sinkhole
# DNS Sinkhole redirects C2 DNS queries to a sinkhole IP, identifying infected hosts
# Enable botnet report: Monitor > Botnet
```
Verify:
```spl
index=firewall earliest=-24h
| where match(_raw, "(?i)botnet|command.and.control|c2|spyware|sinkhole|beacon")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Botnet/C2 traffic detection:**
```spl
index=firewall earliest=-24h
| where match(_raw, "(?i)botnet|command.and.control|spyware|sinkhole|C2|beacon") OR match(category, "(?i)command-and-control|spyware|botnet")
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| eval threat=coalesce(threat_name, attack, signature)
| eval act=lower(coalesce(action, policy_action))
| eval c2_type=case(match(_raw, "(?i)sinkhole|dns.*sinkhole"), "DNS_SINKHOLE", match(_raw, "(?i)dns.*C2|dns.*command"), "DNS_C2_QUERY", match(_raw, "(?i)http.*C2|url.*C2"), "HTTP_C2", match(_raw, "(?i)beacon"), "BEACONING", 1==1, "C2_GENERIC")
| stats count as events dc(dst) as unique_c2_servers values(threat) as threats values(c2_type) as detection_methods latest(_time) as last_seen by src, act
| eval blocked=if(match(act, "(?i)block|drop|deny|sinkhole|reset"), "YES", "ALERT ONLY -- INVESTIGATE")
| eval severity=case(blocked="ALERT ONLY -- INVESTIGATE", "CRITICAL -- C2 traffic NOT blocked", events > 100, "HIGH -- frequent C2 attempts", unique_c2_servers > 5, "HIGH -- host contacting multiple C2 servers", 1==1, "WARNING")
| sort severity, -events
```

**Beaconing detection:**
```spl
index=firewall earliest=-24h
| eval src=coalesce(src_ip, src)
| eval dst=coalesce(dest_ip, dest)
| where match(category, "(?i)command-and-control|spyware|suspicious")
| bin _time span=5m
| stats count as events by _time, src, dst
| eventstats stdev(events) as stdev_events avg(events) as avg_events by src, dst
| where stdev_events < 1 AND avg_events > 0.5
| stats count as regular_intervals dc(dst) as c2_candidates by src
| where regular_intervals > 20
```

### Step 3 — - Validate
(a) Palo Alto: Monitor > Botnet report -- shows suspected botnet hosts.
(b) Test DNS sinkhole: resolve a known malicious domain and verify sinkhole response.
(c) Cross-reference detected C2 IPs with threat intelligence feeds.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Botnet/C2 Detection"):
* Row 1 -- Single-value: "Compromised hosts", "C2 connections (24h)", "Unblocked C2", "Unique C2 servers".
* Row 2 -- Compromised host table with C2 details.
* Row 3 -- Beaconing pattern analysis.

Alerting:
* Critical (C2 traffic not blocked): compromised host actively communicating with attacker.
* High (host contacting multiple C2 servers): multi-stage infection or botnet enrollment.

### Step 5 — - Troubleshooting

* **DNS sinkhole showing internal IPs** -- These are the infected hosts. Investigate each: (1) isolate from network, (2) run full AV/EDR scan, (3) check for lateral movement.

* **C2 detected but action=alert** -- Security profile in detect mode. Change to block mode for C2/spyware categories. DNS sinkhole is preferred for DNS-based C2 as it identifies the infected host.

* **False positive on C2 detection** -- Some legitimate services use patterns similar to C2 (e.g., update checkers, heartbeat services). Verify with threat intelligence before whitelisting. Create an exception only after confirming benign.

## SPL

```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest) as c2_targets dc(dest) as unique_c2 by src
| sort -count
| lookup dnslookup clientip as src OUTPUT clienthost as src_hostname
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

Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).

## Known False Positives

Misclassified benign apps, software updates, and cloud service overlap can look like command-and-control until triaged.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
