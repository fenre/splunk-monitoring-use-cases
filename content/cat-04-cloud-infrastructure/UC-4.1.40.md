<!-- AUTO-GENERATED from UC-4.1.40.json — DO NOT EDIT -->

---
id: "4.1.40"
title: "Route 53 Health Check Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.40 · Route 53 Health Check Failures

## Description

Health check failures indicate endpoint or path unreachable. Used for failover and monitoring of external/internal resources.

## Value

Health check failures indicate endpoint or path unreachable. Used for failover and monitoring of external/internal resources.

## Implementation

HealthCheckStatus 1 = Healthy, 0 = Unhealthy. Alert when status = 0. Create dashboard of all health checks with status. Use for failover routing and status page.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Route 53 health check metrics (HealthCheckStatus).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
HealthCheckStatus 1 = Healthy, 0 = Unhealthy. Alert when status = 0. Create dashboard of all health checks with status. Use for failover routing and status page.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| where Average != 1
| table _time HealthCheckId Average
```

Understanding this SPL

**Route 53 Health Check Failures** — Health check failures indicate endpoint or path unreachable. Used for failover and monitoring of external/internal resources.

Documented **Data sources**: CloudWatch Route 53 health check metrics (HealthCheckStatus). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average != 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Route 53 Health Check Failures**): table _time HealthCheckId Average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (healthy/unhealthy), Table (health check, status), Map (endpoint locations).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| where Average != 1
| table _time HealthCheckId Average
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

Status panel (healthy/unhealthy), Table (health check, status), Map (endpoint locations).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
