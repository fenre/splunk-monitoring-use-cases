<!-- AUTO-GENERATED from UC-5.13.69.json — DO NOT EDIT -->

---
id: "5.13.69"
title: "Catalyst Center + SD-WAN WAN Path Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.69 · Catalyst Center + SD-WAN WAN Path Health

## Description

Correlates Catalyst Center campus network health with SD-WAN WAN path health to provide an end-to-end view and detect scenarios where campus or WAN is the bottleneck.

## Value

Users experience the entire path — campus LAN plus WAN. Correlating both domains shows whether poor experience is caused by local infrastructure or WAN quality.

## Implementation

Both Catalyst Center and SD-WAN data come from the same TA (7538). Ensure both are configured:

1. **Catalyst Center:** Already configured for network health UCs
2. **SD-WAN account:** Add an SD-WAN account in the TA pointing to your vManage/SD-WAN Manager
3. **Enable SD-WAN inputs:** Enable `health` and `site_and_tunnel_health` inputs → `index=sdwan`
4. **Correlation:** Time-based correlation using `appendcols` — both health scores are time-series

## Detailed Implementation

Prerequisites
• UC-5.13.16 (network health) live on `cisco:dnac:networkhealth`.
• SD-WAN vManage/manager account in TA 7538 with `cisco:sdwan:*` data landing in `index=sdwan` (confirm your index name; update the SPL if you use a different index).

Step 1 — vManage and TA
- In TA 7538, add SD-WAN credentials (OAuth or API per TA version) pointing at your SD-WAN Manager base URL.
- Enable health-related modular inputs: **health** and **site_and_tunnel_health**; note poll intervals (typically minutes).
- Map fields: `health_score` on SD-WAN side vs `healthScore` on Catalyst — the SPL already aliases via `as` in `stats`.

Step 2 — Time alignment
- `appendcols` matches rows 1:1; for sparse polls, use `| bin _time span=5m` on both subsearches or switch to `| timechart` + `| join _time` for stricter bucketing in production.
- Validate clock skew between Splunk, Catalyst Center, and vManage; skew breaks correlation.

Step 3 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health by _time | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health by _time] | eval combined_health=round((campus_health+wan_health)/2,1) | eval health_gap=abs(campus_health-wan_health) | where health_gap > 20 | table _time campus_health wan_health combined_health health_gap
```

Step 4 — Interpretation
- **Large health_gap, campus high / WAN low:** focus on underlays, transport circuits, and SD-WAN policy.
- **WAN healthy, campus low:** campus switching, site LAN, or Assurance issue storms.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health by _time | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health by _time] | eval combined_health=round((campus_health+wan_health)/2,1) | eval health_gap=abs(campus_health-wan_health) | where health_gap > 20 | table _time campus_health wan_health combined_health health_gap
```

## Visualization

Time-series line chart: campus_health, wan_health, health_gap; single-value for combined_health when gap exceeds threshold; optional alert on sustained divergence.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
