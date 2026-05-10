<!-- AUTO-GENERATED from UC-5.20.47.json — DO NOT EDIT -->

---
id: "5.20.47"
title: "IPv6 Route Redistribution Loop and Leak Prevention"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.20.47 · IPv6 Route Redistribution Loop and Leak Prevention

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Security &middot; **Wave:** Run &middot; **Status:** Verified

*Different parts of the network use different road-mapping systems. Sometimes they need to share their maps with each other — that's redistribution. The problem is, if you share everything without checking, you might share directions to your private driveway with the whole world, or create circular directions where cars go round and round forever.*

---

## Description

Detects IPv6 route redistribution anomalies including routing loops from bidirectional redistribution, accidental leaking of link-local or ULA prefixes into external routing, and injection of bogon prefixes through redistribution without proper filtering. Route redistribution is the #1 cause of self-inflicted IPv6 routing outages because operators apply IPv4 redistribution patterns without accounting for IPv6-specific address types (link-local, ULA) that must never be redistributed.

## Value

A single misconfigured redistribution statement can take down an entire IPv6 network. Redistributing BGP full table into an IGP floods the IGP with 220,000+ prefixes, overwhelming CPU and memory on every router in the area. Redistributing link-local prefixes creates unreachable routes that blackhole traffic. Bidirectional redistribution creates loops that cause packets to circle until hop-limit expiry. Detecting these conditions in real-time — before they propagate through the network — is the difference between a 30-second incident and a 30-minute outage.

## Implementation

Monitor routing protocol syslog for redistribution events. Parse source/destination protocols and redistributed prefixes. Flag link-local redistributions (FE80::/10), bogon redistributions, and routing loop indicators. Alert on any redistribution anomaly.

## Detailed Implementation

### Prerequisites
- Route redistribution is configured between IPv6 routing protocols.
- Syslog forwarding capturing routing protocol events.
- Configuration data available for redistribution policy audit.

### Step 1 — Configure data collection

**Collect both syslog and configuration data.** Redistribution anomalies are detected from two sources:
1. **Syslog** — real-time events when problematic routes are redistributed.
2. **Configuration** — audit redistribution statements for missing route-maps/prefix-lists.

**Cisco IOS-XE — correct IPv6 redistribution with filtering:**
```
ipv6 prefix-list NO_LINKLOCAL seq 5 deny FE80::/10 le 128
ipv6 prefix-list NO_LINKLOCAL seq 10 deny FC00::/7 le 128
ipv6 prefix-list NO_LINKLOCAL seq 15 deny FF00::/8 le 128
ipv6 prefix-list NO_LINKLOCAL seq 20 permit ::/0 le 128

route-map REDIST_TO_BGP permit 10
 match ipv6 address prefix-list NO_LINKLOCAL

router bgp 65001
 address-family ipv6 unicast
  redistribute ospf 1 route-map REDIST_TO_BGP
```

**Verification (configuration audit):**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?<redist_line>redistribute\s+(?:ospf|isis|bgp|static|connected)\s+[^\n]+)"
| mvexpand redist_line
| eval has_filter=if(match(redist_line, "route-map|prefix-list"), "yes", "NO FILTER")
| where has_filter="NO FILTER" AND match(redist_line, "(?i)ipv6|address-family ipv6")
| eval issue="CRITICAL — IPv6 redistribution without route-map or prefix-list. All prefixes including link-local will be redistributed."
| table host, redist_line, issue
```

### Step 2 — Create the search and alert

**Unfiltered redistribution alert (configuration audit):**
Use the verification search from Step 1. This catches the most dangerous condition: redistribution without any filtering.

**Link-local prefix in routing table detection:**
```spl
index=network sourcetype="cisco:ios" ("ipv6 route" OR "%ROUTING") earliest=-24h
| rex field=_raw "(?<prefix>[Ff][Ee][89AaBb][0-9a-fA-F]:[0-9a-fA-F:/]+)"
| where isnotnull(prefix)
| eval issue="CRITICAL — link-local prefix " . prefix . " found in routing table. Link-local routes must never be redistributed."
| table _time, host, prefix, issue
```
Trigger: any link-local prefix (FE80::/10) appearing in the routing table with a protocol source other than 'connected'.

**Routing loop detection (Time Exceeded spike correlated with redistribution):**
```spl
index=network sourcetype="cisco:ios" earliest=-1h
| eval event_type=case(
    match(_raw, "(?i)redistrib|import"), "redistribution",
    match(_raw, "(?i)time.?exceeded|hop.?limit"), "time_exceeded",
    match(_raw, "(?i)routing.*loop"), "routing_loop",
    1=1, null())
| where isnotnull(event_type)
| stats count by event_type
| eval potential_loop=if(event_type="time_exceeded" AND count > 100, "WARNING — possible routing loop causing Time Exceeded messages", null())
```

### Step 3 — Validate
(a) **Configuration audit.** Run the unfiltered redistribution search. Verify it correctly identifies redistribution statements without route-maps.

(b) **Link-local test (lab).** Redistribute connected routes without a prefix-list that filters FE80::/10. Verify link-local prefixes appear in the routing table and the alert fires.

(c) **Redistribution loop test (lab).** Set up bidirectional redistribution between OSPFv3 and BGP without route-maps. Verify routes are learned from both protocols and the routing loop indicators appear.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Route Redistribution Audit"):
- Row 1 — Single-value: unfiltered redistribution statements (should be 0), link-local leaks (should be 0).
- Row 2 — Table: all redistribution statements with filter status (has route-map: yes/no).
- Row 3 — Alert panel: active redistribution anomalies.
- Row 4 — Redistribution topology: which protocols are redistributing into which.

**Scheduling:** Configuration audit daily. Link-local leak detection continuous. Routing loop correlation hourly.

**Runbook:**
1. Unfiltered redistribution: URGENT — add a route-map with prefix-list that blocks FE80::/10, FC00::/7, and FF00::/8 at minimum.
2. Link-local in routing table: remove the offending redistribution or add a deny entry for FE80::/10.
3. Routing loop: identify the bidirectional redistribution points. Add route tags and filter to prevent re-import.

### Step 5 — Troubleshooting

- **Route tags for loop prevention** — Use route tags to mark redistributed routes. When redistributing from protocol A to B, tag the routes. When redistributing from B to A, deny routes with that tag. This is the standard loop-prevention mechanism.

- **Administrative distance manipulation** — Setting different AD values for different route sources can prevent suboptimal path selection in redistribution scenarios. However, AD manipulation alone does not prevent loops.

- **IPv6 prefix-list syntax** — Cisco IOS-XE IPv6 prefix-lists use `ipv6 prefix-list` (not `ip prefix-list`). A common error is using `ip prefix-list` which only matches IPv4 prefixes, leaving IPv6 routes unfiltered.

## SPL

```spl
index=network sourcetype="cisco:ios" earliest=-24h
  (("%BGP" OR "%OSPF" OR "%ISIS" OR "%RIP") AND ("redistrib" OR "import" OR "inject"))
  OR ("%ROUTING" AND "loop")
| rex field=_raw "(?:from|source)\s+(?<source_protocol>\S+).*?(?:to|into)\s+(?<dest_protocol>\S+)"
| rex field=_raw "(?:prefix|route|network)\s+(?<prefix>[0-9a-fA-F:/]+)"
| eval is_link_local=if(match(prefix, "^[Ff][Ee][89AaBb]"), 1, 0)
| eval is_bogon=if(match(prefix, "^(?:0{1,4}::|[Ff]{2}|[Ff][Ee][CcDdEeFf]|100::|64:ff9b::)"), 1, 0)
| eval issue=case(
    is_link_local=1, "CRITICAL — link-local prefix redistributed into routing protocol",
    is_bogon=1, "HIGH — bogon/reserved prefix redistributed",
    match(_raw, "(?i)loop"), "CRITICAL — routing loop detected",
    1=1, null())
| where isnotnull(issue)
| table _time, host, source_protocol, dest_protocol, prefix, issue
```

## Visualization

(1) Table: all redistribution anomalies with source, destination, prefix, and issue. (2) Network diagram: redistribution relationships between protocols (nodes=protocols, edges=redistribution, red=anomaly). (3) Timechart: redistribution events over 24 hours. (4) Single-value: active redistribution anomalies.

## Known False Positives

**Intentional redistribution with route-maps.** Controlled redistribution with prefix-lists and route-maps is a legitimate operational practice. The audit should check for redistribution without filtering, not all redistribution.

**Default route redistribution.** Redistributing a static default route (::0/0) from static into IGP is a common and legitimate pattern for providing internet access. The default route prefix should be excluded from bogon checks.

**Connected route redistribution.** Redistributing connected routes (directly-connected subnets) into an IGP is normal. The check should focus on whether link-local connected routes (FE80::/10) are accidentally included.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.2.3 — route filtering recommendations)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 4193 — Unique Local IPv6 Unicast Addresses (fc00::/7 — must not be redistributed to internet)](https://www.rfc-editor.org/rfc/rfc4193)
- [Cisco IPv6 Route Redistribution Best Practices](https://www.cisco.com/c/en/us/support/docs/ip/ip-routing/200756-understand-ospfv3-to-bgp-redistribution.html)
