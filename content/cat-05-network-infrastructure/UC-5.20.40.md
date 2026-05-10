<!-- AUTO-GENERATED from UC-5.20.40.json — DO NOT EDIT -->

---
id: "5.20.40"
title: "ICMPv6 Informational Message Baseline and Abuse Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.40 · ICMPv6 Informational Message Baseline and Abuse Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*The network is always chattering — devices asking 'are you there?' and replying 'yes, I'm here', routers announcing themselves, and groups of devices joining conversations.*

---

## Description

Baselines ICMPv6 informational message rates (Types 128+) and detects abuse patterns including ping floods (DoS/DDoS), NDP exhaustion scans, and IPv6 address reconnaissance. While individual NDP and multicast types are covered by dedicated use cases (UC-5.20.20 through UC-5.20.28), this composite view provides a holistic ICMPv6 informational plane analysis — detecting anomalies in the overall distribution and identifying new attack patterns that may not match individual type-specific detections.

## Value

ICMPv6 informational messages carry the control plane of IPv6. Their rates and distribution form a fingerprint of normal network behaviour. Deviations from this fingerprint indicate either attack activity (floods, scans, spoofing) or infrastructure changes (new network segments, multicast group changes). A composite view catches cross-type anomalies that individual detections miss — for example, a simultaneous spike in Type 133 (RS) and Type 135 (NS) from a single source may indicate a device performing aggressive network discovery or a compromised host probing the network.

## Implementation

Collect ICMPv6 informational message counters via NetFlow/IPFIX and/or SNMP (RFC 4293 ipv6IfIcmp* counters). Baseline rates per type per network segment. Detect anomalies using statistical methods. Alert on floods, sequential probes, and distribution changes.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX with ICMPv6 type and code fields exported (same record as UC-5.20.38/39).
- Optionally, SNMP polling of RFC 4293 ipv6IfIcmp counters for all informational types.
- At least 7 days of baseline data.

### Step 1 — Configure data collection

Use the same NetFlow flow record as UC-5.20.38 (includes ICMPv6 type and code). For SNMP, poll the following OIDs per interface via SC4SNMP:

```yaml
# SC4SNMP polling profile for ICMPv6 informational counters
profile: ipv6_icmpv6_info
frequency: 60
varBinds:
  - ['1.3.6.1.2.1.56.1.1.1.12']  # ipv6IfIcmpInEchos
  - ['1.3.6.1.2.1.56.1.1.1.13']  # ipv6IfIcmpInEchoReplies
  - ['1.3.6.1.2.1.56.1.1.1.18']  # ipv6IfIcmpInRouterSolicits
  - ['1.3.6.1.2.1.56.1.1.1.19']  # ipv6IfIcmpInRouterAdvertisements
  - ['1.3.6.1.2.1.56.1.1.1.20']  # ipv6IfIcmpInNeighborSolicits
  - ['1.3.6.1.2.1.56.1.1.1.21']  # ipv6IfIcmpInNeighborAdvertisements
  - ['1.3.6.1.2.1.56.1.1.1.22']  # ipv6IfIcmpInRedirects
```

**Verification:**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios" OR sourcetype="sc4snmp:metric") earliest=-24h
| eval has_icmpv6=if(match(_raw, "(?i)echo|neighbor|router.?solic|MLD|icmpv6"), 1, 0)
| stats sum(has_icmpv6) as icmpv6_events by sourcetype
```

### Step 2 — Create the search and alert

**Full informational type distribution:**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-24h
| eval icmpv6_info_type=case(
    match(_raw, "(?i)echo.?req|icmpv6.?type.?=?\s*128"), "Echo Request",
    match(_raw, "(?i)echo.?rep|icmpv6.?type.?=?\s*129"), "Echo Reply",
    match(_raw, "(?i)router.?solic|icmpv6.?type.?=?\s*133"), "Router Sol.",
    match(_raw, "(?i)router.?advert|icmpv6.?type.?=?\s*134"), "Router Adv.",
    match(_raw, "(?i)neighbor.?solic|icmpv6.?type.?=?\s*135"), "Neighbor Sol.",
    match(_raw, "(?i)neighbor.?advert|icmpv6.?type.?=?\s*136"), "Neighbor Adv.",
    match(_raw, "(?i)redirect|icmpv6.?type.?=?\s*137"), "Redirect",
    match(_raw, "(?i)MLD|listener|icmpv6.?type.?=?\s*(130|131|132|143)"), "MLD",
    1=1, null())
| where isnotnull(icmpv6_info_type)
| stats count by icmpv6_info_type
| eventstats sum(count) as total
| eval pct=round(count/total*100, 1)
```

**Ping flood detection (Type 128 from a single source):**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-15m
| eval is_echo_req=if(match(_raw, "(?i)echo.?req|icmpv6.?type.?=?\s*128"), 1, 0)
| where is_echo_req=1
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| stats count as echo_count by src_ipv6
| where echo_count > 5000
| eval alert="ICMPv6 ping flood: " . echo_count . " Echo Requests in 15 minutes from " . src_ipv6
```

**Address reconnaissance detection (sequential probing):**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-1h
| eval is_echo_req=if(match(_raw, "(?i)echo.?req|icmpv6.?type.?=?\s*128"), 1, 0)
| where is_echo_req=1
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| rex field=dst_ipv6 "(?<dst_prefix>[0-9a-fA-F:]+:)[0-9a-fA-F]+$"
| stats dc(dst_ipv6) as unique_targets by src_ipv6, dst_prefix
| where unique_targets > 50
| eval alert="IPv6 address scan: " . unique_targets . " unique targets in " . dst_prefix . "/64 from " . src_ipv6
```
Trigger: A single source sending Echo Requests to more than 50 unique addresses within the same /64 is likely performing address reconnaissance (RFC 7707).

### Step 3 — Validate
(a) **Normal baseline.** Over a 7-day period, confirm that the type distribution is stable (e.g., Neighbor Sol/Adv dominate, Echo Request/Reply are consistent, MLD is periodic).

(b) **Ping flood test.** From a test host, run `ping6 -c 10000 -f <target>`. Verify the flood detection alert fires.

(c) **Address scan test.** From a test host, ping a sequential range of addresses in a /64. Verify the reconnaissance detection alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — ICMPv6 Informational Plane"):
- Row 1 — Pie chart: type distribution (normal fingerprint).
- Row 2 — Stacked area timechart: all informational types over 24 hours.
- Row 3 — Top echo sources: hosts generating the most Echo Requests.
- Row 4 — Alerts: active flood and reconnaissance detections.

**Scheduling:** Type distribution baseline daily. Flood detection every 15 minutes. Reconnaissance detection hourly.

**Runbook:**
1. Ping flood: identify source, apply rate limiting at the access switch, investigate whether the host is compromised.
2. Address scan: investigate the source — legitimate scan or attacker? If attacker, block at firewall and alert SOC.
3. Distribution shift: investigate new type ratios — new network segment, multicast application deployment, or configuration change.

### Step 5 — Troubleshooting

- **High NS/NA baseline** — Neighbor Solicitation and Neighbor Advertisement typically account for 60-80% of ICMPv6 informational traffic. This is normal — NDP is the most active ICMPv6 subsystem. Do not alert on high NS/NA volumes unless they deviate from the per-VLAN baseline.

- **Echo Request asymmetry** — Seeing more Echo Requests than Echo Replies may indicate a firewall blocking replies, or destination hosts being unreachable. A 1:1 ratio is normal for successful ping.

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-24h
| eval icmpv6_info_type=case(
    match(_raw, "(?i)echo.?req|icmpv6.?type.?=?\s*128\b"), "Type 128 — Echo Request",
    match(_raw, "(?i)echo.?rep|icmpv6.?type.?=?\s*129\b"), "Type 129 — Echo Reply",
    match(_raw, "(?i)MLD.?query|listener.?query|icmpv6.?type.?=?\s*130\b"), "Type 130 — MLD Query",
    match(_raw, "(?i)MLD.?report|listener.?report|icmpv6.?type.?=?\s*131\b"), "Type 131 — MLD Report",
    match(_raw, "(?i)MLD.?done|listener.?done|icmpv6.?type.?=?\s*132\b"), "Type 132 — MLD Done",
    match(_raw, "(?i)router.?solic|icmpv6.?type.?=?\s*133\b"), "Type 133 — Router Sol.",
    match(_raw, "(?i)router.?advert|icmpv6.?type.?=?\s*134\b"), "Type 134 — Router Adv.",
    match(_raw, "(?i)neighbor.?solic|icmpv6.?type.?=?\s*135\b"), "Type 135 — Neighbor Sol.",
    match(_raw, "(?i)neighbor.?advert|icmpv6.?type.?=?\s*136\b"), "Type 136 — Neighbor Adv.",
    match(_raw, "(?i)redirect|icmpv6.?type.?=?\s*137\b"), "Type 137 — Redirect",
    match(_raw, "(?i)MLDv2|icmpv6.?type.?=?\s*143\b"), "Type 143 — MLDv2 Report",
    1=1, null())
| where isnotnull(icmpv6_info_type)
| timechart span=1h count by icmpv6_info_type
```

## Visualization

(1) Stacked area chart: ICMPv6 informational types over 24 hours — shows the normal distribution pattern. (2) Pie chart: type distribution (should be relatively stable). (3) Top sources: hosts generating the most informational messages. (4) Anomaly overlay: highlight periods with abnormal type distribution.

## Known False Positives

**Network management tools.** NMS platforms (SolarWinds, PRTG, LibreNMS) generate continuous ping (Type 128) traffic for uptime monitoring. These produce steady, high-volume Echo Request traffic that should be excluded from anomaly detection via source IP allow-listing.

**MLD spikes during IPTV events.** MLD Report (Type 131/143) volumes spike when many users join multicast groups simultaneously — for example, at the start of a live sports broadcast. This is normal.

**SLAAC onboarding.** When many devices boot simultaneously (morning onboarding, VLAN migration), Router Solicitation (Type 133) and Neighbor Solicitation (Type 135) spike proportionally. This is a normal operational pattern.

## References

- [RFC 4443 — ICMPv6 Specification](https://www.rfc-editor.org/rfc/rfc4443)
- [RFC 7707 — Network Reconnaissance in IPv6 Networks (address scanning techniques using ICMPv6)](https://www.rfc-editor.org/rfc/rfc7707)
- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
