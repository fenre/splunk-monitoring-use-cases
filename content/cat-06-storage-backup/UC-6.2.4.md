---
id: "6.2.4"
title: "Lifecycle Policy Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.2.4 · Lifecycle Policy Compliance

## Description

Ensures storage cost optimization policies are working. Objects not transitioning per policy waste money.

## Value

Ensures storage cost optimization policies are working. Objects not transitioning per policy waste money.

## Implementation

Monitor storage class distribution per bucket over time. Compare against defined lifecycle policies. Alert when objects remain in expensive storage classes longer than policy dictates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud provider TAs.
• Ensure the following data sources are available: CloudWatch storage class metrics, lifecycle action logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor storage class distribution per bucket over time. Compare against defined lifecycle policies. Alert when objects remain in expensive storage classes longer than policy dictates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats latest(Average) as size by bucket_name, StorageType
| xyseries bucket_name StorageType size
```

Understanding this SPL

**Lifecycle Policy Compliance** — Ensures storage cost optimization policies are working. Objects not transitioning per policy waste money.

Documented **Data sources**: CloudWatch storage class metrics, lifecycle action logs. **App/TA** (typical add-on context): Cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by bucket_name, StorageType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pivots fields for charting with `xyseries`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar (storage class distribution per bucket), Table (policy violations), Pie chart (total storage by class).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats latest(Average) as size by bucket_name, StorageType
| xyseries bucket_name StorageType size
```

## Visualization

Stacked bar (storage class distribution per bucket), Table (policy violations), Pie chart (total storage by class).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
