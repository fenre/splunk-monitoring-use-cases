<!-- AUTO-GENERATED from UC-4.1.70.json — DO NOT EDIT -->

---
id: "4.1.70"
title: "Route 53 Health Check Failover Validation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.70 · Route 53 Health Check Failover Validation

## Description

Failed health checks drive DNS failover; sustained failures mean user-facing outages or flapping routing policies.

## Value

Failed health checks drive DNS failover; sustained failures mean user-facing outages or flapping routing policies.

## Implementation

Map `HealthCheckId` to application names via lookup. Alert on unhealthy state for two consecutive periods. Correlate with target (ALB, IP) metrics. Include calculator health checks for complex routing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/Route53 — HealthCheckStatus, ChildHealthCheckHealthyCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map `HealthCheckId` to application names via lookup. Alert on unhealthy state for two consecutive periods. Correlate with target (ALB, IP) metrics. Include calculator health checks for complex routing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| stats latest(Minimum) as healthy by HealthCheckId, bin(_time, 5m)
| where healthy < 1
| sort HealthCheckId -_time
```

Understanding this SPL

**Route 53 Health Check Failover Validation** — Failed health checks drive DNS failover; sustained failures mean user-facing outages or flapping routing policies.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/Route53 — HealthCheckStatus, ChildHealthCheckHealthyCount). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by HealthCheckId, bin(_time, 5m)** so each row reflects one combination of those dimensions.
• Filters the current rows with `where healthy < 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (health check × time), Table (check id, target), Timeline (failures).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| stats latest(Minimum) as healthy by HealthCheckId, bin(_time, 5m)
| where healthy < 1
| sort HealthCheckId -_time
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

Status grid (health check × time), Table (check id, target), Timeline (failures).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
