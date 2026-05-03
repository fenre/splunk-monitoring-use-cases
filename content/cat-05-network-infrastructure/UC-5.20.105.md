<!-- AUTO-GENERATED from UC-5.20.105.json — DO NOT EDIT -->

---
id: "5.20.105"
title: "IPv6 Extension Header Chain Anomaly and Evasion Detection"
status: "verified"
criticality: "high"
splunkPillar: "ES"
---

# UC-5.20.105 · IPv6 Extension Header Chain Anomaly and Evasion Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Letters on the new address system (IPv6) can have extra instruction sheets attached to them — like 'read this first' or 'forward this to someone else'. Most normal letters have one or two instruction sheets at most. Burglars sometimes attach many confusing instruction sheets to trick the mail sorter into letting something bad through or to overwhelm the sorter so it stops working. We watch for letters with too many or suspicious instruction sheets.*

---

## Description

Detects anomalous IPv6 extension header chains indicative of firewall/IDS evasion, covert channels, or denial-of-service attacks. Monitors for excessive header chaining (3+ headers), Hop-by-Hop options abuse (router CPU exhaustion), deprecated Routing Header Type 0, unknown header types, and other extension header anomalies per RFC 7045 operational recommendations.

## Value

IPv6 extension headers are the single most exploited feature of IPv6 for security evasion. Many firewalls and IDS devices either skip packets with complex extension header chains or crash when processing malformed chains. Attackers know this and use extension headers to bypass security inspection, exfiltrate data in Destination Options, exhaust router CPUs with Hop-by-Hop Options, and exploit RH0 for traffic amplification. Monitoring extension header anomalies is essential for any IPv6 security programme.

## Implementation

Deploy Zeek or Suricata sensors that parse IPv6 extension headers. Monitor extension header counts and types. Alert on anomalous combinations per RFC 7045 recommendations.

## Detailed Implementation

### Prerequisites
- Zeek or Suricata sensor with IPv6 extension header parsing.
- Sensor positioned to see ingress traffic at network perimeter.

### Step 1 — Configure extension header logging

**Zeek — enable extension header logging:**
Zeek's `conn.log` includes basic IPv6 info. For detailed extension header analysis, load the `ipv6-ext-headers` script:
```zeek
@load policy/protocols/conn/known-hosts
@load misc/detect-traceroute

event ipv6_ext_headers(c: connection, p: pkt_hdr) {
    if (|p$ip6$exts| > 2) {
        NOTICE([$note=Conn::Content_Gap,
                $msg=fmt("IPv6 packet with %d extension headers from %s", |p$ip6$exts|, c$id$orig_h),
                $conn=c]);
    }
}
```

**Suricata rules for extension header anomalies:**
```
alert ipv6 any any -> any any (msg:"IPv6 excessive extension headers"; ipv6.exthdr_count:>3; sid:6000010; rev:1;)
alert ipv6 any any -> any any (msg:"IPv6 Routing Header Type 0 (deprecated)"; ipv6.hdr; content:|3b|; offset:40; sid:6000011; rev:1;)
alert ipv6 any any -> any any (msg:"IPv6 Hop-by-Hop outside MLD"; ipv6.hdr; content:|00|; offset:6; sid:6000012; rev:1;)
```

**Cisco FTD extension header policy:**
```
policy-map type inspect ipv6
 parameters
  verify-header order
  verify-header maximum-count 2
  action drop-log
```

### Step 2 — Create analysis searches

**Extension header type distribution (baseline):**
```spl
index=network sourcetype="zeek:conn" earliest=-7d
| eval has_eh=if(isnotnull(ext_headers), 1, 0)
| where has_eh=1
| stats count by ext_headers
| sort -count
```
Use this to establish a baseline of normal extension header patterns in your environment.

**Hop-by-Hop abuse detection:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  "%IPV6-4" AND "hop-by-hop"
| stats count as events by host
| where events > 100
| eval alert="Router " . host . " is processing excessive Hop-by-Hop options (" . events . " events) — possible CPU exhaustion attack"
```

### Step 3 — Validate
(a) **Controlled test.** Use `scapy` to craft IPv6 packets with various extension header combinations:
```python
from scapy.all import *
pkt = IPv6(dst='2001:db8::1')/IPv6ExtHdrHopByHop()/IPv6ExtHdrDestOpt()/IPv6ExtHdrRouting()/TCP(dport=80)
send(pkt)
```
Verify the sensor detects and logs the anomalous chain.

(b) **RH0 test.** Craft a packet with Routing Header Type 0. Verify the router drops it and logs the event.

(c) **Baseline comparison.** Compare current extension header patterns against the established baseline. New patterns require investigation.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Extension Header Security"):
- Row 1 — Single-values: excessive chain count, RH0 detections, unknown header types.
- Row 2 — Bar chart: anomaly types and counts.
- Row 3 — Table: top sources of anomalous extension headers.
- Row 4 — Timechart: extension header event trends.

**Alert 1:** Any RH0 detection — critical. Active exploit attempt.
**Alert 2:** Excessive chain (5+ headers) — high. Evasion or exploit.
**Alert 3:** Unknown header type — high. Possible fuzzing or zero-day exploit.

### Step 5 — Troubleshooting

- **Sensor doesn't parse extension headers.** Not all network sensors fully parse IPv6 extension header chains. Zeek 5.0+ and Suricata 6.0+ have good support. Older versions may miss complex chains. Upgrade if needed.

- **Firewall passes packets with complex headers.** Some firewalls punt packets with complex extension header chains to the slow path or pass them uninspected. This is exactly the vulnerability attackers exploit. Configure the firewall to explicitly limit extension header chain depth.

- **SRv6 false positives.** If your network uses SRv6 (Segment Routing over IPv6), Routing Header Type 3 packets are expected. Create an exception for known SRv6 infrastructure addresses.

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="suricata:alert" OR sourcetype="cisco:ftd") earliest=-24h
  ("ext_header" OR "extension.*header" OR "next.*header" OR "NH=" OR "hop_by_hop" OR "routing_header")
| eval eh_count=coalesce(tonumber(ext_header_count), len(replace(ext_headers, "[^,]", "")) + 1, 1)
| eval anomaly=case(
    eh_count >= 5, "CRITICAL — excessive extension header chain (" . eh_count . " headers) — likely evasion or DoS",
    match(_raw, "(?i)hop.?by.?hop|NH.?=.?0") AND NOT match(_raw, "(?i)router.?alert|MLD"), "HIGH — Hop-by-Hop options outside MLD/RSVP context — router CPU impact",
    match(_raw, "(?i)routing.*type.?0|RH0"), "CRITICAL — Routing Header Type 0 — deprecated (RFC 5095), traffic amplification attack",
    match(_raw, "(?i)unknown.*header|unrecognized.*next.?header"), "HIGH — unknown extension header type — possible exploit",
    eh_count >= 3, "MEDIUM — unusual extension header chain (" . eh_count . " headers)",
    1=1, null())
| where isnotnull(anomaly)
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ip>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ip>[0-9a-fA-F:.]+)"
| stats count as events dc(src_ip) as sources by host, anomaly
| sort -events
```

## Visualization

(1) Bar chart: extension header anomaly types. (2) Timechart: extension header events over time. (3) Table: top sources of anomalous extension headers. (4) Single-value: excessive chain count (red if >0).

## Known False Positives

**MLD and RSVP.** MLD (Multicast Listener Discovery) and RSVP legitimately use Hop-by-Hop options with the Router Alert option. These are normal and should be excluded from anomaly detection.

**IPsec traffic.** Packets with AH (NH=51) and/or ESP (NH=50) headers are legitimate IPsec traffic. Only flag as anomalous if IPsec is not expected on the segment.

**SRv6 (Segment Routing).** Routing Header Type 3 (SRv6) can legitimately create extension header chains. If SRv6 is deployed, baseline the expected header patterns.

**Mobile IPv6.** Routing Header Type 2 is used for Mobile IPv6 home-to-care-of address routing. If Mobile IPv6 is deployed, this is expected.

## References

- [RFC 7045 — Transmission and Processing of IPv6 Extension Headers (operational recommendations)](https://www.rfc-editor.org/rfc/rfc7045)
- [RFC 8200 — Internet Protocol, Version 6 (IPv6) Specification (§4 — extension headers)](https://www.rfc-editor.org/rfc/rfc8200#section-4)
- [RFC 5095 — Deprecation of Type 0 Routing Headers in IPv6](https://www.rfc-editor.org/rfc/rfc5095)
- [RFC 9288 — Recommendations on the Filtering of IPv6 Packets Containing IPv6 Extension Headers at Transit Routers](https://www.rfc-editor.org/rfc/rfc9288)
