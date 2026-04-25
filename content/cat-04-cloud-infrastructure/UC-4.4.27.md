<!-- AUTO-GENERATED from UC-4.4.27.json — DO NOT EDIT -->

---
id: "4.4.27"
title: "Multi-Cloud Egress Cost Comparison"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.4.27 · Multi-Cloud Egress Cost Comparison

## Description

Egress drives surprise bills; comparing outbound spend by provider and region guides data locality and CDN decisions.

## Value

Egress drives surprise bills; comparing outbound spend by provider and region guides data locality and CDN decisions.

## Implementation

Map each provider’s line items to normalized `usage_type` and `cost` fields during ingestion. Join with application tags where available. Alert on week-over-week egress growth above threshold per provider.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Billing exports (CUR, Cost Management export, BigQuery billing).
• Ensure the following data sources are available: `sourcetype=aws:billing`, `sourcetype=azure:cost`, `sourcetype=gcp:billing`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map each provider’s line items to normalized `usage_type` and `cost` fields during ingestion. Join with application tags where available. Alert on week-over-week egress growth above threshold per provider.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud (sourcetype="aws:billing" OR sourcetype="azure:cost" OR sourcetype="gcp:billing")
| eval ut=lower(coalesce(lineItem_UsageType, usage_type, usageType, productSku))
| eval is_egress=if(match(ut,"egress|transfer|internet|download|outbound|data_transfer"),1,0)
| where is_egress=1
| eval provider=case(sourcetype="aws:billing","aws", sourcetype="azure:cost","azure", sourcetype="gcp:billing","gcp",1=1,"unknown")
| eval region=coalesce(lineItem_AvailabilityZone, resourceLocation, region)
| stats sum(cost) as egress_usd by provider, region, bin(_time, 1d)
| sort -egress_usd
```

Understanding this SPL

**Multi-Cloud Egress Cost Comparison** — Egress drives surprise bills; comparing outbound spend by provider and region guides data locality and CDN decisions.

Documented **Data sources**: `sourcetype=aws:billing`, `sourcetype=azure:cost`, `sourcetype=gcp:billing`. **App/TA** (typical add-on context): Billing exports (CUR, Cost Management export, BigQuery billing). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:billing, azure:cost, gcp:billing. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ut** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **is_egress** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where is_egress=1` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **region** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by provider, region, bin(_time, 1d)** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (egress USD by provider), Bar chart (region), Table (top services driving egress).

## SPL

```spl
index=cloud (sourcetype="aws:billing" OR sourcetype="azure:cost" OR sourcetype="gcp:billing")
| eval ut=lower(coalesce(lineItem_UsageType, usage_type, usageType, productSku))
| eval is_egress=if(match(ut,"egress|transfer|internet|download|outbound|data_transfer"),1,0)
| where is_egress=1
| eval provider=case(sourcetype="aws:billing","aws", sourcetype="azure:cost","azure", sourcetype="gcp:billing","gcp",1=1,"unknown")
| eval region=coalesce(lineItem_AvailabilityZone, resourceLocation, region)
| stats sum(cost) as egress_usd by provider, region, bin(_time, 1d)
| sort -egress_usd
```

## Visualization

Line chart (egress USD by provider), Bar chart (region), Table (top services driving egress).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
