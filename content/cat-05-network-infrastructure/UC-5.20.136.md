<!-- AUTO-GENERATED from UC-5.20.136.json — DO NOT EDIT -->

---
id: "5.20.136"
title: "IPv6 NDP Redirect Message Abuse Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.136 · IPv6 NDP Redirect Message Abuse Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Normally, the post office tells you 'there's a closer mailbox for that destination.' But a bad actor can forge these redirect notices to make your letters go through their hands first. We watch for suspicious redirect notices, especially from people who aren't real post office workers.*

---

## Description

Detects abuse of ICMPv6 Redirect messages (type 137) used for man-in-the-middle attacks. An attacker forges redirect messages to reroute a victim's traffic through the attacker's machine. Legitimate redirects are rare in modern networks — most can be disabled without impact.

## Value

ICMPv6 redirects are a classic MITM vector. Because redirects change a host's routing table entry for a specific destination, they allow surgical traffic interception. Unlike RA spoofing (which affects all traffic), redirect attacks target specific flows. Most enterprise networks should disable redirect acceptance on hosts and filter redirects at switches.

## Implementation

Monitor for ICMPv6 type 137 messages. Alert on high redirect rates or redirects from unauthorized sources.

## Detailed Implementation

### Prerequisites
- Network sensor or router logging for ICMPv6.

### Step 1 — Disable redirect acceptance on hosts:
Linux: `sysctl -w net.ipv6.conf.all.accept_redirects=0`
Windows: `netsh interface ipv6 set global icmpredirects=disabled`

### Step 2 — Monitor for redirect messages on the network.

### Step 3 — Validate: Attempt to send a forged redirect. Verify detection fires.

### Step 4 — Operationalize
**Dashboard:** ICMPv6 redirect monitoring. **Alert:** Redirects from unauthorized source — high.

### Step 5 — Troubleshooting
- Disable redirect acceptance on all endpoints to eliminate the attack vector entirely.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="zeek:conn" OR sourcetype="suricata:alert") earliest=-24h
  ("redirect" AND ("ICMPv6" OR "icmpv6" OR "type.*137"))
| rex field=_raw "(?:target|new.?hop)\s*(?<redirect_target>[0-9a-fA-F:]+)"
| rex field=_raw "(?:src|from)\s*(?<redirect_source>[0-9a-fA-F:]+)"
| stats count as redirects dc(redirect_target) as unique_targets by host, redirect_source
| eval severity=case(
    redirects > 50, "HIGH — excessive ICMPv6 redirects from " . redirect_source . " — possible MITM",
    unique_targets > 10, "HIGH — redirects for many targets from single source — systematic attack",
    redirects > 10, "MEDIUM — elevated redirect rate from " . redirect_source,
    1=1, null())
| where isnotnull(severity)
| sort -redirects
```

## Visualization

(1) Table: redirect sources and targets. (2) Single-value: redirect count. (3) Timeline: redirect events.

## Known False Positives

**Router redirects.** Legitimate redirects from default gateways telling hosts about a more optimal next-hop. These are valid but rare in well-designed networks.

**Multiple routers on segment.** When multiple routers serve a segment, the default gateway may redirect traffic to the optimal router. This is legitimate.

## References

- [RFC 4861 — Neighbor Discovery for IPv6 (§8 — Redirect)](https://www.rfc-editor.org/rfc/rfc4861#section-8)
- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages (redirect is MAY DROP)](https://www.rfc-editor.org/rfc/rfc4890)
