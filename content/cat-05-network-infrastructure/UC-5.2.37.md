<!-- AUTO-GENERATED from UC-5.2.37.json — DO NOT EDIT -->

---
id: "5.2.37"
title: "Auto VPN Path Changes and Tunnel Switching (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.37 · Auto VPN Path Changes and Tunnel Switching (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We log automatic tunnel and path changes so the team can tell normal reroutes from a misconfiguration that strands users.*

---

## Description

Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.

## Value

Network engineers track Meraki Auto VPN path changes and tunnel switching to identify SD-WAN path instability and optimize uplink selection thresholds.

## Implementation

Monitor Auto VPN path optimization events. Alert on excessive changes.

## Detailed Implementation

### Prerequisites
* Meraki Auto VPN path change events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:vpn`. Key fields: `vpn_peers`, `path`, `tunnel_status`.
* Meraki Auto VPN: automatically creates IPsec VPN tunnels between MX devices in the same Meraki organization. SD-WAN path selection chooses the best uplink per peer based on latency, loss, and jitter. Path changes occur when one uplink degrades and traffic shifts to another.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Security & SD-WAN > Site-to-site VPN
# Type: Hub or Spoke
# SD-WAN & traffic shaping > Uplink selection: Performance-based
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:vpn") earliest=-7d
| where match(_raw, "(?i)vpn.*path|tunnel.*switch|uplink.*change|vpn.*route")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Auto VPN path change tracking:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:vpn") earliest=-7d
| where match(_raw, "(?i)vpn.*path|tunnel.*change|vpn.*route|uplink.*select")
| eval device=coalesce(serial, host, deviceSerial)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| eval peer=coalesce(peerSerial, peer, vpn_peer)
| lookup meraki_networks.csv serial AS peer OUTPUT network_name AS peer_name
| eval path_info=coalesce(path, uplink, interface)
| bin _time span=1h
| stats count as path_changes dc(peer) as affected_peers values(peer_name) as peer_names by _time, network_name, device
| eventstats avg(path_changes) as avg_changes stdev(path_changes) as stdev_changes by network_name
| eval z_score=if(stdev_changes > 0, round((path_changes - avg_changes)/stdev_changes, 2), 0)
| eval severity=case(
    z_score > 3, "CRITICAL -- abnormal path instability (z-score > 3)",
    path_changes > 20, "WARNING -- excessive VPN path changes",
    path_changes > 5, "INFO -- moderate path switching",
    1==1, "OK")
| where severity != "OK"
| sort severity, -path_changes
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > VPN status -- check tunnel states.
(b) Correlate path changes with WAN quality (UC-5.2.33) degradation.
(c) Verify SD-WAN uplink selection mode (load-balance vs performance-based).

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Auto VPN Paths"):
* Row 1 -- Single-value: "Path changes (24h)", "Affected peers", "Unstable sites".
* Row 2 -- Path change frequency timechart.

Alert: Critical (>50 path changes per hour): SD-WAN path flapping, investigate uplink quality.

### Step 5 — - Troubleshooting

* **Excessive path switching** -- Uplink quality is oscillating near the failover threshold. Consider adjusting SD-WAN performance class thresholds or switching to load-balance mode.

* **Path changes only affecting specific peers** -- Remote site may have unstable WAN. Check the peer's uplink quality metrics.

* **No path changes despite WAN issues** -- Verify SD-WAN uplink selection is set to "Performance-based" not "Default uplink".

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn (signature="*Auto VPN*" OR signature="*path change*")
| stats count as path_change_count by tunnel_id, new_path, old_path
| where path_change_count > 3
```

## Visualization

Path change timeline; tunnel path change distribution; convergence analysis.

## Known False Positives

Route optimization and ISP issues can re-path tunnels; verify impact before calling it a security problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
