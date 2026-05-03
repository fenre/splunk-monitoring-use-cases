<!-- AUTO-GENERATED from UC-5.3.9.json — DO NOT EDIT -->

---
id: "5.3.9"
title: "Connection Queue Depth (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.9 · Connection Queue Depth (F5 BIG-IP)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance

*We look at how deep connection queues get so a slow back end or a traffic spike is not hiding behind a few lucky fast replies.*

---

## Description

Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.

## Value

Application delivery teams monitor F5 BIG-IP connection queue depth by comparing client-side and server-side connection counts, detecting backend bottlenecks where new connections are backing up.

## Implementation

Monitor LTM connection queue statistics via iControl REST or SNMP. Alert when queue depth exceeds 0 persistently (>5 min). Correlate with backend pool member health.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 iControl REST or SNMP polling for connection queue statistics. Key metrics: `clientside_cur_conns`, `serverside_cur_conns`, `num_active_members`, queue depth from `oneconnect` or `connection-limit` pool statistics.

### Step 1 — - Configure data collection
Poll F5 iControl REST for pool and virtual server stats including queue metrics, or use SNMP OID `ltmVsStatusCurrSessions` (1.3.6.1.4.1.3375.2.2.10.13.2.1.2). Verify:
```spl
index=network (sourcetype="f5:bigip:api" OR sourcetype="f5:bigip:syslog") earliest=-4h
| where isnotnull(clientside_cur_conns) OR match(_raw, "(?i)(queue|connection.limit)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Connection queue depth and saturation:**
```spl
index=network (sourcetype="f5:bigip:api" OR sourcetype="f5:bigip:syslog") earliest=-4h
| eval client_conns=coalesce(clientside_cur_conns, client_connections)
| eval server_conns=coalesce(serverside_cur_conns, server_connections)
| eval vs=coalesce(virtual_server, virtual_name)
| bin _time span=5m
| stats max(client_conns) as peak_client max(server_conns) as peak_server by _time, host, vs
| eval queue_estimate=peak_client - peak_server
| eval queue_ratio=if(peak_client > 0, round(peak_server/peak_client, 2), 1)
| where queue_estimate > 50 OR queue_ratio < 0.8
| lookup f5_vip_inventory.csv virtual_server as vs OUTPUT application, tier
| eval severity=case(queue_estimate > 500, "CRITICAL -- large connection backlog", queue_estimate > 100, "HIGH", queue_ratio < 0.5, "WARNING -- backends not keeping up", 1==1, "Monitor")
| sort severity, -queue_estimate
```

### Step 3 — - Validate
(a) Check current connections: `tmsh show ltm virtual <vs> stats` -- compare clientside and serverside current connections.
(b) If clientside >> serverside, connections are queuing.
(c) Reduce pool capacity (disable members) and verify queue buildup in Splunk.

### Step 4 — - Operationalize
Dashboard ("F5 -- Connection Queues"):
* Row 1 -- Single-value: "VIPs with queue buildup", "Max queue depth", "Avg queue ratio".
* Row 2 -- Per-VIP queue analysis table.

Alerting:
* Critical (queue estimate > 500 for > 5 min): severe backend bottleneck.
* Warning (queue ratio < 0.7 for > 10 min): backends falling behind.

### Step 5 — - Troubleshooting

* **High queue but backend connections low** -- Connection limit on pool members may be throttling. Check: `tmsh list ltm pool <pool> members connection-limit`.

* **Queue builds during specific hours** -- Backend capacity insufficient for peak load. Consider auto-scaling or pre-warming backend instances.

* **OneConnect multiplexing** -- If using OneConnect profile, clientside connections will be much higher than serverside (by design -- this is connection reuse, not queuing).

## SPL

```spl
index=network sourcetype="f5:bigip:ltm"
| stats latest(curConns) as connections, latest(connqDepth) as queue_depth by virtual_server
| where queue_depth > 0 | sort -queue_depth
```

## Visualization

Line chart (queue depth over time), Table (virtual server, connections, queue), Gauge.

## Known False Positives

Flash crowds, new campaigns, and slow backends can fill queues during honest peaks.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
