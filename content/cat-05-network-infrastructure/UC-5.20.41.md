<!-- AUTO-GENERATED from UC-5.20.41.json — DO NOT EDIT -->

---
id: "5.20.41"
title: "ICMPv6 Extension Header Abuse Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.41 · ICMPv6 Extension Header Abuse Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*IPv6 letters can have extra pages stapled on — instructions for the postman, routing directions, or security seals. Most legitimate letters have zero or one extra page. If we see a letter with eight extra pages of instructions, someone is probably trying to confuse the postman into delivering something they shouldn't. We also watch for letters with old, cancelled routing instructions that were banned 15 years ago — anyone still using them is up to no good.*

---

## Description

Detects abuse of IPv6 extension headers (EHs) for evasion, reconnaissance, and denial-of-service attacks. Extension headers are the IPv6 mechanism that replaces IPv4 options — they form a chain between the fixed IPv6 header and the upper-layer payload. While legitimate uses exist (IPsec, fragmentation, Segment Routing), attackers exploit EHs to evade security inspection (long header chains that exceed IDS parsing budgets), perform source routing attacks (deprecated RH0), force slow-path processing on routers (Hop-by-Hop flooding), and fragment packets to split security-relevant fields across fragments.

## Value

IPv6 extension headers are a blind spot for many security tools. Firewalls and IDS/IPS that handle IPv4 packet inspection well may fail to parse long IPv6 EH chains, allowing malicious payloads to pass uninspected. RFC 7045 specifically warns about this evasion technique. Detecting anomalous EH usage is essential for IPv6 security because it reveals both active evasion attempts and misconfigured devices generating non-compliant traffic. Routing Header Type 0 was deprecated in 2007 (RFC 5095) due to its use in amplification attacks — any RH0 traffic in a modern network is either an attack or a severely misconfigured device.

## Implementation

Deploy Zeek/Corelight sensors on transit links for packet-level extension header analysis. Parse EH chain information from connection logs. Detect banned (RH0), suspicious (long chains, HBH without Router Alert), and anomalous (tiny fragments) patterns.

## Detailed Implementation

### Prerequisites
- Zeek/Corelight sensors on transit links with IPv6 extension header logging enabled.
- Or Palo Alto firewalls with threat logging that captures extension header information.
- Cisco ASA/FTD with `ipv6 extension-header` inspection policy.
- Reference: RFC 5095 (RH0 deprecated), RFC 7045 (EH processing guidance), RFC 9099 §2.5 (operational security).

### Step 1 — Configure data collection

**Zeek — extension header logging:**
Zeek automatically logs extension headers in `conn.log` when IPv6 traffic is observed. No additional configuration needed. The `ext_header_types` field in conn.log contains a comma-separated list of Next Header values in the EH chain.

**Cisco ASA — extension header inspection:**
```
ipv6 icmp permit any any
ipv6 header-chain count 4
policy-map type inspect ipv6
 class type inspect ipv6 match-any BAD_EH
  match header routing-type range 0 0
  match header count gt 4
  parameters
   match header routing-type range 0 0 action drop log
   match header count gt 4 action drop log
```

**Palo Alto — security profile for IPv6 EH:**
Configure a Vulnerability Protection profile with signatures for IPv6 extension header abuse (signature IDs for RH0, fragmentation evasion, long EH chains).

**Verification:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn") ext_header_types=* earliest=-24h
| stats count by ext_header_types
| sort -count
```

### Step 2 — Create the search and alert

**Routing Header Type 0 detection (CRITICAL):**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn" OR sourcetype="paloalto:traffic" OR sourcetype="cisco:ios")
  ("routing header type 0" OR "RH0" OR (ext_header_types=* "43" AND match(_raw, "type.?0")))
  earliest=-24h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| stats count as rh0_count first(_time) as first_seen last(_time) as last_seen by src_ipv6, dst_ipv6
| eval severity="CRITICAL — Routing Header Type 0 is banned by RFC 5095 since 2007"
| eval action="BLOCK immediately. Investigate source device. No legitimate reason for RH0."
```
Trigger: any RH0 detection. Zero false positives in a modern network.

**Long extension header chain detection:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn") ext_header_types=* earliest=-24h
| eval eh_count=mvcount(split(ext_header_types, ","))
| where eh_count > 3
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| stats count as events max(eh_count) as max_chain values(ext_header_types) as eh_chains by src_ipv6
| sort -max_chain
| eval severity=case(
    max_chain > 6, "CRITICAL — likely evasion attempt",
    max_chain > 4, "HIGH — unusual EH chain length",
    1=1, "MEDIUM — investigate")
```
Normal traffic rarely has more than 2 extension headers (Fragment + ESP for IPsec, or HBH + Fragment for MLD). Chains longer than 3 are suspicious; chains longer than 6 are almost certainly malicious or deeply broken.

**Hop-by-Hop flooding (DoS):**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn" OR sourcetype="cisco:ios") earliest=-15m
| eval has_hbh=if(match(_raw, "(?i)hop.?by.?hop|ext_header.*\b0\b"), 1, 0)
| where has_hbh=1
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| stats count as hbh_count by src_ipv6
| where hbh_count > 1000
| eval alert="HBH flooding: " . hbh_count . " packets with Hop-by-Hop options in 15 min from " . src_ipv6
```
Hop-by-Hop options force routers to process packets in the slow path. Flooding routers with HBH packets is a known DoS technique.

### Step 3 — Validate
(a) **Normal traffic baseline.** Review 7 days of EH data. Confirm that most EH usage is Fragment (44) for legitimate fragmentation and ESP (50) for IPsec. HBH (0) should be rare (MLD only). Routing (43) should be absent unless using SRv6.

(b) **RH0 test (lab).** Generate a packet with Routing Header Type 0 using Scapy. Verify Zeek logs the EH chain and the alert fires.

(c) **Long chain test (lab).** Generate a packet with 8 chained extension headers using Scapy. Verify the long chain detection fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Extension Header Security"):
- Row 1 — Single-value: RH0 detections (should always be 0), long chain detections, HBH anomalies.
- Row 2 — Pie chart: EH type distribution across the network.
- Row 3 — Table: all suspicious EH detections with source, destination, chain details, and severity.
- Row 4 — Timechart: EH types over 24 hours.

**Scheduling:** RH0 detection continuous (every 5 minutes). Long chain detection hourly. HBH flooding every 15 minutes.

**Runbook:**
1. RH0 detected: block source at firewall immediately. Investigate source device — this is either an attack or a 15-year-old misconfiguration.
2. Long EH chain: check if the source is a known security testing tool. If not, block and investigate.
3. HBH flooding: rate-limit HBH traffic at the router. Monitor router CPU (UC-5.1.8) for slow-path impact.

### Step 5 — Troubleshooting

- **Zeek not logging ext_header_types** — Ensure Zeek version 4.0+ is deployed. Older versions may not export this field. Check `conn.log` for the field's presence.

- **Distinguishing SRv6 from RH0** — Segment Routing Header (SRH) uses Routing Header type 4, not type 0. The detection should check the routing header type, not just the presence of Next Header 43. Unfortunately, some IDS/IPS tools do not distinguish between routing header types.

- **Atomic fragment false positives** — RFC 8021 deprecated atomic fragments (Fragment Header with offset=0, M=0, no actual fragmentation). Some older devices still generate them. These are not attacks but should be flagged for remediation at the source device.

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn" OR sourcetype="paloalto:traffic") earliest=-24h
| eval has_ext_headers=case(
    isnotnull(ext_header_types), 1,
    match(_raw, "(?i)extension.?header|routing.?header|fragment.?header|hop.?by.?hop"), 1,
    1=1, 0)
| where has_ext_headers=1
| eval eh_types=coalesce(ext_header_types, "unknown")
| eval suspicious=case(
    match(eh_types, "43") AND match(_raw, "type.?0|RH0"), "CRITICAL — Routing Header Type 0 (deprecated/banned by RFC 5095)",
    match(eh_types, "0") AND NOT match(_raw, "(?i)router.?alert"), "HIGH — Hop-by-Hop options (potential slow-path DoS)",
    len(eh_types) > 20, "HIGH — long extension header chain (possible evasion)",
    match(eh_types, "44") AND match(_raw, "(?i)tiny|offset.?0.*len.?[0-7]\b"), "HIGH — tiny fragment attack",
    1=1, null())
| where isnotnull(suspicious)
| table _time, host, src_ip, dst_ip, eh_types, suspicious
```

## Visualization

(1) Table: detected extension header abuse events with classification. (2) Timechart: EH usage by type over 24 hours. (3) Pie chart: EH type distribution — fragmentation should dominate legitimate EH usage, with routing and HBH being rare. (4) Alert panel: active RH0 or evasion detections.

## Known False Positives

**IPsec traffic.** ESP (Next Header 50) and AH (Next Header 51) are legitimate and common extension headers. IPsec VPN traffic will show these EHs on every packet. Exclude known IPsec endpoints from the anomaly detection.

**Segment Routing v6 (SRv6).** Modern SRv6 deployments use Routing Header type-specific to SRv6 (Segment Routing Header, SRH). This is legitimate but looks similar to the deprecated RH0 in basic detection. Distinguish by routing header type: RH0 = type 0 (banned), SRH = type 4 (legitimate).

**Fragment Header for atomic fragments.** RFC 8021 deprecates atomic fragments (Fragment Header with offset=0 and M=0), but some older implementations still generate them. These are not attacks but indicate outdated implementations.

**Hop-by-Hop Router Alert.** MLD (Multicast Listener Discovery) uses the Hop-by-Hop Router Alert option legitimately. MLD packets with HBH are expected on every link with multicast.

## References

- [RFC 8200 — Internet Protocol, Version 6 Specification (§4 — Extension Headers)](https://www.rfc-editor.org/rfc/rfc8200)
- [RFC 5095 — Deprecation of Type 0 Routing Headers in IPv6](https://www.rfc-editor.org/rfc/rfc5095)
- [RFC 7045 — Transmission and Processing of IPv6 Extension Headers](https://www.rfc-editor.org/rfc/rfc7045)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.5 — Extension header security)](https://www.rfc-editor.org/rfc/rfc9099)
