<!-- AUTO-GENERATED from UC-4.1.73.json — DO NOT EDIT -->

---
id: "4.1.73"
title: "ELB Target Health Check Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.73 · ELB Target Health Check Failures

## Description

Unhealthy targets are removed from rotation; rising unhealthy counts precede customer-facing errors.

## Value

Unhealthy targets are removed from rotation; rising unhealthy counts precede customer-facing errors.

## Implementation

Join with target group tags for app name. Alert when unhealthy > 0 for 5 minutes or half of targets unhealthy. Correlate with ASG events and backend application logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB — UnHealthyHostCount, HealthyHostCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Join with target group tags for app name. Alert when unhealthy > 0 for 5 minutes or half of targets unhealthy. Correlate with ASG events and backend application logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" (namespace="AWS/ApplicationELB" OR namespace="AWS/NetworkELB") metric_name="UnHealthyHostCount"
| stats latest(Maximum) as unhealthy by LoadBalancer, TargetGroup, bin(_time, 5m)
| where unhealthy > 0
| sort - unhealthy
```

Understanding this SPL

**ELB Target Health Check Failures** — Unhealthy targets are removed from rotation; rising unhealthy counts precede customer-facing errors.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB — UnHealthyHostCount, HealthyHostCount). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by LoadBalancer, TargetGroup, bin(_time, 5m)** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unhealthy > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (unhealthy hosts), Table (TG, AZ, count), Status grid (target).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" (namespace="AWS/ApplicationELB" OR namespace="AWS/NetworkELB") metric_name="UnHealthyHostCount"
| stats latest(Maximum) as unhealthy by LoadBalancer, TargetGroup, bin(_time, 5m)
| where unhealthy > 0
| sort - unhealthy
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

Line chart (unhealthy hosts), Table (TG, AZ, count), Status grid (target).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
