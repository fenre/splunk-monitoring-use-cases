<!-- AUTO-GENERATED from UC-5.20.22.json — DO NOT EDIT -->

---
id: "5.20.22"
title: "Router Advertisement Rate Limiting Compliance"
status: "verified"
criticality: "medium"
splunkPillar: "ITSI"
---

# UC-5.20.22 · Router Advertisement Rate Limiting Compliance

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*On a WiFi network, routers regularly announce themselves like someone yelling 'I'm the exit — follow me!' If they yell too often, it keeps waking up everyone's phones and drains their batteries. We check that routers announce themselves at a reasonable frequency so phones can sleep between announcements and save battery.*

---

## Description

Verifies that Router Advertisement rates on each VLAN comply with RFC 7772 (BCP 202) energy-efficiency guidelines and RFC 4861 defaults. On wireless networks, excessive RAs force mobile devices to wake their radio to process each RA, draining battery and consuming airtime. RFC 7772 recommends no more than 7 RAs per hour (approximately 1 every 8.5 minutes). On wired networks, the concern is less about battery but more about NDP processing overhead — extremely high RA rates (>1/second) can overwhelm host IPv6 stacks, especially embedded devices and IoT endpoints. This use case measures the observed RA rate on each VLAN and flags VLANs where the rate exceeds RFC 7772 or platform-configured limits.

## Value

Battery life on wireless devices is directly impacted by RA frequency. Each RA forces a WiFi client to wake its radio, process the RA, and potentially perform SLAAC address generation. At default RA intervals (200 seconds = 18 RAs/hour), this accounts for ~5% of mobile battery consumption. With multiple routers on the same VLAN (VRRP/HSRP), the rate doubles. RFC 7772 calculated that 7 RAs/hour keeps the impact under 2% of battery budget. On WLANs with 50+ SSIDs mapped to 50+ VLANs on the same AP, each client may process RAs from multiple VLANs via multicast leakage, further compounding the problem. Monitoring RA rate ensures compliance with energy-efficiency best practices and prevents user complaints about mobile battery drain.

## Implementation

Monitor observed RA rates on each VLAN using Zeek ICMPv6 Type 134 event counting. Compare against RFC 7772 thresholds (7 RAs/hour per router). Verify Cisco RA Throttler or equivalent is configured on wireless LAN controllers. Alert on VLANs exceeding the threshold.

## Detailed Implementation

### Prerequisites
- Zeek or Suricata deployed on network TAP/SPAN for ICMPv6 Type 134 rate measurement.
- Knowledge of intended RA intervals per VLAN (typically 200 seconds for wired, potentially lower for specific use cases).
- For wireless compliance, knowledge of Cisco RA Throttler configuration on WLC/C9800.

### Step 1 — Configure data collection

**Zeek ICMPv6 monitoring (primary):**
Deploy Zeek on SPAN/TAP covering VLAN trunk ports. Zeek logs every ICMPv6 Type 134 with source MAC, source IP, and decoded RA content. Forward to Splunk with `sourcetype=corelight_zeek`.

**Cisco WLC/C9800 RA Throttler configuration:**
```
! Catalyst 9800 RA Throttler configuration
wireless profile policy WIFI_POLICY
 ipv6 ra-guard
 ipv6 nd-throttle
 ipv6 nd-throttle max-through 10
 ipv6 nd-throttle max-interval 600
```
This limits RAs to 10 per VLAN per 10-minute window. Suppressed RAs generate syslog events.

**Cisco IOS router RA interval tuning:**
```
interface Vlan100
 ipv6 nd ra-interval 600
 ipv6 nd ra-lifetime 1800
```
The `ra-interval 600` sets MaxRtrAdvInterval to 600 seconds. The actual interval is randomised between 0.33× and 1× this value (200-600 seconds). For wireless VLANs, increase to 600-1800 seconds per RFC 7772.

**Verification:**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-1h
| stats count by src_ip
```
Expected: one row per router with a count consistent with the configured RA interval (e.g., ~3 RAs per hour for a 600-second interval).

### Step 2 — Create the search and alert

**Primary search — hourly RA rate per router per VLAN:**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-1h
| stats count as ra_count by src_ip, src_mac, vlan
| eval rfc7772_limit=7
| eval compliant=if(ra_count <= rfc7772_limit, "COMPLIANT", "NON-COMPLIANT")
| eval excess=if(ra_count > rfc7772_limit, ra_count - rfc7772_limit, 0)
| sort -ra_count
| table vlan, src_ip, src_mac, ra_count, rfc7772_limit, compliant, excess
```

**Alert — RA rate exceeds RFC 7772 on wireless VLAN:**
```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-1h
| stats count as ra_count by src_ip, vlan
| lookup wireless_vlans.csv vlan OUTPUT is_wireless
| where is_wireless="true" AND ra_count > 7
```
Trigger: any result. Priority: medium. Action: email wireless operations team.

The `wireless_vlans.csv` lookup identifies which VLANs serve WiFi clients. RA rate limits are most important on wireless VLANs where battery impact is significant.

**RA Throttler effectiveness check:**
```spl
index=network sourcetype="cisco:ios" "nd-throttle" earliest=-24h
| rex field=_raw "(?<action>Throttled|Allowed)\s+RA.*VLAN\s*(?<vlan>\d+)"
| stats count as total count(eval(action="Throttled")) as throttled count(eval(action="Allowed")) as allowed by vlan
| eval throttle_pct=round(throttled / total * 100, 1)
| sort -throttle_pct
```
If throttle_pct is high (>50%), routers are sending excessive RAs and the throttler is working hard. Consider increasing the RA interval on the routers to reduce the load.

### Step 3 — Validate
(a) **RA interval calculation.** On a router, check: `show ipv6 interface Vlan100 | include RA`. Note the interval. In Splunk, count RAs from that router over 1 hour — it should be approximately 3600/interval (e.g., 3600/600 = 6 RAs/hour for a 600-second interval). Account for randomisation (0.33x-1x).

(b) **RFC 7772 compliance.** For wireless VLANs, verify that no router sends more than 7 RAs per hour. For wired VLANs, the threshold is less critical but >18 RAs/hour (200-second interval) is the maximum recommended by RFC 4861 defaults.

(c) **Multi-router VLAN.** On a VLAN with 2 VRRP routers, the combined rate should not exceed 14 RAs/hour (7 per router).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RA Rate Compliance"):
- Row 1 — Single-value: percentage of wireless VLANs compliant with RFC 7772, total excess RAs in 24h.
- Row 2 — Table: per-VLAN RA rate with compliance status, sorted by excess.
- Row 3 — Timechart: hourly RA rate by VLAN over 7 days — identify trending issues.
- Row 4 — RA Throttler: throttled vs allowed ratio per VLAN.

**Scheduling:** Hourly RA rate check. Daily compliance report. Real-time alert for extreme rates (>50 RAs/hour from any source).

**Runbook:**
1. Wireless VLAN exceeding RFC 7772: increase RA interval on the advertising router to 600-1800 seconds. Verify RA Throttler is configured on the WLC.
2. Wired VLAN with extremely high rate (>50/hour): check if the router is misconfigured with a very low RA interval, or if Router Solicitations from scanning/monitoring tools are triggering excessive RA responses.

### Step 5 — Troubleshooting

- **RA rate appears zero** — No ICMPv6 Type 134 events in Zeek. Verify the SPAN/TAP port is mirroring the correct VLANs. Verify Zeek is processing ICMPv6 packets. On some platforms, SPAN may not mirror multicast (ff02::1) traffic — check the SPAN configuration for `replicate multicast` or equivalent.

- **RA rate varies wildly between hours** — This is often caused by Router Solicitation bursts. When many clients wake up (e.g., morning office arrival), they send RS messages that trigger immediate RA responses. Use hourly or 10-minute windows for compliance assessment, not per-minute.

- **RA Throttler syslog not appearing** — Cisco C9800 RA Throttler logging requires `logging level ndproxy notice` or higher. Verify: `show logging | include ndproxy`.

## SPL

```spl
index=network sourcetype="corelight_zeek" icmpv6_type=134 earliest=-1h
| bin _time span=10m
| stats count as ra_count dc(src_ip) as unique_routers by _time, vlan
| eval ra_per_router=round(ra_count / unique_routers, 1)
| eval compliant=if(ra_per_router <= 2, "YES — within RFC 7772 limit", "NO — exceeds 7/hour rate")
| table _time, vlan, ra_count, unique_routers, ra_per_router, compliant
```

## Visualization

(1) Table: per-VLAN RA rate with compliance status. (2) Timechart: RA rate per VLAN over 24 hours — identify VLANs with consistently high rates. (3) Single-value: percentage of VLANs compliant with RFC 7772. (4) Bar chart: top 10 VLANs by RA rate.

## Known False Positives

**Router Solicitation bursts.** When many clients join a VLAN simultaneously (e.g., conference room WiFi during a meeting start), they send Router Solicitations (RS, ICMPv6 Type 133) which trigger immediate RA responses. The router responds within 0.5 seconds per RS (with jitter). This burst is temporary and resolves within seconds. The compliance check should use a 10-minute or 1-hour window, not a per-second rate.

**Multiple routers with different intervals.** If Router A is configured with RA interval 200 seconds and Router B with 30 seconds, the VLAN-level RA rate reflects both routers combined. The per-router rate should be assessed individually.

**RA Throttler suppression events.** When Cisco RA Throttler is active and suppressing excess RAs, the observed RA rate in Zeek may be lower than the configured rate on the router — because the throttler is doing its job. This is correct behaviour, not a false positive.

## References

- [RFC 7772 — Reducing Energy Consumption of Router Advertisements (BCP 202 — RA rate limiting guidelines for wireless)](https://www.rfc-editor.org/rfc/rfc7772)
- [RFC 4861 — Neighbor Discovery for IP version 6 (§6.2.1 — Router Advertisement Interval, MaxRtrAdvInterval default 600s)](https://www.rfc-editor.org/rfc/rfc4861)
- [Cisco Catalyst 9800 RA Throttler Configuration Guide](https://www.cisco.com/c/en/us/td/docs/wireless/controller/9800/config-guide/b_wl_16_12_cg.html)
