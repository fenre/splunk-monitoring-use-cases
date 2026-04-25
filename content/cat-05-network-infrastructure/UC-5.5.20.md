<!-- AUTO-GENERATED from UC-5.5.20.json — DO NOT EDIT -->

---
id: "5.5.20"
title: "Hub-and-Spoke vs Full-Mesh Topology Validation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.20 · Hub-and-Spoke vs Full-Mesh Topology Validation

## Description

SD-WAN overlay topology determines traffic flow patterns. Validating that the actual tunnel mesh matches the intended design prevents asymmetric routing, hairpinning through hubs, and suboptimal site-to-site paths that add latency and waste hub bandwidth.

## Value

SD-WAN overlay topology determines traffic flow patterns. Validating that the actual tunnel mesh matches the intended design prevents asymmetric routing, hairpinning through hubs, and suboptimal site-to-site paths that add latency and waste hub bandwidth.

## Implementation

Map the active tunnel mesh by enumerating BFD sessions per device. Compare against the intended topology (hub-and-spoke, regional hub, full-mesh). Identify sites with fewer tunnels than expected (potential reachability gaps) or more tunnels than intended (resource waste). Review when deploying new sites or changing control policies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage BFD sessions, OMP routes, `sourcetype=cisco:sdwan:bfd`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map the active tunnel mesh by enumerating BFD sessions per device. Compare against the intended topology (hub-and-spoke, regional hub, full-mesh). Identify sites with fewer tunnels than expected (potential reachability gaps) or more tunnels than intended (resource waste). Review when deploying new sites or changing control policies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up"
| stats dc(remote_system_ip) as peer_count, values(remote_system_ip) as peers by local_system_ip, site_id
| eventstats avg(peer_count) as avg_peers
| eval topology=case(peer_count>avg_peers*1.5,"full-mesh candidate",peer_count<=2,"spoke",1=1,"partial-mesh")
| table site_id local_system_ip peer_count topology
| sort -peer_count
```

Understanding this SPL

**Hub-and-Spoke vs Full-Mesh Topology Validation** — SD-WAN overlay topology determines traffic flow patterns. Validating that the actual tunnel mesh matches the intended design prevents asymmetric routing, hairpinning through hubs, and suboptimal site-to-site paths that add latency and waste hub bandwidth.

Documented **Data sources**: vManage BFD sessions, OMP routes, `sourcetype=cisco:sdwan:bfd`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:bfd. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:bfd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by local_system_ip, site_id** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **topology** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Hub-and-Spoke vs Full-Mesh Topology Validation**): table site_id local_system_ip peer_count topology
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network graph (nodes = sites, edges = tunnels), Table (site, peer count, topology type), Bar chart (topology distribution).

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

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
