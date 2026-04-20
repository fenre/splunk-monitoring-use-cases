---
id: "4.4.9"
title: "Reserved Capacity and Savings Plan Utilization (Multi-Cloud)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-4.4.9 · Reserved Capacity and Savings Plan Utilization (Multi-Cloud)

## Description

AWS RIs/SPs, Azure Reservations, and GCP Committed Use discounts reduce cost when utilized. Low utilization wastes commitment spend.

## Value

AWS RIs/SPs, Azure Reservations, and GCP Committed Use discounts reduce cost when utilized. Low utilization wastes commitment spend.

## Implementation

Ingest reservation and usage data from each provider. Calculate utilization (used vs. committed). Dashboard utilization by type and account/project. Alert when utilization < 70% to trigger right-sizing or exchange.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs, billing and usage exports.
• Ensure the following data sources are available: AWS CUR (RI/SP usage), Azure Cost Management (reservation utilization), GCP Committed Use reports.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest reservation and usage data from each provider. Calculate utilization (used vs. committed). Dashboard utilization by type and account/project. Alert when utilization < 70% to trigger right-sizing or exchange.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType=*Reserved* OR lineItem_LineItemType=*Savings*
| stats sum(lineItem_UnblendedCost) as cost sum(lineItem_UsageAmount) as usage by product_instanceType reservation_ReservationARN
| eval utilization_pct = usage / reserved_units * 100
| where utilization_pct < 70
```

Understanding this SPL

**Reserved Capacity and Savings Plan Utilization (Multi-Cloud)** — AWS RIs/SPs, Azure Reservations, and GCP Committed Use discounts reduce cost when utilized. Low utilization wastes commitment spend.

Documented **Data sources**: AWS CUR (RI/SP usage), Azure Cost Management (reservation utilization), GCP Committed Use reports. **App/TA** (typical add-on context): Combined cloud TAs, billing and usage exports. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:billing. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by product_instanceType reservation_ReservationARN** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **utilization_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where utilization_pct < 70` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (reservation, type, utilization %), Gauge (overall utilization), Bar chart (waste by type).

## SPL

```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType=*Reserved* OR lineItem_LineItemType=*Savings*
| stats sum(lineItem_UnblendedCost) as cost sum(lineItem_UsageAmount) as usage by product_instanceType reservation_ReservationARN
| eval utilization_pct = usage / reserved_units * 100
| where utilization_pct < 70
```

## Visualization

Table (reservation, type, utilization %), Gauge (overall utilization), Bar chart (waste by type).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
