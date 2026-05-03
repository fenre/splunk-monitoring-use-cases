<!-- AUTO-GENERATED from UC-5.5.12.json — DO NOT EDIT -->

---
id: "5.5.12"
title: "BFD Session Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.12 · BFD Session Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

BFD (Bidirectional Forwarding Detection) provides sub-second failure detection between SD-WAN endpoints. A BFD session going down means the tunnel is unusable, and traffic must reroute. Tracking BFD flaps reveals transport instability before it cascades.

## Value

Network operations teams monitor BFD session states across all SD-WAN tunnels to detect transport failures, identify flapping circuits, and track session recovery time for rapid incident correlation.

## Implementation

Collect BFD session data from vManage. Alert immediately when a BFD session transitions from up to down. Track flap frequency per tunnel; more than 3 flaps in an hour signals an unstable transport that needs carrier engagement. Cross-reference with ISP maintenance schedules.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for BFD session status. Data in `index=sdwan` with `sourcetype=cisco:sdwan:bfd`. Key fields: `site_id`, `system_ip`, `local_color`, `remote_color`, `remote_system_ip`, `state` (up/down/init), `detect_multiplier`, `tx_interval`, `uptime`.
- BFD (Bidirectional Forwarding Detection) is the heartbeat protocol for SD-WAN tunnels. Each tunnel has a BFD session that detects link failure within milliseconds (default: 1000ms × 3 detect-multiplier = 3 seconds). When BFD detects a tunnel failure, SD-WAN immediately reroutes traffic to surviving tunnels.
- BFD session monitoring is distinct from tunnel health (UC-5.5.1): tunnel health measures quality (loss/latency/jitter), while BFD session monitoring tracks the session state (up/down/flapping). A tunnel can have poor quality but BFD is still up; conversely, BFD can flap while average metrics look acceptable.

### Step 1 — Configure data collection
Verify BFD session data:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats count by state, local_color
```
Healthy output: vast majority in "up" state.

### Step 2 — Create the search and alert

**Primary search — BFD session failures:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats count(eval(state="up")) as up_sessions count(eval(state!="up")) as down_sessions values(state) as states by site_id, system_ip, local_color
| where down_sessions > 0
| eval total=up_sessions + down_sessions
| eval down_pct=round(100*down_sessions/total, 1)
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| eval severity=case(down_pct > 80, "CRITICAL", down_pct > 50, "HIGH", down_sessions > 0, "WARNING", 1==1, "OK")
| table site_name, tier, hostname, system_ip, local_color, up_sessions, down_sessions, down_pct, severity
| sort severity, tier
```

#### Understanding this SPL: A BFD session going down means a specific tunnel is unusable. If all BFD sessions on a transport color are down, that transport is completely failed. If all sessions on all colors are down, the device/site is isolated. The `down_pct` helps distinguish between partial (one peer unreachable) and total (transport failure) outages.

**BFD flapping detection:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-2h
| where state="down" OR state="init"
| bin _time span=5m
| stats count as flap_events dc(remote_system_ip) as affected_peers by _time, site_id, system_ip, local_color
| where flap_events > 3
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval severity=case(flap_events > 20, "CRITICAL", flap_events > 10, "HIGH", 1==1, "WARNING")
```

**BFD session uptime tracking:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up" earliest=-15m
| eval uptime_hours=round(uptime/3600, 1)
| where uptime_hours < 1
| lookup sdwan_sites.csv site_id OUTPUT site_name
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| table site_name, hostname, local_color, remote_color, uptime_hours
| sort uptime_hours
```

### Step 3 — Validate
(a) On an edge device: `show bfd sessions` — compare session states with Splunk results.
(b) In vManage: Monitor > Network > BFD. Verify session counts match.
(c) During a maintenance window: shut down a WAN interface and verify the BFD session goes down in Splunk within the expected detection time.

### Step 4 — Operationalize
Dashboard ("SD-WAN — BFD Sessions"):
- Row 1 — Single-value tiles: "BFD sessions UP", "BFD sessions DOWN", "Flapping sessions (2h)", "Recently bounced (< 1h uptime)".
- Row 2 — BFD failure table: site, device, transport, up sessions, down sessions, severity.
- Row 3 — Flapping detection: devices with frequent BFD state changes.
- Row 4 — Recently bounced sessions: sessions with < 1 hour uptime (indicates recent recovery from failure).

Alerting:
- Critical (> 80% BFD sessions down on a device): device is nearly isolated.
- High (BFD flapping > 10 events in 5 minutes): unstable transport causing constant rerouting.
- Warning (any BFD session down): track and investigate.

### Step 5 — Troubleshooting

- **BFD down on one color but up on others** — The specific WAN transport is down. Check ISP circuit status for that color. If Internet is down but MPLS is up, traffic should already be rerouting.

- **BFD flapping on LTE** — LTE is inherently less stable than wired transports. Consider increasing the BFD detect-multiplier for LTE tunnels to reduce false flaps.

- **BFD sessions show "init" state** — The tunnel is trying to establish but can't complete the BFD handshake. Common causes: NAT issues (BFD uses UDP 3784), firewall blocking BFD packets, or MTU issues.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| where state!="up"
| stats count as flap_count, latest(_time) as last_flap, values(state) as states by local_system_ip, remote_system_ip, local_color, remote_color
| where flap_count > 3
| sort -flap_count
| eval last_flap=strftime(last_flap,"%Y-%m-%d %H:%M:%S")
```

## Visualization

Status grid (BFD sessions by color/site), Timeline (session state changes), Table (flapping tunnels).

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
