---
id: "5.13.73"
title: "Multi-Domain Network Health Executive Dashboard"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.73 · Multi-Domain Network Health Executive Dashboard

## Description

Provides a unified executive dashboard combining health scores from Catalyst Center (campus), SD-WAN (WAN), Meraki (branch), and ThousandEyes (external paths) into a single multi-domain view.

## Value

Executives need one view of network health, not four consoles. This dashboard combines all Cisco network domains into a single composite health score.

## Implementation

1. **7538 (Catalyst, SD-WAN, optional Cyber Vision):** Configure Catalyst Center + vManage per UC-5.13.1 / UC-5.13.16 / UC-5.13.69.
2. **5580 (Meraki):** Org API to `meraki:api` in `index=cisco_network` (UC-5.13.70).
3. **7719 (ThousandEyes):** OTel stream + **`stream_index`** macro for agent-to-server tests (UC-5.13.71).
4. **Composite:** The `coalesce` terms avoid null WAN/branch in partial deployments; replace with 0 or separate panels if you need strict math.
5. **Dashboard:** Dashboard Studio (or Simple XML) with one row per domain + headline single values for `overall_health` and `te_latency_ms`.

## Detailed Implementation

Prerequisites
• UCs 5.13.16, 5.13.68, 5.13.69, 5.13.71 implemented and validated; all feeds healthy (see UC-5.13.74 for pipeline health).
• Indexes: `catalyst`, `sdwan` (or your SD-WAN index), `cisco_network` for Meraki, Te index behind **`stream_index`**.

Step 1 — Data contracts
- Document canonical fields: `healthScore` (campus), `health_score` (SD-WAN), `health_score` (Meraki), `network.latency` (ThousandEyes OTel) — all four must be visible in a test time range before publishing the panel.
- Align Meraki/SD-WAN field names via `eval` in the `stats` that feed `appendcols` if your build differs from the example.

Step 2 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health] | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health] | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as te_latency_s | eval te_latency_ms=round(te_latency_s*1000,1)] | eval overall_health=round((campus_health+coalesce(wan_health,campus_health)+coalesce(branch_health,campus_health))/3,1) | table campus_health wan_health branch_health te_latency_ms overall_health
```

Step 3 — Executive UX
- Use consistent color bands (e.g. green >80, yellow 60–80, red <60) for health scores; show Te latency in ms with a red threshold line.
- Add deep links: campus → Network Health UC; WAN → 5.13.69; ISE/cross-product → 5.13.68; Te path → 5.13.71.

Step 4 — Governance
- Review weekly: missing inputs (`coalesce` hiding gaps), macro drift on **`stream_index`**, and SD-WAN/Meraki API credential expiry.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health] | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health] | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as te_latency_s | eval te_latency_ms=round(te_latency_s*1000,1)] | eval overall_health=round((campus_health+coalesce(wan_health,campus_health)+coalesce(branch_health,campus_health))/3,1) | table campus_health wan_health branch_health te_latency_ms overall_health
```

## Visualization

Executive row: large single values for campus_health, wan_health, branch_health, te_latency_ms, overall_health; treemap of domain status; link-out drilldowns to UC-5.13.68–5.13.72 panel searches.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ThousandEyes App (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Cisco Meraki Add-on (Splunkbase 5580)](https://splunkbase.splunk.com/app/5580)
