<!-- AUTO-GENERATED from UC-5.9.27.json — DO NOT EDIT -->

---
id: "5.9.27"
title: "Endpoint Connection Type and Network Score"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.27 · Endpoint Connection Type and Network Score

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We compare how well internet works over Wi-Fi versus a cable, so we can prove with data whether the company should buy cable adapters for everyone or invest in better Wi-Fi.*

---

## Description

Compares network performance metrics across connection types (Wireless, Ethernet, Modem) to quantify the performance impact of each connection method. Provides data-driven evidence for IT policy decisions about connectivity requirements for specific job roles or use cases (e.g., requiring Ethernet for VoIP-heavy roles).

## Value

IT teams often suspect that Wi-Fi is causing issues but lack data to prove it. This UC provides the proof: if Wireless endpoints average a `network.score` of 0.65 while Ethernet endpoints average 0.92, that's a quantifiable 30% performance gap that justifies purchasing USB-Ethernet adapters for the remote workforce, investing in better Wi-Fi infrastructure in the office, or requiring Ethernet for roles that depend on real-time communications (traders, support agents, video editors). The data also reveals whether the Wi-Fi problem is universal (Wi-Fi standards, interference) or specific to certain locations (bad AP placement, channel congestion). Over time, this UC tracks whether infrastructure investments (new Wi-Fi 6E access points, mesh networks) actually improved wireless performance.

## Implementation

Uses the same Endpoint Agent data stream as UC-5.9.24. Aggregates by `thousandeyes.source.agent.connection.type` to compare connection methods.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.24 apply — Endpoint Agent deployed, Endpoint data flowing, `stream_index` macro configured.
- **Endpoint Agents deployed on a representative mix of connection types.** This UC compares Ethernet vs Wi-Fi (and optionally Modem/cellular). You need endpoints on BOTH connection types to make a comparison. If 100% of your workforce uses laptops on Wi-Fi, you'll see only "Wireless" — the comparison requires at least some Ethernet users (docking stations, desktop PCs).
- **Understand what `thousandeyes.source.agent.connection.type` reports.** The Endpoint Agent detects the active network interface type at the time of measurement:
  - **"Ethernet"** — wired connection (USB-C dock, built-in Ethernet, USB-Ethernet adapter).
  - **"Wireless"** — Wi-Fi connection (any standard: Wi-Fi 5, 6, 6E, 7).
  - **"Modem"** — cellular/mobile data (4G, 5G).
  - **"Unknown"** — detection failed (older Endpoint Agent version or unusual NIC type).
  The agent detects this automatically — no configuration needed.
- **Wi-Fi infrastructure knowledge.** For meaningful recommendations, know:
  - Wi-Fi standard deployed (Wi-Fi 5/6/6E).
  - AP density and channel planning.
  - Enterprise vs home/remote Wi-Fi (compare separately).
  - SSID security type (WPA2-Enterprise, WPA3).
- **Business context.** This UC answers a common executive question: "Should we invest in Wi-Fi upgrades or just buy Ethernet docks?" The data-driven answer requires comparing both connection types.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Endpoint data flows through the same Tests Stream — Metrics OTel input configured in UC-5.9.24. No separate input is needed.

Verify connection type distribution:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-24h
| stats dc(thousandeyes.source.agent.name) as endpoints avg(network.score) as avg_score by thousandeyes.source.agent.connection.type
| sort -endpoints
```
Expected: at least two connection types (Wireless and Ethernet). If only one appears, the comparison is not possible. The `endpoints` count shows the population size per connection type — small samples (< 10 endpoints) may not be representative.

**Understanding local network metrics for connection type analysis:**
- `network.score` — ThousandEyes composite score (0–1) for the local network segment (endpoint → gateway). This is the most holistic metric for connection quality comparison. 1.0 = perfect.
- `network.latency` — round-trip time to the gateway in SECONDS. For Ethernet, expect < 1 ms (0.001 s). For Wi-Fi, expect 1–5 ms. Significantly higher values indicate congestion or interference.
- `network.loss` — packet loss percentage. Ethernet should be 0%. Wi-Fi may show 0.1–2% under normal conditions. > 5% indicates serious Wi-Fi problems.
- `network.jitter` — latency variation in MILLISECONDS. Ethernet should be < 1 ms. Wi-Fi typically shows 1–5 ms. High jitter (> 10 ms) degrades VoIP/video quality.

### Step 2 — Create the search and alert
**Connection type performance comparison (primary view):**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter p95(network.latency) as p95_latency dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,2), p95_latency_ms=round(p95_latency*1000,1), avg_loss_pct=round(avg_loss,3), avg_jitter_ms=round(avg_jitter,2), avg_score_pct=round(avg_score*100,1)
| table thousandeyes.source.agent.connection.type, endpoints, avg_score_pct, avg_latency_ms, p95_latency_ms, avg_loss_pct, avg_jitter_ms
| sort -avg_score_pct
```

**Understanding this SPL**

`target.type="gateway"` — filters to local network measurements (endpoint → default gateway). This isolates the LOCAL connection quality from the broader internet path. The gateway is the first hop — differences between Ethernet and Wi-Fi are most visible here.

`by thousandeyes.source.agent.connection.type` — splits results by connection type so you can directly compare Ethernet vs Wireless.

`dc(thousandeyes.source.agent.name) as endpoints` — shows how many unique endpoints contribute to each row. Important for statistical confidence: 5 endpoints is anecdotal, 100+ endpoints is data.

**Time-based comparison (reveals Wi-Fi congestion during peak hours):**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| timechart span=1h avg(network.score) by thousandeyes.source.agent.connection.type
```
Wi-Fi typically degrades during peak hours (9–11 AM, 2–4 PM) when all users are on video calls. Ethernet performance should remain constant. If the Wi-Fi score drops during business hours but Ethernet doesn't, this proves Wi-Fi congestion.

**Wi-Fi performance gap quantification:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score by thousandeyes.source.agent.connection.type
| xyseries "metric" thousandeyes.source.agent.connection.type avg_score
| eval wifi_gap_pct=round((Ethernet - Wireless) / Ethernet * 100, 1)
| table Ethernet, Wireless, wifi_gap_pct
```
This calculates the Wi-Fi performance gap as a percentage. A gap > 20% is significant and justifies investment.

**Per-endpoint worst Wi-Fi performers (identify users who need help):**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" thousandeyes.source.agent.connection.type="Wireless" earliest=-24h
| stats avg(network.score) as avg_score avg(network.loss) as avg_loss avg(network.latency) as avg_latency by thousandeyes.source.agent.name, thousandeyes.source.agent.network.org
| eval avg_score_pct=round(avg_score*100,1), avg_latency_ms=round(avg_latency*1000,1)
| where avg_score_pct < 50
| sort avg_score_pct
```
Endpoints with < 50% score have serious Wi-Fi issues. These users likely experience poor video call quality, slow downloads, and general frustration.

**Week-over-week Wi-Fi trend:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" thousandeyes.source.agent.connection.type="Wireless" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "this_week", "last_week")
| stats avg(network.score) as avg_score by week
| eval avg_score_pct=round(avg_score*100,1)
| xyseries "metric" week avg_score_pct
| eval trend=if(this_week > last_week, "Improving", "Degrading")
```

**Scheduling:** Weekly report: cron `0 8 * * 1` (Monday 8 AM), time range `-7d to now`. This is a strategic/planning metric, not an operational alert.

### Step 3 — Validate
(a) **Verify multiple connection types.** If only "Wireless" appears, your population has no Ethernet users. Consider deploying a few test endpoints with docking stations to establish an Ethernet baseline.

(b) **Confirm Ethernet outperforms Wireless.** This is expected. If Ethernet performs worse than Wi-Fi, investigate the Ethernet infrastructure (cable quality, switch port speed, docking station issues).

(c) **Sample size check.** For each connection type, verify `endpoints` count is ≥ 10 for reliable statistics. A single endpoint with a broken NIC would skew results.

(d) **Remote vs office segmentation.** Remote workers on home Wi-Fi will generally perform worse than office workers on enterprise Wi-Fi. Segment by `thousandeyes.source.agent.network.org` (ISP name) or location to compare like-for-like: office Wi-Fi vs office Ethernet, remote Wi-Fi vs remote Ethernet.

(e) **Connection type accuracy.** Run `| stats count by thousandeyes.source.agent.connection.type` and check for "Unknown". If > 10% are "Unknown", upgrade Endpoint Agents to the latest version for better detection.

### Step 4 — Operationalize
**Weekly report** ("Connectivity Type Performance Report" — designed for IT infrastructure planning):
- Section 1 — Executive summary: one-row comparison table (Ethernet vs Wireless) with score, latency, loss, jitter, endpoint count, and Wi-Fi performance gap percentage.
- Section 2 — Time-of-day comparison: timechart showing Ethernet vs Wireless score by hour. Highlights peak-hour Wi-Fi degradation.
- Section 3 — Worst Wi-Fi performers: list of endpoints with < 50% Wi-Fi score. These users need help (better AP coverage, Ethernet adapter, or remote network troubleshooting).
- Section 4 — Week-over-week trend: is Wi-Fi performance improving or degrading? Tracks the impact of Wi-Fi infrastructure investments.

**Dashboard** (add to the UC-5.9.24 "Endpoint Network Health" dashboard):
- Row — Connection Type Comparison: bar chart showing avg score per connection type. Single visual proof of the Wi-Fi gap.

**Runbook** (owner: IT infrastructure / workplace technology):
1. **Wi-Fi consistently underperforms Ethernet by > 20%.** (a) Assess Wi-Fi infrastructure: AP density, channel planning, Wi-Fi standard (5 vs 6 vs 6E). (b) Use Wi-Fi survey tools to identify coverage gaps. (c) Present data to justify Wi-Fi upgrade budget.
2. **Specific Wi-Fi locations worse than others.** (a) Correlate worst-performing endpoints with physical locations (if available). (b) Cross-reference with AP coverage maps. (c) Add or reposition APs in problem areas.
3. **Remote workers on Wi-Fi consistently underperform.** (a) Provide USB-Ethernet adapters to remote workers with poor Wi-Fi. (b) Create a self-service guide for home network optimization (router placement, channel selection, Wi-Fi 5 GHz band). (c) Consider subsidizing mesh Wi-Fi for key remote workers.
4. **Wi-Fi performance degrading week-over-week.** (a) Check if new devices or users are adding congestion. (b) Check for new sources of interference (microwave ovens, neighboring networks). (c) Review AP firmware versions for known issues.

### Step 5 — Troubleshooting

- **`connection.type` always shows "Unknown"** — Endpoint Agent version is too old. Upgrade to the latest version. Connection type detection requires a minimum agent version (check ThousandEyes release notes).

- **Only one connection type appears** — Your endpoint population may be homogeneous (all laptops on Wi-Fi). Deploy a few test endpoints with Ethernet to establish a baseline, or skip this UC if Ethernet is not relevant to your environment.

- **Ethernet shows poor performance** — Check for: 100 Mbps Ethernet (should be 1 Gbps), faulty cables, USB-C dock issues (some docks have poor Ethernet chipsets), or switch port errors.

- **Wi-Fi and Ethernet scores are nearly identical** — Your Wi-Fi infrastructure may be excellent (enterprise Wi-Fi 6E with proper AP density). This is a good result — it means your Wi-Fi investment is paying off.

- **All common troubleshooting** — See UC-5.9.24 Step 5 for general endpoint troubleshooting and UC-5.9.1 Step 5 for app issues.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss p95(network.latency) as p95_latency dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1), p95_latency_ms=round(p95_latency*1000,1)
| sort -avg_score
```

## Visualization

(1) Bar chart: average network score by connection type. (2) Box plot: latency distribution by connection type. (3) Table: connection type comparison (avg score, avg latency, avg loss, endpoint count). (4) Timechart: score trending by connection type over 7 days. (5) Pie chart: workforce distribution by connection type.

## Known False Positives

**Enterprise Wi-Fi vs home Wi-Fi.** Office Wi-Fi (enterprise-grade APs, proper channel planning, dedicated SSID) performs significantly better than home Wi-Fi (consumer routers, interference, shared bandwidth). Segment by location or ISP to compare like-for-like.

**Connection type changes during a measurement.** A user docking a laptop switches from Wireless to Ethernet mid-session. The transition period may show anomalous metrics. The Endpoint Agent reports the connection type at the time of measurement, so this typically self-corrects within one measurement cycle.

**Modem connections.** The "Modem" connection type (cellular/mobile data) is inherently variable. High latency and jitter are expected — don't flag these as anomalies unless they're significantly worse than the cellular baseline.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Endpoint attributes](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
