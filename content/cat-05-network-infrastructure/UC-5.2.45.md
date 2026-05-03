<!-- AUTO-GENERATED from UC-5.2.45.json — DO NOT EDIT -->

---
id: "5.2.45"
title: "FortiGate SD-WAN Health Check and SLA Monitoring (Fortinet)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.45 · FortiGate SD-WAN Health Check and SLA Monitoring (Fortinet)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability

*We follow software-defined wide-area health checks so a bad underlay, dead probe, or weak policy is obvious next to the rest of the site story.*

---

## Description

SD-WAN health checks (ICMP, HTTP, DNS, TCP/UDP echo) continuously score each member link against SLA targets for latency, jitter, and loss. When an SLA fails, FortiOS steers traffic to better paths—so log and metric visibility is how you catch ISP brownouts before users open tickets. Trending per-interface loss and delay also validates whether performance problems are underlay-related or application-side.

## Value

Network engineers monitor FortiGate SD-WAN health check latency, jitter, and loss against SLA thresholds, detecting WAN member failures and SLA breaches that trigger path failover.

## Implementation

Define SD-WAN SLAs and health-check servers that reflect real user paths (not only the nearest DNS). Forward `system` SD-WAN events to Splunk and confirm extracted fields with your FortiOS version—field names differ slightly across releases. Alert when SLA violations repeat for the same interface or when loss/latency step-changes correlate with carrier incidents. Cross-check with `fgt_traffic` volume shifts on the same SD-WAN zones.

## Detailed Implementation

### Prerequisites
* FortiGate SD-WAN health check logs. Data in `index=fortinet` or `index=firewall` with `sourcetype=fgt_log` or `sourcetype=fgt_event`. Key fields: `vd`, `interface`, `sla_name`, `latency`, `jitter`, `packetloss`, `status`, `member`.
* FortiGate SD-WAN: performance SLA health checks (ICMP, HTTP, DNS, TCP-echo, UDP-echo) probe each WAN member at configurable intervals. When SLA thresholds are breached, SD-WAN rules can failover traffic or load-balance across remaining healthy members. Configured under `config system sdwan`.

### Step 1 — - Configure data collection
```
# FortiGate CLI -- configure SD-WAN health check
config system sdwan
    set status enable
    config health-check
        edit "ISP1-SLA"
            set server "8.8.8.8"
            set protocol ping
            set interval 500
            set failtime 5
            set recovertime 5
            set sla-fail-log-period 10
            set sla-pass-log-period 60
            config sla
                edit 1
                    set latency-threshold 100
                    set jitter-threshold 30
                    set packetloss-threshold 2
                next
            end
        next
    end
end

# Enable SD-WAN event logging
config log setting
    set resolve-ip enable
end
```
Verify:
```spl
index=fortinet (sourcetype="fgt_log" OR sourcetype="fgt_event") earliest=-4h
| where match(subtype, "(?i)sdwan") OR match(msg, "(?i)sd-wan|health.check|sla")
| stats count by interface, status
```

### Step 2 — - Create the search and alert

**Primary search -- SD-WAN health check SLA monitoring:**
```spl
index=fortinet (sourcetype="fgt_log" OR sourcetype="fgt_event") earliest=-4h
| where match(subtype, "(?i)sdwan") OR match(msg, "(?i)sd-wan|health.check|sla")
| eval iface=coalesce(interface, member, srcintf)
| eval lat=tonumber(coalesce(latency, lat))
| eval jit=tonumber(coalesce(jitter, jit))
| eval loss=tonumber(coalesce(packetloss, pktloss, packet_loss))
| eval sla=coalesce(sla_name, sla, health_check)
| eval link_status=case(
    match(status, "(?i)down|fail|dead"), "DOWN",
    match(status, "(?i)alive|up|pass"), "UP",
    loss > 5 OR lat > 200, "DEGRADED",
    1==1, "UP")
| bin _time span=5m
| stats avg(lat) as avg_latency avg(jit) as avg_jitter avg(loss) as avg_loss latest(link_status) as status by _time, devname, iface, sla
| eval avg_latency=round(avg_latency, 1)
| eval avg_jitter=round(avg_jitter, 1)
| eval avg_loss=round(avg_loss, 2)
| eval severity=case(
    status="DOWN", "CRITICAL -- SD-WAN member DOWN",
    avg_loss > 5 OR avg_latency > 200, "WARNING -- SLA threshold breached",
    avg_loss > 2 OR avg_latency > 100 OR avg_jitter > 30, "INFO -- SLA approaching threshold",
    1==1, "OK")
| where severity != "OK"
| table _time, devname, iface, sla, avg_latency, avg_jitter, avg_loss, status, severity
| sort severity, -avg_loss
```

### Step 3 — - Validate
(a) CLI: `diagnose sys sdwan health-check` -- show current health check status.
(b) CLI: `diagnose sys sdwan member` -- check member link status and metrics.
(c) CLI: `diagnose sys sdwan service` -- verify SD-WAN rules and member priorities.

### Step 4 — - Operationalize
Dashboard ("FortiGate -- SD-WAN Health"):
* Row 1 -- Single-value: "Members UP", "Members DOWN", "SLA violations".
* Row 2 -- SD-WAN health check timechart (latency, loss, jitter per member).
* Row 3 -- SLA violation table.

Alert: Critical (SD-WAN member DOWN): traffic failover occurred, investigate WAN link.

### Step 5 — - Troubleshooting

* **SLA breach but link appears functional** -- Health check target may be unreachable (ISP blocking ICMP). Try HTTP or DNS health check instead.

* **Frequent SLA fluctuations** -- Adjust failtime/recovertime to avoid flapping: increase `failtime` to require sustained degradation before declaring failure.

* **SD-WAN not failing over** -- Check SD-WAN rules: `diagnose sys sdwan service`. Verify health check is referenced in the SD-WAN rule and members have correct priorities.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event") type="system" (subtype="sdwan" OR subtype="sd-wan" OR match(_raw, "(?i)sd-wan|sdwan"))
| eval iface=coalesce(interface, intf, sdwan_zone, link)
| eval loss_pct=coalesce(pktloss, packet_loss, loss, sdwan_loss)
| eval lat_ms=coalesce(latency, rtt, sla_latency)
| eval jitter_ms=coalesce(jitter, sdwan_jitter)
| where loss_pct > 0 OR lat_ms > 200 OR match(lower(_raw), "violated|fail|unreachable|timeout")
| timechart span=15m avg(loss_pct) as avg_loss avg(lat_ms) as avg_latency by iface
```

## Visualization

Timechart (loss/latency per member), Table (SLA violations by interface), Single value (active violated SLAs).

## Known False Positives

Wan flaps, local loop tests, and carrier work can make SLA and health log messages loud without a bad policy.

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
