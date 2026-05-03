<!-- AUTO-GENERATED from UC-5.20.25.json — DO NOT EDIT -->

---
id: "5.20.25"
title: "NDP Redirect Message Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.25 · NDP Redirect Message Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*Sometimes a router says, 'Actually, your neighbour across the street can deliver that package faster than I can — go through them instead.' This is usually helpful, but a bad actor could trick your computer into sending everything through them. We watch for these redirections, especially when they come from someone who is not actually a router.*

---

## Description

Monitors ICMPv6 Type 137 Redirect messages on the network. Redirects are intended to optimise routing by telling a host to use a different next-hop for a specific destination, but they can be exploited for man-in-the-middle attacks. An attacker sends a forged Redirect message claiming that traffic to a target destination should be sent through the attacker's link-local address instead of the legitimate router. Unlike IPv4 ICMP Redirects (which are commonly disabled), IPv6 Redirects are processed by default on most operating systems and are harder to disable without breaking legitimate NDP. This use case monitors the rate and source of Redirect messages to detect both misconfiguration (excessive redirects indicating suboptimal routing) and attacks (redirects from non-router sources).

## Value

IPv6 Redirect attacks are often overlooked because many network engineers assume that Redirect behaviour is the same as in IPv4. In IPv6, Redirect processing is enabled by default on all major operating systems (Windows, Linux, macOS) and cannot be disabled as easily as IPv4 ICMP Redirect rejection. An attacker on the same VLAN can redirect specific traffic flows (e.g., DNS queries, authentication traffic) through their own host without being the default gateway — making the attack stealthier than rogue RA attacks. Monitoring Redirect messages provides detection for this class of attack and also identifies routing misconfigurations where Redirects indicate suboptimal default gateway placement.

## Implementation

Monitor ICMPv6 Type 137 messages via Zeek (network TAP) or router syslog. Maintain a whitelist of legitimate Redirect sources (routers only). Alert on Redirects from non-router sources, excessive Redirect rates, or Redirects targeting critical destinations (DNS, authentication servers).

## Detailed Implementation

### Prerequisites
- Zeek or Suricata deployed on network TAP/SPAN for ICMPv6 Type 137 monitoring.
- A whitelist of legitimate router link-local addresses per VLAN.
- Understanding of intended routing topology: single-router VLANs should have zero Redirects; multi-router VLANs may have occasional legitimate Redirects.

### Step 1 — Configure data collection

**Zeek (primary):**
Zeek decodes ICMPv6 Type 137 and logs: source IP, destination IP (host being redirected), target address (better next-hop), and destination address (the destination being redirected). Forward to Splunk with `sourcetype=corelight_zeek`.

**Cisco IOS syslog (complementary):**
Enable IPv6 ND redirect logging:
```
interface Vlan100
 ipv6 redirects
```
Redirects generate `%IPV6_ND-6-REDIRECT` syslog events.

To disable Redirects on interfaces where they should not occur (single-router VLANs):
```
interface Vlan100
 no ipv6 redirects
```

**On hosts (Linux — disable Redirect acceptance for security):**
```bash
sysctl -w net.ipv6.conf.all.accept_redirects=0
sysctl -w net.ipv6.conf.default.accept_redirects=0
```

**Verification:**
```spl
index=network (sourcetype="corelight_zeek" icmpv6_type=137) OR (sourcetype="cisco:ios" "REDIRECT" "IPV6_ND") earliest=-7d
| stats count
```

### Step 2 — Create the search and alert

**Primary search — Redirect monitoring:**
```spl
index=network (sourcetype="corelight_zeek" icmpv6_type=137)
  OR (sourcetype="cisco:ios" "%IPV6_ND" "REDIRECT")
  earliest=-24h
| rex field=_raw "src[= ]+(?<redirect_source>[0-9a-fA-F:]+)"
| rex field=_raw "target[= ]+(?<better_nexthop>[0-9a-fA-F:]+)"
| rex field=_raw "dest[= ]+(?<redirected_dest>[0-9a-fA-F:]+)"
| lookup ipv6_authorised_routers.csv link_local_ip as redirect_source OUTPUT authorised
| eval from_router=if(authorised="true", "YES", "NO")
| eval severity=case(
    from_router="NO", "CRITICAL — Redirect from non-router source",
    1=1, "INFO — Redirect from known router")
| stats count as redirect_count by redirect_source, from_router, severity, better_nexthop
| sort -severity, -redirect_count
```

**Alert — Redirect from non-router source (probable attack):**
```spl
index=network (sourcetype="corelight_zeek" icmpv6_type=137) earliest=-15m
| rex field=_raw "src[= ]+(?<redirect_source>[0-9a-fA-F:]+)"
| lookup ipv6_authorised_routers.csv link_local_ip as redirect_source OUTPUT authorised
| where isnull(authorised) OR authorised!="true"
```
Trigger: any result. Priority: CRITICAL. A Redirect from a non-router source is a strong indicator of a man-in-the-middle attack.

### Step 3 — Validate
(a) **Zero-Redirect baseline.** On single-router VLANs, verify zero Redirect events over 7 days. Any Redirect on a single-router VLAN is either a misconfiguration or an attack.

(b) **Legitimate Redirect test.** On a multi-router VLAN, send traffic to a destination reachable via a non-default-gateway router. The default gateway should send a Redirect pointing to the better next-hop. Verify the event appears in Splunk with `from_router=YES`.

(c) **Whitelist validation.** Confirm all legitimate routers are in the `ipv6_authorised_routers.csv` lookup.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Redirect Monitoring"):
- Row 1 — Single-value: total Redirects (24h), Redirects from non-router sources.
- Row 2 — Table: Redirect details with source, better-nexthop, severity, router verification.
- Row 3 — Timechart: Redirect rate over time — spikes indicate either attack or routing change.

**Scheduling:** Real-time alert for non-router Redirects. Hourly rate check.

**Runbook:**
1. CRITICAL — Redirect from non-router: locate the source MAC on the switch (`show mac address-table address <mac>`), shut the port, investigate.
2. INFO — excessive Redirects from router: review routing topology — is the default gateway placement optimal? If not, add a second VRRP group or adjust routing.

### Step 5 — Troubleshooting

- **No Redirect events visible** — Redirects are relatively rare on well-designed networks. If your network has single-router VLANs with VRRP/HSRP, Redirects should be genuinely absent. Verify Zeek is capturing ICMPv6 on the correct SPAN port.

- **Redirects disabled on router** — `no ipv6 redirects` on the interface prevents the router from sending Redirects. This is a common hardening recommendation but means you lose the optimisation benefit on multi-router VLANs.

- **Hosts ignoring Redirects** — Some hosts (hardened Linux, security-focused OS configurations) have `accept_redirects=0`, meaning they ignore Redirects. The Redirect is still sent by the router/attacker and logged by Zeek, but it has no effect on the host.

## SPL

```spl
index=network (sourcetype="cisco:ios" "%IPV6_ND" "REDIRECT")
  OR (sourcetype="corelight_zeek" icmpv6_type=137)
| stats count as redirect_count values(src_ip) as sources values(dest_ip) as targets by host, vlan
| where redirect_count > 0
| eval assessment=case(
    redirect_count > 50, "WARNING — excessive redirects, possible attack",
    redirect_count > 10, "INFO — elevated redirect rate",
    1=1, "LOW — occasional redirects")
| sort -redirect_count
```

## Visualization

(1) Timechart: Redirect messages over time — should be near-zero on well-designed networks. (2) Table: Redirect details — source, target destination, better next-hop. (3) Single-value: total Redirects in 24 hours. (4) Alert panel: Redirects from non-router sources.

## Known False Positives

**Multi-router VLAN with asymmetric routing.** When a VLAN has two routers and the default gateway is not the optimal next-hop for certain destinations, the default gateway sends Redirects to hosts for those specific destinations. This is legitimate NDP behaviour. Verify by checking if the Redirect sources are known router IPs and the 'better next-hop' is also a known router.

**Router reboot or VRRP transition.** During a transition, the new active router may send Redirects for destinations that the old active was directly handling. This is transient.

**Static routes on hosts.** Hosts with static IPv6 routes to non-default-gateway routers will trigger Redirects from the default gateway pointing to the correct next-hop. This is by design.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (§8 — Redirect Function)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.3 — Redirect security implications)](https://www.rfc-editor.org/rfc/rfc9099)
- [THC-IPv6 Attack Toolkit — redir6 redirect attack tool](https://github.com/vanhauser-thc/thc-ipv6)
