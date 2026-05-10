<!-- AUTO-GENERATED from UC-5.20.113.json — DO NOT EDIT -->

---
id: "5.20.113"
title: "IPv6 Neighbour Cache Exhaustion (NDP Table Overflow) Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.113 · IPv6 Neighbour Cache Exhaustion (NDP Table Overflow) Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Every router keeps a phone book of devices on its network so it can deliver messages. An attacker can flood the router with fake phone numbers for devices that don't exist, filling up the phone book until there's no room for real devices. When the real devices aren't in the phone book anymore, they can't receive any messages.*

---

## Description

Detects IPv6 Neighbour Cache Exhaustion attacks (RFC 6583) where attackers flood a router's NDP table by generating traffic to non-existent addresses in a /64 subnet. Each non-existent target creates an INCOMPLETE neighbour cache entry, consuming router memory until the cache overflows and legitimate neighbour resolution fails, causing denial of service.

## Value

Neighbour cache exhaustion is one of the most practical IPv6 denial-of-service attacks. It requires only a single host on the same subnet (or routable access to a /64) and can take down an entire subnet's connectivity by preventing the router from resolving legitimate neighbours. The attack exploits the mandatory /64 prefix length in IPv6, which means every subnet has 2^64 potential addresses the attacker can target. Early detection is critical because the attack affects all hosts on the subnet.

## Implementation

Monitor NDP cache utilisation and INCOMPLETE entry counts. Alert on cache full events and high INCOMPLETE rates. Track NDP rate limiting activations.

## Detailed Implementation

### Prerequisites
- Router logging for NDP events.
- Understanding of per-interface NDP cache limits.

### Step 1 — Configure NDP cache protection

**Cisco IOS-XE — NDP cache limits:**
```
interface GigabitEthernet0/0/0
 ipv6 nd cache expire 300
 ipv6 nd cache interface-limit 4000
```

**Cisco IOS-XE — destination guard (rejects traffic to unknown neighbours):**
```
interface GigabitEthernet0/0/0
 ipv6 destination-guard attach-policy DESTGUARD
!
ipv6 destination-guard policy DESTGUARD
 enforcement always
```
Destination guard is the single most effective mitigation — it prevents the router from creating INCOMPLETE entries for non-existent destinations.

**Juniper Junos — NDP table limit:**
```
set interfaces ge-0/0/0 unit 0 family inet6 nd6-max-cache 4000
```

### Step 2 — Create monitoring searches

**NDP cache utilization trending:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  "neighbor" AND ("count" OR "entries" OR "table")
| rex field=_raw "(?<ndp_count>\d+)\s+(?:entries|neighbors)"
| eval ndp_count=tonumber(ndp_count)
| timechart span=15m max(ndp_count) as ndp_entries by host
```

**INCOMPLETE entry surge detection:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-1h
  "INCOMPLETE"
| rex field=_raw "interface\s+(?<interface>\S+)"
| stats count as incomplete_entries by host, interface
| where incomplete_entries > 200
| eval alert="NDP cache exhaustion risk on " . host . " " . interface . " — " . incomplete_entries . " INCOMPLETE entries in 1 hour"
```

### Step 3 — Validate
(a) **Controlled test.** From a test host, use `nmap -6 -sn 2001:db8:test::/120` to scan a small range. Monitor the router's NDP cache growth.

(b) **Cache limit test.** With `ipv6 nd cache interface-limit 100` set on a test interface, generate traffic to >100 addresses. Verify the limit is enforced and the event is logged.

(c) **Destination guard test.** With destination guard enabled, send traffic to a non-existent address. Verify the router drops the traffic without creating an INCOMPLETE entry.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Cache Health"):
- Row 1 — Gauges: NDP cache utilization per key router (% of limit).
- Row 2 — Timechart: INCOMPLETE entry rate.
- Row 3 — Table: routers with cache events.
- Row 4 — Destination guard status by interface.

**Alert 1:** NDP cache full — critical. Immediate response.
**Alert 2:** INCOMPLETE entries >200/hour on single interface — high. Possible attack.

**Runbook:**
1. Verify attack: check source of traffic to non-existent addresses.
2. Immediate mitigation: enable destination guard on affected interface.
3. Long-term: set NDP cache limits, enable destination guard globally.
4. For point-to-point links: use /126 or /127 prefixes to limit the addressable range.

### Step 5 — Troubleshooting

- **Cache full during legitimate growth.** If adding many hosts to a VLAN, the NDP cache grows legitimately. Increase `ipv6 nd cache interface-limit` to accommodate the expected number of hosts, plus 20% buffer.

- **Destination guard blocking legitimate traffic.** Destination guard drops traffic to addresses not in the NDP cache. If a new host connects and immediately receives traffic, the first packets may be dropped before NDP resolves. This is a brief transient (<1 second) and is preferable to cache exhaustion vulnerability.

- **/64 prefix length debate.** RFC 6583 acknowledges that the mandatory /64 prefix length creates the vulnerability. For point-to-point links, use /126 or /127 (RFC 6164) to eliminate the attack surface entirely.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  ("%IPV6_ND" OR "%ADJ" OR "neighbor" OR "adjacency" OR "INCOMPLETE" OR "cache.*full")
| eval cache_event=case(
    match(_raw, "(?i)cache.*full|table.*full|adjacency.*overflow|no.*room"), "CACHE_FULL",
    match(_raw, "(?i)INCOMPLETE.*threshold|incomplete.*limit"), "INCOMPLETE_THRESHOLD",
    match(_raw, "(?i)rate.*limit|throttl"), "RATE_LIMITED",
    match(_raw, "(?i)INCOMPLETE"), "INCOMPLETE_ENTRY",
    1=1, "OTHER")
| stats count as events by host, cache_event
| eval severity=case(
    cache_event="CACHE_FULL", "CRITICAL — NDP cache exhausted on " . host . " — active DoS or misconfigured /64",
    cache_event="INCOMPLETE_THRESHOLD" AND events > 100, "HIGH — INCOMPLETE entry threshold exceeded — possible cache exhaustion attack",
    cache_event="RATE_LIMITED" AND events > 50, "MEDIUM — NDP rate limiting activated — elevated NDP solicitation rate",
    cache_event="INCOMPLETE_ENTRY" AND events > 500, "WARNING — high INCOMPLETE neighbour entry count (" . events . ") — monitor for escalation",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Gauge: NDP cache utilization per router. (2) Timechart: INCOMPLETE entry rates. (3) Single-value: routers with cache full events (red if >0). (4) Table: top routers with high NDP activity.

## Known False Positives

**Large subnets with many hosts.** A /64 with hundreds of active hosts generates many NDP entries. This is normal — monitor for INCOMPLETE entries specifically, which indicate addresses that don't respond.

**Host mobility.** In wireless environments, hosts join and leave frequently, creating short-lived NDP entries. This is normal churn, not an attack.

**Network scanning.** Legitimate network scanning tools (Nessus, Qualys) may trigger cache entries for scanned addresses. Schedule scans during maintenance windows and exclude scanner sources.

## References

- [RFC 6583 — Operational Neighbor Discovery Problems](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 4861 — Neighbor Discovery for IP version 6 (IPv6)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — NDP security)](https://www.rfc-editor.org/rfc/rfc9099)
