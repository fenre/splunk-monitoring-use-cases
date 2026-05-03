<!-- AUTO-GENERATED from UC-5.20.23.json — DO NOT EDIT -->

---
id: "5.20.23"
title: "Neighbor Solicitation Rate Limiting and NDP Exhaustion Defence"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.23 · Neighbor Solicitation Rate Limiting and NDP Exhaustion Defence

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ITSI &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*When a router needs to deliver a message to a device on its local network, it calls out 'Are you there?' and waits for an answer. An attacker can trick the router into calling out to millions of fake addresses, tying up its phone line until it cannot reach real devices. We monitor how many unanswered calls the router is making to catch this attack early.*

---

## Description

Monitors the Neighbor Solicitation (NS) rate on Layer 3 interfaces to detect NDP exhaustion attacks (also called NDP table exhaustion or NDP scanning attacks). RFC 6583 documents this attack in detail: an attacker sends packets addressed to random IPv6 addresses within a /64 prefix. For each unknown destination, the router sends a Neighbor Solicitation (ICMPv6 Type 135) and creates an INCOMPLETE entry in its NDP cache. Since the target addresses don't exist, no Neighbor Advertisement is returned, and the INCOMPLETE entries consume NDP cache capacity until the cache is full. Once full, the router cannot resolve legitimate neighbors, causing connectivity loss for all hosts on that interface. This is the IPv6 equivalent of a broadcast storm exhausting an ARP table, but dramatically worse because the address space is 2^64 instead of 256.

## Value

NDP exhaustion is a well-documented vulnerability unique to IPv6. A single host on a /64 subnet can consume the router's entire NDP cache capacity by sending packets to random addresses within the subnet. The attack requires no special tools — a simple `ping6 -c 1 <random_address_in_prefix>` repeated thousands of times will do it. The router dutifull resolves each address with an NS, creating INCOMPLETE entries that consume memory and CPU. When the cache is full, legitimate hosts lose connectivity. RFC 6583 recommends rate-limiting outbound NS messages and implementing NDP cache limits — this use case monitors both the NS rate and the INCOMPLETE entry count to detect attacks in progress and verify that mitigations are effective.

## Implementation

Poll outbound NS counters via SNMP and calculate the per-second rate. Monitor syslog for `%IPV6_ND-3-RESOLVE_LIMIT` messages indicating the NDP resolution limit has been reached. Alert when the NS rate exceeds thresholds (>100/sec WARNING, >500/sec CRITICAL). Track INCOMPLETE entry count from NDP cache polls (UC-5.20.24).

## Detailed Implementation

### Prerequisites
- SNMP v2c/v3 polling of IPv6 interface statistics from all Layer 3 devices.
- Cisco IOS/IOS-XE NDP mitigation features configured: `ipv6 nd cache interface-limit` and `ipv6 nd resolution data-limit`.
- Baseline NS rates for each interface during normal operation (collect 7 days of data before setting thresholds).

### Step 1 — Configure data collection

**SNMP counter polling (primary):**

Poll the outbound NS counter `ipv6IfStatsOutNeighborSolicits` (OID 1.3.6.1.2.1.55.1.6.1.11) every 60 seconds:
```yaml
# SC4SNMP profiles.yaml
profile_ndp_stats:
  frequency: 60
  varBinds:
    - ['1.3.6.1.2.1.55.1.6.1.7']   # ipv6IfStatsInNeighborSolicits
    - ['1.3.6.1.2.1.55.1.6.1.11']  # ipv6IfStatsOutNeighborSolicits
    - ['1.3.6.1.2.1.55.1.6.1.8']   # ipv6IfStatsInNeighborAdvertisements
    - ['1.3.6.1.2.1.55.1.6.1.12']  # ipv6IfStatsOutNeighborAdvertisements
```
The ratio of outbound NS to inbound NA reveals the INCOMPLETE entry rate: if out_NS >> in_NA, many resolutions are failing (hosts don't exist).

**Cisco syslog (complementary signal):**

When the NDP resolution limit is reached:
```
%IPV6_ND-3-RESOLVE_LIMIT: ipv6 nd resolution limit reached on Vlan100
```
This is a CRITICAL event — the router has stopped resolving new neighbors on that interface.

Configure NDP mitigations on Cisco IOS-XE:
```
interface Vlan100
 ipv6 nd cache interface-limit 4096
 ipv6 nd resolution data-limit 256
```
The `resolution data-limit 256` limits the number of simultaneous INCOMPLETE entries to 256, preventing the full cache from being consumed by unanswered NS messages.

**On Juniper Junos:**
```
set interfaces irb unit 100 family inet6 nd-cache-limit 4096
set system nd-resolution-limit 256
```

**Verification:**
```spl
index=network sourcetype="sc4snmp" "NeighborSolicits" earliest=-15m
| stats count by host, interface
```

### Step 2 — Create the search and alert

**Primary search — NS rate calculation:**
```spl
index=network sourcetype="sc4snmp" ("OutNeighborSolicits") earliest=-10m
| eval ns_out=tonumber(value)
| sort 0 host, interface, _time
| streamstats current=f last(ns_out) as prev_ns last(_time) as prev_time by host, interface
| where isnotnull(prev_ns)
| eval time_delta=_time - prev_time
| eval ns_rate=if(time_delta > 0, round((ns_out - prev_ns) / time_delta, 1), 0)
| where ns_rate > 0
| stats latest(ns_rate) as ns_rate by host, interface
| eval severity=case(
    ns_rate > 500, "CRITICAL — probable NDP exhaustion attack",
    ns_rate > 100, "WARNING — elevated NS rate",
    ns_rate > 50, "INFO — above normal",
    1=1, "OK")
| where severity!="OK"
| sort -ns_rate
| table host, interface, ns_rate, severity
```

**NS-to-NA ratio (INCOMPLETE detection):**
```spl
index=network sourcetype="sc4snmp" ("OutNeighborSolicits" OR "InNeighborAdvertisements") earliest=-10m
| eval metric=case(
    match(metric_name, "OutNeighborSolicits"), "out_ns",
    match(metric_name, "InNeighborAdvertisements"), "in_na")
| chart latest(value) as counter by host, interface, metric
| eval incomplete_pct=if(out_ns > 0, round((1 - in_na / out_ns) * 100, 1), 0)
| where incomplete_pct > 30
| eval assessment=case(
    incomplete_pct > 80, "CRITICAL — >80% NS unanswered, probable scanning/exhaustion",
    incomplete_pct > 50, "WARNING — many resolutions failing",
    incomplete_pct > 30, "INFO — elevated failure rate")
| table host, interface, out_ns, in_na, incomplete_pct, assessment
```

**Syslog alert — resolution limit reached:**
```spl
index=network sourcetype="cisco:ios" "%IPV6_ND-3-RESOLVE_LIMIT"
| rex field=_raw "on\s+(?<interface>\S+)"
| stats count as hit_count latest(_time) as last_hit by host, interface
| eval last_hit=strftime(last_hit, "%Y-%m-%d %H:%M:%S")
```
Trigger: any result. Priority: CRITICAL. This means the NDP cache is full and new hosts cannot connect.

### Step 3 — Validate
(a) **Baseline NS rate.** On a typical access VLAN, the NS rate should be 1-10 per second during normal operation. Collect 7 days of data and establish a per-interface baseline.

(b) **Controlled exhaustion test (lab only).** From a test host on a lab VLAN, ping random addresses in the /64:
```bash
for i in $(seq 1 1000); do
  ping6 -c 1 -W 1 2001:db8:lab::$(openssl rand -hex 8 | sed 's/\(..\)/\1:/g;s/:$//') &
done
```
Observe the NS rate spike in Splunk and the `%IPV6_ND-3-RESOLVE_LIMIT` syslog event when the limit is reached.

(c) **NS-to-NA ratio validation.** On a healthy VLAN, the incomplete_pct should be <10% (most NS get NA responses). On a VLAN under attack, it should spike to >80%.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Exhaustion Defence"):
- Row 1 — Single-value: interfaces in CRITICAL state, resolution limit events (24h).
- Row 2 — Timechart: NS rate per interface over 24 hours — spikes indicate attacks or scanning.
- Row 3 — Table: interfaces with elevated NS rates, NS-to-NA ratios, and severity.
- Row 4 — Syslog events: `%IPV6_ND-3-RESOLVE_LIMIT` with affected interface and frequency.

**Scheduling:** NS rate calculation every 5 minutes. Resolution limit syslog alert in real-time.

**Runbook:**
1. CRITICAL — resolution limit reached:
   a. Identify the interface: check the syslog message for the affected VLAN.
   b. Clear INCOMPLETE entries: `clear ipv6 neighbors incomplete` on Cisco.
   c. Identify the scanning source: `show ipv6 traffic | include Neighbor Solicitation` — look for the source generating the most NS.
   d. Block the source: apply an ACL or shut the port.
   e. Long-term: reduce the /64 to a smaller subnet if possible, or deploy IPv6 Destination Guard.
2. WARNING — elevated NS rate:
   a. Check if a scheduled scan is running.
   b. Monitor the NS-to-NA ratio — if >50%, many addresses don't exist and this is likely scanning.

### Step 5 — Troubleshooting

- **NS counters not incrementing** — The SNMP OID may not be supported on older firmware. Verify: `snmpwalk -v2c -c <community> <device> 1.3.6.1.2.1.55.1.6.1.11`. If no response, use CLI-based collection: `show ipv6 traffic` and parse the NS counter.

- **Resolution limit too low** — The default `ipv6 nd resolution data-limit` on Cisco is often 256, which can be hit during legitimate large-scale deployments (e.g., 300+ hosts on a VLAN). Increase to match your actual host count + 20% headroom.

- **Destination Guard as mitigation** — Cisco IPv6 Destination Guard only resolves destinations that are in the binding table (SISF). Unknown destinations are dropped without NS, preventing the exhaustion attack entirely. Deploy where SISF is available: `ipv6 destination-guard attach-policy DG_POLICY`.

## SPL

```spl
index=network sourcetype="sc4snmp" ("ipv6IfStatsOutNeighborSolicits" OR "OutNeighborSolicits")
| eval ns_out=tonumber(value)
| stats latest(ns_out) as latest_ns earliest(ns_out) as earliest_ns max(_time) as latest_time min(_time) as earliest_time by host, interface
| eval time_delta=latest_time - earliest_time
| eval ns_rate=if(time_delta > 0, round((latest_ns - earliest_ns) / time_delta, 1), 0)
| where ns_rate > 50
| eval severity=case(
    ns_rate > 500, "CRITICAL — probable NDP exhaustion attack",
    ns_rate > 100, "WARNING — elevated NS rate",
    ns_rate > 50, "INFO — above normal",
    1=1, "OK")
| table host, interface, ns_rate, severity
```

## Visualization

(1) Timechart: outbound NS rate per interface over time — spikes indicate scanning or exhaustion attacks. (2) Table: interfaces with elevated NS rates, sorted by severity. (3) Single-value: interfaces in CRITICAL state. (4) Correlation panel: overlay NS rate spikes with NDP cache INCOMPLETE entry count — both should spike simultaneously during an attack.

## Known False Positives

**Legitimate network scanning.** Authorised vulnerability scanners (Nessus, Qualys) performing IPv6 host discovery may generate elevated NS rates as the scanner probes addresses within the /64. Coordinate scan windows with the monitoring team and suppress during scheduled scans.

**Subnet migration or renumbering.** When a new /64 is deployed and hosts begin using it, the router will NS for each new host — producing a brief spike in NS rate. This is transient and correlates with planned network changes.

**Multicast application startup.** Applications using IPv6 multicast (ff02:: groups) trigger NS for group members. This is typically low-rate and produces NA responses (not INCOMPLETE entries).

## References

- [RFC 6583 — Operational Neighbor Discovery Problems (NDP exhaustion attack description and mitigation recommendations)](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.1 — NDP security, cache exhaustion)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 4861 — Neighbor Discovery for IP version 6 (Neighbor Solicitation/Advertisement mechanics)](https://www.rfc-editor.org/rfc/rfc4861)
