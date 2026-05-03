<!-- AUTO-GENERATED from UC-5.20.78.json — DO NOT EDIT -->

---
id: "5.20.78"
title: "IPv6 Logging and Monitoring Parity Audit"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.78 · IPv6 Logging and Monitoring Parity Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We have security cameras (monitoring) watching the old entrance (IPv4). Now we've added a new entrance (IPv6), and we need to make sure every camera and security measure that protects the old entrance also protects the new one. We check each security feature one by one: 'Does this camera also watch the new door? Does this alarm system also cover the new entrance?' We score ourselves on how many security features cover both entrances equally.*

---

## Description

Audits the parity between IPv4 and IPv6 monitoring coverage across all monitoring capabilities — flow data, firewall logging, IDS/IPS, DLP, SIEM rules, syslog, NDP/ARP, and DNS. Every monitoring capability that exists for IPv4 should have an equivalent for IPv6. This audit identifies monitoring blind spots where IPv6 traffic is not inspected, logged, or analysed with the same depth as IPv4 traffic.

## Value

Monitoring parity is the single most important requirement for IPv6 security. If IPv6 traffic is not monitored with the same tools, rules, and depth as IPv4 traffic, attackers will use IPv6 to bypass detection. This audit quantifies the monitoring gap and provides a prioritised remediation list. The goal is 100% monitoring parity — every monitoring capability that works for IPv4 must also work for IPv6.

## Implementation

Create a monitoring capabilities inventory. For each capability, verify IPv6 support is active. Calculate parity score. Prioritise gaps by security impact. Report monthly.

## Detailed Implementation

### Prerequisites
- Inventory of all monitoring capabilities (flow, firewall, IDS, DLP, SIEM rules, syslog, DNS, etc.).
- Knowledge of each capability's IPv6 support status.
- Ability to test IPv6 monitoring coverage.

### Step 1 — Configure data collection

**Create monitoring capabilities inventory:**
```csv
capability,category,ipv4_active,ipv6_active,ipv6_notes,priority
NetFlow/IPFIX flow export,Flow Data,yes,partial,Some exporters still on v5,critical
Firewall ACL deny logging,Firewall,yes,yes,IPv6 ACL logging enabled,critical
IDS/IPS signature matching,Security,yes,partial,Limited IPv6 extension header inspection,critical
DLP content inspection,Security,yes,no,DLP rules use IPv4 regex only,high
SIEM correlation rules,SIEM,yes,partial,50% of rules IPv4-specific regex,critical
Syslog collection,Logging,yes,yes,All devices forward IPv6 events,high
ARP/NDP cache monitoring,L2 Security,yes,no,ARP monitoring active but no NDP monitoring,high
DNS query logging,DNS,yes,yes,AAAA queries logged,medium
Geo-IP blocking,Security,yes,no,Geo-blocking applied to IPv4 only,high
Rate limiting,Availability,yes,partial,Some rate limits IPv4-only,medium
```
Upload as `monitoring_capabilities.csv`.

**Automated parity verification searches:**

**Flow data parity check:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval has_ipv6=if(isnotnull(sourceIPv6Address) OR match(src, ":"), 1, 0)
| stats count(eval(has_ipv6=1)) as v6_flows count(eval(has_ipv6=0)) as v4_flows by exporter_ip
| where v6_flows=0
| eval gap="Flow exporter " . exporter_ip . " has zero IPv6 flows — monitoring parity gap"
```

**SIEM rule IPv4-only regex check:**
```spl
| rest /services/saved/searches
| where match(search, "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}") AND NOT match(search, "[0-9a-fA-F]{1,4}:")
| eval gap="Saved search '" . title . "' uses IPv4 regex but no IPv6 pattern"
| table title, gap
```
This identifies SIEM correlation rules that match IPv4 addresses but have no IPv6 address patterns.

**Verification:**
```spl
| inputlookup monitoring_capabilities.csv
| stats count(eval(ipv6_active="yes")) as full_parity count(eval(ipv6_active="partial")) as partial count(eval(ipv6_active="no")) as no_coverage
```

### Step 2 — Create the dashboard

**Overall parity score:**
```spl
| inputlookup monitoring_capabilities.csv
| eval score=case(ipv6_active="yes", 2, ipv6_active="partial", 1, ipv6_active="no", 0)
| eval max_score=2
| stats sum(score) as achieved sum(max_score) as possible
| eval parity_pct=round(achieved / possible * 100, 0)
```

**Gap prioritisation:**
```spl
| inputlookup monitoring_capabilities.csv
| where ipv6_active != "yes"
| eval priority_order=case(priority="critical", 1, priority="high", 2, priority="medium", 3, 1=1, 4)
| sort priority_order
| table capability, category, ipv4_active, ipv6_active, ipv6_notes, priority
```

### Step 3 — Validate
(a) **Coverage test.** Generate known IPv6 traffic (a specific port/protocol combination). Verify each monitoring capability detects it. Update the lookup with results.

(b) **Red team validation.** Use THC-IPv6 or equivalent to generate IPv6 attack traffic. Verify IDS/IPS detects it. Update the lookup.

(c) **SIEM rule review.** Review all SIEM correlation rules for IPv4-specific patterns. Update each rule to include IPv6 patterns.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Monitoring Parity"):
- Row 1 — Single-value: overall parity score (target: 100%).
- Row 2 — Table: all capabilities with IPv4/IPv6 status, colour-coded.
- Row 3 — Priority list: gaps sorted by criticality.
- Row 4 — Trend: parity score over 12 months.

**Scheduling:** Automated parity checks weekly. Manual assessment quarterly. Executive report monthly.

**Runbook:**
1. Critical gap (DLP, IDS, SIEM rules): immediate remediation. Update DLP patterns and IDS signatures for IPv6. Rewrite SIEM rules with dual-stack patterns.
2. High gap (geo-blocking, NDP monitoring): plan remediation within 30 days. Deploy NDP monitoring (UC-5.20.19 through UC-5.20.28). Apply geo-blocking to IPv6 (UC-5.20.69).
3. Medium gap: plan remediation within 90 days.

### Step 5 — Troubleshooting

- **'Partial' assessments** — Many capabilities have partial IPv6 support. Document exactly what works and what doesn't. For example, IDS may support IPv6 header inspection but not extension header inspection.

- **Vendor IPv6 support** — Contact monitoring tool vendors for their IPv6 capability matrix. Some vendors claim IPv6 support but have significant limitations.

- **Testing methodology** — Use a structured test matrix: generate known IPv6 traffic for each monitoring capability and verify detection. Tools like THC-IPv6, Scapy, and nmap support IPv6 test traffic generation.

## SPL

```spl
| inputlookup monitoring_capabilities.csv
| eval ipv4_coverage=if(ipv4_active="yes", 1, 0)
| eval ipv6_coverage=if(ipv6_active="yes", 1, 0)
| eval parity=if(ipv4_coverage=ipv6_coverage, "PARITY", "GAP")
| stats count(eval(parity="PARITY")) as parity_met count(eval(parity="GAP")) as parity_gaps count as total
| eval parity_score=round(parity_met / total * 100, 0) . "%"
| eval status=case(
    parity_met = total, "FULL PARITY — IPv6 monitoring matches IPv4",
    parity_gaps <= 2, "NEAR PARITY — " . parity_gaps . " gaps remaining",
    1=1, "SIGNIFICANT GAPS — " . parity_gaps . " monitoring capabilities lack IPv6 coverage")
```

## Visualization

(1) Single-value: monitoring parity score (target: 100%). (2) Table: all capabilities with IPv4/IPv6 status and parity indicator. (3) Priority list: monitoring gaps sorted by security impact. (4) Trend: parity score improvement over time.

## Known False Positives

**Intentionally IPv4-only segments.** Some network segments are intentionally IPv4-only (legacy systems, air-gapped networks). IPv6 monitoring is not needed for these segments and should be excluded from the parity calculation.

**Platform limitations.** Some older monitoring platforms genuinely cannot support IPv6. Document these as accepted risks with a migration plan rather than permanent gaps.

**IPv6-specific monitoring.** Some monitoring capabilities are IPv6-specific (NDP cache monitoring, RA Guard, SISF) and have no IPv4 equivalent. These should be counted as additional IPv6 coverage, not parity gaps.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — monitoring requirements)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§5.3 — monitoring equivalence)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
