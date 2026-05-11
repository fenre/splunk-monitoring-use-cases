<!-- AUTO-GENERATED from UC-5.20.84.json — DO NOT EDIT -->

---
id: "5.20.84"
title: "IPv6 Control Plane Policing (CoPP) Effectiveness Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.84 · IPv6 Control Plane Policing (CoPP) Effectiveness Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability &middot; **Wave:** Run &middot; **Status:** Verified

*The post office (router) has a limited number of workers (CPU). We set up a queue management system (CoPP) that limits how many letters of each type the workers have to process. But the new postal system (IPv6) has letter types that didn't exist before.*

---

## Description

Monitors Control Plane Policing (CoPP/CPPr) effectiveness for IPv6-specific protocols including NDP, MLD, OSPFv3, DHCPv6, and ICMPv6 error messages. CoPP protects the router CPU from protocol-level DoS attacks, but IPv6 introduces protocol traffic (especially NDP) that does not exist in IPv4. If CoPP policies do not include explicit IPv6 protocol classifications, IPv6 traffic may fall into the default class and either be dropped (breaking IPv6) or pass unlimited (creating a DoS vulnerability).

## Value

CoPP is the primary defense against control plane exhaustion attacks. IPv6 networks generate significantly more control plane traffic than IPv4 due to NDP (which replaces ARP, DHCP, and ICMP Redirect functions combined). Without proper IPv6 CoPP classification, a single attacker can overwhelm a router's CPU with NDP floods, MLD storms, or OSPFv3 Hello manipulation. This monitoring ensures IPv6 protocols are properly classified, rate-limited, and not silently dropped.

## Implementation

Parse CoPP class-map names and counters from syslog and SNMP. Identify IPv6-specific classes. Alert on excessive drops in IPv6 protocol classes. Alert when IPv6 protocols are not classified (falling to default).

## Detailed Implementation

### Prerequisites
- CoPP/CPPr configured on all routers and L3 switches.
- SNMP polling of CoPP counters or syslog-based counter reporting.
- Understanding of IPv6 protocol classification requirements.

### Step 1 — Configure data collection

**Poll CoPP counters via SNMP or CLI:**
```
show policy-map control-plane
```
Output includes per-class conform/exceed/violate counters. Schedule polling every 5 minutes.

**Alternative: syslog-based detection for excessive drops:**
```
logging rate-limit 1
policy-map control-plane-policy
 class class-ipv6-ndp
  police rate 500 pps
   conform-action transmit
   exceed-action drop log
```
The `log` keyword on exceed-action generates syslog messages for dropped packets.

**Example Cisco IOS-XE CoPP policy with IPv6 classification:**
```
class-map match-any class-ipv6-ndp
 match access-group name ACL-COPP-NDP
!
class-map match-any class-ipv6-ospfv3
 match access-group name ACL-COPP-OSPFV3
!
class-map match-any class-ipv6-bgp
 match access-group name ACL-COPP-BGP6
!
ip access-list extended ACL-COPP-NDP
 permit icmp any any nd-na
 permit icmp any any nd-ns
 permit icmp any any router-advertisement
 permit icmp any any router-solicitation
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%CPP" OR "%COPP" | stats count by host | sort -count
```

### Step 2 — Create monitoring searches

**CoPP IPv6 class coverage audit:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval has_ndp_class=if(match(_raw, "(?i)class.*(ndp|neighbor|icmpv6)"), 1, 0)
| eval has_ospfv3_class=if(match(_raw, "(?i)class.*(ospfv3|ospf.*v6)"), 1, 0)
| eval has_bgpv6_class=if(match(_raw, "(?i)class.*(bgp.*v6|bgp.*ipv6)"), 1, 0)
| eval has_dhcpv6_class=if(match(_raw, "(?i)class.*(dhcpv6|dhcp.*v6)"), 1, 0)
| eval ipv6_classes=has_ndp_class + has_ospfv3_class + has_bgpv6_class + has_dhcpv6_class
| eval status=case(
    ipv6_classes >= 3, "GOOD — IPv6 protocols classified in CoPP",
    ipv6_classes >= 1, "PARTIAL — some IPv6 protocols may fall to default class",
    ipv6_classes=0, "CRITICAL — NO IPv6 protocol classification in CoPP — IPv6 DoS vulnerability")
| table host, has_ndp_class, has_ospfv3_class, has_bgpv6_class, has_dhcpv6_class, status
| sort ipv6_classes
```

### Step 3 — Validate
(a) **CoPP counter verification.** SSH to a sample router. Run `show policy-map control-plane` and compare counters with SPL results.

(b) **Default class check.** Verify IPv6 traffic is NOT hitting the default CoPP class. If NDP packets appear in the default class counters, CoPP is misconfigured for IPv6.

(c) **Load test.** On a lab router, generate NDP floods using THC-IPv6 `flood_router6` and verify CoPP drops the excess traffic while permitting legitimate NDP.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Control Plane Protection"):
- Row 1 — Single-value: devices with no IPv6 CoPP classification (target: 0).
- Row 2 — Table: CoPP class counters for IPv6 protocols across all devices.
- Row 3 — Timechart: NDP drops over time (correlate with NDP exhaustion alerts).
- Row 4 — Configuration audit: devices missing IPv6 CoPP classes.

**Alert:** Device has no IPv6 CoPP classification — critical vulnerability. NDP flood can exhaust CPU.

**Runbook:**
1. No IPv6 CoPP: Deploy IPv6-aware CoPP template. Include classes for NDP, OSPFv3, BGP IPv6, DHCPv6, MLD, and ICMPv6 errors.
2. Excessive NDP drops: Tune NDP rate limit. Default 500 pps is appropriate for most access switches. Core routers may need higher limits.
3. OSPFv3 drops: Increase OSPFv3 CoPP rate during planned convergence events. Create a maintenance window macro.

### Step 5 — Troubleshooting

- **Platform-specific CoPP defaults.** Cisco IOS-XE Cat9K has built-in system-defined CoPP classes for IPv6 (system-cpp-police-ndp). Verify these are not disabled. Cisco IOS-XR requires explicit CoPP configuration.

- **CoPP counter resets.** CoPP counters may reset on configuration changes or policy reattachment. Use rate-based calculations rather than absolute counters.

- **Juniper equivalent.** JunOS uses `firewall filter` applied to `lo0` for control plane protection. IPv6 terms require `family inet6` match conditions.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("%CPP" OR "%COPP" OR "%CPUHOG" OR "control-plane" AND ("drop" OR "conform" OR "exceed" OR "violate"))
| rex field=_raw "class.?map\s+(?<copp_class>\S+)"
| rex field=_raw "(?:conform|dropped|exceeded)\s+(?<counter>\d+)"
| eval counter=tonumber(counter)
| eval ipv6_related=if(match(copp_class, "(?i)ipv6|ndp|icmpv6|ospfv3|mld|dhcpv6|bgp.?v6"), "IPv6-specific", "general")
| stats sum(counter) as total_events by host, copp_class, ipv6_related
| eval status=case(
    ipv6_related="IPv6-specific" AND total_events > 10000, "HIGH DROPS — IPv6 protocol traffic being rate-limited aggressively",
    ipv6_related="general" AND total_events > 50000, "IPv6 traffic may be hitting default class",
    1=1, "OK")
| sort -total_events
```

## Visualization

(1) Table: CoPP classes with conform/drop counters, highlighting IPv6 classes. (2) Timechart: CoPP drops over time by class. (3) Single-value: IPv6 protocol drop rate. (4) Alert panel: devices where IPv6 protocols hit the default CoPP class.

## Known False Positives

**High NDP rates on access switches.** Access layer switches in large VLANs legitimately process high NDP traffic. Tune CoPP thresholds per platform role (core vs access).

**CoPP class naming variations.** Different IOS versions use different default class-map names. The IPv6 class may be named `system-cpp-police-ndp`, `copp-system-p-class-ndp`, or custom names. Build a class name mapping table per platform.

**OSPFv3 adjacency formation bursts.** During router reloads or adjacency re-formation, OSPFv3 traffic spikes are legitimate. Correlate CoPP drops with OSPFv3 adjacency events (UC-5.20.43).

## References

- [Cisco Control Plane Policing (CoPP) Implementation Best Practices](https://www.cisco.com/c/en/us/)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4 — control plane protection)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 6192 — Protecting the Router Control Plane (BCP 164)](https://www.rfc-editor.org/rfc/rfc6192)
