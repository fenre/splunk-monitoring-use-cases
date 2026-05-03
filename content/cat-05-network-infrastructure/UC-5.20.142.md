<!-- AUTO-GENERATED from UC-5.20.142.json — DO NOT EDIT -->

---
id: "5.20.142"
title: "IPv6 First-Hop Security (FHS) Feature Deployment Audit"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.142 · IPv6 First-Hop Security (FHS) Feature Deployment Audit

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Our network switches have security guards at every entry point that check IPv6 'ID cards.' We audit all entry points to make sure every guard is on duty and properly trained. If a guard is missing from one entrance, that's where the burglars get in. This check ensures every entrance is properly covered.*

---

## Description

Audits the deployment of IPv6 First-Hop Security (FHS) features across all access-layer switches. FHS is the IPv6 equivalent of ARP inspection and DHCP snooping. Missing FHS features leave networks vulnerable to Rogue RA, DHCPv6 spoofing, NDP spoofing, and neighbour cache attacks.

## Value

IPv6 FHS is critical for access-layer security. Without RA Guard, any host can become the default router. Without DHCPv6 Guard, any host can assign addresses. Without ND Inspection, any host can spoof neighbour entries. This audit ensures all switches have FHS deployed consistently, preventing gaps that attackers exploit.

## Implementation

Parse switch configurations for FHS feature presence. Report switches missing required FHS features.

## Detailed Implementation

### Prerequisites
- Cisco IOS-XE switches with SISF support.
- Switch configuration collection (SCP, NETCONF, or running-config capture).

### Step 1 — Define required FHS features per switch role.

### Step 2 — Collect switch configurations and parse for FHS feature presence.

### Step 3 — Validate: Manually verify FHS on sample switches:
```
show ipv6 snooping policies
show device-tracking policies
show ipv6 nd raguard policy
```

### Step 4 — Operationalize
**Dashboard:** FHS compliance matrix. **Report:** Monthly FHS audit.

### Step 5 — Troubleshooting
- Enable SISF as the foundation: `device-tracking policy SISF_POLICY` → apply to all access VLANs.
- Then layer RA Guard and DHCPv6 Guard on top of SISF.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-7d
  ("RA Guard" OR "DHCPv6 Guard" OR "ND Inspection" OR "Source Guard" OR "Destination Guard" OR "SISF" OR "ipv6 snooping" OR "device-tracking" OR "binding-table")
| eval fhs_feature=case(
    match(_raw, "(?i)RA.?Guard"), "RA Guard",
    match(_raw, "(?i)DHCPv6.?Guard"), "DHCPv6 Guard",
    match(_raw, "(?i)ND.?Inspection|nd-inspection"), "ND Inspection",
    match(_raw, "(?i)Source.?Guard|source-guard"), "IPv6 Source Guard",
    match(_raw, "(?i)Destination.?Guard|destination-guard"), "IPv6 Destination Guard",
    match(_raw, "(?i)SISF|snooping|device.?tracking|binding.?table"), "SISF/Device Tracking",
    1=1, "Other FHS")
| eval fhs_status=case(
    match(_raw, "(?i)enabled|active|configured|applied"), "ENABLED",
    match(_raw, "(?i)disabled|removed|not.?configured|missing"), "DISABLED",
    match(_raw, "(?i)violation|denied|dropped|blocked"), "ENFORCEMENT",
    1=1, "UNKNOWN")
| stats count as events values(fhs_status) as statuses by host, fhs_feature
| eval compliance=case(
    mvcount(mvfilter(match(statuses, "DISABLED"))) > 0, "NON-COMPLIANT — " . fhs_feature . " disabled on " . host,
    mvcount(mvfilter(match(statuses, "ENABLED"))) > 0, "COMPLIANT",
    1=1, "UNKNOWN")
| sort compliance, fhs_feature
```

## Visualization

(1) Compliance matrix: switches vs FHS features. (2) Pie chart: compliant vs non-compliant. (3) Table: missing features by switch. (4) Trend: compliance over time.

## Known False Positives

**Router-facing ports.** Uplink ports to routers should have RA Guard in 'router' role, not 'host' role. Don't flag these as non-compliant.

**Legacy switches.** Some older switches don't support FHS. These should be flagged for hardware refresh.

## References

- [Cisco — IPv6 First-Hop Security Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipv6_fhsec/configuration/xe-3s/ip6f-xe-3s-book.html)
- [RFC 6105 — IPv6 Router Advertisement Guard (RA Guard)](https://www.rfc-editor.org/rfc/rfc6105)
