---
id: "4.5.9"
title: "Serverless Cost Tracking by Function"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.5.9 · Serverless Cost Tracking by Function

## Description

Function-level spend exposes expensive handlers, mis-scaled concurrency, and test sandboxes left running—essential for FinOps and chargeback.

## Value

Function-level spend exposes expensive handlers, mis-scaled concurrency, and test sandboxes left running—essential for FinOps and chargeback.

## Implementation

Ingest CUR or cost exports with resource-level granularity and tags (`aws:createdBy`, Azure resource name, GCP labels). Normalize into a common schema. Filter to serverless SKUs (Lambda, Azure Functions, Cloud Functions). Schedule weekly reports and alerts for top-N spenders or day-over-day spikes per function.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=aws:billing`, `sourcetype=azure:costmanagement`, `sourcetype=gcp:billing`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CUR or cost exports with resource-level granularity and tags (`aws:createdBy`, Azure resource name, GCP labels). Normalize into a common schema. Filter to serverless SKUs (Lambda, Azure Functions, Cloud Functions). Schedule weekly reports and alerts for top-N spenders or day-over-day spikes per function.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP")
| eval line_cost=coalesce(BlendedCost, UnblendedCost, cost, CostInBillingCurrency)
| eval fn=coalesce(resourceId, ResourceId, labels.value)
| where match(lower(ProductName).lower(service).lower(resource_type), "(lambda|function|cloudfunctions|functions)")
| stats sum(line_cost) as spend by cloud, fn
| sort -spend
```

Understanding this SPL

**Serverless Cost Tracking by Function** — Function-level spend exposes expensive handlers, mis-scaled concurrency, and test sandboxes left running—essential for FinOps and chargeback.

Documented **Data sources**: `sourcetype=aws:billing`, `sourcetype=azure:costmanagement`, `sourcetype=gcp:billing`. **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:billing, azure:costmanagement, gcp:billing. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **line_cost** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **fn** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where match(lower(ProductName).lower(service).lower(resource_type), "(lambda|function|cloudfunctions|functions)")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cloud, fn** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (spend by function), Treemap (cost by cloud and service), Table (cloud, function, spend, % of total).

## SPL

```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP")
| eval line_cost=coalesce(BlendedCost, UnblendedCost, cost, CostInBillingCurrency)
| eval fn=coalesce(resourceId, ResourceId, labels.value)
| where match(lower(ProductName).lower(service).lower(resource_type), "(lambda|function|cloudfunctions|functions)")
| stats sum(line_cost) as spend by cloud, fn
| sort -spend
```

## Visualization

Bar chart (spend by function), Treemap (cost by cloud and service), Table (cloud, function, spend, % of total).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
