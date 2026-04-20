---
id: "4.4.14"
title: "Cloud Trail and Diagnostic Logging Gaps"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.4.14 · Cloud Trail and Diagnostic Logging Gaps

## Description

Missing or disabled CloudTrail, Activity Log export, or GCP audit log sink creates blind spots. Detecting gaps ensures full audit coverage.

## Value

Missing or disabled CloudTrail, Activity Log export, or GCP audit log sink creates blind spots. Detecting gaps ensures full audit coverage.

## Implementation

Use Config rules (e.g. cloudtrail-enabled, multi-region), Azure Policy (diagnostic logs to Event Hub), or GCP org policy for log sinks. Ingest compliance state. Alert when any account/region has trail disabled or logging gap. Dashboard coverage by account and log type.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Config, Azure Policy, GCP Asset Inventory, or custom API checks.
• Ensure the following data sources are available: AWS Config (cloudtrail-enabled), Azure Policy (diagnostic setting compliance), GCP log sink audit.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Config rules (e.g. cloudtrail-enabled, multi-region), Azure Policy (diagnostic logs to Event Hub), or GCP org policy for log sinks. Ingest compliance state. Alert when any account/region has trail disabled or logging gap. Dashboard coverage by account and log type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::CloudTrail::Trail"
| search configuration.isMultiRegionTrail=false OR configuration.logFileValidationEnabled=false
| table resourceId configuration.isMultiRegionTrail configuration.logFileValidationEnabled
```

Understanding this SPL

**Cloud Trail and Diagnostic Logging Gaps** — Missing or disabled CloudTrail, Activity Log export, or GCP audit log sink creates blind spots. Detecting gaps ensures full audit coverage.

Documented **Data sources**: AWS Config (cloudtrail-enabled), Azure Policy (diagnostic setting compliance), GCP log sink audit. **App/TA** (typical add-on context): Config, Azure Policy, GCP Asset Inventory, or custom API checks. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification, AWS::CloudTrail::Trail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Cloud Trail and Diagnostic Logging Gaps**): table resourceId configuration.isMultiRegionTrail configuration.logFileValidationEnabled


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (account, region, trail, multi-region, validation), Status (coverage %), Bar chart (gaps by account).

## SPL

```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::CloudTrail::Trail"
| search configuration.isMultiRegionTrail=false OR configuration.logFileValidationEnabled=false
| table resourceId configuration.isMultiRegionTrail configuration.logFileValidationEnabled
```

## Visualization

Table (account, region, trail, multi-region, validation), Status (coverage %), Bar chart (gaps by account).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
