---
id: "4.1.48"
title: "Athena Query Execution Failures and Bytes Scanned"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.48 · Athena Query Execution Failures and Bytes Scanned

## Description

Failed queries and high bytes scanned impact user experience and cost. Monitoring supports optimization and error triage.

## Value

Failed queries and high bytes scanned impact user experience and cost. Monitoring supports optimization and error triage.

## Implementation

Use CloudTrail for Athena API calls (success/failure). Optionally export query execution IDs and join with GetQueryExecution for bytes scanned and state. Alert on high failure rate or queries scanning >1TB.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: Athena query history via API or CloudWatch (DataScannedInBytes), CloudTrail (StartQueryExecution, GetQueryResults).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use CloudTrail for Athena API calls (success/failure). Optionally export query execution IDs and join with GetQueryExecution for bytes scanned and state. Alert on high failure rate or queries scanning >1TB.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName="StartQueryExecution" errorCode!=""
| table _time userIdentity.arn requestParameters.queryExecutionId errorCode
| sort -_time
```

Understanding this SPL

**Athena Query Execution Failures and Bytes Scanned** — Failed queries and high bytes scanned impact user experience and cost. Monitoring supports optimization and error triage.

Documented **Data sources**: Athena query history via API or CloudWatch (DataScannedInBytes), CloudTrail (StartQueryExecution, GetQueryResults). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Athena Query Execution Failures and Bytes Scanned**): table _time userIdentity.arn requestParameters.queryExecutionId errorCode
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (query, user, bytes, state), Line chart (bytes scanned over time), Bar chart (top users by bytes).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName="StartQueryExecution" errorCode!=""
| table _time userIdentity.arn requestParameters.queryExecutionId errorCode
| sort -_time
```

## Visualization

Table (query, user, bytes, state), Line chart (bytes scanned over time), Bar chart (top users by bytes).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
