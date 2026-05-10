<!-- AUTO-GENERATED from UC-5.20.38.json — DO NOT EDIT -->

---
id: "5.20.38"
title: "ICMPv6 Packet Too Big — Path MTU Discovery Failure Detection"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.20.38 · ICMPv6 Packet Too Big — Path MTU Discovery Failure Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*When a letter is too big for the mailbox, the postman sends it back with a note saying 'the mailbox is only this big — make the letter smaller.' If someone blocks those return notes, the sender keeps trying to cram the same big letter in and it never arrives. We watch for these 'letter too big' notes to make sure they are getting through, and for letters that keep getting stuck.*

---

## Description

Detects Path MTU Discovery (PMTUD) failures and monitors ICMPv6 Packet Too Big (PTB, Type 2) message flows to identify IPv6 black holes — paths where packets are silently dropped because they exceed the link MTU and the PTB messages that should trigger PMTUD are being blocked or lost. PMTUD failure is the #1 most reported IPv6 operational problem, responsible for the majority of 'IPv6 doesn't work' trouble tickets. It creates a particularly confusing symptom: small requests work (ping, DNS), connections appear to establish, but data transfer hangs. This use case detects the problem from two angles: (1) excessive PTB messages indicating a persistent MTU mismatch, and (2) the absence of PTB messages on paths known to have MTU constraints, indicating PTB messages are being dropped.

## Value

PMTUD failure is insidious because it produces intermittent, hard-to-diagnose symptoms. The TCP handshake succeeds because SYN/SYN-ACK/ACK packets are small. The connection then hangs when the server sends a large response (TLS certificate, web page, file download). This makes the problem appear application-specific when it is actually a network issue. Detecting PMTUD failure proactively — before users report 'HTTPS works sometimes' — saves enormous troubleshooting time. Every IPv6 deployment should monitor for this condition.

## Implementation

Monitor for ICMPv6 Type 2 (PTB) messages in syslog and NetFlow. Track PTB message rates per path. Alert on sustained PTB volumes (indicating persistent MTU mismatch) and on the absence of PTB messages on tunnel paths (indicating firewall blocking). Correlate with TCP retransmission data for confirmation.

## Detailed Implementation

### Prerequisites
- ICMPv6 logging enabled on routers and firewalls (especially transit points where MTU changes).
- NetFlow/IPFIX with ICMPv6 type and code exported for volumetric analysis.
- Knowledge of intended MTU values for each network segment (especially tunnels).

### Step 1 — Configure data collection

**Cisco IOS-XE — log ICMPv6 Type 2 specifically:**
```
ipv6 access-list LOG_PTB
 permit icmp any any packet-too-big log
```
Apply as an input ACL on transit interfaces to capture PTB messages traversing the router.

**NetFlow/IPFIX** — ensure ICMPv6 type and code are exported:
```
flow record IPFIX-IPv6
 match ipv6 source address
 match ipv6 destination address
 match transport source-port
 match transport destination-port
 match ipv6 protocol
 match icmpv6 type
 match icmpv6 code
 collect counter bytes
 collect counter packets
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("Packet Too Big" OR "packetTooBig" OR "ICMP type 2") earliest=-24h
| stats count by host
```

### Step 2 — Create the search and alert

**PTB message trending:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="netflow") ("Packet Too Big" OR "packetTooBig" OR "icmpv6_type=2")
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<reported_mtu>\d+)"
| timechart span=1h count by host
```

**Persistent PMTUD failure detection — same source/destination pair generating PTB repeatedly:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="netflow") ("Packet Too Big" OR "packetTooBig" OR "icmpv6_type=2") earliest=-4h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| bin _time span=30m
| stats count as ptb_in_window by src_ipv6, dst_ipv6, _time
| where ptb_in_window > 10
| stats count as sustained_windows values(_time) as timestamps by src_ipv6, dst_ipv6
| where sustained_windows >= 3
| eval issue="PMTUD failure — source is not reducing packet size after receiving PTB messages"
```
Trigger: A source/destination pair that generates more than 10 PTB messages in each of 3 or more consecutive 30-minute windows indicates the source is not responding to PTB messages — likely the return-path PTB message is being blocked by a firewall.

**Tunnel interface MTU mismatch detection:**
```spl
index=network sourcetype="cisco:ios" ("Packet Too Big" OR "%IPV6-3-NOTFRAG") earliest=-24h
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<reported_mtu>\d+)"
| rex field=_raw "(?:interface|Interface)\s*(?<interface>\S+)"
| where match(interface, "(?i)tunnel|gre|ipsec|vxlan")
| stats count as ptb_count avg(reported_mtu) as avg_mtu by host, interface
| where ptb_count > 50
| eval action="Check tunnel MTU configuration — current effective MTU: " . avg_mtu
```

### Step 3 — Validate
(a) **Lab test — successful PMTUD.** Set up a path with MTU 1280 between two hosts. Ping with 1500-byte packets. Verify PTB messages appear in Splunk with `reported_mtu=1280`. Verify the source reduces packet size.

(b) **Lab test — PMTUD failure.** Block ICMPv6 Type 2 at the firewall. Repeat the test. Observe TCP data transfer hangs after handshake. Verify no PTB messages appear in Splunk. Verify the persistent PMTUD failure alert fires.

(c) **Production validation.** Identify paths with known tunnel encapsulation. Verify PTB messages appear at expected rates for those paths.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Path MTU Discovery Health"):
- Row 1 — Single-value: active PMTUD failures (sustained PTB, source not adapting).
- Row 2 — Timechart: PTB messages by source over 24 hours.
- Row 3 — Table: persistent PMTUD failure pairs (source/destination that keep failing).
- Row 4 — Tunnel MTU analysis: tunnel interfaces with high PTB rates.

**Scheduling:** Continuous alerting for PMTUD failures. Hourly trending. Daily tunnel MTU analysis.

**Runbook:**
1. Persistent PMTUD failure: check for firewall blocking ICMPv6 Type 2 on the return path (UC-5.20.37). This is the cause 80% of the time.
2. Tunnel MTU issues: adjust tunnel MTU to match the path. Cisco formula: `ip mtu <path_mtu - encapsulation_overhead>`.
3. ECMP path issues: verify consistent MTU across all ECMP paths. Use `traceroute` with DF bit to discover the minimum MTU.

### Step 5 — Troubleshooting

- **PTB messages not logged** — ICMPv6 Type 2 may be processed by the router's fast path without hitting the ACL. Use NetFlow/IPFIX counters for volumetric measurement instead of syslog.

- **PMTUD works for some destinations but not others** — This is often caused by asymmetric routing. The forward path goes through a low-MTU link, but the PTB message returns via a path that has a firewall blocking ICMPv6. Both the forward and return path firewalls must permit Type 2.

- **MSS clamping as workaround** — TCP MSS clamping (`ipv6 tcp adjust-mss 1220`) avoids PMTUD entirely by pre-setting the maximum segment size. This works for TCP but not for UDP or other protocols. Use it as a temporary workaround while fixing the root cause.

## SPL

```spl
index=network sourcetype="cisco:ios" "%IPNHRP-4-IF_DOWN_ADMIN" OR "%IPV6-3-NOTFRAG" OR "Packet Too Big" OR "packetTooBig" earliest=-24h
| rex field=_raw "(?:src|from)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|to)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<reported_mtu>\d+)"
| stats count as ptb_count values(reported_mtu) as mtu_values by host, src_ipv6, dst_ipv6
| sort -ptb_count
```

## Visualization

(1) Timechart: PTB messages per hour — baseline and anomaly detection. (2) Sankey: PTB message flows showing source → destination pairs with persistent PMTUD issues. (3) Table: paths with MTU mismatches, showing reported MTU values. (4) Correlation panel: TCP retransmissions on the same paths as PTB messages.

## Known False Positives

**Normal PTB messages on tunnel interfaces.** Tunnel encapsulation reduces the effective MTU. PTB messages are expected on paths with tunnels (GRE/1476, IPsec/1400, VXLAN/1450). The important metric is whether the source successfully reduces its packet size after receiving the PTB — if the same source keeps generating PTB messages for the same destination, PMTUD is failing.

**Jumbo frame to standard frame transitions.** In networks with mixed jumbo (9000 byte MTU) and standard (1500 byte MTU) segments, PTB messages are expected at the boundary. This is normal PMTUD operation.

**ECMP path selection.** When ECMP selects different paths for different packets, some paths may have different MTUs. This causes intermittent PTB messages that are difficult to correlate with a specific path.

## References

- [RFC 8201 — Path MTU Discovery for IP version 6](https://www.rfc-editor.org/rfc/rfc8201)
- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls (§4.3.1 — Type 2 must be permitted)](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4 — PMTUD operational considerations)](https://www.rfc-editor.org/rfc/rfc9099)
