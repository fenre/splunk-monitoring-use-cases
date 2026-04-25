<!-- AUTO-GENERATED from UC-4.1.22.json — DO NOT EDIT -->

---
id: "4.1.22"
title: "ELB Target Health and Unhealthy Hosts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.22 · ELB Target Health and Unhealthy Hosts

## Description

Unhealthy targets cause traffic to fail or shift to remaining nodes. Early detection prevents user-facing outages.

## Value

Unhealthy targets cause traffic to fail or shift to remaining nodes. Early detection prevents user-facing outages.

## Implementation

Collect UnHealthyHostCount and HealthyHostCount from CloudWatch. Alert when UnHealthyHostCount > 0 for more than 2 minutes. Correlate with target group and instance health checks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect UnHealthyHostCount and HealthyHostCount from CloudWatch. Alert when UnHealthyHostCount > 0 for more than 2 minutes. Correlate with target group and instance health checks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApplicationELB" metric_name="UnHealthyHostCount"
| where Average > 0
| timechart span=5m max(Average) by LoadBalancer
```

Understanding this SPL

**ELB Target Health and Unhealthy Hosts** — Unhealthy targets cause traffic to fail or shift to remaining nodes. Early detection prevents user-facing outages.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by LoadBalancer** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (unhealthy count), Table (LB, target group, unhealthy), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApplicationELB" metric_name="UnHealthyHostCount"
| where Average > 0
| timechart span=5m max(Average) by LoadBalancer
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

Single value (unhealthy count), Table (LB, target group, unhealthy), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
