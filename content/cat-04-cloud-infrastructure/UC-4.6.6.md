<!-- AUTO-GENERATED from UC-4.6.6.json — DO NOT EDIT -->

---
id: "4.6.6"
title: "CloudTrail/Activity Log Event Volume Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.6.6 · CloudTrail/Activity Log Event Volume Trending

## Description

Management event volume over 90 days highlights automation changes, new integrations, or possible abuse such as enumeration or bulk API use. Baselines help spot anomalies without reading every event.

## Value

Management event volume over 90 days highlights automation changes, new integrations, or possible abuse such as enumeration or bulk API use. Baselines help spot anomalies without reading every event.

## Implementation

Filter to non-read-only events for management actions. For multi-cloud, use union or a combined index with sourcetype in the by clause. Chart 90 days with daily span. Alert on statistical outliers exceeding 3x baseline. Ensure CloudTrail is multi-region and organization trails where applicable so the trend is complete. For Azure, include Activity Log management category events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for AWS, Azure Activity Log add-on.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:cloudtrail`; `sourcetype=azure:monitor:activity`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Filter to non-read-only events for management actions. For multi-cloud, use union or a combined index with sourcetype in the by clause. Chart 90 days with daily span. Alert on statistical outliers exceeding 3x baseline. Ensure CloudTrail is multi-region and organization trails where applicable so the trend is complete. For Azure, include Activity Log management category events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:cloudtrail" readOnly=false
| timechart span=1d count as mgmt_events
| trendline sma7(mgmt_events) as event_trend
| predict mgmt_events as predicted algorithm=LLP future_timespan=14
```

Understanding this SPL

**CloudTrail/Activity Log Event Volume Trending** — Management event volume over 90 days highlights automation changes, new integrations, or possible abuse such as enumeration or bulk API use. Baselines help spot anomalies without reading every event.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudtrail`; `sourcetype=azure:monitor:activity`. **App/TA** (typical add-on context): Splunk Add-on for AWS, Azure Activity Log add-on. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **CloudTrail/Activity Log Event Volume Trending**): trendline sma7(mgmt_events) as event_trend
• Pipeline stage (see **CloudTrail/Activity Log Event Volume Trending**): predict mgmt_events as predicted algorithm=LLP future_timespan=14

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**CloudTrail/Activity Log Event Volume Trending** — Management event volume over 90 days highlights automation changes, new integrations, or possible abuse such as enumeration or bulk API use.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily management events with 7-day SMA, 90 days), anomaly overlay, 14-day forecast.

## SPL

```spl
index=cloud sourcetype="aws:cloudtrail" readOnly=false
| timechart span=1d count as mgmt_events
| trendline sma7(mgmt_events) as event_trend
| predict mgmt_events as predicted algorithm=LLP future_timespan=14
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Line chart (daily management events with 7-day SMA, 90 days), anomaly overlay, 14-day forecast.

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
