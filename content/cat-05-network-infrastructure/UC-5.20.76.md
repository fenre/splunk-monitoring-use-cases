<!-- AUTO-GENERATED from UC-5.20.76.json — DO NOT EDIT -->

---
id: "5.20.76"
title: "IPv6 PMTUD Manipulation Attack Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.76 · IPv6 PMTUD Manipulation Attack Detection

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*When sending a large package, the delivery service may come back and say 'Your package is too big for the tunnel on the route — make it smaller.' If a trickster sends this message falsely, you'll start wrapping everything in tiny packages, making your deliveries very slow even though the route is actually fine. We watch for false 'make it smaller' messages, especially ones claiming impossibly small sizes.*

---

## Description

Detects Path MTU Discovery manipulation attacks where an attacker sends forged ICMPv6 Packet Too Big messages with fraudulently low MTU values to degrade connection throughput. PTB messages claiming an MTU below the IPv6 minimum of 1280 bytes are definitively invalid per RFC 8021. PTB messages with very low MTU values from sources not on the actual network path between endpoints are highly suspicious.

## Value

PMTUD manipulation is a subtle attack — the connection continues to work but at dramatically reduced throughput. Users report 'the network is slow' but not 'the network is down,' making diagnosis difficult. Because IPv6 has no router-level fragmentation (unlike IPv4), PMTUD is the only mechanism for adapting to path MTU constraints. Forging PTB messages exploits this mandatory trust relationship. Detecting forged PTB messages catches this attack before it impacts application performance.

## Implementation

Monitor ICMPv6 PTB messages for fraudulent MTU values. Verify PTB source addresses are on the actual path between endpoints. Alert on MTU values below 1280 (always invalid). Correlate with TCP retransmission patterns.

## Detailed Implementation

### Prerequisites
- ICMPv6 PTB messages visible in syslog, NetFlow, or Zeek logs.
- Network topology knowledge to validate PTB source addresses against actual path.
- TCP performance metrics to correlate with MSS reduction.

### Step 1 — Configure data collection

**Cisco IOS-XE — ICMPv6 logging:**
ICMPv6 PTB messages are logged when `debug ipv6 icmp` is enabled (not recommended for production) or via ACL logging:
```
ipv6 access-list MONITOR_PTB
 permit icmp any any packet-too-big log
 permit ipv6 any any
```

**Zeek/Corelight — ICMPv6 analysis:**
Zeek logs ICMP connections in conn.log. PTB messages appear as ICMP connections with specific type/code fields.

**NetFlow/IPFIX:**
IPFIX can export ICMPv6 type/code in the icmpTypeCodeIPv6 (IE#139) field. Verify this field is included in the flow record.

**Verification:**
```spl
index=network ("Packet Too Big" OR "packetTooBig" OR "icmpv6_type=2") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Invalid MTU detection (<1280):**
```spl
index=network ("Packet Too Big" OR "packetTooBig" OR "icmpv6_type=2") earliest=-1h
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<mtu>\d+)"
| where tonumber(mtu) < 1280
| eval alert="DEFINITIVE ATTACK: PTB with MTU=" . mtu . " — below IPv6 minimum (1280). RFC 8021 explicitly calls this harmful."
| table _time, host, mtu, alert
```
Trigger: any event. MTU < 1280 is ALWAYS invalid in IPv6.

**Suspicious PTB source validation:**
```spl
index=network ("Packet Too Big" OR "icmpv6_type=2") earliest=-4h
| rex field=_raw "(?:src|source|from)\s*=?\s*(?<ptb_src>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<mtu>\d+)"
| lookup known_transit_routers.csv ipv6_address as ptb_src OUTPUT router_name
| where isnull(router_name)
| eval warning="PTB from unknown source " . ptb_src . " (MTU=" . mtu . ") — not a known transit router. Possible spoofed PTB."
| table _time, ptb_src, mtu, warning
```
Legitimate PTB messages come from routers on the actual path. A PTB from an unknown source is suspicious.

**Repeated PTB to same target (sustained attack):**
```spl
index=network ("Packet Too Big" OR "icmpv6_type=2") earliest=-1h
| rex field=_raw "(?:dst|dest|to)\s*=?\s*(?<target>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<mtu>\d+)"
| stats count as ptb_count dc(mtu) as mtu_values by target
| where ptb_count > 20
| eval attack="Sustained PMTUD attack: " . ptb_count . " PTB messages to " . target . " in 1 hour"
```

### Step 3 — Validate
(a) **Invalid MTU test.** Use Scapy to craft a PTB with MTU=1000 and send to a test host. Verify the invalid MTU alert fires.

(b) **Path validation.** On a path with a known transit router, verify PTB messages from that router do NOT trigger the unknown-source alert.

(c) **Normal PTB.** On a path with a VPN tunnel (legitimate reduced MTU), verify PTB messages are classified correctly as legitimate.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — PMTUD Security"):
- Row 1 — Alert: invalid MTU PTB messages (always attack).
- Row 2 — Table: suspicious PTB from unknown sources.
- Row 3 — Timechart: PTB rate per target host.
- Row 4 — Table: known PTB sources (transit routers) vs unknown sources.

**Scheduling:** Invalid MTU real-time. Suspicious source every 15 minutes. Sustained attack hourly.

**Runbook:**
1. MTU < 1280: block the PTB source IP. If the source is spoofed, deploy BCP 38 anti-spoofing.
2. Unknown PTB source: verify the source is not a recently-added transit router. If unknown, block and investigate.
3. Sustained attack: implement ICMPv6 rate limiting on the target host. Consider deploying PMTUD path validation (host-side).

### Step 5 — Troubleshooting

- **PMTUD path cache** — Hosts maintain a path MTU cache. After a PMTUD attack, the reduced MTU persists in the cache even after the attack stops. Clear the path MTU cache on affected hosts to restore performance.

- **PLPMTUD (RFC 8899)** — Packetization Layer PMTUD validates PTB messages by probing the path. Hosts that implement PLPMTUD are more resistant to PMTUD manipulation because they verify the claimed MTU independently.

- **Rate limiting PTB** — Excessive PTB rate limiting can break legitimate PMTUD. Apply rate limits conservatively — 1-10 PTB per second per destination is typically sufficient for legitimate operation.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="netflow" OR sourcetype="zeek:conn") ("Packet Too Big" OR "icmpv6_type=2" OR "packetTooBig") earliest=-4h
| rex field=_raw "(?:mtu|MTU)\s*=?\s*(?<claimed_mtu>\d+)"
| rex field=_raw "(?:src|source|from)\s*=?\s*(?<ptb_source>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest|to)\s*=?\s*(?<ptb_dest>[0-9a-fA-F:.]+)"
| eval claimed_mtu=tonumber(claimed_mtu)
| eval anomaly=case(
    claimed_mtu < 1280, "CRITICAL — MTU below IPv6 minimum (1280). This is ALWAYS an attack (RFC 8021).",
    claimed_mtu < 1300 AND claimed_mtu >= 1280, "WARNING — MTU at IPv6 minimum. Verify path contains a 1280-byte link.",
    1=1, null())
| where isnotnull(anomaly)
| stats count as ptb_count first(_time) as first last(_time) as last by ptb_source, ptb_dest, claimed_mtu, anomaly
| sort -ptb_count
```

## Visualization

(1) Alert table: PTB messages with invalid/suspicious MTU values. (2) Scatter plot: claimed MTU vs PTB source (path validation). (3) Timechart: PTB message rate. (4) Table: connections experiencing sudden MSS reduction.

## Known False Positives

**Legitimate low-MTU paths.** Some network paths genuinely have low MTU — VPN tunnels (typically 1400-1420 bytes), GRE tunnels (1440 bytes), and PPPoE (1492 bytes) reduce the effective MTU. PTB messages from these paths are legitimate.

**IPv6-in-IPv4 tunnels.** 6in4 tunnels have an effective MTU of 1480 bytes (1500 - 20 byte IPv4 header). PTB messages at this MTU from tunnel endpoints are legitimate.

**Cloud provider internal routing.** Some cloud providers use encapsulation internally, reducing effective MTU to 1400-1460 bytes. PTB messages from cloud infrastructure are legitimate.

## References

- [RFC 8021 — Generation of IPv6 Atomic Fragments Considered Harmful](https://www.rfc-editor.org/rfc/rfc8021)
- [RFC 8201 — Path MTU Discovery for IP version 6 (PMTUD specification)](https://www.rfc-editor.org/rfc/rfc8201)
