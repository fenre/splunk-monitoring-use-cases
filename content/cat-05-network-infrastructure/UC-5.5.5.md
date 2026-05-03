<!-- AUTO-GENERATED from UC-5.5.5.json — DO NOT EDIT -->

---
id: "5.5.5"
title: "Control Plane Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.5 · Control Plane Health

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

vSmart/vManage connectivity issues affect policy distribution and overlay routing.

## Value

Network operations teams monitor SD-WAN control plane connections (vSmart, vBond, vManage) to detect controller failures, policy distribution issues, and edge device isolation before they cascade into data plane outages.

## Implementation

Monitor control connections to vSmart and vManage. Alert on any control connection down.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage for control connection status. Data in `index=sdwan` with `sourcetype=cisco:sdwan:control`. Key fields: `site_id`, `system_ip`, `personality` (vmanage/vsmart/vbond/vedge), `peer_system_ip`, `state` (up/down/connect/challenge), `domain_id`, `uptime`.
- The SD-WAN control plane consists of three components: vBond (orchestrator — authenticates devices), vSmart (controller — distributes routing policy via OMP), vManage (management — configuration, monitoring). Edge devices (vEdge/cEdge) must maintain control connections to all three.
- Control plane issues are invisible to end users initially but critical: if an edge loses its vSmart connection, it can't receive policy updates. If vBond is down, new devices can't onboard. If vManage is down, operators lose visibility and can't push configuration changes.
- Build `sdwan_controllers.csv` lookup: `system_ip,hostname,personality,datacenter,redundancy_pair`.

### Step 1 — Configure data collection
Verify control connection data:
```spl
index=sdwan sourcetype="cisco:sdwan:control" earliest=-15m
| stats count by personality, state
```
Healthy output: vast majority of connections in "up" state across all personality types.

### Step 2 — Create the search and alert

**Primary search — Control plane connection health:**
```spl
index=sdwan sourcetype="cisco:sdwan:control" earliest=-15m
| stats count as total count(eval(state="up")) as up_conns count(eval(state!="up")) as problem_conns values(state) as states by system_ip, personality, peer_system_ip
| where problem_conns > 0
| lookup sdwan_sites.csv site_id as system_ip OUTPUT site_name
| lookup sdwan_controllers.csv system_ip as peer_system_ip OUTPUT hostname as peer_hostname
| eval severity=case(personality="vsmart" AND state!="up", "CRITICAL", personality="vbond" AND state!="up", "HIGH", personality="vmanage" AND state!="up", "HIGH", 1==1, "WARNING")
| table system_ip, site_name, personality, peer_system_ip, peer_hostname, states, severity
| sort severity
```

#### Understanding this SPL: A broken vSmart connection means the edge device stops receiving OMP route updates and policy changes — existing data plane tunnels continue working with stale policy, but no adaptation is possible. A broken vBond connection prevents new device onboarding and certificate renewal. Both are invisible to end users but represent a degraded state.

**Control plane topology overview:**
```spl
index=sdwan sourcetype="cisco:sdwan:control" state="up" earliest=-15m
| stats dc(peer_system_ip) as peer_count values(peer_system_ip) as peers by system_ip, personality
| lookup sdwan_controllers.csv system_ip OUTPUT hostname
| eval label=if(isnotnull(hostname), hostname." (".personality.")", system_ip)
| sort personality, -peer_count
```

**Edge devices with missing controller connections:**
```spl
index=sdwan sourcetype="cisco:sdwan:control" earliest=-15m personality IN ("vedge", "cedge")
| stats dc(eval(if(match(peer_system_ip, "vsmart"), peer_system_ip, null()))) as vsmart_conns dc(eval(if(match(peer_system_ip, "vbond"), peer_system_ip, null()))) as vbond_conns dc(eval(if(match(peer_system_ip, "vmanage"), peer_system_ip, null()))) as vmanage_conns by system_ip, site_id
| where vsmart_conns=0 OR vbond_conns=0 OR vmanage_conns=0
| eval missing=mvappend(if(vsmart_conns=0, "vSmart", null()), if(vbond_conns=0, "vBond", null()), if(vmanage_conns=0, "vManage", null()))
| eval missing_str=mvjoin(missing, ", ")
| lookup sdwan_sites.csv site_id OUTPUT site_name
```

### Step 3 — Validate
(a) In vManage: Administration > Settings > check controller status. All controllers should show "active" and connected.
(b) On an edge device CLI: `show control connections` — each controller (vSmart, vBond, vManage) should show state "up". Cross-check with Splunk results.
(c) Verify redundancy: if you have two vSmarts, each edge should show two vSmart connections.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Control Plane Health"):
- Row 1 — Single-value tiles: "Edges with all controllers UP", "Edges missing vSmart", "Edges missing vBond", "Controller connections down".
- Row 2 — Controller status table: controller hostname, personality, connected edges, connection states.
- Row 3 — Edges with missing connections: site, device, missing controller types.

Alerting:
- Critical (any vSmart loses > 50% of edge connections): controller failure — edges can't receive policy updates.
- Critical (all vBond connections down): new device onboarding impossible; certificate renewal blocked.
- High (edge device loses all controller connections): device is operating in "headless" mode with stale policy.

### Step 5 — Troubleshooting

- **Control connection stuck in "challenge" state** — Certificate issue. The edge device's certificate may have expired or been revoked. Check: `show certificate installed` on the device.

- **Edge has vManage connection but no vSmart** — vSmart may be overloaded or unreachable from that site. Check vSmart process health and whether the site's WAN transport can reach the vSmart IP. Also check if the site's control policy allows the connection.

- **Intermittent control connection drops** — Often caused by NAT timeouts on the WAN transport. SD-WAN control connections use DTLS. If the NAT timeout is shorter than the keepalive interval, connections drop. Reduce the keepalive timer or configure NAT keepalive on the transport.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:control"
| where state!="up"
| table _time hostname peer_type peer_system_ip state | sort -_time
```

## Visualization

Status panel, Table, Timeline.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
