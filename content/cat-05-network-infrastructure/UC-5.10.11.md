<!-- AUTO-GENERATED from UC-5.10.11.json — DO NOT EDIT -->

---
id: "5.10.11"
title: "Provider SLA Measurement (Latency, Jitter, Loss to PE)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.11 · Provider SLA Measurement (Latency, Jitter, Loss to PE)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We ping the front doors of our internet suppliers on a schedule and graph delay, wobble, and dropped packets so slow lanes get proved with numbers when we ask for a fix or credit.*

---

## Description

Pulls synthetic probe metrics aimed at each carrier provider-edge endpoint and compares rolling averages against contractual latency, jitter, and packet-loss ceilings encoded in lookup tables—surfacing degradation before subscriber-facing alarms trigger.

## Value

Finance and network assurance teams collect tamper-resistant measurement history suitable for SLA credits or contractual escalation—avoiding subjective traceroute screenshots when circuits brown out intermittently.

## Implementation

Deploy ThousandEyes agents adjacent to each subscriber aggregation POP; define tests targeting PE loopbacks documented in carrier LLAs; map Splunk metrics index macros per docs; seed lookup with SLA thresholds per circuit_id; schedule hourly alert combining violations.

## Detailed Implementation

### Prerequisites
- Completed ThousandEyes OAuth onboarding plus Tests Stream — Metrics input landing in `thousandeyes_metrics`.
- Accurate inventory tying probe agents to geographic markets so latency budgets reflect distance.
- Contract annex listing numeric SLA thresholds per product (often differentiated for consumer versus enterprise tails).
- Splunk macros translating metric names when tenants remain on legacy v1 schemas.

### Step 1 — Create agent-to-server tests enumerating each PE IP with ICMP or lightweight TCP where ICMP blocked—document chosen protocol in lookup to avoid apples-to-oranges comparisons.

### Step 2 — Validate metric presence using short-window `mpreview` or `tstats` (metrics pipeline) ensuring `network.latency`, `network.jitter`, `network.loss` populate.

### Step 3 — Join `carrier_pe_targets.csv` supplying carrier_name, circuit identifiers, and SLA numbers; implement composite alerting requiring two consecutive fifteen-minute breaches before paging.

### Step 4 — Publish dashboard pairing Splunk charts with deep links to ThousandEyes views for carrier collaboration calls.

### Step 5 — Troubleshooting: agents behind NAT may skew latency—relocate agents; PE ICMP de-prioritization exaggerates loss—switch to TCP-based tests; macro drift between Cloud vs Enterprise agents requires periodic validation scripts.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency_sec avg(network.jitter) as avg_jitter_ms avg(network.loss) as avg_loss_pct latest(thousandeyes.source.agent.name) as agent_site by server.address
| lookup carrier_pe_targets.csv pe_ip AS server.address OUTPUT carrier_name sla_latency_ms sla_jitter_ms sla_loss_pct circuit_id
| eval avg_latency_ms=round(avg_latency_sec*1000,2)
| eval latency_violation=if(isnotnull(sla_latency_ms) AND avg_latency_ms>sla_latency_ms,1,0)
| eval jitter_violation=if(isnotnull(sla_jitter_ms) AND avg_jitter_ms>sla_jitter_ms,1,0)
| eval loss_violation=if(isnotnull(sla_loss_pct) AND avg_loss_pct>sla_loss_pct,1,0)
| where latency_violation=1 OR jitter_violation=1 OR loss_violation=1 OR avg_loss_pct>0.5 OR avg_latency_ms>80
| table agent_site carrier_name circuit_id server.address avg_latency_ms avg_jitter_ms avg_loss_pct sla_latency_ms sla_jitter_ms sla_loss_pct
| sort -avg_loss_pct
```

## Visualization

SLA scorecard table with red/yellow cells per metric; timechart overlay latency/jitter/loss for worst circuit; map of agent_site to PE POP.

## Known False Positives

Carrier ICMP rate-limiting mimics loss; scheduled fibre vendor lamp tests raise jitter seconds at night; agent Wi-Fi segments introduce noise unrelated to WAN SLA—prefer wired agents.

## References

- [ThousandEyes Data Model — Metrics (OpenTelemetry v2)](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [Splunkbase — Cisco ThousandEyes App for Splunk](https://splunkbase.splunk.com/app/7719)
