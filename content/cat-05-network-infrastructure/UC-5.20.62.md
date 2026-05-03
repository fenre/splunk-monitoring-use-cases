<!-- AUTO-GENERATED from UC-5.20.62.json — DO NOT EDIT -->

---
id: "5.20.62"
title: "IPv6 Firewall Session Table Utilization and Connection Rate Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.62 · IPv6 Firewall Session Table Utilization and Connection Rate Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The security gate at the building has a logbook that tracks everyone coming and going. IPv6 visitors have longer names that take up more space in the logbook, and the new system where visitors try both the old and new doors at the same time means double the entries. We watch how full the logbook is getting, because when it's completely full, no new visitors can enter — everyone gets turned away.*

---

## Description

Monitors firewall session table utilization with specific attention to IPv6 session overhead. IPv6 sessions consume more memory per entry than IPv4 due to larger addresses. In dual-stack environments with Happy Eyeballs, the connection setup rate effectively doubles as clients attempt both IPv4 and IPv6 simultaneously. Privacy extension addresses multiply the session count per host. These factors can cause session table exhaustion faster than capacity planning based on IPv4 traffic alone would predict.

## Value

Session table exhaustion is a cliff event — the firewall works perfectly until the table is full, then it starts dropping new connections. Users experience 'the network is down' symptoms while existing connections continue to work normally. Because IPv6 sessions are larger and dual-stack traffic doubles the connection rate, adding IPv6 to an existing firewall can push session table utilization over the edge without any increase in actual user count. Monitoring session table utilization proactively, with IPv6-specific capacity adjustments, prevents this surprise capacity failure.

## Implementation

Poll firewall session table metrics via SNMP, API, or syslog. Track utilization percentage over time. Alert on high utilization. Separate IPv4 and IPv6 session counts where possible to understand the IPv6 contribution.

## Detailed Implementation

### Prerequisites
- Firewall system logs or SNMP metrics that include session table utilization.
- Knowledge of each firewall's maximum session table capacity (varies by model and license).
- Understanding of the IPv4/IPv6 traffic mix to estimate IPv6 session overhead.

### Step 1 — Configure data collection

**Palo Alto — session information via syslog:**
Palo Alto includes session information in system logs. Additionally, poll via API:
```
curl -k 'https://<firewall>/api/?type=op&cmd=<show><session><info></info></session></show>&key=<api_key>'
```
Response includes: `num-active`, `num-max`, `num-tcp`, `num-udp`, `num-icmp`.

**Cisco ASA — session table metrics:**
```
show conn count
  123456 in use, 500000 most used
  xlate count 45678 in use, 200000 most used
```

**SNMP polling (generic):**
```yaml
# SC4SNMP profile for firewall session table
profile: firewall_sessions
frequency: 60
varBinds:
  - ['1.3.6.1.4.1.9.9.147.1.2.2.2.1.5.40.6']  # Cisco ASA — cfwConnectionStatValue (current sessions)
```

**Create firewall capacity lookup:**
```csv
host,model,max_sessions,max_cps
fw-01,PA-5250,4000000,720000
fw-02,ASA-5585,10000000,350000
fw-03,FG-3600E,12000000,480000
```
Upload as `firewall_capacity.csv`.

**Verification:**
```spl
index=network (sourcetype="paloalto:system" OR sourcetype="cisco:asa") "session" earliest=-24h
| stats count by host, sourcetype
```

### Step 2 — Create the search and alert

**Session table utilization alert:**
```spl
index=network (sourcetype="paloalto:system" OR sourcetype="cisco:asa" OR sourcetype="sc4snmp:metric")
  ("session" OR metric_name="firewall.active_sessions") earliest=-15m
| rex field=_raw "(?:active|current|in use)\s*:?\s*(?<active>\d+)"
| eval active=coalesce(active, metric_value)
| stats latest(active) as current_sessions by host
| lookup firewall_capacity.csv host OUTPUT max_sessions
| eval utilization=round(current_sessions / max_sessions * 100, 1)
| eval status=case(
    utilization > 95, "CRITICAL",
    utilization > 85, "HIGH",
    utilization > 70, "WARNING",
    1=1, "OK")
| where status != "OK"
```

**IPv6 session contribution analysis:**
```spl
index=network sourcetype="paloalto:traffic" earliest=-1h
| eval ip_version=if(match(src, ":") OR match(dst, ":"), "IPv6", "IPv4")
| stats count as sessions by ip_version
| eventstats sum(sessions) as total
| eval pct=round(sessions / total * 100, 1)
```

**Connection rate spike detection (CPS):**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa")
  ("session" AND ("create" OR "start" OR "conn-id")) earliest=-15m
| eval ip_version=if(match(_raw, ":"), "IPv6", "IPv4")
| timechart span=1m count as cps by ip_version
| eval total_cps=IPv4 + IPv6
```

**Growth projection:**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="firewall.active_sessions" earliest=-30d
| timechart span=1d avg(metric_value) as daily_avg by host
| predict daily_avg as predicted algorithm=LLP5 future_timespan=30
```

### Step 3 — Validate
(a) **Utilization accuracy.** Compare Splunk session count with `show session info` (Palo Alto) or `show conn count` (ASA).

(b) **IPv6 contribution.** Verify the IPv4/IPv6 session breakdown matches expected traffic patterns.

(c) **Growth projection.** Compare the 30-day projection with actual capacity. Verify the prediction algorithm tracks real growth.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Firewall Session Capacity"):
- Row 1 — Gauges: per-firewall session table utilization.
- Row 2 — Stacked timechart: IPv4 vs IPv6 active sessions over 7 days.
- Row 3 — Connection rate: CPS trending with IPv4/IPv6 breakdown.
- Row 4 — Growth projection: 30-day forecast with capacity threshold line.

**Scheduling:** Utilization alert every 5 minutes. CPS spike every 1 minute. Growth projection daily.

**Runbook:**
1. Utilization >85%: reduce session timeouts for idle connections. Enable session aging for half-open connections.
2. Utilization >95%: URGENT — add capacity (HA pair, larger model, or distribute load). Consider offloading IPv6 traffic to a dedicated path.
3. IPv6 session doubling: if Happy Eyeballs is causing session doubling, consider DNS-level IPv6 preference to reduce dual connection attempts.

### Step 5 — Troubleshooting

- **Privacy extension multiplier** — A single host with privacy extensions maintains 2-3 active IPv6 addresses simultaneously. Each address generates separate session entries. In networks with many privacy-extension-enabled hosts, the per-host session multiplier can be 3-5x compared to IPv4.

- **NDP multicast sessions** — Some firewalls create session entries for NDP multicast traffic (FF02::1, FF02::2, FF02::1:FF00:0/104). These consume session table space. Configure the firewall to handle NDP traffic without creating session entries where possible.

- **Half-open connection flood** — SYN flood attacks over IPv6 consume session table entries for half-open connections. Enable SYN cookies or SYN proxy to mitigate.

## SPL

```spl
index=network (sourcetype="paloalto:system" OR sourcetype="cisco:asa" OR sourcetype="fortinet:fortigate") earliest=-24h
  ("session" AND ("table" OR "count" OR "utilization" OR "max"))
| rex field=_raw "(?:active|current)\s*(?:sessions?|connections?)\s*:?\s*(?<active_sessions>\d+)"
| rex field=_raw "(?:max|maximum|limit)\s*(?:sessions?|connections?)\s*:?\s*(?<max_sessions>\d+)"
| eval utilization_pct=round(active_sessions / max_sessions * 100, 1)
| eval severity=case(
    utilization_pct > 95, "CRITICAL — session table nearly full",
    utilization_pct > 85, "HIGH — approaching capacity",
    utilization_pct > 70, "WARNING — monitor growth",
    1=1, "OK")
| stats latest(active_sessions) as current_sessions latest(max_sessions) as max_sessions latest(utilization_pct) as utilization latest(severity) as status by host
| sort -utilization
```

## Visualization

(1) Gauge: session table utilization per firewall. (2) Timechart: session count trending with IPv4/IPv6 breakdown. (3) Projection: session table growth forecast. (4) Alert panel: firewalls approaching capacity.

## Known False Positives

**Legitimate traffic spikes.** Black Friday, product launches, or marketing campaigns cause legitimate session count spikes. Correlate with business events.

**Long-lived connections.** WebSocket, SSH, and VPN connections persist for hours or days, accumulating in the session table. Adjust session timeouts for long-lived protocols.

**Scanning and vulnerability assessment.** Legitimate vulnerability scans create many short-lived sessions simultaneously, spiking the session count temporarily.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4.1 — firewall session table considerations)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§4.3.2 — firewall capacity planning)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
