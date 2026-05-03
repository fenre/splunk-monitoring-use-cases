<!-- AUTO-GENERATED from UC-5.20.116.json — DO NOT EDIT -->

---
id: "5.20.116"
title: "IPv6 Dual-Stack Monitoring Parity Audit"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.116 · IPv6 Dual-Stack Monitoring Parity Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We have security cameras, alarm systems, and visitor logs that watch everything coming and going through the old address system (IPv4). We need to make sure we have the exact same security cameras and alarm systems watching the new address system (IPv6). This tool checks every security system to make sure IPv6 isn't a blind spot — because burglars will always go through the unwatched door.*

---

## Description

Audits monitoring parity between IPv4 and IPv6 across all sourcetypes in Splunk. Identifies sourcetypes with significant IPv4 traffic but little or no IPv6 representation, indicating monitoring blind spots where IPv6 traffic flows unlogged. RFC 9099 §2.6 requires that IPv6 monitoring be at least as comprehensive as IPv4.

## Value

The most dangerous IPv6 vulnerability is not a protocol flaw — it's the monitoring gap. Organisations deploy IPv6 but continue monitoring only IPv4, creating a shadow network that attackers can exploit with impunity. This UC systematically identifies every sourcetype where IPv6 monitoring falls short of IPv4, providing a roadmap for achieving monitoring parity. Without parity, every other IPv6 security control is undermined because attacks go undetected.

## Implementation

Compare IPv6 vs IPv4 event volumes across all sourcetypes. Identify sourcetypes with IPv4 traffic but no IPv6. Generate a parity remediation report.

## Detailed Implementation

### Prerequisites
- Dual-stack network deployment.
- Multiple sourcetypes in Splunk covering different monitoring domains.

### Step 1 — Establish baseline

Run the main SPL search to identify all sourcetypes with parity gaps. This creates the initial remediation backlog.

**Detailed parity analysis by monitoring domain:**
```spl
| makeresults
| eval domain=mvappend(
    "Firewall logging (paloalto:traffic, cisco:asa, cisco:ftd)",
    "Flow data (netflow, sflow, ipfix)",
    "IDS/IPS (suricata:alert, snort:alert, zeek:notice)",
    "Network device syslog (cisco:ios, juniper:junos)",
    "DNS (zeek:dns, named:querylog)",
    "Web server (access_combined, iis)",
    "Authentication (cisco:ise, radius)",
    "SNMP (snmp:trap, snmp:interface)")
| mvexpand domain
| eval expected_ipv6="yes"
| eval actual_ipv6="check manually"
| table domain, expected_ipv6, actual_ipv6
```

### Step 2 — Deep-dive per sourcetype

**Firewall parity (most critical):**
```spl
index=network sourcetype="paloalto:traffic" earliest=-24h
| eval ip_ver=case(
    match(src, ":") OR match(dest, ":"), "IPv6",
    match(src, "^\d+\."), "IPv4",
    1=1, "Unknown")
| stats count as events dc(src) as unique_sources dc(dest) as unique_dests by ip_ver
| eval total_events=events
| eval pct=round(events / sum(events) * 100, 1)
```

**Flow data parity:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval ip_ver=if(match(src, ":") OR match(dest, ":"), "IPv6", "IPv4")
| stats sum(bytes) as total_bytes count as flows by ip_ver
| eval pct=round(flows / sum(flows) * 100, 1)
```

### Step 3 — Validate
(a) **Generate IPv6 traffic.** From a test host, generate known IPv6 traffic (HTTP, DNS, SSH). Verify each sourcetype captures the IPv6 events with full field fidelity.

(b) **Field fidelity check.** For each sourcetype, verify that IPv6 events have the same fields as IPv4 events (src, dest, port, protocol, action, bytes).

(c) **Synthetic test.** If synthetic monitoring is IPv4-only, add IPv6 synthetic tests for each monitored service.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Monitoring Parity"):
- Row 1 — Single-values: sourcetypes with zero IPv6, total parity gap count.
- Row 2 — Table: sourcetypes sorted by IPv6 percentage.
- Row 3 — Bar chart: IPv6 percentage by sourcetype.
- Row 4 — Trend: parity improvement over time (weekly snapshots).

**Scheduled report:** Monthly. Send to security team with remediation priorities.

**Remediation priorities:**
1. Firewall logging (most critical — security inspection).
2. Flow data (traffic analysis and forensics).
3. IDS/IPS (attack detection).
4. DNS (IPv6 resolution monitoring).
5. Authentication (user attribution).
6. Web server logs (application monitoring).
7. SNMP (infrastructure monitoring).

### Step 5 — Troubleshooting

- **Firewall not logging IPv6.** Verify firewall policies include IPv6 address objects. Some firewalls require separate IPv6 rules or 'any' rules that explicitly include IPv6.

- **NetFlow missing IPv6 templates.** Verify the NetFlow exporter is configured to export IPv6 templates. On Cisco IOS: `flow exporter EXPORT / ip flow-export version 9 / ip flow-export template ipv6`. See UC-5.20.58.

- **Web server log format.** Some web servers truncate IPv6 addresses in logs. Verify the log format supports full IPv6 addresses (128-bit). Apache: use `%a` or `%{REMOTE_ADDR}e`.

## SPL

```spl
index=* earliest=-24h
| eval has_ipv6_src=if(match(src, ":"), 1, 0)
| eval has_ipv4_src=if(match(src, "^\d+\.\d+\.\d+\.\d+$"), 1, 0)
| stats count as total count(eval(has_ipv6_src=1)) as ipv6_events count(eval(has_ipv4_src=1)) as ipv4_events by sourcetype
| eval ipv6_pct=round(ipv6_events / max(total, 1) * 100, 1)
| eval parity_status=case(
    ipv6_events=0 AND ipv4_events > 1000, "NO IPv6 — this sourcetype has zero IPv6 events despite significant IPv4 volume",
    ipv6_pct < 1 AND ipv4_events > 1000, "MINIMAL IPv6 — only " . ipv6_pct . "% IPv6 (expected >10% in dual-stack environment)",
    ipv6_pct < 10 AND ipv4_events > 1000, "LOW IPv6 — " . ipv6_pct . "% IPv6 (investigate possible logging gap)",
    1=1, "OK — " . ipv6_pct . "% IPv6")
| where ipv4_events > 1000 AND ipv6_pct < 10
| sort ipv6_pct
| table sourcetype, total, ipv4_events, ipv6_events, ipv6_pct, parity_status
```

## Visualization

(1) Table: sourcetypes with parity status. (2) Bar chart: IPv6 percentage by sourcetype. (3) Single-value: sourcetypes with zero IPv6 (the gap count). (4) Trend: parity improvement over time.

## Known False Positives

**IPv4-only sourcetypes.** Some sourcetypes are inherently IPv4-only (e.g., legacy mainframe, SCADA protocols). These should be documented and excluded from parity calculations.

**Infrastructure-only IPv6.** If IPv6 is only deployed on infrastructure (routers, switches) but not on user segments, user-facing sourcetypes will correctly show low IPv6 percentages.

**Regional deployment.** If IPv6 is deployed in some regions but not others, aggregated parity numbers may be misleading. Segment the analysis by region.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — Monitoring)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§6 — monitoring)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
