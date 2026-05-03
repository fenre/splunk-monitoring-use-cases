<!-- AUTO-GENERATED from UC-5.2.19.json — DO NOT EDIT -->

---
id: "5.2.19"
title: "VPN Tunnel Status and Path Monitoring (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.19 · VPN Tunnel Status and Path Monitoring (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We see whether site-to-site tunnels stay in a good state so branch offices and partners stay connected when paths get noisy.*

---

## Description

Ensures all site-to-site and client VPN tunnels remain active and operative.

## Value

Operations teams monitor Meraki MX Auto VPN and third-party tunnel status with path quality metrics (latency, loss, jitter), detecting site connectivity failures.

## Implementation

Monitor VPN tunnel state from syslog and API. Alert on status != "up".

## Detailed Implementation

### Prerequisites
* Meraki MX VPN logs via Meraki Dashboard API or syslog. Data in `index=meraki` with `sourcetype=meraki:api:vpnstatus` (API) or `sourcetype=meraki:events` (syslog). Key fields: `networkId`, `peer_name`, `peer_type` (site-to-site/third-party), `vpn_status` (online/offline/negotiating), `latency_ms`, `loss_percent`, `jitter_ms`.
* Install `Splunk_TA_cisco_meraki` and configure Meraki Dashboard API polling for VPN status endpoint: `/organizations/{orgId}/appliance/vpn/statuses`.
* Create `meraki_networks.csv` lookup: `networkId`, `network_name`, `site`, `criticality`.

### Step 1 — - Configure data collection
API polling input:
```
# inputs.conf
[meraki_vpn_status]
interval = 300
sourcetype = meraki:api:vpnstatus
index = meraki
```
Syslog from MX:
```
# Meraki Dashboard > Network-wide > General > Reporting > Syslog servers
# Add Splunk syslog IP, port 514, roles: VPN
```
Verify:
```spl
index=meraki (sourcetype="meraki:api:vpnstatus" OR sourcetype="meraki:events") earliest=-4h
| where match(_raw, "(?i)vpn|tunnel|ipsec")
| stats count by sourcetype
```

### Step 2 — - Create the search and alert

**Primary search -- VPN tunnel status and path monitoring:**
```spl
index=meraki sourcetype="meraki:api:vpnstatus" earliest=-4h
| eval vpn_status=lower(coalesce(vpn_status, reachability))
| eval peer=coalesce(peer_name, peerNetworkId)
| lookup meraki_networks.csv networkId OUTPUT network_name, site, criticality
| eval latency=tonumber(latency_ms)
| eval loss=tonumber(loss_percent)
| eval jitter=tonumber(jitter_ms)
| stats latest(vpn_status) as status latest(latency) as latency_ms latest(loss) as loss_pct latest(jitter) as jitter_ms latest(_time) as last_check by network_name, peer, site, criticality
| eval quality=case(loss_pct > 5 OR latency_ms > 200 OR jitter_ms > 50, "DEGRADED", status="offline", "DOWN", 1==1, "HEALTHY")
| eval severity=case(status="offline" AND criticality="high", "CRITICAL -- high-criticality tunnel DOWN", status="offline", "HIGH -- tunnel offline", quality="DEGRADED", "WARNING -- degraded performance (loss=".loss_pct."%, lat=".latency_ms."ms, jitter=".jitter_ms."ms)", 1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) Meraki Dashboard: Security & SD-WAN > VPN Status -- compare online/offline tunnels.
(b) Verify per-tunnel latency/loss/jitter values match dashboard.
(c) Disconnect a test tunnel and verify status change appears in Splunk.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- VPN Health"):
* Row 1 -- Single-value: "Tunnels DOWN", "Degraded tunnels", "Total tunnels".
* Row 2 -- VPN tunnel status table with quality metrics.
* Row 3 -- Latency/loss trending timechart.

Alerting:
* Critical (high-criticality tunnel offline > 5 min): site connectivity lost.
* Warning (loss > 5% or latency > 200ms): degraded performance.

### Step 5 — - Troubleshooting

* **Tunnel offline** -- Check: (1) WAN uplink status at both sites, (2) MX appliance power/connectivity, (3) ISP outage. Meraki Dashboard > Monitor > Appliance status.

* **High latency/loss** -- Check: (1) WAN uplink saturation, (2) ISP path issue, (3) traffic shaping bandwidth limits. Use Meraki "WAN Health" page for uplink performance.

* **Tunnel negotiating but not establishing** -- IKE/IPSec mismatch with third-party VPN peer. Check: pre-shared key, Phase 1/2 settings. Meraki auto-VPN tunnels should establish automatically.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn
| stats latest(status) as tunnel_status, latest(last_changed) as status_change_time by tunnel_id, remote_site
| where tunnel_status="down" OR tunnel_status="unstable"
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

VPN tunnel status matrix; site connectivity map; tunnel health sparklines.

## Known False Positives

ISPs, DPD, and path changes can flap tunnels briefly; compare duration and business impact before paging.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
