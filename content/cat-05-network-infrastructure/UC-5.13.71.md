<!-- AUTO-GENERATED from UC-5.13.71.json — DO NOT EDIT -->

---
id: "5.13.71"
title: "Catalyst Center + ThousandEyes Network Path Correlation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.71 · Catalyst Center + ThousandEyes Network Path Correlation

## Description

Correlates Catalyst Center internal network health with ThousandEyes external path quality to isolate whether performance problems are inside the campus network or on the WAN/internet path.

## Value

The hardest troubleshooting question is 'is it us or them?' Correlating internal health (Catalyst Center) with external path quality (ThousandEyes) answers this question in seconds.

## Implementation

1. **Catalyst Center (TA 7538):** `cisco:dnac:networkhealth` on `index=catalyst` with `healthScore` (UC-5.13.16).
2. **ThousandEyes (app 7719):** Install and connect Te OTel/HTTP to Splunk per app docs; create or confirm the **`stream_index`** macro to point at the index containing Te agent-to-server test metrics (often a dedicated HEC/OTel index).
3. **Field model:** The SPL uses `thousandeyes.test.type` and `network.latency` / `network.loss` in OTel-style JSON — if your app normalizes to different field names, update the `stats` to match (e.g. `avg(latency_ms)`).
4. **Thresholds:** Tune `70`, `100` ms, and `5%` loss to your SLAs and baseline noise.

## Detailed Implementation

Prerequisites
• Network health on Catalyst (7538) and ThousandEyes tests streaming to Splunk via app 7719 with a **`stream_index`** macro defined in Settings → Advanced search → Macros (or the app’s default).
• Agent-to-server tests in ThousandEyes covering paths that matter to the same user population as the Catalyst sites you monitor.

Step 1 — ThousandEyes app 7719
- Install from Splunkbase; configure HEC/OTel ingestion per the app’s setup guide; verify `thousandeyes` tagged events land in the index the macro `stream_index` references.
- In Search: `` `stream_index` `` `thousandeyes` `| head 5` to confirm `network.latency` (or equivalent) and `thousandeyes.test.type` fields exist.

Step 2 — Time alignment
- `appendcols` is fragile under uneven poll rates; in production, use `| bin _time span=1m` on both sides before `appendcols` or use `| join` on binned time.

Step 3 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as internal_health by _time | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by _time | eval avg_latency_ms=round(avg_latency_s*1000,1) | eval loss_pct=round(avg_loss*100,1)] | where internal_health < 70 AND (avg_latency_ms > 100 OR loss_pct > 5) | eval isolation=if(internal_health<70 AND avg_latency_ms<50, "Internal network issue", if(internal_health>=70 AND avg_latency_ms>100, "External path issue", "Both internal and external issues")) | table _time internal_health avg_latency_ms loss_pct isolation
```

Step 4 — Runbook
- **Internal network issue** — start at Assurance, site topology, and campus uplinks.
- **External path issue** — use ThousandEyes path visualization and change ISP/cloud targets.
- **Both** — split war-room: NOC (campus) and cloud/WAN (Te).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as internal_health by _time | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by _time | eval avg_latency_ms=round(avg_latency_s*1000,1) | eval loss_pct=round(avg_loss*100,1)] | where internal_health < 70 AND (avg_latency_ms > 100 OR loss_pct > 5) | eval isolation=if(internal_health<70 AND avg_latency_ms<50, "Internal network issue", if(internal_health>=70 AND avg_latency_ms>100, "External path issue", "Both internal and external issues")) | table _time internal_health avg_latency_ms loss_pct isolation
```

## Visualization

Table of internal_health, avg_latency_ms, loss_pct, isolation; optional Sankey or treemap of isolation reason counts; timechart overlay: internal_health vs Te latency.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ThousandEyes App (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
