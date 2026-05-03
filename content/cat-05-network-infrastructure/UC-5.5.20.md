<!-- AUTO-GENERATED from UC-5.5.20.json — DO NOT EDIT -->

---
id: "5.5.20"
title: "Hub-and-Spoke vs Full-Mesh Topology Validation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.20 · Hub-and-Spoke vs Full-Mesh Topology Validation

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

SD-WAN overlay topology determines traffic flow patterns. Validating that the actual tunnel mesh matches the intended design prevents asymmetric routing, hairpinning through hubs, and suboptimal site-to-site paths that add latency and waste hub bandwidth.

## Value

Network operations teams validate SD-WAN topology against design intent (hub-and-spoke vs. full-mesh), detecting unauthorized direct tunnels that bypass centralized security and missing tunnels that increase inter-site latency.

## Implementation

Map the active tunnel mesh by enumerating BFD sessions per device. Compare against the intended topology (hub-and-spoke, regional hub, full-mesh). Identify sites with fewer tunnels than expected (potential reachability gaps) or more tunnels than intended (resource waste). Review when deploying new sites or changing control policies.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for OMP routes and tunnel topology. Data in `index=sdwan` with `sourcetype=cisco:sdwan:omp` (route table), `sourcetype=cisco:sdwan:bfd` (tunnel inventory), and `sourcetype=cisco:sdwan:device` (device roles).
- SD-WAN topology types: (1) Hub-and-Spoke — branch sites connect only to hub sites (data centers). Inter-branch traffic hair-pins through the hub. Lower tunnel count, centralized security. (2) Full-Mesh — every site connects directly to every other site. Lower latency for inter-branch traffic, higher tunnel count and resource consumption. (3) Partial Mesh — branches connect to hubs and to selected peer branches (e.g., regional hubs).
- vSmart control policy determines topology. `restrict` keyword creates hub-and-spoke; no restrict creates full-mesh. Misconfigurations can create unintended topologies: branches with direct tunnels in a hub-and-spoke design (policy leak) or missing tunnels in a full-mesh design (partial convergence).
- Build `sdwan_topology_policy.csv` lookup: `site_id,expected_topology,expected_hub_id,expected_direct_peers` (e.g., `200,hub-and-spoke,100,`, `100,hub,,-`, `300,full-mesh,,*`).

### Step 1 — Configure data collection
Verify topology data:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up" earliest=-15m
| stats dc(remote_system_ip) as tunnel_peers by site_id, system_ip
| sort -tunnel_peers
```
Hub sites should have many peers (one per branch). Branches in hub-and-spoke should have few peers (only hubs). Full-mesh sites should have peers equal to total sites minus one.

### Step 2 — Create the search and alert

**Primary search — Topology validation against policy:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up" earliest=-15m
| stats dc(remote_system_ip) as actual_peers values(remote_system_ip) as peer_list by site_id, system_ip
| lookup sdwan_topology_policy.csv site_id OUTPUT expected_topology expected_hub_id expected_direct_peers
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval expected_peer_count=case(expected_topology="hub", 999, expected_topology="full-mesh", 999, expected_topology="hub-and-spoke", 2, 1==1, null())
| eval topology_status=case(expected_topology="hub-and-spoke" AND actual_peers > 4, "VIOLATION_EXTRA_TUNNELS", expected_topology="full-mesh" AND actual_peers < 5, "VIOLATION_MISSING_TUNNELS", expected_topology="hub" AND actual_peers < 10, "DEGRADED_HUB", 1==1, "OK")
| where topology_status!="OK"
| table site_name, tier, expected_topology, actual_peers, topology_status, peer_list
| sort topology_status
```

#### Understanding this SPL: Topology violations are subtle but impactful. In hub-and-spoke, a branch with direct tunnels to other branches bypasses centralized security inspection at the hub — a security policy violation. In full-mesh, missing tunnels mean some site-to-site traffic takes a longer path through a hub, increasing latency. This search automates what network engineers manually verify during audits.

**Hub-and-spoke traffic flow validation:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up" earliest=-15m
| lookup sdwan_topology_policy.csv site_id OUTPUT expected_topology expected_hub_id
| where expected_topology="hub-and-spoke"
| eval is_hub_tunnel=if(match(remote_system_ip, expected_hub_id), "hub", "direct")
| stats count(eval(is_hub_tunnel="hub")) as hub_tunnels count(eval(is_hub_tunnel="direct")) as direct_tunnels by site_id
| where direct_tunnels > 0
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval violation="Branch has ".direct_tunnels." direct tunnel(s) bypassing hub"
```

**Tunnel count distribution:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up" earliest=-15m
| stats dc(remote_system_ip) as tunnel_count by site_id
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_topology_policy.csv site_id OUTPUT expected_topology
| eval category=case(tunnel_count > 50, "Heavy mesh", tunnel_count > 20, "Moderate mesh", tunnel_count > 5, "Selective", tunnel_count <= 5, "Hub-spoke only")
| stats count as sites by category, expected_topology
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > select a branch device > Real-Time > OMP Routes. Verify the device only has routes through hub sites (for hub-and-spoke) or direct routes to all sites (for full-mesh).
(b) On an edge device: `show bfd sessions` — count peer devices and verify against expected topology.
(c) Trace traffic between two branches: in hub-and-spoke, `traceroute` should go through the hub; in full-mesh, it should be direct.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Topology Validation"):
- Row 1 — Single-value tiles: "Topology violations", "Extra direct tunnels (hub-spoke)", "Missing tunnels (full-mesh)", "Total fabric tunnels".
- Row 2 — Topology violations table: site, expected topology, actual peer count, violation type, peer list.
- Row 3 — Tunnel count distribution chart: histogram of tunnel counts per site.
- Row 4 — Hub-and-spoke validation: branches with unauthorized direct tunnels.

Alerting:
- High (branch has direct tunnels in hub-and-spoke topology): security policy bypass — traffic not inspected at hub.
- Warning (full-mesh site missing > 20% of expected tunnels): some site-to-site paths are suboptimal.
- Info (weekly): topology audit report for network architecture review.

### Step 5 — Troubleshooting

- **Branches have extra tunnels in hub-and-spoke** — vSmart centralized control policy may be missing the `restrict` keyword for those branches. Check: Configuration > Policies > Centralized Policy > Topology. A missing or misconfigured policy allows direct branch-to-branch tunnels.

- **Full-mesh site missing tunnels** — The device may have insufficient resources (tunnels consume memory) or BFD sessions are timing out to distant sites. Check device resource utilization (UC-5.5.13).

- **Topology changed after policy push** — After a centralized policy change on vSmart, topology reconverges. Allow 5-10 minutes for all BFD sessions to establish or tear down based on the new policy. Re-run the validation after convergence.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up"
| stats dc(remote_system_ip) as peer_count, values(remote_system_ip) as peers by local_system_ip, site_id
| eventstats avg(peer_count) as avg_peers
| eval topology=case(peer_count>avg_peers*1.5,"full-mesh candidate",peer_count<=2,"spoke",1=1,"partial-mesh")
| table site_id local_system_ip peer_count topology
| sort -peer_count
```

## Visualization

Network graph (nodes = sites, edges = tunnels), Table (site, peer count, topology type), Bar chart (topology distribution).

## Known False Positives

Route counts and peer mesh views shift during design changes, new site onboarding, or when a single transport is taken down for tests; confirm intent in vManage before escalation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
