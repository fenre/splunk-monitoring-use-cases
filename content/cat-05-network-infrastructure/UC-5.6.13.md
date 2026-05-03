<!-- AUTO-GENERATED from UC-5.6.13.json — DO NOT EDIT -->

---
id: "5.6.13"
title: "Failed DHCP Assignments and IP Pool Exhaustion (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.13 · Failed DHCP Assignments and IP Pool Exhaustion (Meraki)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.

## Value

Network operations teams monitoring Meraki environments detect DHCP assignment failures and pool exhaustion per site/subnet, enabling proactive pool expansion before users lose network connectivity.

## Implementation

Monitor syslog for DHCP NACK and failure events. Alert on sustained failure rate.

## Detailed Implementation

### Prerequisites
- Cisco Meraki event logs in `index=meraki` via the Splunk_TA_cisco_meraki (Splunkbase 3018). The TA pulls events from the Meraki Dashboard API including DHCP events (`sourcetype=meraki:events` or `sourcetype=meraki`). Meraki MX/MR devices handle DHCP directly — the Dashboard API reports DHCP lease events, failures, and pool status.
- Meraki DHCP events include: `dhcp lease`, `dhcp no offers`, `dhcp nak`, `dhcp request`, `dhcp pool exhaustion`. Key fields: `client_mac`, `client_ip`, `dhcp_server`, `subnet`, `vlan`.
- Build a `meraki_dhcp_pools.csv` lookup: `network_id,subnet,vlan,pool_size,location,owner`. Pool size information comes from the Meraki Dashboard (Network > Addressing & VLANs).
- Meraki-specific consideration: in Meraki environments, DHCP is often served by the MX appliance or the MR access point itself (in NAT mode). DHCP pool exhaustion on a Meraki AP in NAT mode affects only that AP's clients — different blast radius than centralized DHCP exhaustion.

### Step 1 — Configure data collection
Verify Meraki DHCP events:
```spl
index=meraki "dhcp" earliest=-24h
| stats count by event_type
```
Expected event types: `dhcp lease`, `dhcp no offers`, `dhcp request`. If zero, check the Meraki TA configuration and API connectivity.

### Step 2 — Create the search and alert

**Primary search — Failed DHCP assignments:**
```spl
index=meraki ("dhcp no offers" OR "dhcp nak" OR "pool exhaustion") earliest=-4h
| rex field=_raw "(?i)client[\s:]+(?<client_mac>[0-9a-fA-F:.-]+)"
| rex field=_raw "(?i)(?:subnet|network)[\s:]+(?<subnet>[\d./]+)"
| rex field=_raw "(?i)vlan[\s:=]+(?<vlan>\d+)"
| stats count dc(client_mac) as affected_clients by host, subnet, vlan
| eval severity=case(affected_clients > 20, "CRITICAL", affected_clients > 5, "HIGH", 1==1, "WARNING")
| sort -affected_clients
```

#### Understanding this SPL: "dhcp no offers" means no DHCP server could provide an address — either pool exhaustion or no DHCP server reachable. "dhcp nak" means the server rejected the request. The `affected_clients` count shows how many unique devices are impacted — more than 5 affected clients in a short window indicates a systematic issue.

**Meraki DHCP pool utilization estimation:**
```spl
index=meraki "dhcp lease" earliest=-4h
| rex field=_raw "(?i)client[\s:]+(?<client_mac>[0-9a-fA-F:.-]+)"
| rex field=_raw "(?i)ip[\s:]+(?<client_ip>[\d.]+)"
| rex field=_raw "(?i)(?:subnet|network)[\s:]+(?<subnet>[\d./]+)"
| stats dc(client_mac) as active_leases by host, subnet
| lookup meraki_dhcp_pools.csv subnet OUTPUT pool_size location
| eval util_pct=if(isnotnull(pool_size), round(100*active_leases/pool_size, 1), null())
| where util_pct > 70 OR active_leases > 200
| eval status=case(util_pct > 95, "EXHAUSTION", util_pct > 85, "CRITICAL", 1==1, "WARNING")
| sort -util_pct
```

**DHCP failure trending:**
```spl
index=meraki ("dhcp no offers" OR "dhcp nak") earliest=-7d
| bin _time span=1h
| stats count as failures by _time, host
| where failures > 0
```

### Step 3 — Validate
(a) Compare with Meraki Dashboard: Network > Clients shows connected devices per SSID/VLAN. The active lease count should approximate the connected client count.
(b) In the Meraki Dashboard, check Network > Event log for the same DHCP failure events.
(c) Test: on a small test VLAN, reduce the DHCP pool to a very small range and connect devices until exhaustion. Verify alerts fire.

### Step 4 — Operationalize
Dashboard ("Meraki — DHCP Health"):
- Row 1 — Single-value tiles: "DHCP failures (4h)", "Affected clients", "Pools > 85%", "Sites with issues".
- Row 2 — Failure table: host (Meraki device), subnet, VLAN, affected_clients, severity.
- Row 3 — Pool utilization table: subnet, location, active_leases, pool_size, util_pct.
- Row 4 — Failure trending by site over 7 days.

Alerting:
- Critical (> 20 affected clients in 1 hour on any subnet): active DHCP outage — page site operations.
- Warning (pool utilization > 85%): plan pool expansion in Meraki Dashboard.

Runbook:
1. **Pool exhaustion**: In Meraki Dashboard, expand the DHCP pool range (Network > Addressing & VLANs). Alternatively, reduce the lease time to free addresses faster.
2. **"No offers" from MR in NAT mode**: The AP's local DHCP pool (10.x.x.x/28 by default) is exhausted. This affects only clients on that AP. Solutions: move to bridge mode (use centralized DHCP), or increase the NAT subnet size.

### Step 5 — Troubleshooting

- **DHCP events not appearing in Splunk** — Verify Meraki TA API key has Organization-level read access. Check Dashboard API > API access is enabled for the organization.

- **Cannot extract subnet/VLAN from events** — Meraki event log format varies by firmware version. Adjust regex patterns based on sample events (`| search "dhcp" | head 10`).

- **Meraki AP NAT mode DHCP different from MX DHCP** — In NAT mode, the AP serves DHCP locally. In bridge mode, the MX or upstream DHCP server handles it. Failure patterns differ — NAT mode failures are per-AP, bridge mode failures are network-wide.

**DHCPv6 Considerations:** Meraki DHCP failure strings and API fields are often IPv4-centric; validate Dashboard/event wording separately if you monitor DHCPv6 or dual-stack sites. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*" (signature="*failure*" OR signature="*NACK*")
| stats count as failure_count by ap_name, signature
| where failure_count > 5
| sort - failure_count
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

Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
