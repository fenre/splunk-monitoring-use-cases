<!-- AUTO-GENERATED from UC-5.12.2.json — DO NOT EDIT -->

---
id: "5.12.2"
title: "Call Volume Trending by Destination"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.12.2 · Call Volume Trending by Destination

## Description

Traffic engineering for trunk groups and geographic hot spots — detects flash crowds or fraud-driven spikes to premium destinations.

## Value

Traffic engineering for trunk groups and geographic hot spots — detects flash crowds or fraud-driven spikes to premium destinations.

## Implementation

Mask PANI for privacy dashboards; use HMAC of full number for drilldown in secured role.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CDR aggregation.
• Ensure the following data sources are available: `sourcetype="cdr:voip"` with `called_number`, `route_label`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Mask PANI for privacy dashboards; use HMAC of full number for drilldown in secured role.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip sourcetype="cdr:voip"
| eval dest_prefix=substr(called_number,1,6)
| timechart span=1h sum(duration_sec) as minutes count as calls by dest_prefix
| sort -calls
```

Understanding this SPL

**Call Volume Trending by Destination** — Traffic engineering for trunk groups and geographic hot spots — detects flash crowds or fraud-driven spikes to premium destinations.

Documented **Data sources**: `sourcetype="cdr:voip"` with `called_number`, `route_label`. **App/TA** (typical add-on context): CDR aggregation. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: cdr:voip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="cdr:voip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dest_prefix** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by dest_prefix** — ideal for trending and alerting on this use case.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Take one busy hour and compare a few top `dest_prefix` counts in Splunk to your SBC, carrier portal, or rate deck; mask full numbers in shared dashboards if your policy says so.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (calls by prefix), Map (if geo-lookup on prefix), Table (top routes).

## SPL

```spl
index=voip sourcetype="cdr:voip"
| eval dest_prefix=substr(called_number,1,6)
| timechart span=1h sum(duration_sec) as minutes count as calls by dest_prefix
| sort -calls
```

## Visualization

Line chart (calls by prefix), Map (if geo-lookup on prefix), Table (top routes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
