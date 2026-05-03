<!-- AUTO-GENERATED from UC-5.2.13.json — DO NOT EDIT -->

---
id: "5.2.13"
title: "Session Table Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.13 · Session Table Exhaustion

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We follow how full the session table is so we are not caught off guard by sudden growth, leaks, or attacks that eat connection slots.*

---

## Description

When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.

## Value

Operations teams monitor firewall session table utilization against platform limits, detecting exhaustion that causes new connections to be dropped.

## Implementation

Monitor session counts via SNMP or firewall system logs. Know your platform's session limit. Alert at 80% utilization. Investigate top session consumers by source/destination.

## Detailed Implementation

### Prerequisites
* Firewall session/system logs in `index=firewall`. Key metrics: active sessions, session table maximum, sessions created/sec. Palo Alto: `show session info`, Fortinet: `get system session status`, Cisco FTD: `show conn count`.
* Session table exhaustion: every connection through a stateful firewall creates a session entry. When the table is full, new connections are dropped. Different platforms have different limits (PA-3260: 4M sessions, FG-100F: 1.5M sessions).

### Step 1 — - Configure data collection
Verify session table data:
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)session.*(count|table|limit|full|exhaust|maximum)")
| stats count by host, sourcetype
```

### Step 2 — - Create the search and alert

**Primary search -- Session table utilization:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)session")
| eval sessions=tonumber(coalesce(session_count, active_sessions))
| eval session_max=tonumber(coalesce(session_max, max_sessions, session_limit))
| where isnotnull(sessions) AND isnotnull(session_max) AND session_max > 0
| eval session_pct=round(100*sessions/session_max, 1)
| bin _time span=5m
| stats avg(session_pct) as avg_pct max(session_pct) as max_pct avg(sessions) as avg_sessions latest(session_max) as max_limit by _time, host
| eval severity=case(max_pct > 90, "CRITICAL -- session table >90% full", max_pct > 80, "HIGH -- session table >80%", max_pct > 70, "WARNING -- session table >70%", 1==1, "OK")
| where severity != "OK"
| table _time, host, avg_sessions, max_limit, avg_pct, max_pct, severity
```

**Top session consumers:**
```spl
index=firewall earliest=-1h
| eval src=coalesce(src_ip, src)
| stats count as sessions by src, host
| sort -sessions | head 20
```

### Step 3 — - Validate
(a) Palo Alto: `show session info` -- shows "num max" and "num active".
(b) Fortinet: `get system session status` -- shows session count.
(c) Load test and verify session count increases accordingly.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Session Table"):
* Row 1 -- Gauge: "Session table utilization %" per firewall.
* Row 2 -- Session count timechart.
* Row 3 -- Top session consumers.

Alerting:
* Critical (> 90%): imminent connection drops.
* High (> 80%): capacity planning needed.

### Step 5 — - Troubleshooting

* **Session table filling rapidly** -- Check: (1) DDoS attack creating many sessions, (2) worm/malware creating outbound sessions, (3) legitimate traffic growth requiring hardware upgrade. Palo Alto: `show session all filter count yes` to count by type.

* **Reduce session count** -- (1) Lower session timeouts for UDP/ICMP, (2) enable application-based session timeout, (3) identify and mitigate scanning/attacking sources.

* **Session table full but low throughput** -- Many idle sessions consuming table space. Aggressive session timeout tuning for inactive flows. Check for half-open/orphaned sessions.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=network sourcetype="pan:system" "session table"
| append [search index=network sourcetype="pan:traffic" | stats dc(session_id) as active_sessions by dvc | eval max_sessions=coalesce(max_sessions,500000)]
| stats latest(active_sessions) as sessions, latest(max_sessions) as max by dvc
| eval utilization=round(sessions/max*100,1) | where utilization > 80
```

## Visualization

Gauge (per firewall), Line chart (session count trending), Table (top consumers).

## Known False Positives

Backups, file transfers, and internet-heavy days fill session tables; compare to capacity, not a zero baseline.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
