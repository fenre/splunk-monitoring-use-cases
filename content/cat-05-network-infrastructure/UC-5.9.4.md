<!-- AUTO-GENERATED from UC-5.9.4.json — DO NOT EDIT -->

---
id: "5.9.4"
title: "Agent-to-Agent Latency and Throughput"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.4 · Agent-to-Agent Latency and Throughput

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check how our office-to-office links perform in both directions, so we can tell exactly which side of the connection has a problem when things slow down.*

---

## Description

Measures bidirectional network performance between two ThousandEyes Enterprise Agents deployed at different sites, breaking down latency, loss, and jitter by direction (transmit, receive, round-trip). The directional split is critical for WAN troubleshooting — asymmetric routing, congested return paths, and half-duplex faults all produce direction-specific degradation that round-trip measurements alone would mask.

## Value

Site-to-site WAN links are the backbone of branch-office connectivity, and their quality directly governs SD-WAN overlay decisions, voice/video quality between offices, and inter-datacenter replication throughput. Agent-to-Agent tests measure the actual path between sites (not just to a cloud target), and the directional breakdown lets the NOC pinpoint whether the problem is on the outbound leg (TX — your ISP), the return leg (RX — the remote site's ISP), or symmetrical (the WAN circuit itself). This turns a 4-hour "who owns the problem" war room into a 10-minute triage with evidence.

## Implementation

Create Agent-to-Agent tests in ThousandEyes between Enterprise Agents at different sites. Both agents must be Enterprise Agents (Cloud Agents cannot be targets in Agent-to-Agent tests). Enable the Tests Stream — Metrics input if not already enabled. The `network.io.direction` attribute splits results into transmit, receive, and round-trip views.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Both endpoints must be Enterprise Agents** — Cloud Agents cannot serve as targets in Agent-to-Agent tests. Enterprise Agents require the ThousandEyes agent software installed on a supported Linux VM (Ubuntu 18.04+/RHEL 7+/CentOS 7+), Docker container, or Cisco hardware appliance (ISR, ASR, Catalyst 8000 with ThousandEyes agent module). Each agent needs: 2+ vCPU, 2+ GB RAM, outbound HTTPS to `*.thousandeyes.com`.
- **Agent-to-Agent tests configured** in ThousandEyes: **Cloud & Enterprise Agents → Test Settings → Add New Test → Agent to Agent**. Select the source agent, target agent, and protocol (TCP or UDP). TCP is recommended for testing actual application paths; UDP simulates VoIP/real-time traffic patterns.
- **Bidirectional firewall rules:** Agent-to-Agent tests require both agents to communicate with each other directly (not via ThousandEyes cloud). Ensure firewall rules allow traffic on the configured test port (default: TCP/UDP 49153) in BOTH directions between the two agent IPs.
- **Network path context:** know which WAN circuit, SD-WAN overlay, or VPN tunnel connects the two sites. This context is essential for Step 4 runbook triage — without it, you can see the degradation but cannot identify which circuit to investigate.

### Step 1 — Configure data collection
If the Tests Stream — Metrics input from UC-5.9.1 is already enabled and the stream scope includes Agent-to-Agent tests, no additional configuration is needed. Agent-to-Agent metrics flow through the same OTel stream.

To verify, check whether the stream was scoped to a specific test type when created. Navigate to **Inputs → Tests Stream — Metrics → Edit** and confirm that the Test Type filter includes "Cloud & Enterprise Agent Tests" (which encompasses both Agent-to-Server AND Agent-to-Agent). If it was filtered to Agent-to-Server only, broaden the scope or create a second stream input for Agent-to-Agent.

Verification — wait for one test round, then:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="agent-to-agent" earliest=-10m
| stats count by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
```
You should see three rows per agent pair: one each for `transmit`, `receive`, and `round-trip`. The `transmit` row shows performance from source→target; `receive` shows target→source; `round-trip` is the composite.

**Key difference from Agent-to-Server:** The `network.io.direction` attribute is unique to Agent-to-Agent tests. Agent-to-Server tests always report round-trip only. The directional split is the primary analytical value of this UC.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, network.io.direction
```

**Understanding this SPL**

`thousandeyes.test.type="agent-to-agent"` — filters to Agent-to-Agent tests only, excluding Agent-to-Server and other test types.

`by ... network.io.direction` — the critical split. Without this, TX and RX metrics would be averaged together, masking asymmetric path problems. By splitting on direction, you get three rows per agent pair:
- `transmit` — performance from source agent to target agent (outbound leg)
- `receive` — performance from target agent back to source agent (return leg)
- `round-trip` — the combined bidirectional metric

**Why this matters for troubleshooting:** If `transmit` shows 80 ms latency but `receive` shows 20 ms, the outbound ISP path is significantly longer or more congested than the return path. This pinpoints the problem to the source agent's ISP, not the WAN circuit itself.

`eval avg_latency_ms=round(avg_latency_s*1000,1)` — same v2 seconds-to-milliseconds conversion as UC-5.9.1.

`sort thousandeyes.source.agent.name, network.io.direction` — groups results by agent pair with all three directions adjacent, making it easy to compare TX vs RX at a glance.

**Asymmetry detection variant** — add this to the search to flag paths with significant directional asymmetry:
```spl
| eventstats avg(avg_latency_ms) as pair_avg by thousandeyes.source.agent.name, thousandeyes.target.agent.name
| eval asymmetry_pct = abs(avg_latency_ms - pair_avg) / pair_avg * 100
| where network.io.direction!="round-trip" AND asymmetry_pct > 30
```

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`. For alerting, filter to `where network.io.direction="round-trip" AND (avg_latency_ms > 100 OR avg_loss > 0.5)` to avoid double-alerting on TX+RX+round-trip for the same degradation. Throttle on `thousandeyes.source.agent.name` + `thousandeyes.target.agent.name` for 4 hours.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Agent to Agent** and select a specific agent pair. The view shows separate charts for TX, RX, and round-trip. Compare latency, loss, and jitter for each direction against Splunk results.

(b) **Direction parity.** For a test between two agents on the same LAN segment (if you have one for validation), all three directions should show nearly identical sub-1ms latency and 0% loss. Significant differences on a LAN pair indicate an agent configuration problem.

(c) **Firewall verification.** If `receive` direction shows 100% loss while `transmit` works, the target agent's firewall is blocking the return test traffic. Check firewall rules at the target site for the test port (default TCP/UDP 49153).

(d) **Field completeness.** `| fieldsummary` should show `network.io.direction` with `distinct_count=3` (transmit, receive, round-trip). If `network.io.direction` is missing, you may be looking at Agent-to-Server data misidentified as Agent-to-Agent — check `thousandeyes.test.type` values: `| stats count by thousandeyes.test.type`.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes — Site-to-Site WAN Quality"):
- Row 1 — Single value tiles: "WAN links > 100 ms round-trip" (red ≥ 1), "Links with TX/RX asymmetry > 30%" (yellow), "Links with loss > 0.5%" (red).
- Row 2 — Table: source agent | target agent | TX latency (ms) | RX latency (ms) | round-trip latency (ms) | asymmetry % | TX loss | RX loss — pivoted so each agent pair is one row with directional columns. Drilldown to ThousandEyes Path Visualization.
- Row 3 — Timechart: directional latency for a selected agent pair (use dropdown token). Three overlaid series: TX, RX, round-trip. This view immediately shows when asymmetric routing kicks in.
- Row 4 — Correlation panel: side-by-side with SD-WAN tunnel events (UC-5.5.x) if SD-WAN is deployed between the same sites.

**Runbook** (owner: Network Operations / WAN team):
1. Open the alert. Note the agent pair and which direction (TX/RX) is degraded.
2. Open the ThousandEyes Path Visualization via the permalink. Compare the forward and reverse path topologies.
3. **If TX degraded, RX normal:** The source site's ISP or uplink is the problem. Check the local circuit utilization, ISP status, and local router interfaces.
4. **If RX degraded, TX normal:** The target site's ISP or uplink is the problem. Contact the remote site's team or ISP.
5. **If both TX and RX degraded equally:** The WAN circuit or backbone is the problem. Check the WAN provider's status dashboard, open a circuit ticket.
6. **If only one direction shows loss but the other shows latency:** Suspect asymmetric routing — the two paths are going through different ISPs/PoPs. Compare the Path Visualization for each direction to confirm.
7. For SD-WAN environments: check whether the SD-WAN controller changed the active transport (MPLS → broadband → LTE) recently. Correlate with `index=sdwan sourcetype="cisco:sdwan:syslog" "tunnel"` if available.

### Step 5 — Troubleshooting

- **Only `round-trip` direction appears, no `transmit`/`receive`** — The test may be configured as a One-Way Agent-to-Agent test (only available with Enterprise Agents that have NTP synchronization). One-way tests report TX and RX separately; Two-Way tests report round-trip. Check the test configuration in ThousandEyes: **Test Settings → select the test → Direction**.

- **`receive` shows 100% loss consistently** — Firewall at the target site is blocking the return test traffic. The test sends UDP/TCP probes from source to target AND from target to source. Both directions must be allowed through firewalls. Check the test port (default 49153) is open inbound at BOTH sites.

- **Latency much higher than expected between sites on the same WAN** — Check whether the test is traversing the correct circuit. Enterprise Agents send test traffic from the host's default route, which may not be the WAN circuit you intend to test. Use static routes or policy-based routing to force test traffic onto the specific WAN interface.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, v1/v2 metric names, macro configuration, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, network.io.direction
```

## Visualization

(1) Table: source agent, target agent, direction, latency (ms), loss %, jitter (ms) — with colour-coding by quality thresholds. (2) Comparison bar chart: forward (TX) vs reverse (RX) latency for each agent pair — asymmetry > 20% signals routing issues. (3) Timechart: `| timechart span=5m avg(network.latency) as lat by network.io.direction` for a selected agent pair showing directional trends. (4) Drilldown to ThousandEyes Path Visualization via `thousandeyes.permalink` for per-hop analysis of each direction.

## Known False Positives

**Asymmetric routing causing directional disparity.** On many WAN links — especially those with multiple ISP uplinks or SD-WAN overlays — the forward and return paths take different routes through different ISPs. This makes TX and RX latency/loss differ significantly even when both paths are healthy. Distinguish from a real problem by baselining each direction independently over 7 days. If the asymmetry is stable and both directions meet SLA, it's by design.

**Enterprise Agent maintenance or reboot.** When one agent in the pair is rebooted (OS update, agent software upgrade), the test produces loss=100% and high latency for the duration. Distinguish by checking whether the agent's status in ThousandEyes → Agent Settings shows a restart event in the same time window. Suppress by requiring > 3 consecutive rounds of degradation before alerting.

**SD-WAN path selection oscillation.** SD-WAN controllers (Cisco vManage, Arista, Fortinet) continuously optimize path selection based on real-time quality. When the controller switches the active WAN link, Agent-to-Agent latency can spike for 1–2 rounds as the new path warms up. This is normal SD-WAN behavior. Distinguish by correlating with SD-WAN tunnel change events from UC-5.5.x.

**One-sided congestion at branch offices.** Branch offices often have asymmetric bandwidth (e.g., 100 Mbps down / 20 Mbps up). The TX direction from the branch shows higher loss during peak hours because the upload circuit saturates. This is a capacity issue, not a fault — correlate with circuit utilization data.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 Data Model — Agent-to-Agent metrics and direction attribute](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [ThousandEyes Agent-to-Agent Test Configuration](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/network-tests/agent-to-agent-test)
