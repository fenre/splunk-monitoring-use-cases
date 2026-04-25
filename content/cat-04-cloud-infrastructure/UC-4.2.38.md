<!-- AUTO-GENERATED from UC-4.2.38.json — DO NOT EDIT -->

---
id: "4.2.38"
title: "Logic App Run Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.38 · Logic App Run Failures

## Description

Integration workflows power automation; failed runs leave tickets, data, and approvals stuck.

## Value

Integration workflows power automation; failed runs leave tickets, data, and approvals stuck.

## Implementation

Enable Logic App workflow diagnostics. Ingest run status and error codes. Alert on any failed production workflow or retry exhaustion. Replay failed runs from operations team process.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (WorkflowRuntime), Logic App run history export.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Logic App workflow diagnostics. Ingest run status and error codes. Alert on any failed production workflow or retry exhaustion. Replay failed runs from operations team process.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Logic/workflows" status_s="Failed"
| stats count by resource_name_s, code_s, error_s
| sort -count
```

Understanding this SPL

**Logic App Run Failures** — Integration workflows power automation; failed runs leave tickets, data, and approvals stuck.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (WorkflowRuntime), Logic App run history export. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics, Microsoft.Logic/workflows. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource_name_s, code_s, error_s** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (workflow, error), Timeline (failures), Single value (failed runs / hour).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Logic/workflows" status_s="Failed"
| stats count by resource_name_s, code_s, error_s
| sort -count
```

## Visualization

Table (workflow, error), Timeline (failures), Single value (failed runs / hour).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
