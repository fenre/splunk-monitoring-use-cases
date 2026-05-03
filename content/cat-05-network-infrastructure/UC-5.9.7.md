<!-- AUTO-GENERATED from UC-5.9.7.json — DO NOT EDIT -->

---
id: "5.9.7"
title: "WAN Link Quality Scoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.7 · WAN Link Quality Scoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We combine delay, packet loss, and jitter into one easy-to-read score for each network link — like a school grade from A to F — so anyone in the company can tell at a glance whether the network is healthy or needs attention.*

---

## Description

Computes a weighted composite quality score (0–100) for each WAN path by blending latency (40% weight), loss (35% weight), and jitter (25% weight) into a single metric. The score simplifies executive reporting, SLA tracking, and NOC triage — instead of parsing three separate metrics, operators see one number per link: green (80+), yellow (60–79), or red (< 60).

## Value

Executives and non-technical stakeholders cannot interpret raw latency/loss/jitter numbers. A CTO asking "how is our WAN performing?" needs a single answer, not a three-column spreadsheet. The composite score turns network telemetry into a business metric: a score of 92 means "performing well," a score of 45 means "users are complaining." For SLA management, the score provides a contractual measurement point — if the carrier commits to a monthly quality score ≥ 80, this search provides the evidence for every SLA review meeting. For the NOC, the score enables prioritization: a link scoring 30 gets attention before a link scoring 70, even if the 70-score link has slightly higher latency, because the composite accounts for the combined impact of all three dimensions.

## Implementation

Uses the same Tests Stream — Metrics data as UC-5.9.1/2/3. The composite score is computed entirely in SPL — no ThousandEyes or Splunk app changes needed. Adjust the weights (latency 40%, loss 35%, jitter 25%) and tier thresholds based on your SLA requirements and application mix. VoIP-heavy networks should increase the jitter weight; bulk-data networks should increase the latency weight.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- UC-5.9.1 (latency), UC-5.9.2 (loss), and UC-5.9.3 (jitter) should be validated first — this UC depends on all three metrics being accurate and the unit conventions being confirmed.
- **Weight and threshold decisions:** Before deploying, decide the weights and tier boundaries with your network engineering team. The defaults in this UC are:
  - Latency: 40% weight. Tiers: < 50 ms = 100, < 100 ms = 80, < 200 ms = 60, < 500 ms = 40, else = 20.
  - Loss: 35% weight. Tiers: < 0.1% = 100, < 0.5% = 80, < 1% = 60, < 3% = 40, else = 20.
  - Jitter: 25% weight. Tiers: < 5 ms = 100, < 15 ms = 80, < 30 ms = 60, < 50 ms = 40, else = 20.
  These align with Cisco QoS design guide thresholds for voice/video. Adjust for your application mix.

### Step 1 — Configure data collection
No additional data collection beyond UC-5.9.1. This UC is purely an SPL computation over the same metrics stream.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_lat avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval latency_score=case(avg_lat<0.05,100, avg_lat<0.1,80, avg_lat<0.2,60, avg_lat<0.5,40, 1=1,20)
| eval loss_score=case(avg_loss<0.1,100, avg_loss<0.5,80, avg_loss<1,60, avg_loss<3,40, 1=1,20)
| eval jitter_score=case(avg_jitter<5,100, avg_jitter<15,80, avg_jitter<30,60, avg_jitter<50,40, 1=1,20)
| eval quality_score=round((latency_score*0.4 + loss_score*0.35 + jitter_score*0.25),0)
| sort quality_score
```

**Understanding this SPL**

`thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"` — includes both test types to provide a complete WAN quality picture. Agent-to-Server tests measure paths to cloud/internet targets; Agent-to-Agent tests measure site-to-site WAN links. Both contribute to overall WAN quality assessment.

**Tier scoring:** Each metric is mapped to a 5-tier score (100/80/60/40/20) based on industry-standard thresholds:

`latency_score` — uses `avg_lat` which is in **seconds** (OTel v2). The thresholds are in seconds: `0.05` = 50 ms, `0.1` = 100 ms, `0.2` = 200 ms, `0.5` = 500 ms. If your data is v1 (milliseconds), change these to `50, 100, 200, 500`.

`loss_score` — uses `avg_loss` which is a **percentage** (0–100). Thresholds: `0.1` = 0.1% loss, `0.5` = 0.5%, `1` = 1%, `3` = 3%. These are aggressive — 1% loss is already devastating for TCP. For best-effort internet paths, relax to `0.5, 1, 3, 5`.

`jitter_score` — uses `avg_jitter` which is in **milliseconds**. Thresholds: `5, 15, 30, 50` ms. Aligned with VoIP jitter buffer sizing.

**Weighted composite:** `quality_score = latency × 0.4 + loss × 0.35 + jitter × 0.25`. The weights reflect the relative impact on most enterprise applications: latency affects everything (hence 40%), loss causes retransmissions that compound (35%), jitter mainly affects real-time traffic (25%). Swap loss and jitter weights for VoIP-dominant networks.

**Why `case()` not `if()`:** The nested `if()` approach in the original SPL works but is harder to read and maintain. `case()` is cleaner for multi-tier classification and easier to extend (add a 6th tier, change a threshold).

**"Floor rule" variant** — prevents a single terrible dimension from hiding behind good scores in the other two:
```spl
| eval quality_score=if(latency_score<=20 OR loss_score<=20 OR jitter_score<=20, min(quality_score, 40), quality_score)
```
This ensures any path with a "red" dimension scores no higher than 40, regardless of how good the other two are.

**Scheduling:** For alerting, save a filtered version: cron `*/15 * * * *`, time range `-1h to now`, trigger when `quality_score < 60`. Throttle by `thousandeyes.source.agent.name` + `server.address` for 4 hours.

For executive reporting, schedule a daily summary: cron `0 7 * * *`, time range `-24h to now`, output to a CSV or email.

### Step 3 — Validate
(a) **Sanity check scores.** Pick a known-healthy same-datacenter path. Its score should be 100 (latency < 1 ms, loss = 0%, jitter < 1 ms → all dimensions score 100). If it's not 100, check the tier boundaries against the actual metric values.

(b) **Pick a known-degraded path.** If you have a WAN link with known issues (e.g., a congested MPLS circuit), its score should be < 80. If it scores higher than expected, the tier boundaries may be too relaxed for your environment.

(c) **Unit verification.** Run the raw stats for a single path:
```spl
`stream_index` thousandeyes.source.agent.name="<agent>" server.address="<target>" earliest=-1h
| stats avg(network.latency) as lat avg(network.loss) as loss avg(network.jitter) as jitter
```
Verify that `lat` is in seconds (e.g., 0.045 for 45 ms), `loss` is in percentage (e.g., 0.1 for 0.1%), and `jitter` is in milliseconds (e.g., 3.2 for 3.2 ms). If `lat` looks like 45.0, it's in milliseconds (v1) and you need to change the latency tier boundaries.

(d) **Compare with ThousandEyes built-in scoring.** For Endpoint Agent tests, ThousandEyes provides a native `network.score` metric. If you have Endpoint tests, compare the ThousandEyes native score with your computed score to validate the tier boundaries are reasonable.

### Step 4 — Operationalize
**Dashboard** ("WAN Quality Scorecard" — designed for executive and NOC audiences):
- Row 1 — Fleet overview: Large gauge showing fleet average quality score (green/yellow/red). Three single-value tiles: links scoring ≥ 80 (green), 60–79 (yellow), < 60 (red).
- Row 2 — Scorecard table: agent | target | quality score (colour-coded) | latency score | loss score | jitter score | raw latency (ms) | raw loss % | raw jitter (ms). Sorted worst-first. This gives both the executive summary (composite score) and the operational detail (component scores and raw values) in one view.
- Row 3 — Trend: `| timechart span=1d avg(quality_score) by thousandeyes.source.agent.name` over 30 days. Declining trend lines signal capacity issues before they become outages.
- Row 4 — Heatmap: quality score by agent (Y-axis) and hour-of-day (X-axis). Reveals time-of-day patterns (congestion during business hours, maintenance windows at night).

**SLA reporting:** Save the search as a scheduled report running daily at 07:00 with CSV output to a shared drive or email to SLA stakeholders. Include the composite score, component scores, and raw values. Monthly aggregate: `| timechart span=1d avg(quality_score) as daily_score | stats avg(daily_score) as monthly_avg p5(daily_score) as monthly_p5 min(daily_score) as monthly_min`.

**Runbook** (owner: Network Operations / WAN Engineering):
1. **Score < 60 (red):** Investigate immediately. Open the component scores to identify the dominant degradation factor. Follow the appropriate UC runbook (UC-5.9.1 for latency, UC-5.9.2 for loss, UC-5.9.3 for jitter).
2. **Score 60–79 (yellow):** Schedule investigation. Often indicates gradual degradation that hasn't crossed individual metric thresholds but is accumulating across dimensions.
3. **Score ≥ 80 (green):** No action needed. Monitor trend for decline.
4. **Monthly SLA review:** Compare monthly average and P5 scores against carrier SLA commitments. Scores consistently below 80 justify a carrier escalation or circuit upgrade business case.

### Step 5 — Troubleshooting

- **All paths score 20** — Unit mismatch. If the data is v1 (latency in milliseconds), the latency tier boundaries are in the wrong unit. A 50 ms latency reads as `50` (not `0.05`), which falls into the `else` tier (> 500 ms → score 20). Change the latency tiers to `50, 100, 200, 500` for v1 data.

- **Scores don't change despite known degradation** — The search time window may be too long, averaging out transient degradation. Shorten from `-1h` to `-15m` for real-time alerting.

- **Composite score seems "too high" for a clearly bad path** — The weighted average is masking one bad dimension with two good ones. Add the "floor rule" variant from Step 2 to cap the score when any dimension is critically bad.

- **Different scores for the same path in ThousandEyes vs Splunk** — The ThousandEyes native `network.score` (for Endpoint tests) uses a different scoring algorithm than this SPL. The two are designed to be directionally consistent but not identical. ThousandEyes scores also incorporate additional factors like DNS and connection timing that this UC doesn't include.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for data collection, macro configuration, and general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_lat avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval latency_score=case(avg_lat<0.05,100, avg_lat<0.1,80, avg_lat<0.2,60, avg_lat<0.5,40, 1=1,20)
| eval loss_score=case(avg_loss<0.1,100, avg_loss<0.5,80, avg_loss<1,60, avg_loss<3,40, 1=1,20)
| eval jitter_score=case(avg_jitter<5,100, avg_jitter<15,80, avg_jitter<30,60, avg_jitter<50,40, 1=1,20)
| eval quality_score=round((latency_score*0.4 + loss_score*0.35 + jitter_score*0.25),0)
| sort quality_score
```

## Visualization

(1) Gauge or radial chart per link showing the quality score with colour zones: green ≥ 80, yellow 60–79, red < 60. (2) Table: agent, target, quality score, latency score, loss score, jitter score, raw latency (ms), raw loss %, raw jitter (ms) — sorted by quality score ascending (worst first). (3) Timechart: `| timechart span=1h avg(quality_score) by thousandeyes.source.agent.name` showing quality trends over 30 days for capacity review. (4) Heatmap: quality score by agent (Y-axis) and hour-of-day (X-axis) to identify time-of-day patterns.

## Known False Positives

**Score dominated by one bad dimension.** The weighted average can mask a single critical metric. A path with 10 ms latency (score 100), 0% loss (score 100), and 80 ms jitter (score 20) gets a composite score of 65 — "yellow" — which doesn't convey that the path is completely unusable for VoIP. Mitigate by also displaying the component scores alongside the composite, or adding a rule: `| eval quality_score=if(latency_score<40 OR loss_score<40 OR jitter_score<40, min(quality_score, 40), quality_score)` — this caps the composite at 40 if ANY dimension is critically bad.

**Thresholds inappropriate for specific path types.** The default thresholds assume WAN paths between offices. Same-datacenter paths should score 100; satellite paths should use relaxed thresholds (latency 600+ ms is normal, not bad). Consider maintaining a `thousandeyes_path_profiles` lookup with per-path-type threshold overrides.

**v1/v2 unit mismatch invalidates thresholds.** If the data is OTel v1 format, `network.latency` is in milliseconds (not seconds). The latency tier thresholds (`< 0.05` seconds) would incorrectly classify a 50 ms path as scoring 20 (bad) when it should be 100 (excellent). Always verify the unit — see UC-5.9.1 Step 5 for the v1/v2 check.

**Equal weighting may not match business priority.** The default 40/35/25 weighting assumes a general-purpose network. If your WAN primarily carries VoIP, increase jitter weight to 35% and reduce latency weight to 30%. If it primarily carries bulk replication, increase latency weight to 50% and reduce jitter weight to 15%. There is no universal "correct" weighting.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 Data Model — metric definitions and units](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [Cisco QoS Design Guide — network quality thresholds for voice and video](https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/WAN_and_MAN/QoS_SRND_40/QoSIntro_40.html)
- [ITU-T Y.1540 — IP packet transfer performance parameters](https://www.itu.int/rec/T-REC-Y.1540)
