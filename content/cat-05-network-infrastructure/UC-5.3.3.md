<!-- AUTO-GENERATED from UC-5.3.3.json — DO NOT EDIT -->

---
id: "5.3.3"
title: "Connection and Throughput Trending (F5 BIG-IP)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.3.3 · Connection and Throughput Trending (F5 BIG-IP)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Performance, Capacity

*We trend client counts and traffic from the appliance so a surprise spike, a quiet VIP, or a long drift is easy to see next to the same graphs in the device UI.*

---

## Description

Reveals application demand patterns. Useful for capacity planning and DDoS detection.

## Value

Application delivery teams trend F5 BIG-IP virtual server connections and throughput against capacity limits, detecting connection saturation and traffic anomalies before they impact application availability.

## Implementation

Poll F5 via SNMP or iControl REST for VIP statistics. Baseline patterns and alert on anomalies.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 iControl REST API polled for LTM statistics or SNMP data in `index=network` with `sourcetype=f5:bigip:syslog` or `sourcetype=f5:bigip:api`. Key metrics: `clientside_cur_conns`, `clientside_tot_conns`, `clientside_bytes_in`, `clientside_bytes_out`, `clientside_pkts_in`, `clientside_pkts_out` per virtual server.

### Step 1 — - Configure data collection
Poll F5 iControl REST (`/mgmt/tm/ltm/virtual/stats`) every 5 minutes via a scripted input or use SNMP polling for `ltmVirtualServStatClientCurConns` (OID 1.3.6.1.4.1.3375.2.2.10.2.3.1.12). Verify:
```spl
index=network (sourcetype="f5:bigip:api" OR sourcetype="f5:bigip:syslog") earliest=-4h
| where isnotnull(clientside_cur_conns) OR isnotnull(cur_connections)
| stats latest(clientside_cur_conns) as conns by host, virtual_server
| sort -conns
```

### Step 2 — - Create the search and alert

**Primary search -- Connection and throughput trending:**
```spl
index=network (sourcetype="f5:bigip:api" OR sourcetype="f5:bigip:syslog") earliest=-24h
| eval conns=coalesce(clientside_cur_conns, cur_connections)
| eval bytes_in=coalesce(clientside_bytes_in, bytes_in)
| eval bytes_out=coalesce(clientside_bytes_out, bytes_out)
| bin _time span=5m
| stats avg(conns) as avg_conns max(conns) as peak_conns sum(bytes_in) as total_in sum(bytes_out) as total_out by _time, host, virtual_server
| eval throughput_mbps=round((total_in + total_out)*8/(1024*1024*300), 2)
| lookup f5_vip_inventory.csv virtual_server OUTPUT application, tier, max_connections
| eval conn_util=if(isnotnull(max_connections), round(100*peak_conns/max_connections, 1), null())
| where conn_util > 70 OR peak_conns > 10000
| eval status=case(conn_util > 90, "CRITICAL", conn_util > 70, "WARNING", peak_conns > 50000, "HIGH_VOLUME", 1==1, "Monitor")
| sort -conn_util
```

**Anomaly detection (baseline comparison):**
```spl
index=network (sourcetype="f5:bigip:api" OR sourcetype="f5:bigip:syslog") earliest=-24h
| eval conns=coalesce(clientside_cur_conns, cur_connections)
| bin _time span=15m
| stats avg(conns) as avg_conns by _time, virtual_server
| eventstats avg(avg_conns) as baseline stdev(avg_conns) as std by virtual_server
| eval upper=baseline + (3*std)
| where avg_conns > upper
| eval anomaly="Connection spike: ".round(avg_conns,0)." vs baseline ".round(baseline,0)
```

### Step 3 — - Validate
(a) In tmsh: `show ltm virtual <vs> stats` -- compare current connections with Splunk.
(b) Generate load to a test VIP and verify connection count increases in Splunk.
(c) Verify throughput calculation aligns with F5 Dashboard or SNMP data.

### Step 4 — - Operationalize
Dashboard ("F5 -- Connections & Throughput"):
* Row 1 -- Single-value: "Total connections (all VIPs)", "Peak VIP", "Total throughput (Mbps)", "VIPs near capacity".
* Row 2 -- Per-VIP connection utilization table.
* Row 3 -- Connection trending timechart by top-5 VIPs.

Alerting:
* Warning (VIP connection utilization > 80%): approaching connection limit.
* Info (connection anomaly > 3 sigma from baseline): unexpected traffic spike.

### Step 5 — - Troubleshooting

* **Connection count increasing but throughput flat** -- Many idle/keep-alive connections. Check connection timeouts: `tmsh list ltm profile tcp idle-timeout`.

* **Sudden spike in connections** -- Could be: (1) DDoS, (2) application retry storm, (3) legitimate traffic event. Correlate with source IP distribution.

* **Connection limit hit** -- F5 enforces `connection-limit` per VIP. Check: `tmsh list ltm virtual <vs> connection-limit`. Increase or investigate why connections aren't closing.

## SPL

```spl
index=network sourcetype="snmp:f5"
| timechart span=5m sum(clientside_curConns) as connections by virtual_server
```

## Visualization

Line chart per VIP, Area chart (throughput), Table.

## Known False Positives

Stats-only telemetry can spike during tests or polling changes; match to the device graphs before calling an incident.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
