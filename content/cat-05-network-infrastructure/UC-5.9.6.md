<!-- AUTO-GENERATED from UC-5.9.6.json — DO NOT EDIT -->

---
id: "5.9.6"
title: "Network Path Change Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.6 · Network Path Change Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the exact route our traffic takes across the internet, and when it suddenly switches to a different road we flag it — because a new route might go through a congested or unreliable area.*

---

## Description

Detects when the network path between an agent and a target changes topology — different intermediate routers, different ISPs, or different geographic routing — within the search window. Unlike hop count analysis (UC-5.9.5) which only detects length changes, this UC catches path shifts where the hop count stays the same but the actual routers traversed change (e.g., a carrier reroutes through a different PoP at the same hop depth).

## Value

A path change is the single most valuable early-warning signal for imminent or concurrent network degradation. When a carrier cuts over to a backup path — whether due to fiber cut, maintenance, or BGP convergence — latency typically increases by 10–50 ms, jitter doubles, and loss may spike during the transition. By detecting the path change itself in Splunk (not just the latency consequence), the NOC can immediately open the ThousandEyes permalink to see the old-vs-new path topology, identify which carrier made the change, and decide whether to wait it out, reroute via SD-WAN, or escalate to the ISP — all before the latency SLA alert fires.

## Implementation

Requires path visualization data to be enabled (same as UC-5.9.5). The `path_hash` field must either be computed by the app from the ordered sequence of hop IPs, or computed in SPL. If the app does not provide `path_hash` natively, build it with an `eval` that hashes the concatenated hop IPs. Schedule every 30 minutes over the last 4 hours.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.5 apply — path visualization data collection must be enabled in the Tests Stream — Metrics input, the `thousandeyes_pathvis` index must exist, and the `path_viz_index` macro must be configured.
- **Path hash computation:** This UC depends on a `path_hash` field that fingerprints the ordered sequence of intermediate hops. Some versions of the ThousandEyes app compute this natively; others do not. If `path_hash` is not present in your data, you need to build it in SPL from the raw hop data (see Step 2).
- **Baseline path inventory:** Before alerting on path changes, establish a baseline of normal paths for each agent-target pair over 7 days. This lets you distinguish new paths (genuinely new routing) from paths the system has seen before (ECMP rotation through known paths).
- **Difficulty: Advanced** — This UC requires understanding of network path topology and the ability to interpret hop-level path visualization data. The SPL may need customization based on how your version of the app structures path data.

### Step 1 — Configure data collection
Same as UC-5.9.5 — enable "Include Network Path Data" in the Tests Stream — Metrics input. No additional configuration beyond what UC-5.9.5 requires.

Verify path data has sufficient hop-level detail:
```spl
index=thousandeyes_pathvis sourcetype="cisco:thousandeyes:path-vis" earliest=-30m
| head 5
| table _time, thousandeyes.source.agent.name, server.address, hop_count, path_hash
```
If `path_hash` is present and populated, proceed to Step 2. If not, you'll need to compute it.

### Step 2 — Create the search and alert
**If `path_hash` is a native field:**
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths values(path_hash) as path_list count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```

**If `path_hash` must be computed (path data stored as individual hop rows):**
Some app versions store path visualization as one event per path with hop data in multivalue fields, or as separate hop-level events that must be aggregated. For the multivalue case:
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| eval path_fingerprint = md5(mvjoin(mvsort(hop_ips), "→"))
| stats dc(path_fingerprint) as unique_paths values(path_fingerprint) as path_list count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```
Replace `hop_ips` with the actual multivalue field containing the ordered list of hop IP addresses in your data. Use `| fieldsummary` to identify the correct field names.

**Understanding this SPL**

`dc(path_hash)` — counts the number of distinct paths seen for each agent-target pair in the search window. A value of 1 means the path was stable; a value > 1 means the path changed at least once.

`values(path_hash)` — lists all distinct path fingerprints observed, useful for dashboards that show before/after comparison.

`where unique_paths > 1` — fires when ANY path change is detected. For noisy environments with ECMP, raise to `> 2` (allowing one alternate path) or `> 3`. For critical paths where ANY change must be investigated, keep at `> 1`.

**Performance-impact correlation variant:**
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths earliest(_time) as first_seen latest(_time) as last_seen by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| join type=left thousandeyes.source.agent.name, server.address [
  search `stream_index` thousandeyes.test.type="agent-to-server"
  | stats avg(network.latency) as avg_lat_s stdev(network.latency) as stdev_lat_s by thousandeyes.source.agent.name, server.address
  | eval avg_lat_ms=round(avg_lat_s*1000,1)
  | eval variability=round(stdev_lat_s*1000,1)
]
| eval impact=case(avg_lat_ms>100 AND variability>20, "HIGH — path change with latency impact", avg_lat_ms>100, "MEDIUM — elevated latency", variability>20, "MEDIUM — high variability", 1=1, "LOW — path changed but performance stable")
| sort -unique_paths
```
This variant cross-references path changes with latency variability from the metrics stream. Paths that changed AND show high latency variability are the top-priority investigation targets.

**Scheduling:** cron `*/30 * * * *`, time range `-4h to now`. Throttle by `thousandeyes.source.agent.name` + `server.address` for 8 hours.

### Step 3 — Validate
(a) **Known path change.** If you have access to a test environment where you can induce a routing change (e.g., shut down a router interface to force BGP failover), do so and verify that Splunk detects the path change within 2 polling intervals.

(b) **Stable path baseline.** For a path you know is stable (dedicated circuit, no ECMP), `unique_paths` should be 1 over any time window. If it's > 1, either the path fingerprinting is too sensitive (hashing artifacts) or there's a genuine unexpected routing variation.

(c) **Cross-reference ThousandEyes.** Open the Path Visualization for a path that Splunk flagged as changed. ThousandEyes shows a timeline of path changes with visual topology diffs — confirm the path change Splunk detected matches what the UI shows.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes — Path Stability Monitor"):
- Timeline: path change events plotted against time, showing when paths shifted for each agent-target pair.
- Table: agent | target | unique paths | impact level | avg latency (ms) | latency variability — sorted by impact level and unique path count.
- Drilldown to ThousandEyes Path Visualization for visual before/after comparison.

**Runbook** (owner: Network Operations / WAN Engineering):
1. Open the alert. Note the agent, target, and number of unique paths.
2. Open the ThousandEyes permalink to view the current and previous path topology.
3. Compare the two paths: identify which hops changed and whether the new path goes through a different ISP, PoP, or geographic region.
4. Check UC-5.9.1 (latency), UC-5.9.2 (loss), and UC-5.9.3 (jitter) for the same agent-target pair during the path change window. If performance degraded, the path change is the likely cause.
5. **If path changed AND performance degraded:** Escalate to the ISP or carrier responsible for the changed segment. Include ThousandEyes screenshots showing the old vs new path and the correlated latency increase.
6. **If path changed but performance is stable:** Log the change for awareness but don't escalate. The carrier may have optimized routing.
7. For SD-WAN environments: check whether the SD-WAN controller should be configured to prefer the original path or accept the new one.

### Step 5 — Troubleshooting

- **Every path shows multiple unique paths** — The path fingerprinting is too sensitive, capturing minor variations like TTL-expired response differences. Try hashing only the first N hops or ignoring the last hop (which may vary due to load balancing).

- **No path changes detected despite known routing events** — The polling interval may be too long (default 300 seconds) to capture brief path flaps that last < 5 minutes. Consider reducing the polling interval for critical paths, keeping API rate limits in mind.

- **`path_hash` field is empty or missing** — See Step 2 for how to compute it from raw hop data. The field availability depends on the app version.

- **All common troubleshooting** — See UC-5.9.5 and UC-5.9.1 Step 5 for path visualization collection, API polling, macro configuration, and general app troubleshooting.

## SPL

```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths values(path_hash) as path_list count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```

## Visualization

(1) Timeline/event viewer: path change events over time with agent, target, and timestamp — lets the NOC correlate path changes with latency spikes from UC-5.9.1. (2) Table: agent, target, unique path count, path hashes — sorted by most-changed paths. (3) Drilldown to ThousandEyes Path Visualization via `thousandeyes.permalink` for visual before/after comparison.

## Known False Positives

**ECMP path rotation.** On networks with Equal-Cost Multi-Path routing, consecutive test probes may take different paths through the same router's multiple egress interfaces. These are parallel paths through the same network, not routing changes. Distinguish by checking whether the paths diverge at the ECMP boundary and reconverge — this is different from a path that shifts to an entirely different ISP. Reduce noise by ignoring path changes where the first and last 3 hops remain the same (only the middle varies).

**Cloud provider internal routing optimization.** AWS, Azure, and GCP continuously optimize internal routing between availability zones and PoPs. Path visualization to cloud targets may show frequent changes as the cloud provider's SDN fabric rebalances. Distinguish by checking whether path changes occur after a cloud provider PoP boundary (the hops inside the cloud provider's network change, but the hops up to the cloud ingress remain stable). Generally benign if latency is stable.

**DNS-based load balancing to different backends.** If the target hostname resolves to different backend IPs via DNS load balancing, each resolution may route to a different physical server with a different path. Distinguish by checking whether `server.address` changes across rounds — if it does, the path change is expected. Pin the test to a specific IP if you want path stability monitoring for a specific backend.

**ThousandEyes agent network interface change.** If the Enterprise Agent host has multiple network interfaces and the default route flips (e.g., DHCP renewal assigns a different gateway), the first hop changes and the entire path looks different. Distinguish by checking whether the first hop (`hop_1` IP) changed — this indicates a source-side routing change, not a WAN path change.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Path Visualization — Understanding route changes](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/network-tests/)
- [BGP Route Changes and Network Path Instability — RIPE NCC](https://www.ripe.net/publications/docs/ripe-611)
