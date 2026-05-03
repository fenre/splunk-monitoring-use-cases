<!-- AUTO-GENERATED from UC-5.2.11.json — DO NOT EDIT -->

---
id: "5.2.11"
title: "Firewall Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.11 · Firewall Resource Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We follow CPU, memory, and session load on the firewall so the team can add capacity or fix a hot feature before users feel slowness or drops.*

---

## Description

Session table exhaustion blocks new connections. CPU saturation degrades throughput.

## Value

Operations teams monitor firewall CPU, memory, and session table utilization, detecting resource exhaustion that causes packet drops and performance degradation.

## Implementation

Monitor via SNMP (vendor-specific MIB) or system logs. Alert on session table >80%, dataplane CPU >80%.

## Detailed Implementation

### Prerequisites
* Firewall system/performance logs. Palo Alto: `sourcetype=pan:system` (system resource events), or SNMP/API polling. Fortinet: `sourcetype=fgt_event` (performance stats). Cisco FTD: system health events. Key metrics: CPU utilization, memory utilization, session count, throughput, disk usage.
* Firewall resource exhaustion causes packet drops, increased latency, and potential outages. CPU-intensive features: SSL decryption, threat prevention, logging.

### Step 1 — - Configure data collection
**Palo Alto (CLI check):**
```
show running resource-monitor
show system resources
show session info  # session count and limit
```
Forward system events via syslog. For polling, use Palo Alto API scripted input:
```
# inputs.conf
[script:///opt/splunk/etc/apps/Splunk_TA_paloalto/bin/pan_resource.py]
interval = 300
sourcetype = pan:system:resource
index = firewall
```
Verify:
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)cpu|memory|session.*(count|limit|table)|resource|disk|dataplane|mgmtplane")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Resource utilization monitoring:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)cpu|memory|session|resource|dataplane|mgmtplane")
| eval cpu_pct=case(match(_raw, "(?i)cpu"), tonumber(coalesce(cpu_percent, cpu_usage, cpu)), 1==1, null())
| eval mem_pct=case(match(_raw, "(?i)memory|mem"), tonumber(coalesce(mem_percent, memory_usage, mem)), 1==1, null())
| eval sessions=tonumber(coalesce(session_count, active_sessions, sessions))
| eval session_limit=tonumber(coalesce(session_max, max_sessions))
| eval session_pct=if(isnotnull(sessions) AND isnotnull(session_limit) AND session_limit > 0, round(100*sessions/session_limit, 1), null())
| bin _time span=5m
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as max_cpu avg(mem_pct) as avg_mem max(mem_pct) as max_mem avg(session_pct) as avg_session_pct by _time, host
| eval severity=case(max_cpu > 90, "CRITICAL -- CPU >90%", max_mem > 90, "CRITICAL -- Memory >90%", avg_session_pct > 80, "HIGH -- Session table >80%", max_cpu > 70, "WARNING -- CPU >70%", max_mem > 70, "WARNING -- Memory >70%", 1==1, "OK")
| where severity != "OK"
| table _time, host, avg_cpu, max_cpu, avg_mem, max_mem, avg_session_pct, severity
```

### Step 3 — - Validate
(a) Palo Alto: `show running resource-monitor minute` -- compare CPU with Splunk.
(b) Fortinet: `get system performance status` -- shows CPU and memory.
(c) Compare session count: `show session info` (PA) / `get system session status` (Fortinet).

### Step 4 — - Operationalize
Dashboard ("Firewall -- Resource Utilization"):
* Row 1 -- Gauge: "CPU %", "Memory %", "Session table %".
* Row 2 -- Resource utilization timechart per firewall.

Alerting:
* Critical (CPU or Memory > 90%): performance degradation imminent.
* High (Session table > 80%): new connections may be dropped.
* Warning (CPU > 70% sustained): investigate load.

### Step 5 — - Troubleshooting

* **High CPU** -- Check: (1) threat prevention signatures causing deep inspection load, (2) SSL decryption load, (3) logging volume. Palo Alto: `show running resource-monitor` breaks down by function. Fortinet: `diag sys top` shows per-process CPU.

* **High memory** -- Check: (1) session table size, (2) NAT table, (3) ARP table. Memory leaks may require firmware update.

* **Session table filling** -- Short-lived sessions from scanning or DDoS. Consider: (1) reduce session timeout for specific apps, (2) enable SYN proxy for DoS protection, (3) increase session table size if hardware allows.

## SPL

```spl
index=firewall ("session" AND "utilization") OR ("cpu" AND "dataplane")
| timechart span=5m avg(session_utilization) as session_pct by host | where session_pct > 80
```

## Visualization

Gauge (session/CPU/memory), Line chart, Table.

## Known False Positives

Scheduled high traffic, content updates, and backup windows raise CPU and session use without a failure.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
