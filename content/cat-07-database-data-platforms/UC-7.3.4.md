---
id: "7.3.4"
title: "Storage Auto-Scaling Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.4 · Storage Auto-Scaling Events

## Description

Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

## Value

Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

## Implementation

Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud provider TAs.
• Ensure the following data sources are available: CloudTrail (ModifyDBInstance), Azure Activity Log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```

Understanding this SPL

**Storage Auto-Scaling Events** — Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

Documented **Data sources**: CloudTrail (ModifyDBInstance), Azure Activity Log. **App/TA** (typical add-on context): Cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where isnotnull(allocated)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Storage Auto-Scaling Events**): table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```

## Visualization

Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
