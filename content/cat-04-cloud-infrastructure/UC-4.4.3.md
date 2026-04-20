---
id: "4.4.3"
title: "Multi-Cloud Cost Dashboard"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.4.3 · Multi-Cloud Cost Dashboard

## Description

Unified cost visibility across cloud providers enables budgeting, chargeback, and optimization decisions from a single pane of glass.

## Value

Unified cost visibility across cloud providers enables budgeting, chargeback, and optimization decisions from a single pane of glass.

## Implementation

Ingest billing data from each provider. Normalize cost fields. Create a unified dashboard with consistent time-grain (daily). Break down by team using tagging from each provider.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs, billing data.
• Ensure the following data sources are available: AWS CUR, Azure Cost Management, GCP Billing export.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest billing data from each provider. Normalize cost fields. Create a unified dashboard with consistent time-grain (daily). Break down by team using tagging from each provider.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval cost=coalesce(BlendedCost, CostInBillingCurrency, cost)
| timechart span=1d sum(cost) by cloud
```

Understanding this SPL

**Multi-Cloud Cost Dashboard** — Unified cost visibility across cloud providers enables budgeting, chargeback, and optimization decisions from a single pane of glass.

Documented **Data sources**: AWS CUR, Azure Cost Management, GCP Billing export. **App/TA** (typical add-on context): Combined cloud TAs, billing data. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:billing, azure:costmanagement, gcp:billing. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **cost** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by cloud** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area chart (daily cost by cloud), Table (cost by service), Pie chart (cost distribution).

## SPL

```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval cost=coalesce(BlendedCost, CostInBillingCurrency, cost)
| timechart span=1d sum(cost) by cloud
```

## Visualization

Stacked area chart (daily cost by cloud), Table (cost by service), Pie chart (cost distribution).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
