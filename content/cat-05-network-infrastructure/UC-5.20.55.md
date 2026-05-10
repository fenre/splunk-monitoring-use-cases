<!-- AUTO-GENERATED from UC-5.20.55.json — DO NOT EDIT -->

---
id: "5.20.55"
title: "DNS Resolver IPv6 Transport Health (Do53/DoT/DoH over IPv6)"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.55 · DNS Resolver IPv6 Transport Health (Do53/DoT/DoH over IPv6)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Our phone book lookup service needs to call other phone book services around the world to find answers. It can call them using the old phone system (IPv4) or the new phone system (IPv6). We compare how often calls on each system fail. If the new phone system is dropping more calls than the old one, there's a problem with our new phone line to the outside world.*

---

## Description

Monitors the DNS resolver's ability to reach authoritative nameservers over IPv6 transport, detecting IPv6-specific DNS resolution failures that would cause SERVFAIL responses for domains served by IPv6-only nameservers. As more authoritative nameservers become IPv6-enabled (and some ccTLDs have IPv6-only NS records), the resolver's IPv6 transport health directly impacts DNS resolution reliability.

## Value

A DNS resolver that cannot reach authoritative servers over IPv6 will fail to resolve any domain served exclusively by IPv6-only nameservers. While this is currently rare, the number of IPv6-only authoritative servers is growing. More commonly, if a resolver's IPv6 transport is intermittently failing, it causes sporadic SERVFAIL responses that are difficult to troubleshoot because the failures depend on which authoritative server the resolver happens to contact — if it picks an IPv4 server, the query succeeds; if it picks an IPv6 server, it fails. Monitoring IPv6 vs IPv4 transport failure rates reveals this intermittent pattern.

## Implementation

Collect DNS resolver upstream query logs. Parse the transport protocol (IPv4 vs IPv6) used for upstream queries. Compare failure rates between IPv4 and IPv6 transport. Alert on elevated IPv6 transport failures.

## Detailed Implementation

### Prerequisites
- DNS resolver with upstream query logging that includes the transport address (IPv4 or IPv6) and outcome.
- The resolver must be configured to use both IPv4 and IPv6 transport for upstream queries (dual-stack resolver).
- Understanding of the resolver's upstream connectivity paths.

### Step 1 — Configure data collection

**BIND — query logging with upstream transport:**
BIND logs the upstream server address in its response log when `category resolver` is enabled:
```
logging {
  channel resolver_log {
    syslog local3;
    severity info;
    print-time yes;
  };
  category resolver { resolver_log; };
};
```
Sample log: `resolver: query 'example.com/AAAA/IN' to 2001:500:2d::d#53 timed out`

**Unbound — verbosity level 2+:**
```
server:
  verbosity: 2
  log-queries: yes
  log-replies: yes
```

**Verification:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") ("to" OR "sending") ("#53" OR "#853") earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**IPv6 vs IPv4 transport comparison:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") ("to" AND ("#53" OR "#853")) earliest=-24h
| rex field=_raw "to\s+(?<upstream_server>[0-9a-fA-F:.]+)#"
| eval transport=if(match(upstream_server, ":"), "IPv6", "IPv4")
| eval failed=if(match(_raw, "(?i)timeout|SERVFAIL|refused|error"), 1, 0)
| stats count as queries sum(failed) as failures by transport
| eval failure_rate_pct=round(failures / queries * 100, 2)
```

**IPv6 transport failure alert:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") earliest=-1h
| rex field=_raw "to\s+(?<upstream>[0-9a-fA-F:.]+)#"
| eval is_v6=if(match(upstream, ":"), 1, 0)
| eval is_fail=if(match(_raw, "(?i)timeout|SERVFAIL"), 1, 0)
| stats sum(eval(is_v6 * is_fail)) as v6_failures sum(is_v6) as v6_total sum(eval((1-is_v6) * is_fail)) as v4_failures sum(eval(1-is_v6)) as v4_total
| eval v6_rate=round(v6_failures / v6_total * 100, 2)
| eval v4_rate=round(v4_failures / v4_total * 100, 2)
| where v6_rate > v4_rate + 5
| eval alert="IPv6 DNS transport failure rate (" . v6_rate . "%) significantly exceeds IPv4 (" . v4_rate . "%) — investigate IPv6 connectivity to upstream nameservers"
```
Trigger: IPv6 failure rate more than 5 percentage points higher than IPv4.

### Step 3 — Validate
(a) **Normal operation.** Verify that IPv6 and IPv4 failure rates are similar (within 1-2%).

(b) **IPv6 transport block.** Temporarily block outbound IPv6 UDP/TCP port 53 at the firewall. Verify IPv6 failure rate spikes while IPv4 remains normal.

(c) **IPv6-only authoritative test.** Query a domain with IPv6-only NS records. Verify the query is resolved over IPv6 transport.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DNS Transport Health"):
- Row 1 — Dual gauge: IPv4 transport success rate vs IPv6 transport success rate.
- Row 2 — Timechart: IPv6 upstream failures vs IPv4 upstream failures over 24 hours.
- Row 3 — Table: upstream nameservers with highest IPv6 failure rates.

**Scheduling:** Transport health comparison every 15 minutes. Alert on disparity continuous.

**Runbook:**
1. Elevated IPv6 DNS transport failures: check resolver IPv6 connectivity. Test: `dig +tcp @2001:500:2d::d example.com AAAA` (tests IPv6 transport to a root server).
2. Specific nameserver failing: check if that nameserver's IPv6 address is reachable. Check for firewall rules blocking IPv6 port 53.
3. All IPv6 transport failing: check resolver's IPv6 default route, IPv6 interface status, and upstream firewall rules.

### Step 5 — Troubleshooting

- **BIND do-not-query-localhost** — BIND's `do-not-query-localhost` option may inadvertently block queries to ::1 if the resolver is also acting as an authoritative server on the same host.

- **Source address selection** — The resolver's IPv6 source address for upstream queries depends on the routing table and source address selection algorithm (RFC 6724). If the selected source address is a temporary privacy address, some upstream servers may refuse queries from non-stable addresses.

- **DNS flag day** — DNS Flag Day 2020 required support for EDNS0 buffer sizes of at least 1232 bytes over IPv6. Resolvers that do not support EDNS0 or that set buffer sizes below 1232 bytes may experience failures with IPv6 DNS transport.

## SPL

```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") earliest=-24h
| eval upstream_transport=case(
    match(_raw, "(?:query|sending).*(?:via|to)\s*[0-9a-fA-F]+:[0-9a-fA-F:]+"), "IPv6",
    match(_raw, "(?:query|sending).*(?:via|to)\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"), "IPv4",
    1=1, null())
| where isnotnull(upstream_transport)
| eval outcome=case(
    match(_raw, "SERVFAIL|timeout|refused"), "failure",
    match(_raw, "NOERROR|success"), "success",
    1=1, "other")
| stats count(eval(upstream_transport="IPv6" AND outcome="success")) as v6_success count(eval(upstream_transport="IPv6" AND outcome="failure")) as v6_fail count(eval(upstream_transport="IPv4" AND outcome="success")) as v4_success count(eval(upstream_transport="IPv4" AND outcome="failure")) as v4_fail
| eval v6_failure_rate=round(v6_fail / (v6_success + v6_fail) * 100, 2)
| eval v4_failure_rate=round(v4_fail / (v4_success + v4_fail) * 100, 2)
| eval disparity=v6_failure_rate - v4_failure_rate
| eval health=case(
    disparity > 5, "WARNING — IPv6 DNS transport failure rate significantly higher than IPv4",
    v6_failure_rate > 1, "MONITOR — elevated IPv6 DNS failures",
    1=1, "OK")
```

## Visualization

(1) Dual gauge: IPv4 vs IPv6 DNS transport success rates. (2) Timechart: IPv6 upstream query failures over 24 hours. (3) Table: upstream nameservers with highest IPv6 failure rates. (4) Comparison chart: IPv4 vs IPv6 transport health over 7 days.

## Known False Positives

**Authoritative server maintenance.** When an authoritative nameserver is temporarily offline, queries to it fail regardless of transport version. This is not an IPv6 transport issue but a server availability issue.

**Network-specific IPv6 issues.** If the resolver's IPv6 upstream connectivity has a specific routing problem (e.g., a particular transit provider has IPv6 issues), only queries routed through that path will fail. This is a real problem but may not affect all IPv6 queries.

**EDNS0 interaction.** Large DNS responses (>1280 bytes) over IPv6 UDP may fail if the path has an MTU constraint. The resolver should fall back to TCP, but if TCP is also blocked, the query fails. This is technically an MTU/firewall issue, not a transport issue.

## References

- [RFC 3901 — DNS IPv6 Transport Operational Guidelines](https://www.rfc-editor.org/rfc/rfc3901)
- [RFC 7858 — Specification for DNS over Transport Layer Security (DoT)](https://www.rfc-editor.org/rfc/rfc7858)
- [RFC 8484 — DNS Queries over HTTPS (DoH)](https://www.rfc-editor.org/rfc/rfc8484)
