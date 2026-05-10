<!-- AUTO-GENERATED from UC-5.20.104.json — DO NOT EDIT -->

---
id: "5.20.104"
title: "IPv6 Remotely Triggered Black Hole (RTBH) Activation and Effectiveness Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.104 · IPv6 Remotely Triggered Black Hole (RTBH) Activation and Effectiveness Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*When someone is flooding our mailbox with millions of junk letters (a DDoS attack), we tell all the post offices in the area to throw away any letters addressed to our mailbox. This stops the flood, but it also means we can't receive any real letters until we tell the post offices to start delivering again.*

---

## Description

Monitors IPv6 Remotely Triggered Black Hole (RTBH) routing activations for DDoS mitigation. Tracks when RTBH routes are installed (blackhole activation) and withdrawn (deactivation), the scope of blackholed prefixes, BGP community signals, and potential collateral damage from over-broad blackhole announcements. Critical for DDoS response operations where IPv6 attack traffic must be dropped at the network edge.

## Value

DDoS attacks increasingly target IPv6 infrastructure. RTBH is the fastest response mechanism (seconds vs minutes for ACLs), but it must be carefully monitored. An over-broad blackhole announcement can take an entire /48 offline, causing more damage than the DDoS itself. Monitoring RTBH activations, duration, scope, and effectiveness ensures the cure isn't worse than the disease.

## Implementation

Monitor BGP announcements for RTBH communities. Track null-route installations. Alert on blackhole activations with scope analysis. Measure effectiveness by comparing traffic volumes before and after activation.

## Detailed Implementation

### Prerequisites
- BGP peering with RTBH trigger capability.
- BGP logging enabled on border routers.
- Defined RTBH BGP community (e.g., 65535:666 per RFC 7999, or ISP-specific).

### Step 1 — Configure RTBH infrastructure

**Cisco IOS-XE RTBH trigger router configuration:**
```
! Define null route for RTBH
ip route 192.0.2.1 255.255.255.255 Null0
ipv6 route 100::1/128 Null0

! Create RTBH trigger prefix
route-map RTBH permit 10
 set community 65535:666
 set ipv6 next-hop 100::1

! Trigger example: blackhole 2001:db8:victim::1/128
router bgp 65000
 address-family ipv6 unicast
  network 2001:db8:victim::1/128 route-map RTBH
```

**Receiving router configuration:**
```
route-map RTBH-RECEIVE permit 10
 match community RTBH-COMMUNITY
 set ipv6 next-hop 100::1

ipv6 route 100::1/128 Null0

router bgp 65001
 address-family ipv6 unicast
  neighbor 2001:db8::1 route-map RTBH-RECEIVE in
```

### Step 2 — Create monitoring searches

**RTBH activation tracking:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-7d
  ("blackhole" OR "null0" OR "discard" OR "community.*666")
| eval is_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| where is_ipv6=1
| rex field=_raw "(?<prefix>[0-9a-fA-F:]+/\d+)"
| eval action=if(match(_raw, "(?i)withdraw|removed"), "DEACTIVATED", "ACTIVATED")
| table _time, host, prefix, action
| sort _time
```

**RTBH effectiveness — traffic drop verification:**
```spl
index=network sourcetype="netflow" earliest=-4h
| eval is_ipv6=if(match(dest, ":"), 1, 0)
| where is_ipv6=1
| lookup active_rtbh.csv dest_prefix OUTPUT rtbh_active, rtbh_start_time
| eval period=if(_time > strptime(rtbh_start_time, "%Y-%m-%dT%H:%M:%S"), "after_rtbh", "before_rtbh")
| stats sum(bytes) as total_bytes by dest, period
| eval effectiveness=if(period="after_rtbh", "Should be near zero if RTBH is working", "Pre-RTBH baseline")
```

### Step 3 — Validate
(a) **RTBH test.** In a lab environment, activate RTBH for a test prefix. Verify:
- The null route appears on all receiving routers.
- Traffic to the test prefix is dropped.
- The Splunk alert fires within 60 seconds.
- Deactivation restores connectivity.

(b) **Scope verification.** Announce a /128 RTBH route. Verify that only the specific host is blackholed, not the entire /64 or /48.

(c) **Duration tracking.** Activate and deactivate RTBH. Verify the dashboard correctly shows the activation duration.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RTBH Operations"):
- Row 1 — Single-values: currently active RTBH routes, total activations (24h).
- Row 2 — Timeline: RTBH activation/deactivation events.
- Row 3 — Table: currently active blackhole prefixes with scope and duration.
- Row 4 — Traffic chart: before/after traffic volume for blackholed prefixes.

**Alert 1:** RTBH activation — informational. All activations should be logged and reviewed.
**Alert 2:** RTBH active for >4 hours — warning. Long-duration blackholes may indicate forgotten activations.
**Alert 3:** RTBH prefix broader than /64 — critical. Investigate for collateral damage.

**Runbook:**
1. DDoS detected → Activate RTBH for the victim /128.
2. If attack targets a range → Escalate to /64 RTBH maximum.
3. After attack subsides → Deactivate RTBH. Verify service restoration.
4. Post-incident → Review attack patterns. Consider Flowspec for more granular filtering next time.

### Step 5 — Troubleshooting

- **RTBH not propagating.** Verify the RTBH BGP community is accepted by upstream peers. Some ISPs use proprietary RTBH communities rather than RFC 7999's 65535:666.

- **Collateral damage.** If legitimate traffic is being dropped, narrow the RTBH prefix scope. Prefer /128 (single host) over broader prefixes. If the attack targets multiple hosts, use multiple /128 RTBH routes rather than one broad prefix.

- **Forgotten RTBH routes.** RTBH routes should have a defined TTL. Implement automated deactivation after a configurable period (e.g., 4 hours). Monitor for stale RTBH routes.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos") earliest=-24h
  ("%BGP-5" OR "blackhole" OR "null0" OR "discard" OR "rtbh" OR "community.*666")
| eval is_ipv6_rtbh=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}.*(?i)(null|discard|blackhole|666)"), 1, 0)
| where is_ipv6_rtbh=1
| rex field=_raw "(?<blackholed_prefix>[0-9a-fA-F:]+/\d+)"
| rex field=_raw "community\s+(?<bgp_community>[\d:]+)"
| eval action=case(
    match(_raw, "(?i)withdraw|removed|deactivat"), "RTBH_DEACTIVATED",
    match(_raw, "(?i)announce|added|activat|install"), "RTBH_ACTIVATED",
    1=1, "RTBH_EVENT")
| eval prefix_scope=case(
    match(blackholed_prefix, "/128$"), "Single host — precise targeting",
    match(blackholed_prefix, "/6[0-4]$"), "Subnet — moderate scope",
    match(blackholed_prefix, "/4[89]$|/5[0-9]$"), "Large prefix — check for collateral damage",
    match(blackholed_prefix, "/4[0-8]$"), "VERY LARGE — significant collateral risk",
    1=1, "Unknown scope")
| stats count as events latest(_time) as latest by host, blackholed_prefix, action, prefix_scope, bgp_community
| sort -latest
```

## Visualization

(1) Timeline: RTBH activations/deactivations with prefix scope. (2) Table: currently active blackhole routes. (3) Single-value: active RTBH count. (4) Traffic chart: inbound traffic volume before/after blackhole.

## Known False Positives

**Planned maintenance.** During planned maintenance windows, RTBH may be used to redirect traffic. Correlate with change management records.

**Automated testing.** Some organisations periodically test RTBH activation. These brief test activations should be documented and excluded from alert logic.

**Provider-side RTBH.** When an upstream ISP activates RTBH based on a customer request, the announcement may appear in BGP logs before the customer's own routers process it. This is expected behaviour.

## References

- [RFC 5635 — Remote Triggered Black Hole Filtering with Unicast Reverse Path Forwarding (uRPF)](https://www.rfc-editor.org/rfc/rfc5635)
- [RFC 7999 — BLACKHOLE Community](https://www.rfc-editor.org/rfc/rfc7999)
- [RFC 8955 — Dissemination of Flow Specification Rules (Flowspec)](https://www.rfc-editor.org/rfc/rfc8955)
