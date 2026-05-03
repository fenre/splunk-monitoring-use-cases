<!-- AUTO-GENERATED from UC-5.20.115.json — DO NOT EDIT -->

---
id: "5.20.115"
title: "IPv6-to-IPv4 Protocol Translation (NAT64/SIIT) Health Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.115 · IPv6-to-IPv4 Protocol Translation (NAT64/SIIT) Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*When someone using only the new address system (IPv6) wants to talk to someone who only understands the old address system (IPv4), they need a translator in the middle — like an interpreter at the United Nations. We monitor this interpreter to make sure they're not overwhelmed with too many conversations at once, that they're translating correctly, and that they have enough old addresses to assign to the new-address speakers.*

---

## Description

Monitors NAT64 (RFC 6146), SIIT (RFC 7915), and 464XLAT (RFC 6877) protocol translation gateways for session table exhaustion, translation failures, IPv4 address pool depletion, and performance degradation. These translators are critical infrastructure for IPv6-only networks that must communicate with IPv4-only services.

## Value

As organisations move toward IPv6-only networks (per OMB M-21-07 and general industry trend), NAT64 becomes a critical single point of failure. When NAT64 goes down, every IPv6-only client loses access to all IPv4-only content — effectively a total internet outage for those clients. Monitoring NAT64 health, session table utilisation, and translation success rate is essential for maintaining connectivity during the IPv6 transition.

## Implementation

Monitor NAT64 session table utilisation, translation success/failure rates, IPv4 pool utilisation, and DNS64 synthesis health. Alert on session exhaustion and translation failures.

## Detailed Implementation

### Prerequisites
- NAT64 gateway deployed (Cisco ASR/C8000, Juniper MX, or Linux Jool).
- DNS64 resolver configured.
- NAT64 logging enabled.

### Step 1 — Configure NAT64 monitoring

**Cisco IOS-XE NAT64 configuration and logging:**
```
nat64 prefix stateful 64:ff9b::/96
nat64 v4 pool NAT64-POOL 203.0.113.0 203.0.113.255
nat64 v6v4 static 2001:db8::1 203.0.113.1
!
nat64 translation timeout tcp 3600
nat64 translation timeout udp 300
!
logging buffered 8192 informational
```

**Session table monitoring (SNMP or CLI polling):**
```
show nat64 statistics
show nat64 translations
```
Poll via scripted input and send to Splunk.

**DNS64 configuration (BIND 9):**
```
options {
    dns64 64:ff9b::/96 {
        clients { any; };
        mapped { !rfc1918; any; };
        suffix ::;
    };
};
```

### Step 2 — Create monitoring searches

**NAT64 session table utilization:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-1h
  "nat64" AND ("session" OR "translation")
| rex field=_raw "active\s+(?<active_sessions>\d+)"
| rex field=_raw "(?:max|limit)\s+(?<max_sessions>\d+)"
| eval utilization=round(tonumber(active_sessions) / tonumber(max_sessions) * 100, 1)
| stats latest(utilization) as current_pct latest(active_sessions) as sessions by host
| eval status=case(
    current_pct > 90, "CRITICAL — session table " . current_pct . "% full",
    current_pct > 75, "WARNING — session table " . current_pct . "% full",
    1=1, "OK — " . current_pct . "%")
```

**DNS64 synthesis verification:**
```spl
index=dns sourcetype="named:querylog" earliest=-4h
  "dns64" OR "64:ff9b"
| eval synthesised=if(match(_raw, "64:ff9b"), 1, 0)
| stats count as total sum(synthesised) as dns64_responses
| eval dns64_pct=round(dns64_responses / total * 100, 1)
| eval status=if(dns64_responses > 0, "DNS64 active — " . dns64_responses . " synthesised responses", "DNS64 NOT WORKING — no synthesised responses")
```

### Step 3 — Validate
(a) **End-to-end test.** From an IPv6-only client, access an IPv4-only website. Verify the connection succeeds via NAT64/DNS64.

(b) **DNS64 test.** `dig AAAA ipv4only.arpa @<dns64-resolver>`. Should return `64:ff9b::c000:aa` (the well-known NAT64 test domain).

(c) **Session table test.** Generate high connection volume through NAT64. Monitor session table growth and verify it doesn't exceed limits.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NAT64/DNS64 Health"):
- Row 1 — Gauges: NAT64 session table utilization per device.
- Row 2 — Timechart: translations per second.
- Row 3 — Single-values: translation failures, pool utilization.
- Row 4 — DNS64 synthesis status.

**Alert 1:** Session table >90% — critical.
**Alert 2:** IPv4 pool utilization >90% — critical.
**Alert 3:** Translation failures >100/hour — high.

### Step 5 — Troubleshooting

- **Session table full.** Reduce TCP timeout (`nat64 translation timeout tcp 1800`). Enable session logging to identify top consumers. Consider adding more IPv4 pool addresses or deploying additional NAT64 instances.

- **DNS64 not synthesising.** Verify the DNS64 prefix matches the NAT64 prefix. Check that `dns64` is enabled in BIND configuration. Test with `dig AAAA ipv4only.arpa`.

- **Application failures through NAT64.** Some applications embed IPv4 addresses in payloads (FTP, SIP, RTSP). These require ALGs. If an ALG is not available, consider running the application in dual-stack mode or using 464XLAT on the client.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos") earliest=-4h
  ("%NAT64" OR "%NAT-6" OR "nat64" OR "stateful64" OR "SIIT" OR "464XLAT")
| eval nat64_event=case(
    match(_raw, "(?i)session.*table.*full|translation.*limit|pool.*exhaust"), "SESSION_EXHAUSTION",
    match(_raw, "(?i)translation.*fail|nat64.*drop|cannot.*translate"), "TRANSLATION_FAILURE",
    match(_raw, "(?i)pool.*low|address.*running|threshold"), "POOL_LOW",
    match(_raw, "(?i)session.*create|translation.*created"), "SESSION_CREATED",
    match(_raw, "(?i)hairpin|v6v6"), "HAIRPIN",
    1=1, "OTHER")
| stats count as events by host, nat64_event
| eval severity=case(
    nat64_event="SESSION_EXHAUSTION", "CRITICAL — NAT64 session table full — IPv6-only clients losing IPv4 access",
    nat64_event="TRANSLATION_FAILURE" AND events > 100, "HIGH — translation failures (" . events . ") — protocol or ALG issue",
    nat64_event="POOL_LOW", "WARNING — NAT64 IPv4 address pool running low",
    nat64_event="HAIRPIN" AND events > 50, "MEDIUM — NAT64 hairpinning detected (performance impact)",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Gauge: NAT64 session table utilization. (2) Timechart: translations per second. (3) Single-value: translation failure rate. (4) Table: NAT64 devices with health status.

## Known False Positives

**High legitimate translation volume.** During peak hours, NAT64 session creation rates increase naturally. Baseline the normal peak rate before setting alert thresholds.

**ALG-related failures.** Some application protocols (FTP active mode, SIP without IPv6 support) fail through NAT64 by design, not due to a NAT64 malfunction. These are expected failures.

**DNS64 NXDOMAIN.** When a domain doesn't exist (NXDOMAIN), DNS64 correctly returns NXDOMAIN. This is not a DNS64 failure.

## References

- [RFC 6146 — Stateful NAT64: Network Address and Protocol Translation from IPv6 Clients to IPv4 Servers](https://www.rfc-editor.org/rfc/rfc6146)
- [RFC 6147 — DNS64: DNS Extensions for Network Address Translation from IPv6 Clients to IPv4 Servers](https://www.rfc-editor.org/rfc/rfc6147)
- [RFC 6877 — 464XLAT: Combination of Stateful and Stateless Translation](https://www.rfc-editor.org/rfc/rfc6877)
