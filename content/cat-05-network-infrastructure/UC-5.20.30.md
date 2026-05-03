<!-- AUTO-GENERATED from UC-5.20.30.json — DO NOT EDIT -->

---
id: "5.20.30"
title: "DHCPv6 Guard Enforcement Coverage Audit"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.30 · DHCPv6 Guard Enforcement Coverage Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Just as we check that every door has a lock against fake routers (RA Guard), we also check that every door has a lock against fake address servers. A rogue address server can trick devices into using wrong settings, like a con artist handing out fake maps. We make sure every network port is protected against this trick.*

---

## Description

Audits DHCPv6 Guard (RFC 7610) deployment coverage across all access-facing switch ports. DHCPv6 Guard prevents rogue DHCPv6 servers from responding to client requests on access ports — only ports explicitly marked as 'server' or 'trusted' are allowed to send DHCPv6 server messages (ADVERTISE, REPLY, RECONFIGURE). This is the DHCPv6 equivalent of DHCP Snooping in IPv4, but it is frequently not deployed because many organisations assume DHCP Snooping covers both IPv4 and IPv6. It does not — DHCP Snooping only inspects DHCPv4 messages. DHCPv6 Guard is a separate feature that must be explicitly enabled.

On Cisco IOS-XE, DHCPv6 Guard is automatically enabled when SISF is configured with `security-level guard`. On Juniper and Arista, it requires separate configuration.

## Value

A rogue DHCPv6 server can compromise all hosts on a VLAN that use DHCPv6 for addressing or configuration. Even on SLAAC-only networks (M=0, O=1), hosts still query DHCPv6 for DNS servers and domain names. A rogue server can inject malicious DNS resolvers, enabling DNS-based attacks (phishing, credential theft) against every host on the VLAN. Unlike RA Guard (which protects address autoconfiguration), DHCPv6 Guard protects the configuration parameters that hosts receive via DHCPv6. Both controls are needed for comprehensive first-hop security.

## Implementation

Collect running configurations from all switches. Parse interface configurations to identify access ports and check for DHCPv6 Guard policy attachment (either explicit `ipv6 nd dhcpv6-guard` or implicit via SISF `device-tracking` with `security-level guard`). Calculate coverage per switch and alert on gaps.

## Detailed Implementation

### Prerequisites
- Access to running configurations from all access-layer switches (same collection mechanism as UC-5.20.29).
- Understanding of SISF/device-tracking policy inheritance: on Cisco IOS-XE, SISF with `security-level guard` provides both RA Guard and DHCPv6 Guard automatically.

### Step 1 — Configure data collection

Use the same configuration collection script as UC-5.20.29. The DHCPv6 Guard audit parses the same running configuration data.

**Cisco IOS-XE DHCPv6 Guard deployment (reference):**

Option A — Explicit DHCPv6 Guard:
```
ipv6 nd dhcpv6-guard policy DHCPV6_CLIENT
 device-role client
!
ipv6 nd dhcpv6-guard policy DHCPV6_SERVER
 device-role server
!
interface range GigabitEthernet1/0/1 - 48
 ipv6 nd dhcpv6-guard attach-policy DHCPV6_CLIENT
!
interface GigabitEthernet1/0/49
 ipv6 nd dhcpv6-guard attach-policy DHCPV6_SERVER
```

Option B — Implicit via SISF (recommended — covers RA Guard + DHCPv6 Guard + more):
```
device-tracking policy DT_GUARD
 security-level guard
 tracking enable
!
interface range GigabitEthernet1/0/1 - 48
 device-tracking attach-policy DT_GUARD
```

**Verification:**
```
show ipv6 nd dhcpv6-guard policy DHCPV6_CLIENT
  Device Role: client
```

### Step 2 — Create the search and alert

**Primary audit — DHCPv6 Guard coverage per switch:**
Use the same approach as UC-5.20.29 but check for DHCPv6 Guard patterns:
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?ms)(?:^|\n)interface\s+(?<iface>(?:Gi|Te|Tw|Fa)\S+)(?<iface_config>[\s\S]*?)(?=\ninterface\s|\n!|$)"
| eval combined=mvzip(iface, iface_config, "|||")
| mvexpand combined
| rex field=combined "(?<interface>[^|]+)\|\|\|(?<config>.+)"
| eval is_access=if(match(config, "switchport mode access"), 1, 0)
| eval has_dhcpv6_guard=if(match(config, "dhcpv6-guard|dhcp-guard|device-tracking.*guard"), 1, 0)
| where is_access=1
| stats sum(has_dhcpv6_guard) as protected sum(eval(1-has_dhcpv6_guard)) as unprotected by host
| eval total=protected + unprotected
| eval coverage_pct=round(protected / total * 100, 1)
| eval status=case(
    coverage_pct=100, "COMPLIANT",
    coverage_pct >= 90, "NEAR-COMPLIANT",
    1=1, "NON-COMPLIANT")
| sort coverage_pct
| table host, protected, unprotected, total, coverage_pct, status
```

**Combined FHS coverage comparison (RA Guard + DHCPv6 Guard):**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?ms)(?:^|\n)interface\s+(?<iface>(?:Gi|Te|Tw|Fa)\S+)(?<iface_config>[\s\S]*?)(?=\ninterface\s|\n!|$)"
| eval combined=mvzip(iface, iface_config, "|||")
| mvexpand combined
| rex field=combined "(?<interface>[^|]+)\|\|\|(?<config>.+)"
| eval is_access=if(match(config, "switchport mode access"), 1, 0)
| eval has_raguard=if(match(config, "raguard"), 1, 0)
| eval has_dhcpv6_guard=if(match(config, "dhcpv6-guard|dhcp-guard|device-tracking.*guard"), 1, 0)
| where is_access=1
| stats sum(has_raguard) as ra_protected sum(has_dhcpv6_guard) as dhcpv6_protected count as total by host
| eval ra_pct=round(ra_protected / total * 100, 1)
| eval dhcpv6_pct=round(dhcpv6_protected / total * 100, 1)
| eval parity=if(ra_pct==dhcpv6_pct, "YES", "NO — deploy both together")
```

### Step 3 — Validate
(a) **Spot-check** 3 switches against `show ipv6 nd dhcpv6-guard policy` and `show device-tracking policies`.
(b) **SISF implicit coverage.** On a switch with `device-tracking policy` in `guard` mode, verify the audit correctly counts DHCPv6 Guard as deployed (even without explicit `dhcpv6-guard` directive).
(c) **Gap test.** Remove DHCPv6 Guard from one access port, re-run audit, verify the gap is detected.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — First-Hop Security Coverage"):
- Row 1 — Dual single-value: RA Guard coverage % and DHCPv6 Guard coverage %.
- Row 2 — Combined table: per-switch RA Guard and DHCPv6 Guard coverage with parity check.
- Row 3 — Unprotected ports list: interface-level detail for non-compliant switches.

**Scheduling:** Daily audit. Alert on any switch with <100% coverage.

**Runbook:**
1. DHCPv6 Guard gap detected: apply the SISF policy (which provides both RA Guard and DHCPv6 Guard) to the unprotected interfaces.
2. Parity gap (RA Guard deployed but not DHCPv6 Guard): this usually means the switch uses explicit RA Guard policies instead of SISF. Add DHCPv6 Guard policies or migrate to SISF.

### Step 5 — Troubleshooting

- **DHCPv6 Guard blocking legitimate server traffic** — The DHCPv6 server or relay agent port must be configured as `device-role server`. If it is incorrectly set to `client`, legitimate DHCPv6 responses are dropped and hosts cannot obtain DHCPv6 configuration.

- **SISF security-level 'glean' vs 'guard'** — `security-level glean` collects binding information but does NOT enforce DHCPv6 Guard. Only `security-level guard` or `inspect` actually blocks rogue DHCPv6 servers. The audit must specifically check for `guard` or `inspect` mode.

- **DHCPv6 Guard not supported on all platforms** — Some older Catalyst switches (2960-S, 3560) have limited SISF support. Check platform capability and document hardware limitations.

## SPL

```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?ms)(?:^|\n)interface\s+(?<iface>(?:Gi|Te|Tw|Fa)\S+)(?<iface_config>[\s\S]*?)(?=\ninterface\s|\n!|$)"
| eval combined=mvzip(iface, iface_config, "|||")
| mvexpand combined
| rex field=combined "(?<interface>[^|]+)\|\|\|(?<config>.+)"
| eval is_access=if(match(config, "switchport mode access"), 1, 0)
| eval has_dhcpv6_guard=if(match(config, "dhcp-guard|dhcpv6-guard|device-tracking.*guard"), 1, 0)
| where is_access=1
| stats sum(has_dhcpv6_guard) as protected sum(eval(1-has_dhcpv6_guard)) as unprotected by host
| eval coverage_pct=round(protected / (protected + unprotected) * 100, 1)
| eval status=case(
    coverage_pct=100, "COMPLIANT",
    coverage_pct >= 80, "PARTIAL",
    1=1, "NON-COMPLIANT")
| sort coverage_pct
```

## Visualization

(1) Single-value: network-wide DHCPv6 Guard coverage %. (2) Table: per-switch coverage with protected/unprotected port counts. (3) Comparison chart: RA Guard vs DHCPv6 Guard coverage side-by-side. (4) Drilldown: list of unprotected access ports per switch.

## Known False Positives

**SISF implicitly enables DHCPv6 Guard.** On Cisco IOS-XE, `device-tracking policy` with `security-level guard` automatically enables both RA Guard and DHCPv6 Guard. The configuration may not show an explicit `ipv6 nd dhcpv6-guard` directive — the protection is inherited from the device-tracking policy. The audit search must check for both explicit DHCPv6 Guard and implicit SISF `guard` mode.

**VLANs without DHCPv6.** If a VLAN uses SLAAC-only addressing (M=0, O=0, A=1) with no DHCPv6 server, DHCPv6 Guard is still valuable — it prevents a rogue server from answering unsolicited. However, the risk is lower because hosts are not actively seeking DHCPv6.

**Ports connecting to legitimate DHCPv6 relay agents.** These ports must be configured as 'server' role in the DHCPv6 Guard policy, not as 'client'. If misconfigured, legitimate DHCPv6 traffic is blocked.

## References

- [RFC 7610 — DHCPv6-Shield: Protecting Against Rogue DHCPv6 Servers](https://www.rfc-editor.org/rfc/rfc7610)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2.5 — DHCPv6 Guard recommendation)](https://www.rfc-editor.org/rfc/rfc9099)
- [Cisco SISF Configuration Guide — DHCPv6 Guard as part of device-tracking](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sisf/configuration/xe-17/sisf-xe-17-book.html)
