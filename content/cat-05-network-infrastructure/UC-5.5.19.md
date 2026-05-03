<!-- AUTO-GENERATED from UC-5.5.19.json — DO NOT EDIT -->

---
id: "5.5.19"
title: "Transport Circuit SLA Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.19 · Transport Circuit SLA Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

ISPs commit to contractual SLAs for latency, jitter, loss, and uptime per circuit. SD-WAN BFD metrics provide continuous proof of whether carriers meet their commitments. SLA violation evidence supports service credits and carrier negotiations.

## Value

Network operations teams validate ISP/carrier circuit performance against contractual SLA commitments using SD-WAN telemetry, generating evidence-based SLA compliance reports for vendor management and credit claims.

## Implementation

Define contractual SLA thresholds per transport type (MPLS: latency <50ms, loss <0.1%; Internet: latency <80ms, loss <0.5%). Aggregate BFD metrics daily. Generate monthly SLA compliance reports per carrier per circuit. Include uptime percentage from interface state changes. Use as evidence for carrier escalations and service credit claims.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for transport circuit statistics and SLA data. Data in `index=sdwan` with `sourcetype=cisco:sdwan:bfd` (per-tunnel metrics), `sourcetype=cisco:sdwan:interface` (circuit throughput), and `sourcetype=cisco:sdwan:approute` (application SLA tracking).
- Transport circuit SLA tracking measures ISP/carrier performance against contractual SLA commitments. ISP contracts typically specify: availability (99.9%), latency (< 50ms), packet loss (< 0.1%), and CIR (Committed Information Rate). SD-WAN BFD metrics provide the data to validate these SLAs.
- Build `sdwan_circuit_sla.csv` lookup: `site_id,color,provider,circuit_id,contract_availability_pct,contract_latency_ms,contract_loss_pct,contract_cir_mbps,monthly_cost` (e.g., `200,mpls,AT&T,ATT-CHI-12345,99.95,30,0.05,50,3000`).

### Step 1 — Configure data collection
Verify circuit-level data:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-1h
| stats avg(latency) as latency avg(loss_percentage) as loss by site_id, local_color
| lookup sdwan_circuit_sla.csv site_id, color as local_color OUTPUT provider circuit_id
| where isnotnull(provider)
```

### Step 2 — Create the search and alert

**Primary search — Transport SLA compliance report (monthly):**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-30d@d latest=@d
| stats avg(latency) as avg_latency avg(loss_percentage) as avg_loss p95(latency) as p95_latency p99(latency) as p99_latency max(latency) as max_latency count as total_samples count(eval(loss_percentage > 1)) as high_loss_samples by site_id, local_color
| eval loss_sample_pct=round(100*high_loss_samples/total_samples, 2)
| lookup sdwan_circuit_sla.csv site_id, color as local_color OUTPUT provider circuit_id contract_availability_pct contract_latency_ms contract_loss_pct contract_cir_mbps monthly_cost
| where isnotnull(provider)
| eval latency_compliant=if(p95_latency <= contract_latency_ms, "PASS", "FAIL")
| eval loss_compliant=if(avg_loss <= contract_loss_pct, "PASS", "FAIL")
| eval overall_sla=if(latency_compliant="PASS" AND loss_compliant="PASS", "MET", "BREACHED")
| lookup sdwan_sites.csv site_id OUTPUT site_name
| table site_name, provider, circuit_id, contract_latency_ms, p95_latency, latency_compliant, contract_loss_pct, avg_loss, loss_compliant, overall_sla, monthly_cost
| sort overall_sla, provider
```

#### Understanding this SPL: This is the SLA validation report you send to your ISP when claiming SLA credits. It uses P95 latency (not average) because ISP contracts typically specify percentile-based latency commitments. The monthly cost field enables ROI calculation: if a $3000/month MPLS circuit consistently breaches SLA, you have data to negotiate credits or switch providers.

**Real-time circuit health:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-1h
| stats avg(latency) as latency avg(loss_percentage) as loss avg(jitter) as jitter by site_id, local_color
| lookup sdwan_circuit_sla.csv site_id, color as local_color OUTPUT provider circuit_id contract_latency_ms contract_loss_pct monthly_cost
| where isnotnull(provider)
| eval latency_ratio=round(latency/contract_latency_ms, 2)
| eval loss_ratio=round(loss/contract_loss_pct, 2)
| eval risk=case(latency_ratio > 1.5 OR loss_ratio > 2, "HIGH", latency_ratio > 1 OR loss_ratio > 1, "BREACHING", latency_ratio > 0.8 OR loss_ratio > 0.8, "APPROACHING", 1==1, "OK")
| where risk!="OK"
| lookup sdwan_sites.csv site_id OUTPUT site_name
| sort risk
```

**Provider performance comparison:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-30d@d latest=@d
| stats avg(latency) as avg_latency avg(loss_percentage) as avg_loss p95(latency) as p95_latency by local_color
| lookup sdwan_circuit_sla.csv color as local_color OUTPUT provider contract_latency_ms contract_loss_pct
| where isnotnull(provider)
| stats avg(avg_latency) as fleet_avg_latency avg(p95_latency) as fleet_p95_latency avg(avg_loss) as fleet_avg_loss count as circuit_count by provider
| sort fleet_p95_latency
```

### Step 3 — Validate
(a) Cross-check SLA report with ISP's own SLA reports for the same circuits and time period.
(b) Verify circuit ID mapping: ensure `sdwan_circuit_sla.csv` has correct circuit IDs matching ISP billing.
(c) Validate SLA thresholds: confirm contract values match actual ISP agreements.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Transport SLA Tracking"):
- Row 1 — Single-value tiles: "Circuits meeting SLA", "Circuits breaching SLA", "SLA credit eligible", "Total monthly WAN spend".
- Row 2 — Monthly SLA compliance table: site, provider, circuit, contract metrics, actual metrics, pass/fail.
- Row 3 — Real-time circuit risk table: circuits approaching or breaching SLA.
- Row 4 — Provider performance comparison chart.

Alerting:
- High (circuit SLA breached for > 4 hours): document for SLA credit claim.
- Warning (circuit approaching SLA threshold): proactive monitoring.
- Monthly (scheduled report): SLA compliance summary for ISP vendor management.

### Step 5 — Troubleshooting

- **SLA always shows PASS but users complain** — The SLA contract may be too lenient (e.g., latency < 200ms), while applications need < 50ms. Review SLA thresholds against actual application requirements, not just contract terms.

- **P95 latency much higher than average** — Indicates periodic spikes (e.g., congestion during business hours). The average may look fine, but users experience the P95 as sluggish performance at specific times.

- **No data for some circuits** — The BFD session may not be associated with the correct transport color. Verify the WAN interface is configured with the right color in the device template.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss, count as samples by local_color, site_id, remote_system_ip
| eval sla_latency=50, sla_loss=0.1
| eval latency_breach=if(avg_latency>sla_latency,"YES","NO"), loss_breach=if(avg_loss>sla_loss,"YES","NO")
| where latency_breach="YES" OR loss_breach="YES"
| table site_id local_color avg_latency p95_latency avg_jitter avg_loss latency_breach loss_breach
```

## Visualization

Table (circuit SLA compliance), Line chart (latency trending per carrier), Single value (overall SLA compliance %).

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
