<!-- AUTO-GENERATED from UC-5.20.103.json — DO NOT EDIT -->

---
id: "5.20.103"
title: "HIPAA §164.312 IPv6 Technical Safeguard Verification"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.103 · HIPAA §164.312 IPv6 Technical Safeguard Verification

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Run &middot; **Status:** Verified

*Hospitals have strict rules about protecting patient records (HIPAA). When the hospital network uses the new address system (IPv6), we need to make sure patient records are still just as protected as before — encrypted when sent, tracked for who accessed them, and locked behind proper security gates. We check all of this automatically so no patient data is exposed through an unprotected IPv6 path.*

---

## Description

Verifies HIPAA Security Rule §164.312 technical safeguards for IPv6 networks carrying electronic Protected Health Information (ePHI). Checks access control effectiveness for IPv6 traffic to ePHI systems, audit log completeness for IPv6 events, transmission encryption on IPv6 paths, person-to-address attribution, and NDP security on ePHI network segments.

## Value

Healthcare organisations are increasingly deploying IPv6 but often fail to extend HIPAA technical safeguards to IPv6 traffic. If ePHI is accessible over IPv6 but the IPv6 path lacks encryption, audit logging, or access controls, the organisation is non-compliant with HIPAA and exposed to a data breach. This is particularly dangerous because attackers can exploit the unmonitored IPv6 path to access ePHI while IPv4 controls remain intact.

## Implementation

Identify ePHI subnets and systems. Monitor IPv6 traffic to/from ePHI systems. Verify encryption, access control, audit logging, and user attribution for all IPv6 ePHI flows.

## Detailed Implementation

### Prerequisites
- ePHI system and subnet inventory.
- Firewall logging for IPv6 traffic to ePHI subnets.
- User-to-IP mapping (DHCP/RADIUS/NAC logs) for IPv6 attribution.

### Step 1 — Configure data collection

**ePHI subnet lookup:**
```csv
dest_subnet,contains_ephi,system_name,data_classification
2001:db8:10::/48,yes,"EHR Database Cluster","PHI — patient records"
2001:db8:20::/48,yes,"PACS Imaging","PHI — medical images"
2001:db8:30::/48,yes,"Lab Information System","PHI — lab results"
```

**IPv6 user attribution:**
Configure RADIUS/NAC to log IPv6 address assignments with user identity:
```spl
index=authentication sourcetype="cisco:ise" "IPv6" earliest=-24h
| rex field=_raw "User-Name\s*=?\s*(?<username>[^,]+)"
| rex field=_raw "Framed-IPv6-Address\s*=?\s*(?<ipv6_addr>[0-9a-fA-F:]+)"
| table _time, username, ipv6_addr
| outputlookup ipv6_user_mapping.csv
```

### Step 2 — Create HIPAA monitoring searches

**§164.312(e)(1) — Transmission security (encryption audit):**
```spl
index=network sourcetype="paloalto:traffic" earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| lookup ephi_subnets.csv dest_subnet as dest OUTPUT contains_ephi
| where contains_ephi="yes" AND is_ipv6=1
| eval encrypted=if(match(app, "(?i)ssl|tls|https|ipsec|ssh"), 1, 0)
| stats count as total count(eval(encrypted=0)) as unencrypted by dest
| where unencrypted > 0
| eval finding="HIPAA §164.312(e)(1) VIOLATION: " . unencrypted . " unencrypted IPv6 flows to ePHI system " . dest
```

**§164.312(b) — Audit log completeness:**
```spl
index=network earliest=-7d
| lookup ephi_subnets.csv dest_subnet as dest OUTPUT contains_ephi
| where contains_ephi="yes"
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| eval has_user=if(isnotnull(src_user) AND src_user!="", 1, 0)
| eval has_port=if(isnotnull(src_port), 1, 0)
| stats count as total count(eval(is_ipv6=1)) as ipv6_events count(eval(is_ipv6=1 AND has_user=1)) as ipv6_with_user count(eval(is_ipv6=1 AND has_port=1)) as ipv6_with_port
| eval audit_completeness=round(ipv6_with_user / max(ipv6_events, 1) * 100, 1)
| eval finding=if(audit_completeness < 95, "§164.312(b) — IPv6 audit log user attribution is only " . audit_completeness . "%", "PASS — " . audit_completeness . "% user attribution")
```

### Step 3 — Validate
(a) **Transmission test.** From a workstation on the ePHI VLAN, access an ePHI system over IPv6 using HTTP (not HTTPS). Verify the firewall logs an unencrypted connection and the alert fires.

(b) **Attribution test.** Access an ePHI system from a known user account over IPv6. Verify the user identity appears in the firewall log.

(c) **NDP security test.** On an ePHI VLAN, verify RA Guard and DHCP Guard are enabled. See UC-5.20.21 and UC-5.20.28.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — HIPAA Technical Safeguards"):
- Row 1 — Single-values: unencrypted ePHI flows (red if >0), user attribution percentage.
- Row 2 — Table: violations by HIPAA section.
- Row 3 — ePHI subnet security status.
- Row 4 — NDP security status on ePHI VLANs.

**Alert 1:** Any unencrypted IPv6 access to ePHI — critical. Immediate investigation.
**Alert 2:** IPv6 user attribution drops below 95% — high. RADIUS/NAC configuration issue.

### Step 5 — Troubleshooting

- **Unencrypted ePHI access.** If a clinical application uses HTTP instead of HTTPS for IPv6, the application needs to be reconfigured. If the application doesn't support HTTPS, deploy a reverse proxy with TLS termination.

- **Missing user attribution.** IPv6 temporary addresses (RFC 8981) can complicate user-to-IP mapping. Ensure RADIUS/NAC logs capture the full IPv6 address and that DHCPv6 assignments are correlated. See UC-5.20.6 for privacy address tracking.

- **NDP poisoning on ePHI VLANs.** Deploy Cisco SISF (Switch Integrated Security Features) or equivalent on switches serving ePHI VLANs. RA Guard and DHCP Guard are essential. See UC-5.20.28.

## SPL

```spl
index=network earliest=-24h
  (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd")
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| lookup ephi_subnets.csv dest_subnet as dest OUTPUT contains_ephi
| where contains_ephi="yes" AND is_ipv6=1
| eval hipaa_checks=mvappend(
    if(action="allowed" AND NOT match(app, "(?i)ssl|tls|https|ipsec"), "§164.312(e)(1) — unencrypted IPv6 access to ePHI", null()),
    if(isnull(src_user) OR src_user="", "§164.312(d) — IPv6 access to ePHI without user attribution", null()),
    if(match(src, "^[Ff][Ee][89AaBb]"), "§164.312(c)(1) — link-local IPv6 source accessing ePHI (NDP poisoning risk)", null()))
| mvexpand hipaa_checks
| where isnotnull(hipaa_checks)
| stats count as violations dc(src) as unique_sources by hipaa_checks, dest
| eval severity=case(
    match(hipaa_checks, "unencrypted"), "HIGH — ePHI transmitted in cleartext over IPv6",
    match(hipaa_checks, "without user attribution"), "MEDIUM — cannot attribute IPv6 access to a person",
    match(hipaa_checks, "link-local"), "HIGH — possible NDP-based MITM on ePHI segment",
    1=1, "INFO")
| sort -violations
```

## Visualization

(1) Table: HIPAA violations by section. (2) Single-value: unencrypted IPv6 ePHI flows (should be zero). (3) Map: ePHI subnets with IPv6 security status. (4) Timeline: violation trends.

## Known False Positives

**Internal monitoring traffic.** Health monitoring systems (Nagios, Zabbix, Splunk UF) may access ePHI systems over IPv6 without user authentication. These are service accounts, not person access — document as an exception.

**Encrypted but unidentified.** Some encrypted IPv6 connections may not be classified as TLS/HTTPS by the firewall (e.g., proprietary protocols). Verify the connection is encrypted even if the app classification is generic.

**IPv6 multicast on ePHI VLANs.** NDP and MLD multicast traffic on ePHI VLANs is normal. Flag only link-local unicast sources attempting to access ePHI hosts.

## References

- [HIPAA Security Rule — §164.312 Technical Safeguards](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312)
- [HHS — Guidance on HIPAA Security Rule Technical Safeguards](https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html)
- [NIST SP 800-66 — Implementing the HIPAA Security Rule](https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final)
