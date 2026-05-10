<!-- AUTO-GENERATED from UC-5.20.70.json — DO NOT EDIT -->

---
id: "5.20.70"
title: "IPv6 Traffic Class / DSCP Marking Parity Monitoring"
status: "verified"
criticality: "low"
splunkPillar: "IT Operations"
---

# UC-5.20.70 · IPv6 Traffic Class / DSCP Marking Parity Monitoring

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*In our building, important visitors (like doctors and emergency workers) get priority elevator access — they get to skip the queue. But when we added the new IPv6 entrance, we forgot to put up the 'priority visitors' signs. So important visitors entering through the new door have to wait in the regular queue while the same visitors entering through the old door (IPv4) still get priority.*

---

## Description

Compares DSCP marking distributions between IPv4 and IPv6 traffic from IPFIX/NetFlow flow records to detect QoS parity violations. In dual-stack networks, applications should receive equivalent QoS treatment regardless of whether they communicate over IPv4 or IPv6. A DSCP distribution skew between protocol versions indicates that QoS classification policies have not been updated for IPv6.

## Value

QoS policies that mark VoIP (DSCP EF/46), video (DSCP AF41/34), or business-critical applications (DSCP AF31/26) are frequently applied only to IPv4 traffic. As applications transition to dual-stack, their IPv6 traffic receives best-effort treatment while their IPv4 traffic continues to receive priority. This causes intermittent quality issues that are difficult to diagnose — the same application works perfectly over IPv4 but experiences congestion-related degradation over IPv6. Detecting DSCP parity violations enables proactive QoS policy updates.

## Implementation

Export DSCP values from IPFIX/NetFlow for both IPv4 and IPv6 flows. Compare DSCP distributions between protocol versions. Alert on significant parity gaps for specific DSCP values (especially EF, AF41, AF31).

## Detailed Implementation

### Prerequisites
- IPFIX/NetFlow exporters configured to include DSCP/ToS fields for both IPv4 and IPv6.
- QoS policy documentation identifying expected DSCP markings per application class.
- Dual-stack deployment with meaningful IPv6 traffic.

### Step 1 — Configure data collection

**Cisco IOS-XE — Include DSCP in Flexible NetFlow:**
The `ipClassOfService` field captures the full Traffic Class byte (IPv6) or ToS byte (IPv4):
```
flow record IPV6-QOS
 match ipv6 source address
 match ipv6 destination address
 match ipv6 traffic-class
 match transport source-port
 match transport destination-port
 collect counter bytes long
 collect counter packets long
```

**DSCP reference lookup:**
```csv
dscp,dscp_name,traffic_class,priority
0,BE,Best Effort,low
8,CS1,Scavenger,low
10,AF11,Assured Forwarding 11,medium
18,AF21,Assured Forwarding 21,medium
26,AF31,Assured Forwarding 31,high
34,AF41,Assured Forwarding 41,high
46,EF,Expedited Forwarding (Voice),critical
48,CS6,Routing/Control,critical
```
Upload as `dscp_reference.csv`.

**Verification:**
```spl
index=network sourcetype="netflow" earliest=-1h
| eval dscp=round(tonumber(coalesce(ipDiffServCodePoint, ipClassOfService)) / 4, 0)
| stats count by dscp
| lookup dscp_reference.csv dscp
| table dscp, dscp_name, traffic_class, count
```

### Step 2 — Create the search and alert

**Voice (EF) DSCP parity check:**
```spl
index=network sourcetype="netflow" earliest=-4h
| eval ip_ver=if(isnotnull(sourceIPv6Address) OR match(src, ":"), "IPv6", "IPv4")
| eval dscp=round(tonumber(coalesce(ipDiffServCodePoint, ipClassOfService)) / 4, 0)
| eval is_ef=if(dscp=46, 1, 0)
| stats sum(is_ef) as ef_flows count as total by ip_ver
| eval ef_pct=round(ef_flows / total * 100, 2)
| eval issue=if(ip_ver="IPv6" AND ef_pct < 0.1 AND total > 1000, "WARNING — no voice-class (EF) DSCP marking on IPv6 traffic", "OK")
| table ip_ver, ef_flows, total, ef_pct, issue
```
If IPv4 shows 5-10% EF traffic but IPv6 shows near-zero, VoIP QoS policies are missing for IPv6.

**Comprehensive parity analysis:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval ip_ver=if(isnotnull(sourceIPv6Address) OR match(src, ":"), "IPv6", "IPv4")
| eval dscp=round(tonumber(coalesce(ipDiffServCodePoint, ipClassOfService)) / 4, 0)
| lookup dscp_reference.csv dscp OUTPUT dscp_name, priority
| where priority="critical" OR priority="high"
| stats count as flows by ip_ver, dscp, dscp_name
| eventstats sum(flows) as total by ip_ver
| eval pct=round(flows / total * 100, 2)
| chart values(pct) as percentage by dscp_name ip_ver
```

### Step 3 — Validate
(a) **Known QoS policy.** On a router with both IPv4 and IPv6 QoS policies, verify the DSCP distributions match.

(b) **Missing IPv6 policy.** On a router with IPv4-only QoS, verify the parity check identifies the gap.

(c) **Voice traffic.** If VoIP is deployed, verify EF marking appears for both IPv4 and IPv6 voice traffic.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — QoS Parity"):
- Row 1 — Side-by-side bar: DSCP distribution IPv4 vs IPv6.
- Row 2 — Table: DSCP classes with parity gaps.
- Row 3 — Timechart: EF/AF41/AF31 percentages for IPv4 vs IPv6 over 7 days.
- Row 4 — Single-value: number of high-priority DSCP classes with parity gap.

**Scheduling:** Parity analysis daily. Voice DSCP check hourly during business hours.

**Runbook:**
1. EF parity gap: add IPv6 class-map and policy-map entries matching the IPv4 QoS policy. Apply to all dual-stack interfaces.
2. AF parity gap: update application-based classification to match IPv6 traffic. Verify NBAR or application identification works for IPv6.
3. Tunnel DSCP issue: add `qos pre-classify` on tunnel interfaces to classify inner packets rather than the outer tunnel header.

### Step 5 — Troubleshooting

- **NBAR IPv6 support** — Cisco NBAR (Network-Based Application Recognition) may not classify IPv6 traffic for some applications. Verify NBAR IPv6 support on the platform and IOS version.

- **class-map IPv6 matching** — QoS class-maps must explicitly match IPv6 ACLs (not IPv4 ACLs). A class-map referencing an `access-list 100` will never match IPv6 traffic.

- **MQC IPv6 syntax** — On Cisco platforms, `match protocol ipv6` or `match access-group name IPv6_ACL` is required in the class-map for IPv6 traffic classification.

## SPL

```spl
index=network sourcetype="netflow" earliest=-24h
| eval ip_ver=if(isnotnull(sourceIPv6Address) OR match(src, ":"), "IPv6", "IPv4")
| eval dscp=coalesce(ipDiffServCodePoint, round(tonumber(ipClassOfService) / 4, 0))
| stats count as flows by ip_ver, dscp
| eventstats sum(flows) as total by ip_ver
| eval pct=round(flows / total * 100, 1)
| xyseries dscp ip_ver pct
| eval parity_diff=abs(coalesce(IPv4, 0) - coalesce(IPv6, 0))
| where parity_diff > 10
| eval issue=case(
    isnotnull(IPv4) AND isnull(IPv6), "DSCP " . dscp . " applied to IPv4 only — IPv6 traffic is unmarked",
    isnotnull(IPv6) AND isnull(IPv4), "DSCP " . dscp . " applied to IPv6 only — unexpected",
    parity_diff > 10, "DSCP " . dscp . " parity gap: IPv4=" . IPv4 . "% vs IPv6=" . IPv6 . "%",
    1=1, null())
| sort -parity_diff
```

## Visualization

(1) Stacked bar chart: DSCP distribution for IPv4 vs IPv6 side by side. (2) Table: DSCP values with parity gaps. (3) Timechart: DSCP EF (voice) percentage for IPv4 vs IPv6 over 7 days. (4) Single-value: number of DSCP classes with >10% parity gap.

## Known False Positives

**Different application mix.** If different applications use IPv4 vs IPv6 (e.g., legacy apps are IPv4-only, new apps are IPv6-first), the DSCP distributions will differ legitimately because they carry different traffic types.

**Tunnel endpoints.** Traffic entering or exiting tunnels may have DSCP remarked. This is legitimate if the tunnel endpoint has explicit DSCP copy/remark policies.

**Early IPv6 deployment.** In early dual-stack deployments, IPv6 traffic is predominantly web browsing and DNS (best-effort), while IPv4 carries the full application mix. This naturally creates a DSCP distribution difference that is not a policy gap.

## References

- [RFC 2474 — Definition of the Differentiated Services Field (DSCP)](https://www.rfc-editor.org/rfc/rfc2474)
- [RFC 8200 — Internet Protocol, Version 6 (IPv6) Specification (§7 — Traffic Class)](https://www.rfc-editor.org/rfc/rfc8200)
