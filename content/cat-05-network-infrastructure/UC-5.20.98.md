<!-- AUTO-GENERATED from UC-5.20.98.json — DO NOT EDIT -->

---
id: "5.20.98"
title: "IPv6 Fragment Reassembly Timeout and Evasion Attack Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.98 · IPv6 Fragment Reassembly Timeout and Evasion Attack Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Imagine someone sends you a large birthday card by cutting it into several pieces and mailing each piece separately. Normally, you put the pieces back together to read the card. But a burglar might send confusing, overlapping pieces to trick your mail sorter into letting something bad through.*

---

## Description

Detects IPv6 fragmentation anomalies and attacks: overlapping fragments (RFC 5722 violation), tiny fragments used for IDS evasion (RFC 8200 §4.5), reassembly timeout floods, and atomic fragment injection (RFC 8021). IPv6 fragmentation is inherently suspicious because only source hosts can fragment — routers do not. Any fragmentation at a transit point is either a misconfigured source or an active attack.

## Value

IPv6 fragmentation is a primary tool for IDS/IPS evasion. Attackers use tiny fragments to hide upper-layer headers from stateless devices, overlapping fragments to confuse reassembly logic, and fragment floods to exhaust reassembly buffers. Because IPv6 fragmentation is source-only and rare in legitimate traffic, detecting it provides a high-signal indicator of attack activity. RFC 5722 compliance (drop overlapping fragments) and RFC 8021 (deprecate atomic fragments) are critical security controls.

## Implementation

Monitor for IPv6 fragment header presence in traffic. Classify fragments by type (overlapping, tiny, atomic, timeout). Alert on RFC 5722/8021 violations. Track reassembly timeout rates for DoS detection.

## Detailed Implementation

### Prerequisites
- Zeek or Suricata sensor deployed on key network segments.
- Router/firewall logging enabled for IPv6 fragment events.
- Splunk Add-on for Zeek or Suricata TA installed.

### Step 1 — Configure data collection

**Zeek configuration for fragment logging:**
Zeek automatically logs fragmented connections in `conn.log` and generates notices for fragment anomalies. Ensure `policy/protocols/conn/known-hosts.zeek` and `policy/misc/known-devices.zeek` are loaded.

For enhanced detection, add to `local.zeek`:
```zeek
@load policy/frameworks/notice/actions/add-geodata
@load policy/protocols/conn/known-hosts
redef TCP::max_initial_window = 16384;
```

**Cisco IOS/IOS-XE fragment logging:**
Enable logging for fragment-related ACL hits:
```
ipv6 access-list FRAGMENT-MONITOR
  deny ipv6 any any fragments log
  permit ipv6 any any
!
interface GigabitEthernet0/0
  ipv6 traffic-filter FRAGMENT-MONITOR in
```

**Suricata rules for IPv6 fragment attacks:**
```
alert ipv6 any any -> any any (msg:"IPv6 overlapping fragment"; fragbits:M; fragoffset:>0; sid:6000001; rev:1;)
alert ipv6 any any -> any any (msg:"IPv6 tiny fragment"; dsize:<40; fragbits:M; fragoffset:0; sid:6000002; rev:1;)
```

**Verification:**
```spl
index=network "fragment" | stats count by sourcetype
```

### Step 2 — Create monitoring searches

**Overlapping fragment detection (CRITICAL — must be zero):**
```spl
index=network (sourcetype="zeek:weird" OR sourcetype="suricata:alert") earliest=-24h
  "overlap" AND "fragment"
| rex field=_raw "(?:src|source)\s*=?\s*(?<attacker>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<target>[0-9a-fA-F:.]+)"
| stats count as fragments by attacker, target
| eval severity="CRITICAL — RFC 5722 mandates dropping all fragments from this source"
| sort -fragments
```

**Reassembly timeout flood (DoS indicator):**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="zeek:conn") earliest=-1h
  "reassembl" AND ("timeout" OR "fail")
| timechart span=5m count as reassembly_timeouts
| where reassembly_timeouts > 50
| eval alert="Fragment reassembly timeout flood — possible DoS. Rate: " . reassembly_timeouts . " in 5 minutes"
```

### Step 3 — Validate
(a) **Controlled test.** Use `nmap -6 --mtu 256 <target>` to generate fragmented IPv6 packets. Verify fragments appear in Splunk.

(b) **Overlap test.** Use the `fragrouter` tool or `scapy` to craft overlapping IPv6 fragments. Verify the firewall/IDS drops them and logs the event:
```python
from scapy.all import *
pkt = IPv6(dst='2001:db8::1')/IPv6ExtHdrFragment(offset=0, m=1)/TCP(dport=80)
pkt2 = IPv6(dst='2001:db8::1')/IPv6ExtHdrFragment(offset=0, m=0)/TCP(dport=80, flags='S')
send([pkt, pkt2])
```

(c) **Verify zero baseline.** In a healthy network, overlapping fragment count should be zero. Any non-zero value requires investigation.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Fragmentation Security"):
- Row 1 — Single-values: overlapping fragments (red if >0), reassembly timeouts, tiny fragments.
- Row 2 — Timechart: fragment events by type.
- Row 3 — Table: top fragment sources with classification.
- Row 4 — Correlation: fragment sources cross-referenced with known scanning sources.

**Alert 1:** Any overlapping fragment — critical. Immediate investigation.
**Alert 2:** Reassembly timeout rate >50/5min — high. Possible DoS.
**Alert 3:** Tiny fragments from single source >10/hour — high. IDS evasion attempt.

### Step 5 — Troubleshooting

- **Legitimate fragmentation vs attack.** Check the source address. Legitimate fragmentation comes from known internal hosts with large payloads (NFS, database replication). Attacks come from external sources or spoofed addresses.

- **PMTUD failure causing fragmentation.** If internal hosts are fragmenting, check that ICMPv6 Packet Too Big messages (type 2) are not being blocked by firewalls. PMTUD requires end-to-end ICMPv6 PTB delivery.

- **Firewall fragment handling.** Not all firewalls handle IPv6 fragments correctly. Some pass fragments without reassembly (allowing evasion). Verify your firewall reassembles IPv6 fragments before applying policy. On Cisco ASA: `fragment reassembly ipv6`. On Palo Alto: fragment reassembly is enabled by default.

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="cisco:ios" OR sourcetype="suricata:alert") earliest=-24h
  ("fragment" OR "reassembl" OR "frag_offset" OR "%IPV6-4-FRAG")
| eval frag_event=case(
    match(_raw, "(?i)overlap.*fragment|RFC.?5722"), "OVERLAPPING_FRAGMENT — RFC 5722 violation",
    match(_raw, "(?i)tiny.?frag|small.?fragment|fragment.*offset.*0.*len.?[0-9]{1,2}[^0-9]"), "TINY_FRAGMENT — IDS evasion attempt",
    match(_raw, "(?i)reassembl.*timeout|reassembly.*fail|frag.*timeout"), "REASSEMBLY_TIMEOUT — possible fragment DoS",
    match(_raw, "(?i)atomic.?frag|frag.*M.?=.?0.*offset.?=.?0"), "ATOMIC_FRAGMENT — RFC 8021 concern",
    match(_raw, "(?i)fragment"), "FRAGMENT — normal",
    1=1, "OTHER")
| rex field=_raw "(?:src|source)\s*=?\s*(?<frag_src>[0-9a-fA-F:.]+)"
| stats count as events dc(frag_src) as unique_sources by host, frag_event
| eval severity=case(
    like(frag_event, "OVERLAPPING_FRAGMENT%"), "CRITICAL — must drop; indicates active attack",
    like(frag_event, "TINY_FRAGMENT%"), "HIGH — likely IDS evasion or scanning",
    like(frag_event, "REASSEMBLY_TIMEOUT%") AND events > 100, "HIGH — possible fragment flood DoS",
    like(frag_event, "ATOMIC_FRAGMENT%"), "MEDIUM — investigate upstream ICMPv6 PTB source",
    1=1, "INFO")
| sort -events
```

## Visualization

(1) Timechart: fragment events by type over time. (2) Table: top fragment sources with event type. (3) Single-value: overlapping fragment count (should be zero). (4) Map: geographic source of fragment attacks.

## Known False Positives

**Legitimate large payloads.** Some applications (DNS over TCP fallback, NFS over IPv6) may legitimately fragment. Verify the source and payload before assuming an attack.

**Path MTU discovery.** When PMTUD fails (ICMPv6 PTB messages are blocked), hosts may fragment. This indicates a broken PMTUD path, not an attack — but it still needs fixing.

**Tunneled traffic.** Encapsulated traffic (GRE, VXLAN) may fragment at the tunnel endpoint. These fragments are legitimate but may indicate an MTU mismatch.

## References

- [RFC 8200 — Internet Protocol, Version 6 (IPv6) Specification (§4.5 — Fragment Header)](https://www.rfc-editor.org/rfc/rfc8200#section-4.5)
- [RFC 5722 — Handling of Overlapping IPv6 Fragments](https://www.rfc-editor.org/rfc/rfc5722)
- [RFC 8021 — Generation of IPv6 Atomic Fragments Considered Harmful](https://www.rfc-editor.org/rfc/rfc8021)
- [RFC 7707 — Network Reconnaissance in IPv6 Networks (§5 — fragmentation-based scanning)](https://www.rfc-editor.org/rfc/rfc7707)
