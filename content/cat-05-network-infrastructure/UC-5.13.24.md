---
id: "5.13.24"
title: "Issue Resolution Time Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.24 · Issue Resolution Time Tracking

## Description

Measures how long it takes to resolve Catalyst Center assurance issues by priority and category, tracking mean time to resolve (MTTR).

## Value

MTTR is a key operational metric. Tracking resolution times by priority and category reveals bottlenecks and measures the effectiveness of the operations team.

## Implementation

Enable the `issue` input. Ensure `issue_time` and `resolved_time` (epoch seconds) are present in events or normalized via the TA. Validate field names if your build uses different aliases.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:issue (fields status, resolved_time, issue_time, priority, category).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `issue` input. Ensure `issue_time` and `resolved_time` (epoch seconds) are present in events or normalized via the TA. Validate field names if your build uses different aliases.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval resolve_time_hrs=round((resolved_time-issue_time)/3600, 1) | stats avg(resolve_time_hrs) as avg_resolve_hrs median(resolve_time_hrs) as median_resolve_hrs max(resolve_time_hrs) as max_resolve_hrs by priority, category | sort priority
```

Understanding this SPL

**Issue Resolution Time Tracking** — MTTR is a key operational metric. Tracking resolution times by priority and category reveals bottlenecks and measures the effectiveness of the operations team.

**Pipeline walkthrough**

• Filters to `RESOLVED` issues so you only measure completed work.
• `eval resolve_time_hrs` converts the difference between `resolved_time` and `issue_time` from seconds to hours, rounded to one decimal.
• `stats` summarises mean, median, and maximum resolution hours split by `priority` and `category` for service-level and root-cause views.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (avg, median, max resolve hours by priority and category), bar chart of median MTTR by category.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval resolve_time_hrs=round((resolved_time-issue_time)/3600, 1) | stats avg(resolve_time_hrs) as avg_resolve_hrs median(resolve_time_hrs) as median_resolve_hrs max(resolve_time_hrs) as max_resolve_hrs by priority, category | sort priority
```

## Visualization

Table (avg, median, max resolve hours by priority and category), bar chart of median MTTR by category.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
