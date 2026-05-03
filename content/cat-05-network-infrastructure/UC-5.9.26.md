<!-- AUTO-GENERATED from UC-5.9.26.json — DO NOT EDIT -->

---
id: "5.9.26"
title: "VPN Path Performance"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.26 · VPN Path Performance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how well the secure tunnel (VPN) that connects each employee's computer to the company network is working, so we can tell whether slowness is coming from their home internet or from the tunnel itself.*

---

## Description

Monitors VPN connection quality from the Endpoint Agent's perspective — measuring latency, loss, and composite score between the user's device and the VPN concentrator. Groups by VPN vendor and concentrator to identify whether VPN performance issues are client-specific, concentrator-specific, or vendor-wide.

## Value

VPN is the most complained-about infrastructure component in hybrid workplaces. Users say "VPN is slow" but can't articulate whether the problem is their home Wi-Fi (UC-5.9.25), the VPN tunnel itself (this UC), or the application behind the VPN. By measuring the VPN hop independently, this UC isolates VPN tunnel performance from the rest of the path. If the gateway score (UC-5.9.25) is healthy but the VPN score is degraded, the problem is between the user's ISP and the VPN concentrator (geographic distance, ISP peering, or concentrator overload). If both gateway and VPN scores are degraded, the problem originates at the user's local network. This isolation saves the VPN team from chasing phantom issues and provides data-driven decisions for VPN architecture changes (concentrator placement, split-tunnel policies, vendor migration).

## Implementation

Uses the same Endpoint Agent data stream as UC-5.9.24. Filter by `target.type="vpn"` to focus on VPN hop metrics. The `vpn.vendor` attribute identifies the VPN client in use.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.24 apply — Endpoint Agents deployed, data streaming to Splunk.
- **Users connecting via VPN.** This UC only produces data when users have an active VPN connection. In always-on VPN environments, data is continuous. In on-demand VPN environments, data appears only during VPN sessions.

### Step 1 — Configure data collection
Same as UC-5.9.24.

Verify VPN data:
```spl
index=thousandeyes_metrics thousandeyes.test.domain="endpoint" target.type="vpn"
| stats dc(thousandeyes.source.agent.name) as agents count by vpn.vendor, server.address
| sort -agents
```
This shows VPN vendors and concentrators in use.

### Step 2 — Create the search
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, vpn.vendor, server.address, thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1)
| where avg_score < 0.7 OR avg_loss > 1
| sort avg_score
```

**VPN concentrator health** (aggregated view):
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn" earliest=-4h
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency dc(thousandeyes.source.agent.name) as user_count by server.address, vpn.vendor
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```
Low scores on a specific `server.address` with many users indicates a concentrator capacity issue.

**Gateway vs VPN comparison** (isolates VPN-specific problems):
```spl
`stream_index` thousandeyes.test.domain="endpoint" (target.type="gateway" OR target.type="vpn") earliest=-4h
| stats avg(network.score) as avg_score by thousandeyes.source.agent.name, target.type
| xyseries thousandeyes.source.agent.name target.type avg_score
| rename gateway as gw_score, vpn as vpn_score
| eval vpn_degradation=round(gw_score - vpn_score, 2)
| where vpn_degradation > 0.2
| sort -vpn_degradation
```
Endpoints where the VPN score is significantly worse than the gateway score have VPN-specific problems.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`.

### Step 3 — Validate
(a) Test with a known VPN connection. Connect to VPN on a device with the Endpoint Agent and verify data appears with `target.type="vpn"` and the correct `vpn.vendor`.
(b) Compare latency values with a manual `ping` to the VPN concentrator.
(c) Cross-reference with ThousandEyes UI: **Endpoint Agents → Views → Network Access → filter by Target Type: VPN**.

### Step 4 — Operationalize
**Dashboard** ("VPN Performance" or panel in "Endpoint Experience Overview"):
- Concentrator scoreboard: avg score, user count, avg latency per concentrator.
- Gateway vs VPN comparison: identifies VPN-specific degradation.
- Worst endpoints table.

**Runbook** (owner: network / VPN team):
1. VPN score degraded but gateway score healthy → VPN tunnel or concentrator issue.
   a. Check concentrator capacity (session count, CPU, memory).
   b. Check ISP peering between user's ISP and the concentrator's ISP.
   c. Consider adding concentrators in additional regions.
2. Both VPN and gateway scores degraded → local network issue (UC-5.9.25).
3. Specific VPN vendor showing consistently lower scores → evaluate vendor alternatives or configuration tuning.
4. VPN latency > 200 ms → user is likely connecting to a geographically distant concentrator. Enable geo-based VPN server selection.

### Step 5 — Troubleshooting
- **No VPN data** — Users may not be connected to VPN (split-tunnel, office workers, direct internet access). Check your VPN deployment model.

- **`vpn.vendor` shows as empty or unknown** — The Endpoint Agent may not recognize the VPN client. Check supported VPN vendors in the ThousandEyes Endpoint Agent documentation.

- See UC-5.9.24 Step 5 for general endpoint data troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, vpn.vendor, server.address, thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1)
| where avg_score < 0.7 OR avg_loss > 1
| sort avg_score
```

## Visualization

(1) Table: endpoints sorted by VPN score, showing vendor, concentrator, latency, loss. (2) Bar chart: average VPN score by concentrator (identifies overloaded concentrators). (3) Comparison chart: gateway score vs VPN score per endpoint (isolates VPN-specific issues). (4) Timechart: VPN score by vendor over 24 hours.

## Known False Positives

**VPN not active.** If a user isn't connected to VPN, no `target.type="vpn"` data is produced. The absence of VPN data doesn't indicate a problem — the user may be on a split-tunnel configuration or working from the office.

**VPN reconnection bursts.** When a VPN session drops and reconnects, there may be a brief period of high latency / loss during the handshake. This is normal for VPN reconnections, especially when switching networks (e.g., Wi-Fi to cellular).

**VPN concentrator geographic distance.** Users connecting to a VPN concentrator in a different continent will inherently have higher latency. This is expected physics, not a problem. Compare with other users connecting to the same concentrator from the same region.

**Split-tunnel vs full-tunnel.** In split-tunnel VPN, only corporate traffic traverses the VPN tunnel. The VPN metrics reflect tunnel performance, but internet-bound traffic bypasses VPN entirely. This means a low VPN score doesn't affect internet browsing but does affect corporate app access.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Endpoint Local Network VPN attributes](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
