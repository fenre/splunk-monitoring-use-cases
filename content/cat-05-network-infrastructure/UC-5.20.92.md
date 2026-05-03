<!-- AUTO-GENERATED from UC-5.20.92.json — DO NOT EDIT -->

---
id: "5.20.92"
title: "PCI DSS 4.0 IPv6 Network Segmentation Validation"
status: "verified"
criticality: "critical"
splunkPillar: "ES"
---

# UC-5.20.92 · PCI DSS 4.0 IPv6 Network Segmentation Validation

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*Payment card data is stored in a secure vault (CDE) with strict access rules about who can enter. The old access rules (IPv4 firewall) work perfectly. But if the vault has a new entrance (IPv6) with no rules at all, anyone can walk in through the new door. We check that the new entrance has exactly the same locks and access rules as the old one.*

---

## Description

Validates that PCI DSS 4.0 network segmentation controls are equally effective for IPv6 as they are for IPv4. The most critical PCI DSS IPv6 gap: if firewall rules isolating the Cardholder Data Environment (CDE) are IPv4-only, IPv6 creates a direct bypass path to cardholder data. PCI DSS 4.0 Requirements 1.2.3, 1.3.1, 10.2.1, and 11.4.5 all have implicit IPv6 requirements that are frequently overlooked during QSA assessments.

## Value

A PCI DSS segmentation failure is a critical finding that can result in expanded audit scope (every system becomes in-scope) and potential compromise of cardholder data. IPv6 segmentation bypass is one of the most commonly missed PCI DSS vulnerabilities because QSA assessments often focus exclusively on IPv4 firewall rules. This monitoring provides continuous segmentation validation for IPv6, satisfying Requirement 11.4.5's semi-annual verification requirement.

## Implementation

Define CDE subnets and approved source subnets in lookup tables. Monitor firewall logs for any IPv6 traffic reaching CDE from unapproved sources. Alert on segmentation bypass. Provide evidence for PCI DSS audit.

## Detailed Implementation

### Prerequisites
- Documented CDE network boundaries (subnets, VLANs).
- Documented approved access sources for the CDE.
- Firewall log data with IPv6 visibility.
- Understanding of PCI DSS 4.0 segmentation requirements.

### Step 1 — Configure data collection

**Create CDE subnet lookup:**
```csv
dest_subnet,is_cde,description
10.10.0.0/16,yes,CDE IPv4 subnet
2001:db8:cde::/48,yes,CDE IPv6 subnet (if intentionally deployed)
```
Upload as `cde_subnets.csv`.

**Create approved sources lookup:**
```csv
src_subnet,approved,description
10.20.0.0/24,yes,POS terminal subnet
10.30.0.0/24,yes,Payment processing servers
2001:db8:pos::/48,yes,POS IPv6 subnet (if applicable)
```
Upload as `cde_approved_sources.csv`.

**IPv6 policy parity check on firewall:**
```spl
index=network (sourcetype="paloalto:config" OR sourcetype="cisco:asa:config") earliest=-7d
| eval has_ipv4_cde_rule=if(match(_raw, "(?i)(deny|drop).*10\.10\.0\.0"), 1, 0)
| eval has_ipv6_cde_rule=if(match(_raw, "(?i)(deny|drop).*2001:db8:cde:") OR match(_raw, "(?i)(deny|drop).*ipv6.*any.*cde"), 1, 0)
| eval parity=if(has_ipv4_cde_rule=1 AND has_ipv6_cde_rule=0, "GAP — IPv4 CDE rules exist but NO IPv6 equivalent", "OK")
| where parity != "OK"
| table host, parity
```

**Verification:**
```spl
index=network sourcetype="paloalto:traffic" dest_zone="CDE" | eval is_ipv6=if(match(src, ":"), 1, 0) | stats count by is_ipv6
```

### Step 2 — Create segmentation validation

**Continuous IPv6 segmentation monitoring:**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa") earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval dest_in_cde=case(
    cidrmatch("2001:db8:cde::/48", dest), "yes",
    cidrmatch("10.10.0.0/16", dest), "yes",
    1=1, "no")
| where dest_in_cde="yes"
| eval src_approved=case(
    cidrmatch("2001:db8:pos::/48", src), "yes",
    cidrmatch("10.20.0.0/24", src), "yes",
    1=1, "no")
| stats count by src, dest, action, src_approved
| where src_approved="no" AND action!="denied" AND action!="blocked"
| eval finding="PCI DSS SEGMENTATION VIOLATION: unapproved IPv6 source " . src . " accessed CDE destination " . dest
```

**Semi-annual segmentation test evidence (Req 11.4.5):**
```spl
| inputlookup pci_segmentation_tests.csv
| eval ipv6_tested=if(test_protocol="IPv6", 1, 0)
| stats count(eval(ipv6_tested=1)) as ipv6_tests count as total_tests
| eval ipv6_coverage=round(ipv6_tests / total_tests * 100, 0) . "%"
| eval assessment=if(ipv6_coverage="0%", "CRITICAL — no IPv6 segmentation testing performed (Req 11.4.5 gap)", "IPv6 segmentation testing: " . ipv6_coverage . " of tests include IPv6")
```

### Step 3 — Validate
(a) **IPv6 penetration test.** From a non-CDE VLAN, attempt to reach CDE servers via IPv6. Use `nmap -6 -sT 2001:db8:cde::1`. Verify the firewall blocks the traffic.

(b) **Rogue RA test.** On a non-CDE VLAN, inject a rogue RA (lab only). Verify that even with IPv6 connectivity, CDE is unreachable.

(c) **Firewall rule review.** Compare IPv4 and IPv6 rule counts on the CDE firewall. If IPv4 has 50 rules and IPv6 has 0, there is a segmentation gap.

### Step 4 — Operationalize

**Dashboard** ("PCI DSS — IPv6 Segmentation Compliance"):
- Row 1 — Single-value: IPv6 segmentation violations (target: 0). Red/green indicator.
- Row 2 — Firewall rule parity: IPv4 vs IPv6 CDE rule comparison.
- Row 3 — Table: all IPv6 traffic to/from CDE with approval status.
- Row 4 — Semi-annual test evidence: IPv6 segmentation test results.

**Alert:** Any permitted IPv6 traffic to CDE from unapproved source — CRITICAL. PCI DSS segmentation failure.

**Runbook:**
1. Segmentation violation detected: Block the IPv6 traffic immediately. Add explicit IPv6 deny rules for CDE zones. Document as incident.
2. No IPv6 CDE firewall rules: Create IPv6 equivalents of all IPv4 CDE rules. Test before production deployment.
3. QSA evidence: Export dashboard panels as PDF for QSA review. Include segmentation test results for Req 11.4.5.

### Step 5 — Troubleshooting

- **IPv6 on CDE servers.** The simplest remediation may be to disable IPv6 on CDE servers if not needed (CIS control 3.1.1). This eliminates the IPv6 attack surface entirely.

- **Firewall IPv6 default policy.** Verify the firewall's IPv6 default policy is deny-all. Some firewalls have implicit allow for IPv6 even when IPv4 is deny-by-default.

- **Zone-based firewalls.** In zone-based firewall architectures, verify that IPv6 traffic is subject to the same zone policies as IPv4. Some platforms process IPv4 and IPv6 policies independently.

## SPL

```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd") earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| lookup cde_subnets.csv dest_subnet as dest OUTPUT is_cde
| where is_cde="yes" AND is_ipv6=1
| lookup cde_approved_sources.csv src_subnet as src OUTPUT approved
| eval segmentation_status=case(
    approved="yes", "PERMITTED — approved source to CDE via IPv6",
    action="allowed" AND (approved!="yes" OR isnull(approved)), "VIOLATION — unapproved IPv6 access to CDE PERMITTED",
    action="denied" OR action="blocked", "BLOCKED — unapproved IPv6 access to CDE correctly denied",
    1=1, "UNKNOWN")
| where segmentation_status="VIOLATION*"
| stats count as violations dc(src) as unique_sources sum(bytes) as volume by host, dest, segmentation_status
| eval pci_impact="PCI DSS Req 1.2.3/1.3.1 VIOLATION — IPv6 traffic bypassing CDE segmentation"
| sort -violations
```

## Visualization

(1) Single-value: IPv6 segmentation violations (target: 0). (2) Table: all IPv6 traffic to/from CDE with segmentation status. (3) Timechart: IPv6 CDE access attempts over 30 days. (4) Compliance evidence panel for QSA review.

## Known False Positives

**Dual-stack CDE services.** If the CDE intentionally supports IPv6 access from approved sources, IPv6 traffic to the CDE is expected. Ensure the `cde_approved_sources.csv` lookup includes approved IPv6 subnets.

**Management traffic.** IPv6 management traffic (SSH, SNMP) to CDE systems from management VLANs may be legitimate. Verify these are documented in the firewall rule set.

**DNS and NTP.** CDE systems may need IPv6 connectivity to DNS and NTP servers. These should be explicitly approved in the segmentation policy.

## References

- [PCI DSS v4.0 — Payment Card Industry Data Security Standard](https://www.pcisecuritystandards.org/document_library/)
- [PCI DSS Information Supplement: Network Segmentation](https://www.pcisecuritystandards.org/documents/Guidance-PCI-DSS-Scoping-and-Segmentation_v1_1.pdf)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4 — filtering and segmentation)](https://www.rfc-editor.org/rfc/rfc9099)
