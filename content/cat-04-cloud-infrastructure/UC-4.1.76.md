---
id: "4.1.76"
title: "Lambda Layer Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.76 · Lambda Layer Version Compliance

## Description

Outdated layers carry vulnerable dependencies; enforcing approved layer ARNs avoids shadow IT libraries in functions.

## Value

Outdated layers carry vulnerable dependencies; enforcing approved layer ARNs avoids shadow IT libraries in functions.

## Implementation

Maintain CSV lookup of approved layer version ARNs. Alert on attach of unapproved layer or version drift weekly scan via `ListFunctions`. Integrate with CI/CD to block deploys pre-merge.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (lambda:GetFunction, PublishLayerVersion), Config custom rule output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain CSV lookup of approved layer version ARNs. Alert on attach of unapproved layer or version drift weekly scan via `ListFunctions`. Integrate with CI/CD to block deploys pre-merge.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="lambda.amazonaws.com" eventName="UpdateFunctionConfiguration"
| spath path=requestParameters.layers{}
| mvexpand requestParameters.layers{} limit=200
| eval layer_arn=requestParameters.layers{}
| lookup approved_lambda_layers layer_arn OUTPUT approved
| where isnull(approved)
| stats count by userIdentity.arn, requestParameters.functionName, layer_arn
```

Understanding this SPL

**Lambda Layer Version Compliance** — Outdated layers carry vulnerable dependencies; enforcing approved layer ARNs avoids shadow IT libraries in functions.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (lambda:GetFunction, PublishLayerVersion), Config custom rule output. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• `eval` defines or adjusts **layer_arn** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where isnull(approved)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn, requestParameters.functionName, layer_arn** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (function, layer, user), Bar chart (non-compliant functions), Timeline (changes).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="lambda.amazonaws.com" eventName="UpdateFunctionConfiguration"
| spath path=requestParameters.layers{}
| mvexpand requestParameters.layers{} limit=200
| eval layer_arn=requestParameters.layers{}
| lookup approved_lambda_layers layer_arn OUTPUT approved
| where isnull(approved)
| stats count by userIdentity.arn, requestParameters.functionName, layer_arn
```

## Visualization

Table (function, layer, user), Bar chart (non-compliant functions), Timeline (changes).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
