---
id: "6.2.6"
title: "S3 and Azure Blob Lifecycle Policy Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.2.6 · S3 and Azure Blob Lifecycle Policy Compliance

## Description

Confirms lifecycle rules exist per bucket/container and that transitions match tagging/age rules. Reduces cost leakage from objects stuck in hot tiers.

## Value

Confirms lifecycle rules exist per bucket/container and that transitions match tagging/age rules. Reduces cost leakage from objects stuck in hot tiers.

## Implementation

Export bucket lifecycle configurations via API/Config daily. For Azure, ingest policy definitions from Activity/Resource Graph. Alert on production buckets missing lifecycle or expiration actions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, Config/Policy inventory.
• Ensure the following data sources are available: S3 bucket lifecycle XML inventory, Azure Blob management policy JSON, AWS Config.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export bucket lifecycle configurations via API/Config daily. For Azure, ingest policy definitions from Activity/Resource Graph. Alert on production buckets missing lifecycle or expiration actions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:s3:lifecycle_inventory"
| stats values(rule_id) as rules, latest(has_expiration) as exp by bucket_name, region
| where mvcount(rules)=0 OR exp=0
| table bucket_name region rules exp
```

Understanding this SPL

**S3 and Azure Blob Lifecycle Policy Compliance** — Confirms lifecycle rules exist per bucket/container and that transitions match tagging/age rules. Reduces cost leakage from objects stuck in hot tiers.

Documented **Data sources**: S3 bucket lifecycle XML inventory, Azure Blob management policy JSON, AWS Config. **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, Config/Policy inventory. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:s3:lifecycle_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:s3:lifecycle_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by bucket_name, region** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where mvcount(rules)=0 OR exp=0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **S3 and Azure Blob Lifecycle Policy Compliance**): table bucket_name region rules exp


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (buckets without compliant lifecycle), Pie chart (compliant vs non-compliant), Single value (non-compliant count).

## SPL

```spl
index=aws sourcetype="aws:s3:lifecycle_inventory"
| stats values(rule_id) as rules, latest(has_expiration) as exp by bucket_name, region
| where mvcount(rules)=0 OR exp=0
| table bucket_name region rules exp
```

## Visualization

Table (buckets without compliant lifecycle), Pie chart (compliant vs non-compliant), Single value (non-compliant count).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
