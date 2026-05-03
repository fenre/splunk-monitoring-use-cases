<!-- AUTO-GENERATED from UC-5.2.41.json — DO NOT EDIT -->

---
id: "5.2.41"
title: "Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.41 · Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count intrusion and prevention hits on the SRX so serious signatures rise above everyday noise and get staff attention in order.*

---

## Description

Juniper SRX runs an integrated IDP/IPS engine with signature-based and protocol-anomaly detection alongside firewall state. Because events are generated in the same flow path as security policy, logs carry application context, zones, and session identifiers that standalone IPS appliances often lack. Monitoring attack name, severity, destination service, and enforcement action (drop, close, ignore) lets you prioritize true positives, spot targeted attacks, and prove that prevention is working without waiting for incident tickets.

## Value

SOC teams monitor Juniper SRX IDP/IPS events by severity and action, prioritizing critical unblocked intrusion attempts for immediate investigation and response.

## Implementation

Enable IDP on applicable SRX policies and send IDP logs to Splunk (structured syslog preferred). Install and enable the Juniper TA for field extraction. Build alerts for `sev` in (critical, high) or for rapid growth in `hits` against the same `dest_ip`/service. Correlate with allow/deny traffic logs on the same five-tuple. Add suppressions for known vulnerability scanners after a baseline window. Validate CIM `Intrusion_Detection` tags if you accelerate the data model.

## Detailed Implementation

### Prerequisites
* Juniper SRX IDP/IPS event logs forwarded to Splunk. Data in `index=juniper` or `index=firewall` with `sourcetype=juniper:srx:idp` or `sourcetype=juniper:srx:structured`. The Juniper SRX TA (Splunk_TA_juniper) parses structured syslog from SRX. Key fields: `attack_name`, `severity`, `source_address`, `destination_address`, `source_port`, `destination_port`, `protocol_name`, `action` (drop/close/alert).
* Juniper SRX IDP: integrated IDS/IPS engine. Policies are defined under `security idp` stanza. Signature database is updated from Juniper security intelligence feeds. Modes: `idp-policy` attached to firewall rules, or standalone. Supports custom signatures and protocol anomaly detection.

### Step 1 — - Configure data collection
```
# SRX configuration -- enable IDP event logging
set security idp idp-policy my-idp-policy rulebase-ips rule rule1 then notification log-attacks
set security idp idp-policy my-idp-policy rulebase-ips rule rule1 then notification alert
set security log mode stream
set security log stream splunk-stream host <splunk-syslog-ip>
set security log stream splunk-stream port 514
set security log stream splunk-stream format sd-syslog
set security log stream splunk-stream severity info
set security log stream splunk-stream category idp

# Splunk inputs.conf
[udp://514]
sourcetype = juniper:srx:structured
index = juniper
```
Verify:
```spl
index=juniper sourcetype="juniper:srx:idp" earliest=-4h
| stats count by attack_name, severity, action
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- IDP/IPS event severity analysis:**
```spl
index=juniper sourcetype="juniper:srx:idp" earliest=-4h
| eval src=coalesce(source_address, src_ip, src)
| eval dst=coalesce(destination_address, dest_ip, dst)
| eval attack=coalesce(attack_name, message_type, signature)
| eval sev=lower(coalesce(severity, threat_severity))
| eval act=lower(coalesce(action, idp_action))
| eval blocked=if(match(act, "(?i)drop|close|reset|reject"), "YES", "NO")
| stats count as hits dc(src) as unique_sources dc(dst) as unique_targets values(act) as actions by attack, sev, blocked
| eval severity_rank=case(sev="critical", 1, sev="major", 2, sev="minor", 3, 1==1, 4)
| eval alert_level=case(
    sev="critical" AND blocked="NO", "CRITICAL -- critical IDP alert NOT blocked",
    sev="critical", "HIGH -- critical IDP alert (blocked)",
    sev="major" AND blocked="NO", "HIGH -- major IDP alert NOT blocked",
    sev="major" AND hits > 10, "WARNING -- repeated major IDP alerts",
    1==1, "INFO")
| where alert_level != "INFO"
| sort severity_rank, -hits
```

### Step 3 — - Validate
(a) CLI: `show security idp status` -- verify IDP engine is running and signature DB is current.
(b) CLI: `show security idp counters` -- check packet processing stats.
(c) Test: run a known exploit against a test server and verify detection.

### Step 4 — - Operationalize
Dashboard ("Juniper SRX -- IDP/IPS Events"):
* Row 1 -- Single-value: "Critical alerts", "Attacks blocked", "Unique attack sources".
* Row 2 -- Attack timeline by severity.
* Row 3 -- Top attacks table with source/destination details.

Alert: Critical (critical-severity IDP event with action=alert only, not dropped): immediate SOC investigation.

### Step 5 — - Troubleshooting

* **IDP signature database outdated** -- Run `request security idp security-package download` and `request security idp security-package install`. Schedule automatic updates via `set security idp security-package automatic`.

* **High false positive rate** -- Review attack signatures. Use `set security idp idp-policy ... rulebase-ips rule ... match attacks custom-attacks` to create exemptions. Switch noisy signatures from DROP to ALERT for observation.

* **IDP not inspecting traffic** -- Verify IDP policy is attached to the correct firewall policy: `set security policies from-zone untrust to-zone trust policy p1 then permit application-services idp-policy my-idp-policy`. Check that the IDP engine has sufficient memory.

## SPL

```spl
index=network (sourcetype="juniper:junos:idp" OR sourcetype="juniper:junos:idp:structured")
| eval attack=coalesce(attack_name, signature, threat_name, idp_attack_name)
| eval sev=lower(coalesce(severity, threat_severity, idp_severity))
| eval act=coalesce(action, idp_action, policy_action)
| eval src_ip=coalesce(src, src_ip, srcaddr)
| eval dest_ip=coalesce(dest, dest_ip, dstaddr)
| stats count as hits by host attack sev act src_ip dest_ip dest_port service
| sort -hits
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

Table (attack, severity, action, endpoints), Bar chart (top signatures), Timeline (bursts by host).

## Known False Positives

IDP false positives, scanner traffic, and new apps can raise signatures until you tune and whitelist known noise.

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
