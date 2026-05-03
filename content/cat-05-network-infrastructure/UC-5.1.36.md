<!-- AUTO-GENERATED from UC-5.1.36.json — DO NOT EDIT -->

---
id: "5.1.36"
title: "Port Utilization and Congestion Alerts (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.36 · Port Utilization and Congestion Alerts (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with port utilization and congestion alerts so the team can act before it grows into a bigger outage.*

---

## Description

Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.

## Value

Operations teams monitor Meraki MS switch port utilization and congestion, identifying saturated ports that require link aggregation or capacity upgrades.

## Implementation

Query MS switch device API for port utilization metrics. Alert on sustained >80% utilization.

## Detailed Implementation

### Prerequisites
* Meraki MS switch port utilization data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:switch:ports` or `sourcetype=meraki:api:switch:portstatus`. Key fields: `portId`, `usageInKb`, `status`, `speed`, `duplex`.
* Meraki Dashboard API: `GET /devices/{serial}/switch/ports/statuses` returns per-port traffic, status, speed/duplex, and PoE. Polling interval should be 5 minutes for real-time visibility.

### Step 1 — - Configure data collection
```
# inputs.conf
[meraki_switch_ports]
interval = 300
sourcetype = meraki:api:switch:portstatus
index = meraki
# API: GET /devices/{serial}/switch/ports/statuses
```
Verify:
```spl
index=meraki sourcetype="meraki:api:switch:portstatus" earliest=-1h
| stats count by host, portId
```

### Step 2 — - Create the search and alert

**Primary search -- Port utilization and congestion alerts:**
```spl
index=meraki sourcetype="meraki:api:switch:portstatus" earliest=-4h
| eval port=coalesce(portId, port_id)
| eval speed_mbps=case(match(speed, "(?i)10 G"), 10000, match(speed, "(?i)1 G"), 1000, match(speed, "(?i)100 M"), 100, 1==1, 1000)
| eval sent_kbps=tonumber(coalesce(usageInKb.sent, sent_kbps, sent))/300
| eval recv_kbps=tonumber(coalesce(usageInKb.recv, recv_kbps, recv))/300
| eval total_kbps=sent_kbps + recv_kbps
| eval total_mbps=round(total_kbps/1024, 2)
| eval util_pct=round(100*total_mbps/speed_mbps, 1)
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| bin _time span=5m
| stats avg(util_pct) as avg_util max(util_pct) as max_util avg(total_mbps) as avg_mbps by _time, network_name, device, port
| eval severity=case(
    max_util > 90, "CRITICAL -- port ".port." near saturation (".max_util."%)",
    max_util > 75, "WARNING -- port ".port." high utilization",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, port, avg_mbps, avg_util, max_util, severity
| sort severity, -max_util
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check per-port utilization graphs.
(b) Compare with Dashboard live tools: cable test, packet capture.
(c) Verify port speed/duplex negotiation is correct.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Port Utilization"):
* Row 1 -- Single-value: "Ports > 75% utilization", "Peak port utilization (%)".
* Row 2 -- Port utilization timechart.

Alert: Critical (port >90% sustained): trunk upgrade or traffic optimization needed.

### Step 5 — - Troubleshooting

* **Uplink port congested** -- Insufficient bandwidth between switches. Consider: link aggregation, upgrading to 10G uplink, or traffic optimization.

* **Access port high utilization** -- Single device consuming excessive bandwidth. Check connected device type and activity. Apply traffic shaping if needed.

* **Port speed mismatch** -- Verify negotiated speed matches expected. Dashboard: Switch ports > port details.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(port_utilization) as avg_util, max(port_utilization) as max_util by switch_name, port_id
| where max_util > 80
| sort - max_util
```

## Visualization

Table of congested ports; timeline showing peak congestion; port utilization heatmap.

## Known False Positives

Short bursts during backups, patch pushes, or video calls can approach thresholds without an outage. Match alerts to business hours and known batch jobs.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
