<!-- AUTO-GENERATED from UC-5.20.86.json — DO NOT EDIT -->

---
id: "5.20.86"
title: "RA Rate Limiting on Wireless Networks (RFC 7772 / BCP 202)"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.86 · RA Rate Limiting on Wireless Networks (RFC 7772 / BCP 202)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*When you use wireless internet on your phone, the router keeps sending announcement messages (RAs) that force your phone to wake up and listen. If these announcements come too often — like someone ringing your doorbell every 4 seconds — your phone battery drains fast. The standards say the router should only ring the doorbell about 7 times per hour.*

---

## Description

Monitors Router Advertisement rates on wireless networks against RFC 7772 (BCP 202) recommendations and Cisco RA Throttler enforcement. Excessive RA rates on WiFi networks drain mobile device batteries, waste airtime, and can indicate rogue RA sources or misconfigured routers. BCP 202 recommends a maximum of 7 RAs per hour per VLAN to keep mobile power consumption below 2% of battery capacity.

## Value

In large enterprise WiFi deployments, IPv6 RA storms are a common cause of mysterious battery drain and poor WiFi performance. A single misconfigured router advertising RAs every 4 seconds on a wireless VLAN will cause every connected device to wake its radio 900 times per hour. This use case ensures RA rates are within BCP 202 limits, RA Throttler is functioning, and rogue RA sources are identified before they impact the user experience.

## Implementation

Monitor RA Throttler events on WLCs and Catalyst 9800 controllers. Track per-VLAN RA rates. Alert when rates exceed BCP 202 limits. Identify RA sources for remediation.

## Detailed Implementation

### Prerequisites
- Cisco WLC or Catalyst 9800 wireless controller with RA Throttler capability.
- Syslog forwarding from wireless controllers to Splunk.
- IPv6 enabled on wireless VLANs.

### Step 1 — Configure data collection

**Enable RA Throttler on Cisco Catalyst 9800:**
```
wlan MY_SSID 1 MY_SSID
 ipv6 nd ra-throttler
 ipv6 nd ra-throttler attach-policy RA_LIMIT
!
ipv6 nd ra-throttler policy RA_LIMIT
 throttle-period 600
 max-through 10
```
This limits RA forwarding to 10 RAs per 600 seconds (10 minutes) per VLAN per SSID.

**Configure RA interval on routers (BCP 202 compliant):**
```
interface Vlan100
 ipv6 nd ra interval 600
 ipv6 nd ra lifetime 1800
```
This sets RA interval to 600 seconds (10 minutes), producing ~6 RAs/hour — within BCP 202 limits.

**Verification:**
```spl
index=network (sourcetype="cisco:wlc" OR sourcetype="cisco:iosxe") "ra-throttl" | stats count by host
```

### Step 2 — Create monitoring searches

**RA rate per VLAN:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="zeek:conn") earliest=-1h
  ("ICMPv6" AND "134" OR "router-advertisement" OR "RA")
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| rex field=_raw "(?:src|source|from)\s*=?\s*(?<ra_source>[0-9a-fA-F:.]+)"
| bin _time span=1h
| stats count as ra_count dc(ra_source) as unique_sources by _time, vlan
| eval bcp202_status=case(
    ra_count > 20, "EXCEEDS — " . ra_count . " RAs/hour (BCP 202 max: 7)",
    ra_count > 7, "ABOVE LIMIT — " . ra_count . " RAs/hour",
    1=1, "COMPLIANT — " . ra_count . " RAs/hour")
| table _time, vlan, ra_count, unique_sources, bcp202_status
```

**RA Throttler drop analysis:**
```spl
index=network sourcetype="cisco:wlc" "ra-throttl" "drop" earliest=-24h
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| rex field=_raw "(?:src|source)\s*=?\s*(?<ra_source>[0-9a-fA-F:.]+)"
| stats count as dropped_ras by vlan, ra_source
| eval issue="RA source " . ra_source . " is generating excess RAs — " . dropped_ras . " throttled in last 24h"
| sort -dropped_ras
```

### Step 3 — Validate
(a) **BCP 202 compliance check.** On a wireless VLAN, count RAs over 1 hour (using packet capture or Zeek). Verify the count is ≤ 7.

(b) **RA Throttler test.** Configure a test router with RA interval 4 seconds (MaxRtrAdvInterval=4). Connect to a wireless VLAN with RA Throttler. Verify excess RAs are dropped and only ~10 per 10-minute window are forwarded.

(c) **Battery impact measurement.** On iOS, use Settings → Battery to check 24-hour drain. On Android, use `dumpsys batterystats`. Correlate with RA rates.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Wireless RA Health"):
- Row 1 — Single-value: VLANs exceeding BCP 202 (target: 0). RA Throttler active count.
- Row 2 — Table: per-VLAN RA rates with BCP 202 compliance status.
- Row 3 — Timechart: RA rates over 24 hours by VLAN.
- Row 4 — Table: top RA sources generating excess RAs (remediation targets).

**Alert:** RA rate > 20/hour on any wireless VLAN — indicates misconfigured router or rogue RA source.

**Runbook:**
1. High RA rate from legitimate router: Increase `ipv6 nd ra interval` to 600-1800 seconds.
2. High RA rate from unknown source: Investigate source port via switch MAC table. May be rogue device — disable port.
3. RA Throttler dropping legitimate RAs: Acceptable behaviour. Fix the source by increasing RA interval.

### Step 5 — Troubleshooting

- **RA interval randomisation.** RFC 4861 requires a ±20% randomisation on RA interval. MaxRtrAdvInterval=600s means actual intervals range from 480-720s. Account for this in rate calculations.

- **Multiple VLANs per SSID.** Cisco WLC can map multiple VLANs to one SSID (dynamic VLAN assignment). Each VLAN has its own RA sources. The aggregate RA rate on the SSID is the sum of all VLAN RA rates. Configure RA Throttler per SSID.

- **FlexConnect mode.** In FlexConnect (local switching) mode, RA Throttler processing happens at the AP, not the WLC. Verify AP software version supports RA Throttler in FlexConnect.

## SPL

```spl
index=network (sourcetype="cisco:wlc" OR sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("RA" AND ("throttl" OR "drop" OR "rate" OR "suppress") OR "%IPV6_ND-6-RA_THROTTLE")
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| rex field=_raw "(?:rate|count)\s*=?\s*(?<ra_rate>\d+)"
| eval ra_rate=tonumber(ra_rate)
| eval status=case(
    match(_raw, "(?i)throttl|suppress|drop"), "THROTTLED — excess RAs dropped by RA Throttler",
    ra_rate > 20, "WARNING — RA rate exceeds BCP 202 recommendation (" . ra_rate . " RAs/hour vs 7 max)",
    ra_rate > 7, "ELEVATED — RA rate above BCP 202 limit",
    1=1, "OK")
| stats count as events latest(ra_rate) as current_rate by host, vlan, status
| sort -current_rate
```

## Visualization

(1) Single-value: VLANs exceeding BCP 202 RA rate limit. (2) Table: per-VLAN RA rates with throttling status. (3) Timechart: RA rate by VLAN over 24 hours. (4) Alert panel: RA Throttler drop events.

## Known False Positives

**Multiple router sources.** If multiple routers advertise the same prefix on the same VLAN, the aggregate RA rate may exceed BCP 202 limits even though each individual router complies. Tune RA intervals per-router to keep aggregate rate within limits.

**RA Throttler legitimate drops.** RA Throttler silently drops excess RAs as designed. These are not errors — they are the control working correctly. Alert only if the SOURCE rate is excessive, indicating a misconfigured router that should be fixed at the source.

**VRRP/HSRP failover.** Gateway failover events generate a burst of RAs to announce the new active router. Brief RA spikes during failover are expected.

## References

- [RFC 7772 — Reducing Energy Consumption of Router Advertisements (BCP 202)](https://www.rfc-editor.org/rfc/rfc7772)
- [Cisco Catalyst 9800 RA Throttler Configuration Guide](https://www.cisco.com/c/en/us/td/docs/wireless/controller/9800/config-guide/b_wl_9800_cg/ipv6.html)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.5 — wireless RA considerations)](https://www.rfc-editor.org/rfc/rfc9099)
