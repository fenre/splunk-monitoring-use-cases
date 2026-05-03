<!-- AUTO-GENERATED from UC-5.20.19.json — DO NOT EDIT -->

---
id: "5.20.19"
title: "NDP Cache Size Trending and Capacity Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.19 · NDP Cache Size Trending and Capacity Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Availability, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*Each router keeps a contact list of all the IPv6 devices it can talk to directly — like a phone book for the local neighbourhood. If this phone book gets too full, the router cannot add new contacts and new devices cannot connect to the network. We watch how full each phone book is getting and warn before it overflows.*

---

## Description

Tracks the number of entries in the IPv6 Neighbor Discovery Protocol (NDP) cache on each Layer 3 interface and alerts when utilisation approaches the platform-specific hard limit. Unlike ARP tables in IPv4, NDP caches grow significantly larger because each IPv6 host produces multiple cache entries — a link-local address, one or more global unicast addresses, and temporary privacy extension addresses that rotate daily. A subnet with 200 hosts may generate 600-1000 NDP entries, easily approaching default limits. When the NDP cache reaches capacity, the device cannot resolve new neighbor solicitations, causing packet drops and connectivity loss for newly connecting hosts — while existing connections may continue to work (since those entries are already cached), making the problem appear intermittent and extremely difficult to troubleshoot.

## Value

NDP cache exhaustion is one of the most commonly overlooked IPv6 failure modes. Network engineers familiar with ARP tables rarely check NDP cache capacity because they assume the same sizing applies. In reality, IPv6 privacy extension addresses (RFC 8981) can multiply the cache entries per host by 5-10x, and a single broadcast domain with 500 hosts can generate 2000-5000 NDP entries. The default gc_thresh3 of 1024 on Linux gateways will be exhausted, causing silent drops. This use case provides early warning by tracking NDP cache utilisation over time and alerting well before the hard limit is reached.

## Implementation

Poll NDP cache entry counts via SNMP (`ipv6NetToMediaTable` row count) or CLI scraping (`show ipv6 neighbors summary`) on every Layer 3 device. Store per-interface entry counts in Splunk. Compare against known platform limits (stored in a lookup) and alert at 70% utilisation. Trend over time to project when capacity will be reached.

## Detailed Implementation

### Prerequisites
- SNMP v2c/v3 polling access to all Layer 3 devices from the SC4SNMP host or Splunk SNMP input.
- Knowledge of platform-specific NDP cache limits:
  - Cisco IOS/IOS-XE: default 4096 per interface (`ipv6 nd cache interface-limit <max>`).
  - Cisco NX-OS: default 9216 per VRF.
  - Juniper Junos: default 20000 per routing-instance.
  - Linux: `sysctl net.ipv6.neigh.default.gc_thresh3` (default 1024, but often set to 4096 or 16384 in production).
  - Arista EOS: default 4096 per VRF.
- A capacity lookup (CSV or KV store) mapping each device/interface to its configured NDP cache limit. This is essential — without it, you cannot calculate utilisation percentage.

### Step 1 — Configure data collection

**Create the capacity lookup:**
```csv
host,interface,gc_thresh3
core-sw-01,Vlan100,4096
core-sw-01,Vlan200,4096
core-rtr-01,GigabitEthernet0/0,4096
linux-gw-01,eth0,16384
```
Upload as `ndp_capacity_lookup.csv` to the IPv6 monitoring app.

**SNMP polling for NDP cache entry count:**

The simplest approach is to count rows in `ipv6NetToMediaTable`:
```yaml
# SC4SNMP profiles.yaml
profile_ndp_cache_count:
  frequency: 300
  varBinds:
    - ['1.3.6.1.2.1.55.1.12']  # ipv6NetToMediaTable
```
Alternatively, on Cisco IOS/IOS-XE, use the `show ipv6 neighbors statistics` CLI command via SSH scripted input:
```
show ipv6 neighbors statistics

ICMPv6 Adjacency Statistics
Entry count: 347, High-water mark: 892
Limit: 4096
```
This output provides entry count, high-water mark, and limit directly.

**Scripted input for CLI approach:**
```bash
#!/bin/bash
# ndp_cache_stats.sh — collect NDP cache statistics from all routers
for device in $(cat /opt/splunk/etc/apps/ipv6_ops/lookups/l3_devices.txt); do
  echo "=== $device ==="
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 splunk-svc@$device \
    "show ipv6 neighbors statistics" 2>/dev/null
done
```
```
# inputs.conf
[script://./bin/ndp_cache_stats.sh]
interval = 300
sourcetype = ndp:stats
index = network
source = ndp_cache_stats
```

**Verification:**
```spl
index=network (sourcetype="ndp:stats" OR sourcetype="sc4snmp") earliest=-15m
| stats count by host
```

### Step 2 — Create the search and alert

**Primary search — NDP cache utilisation per interface:**
```spl
index=network (sourcetype="ndp:stats" OR sourcetype="sc4snmp" OR sourcetype="ndp:cache") earliest=-15m
| rex field=_raw "Entry count:\s*(?<ndp_entries>\d+).*Limit:\s*(?<ndp_limit>\d+)"
| eval ndp_entries=if(isnotnull(ndp_entries), tonumber(ndp_entries), 1)
| stats latest(ndp_entries) as ndp_entries latest(ndp_limit) as ndp_limit by host
| lookup ndp_capacity_lookup host OUTPUT gc_thresh3
| eval capacity=coalesce(ndp_limit, gc_thresh3, 4096)
| eval utilization_pct=round(ndp_entries / capacity * 100, 1)
| eval status=case(
    utilization_pct >= 90, "CRITICAL",
    utilization_pct >= 70, "WARNING",
    1=1, "OK")
| sort -utilization_pct
| table host, ndp_entries, capacity, utilization_pct, status
```

**Understanding this SPL:**
- Parses `Entry count` and `Limit` from Cisco `show ipv6 neighbors statistics` output.
- Falls back to the capacity lookup if the CLI output doesn't include a limit field.
- Default capacity of 4096 if neither source has the data.
- Three-tier alerting: OK (<70%), WARNING (70-89%), CRITICAL (>=90%).

**Alert — NDP cache approaching capacity:**
```spl
<above search>
| where utilization_pct >= 70
```
Trigger: any result. Priority: CRITICAL >=90%, WARNING >=70%. Action: PagerDuty/email network operations.

**Trending search — project exhaustion date:**
```spl
index=network (sourcetype="ndp:stats" OR sourcetype="sc4snmp") earliest=-30d
| timechart span=1d avg(ndp_entries) as avg_entries by host
| predict avg_entries as predicted_entries algorithm=LLP5 future_timespan=30
| eval days_to_capacity=if(predicted_entries > 0, round((4096 - predicted_entries) / ((predicted_entries - avg_entries) / 30)), "N/A")
```

### Step 3 — Validate
(a) **Known count comparison.** On a router, run `show ipv6 neighbors` and count entries manually. Compare with Splunk `ndp_entries` — should match within 5% (entries may arrive/depart between CLI snapshot and SNMP poll).

(b) **Capacity test.** On a lab device with gc_thresh3=100, connect more than 100 IPv6 hosts (or use a packet generator). Observe the Splunk utilisation percentage climbing past 100% and the CRITICAL alert firing. Verify the actual connectivity impact: host #101 should fail NDP resolution.

(c) **Lookup validation.** Query the capacity lookup: `| inputlookup ndp_capacity_lookup | stats count`. Ensure every L3 device is listed with correct limits.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Cache Capacity"):
- Row 1 — Single-value: devices in CRITICAL, devices in WARNING, devices OK.
- Row 2 — Bar chart: top 20 interfaces by NDP cache utilisation %.
- Row 3 — Timechart: NDP entry count trending for top 5 busiest devices (30-day view with prediction).
- Row 4 — Table: full inventory with utilisation, status, and capacity.

**Scheduling:** Poll every 5 minutes. Alert evaluation every 5 minutes for CRITICAL, every 15 minutes for WARNING.

**Runbook:**
1. WARNING (70-89%): Review the interface — is the subnet legitimately growing (new hosts, new VLANs), or is privacy extension churn inflating entries? Action: increase gc_thresh3 to 2x current limit, or reduce subnet size by splitting the /64.
2. CRITICAL (>=90%): Immediate risk of connectivity loss. Temporary fix: clear old entries (`clear ipv6 neighbors` on Cisco) and increase the cache limit. Permanent fix: reduce the broadcast domain size (split into smaller subnets) or tune privacy extension lifetimes.
3. Investigate privacy extension impact: `index=network sourcetype=ndp:cache host=<device> | stats dc(ipv6_address) as addr_count by mac_address | where addr_count > 5` — if many MACs have >5 addresses, privacy extensions are the primary driver.

### Step 5 — Troubleshooting

- **NDP cache limits not visible via SNMP** — The `ipv6NetToMediaTable` shows entries but not the configured limit. Use CLI-based collection (`show ipv6 neighbors statistics`) for limit information, or maintain the capacity lookup manually.

- **Sudden cache spikes after network changes** — Adding a new VLAN or connecting a new access switch floods the NDP cache as all hosts on the new segment resolve. This is expected during onboarding events.

- **Linux gc_thresh confusion** — Linux has three thresholds: gc_thresh1 (128, minimum retained entries), gc_thresh2 (512, soft limit — triggers faster garbage collection), gc_thresh3 (1024, hard limit — new entries are rejected). Most monitoring should focus on gc_thresh3 as the failure boundary. Check with: `sysctl net.ipv6.neigh.default.gc_thresh3`.

- **Different limits per VRF on NX-OS** — Cisco NX-OS sets NDP cache limits per VRF, not per interface. Ensure the capacity lookup reflects VRF-level limits if you run multi-VRF.

## SPL

```spl
index=network sourcetype="sc4snmp" OR sourcetype="ndp:cache"
| eval ndp_entry=1
| stats count as ndp_entries by host, interface
| lookup ndp_capacity_lookup host OUTPUT gc_thresh3 as capacity
| eval utilization_pct=round(ndp_entries / capacity * 100, 1)
| where utilization_pct > 70
| sort -utilization_pct
| table host, interface, ndp_entries, capacity, utilization_pct
```

## Visualization

(1) Single-value: interfaces above 70% NDP cache utilisation. (2) Table: per-interface NDP entries vs capacity with utilisation percentage. (3) Timechart: NDP cache entry count over time per device — trending upward indicates growth that may exceed capacity. (4) Bar chart: top 10 interfaces by NDP utilisation percentage.

## Known False Positives

**Privacy extension churn events.** When many hosts simultaneously rotate their privacy extension addresses (typically at midnight or on a 24-hour cycle), the NDP cache may briefly spike as both old (STALE) and new (REACHABLE) entries coexist. The spike resolves within minutes as garbage collection clears STALE entries. This is normal and should not trigger capacity alerts unless it pushes the cache above 70%.

**Network scanning tools.** Authorised vulnerability scanners targeting an IPv6 subnet may temporarily inflate the NDP cache with INCOMPLETE entries for scanned addresses. These expire quickly (default: 3 seconds for INCOMPLETE state on Cisco) but can cause a transient spike.

**VRRP/HSRP failover.** After a gateway failover, the new active router's NDP cache starts empty and fills rapidly as all hosts re-resolve. This is normal NDP operation and the cache stabilises within seconds.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (NDP cache mechanics, Neighbor Solicitation/Advertisement lifecycle)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 6583 — Operational Neighbor Discovery Problems (NDP cache exhaustion, scanning attacks, gc_thresh recommendations)](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.1 — NDP cache capacity planning)](https://www.rfc-editor.org/rfc/rfc9099)
