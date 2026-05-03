<!-- AUTO-GENERATED from UC-5.6.16.json — DO NOT EDIT -->

---
id: "5.6.16"
title: "DHCP Lease Exhaustion and Scope Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.16 · DHCP Lease Exhaustion and Scope Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Exhausted DHCP scopes prevent new devices from joining the network. Monitoring utilization and lease count supports proactive scope expansion or cleanup.

## Value

Network operations teams maintain a unified view of DHCP scope utilization across all enterprise DHCP servers (Infoblox, Windows, ISC), predicting exhaustion dates and alerting before users lose network connectivity.

## Implementation

Poll DHCP server (Infoblox API, Windows WMI, or lease file) for scope size and in-use count. Ingest daily or hourly. Alert when utilization exceeds 85%. Track lease duration and stale lease cleanup.

## Detailed Implementation

### Prerequisites
- DHCP lease and scope data from enterprise DHCP servers flowing into `index=dhcp`. This is a comprehensive scope utilization UC covering multiple DHCP server platforms: Infoblox NIOS (`sourcetype=infoblox:dhcp`), Windows DHCP Server (`sourcetype=MSAD:NT6:DHCP`), ISC DHCP (`sourcetype=isc:dhcp`), and Cisco IOS DHCP (`sourcetype=syslog` with DHCP messages).
- Build a comprehensive `all_dhcp_scopes.csv` lookup: `scope_id,network,pool_size,server_type,location,vlan,owner,contact`. This should cover all scopes across all DHCP servers for a unified view.
- Lease exhaustion lifecycle: (1) Healthy (< 70% utilization), (2) Monitoring (70-84%), (3) Warning (85-94%), (4) Critical (95-99%), (5) Exhausted (100% — no new clients can connect). The goal is to alert at stage 3 and resolve before stage 5.
- Multi-server consideration: in environments with DHCP failover pairs (Infoblox Grid, Windows DHCP failover, ISC failover), utilization must be calculated across the pair, not per server.

### Step 1 — Configure data collection
Verify DHCP data from all server types:
```spl
index=dhcp earliest=-1h
| stats count by sourcetype, host
```
Each DHCP server should appear. If a server is missing, check its log forwarding configuration.

### Step 2 — Create the search and alert

**Primary search — Unified scope utilization across all DHCP servers:**
```spl
index=dhcp earliest=-4h
| where match(_raw, "(?i)DHCPACK|lease.*granted|Ack")
| rex field=_raw "(?i)(?:on|for|ip)[\s:=]+(?<lease_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
| rex field=_raw "(?i)(?:to|mac)[\s:=]+(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| eval scope_prefix=replace(lease_ip, "\.\d+$", ".0/24")
| stats dc(client_mac) as active_leases dc(lease_ip) as used_ips latest(_time) as last_activity by scope_prefix, host, sourcetype
| lookup all_dhcp_scopes.csv scope_id as scope_prefix OUTPUT pool_size network location vlan owner
| eval util_pct=if(isnotnull(pool_size) AND pool_size>0, round(100*active_leases/pool_size, 1), null())
| eval status=case(util_pct>=98, "EXHAUSTED", util_pct>=95, "CRITICAL", util_pct>=85, "WARNING", util_pct>=70, "Monitor", 1==1, "Healthy")
| where util_pct>=70 OR active_leases > 200
| sort -util_pct
```

#### Understanding this SPL: A unified search across Infoblox, Windows DHCP, and ISC DHCP. The regex patterns cover common DHCP ACK log formats. The lookup provides pool sizes for utilization calculation. The status tiers follow industry best practices for DHCP capacity management.

**Exhaustion prediction (30-day trending):**
```spl
index=dhcp "DHCPACK" OR "lease granted" OR "Ack" earliest=-30d
| rex field=_raw "(?i)(?:on|for)\s+(?<lease_ip>\d+\.\d+\.\d+\.\d+)"
| eval scope=replace(lease_ip, "\.\d+$", ".0/24")
| bin _time span=1d
| stats dc(lease_ip) as daily_leases by _time, scope
| eventstats first(daily_leases) as initial latest(daily_leases) as current by scope
| eval daily_growth=round((current - initial)/30, 1)
| lookup all_dhcp_scopes.csv scope_id as scope OUTPUT pool_size location
| eval days_to_full=if(daily_growth > 0 AND isnotnull(pool_size), round((pool_size - current)/daily_growth, 0), null())
| where isnotnull(days_to_full) AND days_to_full < 90 AND days_to_full > 0
| stats latest(current) as current latest(daily_growth) as growth latest(days_to_full) as days_to_full by scope, location
| sort days_to_full
```

**DHCPNAK/decline rate — scope health indicator:**
```spl
index=dhcp ("DHCPNAK" OR "NAK" OR "DHCPDECLINE" OR "decline") earliest=-24h
| bin _time span=1h
| rex field=_raw "(?i)(?:on|for)\s+(?<lease_ip>\d+\.\d+\.\d+\.\d+)"
| eval scope=replace(lease_ip, "\.\d+$", ".0/24")
| stats count as failures by _time, scope, host
| where failures > 3
| sort -failures
```

### Step 3 — Validate
(a) Compare utilization with each DHCP server's native reporting: Infoblox NIOS IPAM, Windows DHCP console, ISC dhcpd-pool.
(b) Verify the `all_dhcp_scopes.csv` is comprehensive — missing scopes show as null pool_size.
(c) During a known exhaustion event (if you've experienced one), verify the alerts would have fired in time.

### Step 4 — Operationalize
Dashboard ("DHCP — Enterprise Scope Health"):
- Row 1 — Single-value tiles: "Scopes > 85%", "Predicted exhaustions (90d)", "NAK rate (24h)", "Total active leases".
- Row 2 — Status table: scope, network, location, VLAN, server, active_leases, pool_size, util_pct, status. Color-coded.
- Row 3 — Exhaustion prediction table: scope, current, daily growth, days to exhaustion.
- Row 4 — NAK/Decline trending by scope.

Alerting:
- Critical (any scope > 95%): page network operations — new clients cannot connect.
- Warning (scope > 85% or predicted exhaustion < 30 days): schedule scope expansion.
- Informational (NAK rate > 10/hour on any scope): investigate — may indicate client issues or early exhaustion.

Runbook:
1. **Scope at 95%+**: Immediate actions: reduce lease time (short-term), expand pool range (if subnetting allows), add a secondary DHCP scope on a new subnet, or implement DHCP relay to an additional scope.
2. **Predicted exhaustion within 30 days**: Plan scope expansion during the next change window. Request additional subnet allocation from IP address management.
3. **High NAK rate**: Investigate cause — if NAKs are from clients requesting addresses from a wrong subnet (roaming), this is expected. If NAKs are from the server refusing all requests, the scope may have issues (conflicts, reservations consuming the pool).

### Step 5 — Troubleshooting

- **Different DHCP log formats across servers** — The regex patterns cover common formats. For custom formats, test against sample events and adjust.

- **Scope derivation from IP assumes /24** — Adjust the `replace` pattern for non-/24 scopes. For accurate scoping, use a CIDR-aware lookup or maintain the exact scope ranges in the lookup.

- **Failover pair double-counting** — If both failover partners serve the same scope, active leases may appear on both servers. Deduplicate by MAC address: the `dc(client_mac)` already handles this within the search.

**DHCPv6 Considerations:** Unified enterprise utilization should separate IPv4 scopes from DHCPv6 IA_NA and prefix-delegation pools—regex and pool lookups that assume dotted-quad IPs will miss IPv6. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=network sourcetype=dhcp_scope
| eval used_pct=round(leases_in_use/scope_size*100, 1)
| stats latest(used_pct) as pct, latest(leases_in_use) as used by scope_name, server
| where pct > 85
| table scope_name server used scope_size pct
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

## Visualization

Gauge per scope, Table (scope, used, size, %), Line chart (utilization trend).

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
