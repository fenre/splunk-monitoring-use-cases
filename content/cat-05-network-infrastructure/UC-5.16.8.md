<!-- AUTO-GENERATED from UC-5.16.8.json — DO NOT EDIT -->

---
id: "5.16.8"
title: "High-Latency Path Detection (Pre/Post Optimization Delta)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.16.8 · High-Latency Path Detection (Pre/Post Optimization Delta)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Anomaly, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure travel time before and after the shortcut is applied. When the trip still feels endless even after the shortcut, something on the road—or the shortcut itself—is wrong, and we flag it before folks blame the computers at their desks.*

---

## Description

Splunk flags flows whose inner latency remains chronically high while optimization subtracts almost nothing—highlighting brownfield circuits, miswired asymmetric routing, or misapplied policies masquerading as optimized paths.

## Value

Engineers differentiate WAN backbone congestion from optimizer misconfiguration faster while executives gain trustworthy SaaS experience narratives anchored to measured delta stagnation.

## Implementation

Normalize probes every five minutes per site, maintain adaptive baseline via `predict`, suppress alerts during carrier-declared maintenance windows stored in lookup.

## Detailed Implementation

### Prerequisites
- Consistent probe endpoints across branches referencing identical SaaS or DC targets.
- Documentation labeling measurement insertion points (LAN vs WAN side taps).
- Cooperation from carriers when escalating backbone latency proofs.

### Step 1 — Configure data collection
Deploy lightweight synthetic agents writing JSON latency tuples via HEC; mirror appliance-native latency feeds into same sourcetype namespace.

### Step 2 — Create the search and alert
Materialize SPL as `wanopt_latency_delta_gap`; alert when samples>=12/hour and avg_delta_ms<=5 while avg_pre_ms>=180.

### Step 3 — Validate
Compare to traceroute archives and carrier PM tickets—ensure Splunk aligns with carrier MTTR narratives.

### Step 4 — Operationalize
Dashboard overlays map site_code coloring severity with drilldown traceroute runbook buttons.

### Step 5 — Troubleshooting
**UDP vs TCP probes:** reconcile methodology.**Satellite backhaul:** elevate thresholds ethically.**DNS geo-steering:** rotating destinations confuse aggregates—anchor FQDN.**ZDX-only legs:** confirm optimizers actually sit in path via CMDB.

## SPL

```spl
index=wanop OR index=network earliest=-24h latest=now
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval pre_ms=tonumber(coalesce(latency_before_ms,rtt_inner_ms,wano_inner_rtt))
| eval post_ms=tonumber(coalesce(latency_after_ms,rtt_outer_ms,wano_outer_rtt))
| eval delta_ms=if(isnotnull(pre_ms) AND isnotnull(post_ms), pre_ms-post_ms, null())
| eval app=coalesce(application,app_name,target_saas,"unspecified")
| where isnotnull(pre_ms) AND pre_ms>=120
| eval stalled_opt=if(isnull(delta_ms),1,if(delta_ms<10 AND pre_ms>=120,1,0))
| where stalled_opt=1
| stats avg(pre_ms) as avg_pre_ms avg(post_ms) as avg_post_ms avg(delta_ms) as avg_delta_ms count as samples dc(host) as appliance_hops by vendor app site_code
| eval severity=case(avg_pre_ms>=250,"critical",avg_pre_ms>=180,"high","medium")
| sort - avg_pre_ms vendor app
| head 200
```

## Visualization

Scatter plot avg_pre_ms vs avg_delta_ms with quadrant thresholds; companion table listing worst apps per vendor.

## Known False Positives

**Long-haul physics:** extreme distances limit optimization gains.**Encrypted UDP workloads:** latency unchanged legitimately.**Telemetry skew:** sporadic sampling triggers false stalls—enforce minimum counts.**Multi-cloud anycast:** rotating POPs inflate variance.

## References

- [Splunk Lantern — Synthetic monitoring patterns](https://lantern.splunk.com/Observability_Applications)
- [Zscaler Help — ZDX Administration Guide](https://help.zscaler.com/zdx)
