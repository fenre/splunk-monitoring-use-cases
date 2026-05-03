<!-- AUTO-GENERATED from UC-5.20.77.json — DO NOT EDIT -->

---
id: "5.20.77"
title: "NIST SP 800-119 IPv6 Deployment Compliance Dashboard"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.77 · NIST SP 800-119 IPv6 Deployment Compliance Dashboard

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*The government has published a list of safety rules for the new building system (IPv6). We have a big checklist on the wall showing which rules we follow and which ones we still need to work on. The score tells the building inspector how safe our building is — if we pass all the rules, we get an A grade. If we're missing important safety features, we need to fix them before the next inspection.*

---

## Description

Provides a consolidated compliance dashboard for NIST Special Publication 800-119 'Guidelines for the Secure Deployment of IPv6.' The dashboard aggregates results from multiple IPv6 use cases (bogon filtering, RA Guard coverage, flow monitoring, firewall parity, EUI-64 detection, tunnel detection, and logging parity) into a single compliance score. Each NIST requirement maps to one or more dedicated use cases that perform the detailed compliance check.

## Value

NIST SP 800-119 compliance is required for US federal agencies (FISMA) and is widely adopted as a best-practice standard by enterprise organisations. Without a consolidated view, tracking compliance across the many individual NIST requirements is fragmented and labour-intensive. This dashboard provides executive visibility into overall IPv6 security posture and identifies specific areas requiring remediation.

## Implementation

Create a compliance lookup table mapping each NIST SP 800-119 requirement to its corresponding use case and pass/fail status. Populate the lookup via scheduled searches from individual compliance use cases. Display aggregated results in a compliance dashboard.

## Detailed Implementation

### Prerequisites
- Individual IPv6 compliance use cases deployed and generating results.
- Compliance lookup table (`nist_800_119_status.csv`) created and maintained.
- Understanding of organisational scope for NIST SP 800-119 applicability.

### Step 1 — Configure data collection

**Create the compliance requirements lookup:**
```csv
requirement,uc_reference,check_description,status,last_checked,evidence,criticality
1. IPv6 device inventory,UC-5.20.4,Complete inventory of IPv6-enabled devices,pending,,Passive discovery via NDP and flow data,high
2. IPv6 address plan,UC-5.20.8,Documented IPv6 address plan with prefix assignments,pending,,IPAM plan compliance audit,medium
3. Bogon filtering,UC-5.20.63,Block all IPv6 bogon prefixes at perimeter,pending,,Bogon prefix-list deployed and verified,high
4. ICMPv6 essential permits,UC-5.20.37/UC-5.20.64,Permit ICMPv6 Types 1-4 and 133-137 per RFC 4890,pending,,Firewall rule audit results,critical
5. RA Guard coverage,UC-5.20.29/UC-5.20.36,RA Guard on all access switch ports,pending,,FHS coverage gap audit results,critical
6. IPv6 flow monitoring,UC-5.20.66,All exporters sending IPv6 flow records,pending,,NetFlow/IPFIX template validation,high
7. Firewall parity,UC-5.20.61/UC-5.20.64,IPv6 firewall rules equivalent to IPv4,pending,,ACL parity check results,critical
8. No EUI-64 addresses,UC-5.20.13,RFC 8064 compliant — no EUI-64 IIDs in active use,pending,,EUI-64 address scan results,medium
9. Tunnel detection,UC-5.20.57,No unauthorized 6to4 or Teredo tunnels,pending,,Tunnel protocol detection results,high
10. Logging parity,UC-5.20.66,IPv6 syslog and IPFIX coverage matches IPv4,pending,,Exporter and syslog coverage audit,high
11. NDP security,UC-5.20.32/UC-5.20.72,SISF/FHS protecting against NDP attacks,pending,,SISF deployment and event analysis,high
12. DHCPv6 security,UC-5.20.30,DHCPv6 Guard on access ports,pending,,DHCPv6 Guard coverage audit,high
13. Routing security,UC-5.20.49,RPKI ROV for IPv6 BGP,pending,,RPKI status and invalid route count,medium
14. Anti-spoofing,UC-5.20.63,uRPF or equivalent for IPv6 source validation,pending,,uRPF status per interface,high
```
Upload as `nist_800_119_status.csv`.

**Automated status update searches:**
Create scheduled searches that update the compliance lookup based on individual UC results:
```spl
| search [search index=network sourcetype="cisco:ios" "%SISF" OR "%RA_GUARD" earliest=-7d | stats count | where count > 0 | eval search="*" | fields search]
| stats count as sisf_events
| eval ra_guard_status=if(sisf_events > 0, "pass", "fail")
| outputlookup append=true nist_800_119_status.csv where requirement="5. RA Guard coverage"
```
Repeat for each requirement, mapping to the corresponding UC results.

**Verification:**
```spl
| inputlookup nist_800_119_status.csv
| stats count(eval(status="pass")) as passed count(eval(status="fail")) as failed count(eval(status="pending")) as pending
```

### Step 2 — Create the dashboard

**Overall compliance score:**
```spl
| inputlookup nist_800_119_status.csv
| stats count(eval(status="pass")) as passed count as total
| eval score=round(passed / total * 100, 0)
| eval grade=case(
    score >= 90, "A",
    score >= 80, "B",
    score >= 70, "C",
    score >= 60, "D",
    1=1, "F")
```

**Failing requirements prioritised:**
```spl
| inputlookup nist_800_119_status.csv
| where status="fail" OR status="pending"
| eval priority_order=case(
    criticality="critical", 1,
    criticality="high", 2,
    criticality="medium", 3,
    1=1, 4)
| sort priority_order
| table requirement, criticality, status, uc_reference, check_description, evidence
```

### Step 3 — Validate
(a) **Score accuracy.** Manually verify 3-5 requirements against their individual UC results to ensure the lookup accurately reflects current status.

(b) **Auto-update.** Verify scheduled searches correctly update the lookup after individual UC results change.

(c) **Coverage.** Verify all major NIST SP 800-119 requirements are represented in the lookup.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NIST SP 800-119 Compliance"):
- Row 1 — Single-value: overall compliance score and grade. Gauge: 90-day trend.
- Row 2 — Table: all requirements with status, colour-coded (green=pass, red=fail, grey=pending).
- Row 3 — Priority list: failing/pending requirements sorted by criticality.
- Row 4 — Evidence links: drilldown from each requirement to the detailed UC dashboard.

**Scheduling:** Compliance dashboard refreshes hourly. Individual UC checks per their own schedules. Executive report monthly.

**Runbook:**
1. Score below 70%: executive escalation. Prioritise critical and high-criticality failures.
2. Individual requirement failure: drill into the referenced UC dashboard for detailed remediation guidance.
3. Pending requirements: schedule the individual UC assessment. Do not leave requirements in 'pending' state.

### Step 5 — Troubleshooting

- **Lookup synchronisation** — The compliance lookup is updated by multiple scheduled searches. Ensure they do not overwrite each other. Use `outputlookup append=true` with specific filters.

- **Scope definition** — Define which network segments are in-scope for NIST SP 800-119 compliance. Out-of-scope segments should be documented, not ignored.

- **Audit trail** — Maintain historical compliance scores by appending timestamped results to a summary index. This provides the trend data for the 90-day gauge.

## SPL

```spl
| makeresults
| eval requirement=mvappend(
    "1. IPv6 device inventory",
    "2. IPv6 address plan documented",
    "3. Bogon filtering at perimeter",
    "4. ICMPv6 essential types permitted",
    "5. RA Guard on access ports",
    "6. IPv6 flow monitoring active",
    "7. IPv6 firewall rules parity",
    "8. No EUI-64 addresses in use",
    "9. Unauthorized tunnel detection",
    "10. IPv6 logging parity")
| mvexpand requirement
| lookup nist_800_119_status.csv requirement OUTPUT status, last_checked, evidence
| eval compliant=if(status="pass", 1, 0)
| eventstats sum(compliant) as passed count as total
| eval overall_score=round(passed / total * 100, 0) . "%"
| table requirement, status, last_checked, evidence, overall_score
```

## Visualization

(1) Single-value: overall NIST SP 800-119 compliance score (percentage). (2) Table: requirement-by-requirement status with pass/fail and evidence. (3) Gauge: compliance trend over 90 days. (4) Priority list: failing requirements sorted by criticality.

## Known False Positives

**Partial compliance.** Some requirements have multiple sub-requirements. A requirement may show as 'fail' when one sub-component is non-compliant even though most are.

**Assessment timing.** Individual compliance checks run on different schedules. The dashboard shows the most recent result for each requirement, which may be hours or days old.

**Scope exclusions.** Some network segments may be intentionally excluded from IPv6 (air-gapped, legacy). These exclusions should be documented and reflected in the compliance lookup.

## References

- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks](https://www.rfc-editor.org/rfc/rfc9099)
