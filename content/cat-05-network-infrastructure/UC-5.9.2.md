<!-- AUTO-GENERATED from UC-5.9.2.json — DO NOT EDIT -->

---
id: "5.9.2"
title: "Network Packet Loss Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.2 · Network Packet Loss Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track packet loss on the paths that matter, because even a tiny amount of lost data can make calls choppy, video freeze, and web pages load wrong.*

---

## Description

Flags Agent-to-Server paths where average packet loss exceeds 0.5% over the search window, ranked worst-first. Even sub-1% packet loss devastates TCP throughput (retransmissions compound exponentially) and makes real-time protocols like VoIP, video, and RDP unusable — this search catches the degradation before the help desk lights up.

## Value

When a path drops packets, the application layer retransmits, and every retransmission adds one full round-trip of latency on top of the loss itself. A 1% loss rate on a 100 ms path effectively doubles perceived latency for bulk transfers and causes audible clicks in VoIP calls (MOS drops below 3.5). Catching the loss in Splunk first lets the NOC open the ThousandEyes Path Visualization to identify the exact lossy hop — whether it's a congested peering point, a failing interface, or a carrier circuit at capacity — and route around it or escalate with evidence before users start calling.

## Implementation

Uses the same Tests Stream — Metrics input as UC-5.9.1. If that input is already enabled, no additional data collection setup is needed — `network.loss` arrives in the same OTel events as `network.latency`. Update the `stream_index` macro if you used a custom index name. Schedule the search every 15 minutes over the last 1 hour, trigger when results > 0, throttle by `thousandeyes.source.agent.name` + `server.address` for 4 hours.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.1 apply — the `ta_cisco_thousandeyes` app must be installed, OAuth authenticated, HEC configured, and the Tests Stream — Metrics input enabled with Agent-to-Server tests streaming to `thousandeyes_metrics`. If you implemented UC-5.9.1, no additional data collection setup is needed for this UC — `network.loss` arrives in the same OTel events as `network.latency`.
- **ThousandEyes Agent-to-Server tests** must be configured with ICMP or TCP protocol. The default protocol is ICMP; be aware that some paths deprioritize ICMP (see Known False Positives). For loss-sensitive monitoring of critical application paths, configure the test with **TCP** on the application's actual port (e.g., TCP 443 for HTTPS targets) — this gives a more representative loss measurement.
- Splunk role with `srchIndexesAllowed` including `thousandeyes_metrics`.
- Baseline knowledge: expected normal packet loss per path type. Same-datacenter paths should be 0.000%. Same-metro WAN paths should be < 0.01%. Cross-continental paths may show 0.01–0.1% baseline. Anything above 0.5% sustained is almost always a problem.

### Step 1 — Configure data collection
If the Tests Stream — Metrics input from UC-5.9.1 is already enabled, no additional configuration is needed. The `network.loss` metric is delivered in the same OTel events as `network.latency` and `network.jitter`.

If you have not yet set up data collection, follow UC-5.9.1 Step 1 in full. After enabling the stream, verify that `network.loss` is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="agent-to-server" earliest=-10m
| stats avg(network.loss) as avg_loss by thousandeyes.source.agent.name
| where isnotnull(avg_loss)
```
You should see one row per agent with a loss percentage. If `network.loss` is null but `network.latency` is populated, the test may be configured in a mode that doesn't report loss (unlikely for Agent-to-Server but possible for some Enterprise Agent proxy configurations).

**Understanding the metric:** `network.loss` in OTel v2 is a percentage (0–100), NOT a ratio (0–1). A value of `0.5` means 0.5% packet loss, not 50%. This differs from some monitoring tools that use ratio format. The SPL threshold `where avg_loss > 0.5` means "flag paths with more than half a percent loss" — no unit conversion needed.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.loss) as avg_loss max(network.loss) as max_loss by thousandeyes.source.agent.name, server.address
| where avg_loss > 0.5
| sort -avg_loss
```

**Understanding this SPL**

`stream_index` — expands to `index=thousandeyes_metrics` (the app-defined macro).

`thousandeyes.test.type="agent-to-server"` — filters to Agent-to-Server tests. The same `network.loss` metric also appears in Agent-to-Agent tests (UC-5.9.4) but with different resource attributes.

`stats avg(network.loss) as avg_loss max(network.loss) as max_loss` — computes both average and maximum loss for each agent-target pair. Why both: average loss tells you the sustained quality of a path (TCP throughput is governed by sustained loss rate via the TCP throughput equation: `throughput ≈ MSS / (RTT × √loss)`). Maximum loss captures burst events — a 30-second burst of 10% loss during a video call is devastating even if the hourly average is 0.3%. Presenting both helps the NOC distinguish chronic path degradation from transient bursts.

`where avg_loss > 0.5` — 0.5% average packet loss is the threshold where TCP throughput measurably degrades and VoIP quality drops below acceptable levels (ITU-T G.114 recommends < 1% for voice; Cisco design guides recommend < 0.5% for video). For your environment, tune this: 0.1% for latency-sensitive financial trading paths, 1% for bulk backup paths. Consider maintaining a `thousandeyes_loss_thresholds` lookup with per-path thresholds for differentiated SLAs.

`sort -avg_loss` — worst-first so the most degraded path appears at the top of the table.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`. Trigger on "Number of results > 0". Throttle on `thousandeyes.source.agent.name` + `server.address` for 4 hours. For high-urgency paths (e.g., trading floor to exchange), consider a tighter schedule (`*/5 * * * *` with `-15m` window) and immediate paging.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Agent to Server** and select the same time window. Click on a specific agent-target pair and note the **Loss %** column. In Splunk, run:
```spl
`stream_index` thousandeyes.test.type="agent-to-server" thousandeyes.source.agent.name="<agent>" server.address="<target>" earliest=-1h
| stats avg(network.loss) as avg_loss
```
The values should match to within 0.1% (rounding and timing differences).

(b) **Zero-loss baseline.** Pick a known healthy same-datacenter path. Splunk should show `avg_loss=0.0` or very close to it. If a local path shows loss, the problem is either the agent host (NIC drops, hypervisor overcommit) or a local switch/router issue — not the wide-area network.

(c) **Known-lossy path.** If you have a path you know experiences loss (e.g., a congested cross-continental WAN link), verify Splunk shows a non-zero `avg_loss` consistent with what you observe in ThousandEyes.

(d) **Field completeness.** `index=thousandeyes_metrics thousandeyes.test.type="agent-to-server" earliest=-5m | fieldsummary | search field=network.loss` should show `count > 0` and `distinct_count >= 1`. If `network.loss` is entirely absent, check whether the stream is delivering v1 data (field name `net.metrics.loss`) — see UC-5.9.1 Step 5 troubleshooting for the v1/v2 check.

(e) **Distinguish from total unreachability.** A `network.loss` of 100% means the target is completely unreachable from that agent — this is a different class of event than partial loss. Consider adding a separate alert for `where max_loss >= 100` as a hard-down indicator with immediate paging.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes — Packet Loss Overview" or add as a row in the UC-5.9.1 latency dashboard):
- Row 1 — Single value tiles: "Paths > 0.5% loss" (red threshold ≥ 1), "Paths > 2% loss" (red, critical), "Unreachable paths (100% loss)" (red, links to filtered view).
- Row 2 — Sortable table: agent name | server address | avg loss % | max loss % | agent location — sorted worst-first. Colour-code the `avg_loss` column: green < 0.1, yellow 0.1–0.5, orange 0.5–2, red > 2. Drilldown to `thousandeyes.permalink`.
- Row 3 — Timechart: loss % per agent over 24 hours at 5-minute granularity. Use area chart with stacked fills — sustained elevated areas indicate circuit faults; narrow spikes indicate congestion bursts.
- Row 4 — Correlation panel: side-by-side timecharts of `network.loss` and `network.latency` for the same path, showing how loss and latency co-occur (congestion) or diverge (different root causes).

**Alerting:**
- > 0.5% avg loss → low-urgency notification (Slack/Teams `#network-ops`), 4-hour suppression per path.
- > 2% avg loss or 100% max loss → high-urgency page (PagerDuty/On-Call) with immediate escalation. Include the `thousandeyes.permalink` URL and the agent/target pair in the alert payload.

**Runbook** (owner: Network Operations on-call):
1. Open the alert. Note the agent, target, avg loss %, and max loss %.
2. Click the `thousandeyes.permalink` to open ThousandEyes Path Visualization. Identify which hop in the path shows per-hop packet loss (red circles in the path diagram).
3. **If loss is at a single intermediate hop (ISP/carrier):** Open a ticket with the carrier. Include the ThousandEyes permalink as evidence showing the exact router interface IP, loss percentage, and time window.
4. **If loss is at the last hop (target server):** The server or its local network is the bottleneck. Check server-side NIC stats (`ethtool -S eth0 | grep drop` on Linux, `netstat -e` on Windows) and local switch interface counters.
5. **If loss affects multiple agents to the same target:** The problem is near the target end. Check load balancer health, server NIC saturation, or target-side firewall rate limiting.
6. **If loss affects one agent to multiple targets:** The problem is near the agent end. Check the agent's uplink circuit, local switch, or ISP last-mile.
7. **If loss is 100% (unreachable):** This is a hard down — escalate to UC-5.9.18 (Network Outage Event Detection) investigation. Check whether ThousandEyes also generated an event/alert for this path.
8. Correlate with UC-5.9.1 (latency) and UC-5.9.3 (jitter) — if all three degrade simultaneously, the cause is likely congestion. If only loss degrades while latency is stable, suspect a failing interface (CRC errors, buffer overruns) rather than congestion.

### Step 5 — Troubleshooting

- **`network.loss` always reads 0.0 for all paths** — This is likely correct! Well-provisioned networks with dedicated circuits should show 0% loss. Only flag this as a problem if you know some paths should be showing loss. If you're testing lossy paths and still see 0%, check whether the test interval is long enough to capture loss events (default 1-minute rounds should be sufficient).

- **Loss seems unrealistically high on some paths** — ICMP deprioritization. Some ISPs (notably Comcast, AT&T on consumer circuits) and corporate firewalls rate-limit or deprioritize ICMP. The Agent-to-Server test default protocol is ICMP, so the measured loss reflects ICMP treatment, not application-layer reality. Fix: switch the ThousandEyes test to TCP mode (`Test Settings → Protocol → TCP`) on the application port. Compare ICMP vs TCP loss for the same path to quantify the discrepancy.

- **Sporadic 100% loss for one round then recovery** — Agent-side transient. The agent process was briefly blocked (VM snapshot, GC pause on the agent host). If this happens more than once per day, increase the agent VM's CPU/memory allocation. You can filter single-round spikes by adding `| where avg_loss < 100` or requiring two consecutive rounds above threshold.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth token refresh, v1/v2 metric name mismatches, stream_index macro configuration, and role permissions. The same issues apply to all metrics from the Tests Stream — Metrics input.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.loss) as avg_loss max(network.loss) as max_loss by thousandeyes.source.agent.name, server.address
| where avg_loss > 0.5
| sort -avg_loss
```

## Visualization

(1) Sortable table: agent name, server address, avg loss %, max loss % — sorted worst-first so the most lossy paths are immediately visible. Colour-code: green (< 0.1%), yellow (0.1–0.5%), orange (0.5–2%), red (> 2%). (2) Single value tile: count of paths exceeding 0.5% loss (red threshold ≥ 1). (3) Timechart: `| timechart span=5m avg(network.loss) as avg_loss by thousandeyes.source.agent.name` — useful for spotting whether loss is sustained (circuit fault) or bursty (congestion window). (4) Combined panel with UC-5.9.1 latency and UC-5.9.3 jitter for a complete path quality picture. (5) Drilldown: click a row to open `thousandeyes.permalink` in ThousandEyes for per-hop loss analysis.

## Known False Positives

**Last-mile ISP congestion during peak hours.** Shared cable/DSL/fibre-to-the-building last-mile links commonly drop 0.5–2% of packets during evening peaks (18:00–22:00 local) or business-hour peaks for office circuits. Distinguish from a circuit fault by checking whether the loss follows a daily pattern (`| timechart span=1h avg(network.loss) by date_hour` over 7 days) and whether it affects all agents on the same ISP. Tune by raising the threshold to 1% for known shared-media paths.

**Cloud provider maintenance.** AWS, Azure, and GCP occasionally perform network maintenance that causes transient packet loss (typically < 5 minutes). Distinguish by correlating with cloud provider status pages and checking whether loss affects multiple agents targeting the same cloud region simultaneously. Suppress with a `cloud_maintenance_windows` lookup.

**ICMP deprioritization.** Some ISPs and firewalls deprioritize or rate-limit ICMP packets, which Agent-to-Server tests use by default. This makes the measured loss higher than what TCP/UDP application traffic actually experiences on the same path. Distinguish by comparing with HTTP Server test results (UC-5.9.34) — if HTTP availability is 100% but network loss shows 2%, ICMP is being deprioritized. Fix by switching the ThousandEyes test to TCP mode on a specific port.

**Enterprise Agent host packet drops.** If the Enterprise Agent VM's virtual NIC buffer is undersized or the host hypervisor is overcommitted, the agent itself drops packets before they reach the network. Distinguish by comparing Cloud Agent results to the same target — if Cloud Agents show 0% loss while the Enterprise Agent shows loss, the problem is local. Fix by increasing the VM's NIC ring buffer (`ethtool -G eth0 rx 4096`) or reducing hypervisor overcommit.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 Data Model — Agent-to-Server metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [ThousandEyes Splunk App — Inputs Documentation](https://docs.thousandeyes.com/product-documentation/integration-guides/custom-built-integrations/splunk-app/inputs)
- [Impact of Packet Loss on TCP Throughput (RFC 3649 background)](https://www.rfc-editor.org/rfc/rfc3649)
