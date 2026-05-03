<!-- AUTO-GENERATED from UC-5.20.21.json — DO NOT EDIT -->

---
id: "5.20.21"
title: "Router Advertisement Anomaly Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.21 · Router Advertisement Anomaly Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Threat Detection &middot; **Wave:** Walk &middot; **Status:** Verified

*On an IPv6 network, a special announcement called a 'Router Advertisement' tells all devices where the exit to the internet is, like a sign saying 'This way out.' If someone puts up a fake sign pointing to their own house instead, they can intercept everyone's traffic. We watch for any fake signs that appear and immediately alert the security team.*

---

## Description

Detects rogue Router Advertisements on the network — the single most dangerous IPv6-specific attack. A rogue RA can redirect all host traffic to an attacker-controlled 'router', assign a malicious prefix that routes through the attacker, change DNS servers to point to a malicious resolver, or set address configuration flags that disrupt connectivity. Unlike IPv4 where DHCP snooping protects against rogue DHCP, IPv6 RA protection (RA Guard, RFC 6105) is frequently not deployed, leaving networks vulnerable. This use case detects rogue RAs through two independent signals: RA Guard violation logs (SISF PAK_DROP with Reason:RA guard) on switches where RA Guard is deployed, and network TAP/SPAN analysis (Zeek) for networks without RA Guard. It also detects excessive RA rates that may indicate a flooding attack designed to overwhelm host RA processing (each RA triggers prefix evaluation, address generation, and potentially DHCPv6 queries).

## Value

A single rogue RA can compromise an entire VLAN. Unlike DHCP-based attacks in IPv4 where hosts must actively request an address, IPv6 RAs are unsolicited — all hosts on the VLAN automatically process them. An attacker can redirect default gateways, inject malicious prefixes, and change DNS servers with a single multicast packet. The THC-IPv6 toolkit includes `fake_router6` which automates this attack. Without monitoring, rogue RAs can persist for hours or days, especially when they come from misconfigured devices rather than deliberate attacks. This use case provides both prevention (RA Guard) and detection (monitoring) layers.

## Implementation

Deploy RA Guard on all access-facing switch ports (UC-5.20.29). Monitor RA Guard violation events (PAK_DROP with RA guard reason) in Splunk. Deploy Zeek or Suricata on network TAPs to decode ICMPv6 Type 134 as a secondary detection layer. Alert on any RA from non-whitelisted sources, excessive RA rates, or RA content anomalies (unexpected prefix, changed flags).

## Detailed Implementation

### Prerequisites
- RA Guard deployed on access-layer switches (see UC-5.20.29 for coverage audit). Without RA Guard, rogue RAs are not blocked, only detected.
- A whitelist of legitimate RA sources: for each VLAN, the MAC addresses and link-local IPv6 addresses of authorised routers. This is typically 1-2 MACs per VLAN (primary + VRRP/HSRP standby).
- Network TAP or SPAN capability for Zeek/Suricata deployment as a secondary detection layer.

### Step 1 — Configure data collection

**RA Guard syslog (primary detection on Cisco IOS-XE):**

RA Guard must be deployed first. On Cisco IOS-XE:
```
ipv6 nd raguard policy RA_FROM_ROUTER
 device-role router
!
ipv6 nd raguard policy RA_FROM_HOST
 device-role host
!
interface GigabitEthernet1/0/1
 description Uplink to Router
 ipv6 nd raguard attach-policy RA_FROM_ROUTER
!
interface range GigabitEthernet1/0/2 - 48
 description Access Ports
 ipv6 nd raguard attach-policy RA_FROM_HOST
```

When a host port sends an RA, RA Guard drops it and generates:
```
%SISF-4-PAK_DROP: from port Gi1/0/15 interface Vlan100,
  Packet dropped, Reason:RA guard policy - rogue router advertisement
  IPv6 SRC: fe80::bad:cafe:dead:beef, IPv6 DST: ff02::1
```

These events are forwarded to Splunk via the Cisco IOS TA.

**On Juniper EX/QFX:**
```
set protocols router-advertisement interface ge-0/0/0.0 managed-configuration
set switch-options ip-source-guard-enabled
```
Juniper logs blocked RAs as `RTADV_GUARD_BLOCKED` in syslog.

**Zeek/Corelight (secondary detection layer):**

Zeek decodes every ICMPv6 Type 134 on the monitored segment and logs RA details including source MAC, source IPv6, prefix, flags, and lifetimes. Deploy Zeek on a network TAP or SPAN port covering VLAN trunks or access-layer uplinks.

Zeek generates events in `icmp.log` for ICMPv6 Type 134. Forward to Splunk with `sourcetype=corelight_zeek`.

**Verification:**
```spl
index=network ("PAK_DROP" "RA guard") OR (sourcetype="corelight_zeek" icmpv6_type=134) earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Alert 1 — Rogue RA blocked by RA Guard (real-time):**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" "RA guard"
| rex field=_raw "port\s+(?<src_port>\S+)\s+interface\s+(?<vlan>\S+)"
| rex field=_raw "IPv6 SRC:\s+(?<ra_source_ip>[0-9a-fA-F:]+)"
| stats count as drop_count values(ra_source_ip) as attacker_ips values(src_port) as ports latest(_time) as last_event by host, vlan
| eval last_event=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort -drop_count
```
Trigger: any result. Priority: HIGH. Action: PagerDuty + email to network security team.

**Alert 2 — Excessive RA rate from any source (potential RA flood):**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-10m
| stats count as ra_count by src_ip, src_mac
| where ra_count > 30
| eval anomaly="EXCESSIVE_RA_RATE: " . ra_count . " RAs in 10 minutes from " . src_ip
```
Normal: ~3 RAs per 10 minutes (1 per 200 seconds default). >30 in 10 minutes = 1 per 20 seconds, which is either a flooding attack or a severely misconfigured router.

**Alert 3 — RA from non-whitelisted source:**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-1h
| lookup ipv6_authorised_ra_sources.csv src_mac OUTPUT authorised
| where isnull(authorised) OR authorised!="true"
| stats count as ra_count values(src_ip) as sources values(src_mac) as macs by vlan
| sort -ra_count
```
The `ipv6_authorised_ra_sources.csv` lookup maps each VLAN to the MAC addresses of its legitimate routers. Any RA from an unlisted MAC is a rogue.

**RA content anomaly detection:**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-24h
| rex field=_raw "prefix=(?<ra_prefix>[0-9a-fA-F:]+/\d+)"
| lookup ipv6_prefix_plan.csv prefix as ra_prefix OUTPUT expected
| where isnull(expected)
| eval anomaly="UNEXPECTED_PREFIX: " . ra_prefix . " advertised by " . src_ip
| table _time, src_ip, src_mac, ra_prefix, anomaly
```
Detects RAs advertising prefixes not in your IPAM plan — strong indicator of a rogue or misconfigured router.

### Step 3 — Validate
(a) **Controlled rogue RA test (lab only).** On a test VLAN with RA Guard, connect a Linux laptop and enable IPv6 forwarding:
```bash
sudo sysctl net.ipv6.conf.eth0.forwarding=1
sudo radvd   # or: sudo fake_router6 eth0
```
Verify: RA Guard drops the RA and generates PAK_DROP events in Splunk. If Zeek is monitoring, it should also log the ICMPv6 Type 134.

(b) **RA rate test.** Use `rdisc6 -m eth0` (from ndisc6 package) to send rapid Router Solicitations, causing legitimate routers to respond with RAs at their minimum interval. Verify the excessive-rate alert does NOT fire for normal RA rates from whitelisted sources.

(c) **Whitelist validation.** Confirm that legitimate router RAs are NOT flagged by the non-whitelisted source alert. Run: `| inputlookup ipv6_authorised_ra_sources.csv` and verify completeness.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RA Security"):
- Row 1 — Single-value: rogue RAs blocked (24h), unverified RAs detected, VLANs without RA Guard.
- Row 2 — Table: rogue RA events with source port, VLAN, source MAC, timestamp, and frequency.
- Row 3 — Timechart: RA events by type (legitimate vs blocked vs unverified) over time.
- Row 4 — RA content summary: all active prefixes being advertised, by which router, with which flags. Unexpected prefixes highlighted.

**Scheduling:** Real-time alert for RA Guard violations (PAK_DROP). Every 10 minutes for excessive RA rate. Every hour for non-whitelisted source check.

**Runbook:**
1. Rogue RA detected:
   a. Identify the source port from the PAK_DROP event.
   b. Check the switch: `show mac address-table interface <port>` to find the device MAC.
   c. If the MAC belongs to a user laptop: contact the user, disable IPv6 forwarding or Internet Connection Sharing.
   d. If the MAC is unknown: shut the port immediately (potential deliberate attack).
   e. If RA Guard is NOT deployed on the affected VLAN: escalate to deploy RA Guard (UC-5.20.29).
2. Excessive RA rate from legitimate router:
   a. Check the router RA interval configuration: `show ipv6 interface <vlan> | include RA`.
   b. If interval is too low (<30 seconds), increase to 200 seconds (default).
   c. If the router is under load (many Router Solicitations), this may be normal — RAs are sent in response to RS up to the minimum interval.

### Step 5 — Troubleshooting

- **RA Guard can be bypassed with fragmented RAs** — RFC 7113 documents RA Guard bypass techniques using IPv6 fragmentation. The attacker fragments the RA so that the first fragment doesn't contain the ICMPv6 Type 134 header, and older RA Guard implementations pass it. Fix: upgrade to Cisco IOS-XE 16.x+ which implements RFC 7113 mitigations, and deploy `ipv6 nd raguard policy <name>` with `match ipv6 access-list` and reassembly.

- **No PAK_DROP events but rogue RAs suspected** — RA Guard may not be deployed on all VLANs. Check coverage: UC-5.20.29. Alternatively, RA Guard may be in `monitor` mode instead of `guard` mode — it logs but does not block.

- **Zeek not decoding ICMPv6** — Ensure the SPAN/TAP port mirrors the correct VLAN traffic. Verify Zeek is capturing ICMPv6: `zeekctl capstats` should show a non-zero packet rate. If using a GRE tunnel for SPAN delivery, ensure Zeek is configured to decapsulate GRE.

- **Windows ICS generating continuous rogue RAs** — Windows Internet Connection Sharing enables RA sending. The only permanent fix is to disable ICS/mobile hotspot or deploy RA Guard. These events are real misconfigurations, not false positives — investigate each one.

## SPL

```spl
index=network (sourcetype="cisco:ios" "%SISF-4-PAK_DROP" "RA guard")
  OR (sourcetype="cisco:ios" "SISF" "router-advertisement")
  OR (sourcetype="corelight_zeek" icmpv6_type=134)
| eval detection_type=case(
    match(_raw, "PAK_DROP.*RA guard"), "ROGUE_RA_BLOCKED",
    match(_raw, "icmpv6_type=134") AND NOT match(src_mac, "^(00:00:5e|00:01:00)"), "UNVERIFIED_RA",
    1=1, "LEGITIMATE_RA")
| stats count as ra_count dc(src_ip) as unique_sources values(src_ip) as sources values(src_mac) as macs by host, detection_type
| where detection_type!="LEGITIMATE_RA"
| sort -ra_count
```

## Visualization

(1) Single-value: rogue RA events in the last 24 hours — should be zero in a properly secured network. (2) Table: rogue RA details — source MAC, source IP, switch/interface, timestamp. (3) Timechart: RA events over time — a burst indicates an active attack or new rogue device. (4) Network map: which VLANs/switches are seeing rogue RAs — helps localise the source.

## Known False Positives

**Windows Internet Connection Sharing (ICS).** When a Windows laptop enables ICS or mobile hotspot, it enables IPv6 forwarding and starts sending RAs on its connected interface. This is the #1 source of accidental rogue RAs in enterprise networks. The RAs typically advertise the laptop's self-assigned ULA prefix (fd00::/64). RA Guard blocks them, but the PAK_DROP events fire. This is a genuine misconfiguration that should be investigated, even though it is not malicious.

**Docker/Podman/LXC containers.** Container runtimes on hosts with IPv6 forwarding enabled may send RAs on the host network interface. These are typically link-local only and confined to the container bridge, but misconfigured bridge networking can leak RAs onto the physical LAN.

**Network equipment during configuration.** When a new router or layer-3 switch is being configured, it may briefly send RAs with incorrect or test prefixes before final configuration is applied. These should be time-limited to the maintenance window.

## References

- [RFC 6105 — IPv6 Router Advertisement Guard (RA Guard specification)](https://www.rfc-editor.org/rfc/rfc6105)
- [RFC 7113 — Implementation Advice for IPv6 Router Advertisement Guard (RA-Guard bypass mitigations)](https://www.rfc-editor.org/rfc/rfc7113)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2 — RA security)](https://www.rfc-editor.org/rfc/rfc9099)
- [THC-IPv6 Attack Toolkit — fake_router6 rogue RA tool](https://github.com/vanhauser-thc/thc-ipv6)
