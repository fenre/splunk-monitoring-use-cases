---
id: "4.4.15"
title: "Cloud Resource Tag Compliance and Drift"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.15 · Cloud Resource Tag Compliance and Drift

## Description

Missing or inconsistent tags (Owner, CostCenter, Environment) block cost allocation, automation, and governance. Detecting untagged or non-compliant resources supports tag policy enforcement.

## Value

Missing or inconsistent tags (Owner, CostCenter, Environment) block cost allocation, automation, and governance. Detecting untagged or non-compliant resources supports tag policy enforcement.

## Implementation

Use AWS Config rules (required-tags), Azure Policy (e.g. RequireTagAndValue), or GCP org policy for label requirements. Ingest compliance results. Alert when net new untagged resources appear or compliance score drops below threshold. Dashboard by OU/account and resource type.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure Resource Graph, GCP Asset Inventory.
• Ensure the following data sources are available: AWS Config (resource compliance), Azure Policy compliance, GCP labels API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use AWS Config rules (required-tags), Azure Policy (e.g. RequireTagAndValue), or GCP org policy for label requirements. Ingest compliance results. Alert when net new untagged resources appear or compliance score drops below threshold. Dashboard by OU/account and resource type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:resource" tag_compliance="non_compliant"
| stats count by resourceType, account_id, region
| where count > 0
| sort -count
```

Understanding this SPL

**Cloud Resource Tag Compliance and Drift** — Missing or inconsistent tags (Owner, CostCenter, Environment) block cost allocation, automation, and governance. Detecting untagged or non-compliant resources supports tag policy enforcement.

Documented **Data sources**: AWS Config (resource compliance), Azure Policy compliance, GCP labels API. **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure Resource Graph, GCP Asset Inventory. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:resource. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:resource". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceType, account_id, region** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (account, resource type, non-compliant count), Gauge (tag compliance %), Bar chart by tag key missing.

## SPL

```spl
index=aws sourcetype="aws:config:resource" tag_compliance="non_compliant"
| stats count by resourceType, account_id, region
| where count > 0
| sort -count
```

## Visualization

Table (account, resource type, non-compliant count), Gauge (tag compliance %), Bar chart by tag key missing.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
