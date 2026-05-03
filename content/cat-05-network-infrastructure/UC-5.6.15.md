<!-- AUTO-GENERATED from UC-5.6.15.json — DO NOT EDIT -->

---
id: "5.6.15"
title: "DHCP Pool Exhaustion and Address Allocation Issues (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.15 · DHCP Pool Exhaustion and Address Allocation Issues (Meraki)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.

## Value

Network operations teams proactively predict DHCP pool exhaustion dates across Meraki-managed sites, enabling planned pool expansion before users are impacted by address unavailability.

## Implementation

Query appliance API for DHCP metrics by VLAN. Alert on >85% allocation.

## Detailed Implementation

### Prerequisites
- Cisco Meraki event logs in `index=meraki` via Splunk_TA_cisco_meraki. This UC focuses specifically on DHCP pool exhaustion monitoring across Meraki-managed networks, complementing UC-5.6.13 with deeper pool analysis and address allocation tracking.
- Meraki MX appliances serve DHCP for configured VLANs. Pool ranges are defined in Dashboard: Network > Addressing & VLANs. The MX logs DHCP events including leases, failures, and pool status.
- Key difference from UC-5.6.13: this UC focuses on proactive capacity trending and allocation patterns, while UC-5.6.13 focuses on immediate failure detection. Use both together for comprehensive DHCP monitoring.
- Build a `meraki_networks.csv` lookup: `network_id,network_name,site,region` for site-level aggregation.

### Step 1 — Configure data collection
Verify DHCP lease volume per network:
```spl
index=meraki "dhcp" earliest=-24h
| stats count by host, event_type
```

### Step 2 — Create the search and alert

**Primary search — Pool exhaustion risk by site/VLAN:**
```spl
index=meraki "dhcp lease" earliest=-4h
| rex field=_raw "(?i)client[\s:]+(?<client_mac>[0-9a-fA-F:.-]+)"
| rex field=_raw "(?i)ip[\s:]+(?<client_ip>[\d.]+)"
| rex field=_raw "(?i)vlan[\s:=]+(?<vlan>\d+)"
| eval subnet=replace(client_ip, "\.\d+$", ".0/24")
| stats dc(client_mac) as active_clients dc(client_ip) as used_ips by host, vlan, subnet
| lookup meraki_dhcp_pools.csv subnet OUTPUT pool_size location
| eval util_pct=if(isnotnull(pool_size), round(100*active_clients/pool_size, 1), null())
| eval status=case(util_pct > 95, "EXHAUSTED", util_pct > 85, "CRITICAL", util_pct > 70, "WARNING", 1==1, "Healthy")
| where util_pct > 70
| sort -util_pct
```

**Allocation trend — growth prediction:**
```spl
index=meraki "dhcp lease" earliest=-30d
| rex field=_raw "(?i)ip[\s:]+(?<client_ip>[\d.]+)"
| eval subnet=replace(client_ip, "\.\d+$", ".0/24")
| bin _time span=1d
| stats dc(client_ip) as daily_leases by _time, subnet
| eventstats first(daily_leases) AS initial latest(daily_leases) AS current by subnet
| eval growth_rate=round((current - initial) / 30, 1)
| lookup meraki_dhcp_pools.csv subnet OUTPUT pool_size
| eval days_to_exhaustion=if(growth_rate > 0 AND isnotnull(pool_size), round((pool_size - current) / growth_rate, 0), null())
| where isnotnull(days_to_exhaustion) AND days_to_exhaustion < 60
| stats latest(current) as current_leases latest(growth_rate) as daily_growth latest(days_to_exhaustion) as days_to_exhaust by subnet
| sort days_to_exhaust
```

#### Understanding this SPL: Projects when each pool will exhaust based on 30-day growth rate. If a pool is predicted to exhaust within 60 days, proactive action is needed: expand the pool, add a VLAN, or reduce lease times.

**IP address conflict detection:**
```spl
index=meraki "dhcp" earliest=-4h
| rex field=_raw "(?i)ip[\s:]+(?<client_ip>[\d.]+)"
| rex field=_raw "(?i)client[\s:]+(?<client_mac>[0-9a-fA-F:.-]+)"
| stats dc(client_mac) as mac_count values(client_mac) as macs by client_ip
| where mac_count > 1
| eval conflict="IP address ".client_ip." assigned to ".mac_count." different MACs"
| sort -mac_count
```

### Step 3 — Validate
(a) Compare pool utilization with Meraki Dashboard: Network > Clients shows connected devices per VLAN.
(b) Verify pool sizes in the lookup match Dashboard configuration.
(c) Compare growth predictions with historical trends visible in Meraki Dashboard analytics.

### Step 4 — Operationalize
Dashboard ("Meraki — DHCP Pool Health"):
- Row 1 — Single-value tiles: "Pools at risk", "Pools > 85%", "Predicted exhaustions (60d)", "IP conflicts".
- Row 2 — Pool utilization table: subnet, location, active clients, pool size, utilization %, status.
- Row 3 — Growth prediction table: subnet, current, daily growth, days to exhaustion.
- Row 4 — IP conflict alerts.

Alerting:
- Critical (pool > 95%): immediate expansion needed — page site operations.
- Warning (predicted exhaustion < 30 days): plan expansion.
- Warning (IP address conflict detected): investigate — may cause connectivity issues.

Runbook:
1. **Pool approaching exhaustion**: In Meraki Dashboard, expand the DHCP pool range or add a secondary VLAN. Consider reducing lease time (shorter leases free addresses faster).
2. **IP conflict**: Identify both devices using the conflicting IP. One may have a static IP within the DHCP range — reserve it in the Meraki DHCP configuration or move it outside the DHCP range.

### Step 5 — Troubleshooting

- **Pool size unknown** — The Meraki API can provide pool ranges: `GET /networks/{id}/vlans` returns DHCP settings including the address range. Calculate pool_size from the range and populate the lookup.

- **Growth rate shows negative** — Device count decreased (seasonal, office moves). Negative growth is good but the prediction formula should handle it: `days_to_exhaustion` will be null for shrinking pools.

- **NAT mode vs. Bridge mode** — In NAT mode, each MR AP has its own tiny DHCP pool (default /28 = 14 addresses). This exhausts quickly in dense environments. Monitor NAT-mode APs separately.

**DHCPv6 Considerations:** Meraki pool-capacity searches here assume IPv4 lease patterns; extend monitoring if you rely on DHCPv6 or prefix delegation alongside IPv4 pools. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=cisco_network sourcetype="meraki:api" dhcp_pool=*
| stats latest(addresses_available) as available_ips, latest(pool_size) as total_pool by vlan_id
| eval allocation_pct=round((total_pool-available_ips)*100/total_pool, 2)
| where allocation_pct > 85
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

DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
