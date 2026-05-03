<!-- AUTO-GENERATED from UC-5.9.3.json — DO NOT EDIT -->

---
id: "5.9.3"
title: "Network Jitter Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.3 · Network Jitter Monitoring

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch how much packet timing wiggles on our network paths, because uneven delay makes voice calls crackle and video freeze even when the connection speed looks fine.*

---

## Description

Flags Agent-to-Server paths where average jitter (variation in packet delay) exceeds 30 ms, ranked worst-first. Jitter above 30 ms degrades voice quality even when mean latency is acceptable, because jitter buffers overflow and packets arrive too late to be played back, causing clicks, garbled audio, and frozen video frames.

## Value

A VoIP call over a 50 ms latency path with 5 ms jitter sounds fine; the same 50 ms path with 40 ms jitter sounds terrible — drops, clicks, and one-way audio that make callers hang up and call back on their mobile. Video conferencing is even more sensitive: 30+ ms jitter causes visible frame freezing and lip-sync drift. Catching jitter in Splunk before the help desk floods lets the NOC correlate with latency (UC-5.9.1) and loss (UC-5.9.2) to distinguish congestion-induced jitter (all three degrade) from queuing-induced jitter (jitter rises while latency stays stable — points to a QoS misconfiguration or a bufferbloat problem in a specific device).

## Implementation

Uses the same Tests Stream — Metrics input as UC-5.9.1 and UC-5.9.2. If that input is already enabled, no additional data collection setup is needed — `network.jitter` arrives in the same OTel events. Schedule the search every 15 minutes over the last 1 hour, trigger when results > 0, throttle by `thousandeyes.source.agent.name` + `server.address` for 4 hours.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.1 apply — the `ta_cisco_thousandeyes` app must be installed, OAuth authenticated, HEC configured, and the Tests Stream — Metrics input enabled with Agent-to-Server tests streaming to `thousandeyes_metrics`.
- `network.jitter` arrives in the same OTel events as `network.latency` and `network.loss`. If you implemented UC-5.9.1, no additional data collection is needed.
- **Jitter context:** understand that ThousandEyes reports jitter as the standard deviation of round-trip times within a test round, not the inter-packet delay variation (IPDV) that some RTP-specific tools report. The two are related but not identical — ThousandEyes jitter is based on ICMP or TCP probe timing, not RTP stream analysis. For RTP-specific jitter and MOS, see the Voice/RTP test UCs (UC-5.9.44+).
- Baseline knowledge: expected jitter by path type. Same-datacenter wired paths: < 1 ms. Same-metro WAN: 1–5 ms. Cross-continental WAN: 5–15 ms. Wi-Fi last-mile: 15–50 ms (not representative of WAN quality). Satellite: 50–200 ms.

### Step 1 — Configure data collection
If the Tests Stream — Metrics input from UC-5.9.1 is already enabled, no additional configuration is needed. The `network.jitter` metric is delivered in the same OTel events as `network.latency` and `network.loss`.

If you have not yet set up data collection, follow UC-5.9.1 Step 1 in full. After enabling the stream, verify jitter data:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="agent-to-server" earliest=-10m
| stats avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name
| where isnotnull(avg_jitter)
```

**Unit note:** Unlike `network.latency` (seconds in v2), `network.jitter` remains in **milliseconds** in both v1 and v2 of the OTel data model. No unit conversion is needed — the SPL thresholds are directly in ms. Verify by checking a known stable path: a same-datacenter path should show jitter < 1 ms. If it shows 0.001, you have a unit mismatch (unlikely but worth confirming).

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.jitter) as avg_jitter_ms max(network.jitter) as max_jitter_ms by thousandeyes.source.agent.name, server.address
| where avg_jitter_ms > 30
| sort -avg_jitter_ms
```

**Understanding this SPL**

`stats avg(network.jitter) ... max(network.jitter)` — Average jitter tells you the sustained path variability that jitter buffers must absorb. Maximum jitter tells you the worst burst — jitter buffers are sized for the maximum, not the average. If `avg` is 15 ms but `max` is 80 ms, the path has periodic jitter spikes that will cause intermittent audio glitches even though the average looks OK.

`where avg_jitter_ms > 30` — 30 ms is the threshold recommended by Cisco's QoS design guides for acceptable VoIP quality. Below 30 ms, a standard 60 ms jitter buffer can absorb the variation without packet discards. Above 30 ms, the jitter buffer overflows and late packets are discarded, causing audible clicks. For video conferencing (Webex, Zoom, Teams), jitter above 20 ms starts causing visible freezing — tighten to 20 ms for video-critical paths. For bulk data transfer paths where real-time quality doesn't matter, relax to 50 ms or disable jitter alerting entirely.

**Why jitter matters independently of latency:** A path with 100 ms mean latency and 5 ms jitter is fine for VoIP — the jitter buffer easily handles it. A path with 30 ms mean latency and 40 ms jitter is terrible for VoIP — individual packets arrive anywhere from 0 ms to 70 ms, overwhelming the buffer. This is why jitter gets its own UC rather than being folded into the latency UC.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`. Trigger on "Number of results > 0". Throttle on `thousandeyes.source.agent.name` + `server.address` for 4 hours.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Agent to Server** and look at the **Jitter** column for the same time window. Pick a path showing moderate jitter (10–30 ms) and compare to Splunk:
```spl
`stream_index` thousandeyes.test.type="agent-to-server" thousandeyes.source.agent.name="<agent>" server.address="<target>" earliest=-1h
| stats avg(network.jitter) as avg_jitter
```
Values should match within 1–2 ms.

(b) **Zero-jitter baseline.** A same-datacenter wired path should show < 1 ms jitter. If a local path shows > 5 ms, something is wrong with the agent host, local network, or test configuration.

(c) **Correlation check.** For a path showing elevated jitter, also check latency and loss:
```spl
`stream_index` thousandeyes.test.type="agent-to-server" thousandeyes.source.agent.name="<agent>" server.address="<target>" earliest=-1h
| stats avg(network.latency) as lat_s avg(network.loss) as loss avg(network.jitter) as jitter
| eval lat_ms=round(lat_s*1000,1)
```
If all three are elevated → congestion. If only jitter is elevated → QoS/buffering issue. If jitter and loss are elevated but latency is stable → interface errors / CRC problems.

(d) **Verify jitter units.** Confirm the unit is milliseconds by checking a known stable path. Jitter should read < 1.0 for a same-datacenter path. If it reads < 0.001, the data is in seconds and your thresholds are wrong.

### Step 4 — Operationalize
**Dashboard** (add as a row in the UC-5.9.1 "Network Performance" dashboard, or create standalone "ThousandEyes — Path Quality"):
- Row 1 — Three single value tiles side by side: "Paths > 100 ms latency" (from UC-5.9.1), "Paths > 0.5% loss" (from UC-5.9.2), "Paths > 30 ms jitter" (this UC). This gives a fleet-wide path quality summary at a glance.
- Row 2 — Combined timechart: latency (ms, left Y-axis), loss (%, right Y-axis), and jitter (ms, overlaid) for a selected agent-target pair. Use tokens/dropdowns to select the pair.
- Row 3 — Scatter plot: latency vs jitter, colour-coded by loss rate. Paths clustering in the upper-right (high latency, high jitter) with red colour (high loss) are "triple bad" — immediate action required.

**Runbook** (owner: Network Operations / Unified Comms team):
1. Open the alert. Note the agent, target, and avg jitter.
2. Open the ThousandEyes permalink. Check the Path Visualization for per-hop jitter.
3. **If jitter increases at a specific intermediate hop:** That device is introducing queuing delay. If it's in your network, check QoS configuration — is the traffic being marked DSCP EF for priority queuing? If not, apply QoS policy. If it's in a transit network, escalate to the carrier.
4. **If jitter is elevated across all hops equally:** The source is likely the agent's local network (Wi-Fi contention, congested access switch). Check the agent's connection type.
5. **If jitter is elevated only to certain targets:** Those targets may be behind a load balancer or proxy that introduces variable processing delay. Check the target's infrastructure.
6. **Correlate with VoIP quality:** If you have Webex/Teams call quality data or RTP test results (UC-5.9 voice UCs), check whether MOS scores correlate with jitter spikes on the same paths.

### Step 5 — Troubleshooting

- **Jitter reads exactly 0 for all paths** — The metric may not be populated. Check whether the test type supports jitter reporting — Agent-to-Server tests with ICMP or TCP should always report jitter. If using a proxy configuration on the Enterprise Agent, jitter may not be measurable through the proxy.

- **Jitter values seem extremely high (> 200 ms) but latency is normal** — The agent host is likely experiencing scheduling jitter. VM snapshots, CPU steal time, or garbage collection pauses on the agent process can inflate jitter measurements without affecting mean latency. Check `| stats stdev(network.latency) as computed_jitter` and compare with the reported `network.jitter` — if they diverge significantly, the reported jitter may include agent-side artifacts.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth token refresh, v1/v2 metric name mismatches (`net.metrics.jitter` in v1 vs `network.jitter` in v2 — note: units are ms in both versions), stream_index macro, and role permissions.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.jitter) as avg_jitter_ms max(network.jitter) as max_jitter_ms by thousandeyes.source.agent.name, server.address
| where avg_jitter_ms > 30
| sort -avg_jitter_ms
```

## Visualization

(1) Sortable table: agent name, server address, avg jitter (ms), max jitter (ms) — sorted worst-first. Colour-code: green < 10 ms, yellow 10–30 ms, red > 30 ms. (2) Combined panel: timechart overlay of `network.latency` (converted to ms), `network.loss`, and `network.jitter` for a selected agent-target pair — this three-metric view is the standard network quality assessment. (3) Single value tile: count of paths exceeding 30 ms jitter (red threshold ≥ 1). (4) Scatter plot: `avg_latency_ms` on X-axis vs `avg_jitter_ms` on Y-axis, colour by `server.address` — paths in the upper-right quadrant (high latency AND high jitter) are the worst candidates for real-time traffic.

## Known False Positives

**Wi-Fi last-mile variability.** Enterprise Agents or endpoint agents connected via Wi-Fi inherently show higher jitter (20–60 ms) than wired connections due to radio contention, retransmissions, and roaming. Distinguish from a real WAN issue by checking whether the same target shows low jitter from a wired Cloud Agent. Do not use Wi-Fi-connected agents as the authority for WAN jitter — use them for endpoint experience monitoring (UC-5.9.24) instead.

**Bufferbloat on consumer-grade routers.** Consumer and SOHO routers with large, unmanaged buffers (common on cable/DSL modems) introduce variable queuing delay that shows up as jitter. The mean latency may look normal because the buffer absorbs bursts, but jitter spikes during any concurrent traffic. Distinguish by checking whether jitter correlates with time-of-day patterns and whether it improves when other traffic on the same circuit is reduced.

**VPN encryption overhead.** Traffic traversing IPsec or SSL VPN tunnels can show elevated jitter due to variable encryption processing time on the VPN concentrator. Distinguish by comparing jitter to the same target with and without VPN (requires a test from outside the VPN). This is particularly noticeable on undersized firewall/VPN appliances handling high throughput.

**QoS remarking at transit boundaries.** When traffic crosses from a DSCP-marked QoS domain into a best-effort transit network, the loss of priority scheduling causes jitter to increase abruptly at the boundary hop. Distinguish by correlating with Path Visualization (UC-5.9.33) — if jitter jumps at a specific hop that coincides with an ISP handoff, QoS policy is the cause.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 Data Model — Agent-to-Server metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [ITU-T G.114 — One-way transmission time (VoIP quality thresholds)](https://www.itu.int/rec/T-REC-G.114)
- [Cisco Design Guide — QoS for VoIP and Video (jitter buffer sizing)](https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/WAN_and_MAN/QoS_SRND_40/QoSIntro_40.html)
