<!-- AUTO-GENERATED from UC-5.13.73.json — DO NOT EDIT -->

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
• UCs 5.13.16 (campus health), 5.13.69 (SD-WAN), 5.13.70 (Meraki), and 5.13.71 (ThousandEyes) each feeding their respective indexes, plus UC-5.13.74 for `cisco:dnac:*` pipeline health.
• Indexes: `catalyst`, `sdwan` (or your SD-WAN index), `cisco_network` (Meraki), and the ThousandEyes index behind the **`stream_index`** macro.

Step 1 — Data contracts (Catalyst Center + vManage + Meraki + Te)
• Document canonical fields: `healthScore` (campus), `health_score` (SD-WAN and Meraki), and `network.latency` in seconds or ms from ThousandEyes — confirm a **test** search over the same 24h for each product before the executive board meets.
• Align field names in `eval` on each `appendcols` branch if your TA version differs; never assume Meraki and SD-WAN use the same 0–100 scale without checking sample events.

Step 2 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health] | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health] | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as te_latency_s | eval te_latency_ms=round(te_latency_s*1000,1)] | eval overall_health=round((campus_health+coalesce(wan_health,campus_health)+coalesce(branch_health,campus_health))/3,1) | table campus_health wan_health branch_health te_latency_ms overall_health
```

Step 3 — Executive UX
• Use a consistent green/yellow/red band for the three **health** numbers; show ThousandEyes latency in ms on its own scale so execs are not misled by a single blended score for internet quality.
• **Deep links:** campus → network health (UC-5.13.16); WAN → UC-5.13.69; Meraki → UC-5.13.70; Te → UC-5.13.71. (ISE correlation is a separate use case; add UC-5.13.68 as an adjacent link only if you have ISE in scope.)

Step 4 — Governance
• Weekly: confirm no domain is silently missing (watch `coalesce` masking null WAN or branch in the average). Rotate API credentials for SD-WAN, Meraki, and ThousandEyes per vendor policy; after Catalyst Center upgrades, re-validate the `stream_index` macro still points to the HEC/OTel index you expect.


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
