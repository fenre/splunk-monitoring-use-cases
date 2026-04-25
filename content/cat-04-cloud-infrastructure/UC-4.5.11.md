<!-- AUTO-GENERATED from UC-4.5.11.json — DO NOT EDIT -->

---
id: "4.5.11"
title: "AWS Step Functions Execution Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.11 · AWS Step Functions Execution Failures

## Description

Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

## Value

Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

## Implementation

Enable CloudWatch metrics for Step Functions (`ExecutionsFailed`, `ExecutionsTimedOut`, `ExecutionsAborted`). Ingest via Splunk_TA_aws. Optionally join with execution history forwarded to S3 or CloudWatch Logs for failure context. Alert on any failed executions in production state machines or rate-based thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (namespace `AWS/States`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch metrics for Step Functions (`ExecutionsFailed`, `ExecutionsTimedOut`, `ExecutionsAborted`). Ingest via Splunk_TA_aws. Optionally join with execution history forwarded to S3 or CloudWatch Logs for failure context. Alert on any failed executions in production state machines or rate-based thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/States" metric_name="ExecutionsFailed"
| timechart span=5m sum(Sum) as failed by StateMachineArn
| where failed > 0
```

Understanding this SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (namespace `AWS/States`). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by StateMachineArn** — ideal for trending and alerting on this use case.
• Filters the current rows with `where failed > 0` — typically the threshold or rule expression for this monitoring goal.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**AWS Step Functions Execution Failures** — Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failed executions by state machine), Single value (failures in last hour), Table (StateMachineArn, failed, timed out).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/States" metric_name="ExecutionsFailed"
| timechart span=5m sum(Sum) as failed by StateMachineArn
| where failed > 0
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (failed executions by state machine), Single value (failures in last hour), Table (StateMachineArn, failed, timed out).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
