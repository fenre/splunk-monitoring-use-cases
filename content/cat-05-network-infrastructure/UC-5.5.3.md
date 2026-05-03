<!-- AUTO-GENERATED from UC-5.5.3.json — DO NOT EDIT -->

---
id: "5.5.3"
title: "Application SLA Violations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.3 · Application SLA Violations

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Detects when business-critical applications aren't meeting performance requirements over the WAN.

## Value

Network operations teams detect when SD-WAN tunnels violate application-specific SLA thresholds for voice, video, and business-critical traffic, enabling targeted troubleshooting and validating automatic path failover.

## Implementation

Collect app-aware routing statistics from vManage. Alert when critical applications violate their SLA class.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for application-aware routing (AAR) statistics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:approute`. Key fields: `site_id`, `system_ip`, `app_route_name` (SLA policy name), `loss`, `latency`, `jitter`, `mean_loss`, `mean_latency`, `mean_jitter`, `sla_class`.
- SD-WAN application SLAs define the maximum tolerable loss, latency, and jitter for application classes. These are configured in vManage under Configuration > Policies > Application-Aware Routing. Common SLA classes: Voice (loss < 1%, latency < 150ms, jitter < 30ms), Real-Time Video (loss < 0.5%, latency < 200ms, jitter < 50ms), Business Critical (loss < 3%, latency < 300ms), Default (loss < 10%, latency < 500ms).
- Build an `sdwan_sla_policies.csv` lookup: `sla_class,max_loss,max_latency,max_jitter,app_examples` (e.g., `VoiceAndVideo,1,150,30,UC/Webex/Teams`).
- When an SLA is violated, SD-WAN should automatically switch to a better path. This UC monitors both the SLA violations (indicating transport problems) and whether the failover worked (traffic moved to a path that meets SLA).

### Step 1 — Configure data collection
Verify application-aware routing data:
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-15m
| stats count by sla_class, site_id
```

### Step 2 — Create the search and alert

**Primary search — Application SLA violations by site:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-15m
| lookup sdwan_sla_policies.csv sla_class OUTPUT max_loss max_latency max_jitter app_examples
| eval loss_violation=if(isnotnull(max_loss) AND mean_loss > max_loss, 1, 0)
| eval latency_violation=if(isnotnull(max_latency) AND mean_latency > max_latency, 1, 0)
| eval jitter_violation=if(isnotnull(max_jitter) AND mean_jitter > max_jitter, 1, 0)
| eval any_violation=if(loss_violation + latency_violation + jitter_violation > 0, 1, 0)
| where any_violation=1
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval violation_detail=case(loss_violation=1 AND latency_violation=1, "Loss + Latency", loss_violation=1, "Loss only", latency_violation=1, "Latency only", jitter_violation=1, "Jitter only", 1==1, "Multiple")
| table _time, site_name, tier, sla_class, app_examples, mean_loss, max_loss, mean_latency, max_latency, mean_jitter, max_jitter, violation_detail
| sort tier, site_name
```

#### Understanding this SPL: Compares real-time tunnel metrics against configured SLA thresholds per application class. This tells you not just that a tunnel is bad, but which applications are impacted. A tunnel with 2% loss violates Voice SLA but passes Default SLA — the impact is voice quality, not general connectivity.

**SLA violation trending by application class:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-24h
| lookup sdwan_sla_policies.csv sla_class OUTPUT max_loss max_latency max_jitter
| eval violated=if((isnotnull(max_loss) AND mean_loss > max_loss) OR (isnotnull(max_latency) AND mean_latency > max_latency) OR (isnotnull(max_jitter) AND mean_jitter > max_jitter), 1, 0)
| bin _time span=15m
| stats sum(violated) as violations count as total by _time, sla_class
| eval violation_rate=round(100*violations/total, 1)
```

**Worst-performing sites for voice SLA:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" sla_class="VoiceAndVideo" earliest=-4h
| stats avg(mean_loss) as avg_loss avg(mean_latency) as avg_latency avg(mean_jitter) as avg_jitter by site_id
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval voice_score=round(100 - (avg_loss*10 + avg_latency*0.1 + avg_jitter*0.5), 1)
| sort voice_score
| head 10
```

### Step 3 — Validate
(a) In vManage: Monitor > Application-Aware Routing. Compare SLA violation count with Splunk results.
(b) During a controlled test: degrade a WAN link (traffic shaping to add loss) and verify SLA violations appear.
(c) Verify that SD-WAN path failover worked: after an SLA violation, check if traffic moved to an alternate path.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Application SLA"):
- Row 1 — Single-value tiles: "Voice SLA violations (1h)", "Video SLA violations", "Business SLA violations", "Sites with violations".
- Row 2 — SLA violation table: site, SLA class, applications, violation detail, metrics vs. thresholds.
- Row 3 — Voice quality heatmap: sites ranked by voice score (0-100).
- Row 4 — Violation trending by SLA class over 24h.

Alerting:
- Critical (Voice SLA violation on Tier1 site > 5 min): call quality impacted — alert UC team and NOC.
- High (Business Critical SLA violation sustained): alert application owners.
- Warning (Default SLA violation): monitor — may indicate degrading transport.

Runbook:
1. **Voice SLA violation**: Check tunnel metrics (UC-5.5.1). If one transport is degraded, verify AAR policy is failing over to backup transport. If all transports are bad, escalate to ISP.
2. **SLA violations across many sites simultaneously**: Check the controller (vSmart) and vManage health. A controller issue can disrupt all sites' policy enforcement.

### Step 5 — Troubleshooting

- **SLA class field is empty or "None"** — Application-Aware Routing policy may not be applied to the device template. Check vManage: Configuration > Templates > device template > Application-Aware Routing.

- **SLA violations detected but no path failover** — AAR policy may be configured for monitoring only (not enforcement). Check if the policy action is "SLA class list" with backup preferred colors configured.

- **mean_loss and mean_latency show different values than vManage** — The TA polls API at intervals; vManage shows aggregated/smoothed data. Small differences are expected. Large differences indicate a polling or parsing issue.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:approute"
| where sla_violation="true"
| stats count by site, app_name, sla_class | sort -count
```

## Visualization

Table (site, app, violations), Bar chart by app, Timechart.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
