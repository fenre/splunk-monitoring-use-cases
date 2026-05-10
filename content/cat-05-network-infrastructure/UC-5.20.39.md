<!-- AUTO-GENERATED from UC-5.20.39.json — DO NOT EDIT -->

---
id: "5.20.39"
title: "ICMPv6 Error Message Rate Monitoring and Anomaly Detection"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.20.39 · ICMPv6 Error Message Rate Monitoring and Anomaly Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*The network sends little error notes whenever something goes wrong — 'address not found', 'letter too big', 'went around in circles too many times', or 'I can't read this address.' We count these error notes and watch for sudden increases. A big spike in 'went around in circles' notes means the mail is going round and round between two post offices and never arriving.*

---

## Description

Tracks ICMPv6 error message rates (Types 1-4) and detects anomalies that indicate network infrastructure problems. ICMPv6 error messages are the IPv6 network's built-in health reporting system — they signal routing failures, MTU constraints, forwarding loops, and packet corruption. In a healthy network, error message rates are low and predictable. Sudden changes in these rates are among the earliest indicators of routing events, firewall policy changes, or software bugs.

## Value

ICMPv6 error messages are generated at the point of failure — the exact router where the problem occurs. They are the most direct and immediate signal of infrastructure issues, often appearing minutes before users report application failures. A spike in Destination Unreachable messages after a route withdrawal is the clearest possible indicator of a routing problem. A spike in Time Exceeded messages is a routing loop. A spike in Parameter Problem is a software bug. Monitoring these rates transforms ICMPv6 from a diagnostic tool into a proactive alerting signal.

## Implementation

Collect ICMPv6 error messages from NetFlow/IPFIX (for volumetric analysis) and syslog (for detailed per-event context). Baseline normal rates per type per router. Apply anomaly detection to identify deviations. Alert on sustained anomalies.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX with ICMPv6 type and code exported from all transit routers.
- Syslog with ICMPv6-related messages (rate-limited to prevent syslog storms).
- At least 7 days of baseline data for anomaly detection to establish normal patterns.

### Step 1 — Configure data collection

**Cisco IOS-XE — SNMP counters for ICMPv6 (RFC 4293):**
```
snmp-server enable traps ipv6
```

**ICMPv6 statistics available via CLI:**
```
show ipv6 traffic
  ICMP statistics:
    Rcvd: 0 format errors, 0 checksum errors
    Sent: 45 destination unreachable, 12 packet too big, 3 time exceeded, 0 parameter problem
```

Poll `ipv6IfIcmpOutDestUnreachs`, `ipv6IfIcmpOutPktTooBigs`, `ipv6IfIcmpOutTimeExcds`, `ipv6IfIcmpOutParmProblems` via SC4SNMP or Telegraf SNMP plugin for continuous metrics.

**NetFlow-based collection (preferred for scale):**
Use the flow record from UC-5.20.38 with ICMPv6 type/code fields.

**Verification:**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") ("dest-unreach" OR "packet-too-big" OR "time-exceeded" OR "parameter-problem" OR icmpv6_type=*) earliest=-24h
| stats count by host
```

### Step 2 — Create the search and alert

**Baseline and anomaly detection:**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-7d
| eval icmpv6_type=case(
    match(_raw, "(?i)dest.?unreach|icmpv6.?type.?=?\s*1\b"), "Type1",
    match(_raw, "(?i)pkt.?too.?big|packet.?too.?big|icmpv6.?type.?=?\s*2\b"), "Type2",
    match(_raw, "(?i)time.?exceed|icmpv6.?type.?=?\s*3\b"), "Type3",
    match(_raw, "(?i)param.?prob|icmpv6.?type.?=?\s*4\b"), "Type4",
    1=1, null())
| where isnotnull(icmpv6_type)
| timechart span=1h count by icmpv6_type
| predict Type1 as predicted_t1 algorithm=LLP5 future_timespan=0
| predict Type3 as predicted_t3 algorithm=LLP5 future_timespan=0
| eval t1_anomaly=if(Type1 > predicted_t1 * 3 AND Type1 > 50, 1, 0)
| eval t3_anomaly=if(Type3 > predicted_t3 * 3 AND Type3 > 20, 1, 0)
```

**Alert — routing loop detection (Type 3 spike):**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-1h
| eval is_time_exceeded=if(match(_raw, "(?i)time.?exceed|hop.?limit|icmpv6.?type.?=?\s*3\b"), 1, 0)
| where is_time_exceeded=1
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| stats count as time_exceeded by host, dst_ipv6
| where time_exceeded > 100
| eval alert="Possible routing loop — " . time_exceeded . " Time Exceeded messages for destination " . dst_ipv6
```
Trigger: more than 100 Time Exceeded messages per hour for a single destination indicates a routing loop. Packets are circling between routers until their hop limit expires.

**Alert — firewall policy change (Type 1 code 1 spike):**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-1h
| eval is_admin_prohibited=if(match(_raw, "(?i)admin.?prohib|communication.?prohibited|icmpv6.?code.?=?\s*1\b"), 1, 0)
| where is_admin_prohibited=1
| stats count as admin_denied by host
| where admin_denied > 200
| eval alert="Possible firewall policy change — " . admin_denied . " administratively prohibited messages from " . host
```

### Step 3 — Validate
(a) **Traceroute validation.** Run `traceroute6` to a distant destination. Count the hops. Verify that many Type 3 messages appear in Splunk (one per hop). This is normal.

(b) **Route withdrawal test (lab).** Withdraw a route in a lab environment. Verify Type 1 messages appear for the withdrawn prefix.

(c) **Routing loop test (lab).** Create a static routing loop between two routers. Verify a burst of Type 3 messages appears. Confirm the alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — ICMPv6 Error Rate Analysis"):
- Row 1 — Single-value: total ICMPv6 errors per hour, anomaly count.
- Row 2 — Timechart: stacked area chart of Types 1-4 over 24 hours.
- Row 3 — Anomaly timeline: periods where actual rate exceeded 3x predicted.
- Row 4 — Top error generators: routers producing the most error messages.
- Row 5 — Correlation: overlay ICMPv6 error spikes with BGP/OSPF events (from UC-5.1.4/5.1.5).

**Scheduling:** Anomaly detection hourly. Routing loop alert continuous. Dashboard refresh every 15 minutes.

**Runbook:**
1. Type 1 spike: check BGP/OSPF for route withdrawals. Check firewall for policy changes.
2. Type 3 spike: check for routing loops using `traceroute6` and `show ipv6 route`.
3. Type 4 spike: check for software bugs or misconfigured extension headers. Capture a sample packet.

### Step 5 — Troubleshooting

- **ICMPv6 rate limiting on routers** — Routers rate-limit ICMPv6 generation (default: 100 messages per second on Cisco). During a routing convergence event, the actual error rate may be higher than what appears in syslog. NetFlow provides more accurate volumetric data because it counts at the flow level, not the message level.

- **SNMP polling interval** — RFC 4293 ICMPv6 counters are cumulative. Poll at consistent intervals (e.g., 60 seconds) and compute delta rates in Splunk. A 5-minute polling interval may miss short spikes.

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-24h
| eval icmpv6_type=case(
    match(_raw, "(?i)destination.?unreachable|icmpv6.?type.?=?\s*1\b|dest.?unreach"), "Type 1 — Dest Unreachable",
    match(_raw, "(?i)packet.?too.?big|icmpv6.?type.?=?\s*2\b"), "Type 2 — Packet Too Big",
    match(_raw, "(?i)time.?exceeded|hop.?limit|icmpv6.?type.?=?\s*3\b"), "Type 3 — Time Exceeded",
    match(_raw, "(?i)parameter.?problem|icmpv6.?type.?=?\s*4\b"), "Type 4 — Parameter Problem",
    1=1, null())
| where isnotnull(icmpv6_type)
| timechart span=1h count by icmpv6_type
| predict "Type 1 — Dest Unreachable" as predicted_type1 algorithm=LLP5 future_timespan=0
| eval type1_anomaly=if("Type 1 — Dest Unreachable" > predicted_type1 * 3, "ANOMALY", "normal")
```

## Visualization

(1) Timechart: ICMPv6 error types 1-4 stacked over 24 hours. (2) Baseline comparison: actual vs predicted rate with anomaly highlighting. (3) Top talkers: routers generating the most error messages. (4) Correlation: overlay ICMPv6 error spikes with BGP/OSPF routing events.

## Known False Positives

**Port scanning.** Legitimate network scanning (vulnerability assessments, asset discovery) generates Destination Unreachable code 4 (port unreachable) messages for every closed port probed. Schedule scanning windows and exclude them from anomaly detection.

**Traceroute.** `traceroute6` intentionally generates Time Exceeded (Type 3 code 0) messages at every hop. A user running traceroute produces one Type 3 per router on the path. This is normal and expected.

**BGP convergence.** During planned routing changes (maintenance windows), Destination Unreachable rates may spike temporarily as routes are withdrawn and re-advertised. This is expected during change windows.

## References

- [RFC 4443 — Internet Control Message Protocol (ICMPv6) for the Internet Protocol Version 6 (IPv6) Specification](https://www.rfc-editor.org/rfc/rfc4443)
- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks](https://www.rfc-editor.org/rfc/rfc9099)
