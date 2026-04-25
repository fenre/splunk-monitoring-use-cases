<!-- AUTO-GENERATED from UC-4.4.21.json — DO NOT EDIT -->

---
id: "4.4.21"
title: "Cloud Resource Tag Coverage Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.21 · Cloud Resource Tag Coverage Trending

## Description

Untagged or improperly tagged resources impact cost allocation, governance, and security. Compliance gaps block chargeback and policy enforcement.

## Value

Untagged or improperly tagged resources impact cost allocation, governance, and security. Compliance gaps block chargeback and policy enforcement.

## Implementation

Enable AWS Config rule `required-tags` (or custom rule). Use Azure Policy for tag compliance. Export GCP Asset Inventory to BigQuery or Pub/Sub. Ingest compliance results in Splunk with normalized fields (provider, resource_type, compliance_status). For multi-cloud, use `index=cloud` and union searches per provider. Dashboard untagged resources by provider, resource type, and owner. Alert when critical resources (e.g. production EC2, storage) lack required tags (Environment, Owner, CostCenter).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure inputs, GCP inputs.
• Ensure the following data sources are available: AWS Config rules (required-tags), Azure Policy (tag compliance), GCP Asset Inventory (resource metadata).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AWS Config rule `required-tags` (or custom rule). Use Azure Policy for tag compliance. Export GCP Asset Inventory to BigQuery or Pub/Sub. Ingest compliance results in Splunk with normalized fields (provider, resource_type, compliance_status). For multi-cloud, use `index=cloud` and union searches per provider. Dashboard untagged resources by provider, resource type, and owner. Alert when critical resources (e.g. production EC2, storage) lack required tags (Environment, Owner, CostCenter).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" configRuleName="*required-tags*" complianceType="NON_COMPLIANT"
| eval provider="aws", resource_type=coalesce(resourceType, configuration.resourceType)
| stats count by provider, resource_type
| sort -count
```

Understanding this SPL

**Cloud Resource Tag Coverage Trending** — Untagged or improperly tagged resources impact cost allocation, governance, and security. Compliance gaps block chargeback and policy enforcement.

Documented **Data sources**: AWS Config rules (required-tags), Azure Policy (tag compliance), GCP Asset Inventory (resource metadata). **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure inputs, GCP inputs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by provider, resource_type** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (provider, resource type, compliance count), Pie chart (compliant vs non-compliant), Bar chart (non-compliant by tag key).

## SPL

```spl
index=aws sourcetype="aws:config:notification" configRuleName="*required-tags*" complianceType="NON_COMPLIANT"
| eval provider="aws", resource_type=coalesce(resourceType, configuration.resourceType)
| stats count by provider, resource_type
| sort -count
```

## Visualization

Table (provider, resource type, compliance count), Pie chart (compliant vs non-compliant), Bar chart (non-compliant by tag key).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
