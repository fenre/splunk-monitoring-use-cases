<!-- AUTO-GENERATED from UC-5.20.82.json — DO NOT EDIT -->

---
id: "5.20.82"
title: "IPv6 Anti-Spoofing (uRPF/BCP 38) Verification"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.82 · IPv6 Anti-Spoofing (uRPF/BCP 38) Verification

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*When you receive a letter (packet), you check the return address against your address book (routing table). If no one at that address could have sent the letter through this mailbox (interface), the return address must be fake (spoofed). We make sure every post office (router) is checking return addresses, and we track when fake ones are caught.*

---

## Description

Verifies that Unicast Reverse Path Forwarding (uRPF) anti-spoofing protection is active on all IPv6-enabled interfaces and analyses uRPF drop events to characterise spoofing attempts. BCP 38 (RFC 2827/3704) mandates source address validation to prevent IP spoofing. IPv6 makes anti-spoofing even more critical than IPv4 because there is no NAT to provide accidental source validation, and globally routable addresses are used directly by hosts.

## Value

Source address spoofing is the foundation of DDoS reflection/amplification attacks, NDP cache poisoning, and network reconnaissance evasion. Without uRPF, an attacker on any IPv6 subnet can forge packets from any global unicast address. uRPF verification ensures this critical control is deployed fleet-wide, and drop analysis provides visibility into active spoofing attempts. The combination of deployment verification and drop analysis closes both the prevention and detection gaps.

## Implementation

Verify uRPF is configured on all IPv6 interfaces via configuration audit. Monitor uRPF drop events for spoofing detection. Alert on link-local or ULA sources appearing in routed traffic.

## Detailed Implementation

### Prerequisites
- IPv6 routing table on all border and distribution routers.
- Configuration collection infrastructure.
- Understanding of network topology for choosing strict vs loose vs feasible-path uRPF.

### Step 1 — Configure data collection

**Configuration audit for uRPF deployment:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| rex field=_raw max_match=0 "interface\s+(?<interface>\S+).*?ipv6 verify unicast source reachable-via (?<urpf_mode>rx|any)"
| eval urpf_interfaces=mvcount(interface)
| rex field=_raw max_match=0 "interface\s+(?<all_interfaces>\S+).*?ipv6 enable"
| eval ipv6_interfaces=mvcount(all_interfaces)
| eval coverage_pct=round(urpf_interfaces / ipv6_interfaces * 100, 0)
| eval status=case(
    coverage_pct=100, "FULL COVERAGE",
    coverage_pct >= 80, "GOOD — " . (ipv6_interfaces - urpf_interfaces) . " interfaces missing uRPF",
    1=1, "POOR — " . (ipv6_interfaces - urpf_interfaces) . " interfaces unprotected")
| table host, ipv6_interfaces, urpf_interfaces, coverage_pct, status
| sort coverage_pct
```

**Cisco IOS/IOS-XE uRPF configuration:**
```
interface GigabitEthernet0/0
 ipv6 verify unicast source reachable-via rx   ! strict mode
!
interface GigabitEthernet0/1
 ipv6 verify unicast source reachable-via any  ! loose mode (multi-homed)
```

**Juniper JunOS equivalent:**
```
set interfaces ge-0/0/0 unit 0 family inet6 rpf-check
```

**Verification:**
```spl
index=network sourcetype="cisco:ios:config" "ipv6 verify unicast" | stats count by host
```

### Step 2 — Create monitoring search

**uRPF drop event monitoring:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-1h
  ("rpf" OR "reverse-path" OR "unicast RPF" OR "%IPV6-4-URPF")
| rex field=_raw "(?:src|source)\s*=?\s*(?<spoofed_src>[0-9a-fA-F:.]+)"
| eval scope=case(
    match(spoofed_src, "^[Ff][Ee][89AaBb]"), "link-local (ALWAYS invalid in routed traffic)",
    match(spoofed_src, "^[Ff][CcDd]"), "ULA (should not cross perimeter)",
    match(spoofed_src, "^3[Ff][Ff][Ee]"), "6bone (decommissioned)",
    match(spoofed_src, "^2001:[Dd][Bb]8:"), "documentation prefix",
    1=1, "global unicast (RIB mismatch)")
| timechart span=5m count by scope
```

### Step 3 — Validate
(a) **Deployment verification.** SSH to 3 sample routers across tiers. Run `show ipv6 interface <intf> | include verify` and confirm uRPF mode matches SPL results.

(b) **Drop verification.** On a test interface with strict uRPF, generate traffic with a spoofed source address from a different subnet. Verify the drop is logged and appears in Splunk.

(c) **False positive check.** On multi-homed interfaces using strict mode, verify no legitimate traffic is being dropped. If drops occur for valid sources, switch to loose or feasible-path mode.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Anti-Spoofing Coverage"):
- Row 1 — Single-value: uRPF coverage percentage across all IPv6 interfaces.
- Row 2 — Table: devices with missing uRPF, sorted by exposure risk.
- Row 3 — Timechart: uRPF drops over 24 hours by category.
- Row 4 — Table: top spoofed source addresses with characterisation.

**Alert:** Link-local or ULA source address in routed traffic — always a spoofing indicator. Critical severity.

**Runbook:**
1. Missing uRPF on edge interface: Deploy `ipv6 verify unicast source reachable-via rx` (strict). Test for 24 hours in monitor mode before enforcing.
2. Excessive drops on multi-homed interface: Switch from strict to loose mode. Verify asymmetric routing is the cause.
3. Spike in drops from new source prefix: Investigate whether this is a new spoofing campaign or a legitimate routing change.

### Step 5 — Troubleshooting

- **Platform-specific logging.** Not all platforms log uRPF drops to syslog by default. On Cisco IOS, uRPF drops may require `ip verify unicast source reachable-via rx allow-default` with explicit logging ACL. On NX-OS, use `logging level ipv6 6`.

- **CEF/FIB dependency.** uRPF requires a populated FIB. If CEF is disabled or the IPv6 FIB is incomplete (e.g., during convergence), uRPF may drop legitimate traffic. Monitor BGP/OSPF convergence alongside uRPF drops.

- **Default route interaction.** With `allow-default`, loose uRPF permits any source that matches the default route. Without it, hosts behind default routes are blocked. Choose based on deployment scenario.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") ("%IPV6_ACL-6-ACCESSLOGP" OR "%IOSXE-6-PLATFORM" OR "rpf-check" OR "urpf") earliest=-24h
| eval is_urpf_drop=if(match(_raw, "(?i)rpf.?(check|fail|drop)|urpf|reverse.?path"), 1, 0)
| where is_urpf_drop=1
| rex field=_raw "(?:src|source)\s*=?\s*(?<spoofed_src>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:interface|IF)\s+(?<ingress_interface>\S+)"
| eval spoof_type=case(
    match(spoofed_src, "^[Ff][Ee][89AaBb]"), "link-local source in routed traffic — ALWAYS spoofed",
    match(spoofed_src, "^[Ff][CcDd]"), "ULA source at perimeter — policy violation",
    match(spoofed_src, "^::$"), "unspecified address (::) — misconfiguration or attack",
    match(spoofed_src, "^::1$"), "loopback address — always spoofed in transit",
    1=1, "global unicast source not in RIB for ingress interface")
| stats count as drops first(_time) as first last(_time) as last by host, ingress_interface, spoofed_src, spoof_type
| sort -drops
```

## Visualization

(1) Single-value: interfaces with uRPF enabled vs total IPv6 interfaces. (2) Table: uRPF drop events with source, interface, and characterisation. (3) Timechart: uRPF drops over time by category. (4) Map: geographic origin of spoofed source addresses (using IPFIX).

## Known False Positives

**Asymmetric routing.** Strict uRPF will drop legitimate traffic on interfaces with asymmetric routing paths. Use loose or feasible-path mode on multi-homed interfaces.

**Floating static routes.** Backup routes that are not in the active RIB may cause strict uRPF to drop traffic during failover. Feasible-path mode resolves this by considering backup routes.

**VRF leaking.** Traffic leaked between VRFs may have source addresses not present in the ingress VRF's RIB. Configure per-VRF uRPF or use loose mode on VRF interconnection points.

## References

- [RFC 3704 — Ingress Filtering for Multihomed Networks (BCP 84, extends BCP 38)](https://www.rfc-editor.org/rfc/rfc3704)
- [RFC 2827 — Network Ingress Filtering: Defeating Denial of Service Attacks which employ IP Source Address Spoofing (BCP 38)](https://www.rfc-editor.org/rfc/rfc2827)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4.1 — ingress filtering)](https://www.rfc-editor.org/rfc/rfc9099)
- [MANRS — Mutually Agreed Norms for Routing Security (requires anti-spoofing)](https://www.manrs.org/)
