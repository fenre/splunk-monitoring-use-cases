<!-- AUTO-GENERATED from UC-5.6.11.json — DO NOT EDIT -->

---
id: "5.6.11"
title: "DHCP Lease Duration Analysis"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.6.11 · DHCP Lease Duration Analysis

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.

## Value

Network operations teams analyze DHCP lease duration patterns to optimize lease times per network type, identify stale leases consuming IP addresses, and detect misconfigured DHCP clients causing excessive renewals.

## Implementation

Collect DHCP server logs. Analyze lease durations per scope. Identify scopes with unusually short leases (frequent renewals) or extremely long leases. Adjust based on network type (guest vs. corporate).

## Detailed Implementation

### Prerequisites
- DHCP lease event logs in `index=dhcp` with lease duration information. Sources: Infoblox NIOS DHCP logs (`sourcetype=infoblox:dhcp`), Windows DHCP Server events (`sourcetype=MSAD:NT6:DHCP`), ISC DHCP logs. Lease duration comes from the `lease-time` parameter in the DHCP ACK, or calculated from lease start/end timestamps.
- Understanding lease duration: short leases (< 30 minutes) increase DHCP server load and cause more frequent renewals, but free IPs faster. Long leases (> 24 hours) reduce server load but can lead to scope exhaustion (devices that left the network still hold IPs). The right lease time depends on the network type: guest WiFi (1-4 hours), employee wired (8-24 hours), servers (7+ days or static reservation).
- Lease duration analysis reveals: (a) scope configuration issues (lease times not matching network type), (b) devices holding leases excessively long, (c) lease time mismatch causing address hoarding on high-mobility networks.

### Step 1 — Configure data collection
Verify lease duration data:
```spl
index=dhcp "DHCPACK" earliest=-24h
| rex field=_raw "(?i)lease[\s-]?(?:time|duration)[\s:=]+(?<lease_seconds>\d+)"
| stats count avg(lease_seconds) as avg_lease_sec by host
| eval avg_lease_hours=round(avg_lease_sec/3600, 1)
```
If `lease_seconds` is null, lease duration may not be logged directly. In that case, calculate from lease start and expiry events.

### Step 2 — Create the search and alert

**Primary search — Lease duration distribution by scope:**
```spl
index=dhcp "DHCPACK" earliest=-24h
| rex field=_raw "(?i)(?:on|for)\s+(?<lease_ip>\d+\.\d+\.\d+\.\d+)"
| rex field=_raw "(?i)lease[\s-]?(?:time|duration)[\s:=]+(?<lease_sec>\d+)"
| eval scope=replace(lease_ip, "\.\d+$", ".0/24")
| eval lease_hours=round(lease_sec/3600, 1)
| eval lease_category=case(lease_hours < 0.5, "Ultra-short (<30min)", lease_hours < 4, "Short (30min-4h)", lease_hours < 24, "Medium (4-24h)", lease_hours < 168, "Long (1-7d)", 1==1, "Very Long (>7d)")
| stats count avg(lease_hours) as avg_hours max(lease_hours) as max_hours by scope, lease_category
| sort scope, lease_category
```

#### Understanding this SPL: Categorizes lease durations to reveal configuration issues. Guest WiFi scopes should show short leases (< 4h). Employee VLANs should show medium leases (8-24h). IoT/OT devices should have longer leases (7+ days) to avoid disruption from renewals. Mismatched categories indicate misconfiguration.

**Stale lease detection — devices that stopped using the network:**
```spl
index=dhcp earliest=-7d
| rex field=_raw "(?i)(?:to|mac)[\s:=]+(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| rex field=_raw "(?i)(?:on|for)\s+(?<lease_ip>\d+\.\d+\.\d+\.\d+)"
| stats latest(_time) as last_seen earliest(_time) as first_seen by client_mac, lease_ip
| eval hours_since_seen=round((now()-last_seen)/3600, 1)
| eval lease_held_hours=round((now()-first_seen)/3600, 1)
| where hours_since_seen > 48 AND lease_held_hours > 48
| sort -lease_held_hours
| head 50
```

#### Understanding this SPL: Finds devices that were given a lease but haven't been seen in 48+ hours. These "stale" leases hold IP addresses that could be used by active devices. On high-density networks (event venues, hospitals), stale leases directly contribute to scope exhaustion.

**Lease renewal rate analysis:**
```spl
index=dhcp ("DHCPREQUEST" OR "DHCPACK") earliest=-24h
| rex field=_raw "(?i)(?:to|mac)[\s:=]+(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| stats count as events dc(eval(if(match(_raw, "DHCPREQUEST"), _raw, null()))) as requests dc(eval(if(match(_raw, "DHCPACK"), _raw, null()))) as acks by client_mac
| where requests > 20
| eval renewals_per_hour=round(requests/24, 1)
| sort -renewals_per_hour
| head 20
```

### Step 3 — Validate
(a) Compare lease times with DHCP scope configuration: `show dhcp server scope` or equivalent. Configured lease time should match observed values.
(b) Check for stale leases: compare Splunk's stale list with the DHCP server's active lease table. Devices not in the server's lease table were already released.

### Step 4 — Operationalize
Dashboard ("DHCP — Lease Analysis"):
- Row 1 — Single-value tiles: "Average lease duration (h)", "Stale leases (48h+)", "High-renewal clients", "Scopes analyzed".
- Row 2 — Lease distribution chart: stacked bar by scope and lease category.
- Row 3 — Stale lease table: MAC, IP, hours since seen.
- Row 4 — Chatty clients: MAC, renewal rate, scope.

Alerting:
- Warning (scope with > 30% stale leases): recommend reducing lease time or implementing lease cleanup.
- Warning (any client renewing > 10 times/hour): possible DHCP client issue or configuration error.

Runbook:
1. **High stale lease count**: Reduce lease time on the affected scope. For guest WiFi: 1-2 hours. For employee networks: 8 hours. This frees addresses faster when devices leave.
2. **Chatty DHCP client**: Investigate the device — it may be failing to get an IP and retrying (check for DHCPNAK), or it may have a very short lease and legitimate high renewal rate.

### Step 5 — Troubleshooting

- **Lease duration not in DHCP logs** — Not all DHCP server implementations log the lease time in every event. For Infoblox, it's often in the DHCPACK event. For Windows, check the DhcpServerAuditLog files in `%windir%\System32\dhcp`.

- **Stale lease analysis inaccurate** — The "stale" detection depends on seeing renewed DHCP events. If a device uses a static lease or sends DHCP RELEASE when disconnecting, the analysis may be off. Cross-reference with network access logs (802.1X, NAC).

**DHCPv6 Considerations:** Lease-duration tuning must use IA_NA and IA_PD preferred/valid lifetimes where logged, not only DHCPv4 lease-time fields. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=network sourcetype="infoblox:dhcp" "DHCPACK"
| rex "lease (?<lease_ip>\d+\.\d+\.\d+\.\d+).*?(?<lease_duration>\d+)"
| stats avg(lease_duration) as avg_lease, count as renewals by subnet
| eval avg_hours=round(avg_lease/3600,1) | sort -renewals
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

Table (scope, avg lease, renewal count), Bar chart (renewals by scope).

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
