<!-- AUTO-GENERATED from UC-4.5.12.json — DO NOT EDIT -->

---
id: "4.5.12"
title: "Azure Durable Functions Orchestration Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.12 · Azure Durable Functions Orchestration Health

## Description

Durable orchestrations span many activities; failed or stuck instances block business workflows until replayed or purged from storage.

## Value

Durable orchestrations span many activities; failed or stuck instances block business workflows until replayed or purged from storage.

## Implementation

Enable verbose logging for Durable Functions and ingest FunctionAppLogs. Extract orchestration instance IDs where present. Correlate with Storage Account metrics (queue/table used by the task hub) for backlog. Alert on failure patterns or rising pending instances versus completions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (FunctionAppLogs, traces).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable verbose logging for Durable Functions and ingest FunctionAppLogs. Extract orchestration instance IDs where present. Correlate with Storage Account metrics (queue/table used by the task hub) for backlog. Alert on failure patterns or rising pending instances versus completions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs"
| where match(_raw, "(?i)orchestration.*(failed|faulted)|TaskFailed|SubOrchestrationFailed")
| stats count as orch_failures by resourceName, coalesce(functionName, name)
| sort -orch_failures
```

Understanding this SPL

**Azure Durable Functions Orchestration Health** — Durable orchestrations span many activities; failed or stuck instances block business workflows until replayed or purged from storage.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (FunctionAppLogs, traces). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(_raw, "(?i)orchestration.*(failed|faulted)|TaskFailed|SubOrchestrationFailed")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by resourceName, coalesce(functionName, name)** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (app, orchestration name, failures), Line chart (failures over time), Link to Application Insights-style trace IDs if forwarded.

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs"
| where match(_raw, "(?i)orchestration.*(failed|faulted)|TaskFailed|SubOrchestrationFailed")
| stats count as orch_failures by resourceName, coalesce(functionName, name)
| sort -orch_failures
```

## Visualization

Table (app, orchestration name, failures), Line chart (failures over time), Link to Application Insights-style trace IDs if forwarded.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
