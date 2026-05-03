<!-- AUTO-GENERATED from UC-5.9.29.json — DO NOT EDIT -->

---
id: "5.9.29"
title: "SD-WAN Overlay vs Underlay Performance"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.29 · SD-WAN Overlay vs Underlay Performance

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We compare how fast traffic moves through our smart network routing system (SD-WAN) versus the raw internet connection underneath it, so we can tell whether the smart system is helping or actually making things slower.*

---

## Description

Compares SD-WAN overlay (fabric-routed) path performance against the raw underlay (transport-level) path performance to quantify the overhead introduced by the SD-WAN fabric. By running parallel ThousandEyes tests — one through the overlay, one against the underlay — this UC isolates whether performance issues originate in the SD-WAN fabric (policy routing, encryption, tunneling overhead) or in the underlying transport (ISP, MPLS, broadband).

## Value

SD-WAN vendors promise intelligent path selection, but operators need data to verify. If overlay latency is 50 ms but underlay latency is only 10 ms, the SD-WAN fabric is adding 40 ms of overhead — a critical finding for real-time applications. Conversely, if overlay and underlay latency are nearly identical, the SD-WAN is performing well and any application slowness is due to other factors. This comparison is essential for: (1) validating SD-WAN POC performance claims, (2) diagnosing application performance issues ("is SD-WAN the bottleneck?"), (3) justifying transport upgrades (if the underlay is degraded, upgrading to a better circuit is the fix, not changing SD-WAN vendors), and (4) detecting SD-WAN fabric failures (if overlay latency spikes while underlay remains stable, the fabric has a problem).

## Implementation

Requires deliberate test design: create paired Agent-to-Server tests at each SD-WAN site — one routed through the overlay fabric, one targeting the underlay transport directly. Use consistent naming conventions (e.g., "SiteA-HubDC-Overlay" and "SiteA-ISP-Underlay") so SPL can categorize them.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Enterprise Agents deployed at SD-WAN sites.** ThousandEyes Enterprise Agents must be installed at branch sites (behind the SD-WAN edge device, so traffic naturally traverses the SD-WAN fabric) AND at hub/data center sites. Deploy agents as VMs or Docker containers on local compute (a dedicated Linux VM with 2 vCPU / 2 GB RAM per agent is recommended). The agent must sit on a VLAN that is subject to SD-WAN policy routing — if the agent is on a management VLAN that bypasses SD-WAN, overlay tests won't actually traverse the fabric.
- **Paired test design — this is the critical step.** For each site-to-hub path, create TWO Agent-to-Server tests:
  - **Overlay test:** target the hub/DC application server IP. Traffic routes through the SD-WAN fabric via normal policy (e.g., via vEdge/cEdge). Name: `SiteA-HubDC-Overlay`. The target IP should be one that the SD-WAN fabric routes — typically a server in the data center reachable via the IPSEC/GRE tunnel.
  - **Underlay test:** target the raw transport endpoint — the MPLS PE router IP, the DIA next-hop gateway, or the broadband ISP's first hop. Name: `SiteA-MPLS-Underlay` or `SiteA-DIA-Underlay`. This traffic should NOT traverse the SD-WAN tunnel — configure the test to use a specific source interface on the agent host that bypasses SD-WAN, OR target an IP that the SD-WAN policy does not steer into the overlay.
  - **Alternative: ThousandEyes tags.** Instead of name-matching, apply tags in ThousandEyes (e.g., `path:overlay`, `path:underlay`) and use the tag attributes in SPL. Tags are more reliable than name-matching but require ThousandEyes account admin access.
- **Know your SD-WAN topology:** document which transport links (MPLS, DIA, broadband, LTE) are available at each site, and which SLA policy governs traffic steering. Without this, you can't interpret overlay premium values correctly.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Both overlay and underlay tests flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify that paired tests exist and data is flowing:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*") earliest=-30m
| stats dc(thousandeyes.test.name) as tests values(thousandeyes.test.name) as test_names by thousandeyes.source.agent.name
| sort thousandeyes.source.agent.name
```
Each agent (site) should have at least one overlay and one underlay test. If an agent shows only overlay tests, the underlay test hasn't been created yet. If it shows only underlay tests, the overlay test either doesn't exist or the test isn't traversing the agent (the agent may be on a management VLAN).

**Understanding the data model for this UC:**
- Both overlay and underlay tests produce identical metrics: `network.latency` (seconds), `network.loss` (percentage), `network.jitter` (milliseconds). The difference is purely in the network path they traverse — the SD-WAN fabric vs the raw transport.
- The `thousandeyes.test.name` attribute is the primary differentiator. The SPL extracts `path_type` from the test name using regex matching.
- Consider also checking `thousandeyes.source.agent.name` to identify which site each test belongs to, enabling per-site overlay premium analysis.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*")
| eval path_type=if(match(thousandeyes.test.name, "(?i)overlay"), "Overlay", "Underlay")
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address, path_type
| eval avg_latency_ms=round(avg_latency*1000,1)
| xyseries thousandeyes.source.agent.name path_type avg_latency_ms
| eval overlay_premium_ms=round(Overlay - Underlay, 1)
| sort -overlay_premium_ms
```

**Understanding this SPL**

`(thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*")` — selects only the paired SD-WAN tests. This relies on consistent naming. If you use tags instead: `thousandeyes.test.tags="path:overlay" OR thousandeyes.test.tags="path:underlay"`.

`eval path_type=if(match(...))` — classifies each test as Overlay or Underlay. The `(?i)` flag makes the match case-insensitive.

`stats avg(network.latency) ... by thousandeyes.source.agent.name, server.address, path_type` — computes average metrics per agent per path type. Note: `network.latency` is in seconds (OTel v2), so we multiply by 1000 for milliseconds.

`xyseries thousandeyes.source.agent.name path_type avg_latency_ms` — pivots the table so each row is a site with Overlay and Underlay columns side-by-side.

`eval overlay_premium_ms=round(Overlay - Underlay, 1)` — the key metric: how many milliseconds the SD-WAN fabric adds. Positive = overlay is slower (expected). Negative = overlay is faster (SD-WAN is routing via a better transport — correct behavior).

**Time-series overlay premium** (trend the gap over time to catch gradual fabric degradation):
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*")
| eval path_type=if(match(thousandeyes.test.name, "(?i)overlay"), "Overlay", "Underlay")
| timechart span=1h avg(network.latency) as avg_latency by path_type
| eval overlay_ms=round(Overlay*1000,1), underlay_ms=round(Underlay*1000,1)
| eval premium_ms=overlay_ms - underlay_ms
```

**Per-metric comparison** (full picture — latency, loss, jitter each compared):
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*")
| eval path_type=if(match(thousandeyes.test.name, "(?i)overlay"), "Overlay", "Underlay")
| stats avg(network.latency) as latency_s avg(network.loss) as loss_pct avg(network.jitter) as jitter_ms by thousandeyes.source.agent.name, path_type
| eval latency_ms=round(latency_s*1000,1)
```

**Scheduling:** cron `*/30 * * * *`, time range `-1h to now`. Trigger on `overlay_premium_ms > 20`. Throttle by `thousandeyes.source.agent.name` for 4 hours. A 20 ms premium is the threshold where real-time applications (VoIP, video) start experiencing quality degradation attributable to the fabric.

### Step 3 — Validate
(a) **Verify overlay path.** Use ThousandEyes path visualization (UC-5.9.5 / UC-5.9.33) for the overlay test. The path should show SD-WAN tunnel endpoints (typically the cEdge/vEdge loopback IPs) as intermediate hops. If the path looks like a normal internet path without tunnel endpoints, the test traffic is NOT traversing the SD-WAN fabric — the agent may be on a wrong VLAN.

(b) **Verify underlay path.** Path visualization for the underlay test should show a simpler path — direct ISP hops without tunnel encapsulation. If the underlay path also shows tunnel endpoints, the test is accidentally going through the overlay.

(c) **Baseline overlay premium.** Run the search over a 24-hour period during low-traffic hours. Expected premiums:
  - IPsec encryption overhead: 1–3 ms.
  - GRE tunneling: 0.5–1 ms.
  - SD-WAN controller policy lookup: 0.5–2 ms.
  - Total expected: **2–6 ms** for a well-functioning SD-WAN fabric.
  - 5–15 ms: elevated but acceptable for most non-real-time applications.
  - > 15 ms: investigate SD-WAN controller, edge device CPU, or fabric congestion.

(d) **Cross-reference SD-WAN dashboard.** If you also collect Cisco SD-WAN data via `TA_cisco_catalyst` (UC-5.13.x), compare the ThousandEyes overlay premium with SD-WAN tunnel statistics (tunnel latency, jitter from vManage API). They should be consistent.

(e) **Confirm unit conversion.** `network.latency` in OTel v2 is seconds. Verify by checking a known path: `| stats avg(network.latency) as raw | eval ms=raw*1000`. The `ms` value should match what ThousandEyes UI shows in the Agent-to-Server view.

### Step 4 — Operationalize
**Dashboard** ("SD-WAN Overlay Health" — designed for SD-WAN operations team):
- Row 1 — Single value tiles: "Sites with overlay premium > 15 ms" (red ≥ 1), "Average overlay premium across all sites" (green < 5, yellow < 15, red ≥ 15), "Sites with overlay packet loss > underlay" (red ≥ 1).
- Row 2 — Side-by-side bar chart: overlay vs underlay latency per site. Stacked or grouped bars, colour-coded (blue = overlay, grey = underlay). Sort by overlay premium descending so the most problematic site appears first.
- Row 3 — Timechart: overlay and underlay latency trending for a selected site (use a dropdown token for site selection). Dual-line chart with area fill to visually separate the two paths. Add a reference line at the 15 ms premium threshold.
- Row 4 — Detailed table: site | overlay latency | underlay latency | overlay premium | overlay loss | underlay loss | overlay jitter | underlay jitter — sorted by overlay premium descending. Colour-code cells (green < 5 ms premium, yellow 5–15, red > 15).

**Alerting:**
- Overlay premium > 15 ms sustained for 1 hour → low-urgency Slack/Teams notification to `#sd-wan-ops`. Include the site name, premium value, and ThousandEyes permalink.
- Overlay premium > 30 ms OR overlay loss > 2% when underlay loss < 0.5% → high-urgency page (PagerDuty). This indicates a failing SD-WAN fabric component.
- Overlay premium negative for > 4 hours → informational notification (the SD-WAN is actively optimizing path selection — good news, but worth noting).

**Runbook** (owner: SD-WAN / network architecture team):
1. **High overlay premium, stable underlay** → SD-WAN fabric issue. Check: (a) SD-WAN controller (vManage/vSmart) health — CPU, memory, tunnel count. (b) Edge device (cEdge/vEdge) CPU — high CPU causes forwarding delays in the data plane. (c) SD-WAN policy conflicts — check if application-aware routing (AAR) policies are misconfigured, causing traffic to take suboptimal paths. (d) Fabric congestion — if many tunnels share the same underlay transport, the encrypted tunnel overhead may saturate the link.
2. **High overlay AND high underlay latency** → the underlying transport is degraded. Contact the ISP/MPLS provider. The SD-WAN is not the problem — it's faithfully reflecting the bad transport. Check UC-5.9.1 for the underlay path.
3. **Overlay shows packet loss but underlay doesn't** → tunnel instability. Possible causes: (a) Edge device dropping packets under load (check `show sdwan tunnel statistics`). (b) MTU mismatch — PMTUD failure causing fragmentation. (c) NAT/firewall between sites dropping encapsulated packets.
4. **Overlay premium fluctuates widely** → SD-WAN path switching. The fabric is alternating between transports (MPLS ↔ DIA ↔ broadband). Check SLA policy thresholds — they may be too sensitive, causing flapping.
5. **Underlay shows different latency on different transports** → expected. MPLS typically has lower latency than broadband. The SD-WAN should prefer the lower-latency transport for real-time apps.
6. **Negative overlay premium** → SD-WAN is routing through a better transport than the one you're testing for underlay. This is correct behavior — the overlay is optimizing. Verify by checking which underlay transport the overlay is currently using.

### Step 5 — Troubleshooting

- **No underlay test data** — Underlay tests must be explicitly created in ThousandEyes. SD-WAN overlay tests are NOT automatically paired with underlay tests. Create Agent-to-Server tests targeting each transport's next-hop IP.

- **Overlay premium is always exactly 0 ms** — Both tests may be traversing the same path. Verify with path visualization that the overlay test actually goes through the SD-WAN tunnel. If the agent is on a management VLAN, it may bypass SD-WAN policy entirely.

- **Overlay premium is negative (overlay faster than underlay)** — This is not an error. The SD-WAN may be routing via a faster transport (e.g., DIA instead of congested MPLS). If the negative premium is persistent, your underlay test may be targeting the wrong transport endpoint.

- **`xyseries` produces null columns** — If test naming is inconsistent (some tests don't contain "overlay" or "underlay" in the name), the `path_type` eval won't classify them. Check `| stats values(thousandeyes.test.name)` to verify naming. Alternatively, switch to tag-based classification.

- **Path visualization shows unexpected intermediate hops** — The overlay test may be going through a transit SD-WAN hub instead of a direct tunnel. Check the SD-WAN topology — hub-and-spoke vs full-mesh — and verify the test path matches your expected topology.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, v1/v2 field name differences, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*")
| eval path_type=if(match(thousandeyes.test.name, "(?i)overlay"), "Overlay", "Underlay")
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address, path_type
| eval avg_latency_ms=round(avg_latency*1000,1)
| xyseries thousandeyes.source.agent.name path_type avg_latency_ms
| eval overlay_premium_ms=round(Overlay - Underlay, 1)
| sort -overlay_premium_ms
```

## Visualization

(1) Side-by-side bar chart: overlay vs underlay latency per site. (2) Table: site, overlay latency, underlay latency, overlay premium (difference). (3) Timechart: overlay and underlay latency trending for a specific site. (4) Single value: average overlay premium across all sites.

## Known False Positives

**Overlay path selection differences.** The SD-WAN fabric may route overlay traffic through a different underlay transport than the one you're testing. For example, your underlay test hits the MPLS PE, but the overlay currently routes via the broadband link. The comparison is only valid when you know which underlay transport the overlay is using.

**Overlay encryption overhead.** IPsec encryption in the SD-WAN tunnel adds 1–3 ms of latency. This is expected and not a performance problem — it's the cost of encryption. Only flag overlay premium > 10 ms as potentially problematic.

**SD-WAN path failover during measurement.** If the SD-WAN fabric switches from MPLS to broadband mid-test, the overlay measurement reflects a blended result. Use short measurement intervals and look at per-round data rather than averages.

**Test naming inconsistency.** The SPL relies on test names containing "overlay" or "underlay." If naming conventions aren't followed, the `path_type` classification will be wrong. Alternatively, use ThousandEyes tags instead of name matching.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes SD-WAN monitoring best practices](https://www.thousandeyes.com/solutions/sd-wan)
- [ThousandEyes OTel v2 — Network metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
