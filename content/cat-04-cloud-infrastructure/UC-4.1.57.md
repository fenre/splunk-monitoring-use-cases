<!-- AUTO-GENERATED from UC-4.1.57.json — DO NOT EDIT -->

---
id: "4.1.57"
title: "AWS ECS Task Placement Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.57 · AWS ECS Task Placement Failures

## Description

Tasks failing to place due to resource constraints (CPU, memory, ports, attributes) cause service scaling failures and deployment blockages.

## Value

Tasks failing to place due to resource constraints (CPU, memory, ports, attributes) cause service scaling failures and deployment blockages.

## Implementation

CloudTrail logs ECS API calls; RunTask and CreateService responses include a `failures` array when placement fails. Ingest ECS events from EventBridge for container instance state changes. Parse failure reasons (RESOURCE:MEMORY, RESOURCE:CPU, RESOURCE:PORT, attribute constraints). Alert on any placement failure. Dashboard by cluster, reason, and task definition. Remediate by adding capacity, relaxing constraints, or adjusting task definitions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudTrail (RunTask, CreateService with placement failures), ECS container instance state change events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
CloudTrail logs ECS API calls; RunTask and CreateService responses include a `failures` array when placement fails. Ingest ECS events from EventBridge for container instance state changes. Parse failure reasons (RESOURCE:MEMORY, RESOURCE:CPU, RESOURCE:PORT, attribute constraints). Alert on any placement failure. Dashboard by cluster, reason, and task definition. Remediate by adding capacity, relaxing constraints, or adjusting task definitions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ecs.amazonaws.com" (eventName="RunTask" OR eventName="CreateService")
| spath path=responseElements.failures{}
| mvexpand responseElements.failures{} limit=500
| spath input=responseElements.failures{} path=reason
| spath input=responseElements.failures{} path=arn
| search reason=*
| stats count by reason, requestParameters.cluster
| sort -count
```

Understanding this SPL

**AWS ECS Task Placement Failures** — Tasks failing to place due to resource constraints (CPU, memory, ports, attributes) cause service scaling failures and deployment blockages.

Documented **Data sources**: CloudTrail (RunTask, CreateService with placement failures), ECS container instance state change events. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by reason, requestParameters.cluster** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (reason, cluster, count), Bar chart (failures by reason), Timeline (placement failure events).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ecs.amazonaws.com" (eventName="RunTask" OR eventName="CreateService")
| spath path=responseElements.failures{}
| mvexpand responseElements.failures{} limit=500
| spath input=responseElements.failures{} path=reason
| spath input=responseElements.failures{} path=arn
| search reason=*
| stats count by reason, requestParameters.cluster
| sort -count
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

Table (reason, cluster, count), Bar chart (failures by reason), Timeline (placement failure events).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
