<!-- AUTO-GENERATED from UC-8.7.3.json — DO NOT EDIT -->

---
id: "8.7.3"
title: "Application Error Budget Burn Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.7.3 · Application Error Budget Burn Rate Trending

## Description

Error budget remaining over a sprint or month shows whether reliability goals are sustainable. Accelerating burn triggers freeze or rollback decisions before users experience widespread outages.

## Value

Error budget remaining over a sprint or month shows whether reliability goals are sustainable. Accelerating burn triggers freeze or rollback decisions before users experience widespread outages.

## Implementation

Populate `remaining_pct` from your SLO tool (Datadog, Dynatrace, homemade) via HEC or scheduled pull. Define calendar alignment (monthly vs rolling 30d) consistently with product owners. Combine with release markers using `annotate` or a `releases` lookup. Alert on multi-day burn-rate thresholds per Google SRE multi-window practice if you export windowed burn fields.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom SLO pipeline, Splunk Observability Cloud export, or scripted inputs from service catalogs.
• Ensure the following data sources are available: `index=app` SLO metrics, `sourcetype=stash` error-budget summaries, `index=middleware` synthetic or gateway SLO fields.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Populate `remaining_pct` from your SLO tool (Datadog, Dynatrace, homemade) via HEC or scheduled pull. Define calendar alignment (monthly vs rolling 30d) consistently with product owners. Combine with release markers using `annotate` or a `releases` lookup. Alert on multi-day burn-rate thresholds per Google SRE multi-window practice if you export windowed burn fields.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=app sourcetype=stash source="*error_budget*" OR index=middleware sourcetype="slos:metrics"
| eval remaining_pct=coalesce(error_budget_remaining_pct, slo_remaining_percent, 100 - burn_rate_pct)
| eval sprint=strftime(_time,"%Y-W%V")
| bin _time span=1d
| stats first(remaining_pct) as budget_remaining by _time, service
| timechart span=1d min(budget_remaining) as min_budget_remaining by service limit=10
```

Understanding this SPL

**Application Error Budget Burn Rate Trending** — Error budget remaining over a sprint or month shows whether reliability goals are sustainable. Accelerating burn triggers freeze or rollback decisions before users experience widespread outages.

Documented **Data sources**: `index=app` SLO metrics, `sourcetype=stash` error-budget summaries, `index=middleware` synthetic or gateway SLO fields. **App/TA** (typical add-on context): Custom SLO pipeline, Splunk Observability Cloud export, or scripted inputs from service catalogs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: app, middleware; **sourcetype**: stash, slos:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=app, index=middleware, sourcetype=stash. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **remaining_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **sprint** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, service** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by service limit=10** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Area chart (budget remaining %), line chart with release annotations, single value (days of budget left at current burn).

## SPL

```spl
index=app sourcetype=stash source="*error_budget*" OR index=middleware sourcetype="slos:metrics"
| eval remaining_pct=coalesce(error_budget_remaining_pct, slo_remaining_percent, 100 - burn_rate_pct)
| eval sprint=strftime(_time,"%Y-W%V")
| bin _time span=1d
| stats first(remaining_pct) as budget_remaining by _time, service
| timechart span=1d min(budget_remaining) as min_budget_remaining by service limit=10
```

## Visualization

Area chart (budget remaining %), line chart with release annotations, single value (days of budget left at current burn).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
