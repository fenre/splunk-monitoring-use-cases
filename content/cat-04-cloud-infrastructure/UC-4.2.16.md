---
id: "4.2.16"
title: "Logic Apps Run Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.16 · Logic Apps Run Failures

## Description

Logic App run failures break automation and integrations. Tracking failures and retries supports debugging and SLA.

## Value

Logic App run failures break automation and integrations. Tracking failures and retries supports debugging and SLA.

## Implementation

Enable diagnostic logging for Logic Apps to Event Hub or Log Analytics. Ingest in Splunk. Alert when run status=Failed. Track retry patterns and correlate with connector/API errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Logic Apps workflow run history via diagnostic logs or Azure Monitor.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostic logging for Logic Apps to Event Hub or Log Analytics. Ingest in Splunk. Alert when run status=Failed. Track retry patterns and correlate with connector/API errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.LOGIC/WORKFLOWS" status="Failed"
| stats count by resourceId runId
| sort -count
```

Understanding this SPL

**Logic Apps Run Failures** — Logic App run failures break automation and integrations. Tracking failures and retries supports debugging and SLA.

Documented **Data sources**: Logic Apps workflow run history via diagnostic logs or Azure Monitor. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics, MICROSOFT.LOGIC/WORKFLOWS. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceId runId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (runs, failures by workflow), Table (workflow, run, status), Single value (failure rate).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.LOGIC/WORKFLOWS" status="Failed"
| stats count by resourceId runId
| sort -count
```

## Visualization

Line chart (runs, failures by workflow), Table (workflow, run, status), Single value (failure rate).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
