---
id: "4.6.1"
title: "Cloud Resource Count Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.6.1 · Cloud Resource Count Trending

## Description

EC2/VM instance count over 90 days reveals organic growth, failed automation leaving orphan instances, or shrinkage after optimization campaigns. Supports FinOps conversations and capacity forecasts.

## Value

EC2/VM instance count over 90 days reveals organic growth, failed automation leaving orphan instances, or shrinkage after optimization campaigns. Supports FinOps conversations and capacity forecasts.

## Implementation

Ingest periodic inventory snapshots (AWS Config, DescribeInstances exports, or Azure Resource Graph) into index=cloud with one event per instance per snapshot. If only change streams exist, maintain state with a nightly summary search. Chart instance_count over 90 days; optionally split by accountId or region. For multi-cloud, normalize resourceType across providers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for AWS, Splunk Add-on for Microsoft Cloud Services, Google Cloud add-ons.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:config:notification` or `sourcetype=aws:description` (inventory); Azure Resource Graph exports; GCP Asset Inventory.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest periodic inventory snapshots (AWS Config, DescribeInstances exports, or Azure Resource Graph) into index=cloud with one event per instance per snapshot. If only change streams exist, maintain state with a nightly summary search. Chart instance_count over 90 days; optionally split by accountId or region. For multi-cloud, normalize resourceType across providers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| bin _time span=1d
| stats dc(resourceId) as instance_count by _time, awsAccountId
| timechart span=1d sum(instance_count) as total_instances
| trendline sma7(total_instances) as instance_trend
| predict total_instances as predicted algorithm=LLP future_timespan=30
```

Understanding this SPL

**Cloud Resource Count Trending** — EC2/VM instance count over 90 days reveals organic growth, failed automation leaving orphan instances, or shrinkage after optimization campaigns. Supports FinOps conversations and capacity forecasts.

Documented **Data sources**: `index=cloud sourcetype=aws:config:notification` or `sourcetype=aws:description` (inventory); Azure Resource Graph exports; GCP Asset Inventory. **App/TA** (typical add-on context): Splunk Add-on for AWS, Splunk Add-on for Microsoft Cloud Services, Google Cloud add-ons. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:config:notification, AWS::EC2::Instance. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, awsAccountId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Cloud Resource Count Trending**): trendline sma7(total_instances) as instance_trend
• Pipeline stage (see **Cloud Resource Count Trending**): predict total_instances as predicted algorithm=LLP future_timespan=30


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (instance count over 90 days with trend and 30-day forecast), area chart stacked by account.

## SPL

```spl
index=cloud sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| bin _time span=1d
| stats dc(resourceId) as instance_count by _time, awsAccountId
| timechart span=1d sum(instance_count) as total_instances
| trendline sma7(total_instances) as instance_trend
| predict total_instances as predicted algorithm=LLP future_timespan=30
```

## Visualization

Line chart (instance count over 90 days with trend and 30-day forecast), area chart stacked by account.

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)
