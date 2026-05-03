<!-- AUTO-GENERATED from UC-5.3.11.json — DO NOT EDIT -->

---
id: "5.3.11"
title: "Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.11 · Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly

*We catch rate limit and attack style events on the same appliance so a honest flash crowd and a real flood are both visible for the right follow-up.*

---

## Description

Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.

## Value

Security teams monitor F5 BIG-IP AFM rate limiting and DDoS mitigation events across network, DNS, and application layers, tracking attack vectors, mitigation effectiveness, and peak attack rates.

## Implementation

Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.

## Detailed Implementation

### Prerequisites
* F5 BIG-IP AFM (Advanced Firewall Manager) or LTM with DoS/DDoS protection profiles. Data in `index=network` with `sourcetype=f5:bigip:afm:syslog` or `sourcetype=f5:bigip:syslog`. Key fields: `attack_type`, `source_ip`, `action` (drop/rate-limit/allow), `packets_per_sec`, `connections_per_sec`, `virtual_server`, `dos_profile`.
* F5 DoS protection includes: (1) Network-level DoS (SYN flood, UDP flood, ICMP flood), (2) DNS DoS (query flood, NXDOMAIN attack), (3) Application-level DoS (HTTP flood, slowloris), (4) Behavioral DoS (machine-learning-based anomaly detection).

### Step 1 — - Configure data collection
Enable AFM/DoS logging:
```
tmsh create security log profile splunk_dos dos-application add { app_dos { remote-storage splunk servers add { <splunk_ip>:<port> } } } dos-network-publisher local-db-publisher
tmsh modify ltm virtual <vs> security-log-profiles add { splunk_dos }
```

Verify:
```spl
index=network (sourcetype="f5:bigip:afm:syslog" OR sourcetype="f5:bigip:syslog") ("rate" OR "limit" OR "dos" OR "flood" OR "attack" OR "mitigat") earliest=-24h
| stats count by attack_type, action
```

### Step 2 — - Create the search and alert

**Primary search -- DDoS mitigation event analysis:**
```spl
index=network (sourcetype="f5:bigip:afm:syslog" OR sourcetype="f5:bigip:syslog") ("dos" OR "flood" OR "attack" OR "rate.limit" OR "mitigat" OR "behavioral") earliest=-4h
| eval attack=coalesce(attack_type, dos_attack_name, threat_type)
| eval act=coalesce(action, enforcement_action)
| eval vs=coalesce(virtual_server, virtual_name)
| eval rate=coalesce(packets_per_sec, connections_per_sec, request_rate)
| eval attack_layer=case(match(attack, "(?i)(syn|udp|icmp|tcp).*flood"), "L3/L4 Network DoS", match(attack, "(?i)(dns|query|nxdomain)"), "DNS DoS", match(attack, "(?i)(http|slowloris|slow.post|request)"), "L7 Application DoS", match(attack, "(?i)(behavioral|anomaly)"), "Behavioral DoS", 1==1, "Other")
| stats count as events sum(eval(if(act="drop" OR act="rate-limit", 1, 0))) as mitigated dc(source_ip) as unique_sources max(rate) as peak_rate by attack_layer, attack, vs
| eval mitigation_pct=if(events > 0, round(100*mitigated/events, 1), 0)
| sort attack_layer, -events
```

### Step 3 — - Validate
(a) Compare mitigation events with F5 Security Dashboard: Security > Reporting > DoS.
(b) During a controlled test (with authorization), generate a SYN flood and verify it appears.
(c) Verify behavioral DoS baselines are established (F5 needs learning time).

### Step 4 — - Operationalize
Dashboard ("F5 -- DDoS Protection"):
* Row 1 -- Single-value: "Active attacks", "Events mitigated", "Peak rate (pps)", "Unique sources".
* Row 2 -- Attack breakdown by layer with mitigation percentage.

Alerting:
* Critical (L3/L4 flood > 10000 pps): volumetric DDoS -- may require upstream mitigation.
* High (L7 behavioral DoS detected): application-layer attack.
* Warning (rate limiting active on prod VIP): traffic being dropped.

### Step 5 — - Troubleshooting

* **Legitimate traffic being rate-limited** -- DoS thresholds may be too aggressive. Review: Security > DoS Protection > Application > Detection. Increase thresholds or switch behavioral DoS to "Transparent" mode to learn before blocking.

* **No behavioral DoS events** -- Behavioral DoS needs a learning period (typically 24-48 hours of normal traffic). Check: `tmsh show security dos application <vs> behavioral`.

* **Attack mitigated but users still impacted** -- The volumetric attack may be saturating the network link before reaching the F5. Consider upstream DDoS mitigation (ISP scrubbing, cloud DDoS service).

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src) as src_values dc(src) as unique_sources by virtual_server, attack_type
| sort -count
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

Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).

## Known False Positives

Rate-based blocks and shapers can add events during real peaks and during pen tests; confirm intent before relaxing controls.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
