<!-- AUTO-GENERATED from UC-5.20.108.json — DO NOT EDIT -->

---
id: "5.20.108"
title: "Segment Routing over IPv6 (SRv6) Security and Anomaly Detection"
status: "verified"
criticality: "high"
splunkPillar: "ES"
---

# UC-5.20.108 · Segment Routing over IPv6 (SRv6) Security and Anomaly Detection

> **Criticality:** High &middot; **Difficulty:** Expert &middot; **Pillar:** ES &middot; **Type:** Security, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*In our network, we've built smart roads (SRv6) where the address on a letter also contains driving directions — telling each post office exactly where to forward it next. We watch to make sure nobody from outside our postal system is sending letters with fake driving directions that would reroute mail through the wrong post offices, where it could be read or tampered with.*

---

## Description

Monitors Segment Routing over IPv6 (SRv6) for security anomalies: unauthorized Segment Routing Header (SRH) injection at domain boundaries, SID table changes, policy violations, and locator prefix leakage. SRv6 is the successor to MPLS in modern networks and embeds forwarding instructions in IPv6 addresses, creating unique security challenges around SRH manipulation and SID exposure.

## Value

SRv6 is being deployed at scale by service providers and large enterprises as the successor to MPLS. Because SRv6 SIDs are valid IPv6 addresses, a misconfigured domain boundary that accepts external SRH packets allows traffic hijacking. Monitoring SRH processing at domain boundaries, SID table integrity, and policy compliance is essential for any SRv6 deployment. This UC detects the most common SRv6 security issues before they lead to traffic manipulation.

## Implementation

Monitor SRv6 events on all SRv6-capable routers. Alert on SRH rejections at domain boundaries (indicates external injection attempts). Track SID table changes. Verify SRv6 locator prefixes are not advertised externally.

## Detailed Implementation

### Prerequisites
- SRv6 deployment with IS-IS or OSPFv3 advertising SRv6 locators.
- SRv6-capable routers with logging enabled.
- Understanding of the SRv6 domain boundary topology.

### Step 1 — Configure data collection

**Cisco IOS-XE SRv6 logging:**
```
logging buffered 8192 informational
logging host <splunk_ip> transport udp port 514
!
segment-routing srv6
 logging
 locators
  locator MAIN
   prefix fc00:0:1::/48
  !
!
```

**SRv6 domain boundary protection (IOS-XE):**
```
ipv6 access-list SRV6-DOMAIN-BOUNDARY
 remark Drop SRH from external sources
 deny ipv6 any any routing-type 3 log
 permit ipv6 any any
!
interface GigabitEthernet0/0/0
 description External peering - NO SRH accepted
 ipv6 traffic-filter SRV6-DOMAIN-BOUNDARY in
```

**Verification — SID table monitoring:**
```spl
index=network sourcetype="cisco:iosxe" "SRv6" earliest=-24h | stats count by host
```

### Step 2 — Create security searches

**SRH injection detection (domain boundary):**
```spl
index=network (sourcetype="cisco:iosxe" OR sourcetype="cisco:nxos") earliest=-24h
  "%IPV6_ACL" AND "routing-type 3" AND "denied"
| rex field=_raw "(?:src|source)\s*=?\s*(?<external_src>[0-9a-fA-F:.]+)"
| stats count as injection_attempts by host, external_src
| eval alert="SRH injection attempt from " . external_src . " blocked at " . host . " (" . injection_attempts . " attempts)"
| sort -injection_attempts
```

**SRv6 locator leak detection:**
```spl
index=network (sourcetype="cisco:iosxe" OR sourcetype="juniper:junos") earliest=-24h
  "BGP" AND ("fc00:" OR "fd00:") AND ("advertise" OR "announce")
| eval is_srv6_locator=if(match(_raw, "fc00:0:[0-9a-fA-F]+::/48"), 1, 0)
| eval is_external_peer=if(match(_raw, "(?i)eBGP|external"), 1, 0)
| where is_srv6_locator=1 AND is_external_peer=1
| eval alert="SRv6 locator prefix leaked to external BGP peer — immediate remediation required"
| table _time, host, alert
```

### Step 3 — Validate
(a) **Domain boundary test.** From outside the SR domain, send a packet with an SRH (Routing Header Type 3). Verify it is dropped and logged at the domain boundary router.

(b) **SID table audit.** Compare the running SID table (`show segment-routing srv6 sid`) against the expected SID table from configuration management. Flag any discrepancies.

(c) **Locator containment.** Verify SRv6 locator prefixes are not leaked to external BGP peers by checking `show bgp ipv6 unicast neighbors <peer> advertised-routes`.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — SRv6 Security"):
- Row 1 — Single-values: SRH rejections (should be zero in a clean environment), SID table size.
- Row 2 — Table: SRH injection attempts with source and target.
- Row 3 — SID table changes (new installs/removals).
- Row 4 — Locator prefix containment status.

**Alert 1:** SRH rejected at domain boundary — high. Possible SRH injection attempt.
**Alert 2:** SRv6 locator prefix advertised to external BGP peer — critical. Traffic hijacking risk.
**Alert 3:** Unexpected SID installed in SID table — medium. Verify intentional.

### Step 5 — Troubleshooting

- **SRH packets dropped internally.** If SRH packets are being dropped within the SR domain (not at the boundary), check that all routers in the path have the SRv6 locator and SID installed. Missing SIDs cause the router to drop the packet.

- **SID table synchronisation.** In multi-area IS-IS, SRv6 locators must be redistributed between areas. Missing redistribution causes SID table gaps and traffic black holes.

- **Micro-SID security.** When using SRv6 micro-SID (uSID), the compressed SID format means multiple SIDs are packed into a single 128-bit field. Monitoring tools must understand uSID encoding to correctly parse the SID list.

## SPL

```spl
index=network (sourcetype="cisco:iosxe" OR sourcetype="cisco:nxos" OR sourcetype="juniper:junos") earliest=-24h
  ("%SRV6" OR "%ISIS" OR "segment-routing" OR "srv6" OR "SRH")
| eval event_type=case(
    match(_raw, "(?i)SRH.*drop|SRH.*reject|SRH.*invalid"), "SRH_REJECTED",
    match(_raw, "(?i)SID.*install|SID.*add"), "SID_INSTALLED",
    match(_raw, "(?i)SID.*delete|SID.*remove"), "SID_REMOVED",
    match(_raw, "(?i)policy.*fail|policy.*violation"), "POLICY_VIOLATION",
    match(_raw, "(?i)locator.*change|locator.*update"), "LOCATOR_CHANGE",
    match(_raw, "(?i)SRv6.*error|SRv6.*fail"), "SRV6_ERROR",
    1=1, "OTHER")
| eval severity=case(
    event_type="SRH_REJECTED", "HIGH — SRH packet rejected at domain boundary (possible injection attempt)",
    event_type="POLICY_VIOLATION", "HIGH — SRv6 policy violation detected",
    event_type="SRV6_ERROR", "MEDIUM — SRv6 processing error",
    event_type="LOCATOR_CHANGE", "INFO — SRv6 locator update (verify intentional)",
    1=1, "INFO")
| stats count as events by host, event_type, severity
| sort -events
```

## Visualization

(1) Table: SRv6 events by type and device. (2) Single-value: SRH rejection count. (3) Timeline: SID table changes. (4) Map: SRv6 topology with anomaly indicators.

## Known False Positives

**SRv6 topology changes.** During planned maintenance or network convergence, SID installations and removals are expected. Correlate with change management windows.

**IGP convergence.** When IS-IS or OSPF reconverges, SRv6 locators may be withdrawn and re-advertised. Brief SID changes during convergence are normal.

**SRH at domain boundary.** If inter-domain SRv6 peering is intentionally configured (e.g., between two trusted domains), SRH acceptance at the boundary is expected. Document these peering relationships.

## References

- [RFC 8754 — IPv6 Segment Routing Header (SRH)](https://www.rfc-editor.org/rfc/rfc8754)
- [RFC 8986 — Segment Routing over IPv6 (SRv6) Network Programming](https://www.rfc-editor.org/rfc/rfc8986)
- [RFC 9256 — Segment Routing Policy Architecture](https://www.rfc-editor.org/rfc/rfc9256)
- [draft-ietf-spring-srv6-security — SRv6 Security Considerations](https://datatracker.ietf.org/doc/draft-ietf-spring-srv6-security/)
