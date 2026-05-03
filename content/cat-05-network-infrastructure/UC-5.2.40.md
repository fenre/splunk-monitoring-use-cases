<!-- AUTO-GENERATED from UC-5.2.40.json — DO NOT EDIT -->

---
id: "5.2.40"
title: "Meraki VPN Tunnel and Failover Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.40 · Meraki VPN Tunnel and Failover Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep watch on tunnel and failover state from the cloud dashboard data so a down path is not something you only hear about in a meeting.*

---

## Description

Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.

## Value

NOC teams monitor Meraki MX site-to-site and client VPN tunnel status, detecting tunnel failures and flapping to maintain inter-site connectivity and remote user access.

## Implementation

Poll Meraki API for VPN tunnel status or ingest MX syslog for tunnel events. Alert when any tunnel is down. Track failover events for active/standby links.

## Detailed Implementation

### Prerequisites
* Meraki MX VPN tunnel status data. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:vpn`. Key fields: `vpn_type` (site-to-site, client), `tunnel_status`, `peer_serial`, `peer_network`.
* Meraki Auto VPN: creates full-mesh or hub-spoke IPsec tunnels between MX devices. Client VPN: AnyConnect or L2TP/IPsec for remote users. Dashboard > Security & SD-WAN > Site-to-site VPN and Client VPN.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Security & SD-WAN > Site-to-site VPN
# Type: Hub, Spoke, or Off (per network)
# Client VPN: Security & SD-WAN > Client VPN > Enabled
# API polling: GET /networks/{networkId}/appliance/vpn/statuses
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:vpn") earliest=-24h
| where match(_raw, "(?i)vpn|tunnel|ipsec")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- VPN tunnel status and health:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:vpn") earliest=-24h
| eval device=coalesce(serial, host, deviceSerial)
| lookup meraki_networks.csv serial AS device OUTPUT network_name AS local_network, site_name AS local_site
| eval peer=coalesce(peerSerial, peer, peer_serial)
| lookup meraki_networks.csv serial AS peer OUTPUT network_name AS peer_network
| eval tunnel_type=case(match(_raw, "(?i)site.?to.?site|s2s|auto.?vpn"), "Site-to-Site", match(_raw, "(?i)client|anyconnect|l2tp|remote"), "Client VPN", 1==1, "Unknown")
| eval status=case(
    match(_raw, "(?i)up|established|connected|online"), "UP",
    match(_raw, "(?i)down|disconnected|failed|offline|lost"), "DOWN",
    match(_raw, "(?i)negotiat|establish|connect"), "NEGOTIATING",
    1==1, "UNKNOWN")
| sort device, peer, _time
| dedup device, peer sortby -_time
| eval severity=case(
    status="DOWN" AND tunnel_type="Site-to-Site", "CRITICAL -- site-to-site VPN tunnel down",
    status="DOWN" AND tunnel_type="Client VPN", "WARNING -- client VPN disconnected",
    status="NEGOTIATING", "INFO -- tunnel re-establishing",
    1==1, "OK")
| where severity != "OK"
| table local_network, local_site, peer_network, tunnel_type, status, _time, severity
| sort severity
```

**Secondary search -- VPN tunnel flapping (up/down cycling):**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:vpn") earliest=-24h
| where match(_raw, "(?i)vpn|tunnel|ipsec")
| eval device=coalesce(serial, host, deviceSerial)
| eval peer=coalesce(peerSerial, peer)
| eval status=if(match(_raw, "(?i)up|established|connected"), "UP", "DOWN")
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| bin _time span=1h
| stats count as state_changes dc(eval(status)) as unique_states by _time, device, network_name, peer
| where state_changes > 4
| eval severity="WARNING -- VPN tunnel flapping (".state_changes." state changes/hour)"
| sort -state_changes
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > VPN status -- verify tunnel states match.
(b) Test: temporarily disable VPN on a spoke and verify DOWN event.
(c) Compare with uplink failover events (UC-5.2.34) for correlation.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- VPN Tunnel Health"):
* Row 1 -- Single-value: "Tunnels DOWN", "Tunnels UP", "Flapping tunnels".
* Row 2 -- VPN tunnel status table (all tunnels with current state).
* Row 3 -- Tunnel state change timeline.

Alerting:
* Critical (site-to-site tunnel DOWN > 5 minutes): page NOC.
* Warning (tunnel flapping > 4 state changes/hour): investigate WAN stability.

### Step 5 — - Troubleshooting

* **Tunnel won't establish** -- Check: (1) both MX devices are online, (2) uplink IPs are reachable, (3) firewall allows UDP 500 and 4500 (IKE/IPsec), (4) NAT-T is functioning.

* **Tunnel flapping** -- Often caused by underlying WAN instability. Correlate with WAN quality (UC-5.2.33) and uplink failover (UC-5.2.34). Consider adjusting DPD (Dead Peer Detection) timers.

* **Client VPN disconnections** -- Check AnyConnect or L2TP client configuration. Verify authentication (RADIUS/Meraki auth). Check concurrent user limits on MX model.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" vpn_tunnel=*
| stats latest(tunnel_state) as state, latest(peer_ip) as peer by device_serial, tunnel_id
| where state != "up"
| table device_serial tunnel_id peer state _time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).

## Known False Positives

Tunnels, peers, and monitored paths can flap during routine network work; use duration to separate noise from outage.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
