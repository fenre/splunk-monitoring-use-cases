<!-- AUTO-GENERATED from UC-5.20.74.json — DO NOT EDIT -->

---
id: "5.20.74"
title: "NDP Exhaustion (NS Flood) DDoS Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.74 · NDP Exhaustion (NS Flood) DDoS Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*Our building directory has space for a certain number of names. If someone keeps sending letters to fake apartment numbers that don't exist, the building manager has to look up each one — 'Does this person live here? No? Does THIS person live here? No?' — until the directory fills up with all these 'looking for...' entries. Eventually, when a real letter arrives, the building manager says 'sorry, my directory is full, I can't look up anyone new.' We watch the directory to see if it's filling up with fake lookups.*

---

## Description

Detects NDP exhaustion denial-of-service attacks where an attacker floods a router with traffic destined for non-existent IPv6 addresses within a /64 subnet. Each non-existent destination forces the router to create an INCOMPLETE NDP cache entry. When the cache fills, the router cannot resolve any new legitimate addresses — causing a denial of service for all hosts on the subnet. This attack is unique to IPv6 (no direct IPv4 equivalent) and is documented in RFC 6583.

## Value

NDP exhaustion is a trivial attack to launch (send packets to random addresses in a /64) but devastating in impact (all IPv6 connectivity through the router stops). The attack can be launched from anywhere that can route packets to the target subnet — it does not require local access. Without detection, the router simply stops forwarding IPv6 traffic with no clear indication of why. Early detection of NDP cache filling enables response before the router is completely saturated.

## Implementation

Monitor NDP cache utilisation via SNMP or syslog. Detect spikes in INCOMPLETE entries. Monitor NDP resolution failure rates. Alert on NDP cache resource exhaustion events. Correlate with Destination Guard events.

## Detailed Implementation

### Prerequisites
- NDP cache metrics available via SNMP polling or syslog.
- Knowledge of each router's NDP cache maximum capacity.
- Destination Guard deployed where possible (see UC-5.20.34) as primary mitigation.

### Step 1 — Configure data collection

**Cisco IOS-XE — NDP cache limits and monitoring:**
```
! Set NDP cache limits per interface (RFC 6583 recommendation)
interface Vlan100
 ipv6 nd cache expire 300
 ipv6 nd cache interface-limit 8192
```

**SNMP polling for NDP cache size:**
Poll `ipv6NetToMediaTable` (RFC 4293) entries:
```yaml
# SC4SNMP profile
profile: ipv6_ndp_cache
frequency: 60
varBinds:
  - ['1.3.6.1.2.1.55.1.12.1']  # ipv6NetToMediaTable
```

**Scripted input for NDP cache stats:**
```
[script]
interval = 60
index = network
sourcetype = cisco:ios:ndp_cache
script = /opt/splunk/bin/scripts/poll_ndp_cache.sh
# Script runs: show ipv6 neighbors statistics
```

Output example:
```
ICMPv6 ND Statistics
  Rcvd: 12345 NS, 11000 NA, 500 RS, 450 RA
  Sent: 11000 NS, 12345 NA, 2 RS, 450 RA
  NDP cache: 4500/8192 entries (54.9%)
  INCOMPLETE: 150, REACH: 3000, STALE: 1300, DELAY: 50
```

**Verification:**
```spl
index=network (sourcetype="cisco:ios" "%IPV6" "%ND" OR sourcetype="cisco:ios:ndp_cache") earliest=-1h
| stats count by host, sourcetype
```

### Step 2 — Create the search and alert

**NDP cache utilisation monitoring:**
```spl
index=network sourcetype="cisco:ios:ndp_cache" earliest=-15m
| rex field=_raw "NDP cache:\s*(?<current>\d+)/(?<maximum>\d+)"
| eval utilisation=round(tonumber(current) / tonumber(maximum) * 100, 1)
| eval status=case(
    utilisation > 90, "CRITICAL — NDP cache nearly full: " . current . "/" . maximum,
    utilisation > 70, "WARNING — NDP cache elevated: " . current . "/" . maximum,
    1=1, "OK")
| where status != "OK"
| table _time, host, current, maximum, utilisation, status
```

**INCOMPLETE entry spike (attack indicator):**
```spl
index=network sourcetype="cisco:ios:ndp_cache" earliest=-15m
| rex field=_raw "INCOMPLETE:\s*(?<incomplete>\d+)"
| eval incomplete=tonumber(incomplete)
| where incomplete > 500
| eval alert="NDP exhaustion attack likely: " . incomplete . " INCOMPLETE entries on " . host . " — traffic being sent to " . incomplete . " non-existent IPv6 addresses"
| table _time, host, incomplete, alert
```
A sustained count of >500 INCOMPLETE entries is abnormal — legitimate networks typically have fewer than 50.

**Attack source identification via NetFlow:**
```spl
index=network sourcetype="netflow" earliest=-15m
| eval dest=coalesce(destinationIPv6Address, dest)
| where match(dest, ":")
| rex field=dest "(?<dest_prefix>[0-9a-fA-F:]+:)[0-9a-fA-F]+$"
| stats dc(dest) as unique_dests count as pkts by sourceIPv6Address, dest_prefix
| where unique_dests > 200
| eval attack_source="NDP exhaustion source: " . sourceIPv6Address . " → " . unique_dests . " unique destinations in " . dest_prefix . "/64"
| sort -unique_dests
```

### Step 3 — Validate
(a) **NDP cache baseline.** Measure normal INCOMPLETE entry count on each router. Typical: 10-50 on a /64 with 200 active hosts.

(b) **Exhaustion simulation.** Use `thc-ipv6 flood_router6` or equivalent on a test network. Verify the alert fires before the cache is completely full.

(c) **Destination Guard effectiveness.** On a router with Destination Guard enabled, verify the attack traffic is blocked with `PAK_DROP` events and the NDP cache does not fill.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Exhaustion"):
- Row 1 — Gauges: NDP cache utilisation per router.
- Row 2 — Timechart: INCOMPLETE entry count per router over 24 hours.
- Row 3 — Alert table: attack indicators (high INCOMPLETE counts, resource exhaustion events).
- Row 4 — Source identification: top senders to non-existent IPv6 destinations.

**Scheduling:** NDP cache utilisation every 1 minute. INCOMPLETE spike every 1 minute. Source identification every 5 minutes.

**Runbook:**
1. NDP cache >90%: IMMEDIATE — apply per-interface NDP entry limits if not already configured. Enable Destination Guard. Identify and block the attack source.
2. High INCOMPLETE count: identify the target prefix and source via NetFlow. Apply ACL to block the attack source. Consider reducing NDP cache entry timeout.
3. Post-attack: clear the NDP cache (`clear ipv6 neighbors`) to remove stale INCOMPLETE entries. Monitor for re-attack.

### Step 5 — Troubleshooting

- **NDP cache vs ARP cache capacity** — IPv6 NDP cache is separate from the ARP table. Some platforms share memory between ARP and NDP. Verify the NDP cache limit is sufficient for the subnet size.

- **Rate limiting NDP** — Configure `ipv6 nd ns-interval` and rate-limit INCOMPLETE entries per RFC 6583. Aggressive rate limiting may delay legitimate NDP resolution.

- **Destination Guard caveats** — Destination Guard only works for traffic forwarded by the switch/router. Traffic originating from hosts on the same VLAN (same-subnet, layer-2) does not pass through the router and is not protected by Destination Guard.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%IPV6-4-NORESOURCE" OR "%IPV6_ND-3-RESOLVE" OR "%SISF-4-PAK_DROP" AND "DG") earliest=-15m
| eval indicator=case(
    match(_raw, "NORESOURCE"), "NDP cache exhausted — cannot create new entries",
    match(_raw, "RESOLVE") AND match(_raw, "fail"), "NDP resolution failure — address not on link",
    match(_raw, "DG"), "Destination Guard blocked traffic to unknown host",
    1=1, "NDP issue")
| stats count as events by host, indicator
| eval severity=case(
    match(indicator, "exhausted") AND events > 10, "CRITICAL — NDP table FULL on " . host,
    match(indicator, "Destination Guard") AND events > 100, "HIGH — significant NDP exhaustion attempt blocked by Destination Guard on " . host,
    events > 50, "MEDIUM — elevated NDP failures on " . host,
    1=1, "LOW")
| sort -events
```

## Visualization

(1) Gauge: NDP cache utilisation per router. (2) Timechart: INCOMPLETE NDP entries over time. (3) Alert panel: NDP exhaustion indicators. (4) Table: top sources sending traffic to non-existent IPv6 destinations.

## Known False Positives

**Legitimate traffic to decommissioned hosts.** When a server is decommissioned but DNS records remain, clients continue to send traffic to its IPv6 address. Each attempt creates an INCOMPLETE NDP entry. Clean up stale DNS records.

**Rapid VM provisioning/deprovisioning.** In environments where VMs are created and destroyed rapidly (CI/CD pipelines, auto-scaling), traffic to recently-destroyed VMs creates INCOMPLETE entries. This is normal churn in dynamic environments.

**Network scanning tools.** Legitimate vulnerability scanners that scan IPv6 subnets will trigger NDP entries for each scanned address. Schedule scans during maintenance windows and exclude scanner sources.

## References

- [RFC 6583 — Operational Neighbor Discovery Problems (NDP exhaustion attack documentation)](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.4 — NDP DoS mitigation)](https://www.rfc-editor.org/rfc/rfc9099)
