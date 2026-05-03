<!-- AUTO-GENERATED from UC-5.20.6.json — DO NOT EDIT -->

---
id: "5.20.6"
title: "IPv6 Interface Counter Parity"
status: "verified"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.20.6 · IPv6 Interface Counter Parity

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We compare how much old-style and new-style internet traffic each network port carries, to make sure the new-style traffic is actually flowing where it should be and isn't being silently blocked somewhere.*

---

## Description

Compares per-interface IPv4 and IPv6 traffic counters from RFC 4293 ipIfStatsTable via SNMP, detecting interfaces where IPv6 counters are unexpectedly zero (IPv6 not working despite being configured), where IPv6 discard rates significantly exceed IPv4 (indicating IPv6-specific ACLs, CoPP, or routing issues), or where IPv6 traffic is present on interfaces where it shouldn't be. RFC 9099 §2.6.1.3 specifically calls out per-interface IPv6 counter monitoring as an operational necessity because aggregate counters mask per-link issues.

## Value

Interface-level counter parity catches problems that traffic ratio monitoring (UC-5.20.1) cannot detect. A campus network may show 30% IPv6 overall, but if one distribution switch has zero IPv6 counters on its uplinks, that entire building has no IPv6 connectivity — masked by healthy traffic from other buildings. Similarly, high IPv6 discard rates on a single interface may indicate an ACL misconfiguration that blocks IPv6 only on that link, while IPv4 works fine and nobody notices until a dual-stack application breaks for users in that zone.

## Implementation

Configure SNMP polling of `ipIfStatsTable` (RFC 4293) on all Layer 3 devices. This MIB provides separate counters for IPv4 (ipVersion=1) and IPv6 (ipVersion=2) per interface, including bytes, packets, discards, and forwarded counts. Poll every 5 minutes and compare the IPv6 counters to IPv4 counters on each interface. Alert when IPv6 counters are zero on an interface where IPv6 is configured, or when IPv6 discards exceed IPv4 discards by more than 10x.

## Detailed Implementation

### Prerequisites
- SNMP v2c or v3 configured on all Layer 3 network devices with access from the Splunk polling host (Heavy Forwarder running SC4SNMP, or Telegraf agent).
- The device must support RFC 4293 `ipIfStatsTable`. Most modern platforms do (Cisco IOS-XE 16.x+, NX-OS 7.x+, Juniper Junos 15.1+, Arista EOS 4.20+). Verify with: `snmpwalk -v2c -c <community> <device_ip> 1.3.6.1.2.1.4.31.3.1.1` — this should return entries indexed by IP version (1 or 2) and ifIndex.
- Prefer 64-bit high-capacity (HC) counters: `ipIfStatsHCInOctets` (OID .6) and `ipIfStatsHCOutOctets` (OID .10). 32-bit counters wrap too quickly on Gigabit+ links.
- An interface-to-name mapping is helpful. Poll `ifDescr` (1.3.6.1.2.1.2.2.1.2) alongside ipIfStatsTable to get human-readable interface names.

### Step 1 — Configure data collection

**Using SC4SNMP (recommended):**

Add the `ipIfStatsTable` to your SC4SNMP polling profile:
```yaml
# SC4SNMP profiles.yaml
profile_ipv6_counters:
  frequency: 300
  varBinds:
    - ['1.3.6.1.2.1.4.31.3']       # ipIfStatsTable (full table)
    - ['1.3.6.1.2.1.2.2.1.2']      # ifDescr for interface names
```

Map the profile to your device inventory:
```yaml
# SC4SNMP inventory.yaml
- address: 10.1.1.1
  port: 161
  version: 2c
  community: <community_string>
  profiles:
    - profile_ipv6_counters
```

SC4SNMP sends results to Splunk HEC as `sourcetype=sc4snmp:event` or `sc4snmp:metric`. Configure the HEC token to route to `index=network`.

**Using Telegraf (alternative):**
```toml
[[inputs.snmp]]
  agents = ["udp://10.1.1.1:161"]
  version = 2
  community = "<community_string>"
  interval = "300s"

  [[inputs.snmp.table]]
    name = "ipIfStats"
    oid = "1.3.6.1.2.1.4.31.3"
    [[inputs.snmp.table.field]]
      oid = "1.3.6.1.2.1.4.31.3.1.1"
      name = "ipVersion"
      is_tag = true
    [[inputs.snmp.table.field]]
      oid = "1.3.6.1.2.1.4.31.3.1.6"
      name = "HCInOctets"
    [[inputs.snmp.table.field]]
      oid = "1.3.6.1.2.1.4.31.3.1.10"
      name = "HCOutOctets"
    [[inputs.snmp.table.field]]
      oid = "1.3.6.1.2.1.4.31.3.1.7"
      name = "InDiscards"
    [[inputs.snmp.table.field]]
      oid = "1.3.6.1.2.1.4.31.3.1.11"
      name = "OutDiscards"
```

Verification:
```spl
index=network sourcetype=sc4snmp:* ipIfStatsIPVersion=* earliest=-15m
| stats count by host, ipIfStatsIPVersion
```
Expect two rows per host: one for ipVersion=1 (IPv4) and one for ipVersion=2 (IPv6). If only ipVersion=1 appears, the device may not support IPv6 counters, or IPv6 is not configured on any interface.

### Step 2 — Create the search and alert

**Primary search — per-interface IPv4 vs IPv6 counter comparison:**
```spl
index=network sourcetype="sc4snmp:*" ipIfStatsIPVersion=* earliest=-1h
| eval ip_version=case(ipIfStatsIPVersion="1", "IPv4", ipIfStatsIPVersion="2", "IPv6", 1==1, "Unknown")
| stats latest(ipIfStatsHCInOctets) as in_bytes latest(ipIfStatsHCOutOctets) as out_bytes latest(ipIfStatsInDiscards) as in_discards latest(ipIfStatsOutDiscards) as out_discards by host, ifIndex, ip_version
| eval total_bytes=in_bytes + out_bytes
| eval total_discards=in_discards + out_discards
| chart sum(total_bytes) as bytes sum(total_discards) as discards over host by ip_version
| eval ipv6_bytes_pct=if(isnum('bytes.IPv6') AND isnum('bytes.IPv4') AND ('bytes.IPv4' + 'bytes.IPv6') > 0, round('bytes.IPv6' / ('bytes.IPv4' + 'bytes.IPv6') * 100, 1), 0)
| eval discard_ratio=if(isnum('discards.IPv4') AND 'discards.IPv4' > 0, round('discards.IPv6' / 'discards.IPv4', 2), "N/A")
| sort -discard_ratio
```

**Understanding this SPL:**
- `ipIfStatsIPVersion` is the MIB index that separates IPv4 (1) and IPv6 (2) counters. Every counter in the table exists twice — once for each IP version.
- `latest()` takes the most recent counter value. For rate-based analysis, use `| streamstats current=f last(in_bytes) as prev_in_bytes by host, ifIndex, ip_version | eval in_rate=in_bytes-prev_in_bytes`.
- `discard_ratio` highlights interfaces where IPv6 drops are disproportionately higher than IPv4 drops, suggesting IPv6-specific filtering issues.

**Alert — IPv6 counters zero on IPv6-enabled interface:**
```spl
index=network sourcetype="sc4snmp:*" ipIfStatsIPVersion="2" earliest=-1h
| stats latest(ipIfStatsHCInOctets) as ipv6_in_bytes latest(ipIfStatsHCOutOctets) as ipv6_out_bytes by host, ifIndex
| where ipv6_in_bytes=0 AND ipv6_out_bytes=0
| lookup ipv6_enabled_interfaces host, ifIndex OUTPUT ipv6_expected
| where ipv6_expected="true"
| table host, ifIndex
```
Trigger: any interface tagged as IPv6-expected with zero IPv6 traffic. Requires an `ipv6_enabled_interfaces` lookup (CSV or KV store) that maps which interfaces should have IPv6 traffic.

### Step 3 — Validate
(a) **CLI comparison:** On a Cisco IOS-XE router: `show ipv6 traffic`. Compare `IPv6 statistics: ... Rcvd: ... total` to the SNMP counter value for that device.

(b) **Correlation with flow data:** Compare the per-device IPv6 byte percentage from this UC (SNMP-based) with the flow-based ratio from UC-5.20.1. They should be within 5-10 percentage points. Large discrepancies indicate flow export or SNMP polling issues.

(c) **Counter rate validation:** Plot `| timechart span=5m max(ipIfStatsHCInOctets) by host, ifIndex, ip_version` for a known-busy interface. The curve should show smooth growth, not flat lines (stale data) or sawtooth patterns (counter resets).

### Step 4 — Operationalize

**Dashboard** (panel on "IPv6 Address Hygiene" or standalone "IPv6 Interface Health"):
- Row 1 — Table: per-device IPv6 byte percentage and discard ratio. Colour-code: green (IPv6 > 10%, discards within norm), yellow (IPv6 < 5%), red (IPv6 = 0% on expected interfaces).
- Row 2 — Interface-level detail: click a device to see per-interface breakdown.

**Scheduling:** Daily report for compliance tracking. Alert (zero-counter check) every hour.

**Runbook** (owner: Network Engineering):
1. Zero IPv6 counters on expected interface: check `show ipv6 interface <intf>` — is IPv6 configured? Is the address link-local only or also global? Check upstream device for RA suppression.
2. High IPv6 discard ratio: check `show ipv6 access-list` and CoPP policy applied to that interface. A common cause is an IPv6 ACL that blocks legitimate traffic (e.g., ICMPv6 deny — see UC-5.20.37).

### Step 5 — Troubleshooting

- **ipIfStatsTable not available** — Older platforms may not implement RFC 4293. Fallback to `ipSystemStatsTable` (1.3.6.1.2.1.4.31.1) for system-wide (not per-interface) IPv4/IPv6 counters. Less granular but still useful.

- **Only ipVersion=1 returned** — IPv6 is not configured on any interface of that device, OR the SNMP MIB implementation only populates IPv6 entries when IPv6 is active. Configure IPv6 on at least one interface and re-poll.

- **Counter values don't change** — The device may not update ipIfStatsTable for IPv6 traffic. This is a known limitation on some Cisco NX-OS linecards and some Juniper MX FPCs. Check platform-specific documentation for MIB support status.

- **HC (64-bit) counters unavailable** — Use the 32-bit counterparts (`ipIfStatsInOctets`, OID .2) but be aware of wraparound on 10G+ links. If your poll interval is 300s, 32-bit counters can wrap at rates above ~115 Mbps, producing negative deltas in rate calculations.

## SPL

```spl
index=network sourcetype="snmp:ipIfStatsTable" earliest=-1h
| eval ip_version=case(ipIfStatsIPVersion=1, "IPv4", ipIfStatsIPVersion=2, "IPv6", 1==1, "Unknown")
| stats latest(ipIfStatsHCInOctets) as in_bytes latest(ipIfStatsHCOutOctets) as out_bytes latest(ipIfStatsInDiscards) as in_discards latest(ipIfStatsOutDiscards) as out_discards by host, ifIndex, ip_version
| eval total_bytes=in_bytes + out_bytes
| chart sum(total_bytes) as bytes sum(in_discards) as discards over host by ip_version
| eval ipv6_pct=round('IPv6' / ('IPv4' + 'IPv6') * 100, 1)
| eval discard_delta=abs('IPv6' - 'IPv4')
| sort -discard_delta
```

## Visualization

(1) Table: host, interface, IPv4 bytes, IPv6 bytes, IPv6 percentage, IPv4 discards, IPv6 discards — sorted by interfaces with zero IPv6 bytes first. (2) Trellis sparklines: per-interface IPv6 byte rate over 24h — flat lines at zero are the problem interfaces. (3) Scatter plot: IPv4 discard rate vs IPv6 discard rate per interface — outliers above the diagonal indicate IPv6-specific packet drops.

## Known False Positives

**Interfaces with IPv4 only by design.** Management interfaces, out-of-band management networks, and legacy WAN links may intentionally carry only IPv4. Zero IPv6 counters on these interfaces is expected. Maintain an exclusion list or tag interfaces with `ipv6_expected=true/false` in a lookup to suppress false alerts.

**Counter wraparound on 32-bit counters.** Some older platforms expose only 32-bit counters (`ipIfStatsInOctets` vs `ipIfStatsHCInOctets`). On high-speed links, 32-bit counters wrap in minutes, producing erratic ratios. Always use HC (64-bit) counters where available. Check with `snmpwalk ... 1.3.6.1.2.1.4.31.3.1.6` (HCInOctets) — if absent, the platform doesn't support 64-bit counters.

**Asymmetric routing.** If traffic ingresses via one interface (counted as IPv6 in) but egresses via a different interface, the per-interface ratios will be skewed. Aggregate to per-device totals for a more accurate parity check in networks with asymmetric routing.

## References

- [RFC 4293 — Management Information Base for the Internet Protocol (IP) — ipIfStatsTable](https://www.rfc-editor.org/rfc/rfc4293)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.3 — Per-interface counters)](https://www.rfc-editor.org/rfc/rfc9099)
- [Splunk Connect for SNMP (SC4SNMP) — MIB polling configuration](https://splunk.github.io/splunk-connect-for-snmp/)
