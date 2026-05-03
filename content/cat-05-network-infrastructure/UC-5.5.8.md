<!-- AUTO-GENERATED from UC-5.5.8.json — DO NOT EDIT -->

---
id: "5.5.8"
title: "Jitter and Latency per Tunnel"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.8 · Jitter and Latency per Tunnel

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.

## Value

Network operations teams monitor per-tunnel jitter and latency against voice/video SLA thresholds and historical baselines, enabling proactive detection of transport degradation before real-time application quality suffers.

## Implementation

Ingest BFD and app-route statistics from vManage API. Monitor per-tunnel quality metrics. Alert when latency >100ms, jitter >30ms, or loss >1% for business-critical SLAs.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for BFD session statistics and application-aware routing metrics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:bfd` or `sourcetype=cisco:sdwan:approute`. Key fields: `site_id`, `system_ip`, `tunnel_name`, `local_color`, `remote_color`, `latency` (ms), `jitter` (ms), `loss_percentage`.
- Jitter and latency are the primary indicators of real-time application quality. Voice calls degrade noticeably at > 150ms latency and > 30ms jitter. Video conferencing is impacted at > 200ms latency. SD-WAN BFD probes measure these metrics per tunnel, per transport color.
- Build `sdwan_tunnel_baselines.csv` lookup: `site_id,local_color,baseline_latency_ms,baseline_jitter_ms` from a week of normal operation. This enables anomaly detection beyond static thresholds.

### Step 1 — Configure data collection
Verify per-tunnel metrics:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats avg(latency) as avg_latency avg(jitter) as avg_jitter by site_id, tunnel_name, local_color
| sort -avg_latency
```

### Step 2 — Create the search and alert

**Primary search — Per-tunnel jitter and latency with SLA evaluation:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats avg(latency) as avg_latency avg(jitter) as avg_jitter max(latency) as peak_latency max(jitter) as peak_jitter p95(latency) as p95_latency p95(jitter) as p95_jitter by site_id, system_ip, tunnel_name, local_color, remote_color
| lookup sdwan_tunnel_baselines.csv site_id, local_color OUTPUT baseline_latency_ms baseline_jitter_ms
| eval latency_deviation=if(isnotnull(baseline_latency_ms), round(avg_latency - baseline_latency_ms, 1), null())
| eval jitter_deviation=if(isnotnull(baseline_jitter_ms), round(avg_jitter - baseline_jitter_ms, 1), null())
| eval voice_impact=if(avg_latency > 150 OR avg_jitter > 30, "YES", "NO")
| eval video_impact=if(avg_latency > 200 OR avg_jitter > 50, "YES", "NO")
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval status=case(avg_latency > 300 OR avg_jitter > 100, "CRITICAL", voice_impact="YES", "HIGH", latency_deviation > 50, "ELEVATED", 1==1, "OK")
| where status!="OK"
| sort status, -avg_latency
```

#### Understanding this SPL: Combines static SLA thresholds (voice at 150ms/30ms) with baseline deviation analysis. A tunnel normally at 20ms latency suddenly jumping to 80ms is concerning even though it's below the 150ms voice threshold — it indicates a transport issue that could worsen. P95 metrics show tail latency, which impacts user experience during bursts.

**Latency heatmap over time:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-24h
| bin _time span=5m
| stats avg(latency) as latency by _time, site_id, local_color
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval label=site_name." (".local_color.")"
| xyseries _time label latency
```

**Jitter correlation with packet loss:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-4h
| stats avg(jitter) as jitter avg(loss_percentage) as loss avg(latency) as latency by site_id, local_color
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval quality_score=round(100 - (loss*10 + latency*0.2 + jitter*0.5), 1)
| sort quality_score
```

### Step 3 — Validate
(a) Run a voice call (Webex/Teams) between two SD-WAN sites and compare MOS scores with tunnel metrics during the call.
(b) In vManage: Monitor > Application-Aware Routing > select device > chart latency/jitter per tunnel. Values should match Splunk within the polling interval.
(c) Validate baseline lookup: ensure values reflect actual normal-operation metrics.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Tunnel Quality"):
- Row 1 — Single-value tiles: "Tunnels impacting voice", "Tunnels impacting video", "Worst latency (ms)", "Worst jitter (ms)".
- Row 2 — Tunnel quality table: site, tunnel, transport, latency (avg/p95/peak), jitter (avg/p95/peak), voice impact, video impact.
- Row 3 — Latency heatmap: sites × time (color intensity = latency).
- Row 4 — Quality score ranking: sites sorted by composite quality score.

Alerting:
- Critical (tunnel latency > 300ms or jitter > 100ms): unusable for real-time applications.
- High (voice impact on Tier1 site): call quality degraded.
- Warning (baseline deviation > 50ms): transport quality changing — investigate.

### Step 5 — Troubleshooting

- **High latency on Internet tunnels but not MPLS** — Expected during ISP congestion. If persistent, consider upgrading the Internet circuit or adjusting AAR policy to prefer MPLS for sensitive traffic.

- **High jitter on all tunnels at one site** — Check the edge device CPU utilization (UC-5.5.13). High data-plane CPU causes packet processing delays, which manifest as jitter on all tunnels.

- **Latency spikes at specific times daily** — Often caused by backup jobs or large file transfers saturating the WAN link. Correlate with bandwidth utilization (UC-5.5.7) and DPI data (UC-5.5.15) to identify the application.

## SPL

```spl
index=network sourcetype="cisco:sdwan:approute"
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss by local_system_ip, remote_system_ip, local_color
| where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1
| sort -avg_latency
```

## Visualization

Line chart (latency/jitter over time), Table (tunnel, metrics), Gauge (SLA compliance).

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
