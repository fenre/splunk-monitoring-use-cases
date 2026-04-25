<!-- AUTO-GENERATED from UC-4.1.62.json — DO NOT EDIT -->

---
id: "4.1.62"
title: "RDS Performance Insights Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.62 · RDS Performance Insights Trending

## Description

Performance Insights exposes DB load by wait state; trending top SQL and waits guides index and instance right-sizing beyond raw CPU.

## Value

Performance Insights exposes DB load by wait state; trending top SQL and waits guides index and instance right-sizing beyond raw CPU.

## Implementation

Enable Performance Insights (7–30 day retention). Export `DBLoad`, `DBLoadCPU`, `DBLoadNonCPU` via API or CloudWatch where available. Alert on sustained elevation vs weekly baseline. Join with application release times.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: Performance Insights API export, `sourcetype=aws:cloudwatch` (PI metrics), RDS log exports.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Performance Insights (7–30 day retention). Export `DBLoad`, `DBLoadCPU`, `DBLoadNonCPU` via API or CloudWatch where available. Alert on sustained elevation vs weekly baseline. Join with application release times.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="DBLoad" statistic="Average"
| timechart span=1h avg(Average) as dbload by DBInstanceIdentifier
| streamstats window=168 global=f avg(dbload) as baseline by DBInstanceIdentifier
| where dbload > baseline * 1.5
```

Understanding this SPL

**RDS Performance Insights Trending** — Performance Insights exposes DB load by wait state; trending top SQL and waits guides index and instance right-sizing beyond raw CPU.

Documented **Data sources**: Performance Insights API export, `sourcetype=aws:cloudwatch` (PI metrics), RDS log exports. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by DBInstanceIdentifier** — ideal for trending and alerting on this use case.
• `streamstats` rolls up events into metrics; results are split **by DBInstanceIdentifier** so each row reflects one combination of those dimensions.
• Filters the current rows with `where dbload > baseline * 1.5` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as load_proxy
  from datamodel=Performance.Performance
  where match(Performance.object, "(?i)dbinstance|RDS|aws/rds")
  by Performance.object span=1h
| sort - load_proxy
```

Understanding this CIM / accelerated SPL

**RDS Performance Insights Trending** — Performance Insights exposes DB load by wait state; trending top SQL and waits guides index and instance right-sizing beyond raw CPU.

Documented **Data sources**: Performance Insights API export, `sourcetype=aws:cloudwatch` (PI metrics), RDS log exports. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.Performance` (mapped DB host or instance metrics) — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DB load vs baseline), Table (instance, wait class if ingested), Area chart (CPU vs non-CPU load).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="DBLoad" statistic="Average"
| timechart span=1h avg(Average) as dbload by DBInstanceIdentifier
| streamstats window=168 global=f avg(dbload) as baseline by DBInstanceIdentifier
| where dbload > baseline * 1.5
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as load_proxy
  from datamodel=Performance.Performance
  where match(Performance.object, "(?i)dbinstance|RDS|aws/rds")
  by Performance.object span=1h
| sort - load_proxy
```

## Visualization

Line chart (DB load vs baseline), Table (instance, wait class if ingested), Area chart (CPU vs non-CPU load).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
