<!-- AUTO-GENERATED from UC-5.20.85.json — DO NOT EDIT -->

---
id: "5.20.85"
title: "Rogue IPv6 Detection on IPv4-Only Networks"
status: "verified"
criticality: "critical"
splunkPillar: "Platform"
---

# UC-5.20.85 · Rogue IPv6 Detection on IPv4-Only Networks

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Imagine a neighbourhood (VLAN) where everyone uses the old postal system (IPv4 only). But all the houses (computers) have mailboxes for both old and new post (IPv6 enabled by default). A burglar moves in and starts telling everyone 'I'm the new postman for the new postal system — send all your new post through me.' Suddenly, half the neighbourhood's letters go through the burglar instead of the real post office. We watch for anyone claiming to be a new postman in neighbourhoods that don't use the new postal system.*

---

## Description

Detects IPv6 traffic on network segments designated as IPv4-only, with specific focus on Rogue Router Advertisement attacks. All modern operating systems have IPv6 enabled by default, so 'IPv4-only' networks always have IPv6 link-local traffic. The critical risk is when an attacker injects Router Advertisements to provide global IPv6 connectivity, redirecting all dual-stack traffic through the attacker's device. This detection is RFC 7123 compliant and addresses the most common oversight in enterprise network security.

## Value

This is arguably the single most impactful IPv6 security use case for organisations that have not yet deployed IPv6. An attacker with physical network access (or a compromised host) can inject a single Router Advertisement and redirect all traffic from every dual-stack host on the VLAN — completely bypassing IPv4 firewalls, IDS/IPS, and DLP systems. Detection of rogue RAs on IPv4-only VLANs is the minimum viable IPv6 security control, even for organisations with no IPv6 deployment plans.

## Implementation

Create a lookup of VLANs designated as IPv4-only. Monitor these VLANs for any IPv6 traffic, especially Router Advertisements. Alert immediately on RA detection. Deploy RA Guard as the primary prevention control.

## Detailed Implementation

### Prerequisites
- Inventory of VLANs/subnets designated as IPv4-only.
- Syslog from switches on IPv4-only segments (or Zeek sensors, SPAN/TAP).
- RA Guard capability on access switches (for prevention).

### Step 1 — Configure data collection

**Create IPv4-only VLAN lookup:**
```csv
vlan,vlan_name,location,ipv4_only,notes
100,users-floor1,Building-A,yes,No IPv6 deployed
200,printers,Building-A,yes,Legacy printers only
300,iot-sensors,Factory,yes,IPv4-only sensors
400,servers,DC-1,no,Dual-stack servers
```
Upload as `ipv4_only_vlans.csv`.

**Enable IPv6 RA syslog on Cisco switches (even on IPv4-only VLANs):**
```
! On all access switches — detect RAs even without RA Guard
interface range GigabitEthernet1/0/1 - 48
 ipv6 nd raguard
!
logging discriminator ROGUE_RA severity includes 4
```
With RA Guard enabled, `%SISF-4-PAK_DROP` messages with reason "RA" indicate rogue RA attempts.

**Zeek-based detection (if deployed):**
```
index=network sourcetype="zeek:weird" name="ipv6_router_advert"
| lookup ipv4_only_vlans.csv vlan as vlan OUTPUT ipv4_only
| where ipv4_only="yes"
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" "RA" | stats count by host
```

### Step 2 — Create detection search

**Rogue RA detection on IPv4-only VLANs:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-1h
  ("%SISF-4-PAK_DROP" AND "RA" OR "%IPV6_ND-3-INVALID_RA" OR "%RA_GUARD")
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| lookup ipv4_only_vlans.csv vlan OUTPUT ipv4_only, location
| where ipv4_only="yes"
| rex field=_raw "(?:source|from|src)\s*=?\s*(?<ra_source>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:port|Port|IF)\s+(?<source_port>\S+)"
| eval severity="CRITICAL — Rogue Router Advertisement detected on IPv4-only VLAN " . vlan . " at " . location
| stats count as events first(_time) as first last(_time) as last by host, vlan, location, source_port, ra_source, severity
```

**Complementary search — detect global IPv6 addresses (evidence of successful RA attack):**
```spl
index=network sourcetype="cisco:ios" earliest=-1h
  "%IPV6-6-ADDR" OR "%IPV6-5-ADDRSTATE"
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| lookup ipv4_only_vlans.csv vlan OUTPUT ipv4_only
| where ipv4_only="yes"
| rex field=_raw "(?<global_ipv6>2[0-9a-fA-F]{3}:[0-9a-fA-F:]+)"
| eval severity="CRITICAL — Host has acquired global IPv6 address on IPv4-only VLAN. A rogue RA has been ACCEPTED."
```

### Step 3 — Validate
(a) **RA Guard test.** On a lab switch with RA Guard enabled and an IPv4-only VLAN, connect a Linux laptop running `radvd` (RA daemon). Verify:
- `%SISF-4-PAK_DROP` with reason "RA" appears in syslog.
- Other hosts on the VLAN do NOT acquire global IPv6 addresses.
- The alert fires in Splunk.

(b) **No RA Guard test.** On a lab switch WITHOUT RA Guard, repeat the test. Verify:
- Other hosts on the VLAN DO acquire global IPv6 addresses (confirming the attack works).
- The global address detection search triggers.

(c) **Baseline check.** Verify that normal IPv6 link-local and multicast traffic on IPv4-only VLANs does NOT trigger high-severity alerts.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Rogue IPv6 on IPv4-Only Networks"):
- Row 1 — Single-value: rogue RA attempts in last 24 hours (target: 0).
- Row 2 — Single-value: hosts with unexpected global IPv6 addresses (target: 0).
- Row 3 — Table: all IPv6 activity on IPv4-only VLANs with classification.
- Row 4 — Deployment status: RA Guard coverage on IPv4-only VLANs.

**Alert:** Rogue RA on IPv4-only VLAN — CRITICAL. This is always an attack or serious misconfiguration. Immediate incident response required.

**Runbook:**
1. Rogue RA detected WITH RA Guard: RA Guard blocked the attack. Investigate the source port. Identify and isolate the device.
2. Rogue RA detected WITHOUT RA Guard: All hosts on the VLAN may be compromised. Immediately deploy RA Guard. Flush IPv6 neighbor caches on affected hosts (`netsh interface ipv6 delete neighbors` on Windows, `ip -6 neigh flush all` on Linux).
3. Global IPv6 address detected on IPv4-only VLAN: A rogue RA has been accepted. Trace the RA source. Disable the port. Deploy RA Guard. Force SLAAC deprecation by advertising the prefix with zero lifetime.

### Step 5 — Troubleshooting

- **RA Guard deployment gaps.** RA Guard must be enabled on EVERY access port on IPv4-only VLANs. A single unprotected port allows an attacker to provide IPv6 to the entire VLAN. Audit deployment with `show ipv6 nd raguard policy` on all switches.

- **Cisco platform requirements.** RA Guard on Catalyst switches requires SISF (device-tracking) to be enabled. On older platforms, use `ipv6 nd raguard attach-policy <name>` per interface.

- **Alternative approach for legacy switches.** On switches that don't support RA Guard, deploy an IPv6 ACL on the VLAN SVI that blocks ICMPv6 types 134 (RA) from non-link-local sources, or use a port ACL to block all ICMPv6 type 134.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="zeek:conn" OR sourcetype="paloalto:traffic") earliest=-24h
| eval is_ipv6=case(
    match(src, ":"), 1,
    match(dest, ":"), 1,
    match(_raw, "(?i)ipv6|ICMPv6|ff02::"), 1,
    1=1, 0)
| where is_ipv6=1
| lookup ipv4_only_vlans.csv vlan as src_vlan OUTPUT ipv4_only
| where ipv4_only="yes"
| eval traffic_type=case(
    match(_raw, "(?i)router.?advert|RA|ICMPv6.*type.?134"), "CRITICAL — Router Advertisement on IPv4-only VLAN",
    match(_raw, "(?i)router.?solicit|ICMPv6.*type.?133"), "WARNING — Router Solicitation (host looking for IPv6 router)",
    match(src, "^2[0-9a-fA-F]{3}:"), "HIGH — Global unicast IPv6 on IPv4-only VLAN (rogue RA has been accepted)",
    match(src, "^[Ff][Ee][89AaBb]"), "INFO — Link-local only (hosts have IPv6 enabled but no global connectivity)",
    match(dest, "^[Ff][Ff]02::"), "INFO — IPv6 multicast (NDP, MLD)",
    1=1, "IPv6 traffic on IPv4-only segment")
| stats count as events first(_time) as first last(_time) as last by host, src_vlan, src, traffic_type
| sort -events
```

## Visualization

(1) Single-value: rogue RA count on IPv4-only VLANs (target: 0). (2) Table: IPv6 traffic by VLAN with traffic type classification. (3) Alert panel: Router Advertisements on IPv4-only segments. (4) Map: physical location of IPv4-only VLANs with IPv6 activity.

## Known False Positives

**Link-local NDP multicast is always present.** IPv6 multicast traffic (ff02::1, ff02::2, MLD) exists on every Ethernet segment because all modern OSes have IPv6 enabled. This is normal and expected. Only alert on Router Advertisements and global unicast addresses.

**Windows Network Discovery.** Windows hosts send IPv6 multicast for LLMNR (ff02::1:3) and mDNS (ff02::fb) as part of network discovery. These are informational, not security-critical.

**Printer and IoT device advertisements.** Some printers and IoT devices advertise IPv6 services. These create 'noise' but are not attacks. However, they indicate devices that should have IPv6 disabled if the VLAN is intentionally IPv4-only.

## References

- [RFC 7123 — Security Implications of IPv6 on IPv4 Networks](https://www.rfc-editor.org/rfc/rfc7123)
- [RFC 6104 — Rogue IPv6 Router Advertisement Problem Statement](https://www.rfc-editor.org/rfc/rfc6104)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.7.1 — IPv6 on IPv4-only networks)](https://www.rfc-editor.org/rfc/rfc9099)
- [THC-IPv6 — Attack toolkit including fake_router6 for RA spoofing testing](https://github.com/vanhauser-thc/thc-ipv6)
