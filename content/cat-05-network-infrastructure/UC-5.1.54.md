<!-- AUTO-GENERATED from UC-5.1.54.json — DO NOT EDIT -->

---
id: "5.1.54"
title: "Carrier Connection Health and Network Performance (Meraki MG)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.54 · Carrier Connection Health and Network Performance (Meraki MG)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch the cellular or backup-WAN link on your Meraki gateway and tell you when carrier or network errors pile up so you can fix the path before sites go dark.*

---

## Description

Monitors carrier connectivity and network performance metrics for backup internet links.

## Value

Operations teams monitor Meraki MG carrier connection health including connection type, latency, and loss to detect carrier network degradation and connection downgrades affecting WAN performance.

## Implementation

Monitor carrier connection and network events. Alert on issues.

## Detailed Implementation

### Prerequisites
* Meraki MG carrier connection health data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:cellular:signal` or `sourcetype=meraki:api:uplinks`. Key fields: `connectionType` (LTE/5G/3G), `provider`, `apn`, `latencyMs`, `lossPct`.
* Meraki MG connects to cellular carriers via configured APNs. Carrier network performance (latency, loss) directly impacts WAN quality. Connection type downgrades (LTE→3G) indicate signal issues.

### Step 1 — - Configure data collection
```
# Same API as UC-5.1.52 plus uplink performance
# GET /devices/{serial}/cellular/sims
# GET /organizations/{orgId}/devices/uplinksLossAndLatency
```
Verify:
```spl
index=meraki sourcetype="meraki:api:cellular:signal" earliest=-4h
| stats latest(connectionType) latest(provider) by host
```

### Step 2 — - Create the search and alert

**Primary search -- Carrier connection health:**
```spl
index=meraki (sourcetype="meraki:api:cellular:signal" OR sourcetype="meraki:api:uplinkstats") earliest=-4h
| eval device=coalesce(serial, host)
| eval conn_type=coalesce(connectionType, connection_type)
| eval carrier=coalesce(provider, carrier, network_provider)
| eval latency=tonumber(coalesce(latencyMs, latency))
| eval loss=tonumber(coalesce(lossPct, loss))
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| bin _time span=15m
| stats latest(conn_type) as connection avg(latency) as avg_latency avg(loss) as avg_loss by _time, network_name, device, carrier
| eval avg_latency=round(avg_latency, 1)
| eval avg_loss=round(avg_loss, 2)
| eval severity=case(
    match(connection, "(?i)3G|2G|EDGE|GPRS"), "WARNING -- degraded cellular connection type: ".connection,
    avg_loss > 5 OR avg_latency > 200, "WARNING -- poor carrier network performance",
    avg_loss > 2 OR avg_latency > 100, "INFO -- moderate carrier latency/loss",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, carrier, connection, avg_latency, avg_loss, severity
| sort severity
```

### Step 3 — - Validate
(a) Dashboard: Cellular gateway > Overview -- check connection type and carrier.
(b) Compare with carrier SLA for the plan level.
(c) Monitor connection type changes over time.

### Step 4 — - Operationalize
Dashboard ("Meraki MG -- Carrier Health"):
* Row 1 -- Single-value: "Connection type", "Carrier", "Avg latency (ms)".
* Row 2 -- Carrier performance timechart (latency, loss).

Alert: Warning (connection downgrade to 3G or high latency): carrier issue.

### Step 5 — - Troubleshooting

* **Connection type downgrade** -- Signal quality insufficient for LTE/5G. Check antenna and placement (UC-5.1.52). May need carrier investigation.

* **High carrier latency** -- Carrier network congestion. Compare with signal quality -- if signal is strong but latency is high, the issue is in the carrier core network. Contact carrier.

* **Frequent carrier disconnections** -- Check SIM status (UC-5.1.55). May indicate SIM or account issue with carrier.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*carrier*")
| stats count as event_count by event_type, carrier_name
| where event_type="connection_error" OR event_type="network_error"
```

## Visualization

Carrier health timeline; connection error table; network performance gauge.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
