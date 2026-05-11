<!-- AUTO-GENERATED from UC-5.18.4.json — DO NOT EDIT -->

---
id: "5.18.4"
title: "PE-CE BGP Session Health (VRF-Aware)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.18.4 · PE-CE BGP Session Health (VRF-Aware)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the handshake between our edge router and each customer’s box inside their private slice of our network. When that handshake stumbles, we know which customer slice blinked—not just that ‘something somewhere’ coughed.*

---

## Description

Splunk highlights PE-CE BGP session transitions inside MPLS Layer-3 VPN contexts so customer-facing VRF adjacency loss, notification storms, and hold-timer expiry surface with neighbor and RD identifiers attached.

## Value

Enterprise service desks shrink mean-time-to-know because Splunk separates noisy global BGP churn from contract-critical CE peers per VPN, letting tier-one engineers page on RD-qualified outages instead of hunting ambiguous `%BGP-5-ADJCHANGE` lines.

## Implementation

Tag inbound syslog with customer-VPN lookups on RD or VRF name, require vrf-aware regex filters to exclude Internet table churn, alert when distinct CE peers per PE exceed playbook thresholds within fifteen minutes.

## Detailed Implementation

### Prerequisites
- Golden lookup `vpn_customer_map.csv` joining `rd`, `vrf`, SLA tier, and escalation contacts.
- CE addressing scheme documented so link-local % interfaces decode consistently.

### Step 1 — Logging verification
On Cisco: confirm PE logs include VRF name with BGP neighbor messages (`address-family` aware). IOS-XR often prefixes `%ROUTING-BGP-*` with VPN context—capture full text. Junos: validate `rpd` exports include routing-instance. Nokia: verify BGP instance naming matches customer VPN service IDs.

### Step 2 — Field extraction
Normalize `vrf` casing; strip `%vrfname` Cisco interface placeholders via secondary `rex`; validate RD pattern `(asn:index)`.

### Step 3 — Saved search
`pe_ce_bgp_vpn_health`: alert when `count`≥2 per `(host,vrf)` or when peer matches `tier1` lookup.

### Step 4 — CLI validation
Compare Splunk peer list to operational state: Cisco `show bgp vpnv4 unicast vrf X summary`; Junos `show bgp summary instance Y`; Nokia `show router bgp neighbor` under correct service routing instance.

### Step 5 — Dashboard handoff
Embed drilldown to traceroute/LSP health panels (cross-link UC-5.18.1 saved searches) so triage distinguishes CE-side modem faults from core issues.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| where match(st,"cisco:ios|cisco:ios_xr|cisco:ios_xe|juniper:junos|nokia")
| eval msg=lower(_raw)
| eval vrf_like=match(msg,"\\bvrf\\b|vpnv[46]|vpn.?ipv[46]|route.?distinguisher|address.?family.*vpn|rd:?\\s*[0-9]+:[0-9]+")
| eval bgp_sess=match(msg,"\\bbgp\\b") AND match(msg,"neighbor|peer|session")
| where bgp_sess=1 AND (vrf_like=1 OR match(msg,"\\bvrf\\b")) AND match(msg,"(?:down|idle|active|reset|notification|hold.?time|dead|flap|(?:state).*(?:chang))")
| rex field=_raw max_match=0 "(?i)vrf[^A-Za-z0-9_/:-]*(?<vrf>[A-Za-z0-9_.:-]+)"
| rex field=_raw max_match=0 "(?i)(?:neighbor|peer)[=: \t]+(?<neighbor>[0-9.]+|[0-9a-f:]+|%?[A-Za-z0-9/.:_-]+)"
| rex field=_raw max_match=0 "(?i)(?:rd|route.?distinguisher)\s*[:=]?\s*(?<rd>[0-9:.]+)"
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(neighbor) as peers values(rd) as rds by host vrf
| sort - count
```

## Visualization

Dashboard Studio: KPI for impacted VPNs; heatmap by `vrf` × `host`; table (`host`, `vrf`, `peers`, `rds`, `count`) filtered by SLA tier token.

## Known False Positives

**Internet BGP churn:** regex too loose pulls global neighbors—enforce `vrf_like`.**CE aggressive BFD:** BGP stays up while syslog reports notification clears—correlate.**IPv6 LL peers:** neighbor field `%interface` mismatches unless normalized.**Maintenance suppress:** forgotten suppress tags hide real outages—expire stale rows.**Duplicate syslog relays:** double counts inflate `count`—dedupe fingerprint `_raw`.

## References

- [Cisco MPLS Layer 3 VPNs Configuration Guide — BGP PE-CE](https://www.cisco.com/c/en/us/)
- [Juniper BGP Layer 3 VPNs Feature Guide](https://www.juniper.net/documentation/us/en/software/junos/bgp/)
- [IETF RFC 4364 — BGP/MPLS IP VPNs](https://www.rfc-editor.org/rfc/rfc4364)
