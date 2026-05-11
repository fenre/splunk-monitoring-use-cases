<!-- AUTO-GENERATED from UC-5.20.102.json — DO NOT EDIT -->

---
id: "5.20.102"
title: "CISA TIC 3.0 IPv6 Trust Zone and Telemetry Compliance"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.102 · CISA TIC 3.0 IPv6 Trust Zone and Telemetry Compliance

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Run &middot; **Status:** Verified

*The government's cybersecurity agency (CISA) has rules about how all government networks must be secured. They've set up checkpoints (like security gates) at the boundaries of different network areas. We need to make sure these security gates work just as well for new-format addresses (IPv6) as they do for old-format addresses (IPv4).*

---

## Description

Validates IPv6 compliance with CISA Trusted Internet Connections (TIC) 3.0 framework. TIC 3.0 requires security capabilities (telemetry, DNS integrity, intrusion detection, web filtering, email security, resilience) at every policy enforcement point, regardless of whether traffic uses IPv4 or IPv6. This UC audits IPv6 coverage across all TIC trust zones.

## Value

Federal agencies subject to TIC 3.0 must demonstrate that IPv6 traffic is inspected and protected with the same capabilities as IPv4 at all trust zone boundaries. TIC 3.0 is architecture-agnostic — it applies equally to on-premises, cloud, and hybrid environments. Many agencies have TIC-compliant IPv4 infrastructure but have not extended the same capabilities to IPv6, creating a compliance gap that this UC addresses.

## Implementation

Map TIC 3.0 security capabilities to IPv6-specific controls. Assess each capability at each trust zone. Track compliance status with evidence collection.

## Detailed Implementation

### Prerequisites
- TIC 3.0 trust zone architecture documented.
- PEP (policy enforcement point) inventory with IPv6 capability status.
- CISA CDM/EINSTEIN telemetry integration.

### Step 1 — Configure compliance tracking

**Create TIC 3.0 status lookup:**
```csv
tic_capability,status,last_verified,trust_zone,evidence_notes
"Telemetry — IPv6 flow/packet data to CISA EINSTEIN/CDM",pass,2026-04-20,"Agency Campus","NetFlow v9 with IPv6 templates configured on all border routers"
"DNS — IPv6 DNS resolution integrity (DNSSEC, DoH/DoT)",partial,2026-04-20,"Agency Campus","DNSSEC validation enabled; DoH/DoT not yet enforced for all clients"
"Intrusion Detection — IPv6 NGFW/IDS inspection depth",pass,2026-04-20,"Agency Campus","Palo Alto PA-5260 with IPv6 threat prevention profiles active"
"Web Filtering — IPv6 proxy/SWG enforcement",fail,2026-04-20,"Branch Office","Branch SWG does not inspect IPv6 — clients bypass proxy via IPv6 DIA"
"Email Security — IPv6 SMTP inspection (SPF/DKIM/DMARC)",pass,2026-04-20,"Agency Campus","Exchange Online with IPv6 MX records and DMARC enforcement"
"Resilience — IPv6 failover and availability at PEPs",partial,2026-04-20,"Agency Campus","Primary path IPv6-enabled; failover path IPv4-only"
```

**Evidence collection search — Telemetry completeness:**
```spl
index=network earliest=-24h
| eval has_ipv6_src=if(match(src, ":"), 1, 0)
| eval has_ipv6_dst=if(match(dest, ":"), 1, 0)
| eval ipv6_flow=if(has_ipv6_src=1 OR has_ipv6_dst=1, 1, 0)
| stats count as total count(eval(ipv6_flow=1)) as ipv6_flows by sourcetype
| eval ipv6_pct=round(ipv6_flows / total * 100, 1)
| eval telemetry_status=if(ipv6_flows > 0, "COLLECTING IPv6 telemetry", "NO IPv6 telemetry — capability gap")
| table sourcetype, total, ipv6_flows, ipv6_pct, telemetry_status
```

### Step 2 — Assess per trust zone

**Trust zone matrix:**
```spl
| inputlookup tic3_ipv6_status.csv
| chart values(status) as status by tic_capability, trust_zone
```

This creates a matrix showing compliance status for each capability at each trust zone, which is the format CISA expects.

### Step 3 — Validate
(a) **Telemetry test.** Generate IPv6 traffic from each trust zone. Verify it appears in Splunk with full field fidelity (src, dest, port, protocol, bytes, timestamp).

(b) **IDS bypass test.** Send a known IPv6 attack signature through the PEP. Verify the IDS detects and alerts. Test with extension headers to ensure they don't bypass inspection.

(c) **Web filter bypass test.** Attempt to access a blocked URL via IPv6 direct connection (bypassing the proxy). Verify the connection is blocked.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — TIC 3.0 Compliance"):
- Row 1 — Heatmap: trust zones (rows) vs capabilities (columns) with pass/partial/fail.
- Row 2 — Single-value: overall compliance percentage.
- Row 3 — Table: non-compliant capabilities with remediation notes.
- Row 4 — Trend: quarterly compliance improvements.

**CISA reporting:** Export the trust zone matrix quarterly for CISA compliance reporting.

### Step 5 — Troubleshooting

- **Web filtering gap at branch offices.** The most common TIC 3.0 IPv6 gap is at branch offices where SWG/proxy does not handle IPv6. Solutions: (a) enable IPv6 on the SWG, (b) tunnel all branch IPv6 traffic to a central TIC access point, (c) deploy a cloud-based SWG that supports IPv6.

- **Telemetry gaps.** If IPv6 telemetry is missing from certain segments, verify that NetFlow/IPFIX templates include IPv6 fields. Some older exporters only include IPv4 templates by default. See UC-5.20.58 for NetFlow IPv6 template verification.

- **DNS security for IPv6.** Ensure recursive resolvers validate DNSSEC for AAAA records and that DNS64 (if used) does not bypass DNSSEC validation. See UC-5.20.53 for DNS64 DNSSEC monitoring.

## SPL

```spl
| makeresults
| eval tic_capability=mvappend(
    "Telemetry — IPv6 flow/packet data to CISA EINSTEIN/CDM",
    "DNS — IPv6 DNS resolution integrity (DNSSEC, DoH/DoT)",
    "Intrusion Detection — IPv6 NGFW/IDS inspection depth",
    "Web Filtering — IPv6 proxy/SWG enforcement",
    "Email Security — IPv6 SMTP inspection (SPF/DKIM/DMARC)",
    "Resilience — IPv6 failover and availability at PEPs")
| mvexpand tic_capability
| lookup tic3_ipv6_status.csv tic_capability OUTPUT status last_verified trust_zone evidence_notes
| eval status=coalesce(status, "NOT ASSESSED")
| eval compliance=case(
    status="pass", "COMPLIANT",
    status="partial", "PARTIALLY COMPLIANT — gaps identified",
    status="fail", "NON-COMPLIANT — remediation required",
    1=1, "NOT ASSESSED — requires evaluation")
| table tic_capability, trust_zone, compliance, last_verified, evidence_notes
```

## Visualization

(1) Table: TIC 3.0 capabilities with IPv6 compliance status per trust zone. (2) Heatmap: trust zones vs capabilities. (3) Single-value: overall compliance percentage. (4) Trend: compliance progress over quarters.

## Known False Positives

**Cloud-delivered TIC.** When TIC access points are cloud-delivered (Zscaler, Palo Alto Prisma), IPv6 inspection capabilities may be handled by the cloud provider. Verify with the provider rather than inspecting on-premises infrastructure.

**MTIPS connections.** Managed Trusted Internet Protocol Service (MTIPS) providers may handle IPv6 TIC compliance as part of their managed service. Confirm with the MTIPS provider.

**Trust zone classification.** Asset misclassification (e.g., a branch office device classified as campus) affects compliance reporting. Maintain accurate trust zone assignments.

## References

- [CISA — Trusted Internet Connections (TIC) 3.0 Core Guidance](https://www.cisa.gov/)
- [CISA — TIC 3.0 Security Capabilities Catalog](https://www.cisa.gov/trusted-internet-connections)
- [OMB M-21-07 — Completing the Transition to IPv6](https://www.whitehouse.gov/wp-content/uploads/2020/11/M-21-07.pdf)
