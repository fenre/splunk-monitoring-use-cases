<!-- AUTO-GENERATED from UC-5.3.8.json — DO NOT EDIT -->

---
id: "5.3.8"
title: "WAF Policy Violations (F5 BIG-IP ASM)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.8 · WAF Policy Violations (F5 BIG-IP ASM)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We add up web application blocks on the same box so real attacks and risky paths stand out from everyday browsing noise with less guesswork.*

---

## Description

WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

## Value

Security teams analyze F5 BIG-IP ASM/Advanced WAF policy violations by attack type, severity, and enforcement action, identifying unblocked critical attacks and top threat sources for policy tuning.

## Implementation

Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.

## Detailed Implementation

### Prerequisites
* F5 BIG-IP ASM (Application Security Manager) / Advanced WAF logs forwarded to Splunk. Data in `index=network` with `sourcetype=f5:bigip:asm:syslog` or `sourcetype=f5:bigip:asm:request`. Key fields: `violations`, `severity`, `attack_type`, `sig_name`, `request_url`, `source_ip`, `response_code`, `policy_name`, `action` (blocked/alarmed/passed).
* F5 ASM remote logging: Security > Event Logs > Logging Profiles > create profile > enable Remote Storage to Splunk syslog or use HSL (High Speed Logging) to a Splunk pool.

### Step 1 — - Configure data collection
Configure ASM remote logging:
```
tmsh create security log profile splunk_asm application add { asm_logging { remote-storage splunk servers add { <splunk_ip>:<port> } filter { request-type illegal-including-staged-signatures } } }
tmsh modify ltm virtual <vs> security-log-profiles add { splunk_asm }
```

Verify:
```spl
index=network (sourcetype="f5:bigip:asm:syslog" OR sourcetype="f5:bigip:asm:request") earliest=-4h
| stats count by attack_type, action
```

### Step 2 — - Create the search and alert

**Primary search -- WAF violation analysis:**
```spl
index=network (sourcetype="f5:bigip:asm:syslog" OR sourcetype="f5:bigip:asm:request") earliest=-4h
| eval attack=coalesce(attack_type, violation_type, sig_name)
| eval action_taken=coalesce(action, enforcement_action)
| stats count as violations dc(source_ip) as unique_sources values(request_url) as target_urls by attack, action_taken, policy_name, severity
| eval risk=case(severity="Critical" AND action_taken="blocked", "HIGH -- blocked critical attack", severity="Critical" AND action_taken!="blocked", "CRITICAL -- critical attack NOT blocked", action_taken="alarmed" AND violations > 50, "WARNING -- high volume alarm only", 1==1, "INFO")
| sort risk, -violations
```

**Top attack sources:**
```spl
index=network (sourcetype="f5:bigip:asm:syslog" OR sourcetype="f5:bigip:asm:request") earliest=-4h
| eval attack=coalesce(attack_type, violation_type)
| stats count as violations dc(attack) as attack_types values(attack) as attacks by source_ip
| where violations > 10
| sort -violations
| head 20
```

### Step 3 — - Validate
(a) Send a test XSS payload to a protected VIP and verify the violation appears in Splunk.
(b) Compare violation counts with F5 ASM: Security > Event Logs > Application > Requests.
(c) Verify that "blocked" vs "alarmed" actions align with the ASM policy mode (blocking vs transparent).

### Step 4 — - Operationalize
Dashboard ("F5 ASM -- WAF Violations"):
* Row 1 -- Single-value: "Total violations", "Blocked attacks", "Critical unblocked", "Unique attackers".
* Row 2 -- Attack type breakdown with action and severity.
* Row 3 -- Top attacker IP addresses.

Alerting:
* Critical (critical severity violation NOT blocked): policy may be in transparent mode -- review.
* High (> 100 violations from single IP in 15 min): targeted attack -- consider blocking IP.
* Warning (new attack type seen): review and tune policy.

### Step 5 — - Troubleshooting

* **High false positive rate** -- ASM policy may be too strict. Review violations in F5: Security > Application Security > Traffic Learning. Accept legitimate learning suggestions to reduce false positives.

* **Violations show "alarmed" not "blocked"** -- ASM policy is in Transparent mode. To enforce: Security > Application Security > Policy > General Settings > Enforcement Mode: Blocking.

* **No ASM data in Splunk** -- Check: (1) logging profile is attached to the virtual server, (2) remote storage destination is correct, (3) HSL pool members are up.

## SPL

```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
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

Table, Bar chart by violation, Map (source IPs), Timeline.

## Known False Positives

Scanners, pen tests, and legacy browser quirks can make a web application firewall look busy; tune rules and test traffic.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
