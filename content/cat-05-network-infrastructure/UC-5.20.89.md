<!-- AUTO-GENERATED from UC-5.20.89.json — DO NOT EDIT -->

---
id: "5.20.89"
title: "ULA (fc00::/7) Perimeter Leakage and Containment Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.89 · ULA (fc00::/7) Perimeter Leakage and Containment Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Some addresses in the new postal system (IPv6) are meant to be used only within your building or organisation — like internal mail that should never leave the premises. We watch the front door (perimeter) to make sure no internal-only mail accidentally goes out to the street, or comes in from outside with a fake internal address.*

---

## Description

Detects Unique Local Address (ULA, fc00::/7) traffic crossing organisational perimeter devices. ULA addresses are the IPv6 equivalent of RFC 1918 private addresses and must be filtered at all external boundaries. ULA leakage indicates routing misconfiguration, missing perimeter filters, or potential data exfiltration via internal addressing. DISA STIG NET-IPV6-032 mandates ULA filtering at all external perimeter interfaces.

## Value

ULA perimeter leakage is a compliance violation (DISA STIG) and a routing hygiene issue. Leaked ULA traffic creates unreachable destinations for external peers, may reveal internal network topology, and indicates missing perimeter ACLs. In the worst case, ULA leakage via BGP can create route announcements that cause traffic black holes for peers who accept the route.

## Implementation

Monitor perimeter firewall and flow data for any traffic with ULA source or destination addresses. Alert on ULA traffic crossing internet-facing interfaces. Verify perimeter ACLs block ULA.

## Detailed Implementation

### Prerequisites
- Perimeter firewall or flow data with IPv6 source/destination visibility.
- Lookup table identifying perimeter-facing interfaces.
- Understanding of legitimate ULA usage within the organisation.

### Step 1 — Configure data collection

**Create perimeter interface lookup:**
```csv
interface,is_perimeter,description
outside,yes,Internet-facing
dmz,yes,DMZ zone
inside,no,Internal
vpn,no,Site-to-site VPN
```
Upload as `perimeter_interfaces.csv`.

**Perimeter ACL to block ULA (and log violations):**
```
! Cisco IOS/IOS-XE
ipv6 access-list PERIMETER-IN
 deny ipv6 fc00::/7 any log
 deny ipv6 any fc00::/7 log
 permit ipv6 any any
!
interface GigabitEthernet0/0
 description Internet-facing
 ipv6 traffic-filter PERIMETER-IN in
```

**Palo Alto Networks security rule:**
```
rulebase security rules {
  BLOCK-ULA {
    from outside;
    to any;
    source fc00::/7;
    destination any;
    action deny;
    log-setting default;
  }
}
```

**Verification:**
```spl
index=network sourcetype="pan:traffic" (src="fc*" OR src="fd*" OR dest="fc*" OR dest="fd*") | stats count by host
```

### Step 2 — Create monitoring search

**ULA leakage detection with characterisation:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="netflow") earliest=-24h
| eval src_is_ula=if(match(src, "^[Ff][CcDd]"), 1, 0)
| eval dst_is_ula=if(match(dest, "^[Ff][CcDd]"), 1, 0)
| where src_is_ula=1 OR dst_is_ula=1
| eval leak_type=case(
    src_is_ula=1 AND match(src, "^[Ff][Cc]0"), "CRITICAL — fc00::/8 source (unassigned block, should not exist)",
    src_is_ula=1, "ULA source (fd00::/8) on perimeter",
    dst_is_ula=1, "ULA destination on perimeter (return traffic or scan)")
| stats count as flows sum(bytes) as volume by host, leak_type, src, dest
| sort -flows
```

**Configuration compliance check:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval blocks_ula_egress=if(match(_raw, "(?i)deny.*ipv6.*fc00::/7.*any|deny.*ipv6.*fd[0-9a-fA-F]{2}::/8.*any"), 1, 0)
| eval blocks_ula_ingress=if(match(_raw, "(?i)deny.*ipv6.*any.*fc00::/7|deny.*ipv6.*any.*fd[0-9a-fA-F]{2}::/8"), 1, 0)
| table host, blocks_ula_egress, blocks_ula_ingress
| where blocks_ula_egress=0 OR blocks_ula_ingress=0
| eval finding="ULA not filtered at perimeter — DISA STIG NET-IPV6-032 violation"
```

### Step 3 — Validate
(a) **ACL verification.** On perimeter devices, run `show ipv6 access-lists` and verify deny rules for fc00::/7 (or fd00::/8) are present.

(b) **Test traffic.** From a test host with a ULA address, attempt to send traffic to an external destination. Verify it is blocked and logged.

(c) **BGP filter check.** Verify BGP outbound filters include `deny fc00::/7 le 128` to prevent ULA route advertisement.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — ULA Containment"):
- Row 1 — Single-value: ULA flows on perimeter in last 24h (target: 0).
- Row 2 — Table: ULA leakage events with classification.
- Row 3 — Configuration compliance: devices missing ULA perimeter filters.
- Row 4 — Trend: ULA leakage events over 30 days.

**Alert:** Any ULA traffic on perimeter interface — high severity.

**Runbook:**
1. ULA egress leak: Add `deny ipv6 fc00::/7 any` to perimeter ACL. Investigate source device for routing misconfiguration.
2. ULA ingress leak: Add `deny ipv6 any fc00::/7` to perimeter ACL. This is unexpected — investigate potential route injection.
3. fc00::/8 traffic: This address block is unassigned and should never appear. Investigate source immediately.

### Step 5 — Troubleshooting

- **ULA in dual-stack environments.** Organisations sometimes use ULA alongside GUA for internal communication stability (ULA doesn't change when ISP changes). Verify ULA is used intentionally and properly contained.

- **ULA and NPTv6.** Network Prefix Translation for IPv6 (RFC 6296) can translate ULA to GUA at the perimeter. If NPTv6 is in use, ULA traffic at the perimeter pre-translation is expected.

- **fc00::/8 vs fd00::/8.** Only fd00::/8 is currently used. The fc00::/8 block was reserved for a proposed central assignment authority that was never created. Any fc00::/8 traffic is suspicious.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="netflow" OR sourcetype="cisco:asa") earliest=-24h
| eval src_ula=if(match(src, "^[Ff][CcDd]"), 1, 0)
| eval dst_ula=if(match(dest, "^[Ff][CcDd]"), 1, 0)
| where src_ula=1 OR dst_ula=1
| eval interface_type=coalesce(ingress_zone, inbound_if, "unknown")
| eval direction=case(
    src_ula=1 AND dst_ula=0, "ULA source to non-ULA destination (EGRESS LEAK)",
    src_ula=0 AND dst_ula=1, "Non-ULA source to ULA destination (INGRESS LEAK)",
    src_ula=1 AND dst_ula=1, "ULA-to-ULA (internal, expected on site-to-site VPN)",
    1=1, "unknown")
| lookup perimeter_interfaces.csv interface as interface_type OUTPUT is_perimeter
| where is_perimeter="yes"
| stats count as events sum(bytes) as total_bytes dc(src) as unique_sources dc(dest) as unique_dests by host, direction
| eval alert=direction . " — " . events . " flows, " . unique_sources . " sources, " . round(total_bytes/1048576, 1) . " MB on perimeter device " . host
| sort -events
```

## Visualization

(1) Single-value: ULA flows on perimeter (target: 0). (2) Table: ULA leakage events with source, destination, and volume. (3) Timechart: ULA leakage over 24 hours. (4) Map: perimeter interfaces with ULA leakage highlighted.

## Known False Positives

**Site-to-site VPN with ULA.** Organisations using ULA for internal inter-site communication over VPN tunnels will see ULA traffic on VPN interfaces. This is legitimate if the VPN is between the organisation's own sites. Exclude VPN tunnel interfaces from perimeter monitoring.

**ULA in NAT64 environments.** Some NAT64 deployments use ULA for the internal IPv6 addressing. Verify NAT is translating ULA to GUA before traffic reaches the perimeter.

**Lab/test networks.** Development and test environments may use ULA and occasionally leak traffic to production perimeters.

## References

- [RFC 4193 — Unique Local IPv6 Unicast Addresses](https://www.rfc-editor.org/rfc/rfc4193)
- [DISA STIG NET-IPV6-032 — ULA must be filtered at external perimeters](https://public.cyber.mil/stigs/)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4.2 — address filtering)](https://www.rfc-editor.org/rfc/rfc9099)
