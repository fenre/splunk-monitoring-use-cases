<!-- AUTO-GENERATED from UC-5.20.139.json — DO NOT EDIT -->

---
id: "5.20.139"
title: "IPv6 Neighbour Cache Exhaustion (NDP Table Overflow) Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.139 · IPv6 Neighbour Cache Exhaustion (NDP Table Overflow) Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Your router keeps a phone book of all the IPv6 addresses it knows about. An attacker can flood it with millions of fake lookups until the phone book is completely full and it can't look up any more real addresses. We watch the phone book's capacity and sound the alarm before it overflows.*

---

## Description

Detects NDP neighbour cache exhaustion (RFC 6583), where an attacker forces a router to perform NDP resolution for many addresses in a /64 subnet. Because a /64 contains 2^64 addresses, even a small fraction can overflow router memory. Symptoms include neighbour cache table full errors and excessive INCOMPLETE NDP entries.

## Value

Neighbour cache exhaustion is the IPv6 equivalent of an ARP exhaustion attack but vastly more severe due to the size of /64 subnets. A single host scanning the subnet can crash a router or prevent legitimate hosts from communicating. This attack is specifically called out in RFC 6583 and is a real operational threat in enterprise networks.

## Implementation

Monitor for NDP table full events, excessive INCOMPLETE entries, and NDP rate-limiting triggers.

## Detailed Implementation

### Prerequisites
- Router syslog with NDP events.
- NDP cache limits configured.

### Step 1 — Configure NDP cache limits and rate-limiting:
```
ipv6 nd cache interface-limit 4096
ipv6 nd ns-interval 1000
```

### Step 2 — Monitor NDP table utilization:
```
show ipv6 neighbors statistics
```

### Step 3 — Validate: Attempt subnet scan with `nmap -6 --script ipv6-multicast-mld-list`. Verify detection fires.

### Step 4 — Operationalize
**Dashboard:** NDP cache health. **Alert:** NDP table utilization >80% or table full — critical.

### Step 5 — Troubleshooting
- Reduce /64 attack surface: Use /120 or /126 subnets for point-to-point links.
- Enable `ipv6 nd cache expire 300` to age out INCOMPLETE entries faster.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  ("INCOMPLETE" OR "neighbor.*table.*full" OR "ND.*table.*overflow" OR "adjacency.*limit" OR "ipv6.*nd.*cache")
| eval cache_event=case(
    match(_raw, "(?i)table.*full|overflow|limit.*reached|exhausted"), "TABLE_FULL",
    match(_raw, "(?i)INCOMPLETE.*count|incomplete.*exceed"), "EXCESSIVE_INCOMPLETE",
    match(_raw, "(?i)rate.*limit|nd.*throttle"), "RATE_LIMITED",
    1=1, "ND_EVENT")
| stats count as events by host, cache_event
| eval severity=case(
    cache_event="TABLE_FULL", "CRITICAL — NDP table full on " . host . " — " . events . " events — neighbour cache exhaustion attack or misconfigured /64",
    cache_event="EXCESSIVE_INCOMPLETE" AND events > 100, "HIGH — " . events . " incomplete NDP entries — possible scanning attack",
    cache_event="RATE_LIMITED", "MEDIUM — NDP rate limiting active — mitigating attack",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Single-value: NDP table utilization %. (2) Timechart: INCOMPLETE entries over time. (3) Table: affected routers. (4) Alert: table full events.

## Known False Positives

**Large subnets with many hosts.** A /64 with hundreds of active hosts may have high NDP cache utilization. This is a sizing issue, not an attack.

**Network scanning tools.** Legitimate scanning (vulnerability assessment, inventory) can trigger high INCOMPLETE counts. Schedule scans and exclude from alerts.

## References

- [RFC 6583 — Operational Neighbor Discovery Problems](https://www.rfc-editor.org/rfc/rfc6583)
- [Cisco — IPv6 Neighbor Discovery Cache Exhaustion Attack Mitigation](https://www.cisco.com/c/en/us/support/docs/ip/ip-version-6-ipv6/212768-ipv6-first-hop-security-best-practice.html)
