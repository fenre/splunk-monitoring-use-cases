<!-- AUTO-GENERATED from UC-6.2.10.json — DO NOT EDIT -->

---
id: "6.2.10"
title: "Storage Class Transition Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.2.10 · Storage Class Transition Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Cost

*We show when objects move between hot, warm, and archive tiers so cost and retrieval time line up with what you expect.*

---

## Description

Validates that objects move to IA/Glacier/Archive per policy. Stalled transitions indicate rule gaps or unsupported objects.

## Value

Validates that objects move to IA/Glacier/Archive per policy. Stalled transitions indicate rule gaps or unsupported objects.

## Implementation

Ingest periodic inventory or CloudWatch breakdown. Compare STANDARD % vs policy targets. Report buckets with excessive STANDARD after expected transition age.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: S3 Inventory, Azure Blob inventory, CloudWatch storage class metrics.
- Ensure the following data sources are available: S3 Inventory reports (CSV), `BucketSizeBytes` by `StorageType`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Ingest periodic inventory or CloudWatch breakdown. Compare STANDARD % vs policy targets. Report buckets with excessive STANDARD after expected transition age.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:s3:inventory" OR sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats sum(size_bytes) as bytes by bucket_name, storage_class
| eventstats sum(bytes) as total by bucket_name
| eval pct=round(bytes/total*100,1)
| where storage_class="STANDARD" AND pct > 40
```

#### Understanding this SPL

**Storage Class Transition Tracking** — Validates that objects move to IA/Glacier/Archive per policy. Stalled transitions indicate rule gaps or unsupported objects.

Documented **Data sources**: S3 Inventory reports (CSV), `BucketSizeBytes` by `StorageType`. **App/TA** (typical add-on context): S3 Inventory, Azure Blob inventory, CloudWatch storage class metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:s3:inventory, aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=aws, sourcetype="aws:s3:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by bucket_name, storage_class** so each row reflects one combination of those dimensions.
- `eventstats` rolls up events into metrics; results are split **by bucket_name** so each row reflects one combination of those dimensions.
- `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where storage_class="STANDARD" AND pct > 40` — typically the threshold or rule expression for this monitoring goal.

### Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Include who owns the cloud account and the bucket lifecycle policy, because object alerts often need a finance or app owner, not only the storage team. Consider visualizations: Stacked bar (storage class % per bucket), Table (buckets with high STANDARD %), Line chart (class mix over time).

## SPL

```spl
index=aws sourcetype="aws:s3:inventory" OR sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats sum(size_bytes) as bytes by bucket_name, storage_class
| eventstats sum(bytes) as total by bucket_name
| eval pct=round(bytes/total*100,1)
| where storage_class="STANDARD" AND pct > 40
```

## Visualization

Stacked bar (storage class % per bucket), Table (buckets with high STANDARD %), Line chart (class mix over time).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
