<!-- AUTO-GENERATED from UC-5.5.16.json — DO NOT EDIT -->

---
id: "5.5.16"
title: "Cloud OnRamp Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.16 · Cloud OnRamp Performance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Cloud OnRamp probes SaaS and IaaS endpoints from each site to select the best path. Monitoring probe results reveals when cloud application performance degrades before users open tickets, and validates that SD-WAN is actually improving cloud access.

## Value

Network operations teams monitor SD-WAN Cloud OnRamp performance to cloud providers (AWS, Azure, GCP) and SaaS applications (O365, Webex), ensuring optimal path selection and detecting cloud connectivity degradation.

## Implementation

Enable Cloud OnRamp for SaaS (Microsoft 365, Webex, Salesforce, etc.) and/or IaaS (AWS, Azure, GCP) in vManage. Collect vQoE scores and probe metrics. Alert when a SaaS application's quality score drops below 8 (out of 10) or latency exceeds 150ms. Compare direct internet access (DIA) vs gateway exit paths to validate routing decisions.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for Cloud OnRamp statistics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:cloudonramp` or `sourcetype=cisco:sdwan:approute` (cloud-bound traffic). Key fields: `site_id`, `system_ip`, `cloud_provider` (aws/azure/gcp), `cloud_region`, `gateway_ip`, `latency`, `loss`, `jitter`, `app_name`, `cloud_type` (SaaS/IaaS).
- Cloud OnRamp optimizes traffic to cloud services: (1) Cloud OnRamp for SaaS — measures performance to SaaS apps (O365, Salesforce, Webex) from each site and directs traffic to the best performing path, (2) Cloud OnRamp for IaaS — extends SD-WAN fabric into AWS/Azure/GCP via transit gateways. (3) Cloud OnRamp for Colocation — connects to cloud providers via a colocation facility.
- Build `sdwan_cloud_sla.csv` lookup: `cloud_provider,cloud_region,service,max_latency_ms,max_loss_pct` (e.g., `aws,us-east-1,IaaS,50,0.1`, `microsoft365,global,SaaS,100,0.5`).

### Step 1 — Configure data collection
Verify Cloud OnRamp data:
```spl
index=sdwan (sourcetype="cisco:sdwan:cloudonramp" OR sourcetype="cisco:sdwan:approute") earliest=-1h
| search cloud* OR saas* OR aws OR azure OR gcp
| stats count by sourcetype, cloud_provider
```

### Step 2 — Create the search and alert

**Primary search — Cloud OnRamp performance by provider and region:**
```spl
index=sdwan sourcetype="cisco:sdwan:cloudonramp" earliest=-1h
| stats avg(latency) as avg_latency avg(loss) as avg_loss avg(jitter) as avg_jitter p95(latency) as p95_latency count as samples by site_id, cloud_provider, cloud_region, cloud_type
| lookup sdwan_cloud_sla.csv cloud_provider, cloud_region OUTPUT max_latency_ms max_loss_pct
| eval latency_status=case(avg_latency > max_latency_ms * 1.5, "CRITICAL", avg_latency > max_latency_ms, "WARNING", 1==1, "OK")
| eval loss_status=case(avg_loss > max_loss_pct * 2, "CRITICAL", avg_loss > max_loss_pct, "WARNING", 1==1, "OK")
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval overall=case(latency_status="CRITICAL" OR loss_status="CRITICAL", "CRITICAL", latency_status="WARNING" OR loss_status="WARNING", "WARNING", 1==1, "OK")
| where overall!="OK"
| sort overall, cloud_provider
```

#### Understanding this SPL: Cloud OnRamp performance directly impacts user experience with cloud applications. If the path to AWS us-east-1 from a branch has 200ms latency, all AWS-hosted applications at that branch suffer. Cloud OnRamp measures this continuously and can dynamically switch from Internet to MPLS (or vice versa) for cloud traffic — this search validates whether the selected path actually meets SLA.

**SaaS application vQoE (Virtual Quality of Experience) scores:**
```spl
index=sdwan sourcetype="cisco:sdwan:cloudonramp" cloud_type="SaaS" earliest=-4h
| stats avg(latency) as latency avg(loss) as loss by site_id, app_name
| eval vqoe_score=round(100 - (loss*20 + latency*0.2), 1)
| eval vqoe_score=if(vqoe_score < 0, 0, vqoe_score)
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval rating=case(vqoe_score > 90, "Excellent", vqoe_score > 70, "Good", vqoe_score > 50, "Fair", 1==1, "Poor")
| sort vqoe_score
```

**Cloud gateway utilization:**
```spl
index=sdwan sourcetype="cisco:sdwan:cloudonramp" cloud_type="IaaS" earliest=-4h
| stats sum(bytes) as total_bytes dc(site_id) as connected_sites by cloud_provider, cloud_region, gateway_ip
| eval total_gb=round(total_bytes/1073741824, 2)
| sort cloud_provider, cloud_region
```

### Step 3 — Validate
(a) In vManage: Monitor > Cloud OnRamp for SaaS/IaaS. Compare latency and vQoE scores with Splunk results.
(b) Run a speed test to a cloud provider from a branch site and compare with the Cloud OnRamp metrics.
(c) Verify cloud SLA lookup against actual cloud provider SLAs (AWS/Azure/GCP published latency targets).

### Step 4 — Operationalize
Dashboard ("SD-WAN — Cloud OnRamp"):
- Row 1 — Single-value tiles: "Cloud connections", "SaaS vQoE < 70", "IaaS latency > SLA", "Cloud providers monitored".
- Row 2 — SaaS vQoE table: site, application, vQoE score, latency, loss, rating.
- Row 3 — IaaS performance table: cloud provider, region, gateway, latency vs. SLA, connected sites.
- Row 4 — Cloud performance trending by provider/region.

Alerting:
- Critical (cloud latency > 1.5× SLA for > 10 minutes): cloud applications severely impacted.
- High (SaaS vQoE < 50 for critical apps like O365/Webex): user experience degraded.
- Warning (cloud latency > SLA threshold): monitor for worsening trend.

### Step 5 — Troubleshooting

- **Cloud OnRamp data not arriving** — Cloud OnRamp may not be enabled on the device template. Check vManage: Configuration > Templates > Cloud OnRamp settings.

- **High latency to AWS from specific sites but not others** — The site's Internet path to the AWS region may be suboptimal. Cloud OnRamp should select the best path, but if all paths are bad, the issue is geographic or ISP-related.

- **vQoE scores inconsistent** — vQoE is a composite score that can fluctuate with transient network conditions. Use 15-minute averages rather than point-in-time values for trend analysis.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:cloudx"
| stats avg(vqoe_score) as avg_score, avg(latency) as avg_latency, avg(loss) as avg_loss by app_name, site_id, exit_type
| where avg_score < 8 OR avg_latency > 150
| sort avg_score
| table app_name site_id exit_type avg_score avg_latency avg_loss
```

## Visualization

Line chart (vQoE score trending per app), Table (underperforming apps), Bar chart (DIA vs gateway comparison).

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
