<!-- AUTO-GENERATED from UC-5.20.132.json — DO NOT EDIT -->

---
id: "5.20.132"
title: "IPv6 Path MTU Discovery (PMTUD) Black Hole Detection"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.132 · IPv6 Path MTU Discovery (PMTUD) Black Hole Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Imagine posting a large package that's too big for some mailboxes along the route. Normally, the postal service sends you a message saying 'make it smaller.' If someone blocks those messages, your package just disappears and you don't know why. We watch for these 'make it smaller' messages being blocked, so large deliveries don't silently fail.*

---

## Description

Detects IPv6 PMTUD black holes where ICMPv6 Packet Too Big messages are blocked by firewalls, causing connections to stall when large packets are dropped silently. PMTUD black holes are one of the most difficult IPv6 problems to diagnose because the initial TCP handshake succeeds but the connection stalls when data transfer begins.

## Value

PMTUD black holes cause mysterious IPv6 connection failures: TCP connects fine (SYN/SYN-ACK are small), but the connection stalls as soon as data transfer starts with larger packets. Users see pages that partially load or connections that timeout. Because the initial handshake succeeds, the problem appears to be application-level rather than network-level, making diagnosis extremely difficult without specific monitoring.

## Implementation

Monitor for blocked ICMPv6 PTB messages (see UC-5.20.131). Detect connection stall patterns. Alert on suspected PMTUD failures.

## Detailed Implementation

### Prerequisites
- Zeek or Suricata sensor.
- Firewall logging for ICMPv6 deny actions.

### Step 1 — Verify ICMPv6 type 2 is permitted through all transit firewalls (see UC-5.20.131).

### Step 2 — Create monitoring searches for PMTUD failures.

**Test PMTUD end-to-end:**
```bash
ping6 -s 1400 -M do <target>
```
If this fails with 'Message too long' and the connection works with -s 1200, there's a PMTUD black hole.

### Step 3 — Validate PMTUD path.

### Step 4 — Operationalize
**Dashboard:** PMTUD health. **Alert:** PTB messages blocked — critical.

### Step 5 — Troubleshooting
- PMTUD black hole: Find and fix the firewall blocking ICMPv6 type 2. As a workaround, reduce TCP MSS: `ipv6 tcp adjust-mss 1220`.

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="cisco:ios") earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval pmtud_issue=case(
    match(_raw, "(?i)too.?big.*drop|PTB.*drop|icmpv6.*type.?2.*deny"), "PTB_BLOCKED",
    match(_raw, "(?i)fragment.*needed|packet.?too.?big"), "PTB_RECEIVED",
    match(_raw, "(?i)retransmit|stall|timeout") AND match(conn_state, "S[0-3]"), "CONNECTION_STALL",
    1=1, null())
| where isnotnull(pmtud_issue)
| stats count as events by host, pmtud_issue
| eval severity=case(
    pmtud_issue="PTB_BLOCKED", "CRITICAL — ICMPv6 PTB messages being blocked — PMTUD is broken",
    pmtud_issue="CONNECTION_STALL" AND events > 50, "HIGH — connection stalls may indicate PMTUD black hole",
    pmtud_issue="PTB_RECEIVED", "INFO — PMTUD working (PTB received and processed)",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Single-value: blocked PTB count (should be zero). (2) Table: connections with stall patterns. (3) Timechart: PTB events. (4) Correlation: stalls vs blocked PTBs.

## Known False Positives

**Application-level timeouts.** Some connection stalls are caused by application issues, not PMTUD failures. Correlate with PTB blocking to distinguish.

**VPN tunnels reducing MTU.** VPN encapsulation reduces effective MTU. This may trigger legitimate PTB messages.

## References

- [RFC 8201 — Path MTU Discovery for IP version 6](https://www.rfc-editor.org/rfc/rfc8201)
- [RFC 8200 — IPv6 Specification (§5 — Packet Size Issues)](https://www.rfc-editor.org/rfc/rfc8200#section-5)
