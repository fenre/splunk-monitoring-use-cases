<!-- AUTO-GENERATED from UC-5.6.5.json — DO NOT EDIT -->

---
id: "5.6.5"
title: "DHCP Scope Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.5 · DHCP Scope Exhaustion

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Empty DHCP scopes prevent new devices from getting network access.

## Value

Network operations teams monitor DHCP scope utilization in real time, detect exhaustion before users are impacted, and identify DHCP starvation attacks or scope sizing issues.

## Implementation

For Windows: forward DHCP audit logs + scripted input for scope stats. For Infoblox: use API or syslog. Alert when >90% utilized.

## Detailed Implementation

### Prerequisites
- DHCP lease/event logs in `index=dhcp` from one or more sources: Infoblox NIOS (`sourcetype=infoblox:dhcp` via Splunk_TA_infoblox), Windows DHCP Server (`sourcetype=MSAD:NT6:DHCP` via Splunk_TA_windows), or ISC DHCP (`sourcetype=isc:dhcp`).
- For Infoblox: DHCP logs come via syslog, same forwarding path as DNS. Ensure the Grid Member's DHCP service is logging lease events (DHCPDISCOVER, DHCPOFFER, DHCPREQUEST, DHCPACK, DHCPNAK, DHCPRELEASE).
- Build a `dhcp_scopes.csv` lookup: `scope,network,pool_size,location,owner` (e.g., `10.10.1.0/24,Employee-WiFi,254,Building-A,IT-NetOps`). Pool_size = total usable IPs in the scope.
- Scope exhaustion means no available IP addresses for new DHCP clients — devices cannot join the network. This is a critical availability issue, especially for WiFi networks with high device density (phones, laptops, IoT devices).
- Exhaustion typically happens when: (a) lease times are too long (devices hoard addresses), (b) scope is too small for the number of devices, (c) static IPs were allocated within the DHCP range, (d) rogue devices flood DHCP with fake MAC addresses (DHCP starvation attack).

### Step 1 — Configure data collection
Verify DHCP data:
```spl
index=dhcp earliest=-1h
| stats count by sourcetype, host
```

Check for DHCPNAK events (indicator of scope issues):
```spl
index=dhcp "DHCPNAK" OR "NAK" earliest=-24h
| stats count by host
```

### Step 2 — Create the search and alert

**Primary search — Scope utilization by network:**
```spl
index=dhcp (sourcetype="infoblox:dhcp" OR sourcetype="MSAD:NT6:DHCP") earliest=-4h
| where match(_raw, "(?i)DHCPACK")
| rex field=_raw "(?i)(?:on|for|ip[\s:=]+)(?<lease_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
| rex field=_raw "(?i)(?:to|mac[\s:=]+)(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| eval scope=replace(lease_ip, "\.\d+$", ".0/24")
| stats dc(client_mac) as active_leases dc(lease_ip) as used_ips by scope, host
| lookup dhcp_scopes.csv scope OUTPUT pool_size network location owner
| eval util_pct=if(isnotnull(pool_size) AND pool_size>0, round(100*active_leases/pool_size, 1), null())
| eval status=case(util_pct>=95, "EXHAUSTION", util_pct>=85, "CRITICAL", util_pct>=70, "WARNING", 1==1, "Healthy")
| where util_pct>=70
| sort -util_pct
```

#### Understanding this SPL: Counts unique MAC addresses with active DHCP leases per scope to estimate utilization. Comparing active leases against the scope's total pool size gives utilization percentage. Scopes above 85% are at risk — any burst of new devices (meeting starts, shift change) could exhaust the pool.

**DHCPNAK trend — active exhaustion indicator:**
```spl
index=dhcp "DHCPNAK" OR "NAK" earliest=-24h
| bin _time span=15m
| stats count as naks by _time, host
| where naks > 5
| eval severity=case(naks > 50, "CRITICAL", naks > 20, "HIGH", 1==1, "WARNING")
```

#### Understanding this SPL: DHCPNAK (Negative Acknowledgment) means the server refused a client's request. Common causes: client requesting an IP from the wrong scope (roaming between subnets), or no available addresses (exhaustion). A sudden spike in NAKs is the most immediate indicator of exhaustion.

**Scope growth trending:**
```spl
index=dhcp "DHCPACK" earliest=-7d
| rex field=_raw "(?i)(?:on|for)\s+(?<lease_ip>\d+\.\d+\.\d+\.\d+)"
| eval scope=replace(lease_ip, "\.\d+$", ".0/24")
| bin _time span=1h
| stats dc(lease_ip) as active_leases by _time, scope
| timechart span=1h max(active_leases) as peak_leases by scope
```

### Step 3 — Validate
(a) Compare utilization with DHCP server's built-in reporting: Infoblox NIOS IPAM view, Windows DHCP console scope statistics, or ISC DHCP `dhcp-lease-list`.
(b) Verify the `dhcp_scopes.csv` pool sizes match the actual scope configuration on the DHCP server.
(c) Test: in a lab, reduce a scope to a very small range and add devices until exhaustion occurs. Verify the alert fires.

### Step 4 — Operationalize
Dashboard ("DHCP — Scope Utilization"):
- Row 1 — Single-value tiles: "Scopes > 85%", "DHCPNAK (1h)", "Total active leases", "Monitored scopes".
- Row 2 — Table: scope, network, location, active_leases, pool_size, util_pct, status.
- Row 3 — Timechart: scope utilization trending over 7 days.
- Row 4 — DHCPNAK timeline.

Alerting:
- Critical (scope > 95% or DHCPNAK > 50 in 15 minutes): active or imminent exhaustion — page network operations.
- Warning (scope > 85%): plan scope expansion.

Runbook:
1. **Scope exhaustion**: Immediately reduce lease time on the affected scope (from hours to minutes) to free IPs faster. Expand the scope if possible (extend the range, add a secondary scope, configure DHCP relay for an additional subnet).
2. **DHCP starvation attack (many unique MACs in short time)**: Enable DHCP snooping and port security on access switches. Enable MAC address rate limiting.

### Step 5 — Troubleshooting

- **Cannot determine scope from lease IP** — The `/24` assumption may be wrong. Adjust the scope derivation to match your actual subnet sizes, or use the `dhcp_scopes.csv` lookup with CIDR matching.

- **Windows DHCP logs lack MAC address** — Windows DHCP audit logs (ID 10, 11, 12) include MAC. Analytical logs may not. Ensure audit logging is enabled: `Set-DhcpServerAuditLog -Enable $true`.

- **Infoblox shows different utilization than Splunk** — Infoblox IPAM counts static allocations + DHCP leases. This search only counts DHCP leases seen in logs. Static IPs reduce the effective pool size but don't appear in DHCP ACK logs.

**DHCPv6 Considerations:** IPv6 scope or prefix-delegation exhaustion does not map cleanly to IPv4 /24-style counting—track IA_NA pools and DHCPv6-PD separately where deployed. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=dhcp sourcetype="DhcpSrvLog" OR sourcetype="infoblox:dhcp"
| stats dc(assigned_ip) as used by scope_name, scope_range
| eval total = scope_end - scope_start
| eval used_pct=round(used/total*100,1) | where used_pct > 90
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

Gauge per scope, Table, Bar chart.

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
