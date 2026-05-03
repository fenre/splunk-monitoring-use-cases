<!-- AUTO-GENERATED from UC-5.2.42.json — DO NOT EDIT -->

---
id: "5.2.42"
title: "Juniper SRX Screen Counter Monitoring (Juniper SRX)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.42 · Juniper SRX Screen Counter Monitoring (Juniper SRX)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Performance

*We follow screen and flood counters on the SRX so unexpected spikes in scans and probes are easy to see next to the rest of the security story.*

---

## Description

Junos “Screen” features apply stateless, early-drop protections against floods, sweeps, malformed packets, and classic DoS patterns before sessions are fully created. Those drops often never appear in session or traffic logs, so screen telemetry is the only way to see perimeter volumetric or reconnaissance attacks. Sustained spikes in specific screen categories usually mean an active attack, a misconfigured peer, or a need to tune thresholds—not “normal” firewall noise.

## Value

Security teams monitor Juniper SRX Screen counter drops by category and zone to detect active flood attacks, port scans, and IP sweeps with early-stage stateless protection.

## Implementation

Confirm screen options are enabled on untrust-facing interfaces and that `RT_SCREEN` syslog messages (or structured equivalents) reach Splunk. For SNMP, poll platform-specific screen/attack counters if your SRX model exposes them, and chart deltas alongside syslog. Baseline each `screen_type` per site; alert on order-of-magnitude jumps or sustained elevation. Investigate source `src` clusters and coordinate with upstream ISP scrubbing if attacks are large. Map to CIM `Intrusion_Detection` where fields align.

## Detailed Implementation

### Prerequisites
* Juniper SRX Screen counter logs forwarded to Splunk. Data in `index=juniper` or `index=firewall` with `sourcetype=juniper:srx:structured` or `sourcetype=juniper:srx:screen`. Key fields: `screen_name`, `source_address`, `destination_address`, `zone_name`, `action`.
* Junos Screen features: stateless, early-drop protections applied before session lookup. Categories include: SYN flood protection, ICMP flood, UDP flood, port scan detection, IP sweep detection, land attack, ping of death, Winnuke, teardrop, and various malformed packet protections. Configured per-zone under `security screen`.

### Step 1 — - Configure data collection
```
# SRX configuration -- enable Screen protections and logging
set security screen ids-option my-screen icmp ping-death
set security screen ids-option my-screen icmp flood threshold 1000
set security screen ids-option my-screen tcp syn-flood alarm-threshold 1024
set security screen ids-option my-screen tcp syn-flood attack-threshold 1625
set security screen ids-option my-screen tcp port-scan threshold 10
set security screen ids-option my-screen ip source-route-option
set security screen ids-option my-screen ip spoofing
set security screen ids-option my-screen limit-session source-ip-based 128

# Apply to zone
set security zones security-zone untrust screen my-screen

# Enable logging
set security log stream splunk-stream category all
```
Verify:
```spl
index=juniper sourcetype="juniper:srx:*" earliest=-4h
| where match(_raw, "(?i)screen|RT_SCREEN")
| stats count by screen_name, source_address
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Screen counter event monitoring:**
```spl
index=juniper sourcetype="juniper:srx:*" earliest=-4h
| where match(_raw, "(?i)RT_SCREEN|screen") OR isnotnull(screen_name)
| eval screen=coalesce(screen_name, attack_type)
| eval src=coalesce(source_address, src_ip, src)
| eval dst=coalesce(destination_address, dest_ip, dst)
| eval zone=coalesce(zone_name, from_zone, ingress_zone)
| eval screen_category=case(
    match(screen, "(?i)syn.*flood"), "SYN Flood",
    match(screen, "(?i)icmp.*flood|ping.*flood"), "ICMP Flood",
    match(screen, "(?i)udp.*flood"), "UDP Flood",
    match(screen, "(?i)port.*scan"), "Port Scan",
    match(screen, "(?i)ip.*sweep|addr.*sweep"), "IP Sweep",
    match(screen, "(?i)land|tear|winnuke|ping.*death"), "Malformed Packet",
    match(screen, "(?i)spoof"), "IP Spoofing",
    match(screen, "(?i)session.*limit"), "Session Limit",
    1==1, "Other")
| bin _time span=5m
| stats count as drops dc(src) as unique_sources by _time, screen_category, zone
| eventstats avg(drops) as avg_drops stdev(drops) as stdev_drops by screen_category, zone
| eval z_score=if(stdev_drops > 0, round((drops - avg_drops)/stdev_drops, 2), 0)
| eval severity=case(
    screen_category="SYN Flood" AND drops > 5000, "CRITICAL -- active SYN flood attack",
    z_score > 4, "CRITICAL -- anomalous screen counter spike",
    z_score > 3 OR drops > 1000, "WARNING -- elevated screen drops",
    1==1, "OK")
| where severity != "OK"
| table _time, zone, screen_category, drops, unique_sources, z_score, severity
| sort severity, -drops
```

### Step 3 — - Validate
(a) CLI: `show security screen statistics zone untrust` -- compare counters.
(b) CLI: `show security monitoring` -- check current threat activity.
(c) Verify Screen is applied to correct zones: `show security zones`.

### Step 4 — - Operationalize
Dashboard ("Juniper SRX -- Screen Counters"):
* Row 1 -- Single-value: "Screen drops (4h)", "SYN floods detected", "Port scans detected".
* Row 2 -- Screen event timechart by category.
* Row 3 -- Top sources triggering Screen drops.

Alert: Critical (SYN flood screen drops > 5000/5min): activate DDoS mitigation.

### Step 5 — - Troubleshooting

* **SYN flood thresholds too low** -- Adjust: `set security screen ids-option my-screen tcp syn-flood alarm-threshold` and `attack-threshold` based on normal traffic patterns. Monitor with `show security screen statistics`.

* **Port scan detection too sensitive** -- Increase threshold: `set security screen ids-option my-screen tcp port-scan threshold`. Default 10 may trigger on legitimate service health checks.

* **Screen not applied to zone** -- Verify: `show security zones security-zone untrust` shows `Screen: my-screen`. Without zone binding, Screen protections are inactive.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=network (sourcetype="juniper:junos:firewall:structured" OR sourcetype="juniper:junos:firewall")
  "RT_SCREEN"
| rex field=_raw "RT_SCREEN_(?<screen_type>[A-Z0-9_]+)"
| rex field=_raw "source:\s*(?<src>\S+)"
| rex field=_raw "destination:\s*(?<dest>\S+)"
| bin _time span=5m
| stats count as screen_hits by _time host screen_type src dest
| eventstats median(screen_hits) as med by screen_type, host
| eval threshold=max(100, 5 * med)
| where screen_hits > threshold
| sort -screen_hits
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Timechart (hits by screen type), Table (top sources), Single value (total screen drops vs prior day).

## Known False Positives

Port scans, routing churn, and loud internet background radiation can set off screen counters without a real breach.

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
