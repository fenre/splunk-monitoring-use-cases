<!-- AUTO-GENERATED from UC-5.20.96.json — DO NOT EDIT -->

---
id: "5.20.96"
title: "SD-WAN IPv6 Overlay and Underlay Health Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.96 · SD-WAN IPv6 Overlay and Underlay Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Our company uses a smart postal network (SD-WAN) that automatically chooses the best route for letters between offices. We need to make sure this smart network works for new-format addresses (IPv6) just as well as for old-format addresses (IPv4). We check every office to make sure they can send and receive new-format letters through the smart network.*

---

## Description

Monitors SD-WAN (Cisco Catalyst SD-WAN/Viptela) fabric health for IPv6-specific components: OMP IPv6 route distribution, IPv6 transport tunnel SLA compliance, VRF-aware IPv6 routing, and dual-stack direct internet access configuration. SD-WAN simplifies branch connectivity but introduces IPv6-specific failure modes when OMP IPv6 address family is not enabled, when SLA policies don't cover IPv6, or when IPv6 DIA is missing.

## Value

SD-WAN is the primary WAN technology for modern enterprises. If IPv6 is not properly configured in the SD-WAN overlay, branch sites lose IPv6 connectivity even when the underlay supports it. This creates user-impacting failures for dual-stack services that the SD-WAN management platform may not highlight. Dedicated IPv6 SD-WAN monitoring ensures parity between IPv4 and IPv6 across the entire SD-WAN fabric.

## Implementation

Monitor OMP route tables for IPv6 address family routes. Track IPv6 transport tunnel SLA metrics. Verify IPv6 DIA configuration. Alert on IPv6 reachability failures across the SD-WAN fabric.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst SD-WAN (vManage, vSmart, vEdge/cEdge) deployment.
- Cisco Catalyst Add-on or Cisco SD-WAN Add-on installed in Splunk.
- vManage API access for real-time status polling.

### Step 1 — Configure data collection

**SD-WAN IPv6 overlay configuration (cEdge):**
```
sdwan
 omp
  address-family ipv6
   advertise connected
   advertise static
  !
!
vpn 1
 ip route 0.0.0.0/0 vpn 0
 ipv6 route ::/0 vpn 0
 interface GigabitEthernet0/0/0
  ipv6 address 2001:db8:branch::1/64
  ipv6 dhcp server BRANCH-DHCPV6
  no shutdown
```

**vManage API polling for OMP IPv6 routes:**
```
GET /dataservice/device/omp/routes/ipv6?deviceId=<device-id>
```
Configure as a scripted input in Splunk.

**Verification:**
```spl
index=network sourcetype="cisco:sdwan" "ipv6" | stats count by host
```

### Step 2 — Create monitoring searches

**OMP IPv6 route coverage by site:**
```spl
index=network sourcetype="cisco:sdwan" "omp" "ipv6" earliest=-1h
| rex field=_raw "site.?id\s*=?\s*(?<site_id>\d+)"
| rex field=_raw "prefix\s*=?\s*(?<ipv6_prefix>[0-9a-fA-F:/]+)"
| stats dc(ipv6_prefix) as ipv6_routes by site_id
| lookup sdwan_site_inventory.csv site_id OUTPUT site_name, expected_ipv6_routes
| eval status=case(
    ipv6_routes >= expected_ipv6_routes, "OK",
    ipv6_routes > 0, "PARTIAL — " . ipv6_routes . " of " . expected_ipv6_routes . " IPv6 routes",
    ipv6_routes=0, "CRITICAL — NO IPv6 OMP routes at site")
| table site_id, site_name, ipv6_routes, expected_ipv6_routes, status
```

**IPv6 transport tunnel SLA:**
```spl
index=network sourcetype="cisco:sdwan" "bfd" earliest=-1h
| eval is_ipv6_transport=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| where is_ipv6_transport=1
| rex field=_raw "latency\s*=?\s*(?<latency_ms>\d+)"
| rex field=_raw "loss\s*=?\s*(?<loss_pct>[0-9.]+)"
| rex field=_raw "jitter\s*=?\s*(?<jitter_ms>\d+)"
| stats avg(latency_ms) as avg_latency avg(loss_pct) as avg_loss avg(jitter_ms) as avg_jitter by host
| eval sla_status=case(
    avg_loss > 1, "SLA VIOLATION — loss " . round(avg_loss, 2) . "%",
    avg_latency > 150, "SLA VIOLATION — latency " . round(avg_latency, 0) . "ms",
    avg_jitter > 30, "SLA WARNING — jitter " . round(avg_jitter, 0) . "ms",
    1=1, "OK")
```

### Step 3 — Validate
(a) **OMP verification.** SSH to a cEdge. Run `show sdwan omp routes ipv6`. Verify IPv6 routes are received and installed.

(b) **End-to-end IPv6 test.** From a branch host, `ping6 2001:db8:dc::1` (data center server). Verify traffic traverses the SD-WAN overlay.

(c) **DIA test.** From a branch host, access an IPv6-only website. Verify the traffic exits via the local internet transport (DIA) rather than backhauling through the data center.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — SD-WAN Health"):
- Row 1 — Map: SD-WAN sites with IPv6 connectivity status (green/amber/red).
- Row 2 — Table: OMP IPv6 route count by site.
- Row 3 — SLA metrics: IPv6 transport tunnel performance.
- Row 4 — Configuration audit: sites missing IPv6 DIA.

**Alert:** Site with zero IPv6 OMP routes — critical. IPv6 traffic at that site has no overlay path.

**Runbook:**
1. No OMP IPv6 routes: Verify `address-family ipv6` is configured under OMP. Check vSmart policy for IPv6 route filters.
2. IPv6 SLA violation: Check transport quality. If ISP IPv6 path is degraded, configure SLA policy to prefer alternate transport.
3. Missing IPv6 DIA: Configure IPv6 NAT DIA on the WAN edge router. Alternatively, configure IPv6 default route pointing to the internet transport.

### Step 5 — Troubleshooting

- **OMP IPv6 not advertised.** The most common issue is missing `address-family ipv6` under the OMP configuration. This must be configured on EVERY cEdge/vEdge.

- **vSmart policy blocking IPv6.** vSmart control policies may inadvertently filter IPv6 routes if the policy doesn't include IPv6 address family match conditions. Verify with `show sdwan policy from-vsmart`.

- **IPv6 DIA with service-insertion.** When traffic is steered through a service chain (firewall, proxy), the service device must support IPv6. If the service device is IPv4-only, IPv6 DIA traffic is blackholed.

## SPL

```spl
index=network (sourcetype="cisco:sdwan" OR sourcetype="cisco:vmanage") earliest=-24h
| eval event_type=case(
    match(_raw, "(?i)OMP.*route.*ipv6|omp.*afi.*2"), "OMP_IPv6_ROUTE",
    match(_raw, "(?i)tunnel.*down|bfd.*down"), "TUNNEL_DOWN",
    match(_raw, "(?i)sla.*violation|threshold.*exceeded"), "SLA_VIOLATION",
    match(_raw, "(?i)ipv6.*not.*reachable|ipv6.*unreachable"), "IPv6_UNREACHABLE",
    1=1, "OTHER")
| eval is_ipv6_related=if(match(_raw, "(?i)ipv6|2[0-9a-fA-F]{3}:|afi.?2"), 1, 0)
| where is_ipv6_related=1
| stats count as events by host, event_type
| eval severity=case(
    event_type="IPv6_UNREACHABLE", "CRITICAL — IPv6 reachability lost",
    event_type="TUNNEL_DOWN" AND events > 1, "HIGH — IPv6 transport tunnel failures",
    event_type="SLA_VIOLATION", "WARNING — IPv6 SLA threshold exceeded",
    1=1, "INFO")
| sort -events
```

## Visualization

(1) Fabric map: SD-WAN sites with IPv6 connectivity status. (2) Table: OMP IPv6 routes by site/VRF. (3) SLA dashboard: IPv6 tunnel performance metrics. (4) Single-value: sites without IPv6 DIA.

## Known False Positives

**IPv4-only SD-WAN sites.** Some branch sites may intentionally run IPv4-only. Missing IPv6 OMP routes at these sites is expected. Maintain an inventory of dual-stack vs IPv4-only sites.

**Transport failover.** When an SD-WAN device fails over between transports (MPLS → Internet), brief tunnel down events are expected. Alert on prolonged outages (>5 minutes), not brief failovers.

**SLA threshold tuning.** Default SLA thresholds may be too aggressive for certain transports. Tune per-transport-type thresholds before alerting.

## References

- [Cisco SD-WAN IPv6 Configuration Guide](https://www.cisco.com/c/en/us/)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.7 — transition and overlay security)](https://www.rfc-editor.org/rfc/rfc9099)
