<!-- AUTO-GENERATED from UC-5.20.16.json — DO NOT EDIT -->

---
id: "5.20.16"
title: "Neighbor Cache Historical Logging"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.16 · Neighbor Cache Historical Logging

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep a detailed log of which device was using which internet address at every moment, like a hotel keeping records of which guest was in which room on any given night. If there's ever a question about who was behind a certain address, we can look it up in our records even weeks later.*

---

## Description

Continuously polls and archives NDP neighbor cache entries from all Layer 3 devices, building a historical record of every MAC-to-IPv6 binding observed on the network. This is the IPv6 equivalent of historical ARP table logging, but more critical because IPv6 devices generate multiple addresses (link-local, global, privacy extensions) and privacy extension addresses rotate every 24 hours. Without historical NDP cache data, you cannot answer 'who had this IPv6 address last Tuesday at 3pm?' — the address may have already rotated out of the live NDP cache. RFC 9099 §2.6.1.4 identifies NDP cache logging as a cornerstone of IPv6 operational security.

## Value

The NDP cache is the only authoritative source of MAC-to-IPv6 bindings at the network layer. It bridges the gap between Layer 3 (IPv6 address in logs) and Layer 2 (MAC address for device identification). Without historical NDP data retained in Splunk, forensic investigations hit a dead end: the IPv6 address from a security alert may have been a privacy extension address that expired 6 hours later, and the router's live NDP cache no longer contains it. With historical retention (90+ days), you can trace any IPv6 address back to a MAC at any point in time — and from the MAC, to the switch port via 802.1X/CAM table, to the user via RADIUS. This is the foundation of the forensic chain described in UC-5.20.15.

## Implementation

Configure SC4SNMP or SNMP Modular Input to poll `ipv6NetToMediaTable` from every Layer 3 device at 5-minute intervals (30-second intervals for high-security environments per RFC 9099). Each poll captures the complete NDP cache snapshot. Retain the data for 90-365 days depending on compliance requirements. Use a summary index or the KV store `ndp_cache_lookup` for fast forensic lookups.

## Detailed Implementation

### Prerequisites
- SNMP v2c or v3 access from the Splunk polling host to all Layer 3 network devices. The polling host needs reachability to the device management IP on UDP 161.
- The device must support RFC 4293 `ipv6NetToMediaTable` (OID 1.3.6.1.2.1.55.1.12). Verify: `snmpwalk -v2c -c <community> <device> 1.3.6.1.2.1.55.1.12 | head 5`. If it returns entries, the MIB is supported.
- Sufficient Splunk license capacity for NDP cache data volume. Sizing: a campus with 500 L3 interfaces averaging 20 NDP entries each, polled every 300 seconds = 500 × 20 × 288 polls/day = 2.88M events/day ≈ 300 MB – 1 GB/day depending on event size.
- Index retention: minimum 90 days for regulatory compliance (SOC 2, HIPAA); 365 days recommended for full forensic capability.

### Step 1 — Configure data collection

**Using SC4SNMP (recommended for scale):**

Create a polling profile for NDP cache:
```yaml
# SC4SNMP profiles.yaml
profile_ndp_cache:
  frequency: 300  # 5-minute intervals; reduce to 30 for high-security
  varBinds:
    - ['1.3.6.1.2.1.55.1.12']  # ipv6NetToMediaTable
```

Map to devices:
```yaml
# SC4SNMP inventory.yaml
- address: 10.1.1.1
  port: 161
  version: 2c
  community: <community_string>
  profiles:
    - profile_ndp_cache
- address: 10.1.1.2
  port: 161
  version: 2c
  community: <community_string>
  profiles:
    - profile_ndp_cache
```

Configure HEC output to Splunk:
```yaml
# SC4SNMP values.yaml (Kubernetes)
splunk:
  hec:
    url: https://splunk-hf.example.com:8088
    token: <hec_token>
    index: network
    sourcetype: ndp:cache
```

**Using scripted CLI input (alternative for small environments):**
```bash
#!/bin/bash
# collect_ndp_cache.sh
for router in $(cat /opt/splunk/etc/apps/ipv6_ops/lookups/l3_devices.txt); do
  echo "=== $router ==="
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 splunk-svc@$router \
    "show ipv6 neighbors" 2>/dev/null
done
```
```
# inputs.conf
[script://./bin/collect_ndp_cache.sh]
interval = 300
sourcetype = ndp:cache
index = network
source = ndp_cache_poll
```

**Verification:**
```spl
index=network sourcetype="ndp:cache" earliest=-15m
| stats count by host
| sort host
```
Expected: one row per polled device with count > 0. If a device shows 0, check SNMP connectivity or SSH access.

### Step 2 — Create the search and alert

**Primary search — historical NDP binding record:**
```spl
index=network sourcetype="ndp:cache" earliest=-24h
| where NOT match(ipv6_address, "^ff")
| stats min(_time) as first_seen max(_time) as last_seen count as poll_count latest(state) as ndp_state latest(host) as switch latest(interface) as port by mac_address, ipv6_address
| eval first_seen_fmt=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
| eval last_seen_fmt=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| eval duration_hours=round((last_seen - first_seen) / 3600, 1)
| sort mac_address, -last_seen
```

**Understanding this SPL:**
- Groups by `mac_address` + `ipv6_address` to track each unique binding.
- `min(_time)` and `max(_time)` provide the first and last time each binding was observed — the forensic window.
- `poll_count` shows how many polls captured this binding — higher counts = more confident in the binding's persistence.
- Filters out multicast addresses (ff::) which are group memberships, not device bindings.

**Forensic lookup — trace an IPv6 address at a specific time:**
```spl
index=network sourcetype="ndp:cache" ipv6_address="2001:db8:1::a8bb:ccff:fedd:eeff"
| stats min(_time) as first_seen max(_time) as last_seen values(mac_address) as mac_addresses values(host) as switches values(interface) as ports by ipv6_address
| eval first_seen=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
```
Replace the address with the target from the security incident.

**Populate the NDP cache KV store lookup (schedule every 5 minutes):**
```spl
index=network sourcetype="ndp:cache" earliest=-10m
| where NOT match(ipv6_address, "^fe80:") AND NOT match(ipv6_address, "^ff")
| stats latest(mac_address) as mac_address latest(host) as switch_hostname latest(interface) as switch_port latest(state) as ndp_state latest(_time) as last_seen by ipv6_address
| outputlookup ndp_cache_lookup
```

**Alert — NDP polling gap detection:**
```spl
index=network sourcetype="ndp:cache" earliest=-1h
| stats latest(_time) as last_poll by host
| eval age_minutes=round((now() - last_poll) / 60)
| where age_minutes > 15
| table host, age_minutes
```
Trigger: any device with no NDP cache data in 15 minutes (3x the expected 5-minute poll interval). Indicates SNMP polling failure for that device.

### Step 3 — Validate
(a) **Live comparison:** On a switch, run `show ipv6 neighbors`. Count the entries. In Splunk: `index=network sourcetype=ndp:cache host=<switch> earliest=-10m | stats dc(ipv6_address)`. The counts should be close (within 10% — some entries may age out between the CLI snapshot and the last poll).

(b) **Forensic test:** Find your own MAC address and IPv6 address. Search Splunk for the binding over the last 7 days. Verify the first_seen and last_seen timestamps make sense (first_seen should be ≤ when you connected, last_seen should be recent if you're currently connected).

(c) **Completeness check:** `index=network sourcetype=ndp:cache earliest=-24h | stats dc(host) as polled_devices | eval expected_devices=<your_l3_device_count>`. If polled < expected, some devices are not being polled.

(d) **Retention check:** `index=network sourcetype=ndp:cache earliest=-90d latest=-89d | stats count`. If zero, your retention policy is shorter than 90 days — adjust index retention.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Cache History"):
- Row 1 — Single-value: devices polled, total unique bindings (24h), days of history available.
- Row 2 — Forensic lookup: input fields for IPv6 address and/or MAC → returns binding history.
- Row 3 — Polling health: timechart of poll count by device — gaps indicate failures.
- Row 4 — Top new bindings (last 24h): MAC-IPv6 pairs seen for the first time — potential new devices or new privacy extension addresses.

**Scheduling:** Polling every 5 minutes (automated by SC4SNMP or scripted input). KV store lookup refresh every 5 minutes. Polling gap alert every 15 minutes.

**Runbook:**
1. Polling gap alert: check SC4SNMP pod health (`kubectl get pods -n sc4snmp`), SNMP reachability to the device (`snmpwalk -v2c -c <community> <device> sysUpTime.0`), and device SNMP configuration.
2. Forensic request from security team: run the forensic lookup search with the target address and time. If no results, extend the search to historical data (summary index). If still no results, the address was not in any polled NDP cache during the retention window — it may have been on an unpolled device or expired before the next poll.
3. Capacity planning: if NDP cache data volume exceeds license budget, consider: increasing poll interval to 10 minutes (reduces volume 50%), excluding infrastructure-only VLANs (no endpoints = no forensic value), or using summary indexing to retain only the first_seen/last_seen per binding rather than every poll.

### Step 5 — Troubleshooting

- **Zero NDP entries from a device** — The device may not support `ipv6NetToMediaTable`, or IPv6 is not configured on any interface. Verify: `snmpwalk -v2c -c <community> <device> 1.3.6.1.2.1.55.1.12`. If no response, check SNMP ACL on the device — it may allow IPv4 SNMP but not IPv6 MIB access.

- **Entries only for link-local addresses** — If only fe80:: entries appear, global IPv6 is not deployed on those VLANs (only NDP for link-local). Check RA configuration (UC-5.20.9) — are global prefixes being advertised?

- **Stale entries accumulating** — NDP cache entries in STALE state can persist for hours. Over time, the historical record may grow with many stale entries for devices that have left the network. This is acceptable — the first_seen/last_seen timestamps provide context.

- **SNMP timeout during large polls** — Devices with thousands of NDP entries may take > 30 seconds to respond to a full table walk. Increase SNMP timeout in SC4SNMP (`snmp.timeout: 60`) or use SNMP GETBULK (non-repeaters=0, max-repetitions=50) for faster table retrieval.

## SPL

```spl
index=network sourcetype="ndp:cache" earliest=-24h
| eval entry_key=mac_address."|".ipv6_address
| stats min(_time) as first_seen max(_time) as last_seen count as poll_count latest(state) as ndp_state latest(host) as switch latest(interface) as port by mac_address, ipv6_address
| eval first_seen=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| eval duration_hours=round((last_seen_epoch - first_seen_epoch) / 3600, 1)
| sort mac_address, -last_seen
```

## Visualization

(1) Single-value: total unique MAC-to-IPv6 bindings in the retention window. (2) Table: historical NDP entries — MAC, IPv6 address, first seen, last seen, duration, switch, port. (3) Timechart: NDP entries over time per switch — flat-line drops indicate polling failures. (4) Forensic lookup panel: search by IPv6 address or MAC to retrieve the full binding history.

## Known False Positives

**NDP cache flush on router reload.** When a router reboots, its NDP cache is empty. The first few polls after a reload will show zero entries for that device, which may look like a data gap. This is expected — entries will repopulate as devices on the attached subnets communicate.

**Stale entries persisting.** NDP caches can retain STALE entries for hours after the device has left the network (depending on platform gc_thresh configuration). The historical record correctly shows the binding was observed, but the device may have disconnected at some point between the last REACHABLE observation and the final STALE poll.

**Virtual router interfaces.** VRRP/HSRP virtual addresses appear in the NDP cache of the active router with the virtual MAC (e.g., 0000.5e00.0101 for VRRP). These are infrastructure bindings, not endpoint devices.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.4 — NDP cache logging recommendation)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 4293 — MIB for IP (ipv6NetToMediaTable — SNMP MIB for NDP cache)](https://www.rfc-editor.org/rfc/rfc4293)
- [Splunk Connect for SNMP — SC4SNMP deployment guide](https://splunk.github.io/splunk-connect-for-snmp/)
