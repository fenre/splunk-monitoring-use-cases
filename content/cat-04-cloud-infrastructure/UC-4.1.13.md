<!-- AUTO-GENERATED from UC-4.1.13.json — DO NOT EDIT -->

---
id: "4.1.13"
title: "EKS/ECS Cluster Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.13 · EKS/ECS Cluster Health

## Description

Unhealthy ECS/EKS control planes strand deployments and skew desired-vs-running task counts, causing user-visible errors before infrastructure metrics breach thresholds. Route platform-level failures (API server, scheduler) to the platform team and workload-level failures (CrashLoopBackOff, OOM) to the application owner.

## Value

Unhealthy ECS/EKS control planes strand deployments and skew desired-vs-running task counts, causing user-visible errors before infrastructure metrics breach thresholds. Route platform-level failures (API server, scheduler) to the platform team and workload-level failures (CrashLoopBackOff, OOM) to the application owner.

## Implementation

Enable Container Insights for EKS/ECS. Collect metrics via CloudWatch. For deeper Kubernetes visibility in EKS, deploy Splunk OTel Collector as described in Category 3.2.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Splunk OTel Collector.
• Ensure the following data sources are available: CloudWatch EKS/ECS metrics, container insights.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Container Insights for EKS/ECS. Collect metrics via CloudWatch. For deeper Kubernetes visibility in EKS, deploy Splunk OTel Collector as described in Category 3.2.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" metric_name="CPUUtilization"
| timechart span=5m avg(Average) by ClusterName, ServiceName
```

Understanding this SPL

**EKS/ECS Cluster Health** — Unhealthy ECS/EKS control planes strand deployments and skew desired-vs-running task counts, causing user-visible errors before infrastructure metrics breach thresholds. Route platform-level failures (API server, scheduler) to the platform team and workload-level failures (CrashLoopBackOff, OOM) to the application owner.

Documented **Data sources**: CloudWatch EKS/ECS metrics, container insights. **App/TA** (typical add-on context): `Splunk_TA_aws`, Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by ClusterName, ServiceName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart per service, Cluster status panel, Table.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" metric_name="CPUUtilization"
| timechart span=5m avg(Average) by ClusterName, ServiceName
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Line chart per service, Cluster status panel, Table.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
