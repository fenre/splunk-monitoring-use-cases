<!-- AUTO-GENERATED from UC-2.6.63.json — DO NOT EDIT -->

---
id: "2.6.63"
title: "DaaS Autoscale Cloud Economics Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.63 · DaaS Autoscale Cloud Economics Tracking

## Description

DaaS autoscale can chase session demand, but public-cloud bills reflect clock time, instance families, and lingering powered-on capacity as much as user counts. Blending host-pool or delivery-group session peaks with tag-aligned cloud spend shows scale-out efficiency, expensive idle headroom, and cost-per-active-session trends. Finance and platform teams get a defensible way to right-size buffer percentages, change instance SKUs, or tune shutdown aggressiveness without only trusting static dashboards in the admin consoles.

## Value

DaaS autoscale can chase session demand, but public-cloud bills reflect clock time, instance families, and lingering powered-on capacity as much as user counts. Blending host-pool or delivery-group session peaks with tag-aligned cloud spend shows scale-out efficiency, expensive idle headroom, and cost-per-active-session trends. Finance and platform teams get a defensible way to right-size buffer percentages, change instance SKUs, or tune shutdown aggressiveness without only trusting static dashboards in the admin consoles.

## Implementation

Tag or label cloud VMs with a stable `citrix_host_pool` value matching Splunk's brokering or MCS data. Ingest a daily (or hourly) cost feed with the same key. Build weekly reports: cost per session by pool, unused powered-on hours, and autoscale event counts versus cost deltas. Set soft alerts for sudden jumps in cost-per-session or sustained idle high-water marks after scale events. Engage FinOps to validate currency and amortization. Never alert on cost alone without a session denominator except for obvious billing anomalies. Document that bursty test traffic can skew short windows.

## Detailed Implementation

Prerequisites
• Consistent resource tagging; billing API permissions; at least 14 days of both cost and session history before trusting ratios.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map catalog or delivery group names in Citrix to tag keys. Fix any untagged SKUs in cloud before go-live to avoid a large unmapped spend bucket.

Step 2 — Create the search and alert
Start with a monthly executive summary; set anomaly alerts on week-over-week cost-per-session per pool using `anomalydetection` or static thresholds.

Step 3 — Validate
Reconcile a single pool for one day against the cloud console subtotal; reconcile session peaks against Citrix Director or equivalent.

Step 4 — Operationalize
Tie into FinOps and change management when autoscale policy or instance family changes are proposed.

## SPL

```spl
index=cloud sourcetype="azure:consume:export" (resource_type="*compute*" OR resource_type="*virtual*")
| eval tag_pool=if(isnotnull(citrix_host_pool) AND citrix_host_pool!="", citrix_host_pool, coalesce(resource_name, resource_id, "unmapped"))
| bin _time span=1d
| stats sum(tonumber(cost,0)) as daily_cost by _time, tag_pool
| join type=left _time, tag_pool [
  search index=xd (sourcetype="citrix:mc:autoscale" OR sourcetype="citrix:brokering:summary")
  | eval tag_pool=coalesce(host_pool, delivery_group, catalog_name, "unmapped")
  | bin _time span=1d
  | stats max(session_count) as peak_sessions, latest(machine_count) as reported_machines by _time, tag_pool
  ]
| eval cost_per_session=if(peak_sessions>0, round(daily_cost/peak_sessions,3), null())
| where isnotnull(daily_cost) AND daily_cost>0
| table _time, tag_pool, daily_cost, peak_sessions, reported_machines, cost_per_session
```

## Visualization

Line chart of cost per session by pool; stacked area of instance hours paid versus sessions; table of autoscale power actions and next-day cost impact.

## References

- [Autoscale in Citrix DaaS](https://docs.citrix.com/en-us/citrix-daas-service-delivery-machines/delivery-groups/autoscale-daas.html)
- [Microsoft Cost Management (export cost data to external tools)](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/analyze-cost-data-azure)
