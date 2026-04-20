---
id: "4.4.8"
title: "Cloud Spend by Tag or Project (Chargeback)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.4.8 · Cloud Spend by Tag or Project (Chargeback)

## Description

Allocating cost by tag (AWS/Azure) or project/label (GCP) enables chargeback and showback. Supports budget accountability and optimization by team.

## Value

Allocating cost by tag (AWS/Azure) or project/label (GCP) enables chargeback and showback. Supports budget accountability and optimization by team.

## Implementation

Ingest billing data with tag/project dimensions. Normalize tag keys (e.g. Owner, Team, Environment). Dashboard cost by tag/project and trend. Set budget alerts per tag/project. Reconcile with actual invoices.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs, CUR, Azure Cost Management export, GCP Billing export.
• Ensure the following data sources are available: AWS CUR (with tag allocation), Azure Cost Management (by tag/resource group), GCP Billing (by project/labels).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest billing data with tag/project dimensions. Normalize tag keys (e.g. Owner, Team, Environment). Dashboard cost by tag/project and trend. Set budget alerts per tag/project. Reconcile with actual invoices.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing"
| spath path=resourceTags output=tags
| mvexpand tags limit=500
| rex field=tags "^(?<tag_key>[^:]+):(?<tag_value>.+)$"
| stats sum(BlendedCost) as cost by tag_key tag_value
| where tag_key="Owner" OR tag_key="Team"
| sort -cost
```

Understanding this SPL

**Cloud Spend by Tag or Project (Chargeback)** — Allocating cost by tag (AWS/Azure) or project/label (GCP) enables chargeback and showback. Supports budget accountability and optimization by team.

Documented **Data sources**: AWS CUR (with tag allocation), Azure Cost Management (by tag/resource group), GCP Billing (by project/labels). **App/TA** (typical add-on context): Combined cloud TAs, CUR, Azure Cost Management export, GCP Billing export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:billing. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by tag_key tag_value** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where tag_key="Owner" OR tag_key="Team"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar (cost by tag value), Table (tag, cost, % of total), Line chart (cost trend by team).

## SPL

```spl
index=aws sourcetype="aws:billing"
| spath path=resourceTags output=tags
| mvexpand tags limit=500
| rex field=tags "^(?<tag_key>[^:]+):(?<tag_value>.+)$"
| stats sum(BlendedCost) as cost by tag_key tag_value
| where tag_key="Owner" OR tag_key="Team"
| sort -cost
```

## Visualization

Stacked bar (cost by tag value), Table (tag, cost, % of total), Line chart (cost trend by team).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
