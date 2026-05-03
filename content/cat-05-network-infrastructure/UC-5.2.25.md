<!-- AUTO-GENERATED from UC-5.2.25.json — DO NOT EDIT -->

---
id: "5.2.25"
title: "Site-to-Site VPN Latency and Performance (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.25 · Site-to-Site VPN Latency and Performance (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We follow tunnel delay on those paths so a slow provider or far peer is visible before people open tickets about "the VPN feels off."*

---

## Description

Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.

## Value

Operations teams trend Meraki MX site-to-site VPN latency, packet loss, and jitter per tunnel, detecting performance degradation that impacts inter-site application quality.

## Implementation

Extract VPN latency and jitter metrics. Monitor tunnel performance.

## Detailed Implementation

### Prerequisites
* Meraki MX VPN performance data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:vpnstatus`. Key metrics: site-to-site VPN tunnel latency, packet loss, jitter per tunnel.
* Meraki Auto VPN: automatic mesh or hub-and-spoke VPN between MX appliances. Performance metrics are available per tunnel via API: `/organizations/{orgId}/appliance/vpn/stats`.

### Step 1 — - Configure data collection
API input for VPN performance:
```
# inputs.conf
[meraki_vpn_stats]
interval = 300
sourcetype = meraki:api:vpnstatus
index = meraki
```
Verify:
```spl
index=meraki sourcetype="meraki:api:vpnstatus" earliest=-4h
| where isnotnull(latencyMs) OR isnotnull(lossPercent)
| stats avg(latencyMs) avg(lossPercent) by networkName, peerNetworkName
```

### Step 2 — - Create the search and alert

**Primary search -- Site-to-site VPN performance trending:**
```spl
index=meraki sourcetype="meraki:api:vpnstatus" earliest=-24h
| eval latency=tonumber(coalesce(latencyMs, latency_ms))
| eval loss=tonumber(coalesce(lossPercent, loss_percent))
| eval jitter=tonumber(coalesce(jitterMs, jitter_ms))
| eval tunnel=networkName." <-> ".peerNetworkName
| lookup meraki_networks.csv networkId OUTPUT site, criticality
| bin _time span=15m
| stats avg(latency) as avg_latency avg(loss) as avg_loss avg(jitter) as avg_jitter max(latency) as max_latency max(loss) as max_loss by _time, tunnel, criticality
| eval quality=case(avg_loss > 2 OR avg_latency > 150 OR avg_jitter > 30, "DEGRADED", avg_loss > 5 OR avg_latency > 300, "POOR", 1==1, "GOOD")
| where quality != "GOOD"
| eval severity=case(quality="POOR" AND criticality="high", "CRITICAL", quality="POOR", "HIGH", 1==1, "WARNING")
| table _time, tunnel, avg_latency, avg_loss, avg_jitter, quality, severity
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > VPN Status -- check per-tunnel metrics.
(b) Compare with network monitoring tools (ping, traceroute between sites).
(c) Correlate VPN performance with WAN uplink utilization.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- VPN Performance"):
* Row 1 -- Single-value: "Degraded tunnels", "Avg latency", "Max packet loss".
* Row 2 -- VPN performance timechart (latency, loss, jitter).

Alerting:
* Critical (critical tunnel with loss > 5% or latency > 300ms): severe VPN degradation.
* Warning (loss > 2% or latency > 150ms): performance degradation.

### Step 5 — - Troubleshooting

* **High latency** -- Check: (1) WAN uplink utilization at both sites, (2) ISP path issues (traceroute), (3) MX CPU utilization, (4) number of VPN tunnels (hub MX may be overloaded).

* **Packet loss** -- Check: (1) WAN link quality, (2) traffic shaping dropping VPN traffic, (3) MTU issues (reduce to 1400 for VPN).

* **Jitter** -- Common on shared WAN links. Enable QoS/traffic shaping to prioritize VPN traffic. Consider MPLS or dedicated WAN link for critical tunnels.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```

## Visualization

Gauge of VPN latency; latency trend line; jitter comparison chart.

## Known False Positives

ISPs, weather, and remote Wi-Fi often dominate latency; rule out the path before blaming the head-end device.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
