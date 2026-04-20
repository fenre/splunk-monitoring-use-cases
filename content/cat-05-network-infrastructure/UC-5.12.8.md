---
id: "5.12.8"
title: "Number Portability Request Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.12.8 · Number Portability Request Tracking

## Description

LNP order status, NPAC responses, and port-out churn — operations and regulatory reporting for porting SLAs.

## Value

LNP order status, NPAC responses, and port-out churn — operations and regulatory reporting for porting SLAs.

## Implementation

SLA alerts for orders >72h in PENDING; root-cause codes joined to carrier contact list.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: NP/BSS extracts, SOA APIs.
• Ensure the following data sources are available: `sourcetype="lnp:order"`, `sourcetype="npac:soa"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
SLA alerts for orders >72h in PENDING; root-cause codes joined to carrier contact list.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=telco sourcetype="lnp:order"
| where order_status IN ("PENDING","REJECTED","TIMEOUT")
| stats count, avg((now()-submitted_epoch)/86400) as age_days by tn_range, losing_carrier
| sort -age_days
```

Understanding this SPL

**Number Portability Request Tracking** — LNP order status, NPAC responses, and port-out churn — operations and regulatory reporting for porting SLAs.

Documented **Data sources**: `sourcetype="lnp:order"`, `sourcetype="npac:soa"`. **App/TA** (typical add-on context): NP/BSS extracts, SOA APIs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: telco; **sourcetype**: lnp:order. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=telco, sourcetype="lnp:order". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where order_status IN ("PENDING","REJECTED","TIMEOUT")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by tn_range, losing_carrier** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Funnel (order states), Table (aging ports), Bar chart (reject reasons).

## SPL

```spl
index=telco sourcetype="lnp:order"
| where order_status IN ("PENDING","REJECTED","TIMEOUT")
| stats count, avg((now()-submitted_epoch)/86400) as age_days by tn_range, losing_carrier
| sort -age_days
```

## Visualization

Funnel (order states), Table (aging ports), Bar chart (reject reasons).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
