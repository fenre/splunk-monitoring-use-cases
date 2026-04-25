<!-- AUTO-GENERATED from UC-4.1.20.json — DO NOT EDIT -->

---
id: "4.1.20"
title: "Reserved Instance Utilization"
criticality: "low"
splunkPillar: "Observability"
---

# UC-4.1.20 · Reserved Instance Utilization

## Description

Underutilized RIs waste money. Tracking RI coverage and utilization helps optimize commit spending vs. on-demand costs.

## Value

Underutilized RIs waste money. Tracking RI coverage and utilization helps optimize commit spending vs. on-demand costs.

## Implementation

Ingest CUR data. Calculate RI utilization by comparing reserved hours against actual usage. Dashboard showing RI coverage percentage and waste. Review monthly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, CUR data.
• Ensure the following data sources are available: `sourcetype=aws:billing` (CUR).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CUR data. Calculate RI utilization by comparing reserved hours against actual usage. Dashboard showing RI coverage percentage and waste. Review monthly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType="DiscountedUsage" OR lineItem_LineItemType="RIFee"
| stats sum(lineItem_UsageAmount) as ri_hours, sum(lineItem_UnblendedCost) as ri_cost by reservation_ReservationARN, product_instanceType
| eval utilization_pct = round(ri_hours / expected_hours * 100, 1)
```

Understanding this SPL

**Reserved Instance Utilization** — Underutilized RIs waste money. Tracking RI coverage and utilization helps optimize commit spending vs. on-demand costs.

Documented **Data sources**: `sourcetype=aws:billing` (CUR). **App/TA** (typical add-on context): `Splunk_TA_aws`, CUR data. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:billing. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by reservation_ReservationARN, product_instanceType** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **utilization_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (RI, type, utilization %), Gauge (overall utilization), Bar chart by instance type.

## SPL

```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType="DiscountedUsage" OR lineItem_LineItemType="RIFee"
| stats sum(lineItem_UsageAmount) as ri_hours, sum(lineItem_UnblendedCost) as ri_cost by reservation_ReservationARN, product_instanceType
| eval utilization_pct = round(ri_hours / expected_hours * 100, 1)
```

## Visualization

Table (RI, type, utilization %), Gauge (overall utilization), Bar chart by instance type.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
