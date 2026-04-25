<!-- AUTO-GENERATED from UC-6.2.4.json — DO NOT EDIT -->

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
• `stats` rolls up events into metrics; results are split **by bucket_name, StorageType** so each row reflects one combination of those dimensions.
• Pivots fields for charting with `xyseries`.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Include who owns the cloud account and the bucket lifecycle policy, because object alerts often need a finance or app owner, not only the storage team. Consider visualizations: Stacked bar (storage class distribution per bucket), Table (policy violations), Pie chart (total storage by class).

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
