<!-- AUTO-GENERATED from UC-4.1.77.json — DO NOT EDIT -->

---
id: "4.1.77"
title: "AWS Fargate Task Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.77 · AWS Fargate Task Health

## Description

Fargate tasks are the unit of scale; tracking stopped tasks and resource limits surfaces platform issues before services miss SLAs.

## Value

Fargate tasks are the unit of scale; tracking stopped tasks and resource limits surfaces platform issues before services miss SLAs.

## Implementation

Enable CloudWatch Container Insights for ECS on Fargate and pull metrics via `Splunk_TA_aws` CloudWatch metric input. Ship task and service logs to Splunk (FireLens, Lambda, or direct subscription) and run a companion search on `sourcetype=aws:cloudwatchlogs` for `Task stopped` / error patterns. Map dimensions `ClusterName`, `ServiceName`, `TaskId`. Alert on sustained high CPU/memory, task stop reasons, and log error bursts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudWatch Logs/Metrics).
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch:metric` or `sourcetype=aws:cloudwatchlogs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch Container Insights for ECS on Fargate and pull metrics via `Splunk_TA_aws` CloudWatch metric input. Ship task and service logs to Splunk (FireLens, Lambda, or direct subscription) and run a companion search on `sourcetype=aws:cloudwatchlogs` for `Task stopped` / error patterns. Map dimensions `ClusterName`, `ServiceName`, `TaskId`. Alert on sustained high CPU/memory, task stop reasons, and log error bursts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:cloudwatch:metric" Namespace="AWS/ECS" MetricName="CPUUtilization"
| stats avg(Average) as cpu_avg, max(Maximum) as cpu_max by ServiceName, ClusterName
| where cpu_max>90
| sort -cpu_max
```

Understanding this SPL

**AWS Fargate Task Health** — Fargate tasks are the unit of scale; tracking stopped tasks and resource limits surfaces platform issues before services miss SLAs.

Documented **Data sources**: `sourcetype=aws:cloudwatch:metric` or `sourcetype=aws:cloudwatchlogs`. **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudWatch Logs/Metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:cloudwatch:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:cloudwatch:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ServiceName, ClusterName** so each row reflects one combination of those dimensions.
• Filters the current rows with `where cpu_max>90` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (CPU/memory by service), Table (stopped tasks with reason), Single value (running task count).

## SPL

```spl
index=cloud sourcetype="aws:cloudwatch:metric" Namespace="AWS/ECS" MetricName="CPUUtilization"
| stats avg(Average) as cpu_avg, max(Maximum) as cpu_max by ServiceName, ClusterName
| where cpu_max>90
| sort -cpu_max
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

Time chart (CPU/memory by service), Table (stopped tasks with reason), Single value (running task count).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)
