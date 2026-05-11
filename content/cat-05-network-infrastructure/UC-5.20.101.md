<!-- AUTO-GENERATED from UC-5.20.101.json — DO NOT EDIT -->

---
id: "5.20.101"
title: "SOC 2 Trust Services Criteria — IPv6 Security Control Evidence Collection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.101 · SOC 2 Trust Services Criteria — IPv6 Security Control Evidence Collection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Run &middot; **Status:** Verified

*When accountants come to check that our computer systems are safe and well-managed (a SOC 2 audit), they want proof that we're protecting the network properly. We built a checklist that automatically gathers evidence showing that our security works just as well for the new address system (IPv6) as it does for the old one (IPv4).*

---

## Description

Generates compliance evidence artifacts for SOC 2 Type II audits by mapping IPv6 security controls to Trust Services Criteria (TSC). Covers CC6.1 (logical access), CC6.6 (system boundaries), CC7.1 (detection), CC7.2 (monitoring), A1.2 (availability), and C1.1 (confidentiality). Provides pre-built evidence collection searches that auditors can verify, ensuring IPv6 controls receive the same SOC 2 scrutiny as IPv4.

## Value

SOC 2 audits increasingly examine IPv6 security controls, but many organisations have a blind spot: their SOC 2 evidence only covers IPv4. Auditors may identify this as a control gap, leading to qualified opinions or exceptions. This use case provides a structured framework for collecting and presenting IPv6 evidence mapped directly to TSC criteria, reducing audit preparation time and demonstrating comprehensive security coverage.

## Implementation

Map SOC 2 TSC criteria to IPv6 security controls. Create evidence collection searches for each criteria. Schedule periodic evidence collection. Generate audit-ready reports.

## Detailed Implementation

### Prerequisites
- SOC 2 Type II audit scope defined.
- Firewall, IDS/IPS, and network device logs flowing to Splunk.
- Evidence status tracking lookup (`soc2_evidence_status.csv`).

### Step 1 — Configure evidence tracking

**Create evidence status lookup:**
```csv
tsc,status,last_evidence_date,auditor_notes
"CC6.1 — Logical access: IPv6 firewall rules and ACLs",collected,2026-04-15,"Palo Alto IPv6 rule audit completed"
"CC6.6 — System boundaries: IPv6 network segmentation",collected,2026-04-15,"Segmentation test results attached"
"CC7.1 — Detection: IPv6 IDS/IPS coverage",not_collected,,
"CC7.2 — Monitoring: IPv6 log completeness",collected,2026-03-20,"Log parity analysis completed"
"A1.2 — Availability: IPv6 infrastructure SLA",not_collected,,
"C1.1 — Confidentiality: IPv6 encryption in transit",collected,2026-04-10,"TLS coverage verified"
```

Upload to `$SPLUNK_HOME/etc/apps/<app>/lookups/soc2_evidence_status.csv`.

### Step 2 — Create evidence collection searches

**CC6.1 — IPv6 firewall rule audit:**
```spl
index=network sourcetype="pan:config" earliest=-30d
| spath output=rules path=config.security.rules{}
| mvexpand rules
| spath input=rules
| eval has_ipv6=if(match(source_address, ":" ) OR match(destination_address, ":"), 1, 0)
| stats count as total_rules count(eval(has_ipv6=1)) as ipv6_rules
| eval ipv6_coverage_pct=round(ipv6_rules / total_rules * 100, 1)
| eval evidence="CC6.1: " . ipv6_rules . " of " . total_rules . " firewall rules cover IPv6 (" . ipv6_coverage_pct . "%)"
```

**CC7.2 — IPv6 log parity:**
```spl
index=network earliest=-7d
| eval ip_version=case(
    match(src, ":"), "IPv6",
    match(src, "^\d+\.\d+\.\d+\.\d+"), "IPv4",
    1=1, "Unknown")
| stats count by ip_version, sourcetype
| eval log_fields="src, dest, src_port, dest_port, action, protocol"
| table sourcetype, ip_version, count, log_fields
```

**CC6.6 — IPv6 segmentation test:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") earliest=-30d
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| lookup network_segments.csv src_subnet as src OUTPUT src_segment
| lookup network_segments.csv dest_subnet as dest OUTPUT dest_segment
| where src_segment != dest_segment
| stats count as cross_segment_flows dc(src) as sources dc(dest) as dests by src_segment, dest_segment, action
| eval evidence=case(
    action="denied", "PASS — cross-segment IPv6 traffic correctly blocked",
    action="allowed", "REVIEW — cross-segment IPv6 traffic permitted")
```

### Step 3 — Validate
(a) **Completeness check.** Verify evidence is collected for ALL TSC criteria in scope, not just the easy ones.

(b) **Auditor review.** Present evidence to internal audit or external auditor for preliminary review before the formal audit.

(c) **Gap remediation.** For any criteria where IPv6 evidence is missing or incomplete, implement the missing controls and collect evidence.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — SOC 2 Evidence Dashboard"):
- Row 1 — Single-value: evidence completeness percentage.
- Row 2 — Table: TSC criteria with status and freshness.
- Row 3 — Detail panels: per-criteria evidence results.
- Row 4 — Action items: criteria with missing or stale evidence.

**Scheduled report:** Quarterly. Send to compliance team with evidence artifacts.

**Audit preparation checklist:**
1. Run all evidence collection searches.
2. Export results as PDF/CSV for auditor evidence binder.
3. Update evidence status lookup with collection date.
4. Review auditor notes from previous audit and address any findings.

### Step 5 — Troubleshooting

- **Evidence gaps.** If a TSC criteria has no IPv6 evidence, it likely means the control doesn't exist for IPv6. This is a finding, not a data problem. Implement the control, then collect evidence.

- **Log parity issues.** If IPv6 logs have fewer fields than IPv4 (e.g., missing source port), the logging infrastructure needs to be updated to capture IPv6 with the same fidelity. See UC-5.20.94 (RFC 6302 source port logging).

- **Cloud-inherited controls.** For cloud deployments, map which IPv6 controls are inherited from the provider (e.g., AWS NACLs, Azure NSGs) vs customer-managed (e.g., application firewall rules). Document the shared responsibility boundary.

## SPL

```spl
| makeresults
| eval tsc=mvappend(
    "CC6.1 — Logical access: IPv6 firewall rules and ACLs",
    "CC6.6 — System boundaries: IPv6 network segmentation",
    "CC7.1 — Detection: IPv6 IDS/IPS coverage",
    "CC7.2 — Monitoring: IPv6 log completeness",
    "A1.2 — Availability: IPv6 infrastructure SLA",
    "C1.1 — Confidentiality: IPv6 encryption in transit")
| mvexpand tsc
| eval evidence_search=case(
    match(tsc, "CC6.1"), "index=network sourcetype=pan:config \"ipv6\" | stats count by policy_name",
    match(tsc, "CC6.6"), "index=network sourcetype=pan:traffic \"ipv6\" action=\"allowed\" | lookup cde_subnets.csv dest | where is_cde=\"yes\"",
    match(tsc, "CC7.1"), "index=network sourcetype=suricata:alert \"ipv6\" | stats dc(alert_signature) as ipv6_sigs",
    match(tsc, "CC7.2"), "index=network | eval v6=if(match(src,\":\"),1,0) | stats count(eval(v6=1)) as ipv6_events count as total",
    match(tsc, "A1.2"), "index=network sourcetype=cisco:ios \"ipv6\" \"down\" OR \"up\" | stats count by host",
    match(tsc, "C1.1"), "index=network sourcetype=pan:traffic \"ipv6\" app=\"ssl\" OR app=\"ipsec\" | stats count by app")
| lookup soc2_evidence_status.csv tsc OUTPUT status last_evidence_date auditor_notes
| eval status=coalesce(status, "NOT COLLECTED")
| table tsc, status, last_evidence_date, evidence_search, auditor_notes
```

## Visualization

(1) Table: TSC criteria with evidence status (collected/not collected/stale). (2) Single-value: evidence collection completeness percentage. (3) Timeline: evidence freshness. (4) Detail panels: per-criteria evidence with search results.

## Known False Positives

**Evidence staleness.** Evidence older than the audit period (typically 12 months for Type II) may be flagged as stale. Schedule quarterly evidence collection.

**Partial evidence.** Some criteria require multiple evidence types (configuration + logs + testing). Ensure all evidence dimensions are collected, not just log counts.

**Inherited controls.** In cloud environments, some IPv6 controls may be inherited from the cloud provider (e.g., AWS VPC security groups). Document inherited vs customer-managed controls.

## References

- [AICPA — SOC 2 Trust Services Criteria (2017)](https://www.aicpa.org/content/dam/aicpa/interestareas/frc/assuranceadvisoryservices/downloadabledocuments/trust-services-criteria.pdf)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks](https://www.rfc-editor.org/rfc/rfc9099)
