<!-- AUTO-GENERATED from UC-5.20.24.json — DO NOT EDIT -->

---
id: "5.20.24"
title: "NDP Cache State Distribution Trending"
status: "verified"
criticality: "medium"
splunkPillar: "ITSI"
---

# UC-5.20.24 · NDP Cache State Distribution Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*Every router keeps a list of its neighbours and whether they are currently at home (REACHABLE), recently seen but maybe out (STALE), or called but never answered (INCOMPLETE). We watch the balance of these categories — if too many neighbours are listed as 'never answered,' something is wrong, either the neighbours are gone or someone is sending fake calls to overwhelm the router.*

---

## Description

Tracks the distribution of NDP cache entry states (INCOMPLETE, REACHABLE, STALE, DELAY, PROBE) across all Layer 3 interfaces over time. The state distribution is a powerful health indicator: a healthy interface shows 40-60% REACHABLE (active hosts), 30-50% STALE (recently active), <5% INCOMPLETE, and <5% PROBE. A sudden spike in INCOMPLETE entries indicates either a scanning attack (UC-5.20.23) or a connectivity problem where hosts are unreachable. A spike in PROBE entries indicates that the router is having difficulty confirming reachability of known hosts — possibly due to congestion, host failure, or firewall filtering of unicast NS/NA. This use case provides the NDP health 'vital signs' that complement cache size monitoring (UC-5.20.19) and poisoning detection (UC-5.20.20).

## Value

NDP cache state distribution is the most sensitive indicator of IPv6 network health at the Layer 2/3 boundary. Unlike simple cache size monitoring (which only tells you how many entries exist), state distribution tells you the quality of those entries. An interface with 1000 entries might look healthy by size, but if 80% are INCOMPLETE, the router is spending CPU on unanswered neighbor solicitations and hosts are not reachable. Conversely, a high STALE percentage is normal and indicates the garbage collector is working correctly. Trending state distribution over time reveals operational patterns: daily REACHABLE peaks during business hours, gradual STALE increase overnight as hosts go idle, and transient PROBE spikes during network maintenance.

## Implementation

Poll NDP cache entries with state information from `ipv6NetToMediaTable`. Aggregate by state per interface. Calculate percentages and trend over time. Alert on anomalous state distributions: >10% INCOMPLETE, >20% PROBE, or a sudden shift from predominantly REACHABLE to predominantly STALE (mass disconnection).

## Detailed Implementation

### Prerequisites
- NDP cache polling (UC-5.20.16) must be operational and include the `state` field from `ipv6NetToMediaState`.
- The SNMP response must include the state column. Verify: `snmpwalk -v2c -c <community> <device> 1.3.6.1.2.1.55.1.12.1.4` — this is the `ipv6NetToMediaState` column (values: 1=reachable, 2=stale, 3=delay, 4=probe, 5=invalid, 6=unknown, 7=incomplete).
- Baseline data: collect 7 days of state distribution data before setting thresholds.

### Step 1 — Configure data collection

Follow UC-5.20.16 for NDP cache polling. The `ipv6NetToMediaState` value is included in each `ipv6NetToMediaTable` row and should be extracted as the `state` field. If using SC4SNMP, the state is automatically included in the SNMP walk response.

**For CLI-based collection:**
Cisco: `show ipv6 neighbors` includes the state column:
```
IPv6 Address                              Age Link-layer Addr State Interface
2001:db8:100::1                             0 aabb.ccdd.eeff  REACH Vlan100
2001:db8:100::2                             5 1122.3344.5566  STALE Vlan100
FE80::1                                     - aabb.ccdd.eeff  REACH Vlan100
```
Parse the `State` column (REACH, STALE, INCMP, DELAY, PROBE) as the `state` field.

**Verification:**
```spl
index=network sourcetype="ndp:cache" earliest=-15m
| stats count by state
```
Expected: predominantly REACHABLE and STALE during business hours.

### Step 2 — Create the search and alert

**Primary search — state distribution per interface:**
```spl
index=network sourcetype="ndp:cache" earliest=-1h
| eval state=upper(state)
| eval state=case(
    match(state, "REACH"), "REACHABLE",
    match(state, "STALE"), "STALE",
    match(state, "INCMP|INCOMPLETE"), "INCOMPLETE",
    match(state, "DELAY"), "DELAY",
    match(state, "PROBE"), "PROBE",
    1=1, state)
| stats count as entries by host, interface, state
| eventstats sum(entries) as total by host, interface
| eval pct=round(entries / total * 100, 1)
| eval anomaly=case(
    state="INCOMPLETE" AND pct > 10, "HIGH INCOMPLETE — possible scanning or exhaustion",
    state="PROBE" AND pct > 20, "HIGH PROBE — reachability problems",
    state="REACHABLE" AND pct < 10 AND total > 50, "LOW REACHABLE — possible mass disconnection",
    1=1, "")
| where isnotnull(anomaly) AND anomaly!=""
| table host, interface, state, entries, pct, anomaly
```

**Trending search — state distribution over time:**
```spl
index=network sourcetype="ndp:cache" earliest=-24h
| eval state=upper(state)
| eval state=case(
    match(state, "REACH"), "REACHABLE",
    match(state, "STALE"), "STALE",
    match(state, "INCMP|INCOMPLETE"), "INCOMPLETE",
    1=1, "OTHER")
| bin _time span=30m
| stats count as entries by _time, host, state
| timechart span=30m sum(entries) by state
```

**Alert — anomalous INCOMPLETE spike:**
```spl
index=network sourcetype="ndp:cache" earliest=-15m
| eval state=upper(state)
| eval is_incomplete=if(match(state, "INCMP|INCOMPLETE"), 1, 0)
| stats sum(is_incomplete) as incomplete_count count as total by host, interface
| eval incomplete_pct=round(incomplete_count / total * 100, 1)
| where incomplete_pct > 10 AND incomplete_count > 20
```
Trigger: any interface with >10% INCOMPLETE AND >20 INCOMPLETE entries. Priority: HIGH.

### Step 3 — Validate
(a) **Expected daily pattern.** Over 24 hours, the state distribution should follow the business day: REACHABLE dominant during work hours, STALE dominant overnight. Verify the stacked area chart shows this pattern.

(b) **Simulated scanning.** On a lab network, run `nmap -6 --unprivileged -sn 2001:db8:lab::/120` (scanning 256 addresses in a /120). The NDP cache should show a spike in INCOMPLETE entries on the router's interface. Verify the alert fires.

(c) **Baseline comparison.** After 7 days of data, establish: average REACHABLE% during business hours (expected: 40-60%), average STALE% overnight (expected: 60-90%), and maximum normal INCOMPLETE% (expected: <5%).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Cache Health"):
- Row 1 — Stacked area chart: state distribution over 24 hours for the selected interface. Colour coding: green=REACHABLE, blue=STALE, yellow=DELAY, orange=PROBE, red=INCOMPLETE.
- Row 2 — Table: interfaces with anomalous state distributions, with specific anomaly descriptions.
- Row 3 — Single-value panels: total INCOMPLETE entries (network-wide), interfaces with >10% INCOMPLETE.
- Row 4 — Drilldown: select an interface to see individual entries and their states.

**Scheduling:** State distribution snapshot every 15 minutes. INCOMPLETE anomaly alert every 5 minutes.

**Runbook:**
1. HIGH INCOMPLETE alert:
   a. Check UC-5.20.23 — is the NS rate also elevated? If yes, probable NDP exhaustion attack.
   b. Check if there is a legitimate reason: network scan, new VLAN deployment, or host outage.
   c. If attack: identify the scanning source, block it, clear INCOMPLETE entries.
2. HIGH PROBE alert:
   a. Hosts are known but not confirming reachability. Check: are the hosts powered on? Is there a Layer 2 issue (STP loop, port security block)?
   b. Check if a firewall is blocking unicast NS/NA between the router and the hosts.
3. LOW REACHABLE alert:
   a. Mass disconnection — check if a power outage or switch failure has disconnected many hosts simultaneously.

### Step 5 — Troubleshooting

- **State column not in SNMP response** — Some older firmware versions may not include `ipv6NetToMediaState` in the walk. Verify: `snmpwalk -v2c -c <community> <device> 1.3.6.1.2.1.55.1.12.1.4`. If empty, use CLI-based collection and parse the state from `show ipv6 neighbors`.

- **All entries show as REACHABLE** — Some platforms report all entries as REACHABLE in the SNMP MIB even when they are STALE or PROBE. This is a vendor MIB implementation bug. Use CLI output for accurate state reporting on affected platforms.

- **INCOMPLETE entries expire too fast to poll** — INCOMPLETE entries have a very short lifetime (3 seconds on Cisco, ~30 seconds on Linux). If your poll interval is 5 minutes, most INCOMPLETE entries will have expired before the next poll. To capture INCOMPLETE counts during attacks, use 30-second polling or rely on the NS rate counter (UC-5.20.23) as a proxy.

## SPL

```spl
index=network sourcetype="ndp:cache" earliest=-1h
| stats count as entries by host, interface, state
| eventstats sum(entries) as total_entries by host, interface
| eval pct=round(entries / total_entries * 100, 1)
| chart values(pct) as pct by host, state
| rename INCOMPLETE as incomplete_pct, REACHABLE as reachable_pct, STALE as stale_pct, DELAY as delay_pct, PROBE as probe_pct
```

## Visualization

(1) Stacked area chart: NDP state distribution over time per interface — the dominant colour should be REACHABLE during business hours and STALE overnight. (2) Table: per-interface state breakdown with percentages and anomaly flags. (3) Single-value: interfaces with anomalous INCOMPLETE or PROBE percentages. (4) Timechart: INCOMPLETE count trending — correlate with UC-5.20.23 NS rate for attack detection.

## Known False Positives

**Overnight STALE dominance.** When users leave the office, their devices stop communicating. NDP entries transition from REACHABLE to STALE (after 30 seconds of inactivity). Overnight, 80-90% STALE is normal and expected. This is not an anomaly — it reflects the daily usage pattern.

**Post-reboot transient INCOMPLETE spike.** After a router reboot, the NDP cache is empty. As hosts on the VLAN communicate, each triggers an NS/NA exchange, and the cache briefly has a high proportion of entries transitioning through INCOMPLETE to REACHABLE. This transient lasts 1-5 minutes.

**Scheduled maintenance windows.** During switch/router upgrades, hosts may become temporarily unreachable, causing entries to move to PROBE and then be deleted. Correlate with change management events.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (§7.3.2 — Neighbor Cache Entry States: INCOMPLETE, REACHABLE, STALE, DELAY, PROBE)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 6583 — Operational Neighbor Discovery Problems (NDP cache state behaviour under attack conditions)](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 4293 — MIB for IP (ipv6NetToMediaState — SNMP MIB for NDP cache entry state)](https://www.rfc-editor.org/rfc/rfc4293)
