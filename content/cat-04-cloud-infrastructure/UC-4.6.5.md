---
id: "4.6.5"
title: "Cloud Network Traffic Volume Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.6.5 · Cloud Network Traffic Volume Trending

## Description

Weekly VPC flow log volume indicates shifting traffic patterns, DDoS aftermath, or misconfigured mirroring. Complements per-flow analysis with a coarse health signal and correlates with network-related cost changes.

## Value

Weekly VPC flow log volume indicates shifting traffic patterns, DDoS aftermath, or misconfigured mirroring. Complements per-flow analysis with a coarse health signal and correlates with network-related cost changes.

## Implementation

Parse VPC Flow or NSG flow fields so bytes is numeric. Filter internal-only noise if needed via RFC1918 CIDR lists. Use weekly buckets for medium-term trending; index volume growth also correlates with ingest cost. For Azure, map to the appropriate custom sourcetype for raw flows. Alert on sudden jumps exceeding 2x the 4-week moving average.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for AWS (VPC Flow Logs), Azure NSG flow logs.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:cloudwatch:vpcflow` OR `sourcetype=azure:nsg:flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse VPC Flow or NSG flow fields so bytes is numeric. Filter internal-only noise if needed via RFC1918 CIDR lists. Use weekly buckets for medium-term trending; index volume growth also correlates with ingest cost. For Azure, map to the appropriate custom sourcetype for raw flows. Alert on sudden jumps exceeding 2x the 4-week moving average.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:cloudwatch:vpcflow"
| eval bytes=tonumber(bytes)
| timechart span=1w sum(bytes) as total_bytes
| eval total_gb=round(total_bytes/1073741824, 2)
| trendline sma4(total_gb) as traffic_trend
```

Understanding this SPL

**Cloud Network Traffic Volume Trending** — Weekly VPC flow log volume indicates shifting traffic patterns, DDoS aftermath, or misconfigured mirroring. Complements per-flow analysis with a coarse health signal and correlates with network-related cost changes.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudwatch:vpcflow` OR `sourcetype=azure:nsg:flow`. **App/TA** (typical add-on context): Splunk Add-on for AWS (VPC Flow Logs), Azure NSG flow logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:cloudwatch:vpcflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:cloudwatch:vpcflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1w** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Cloud Network Traffic Volume Trending**): trendline sma4(total_gb) as traffic_trend

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t sum(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=1w | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Cloud Network Traffic Volume Trending** — Weekly VPC flow log volume indicates shifting traffic patterns, DDoS aftermath, or misconfigured mirroring. Complements per-flow analysis with a coarse health signal and correlates with network-related cost changes.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudwatch:vpcflow` OR `sourcetype=azure:nsg:flow`. **App/TA** (typical add-on context): Splunk Add-on for AWS (VPC Flow Logs), Azure NSG flow logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (weekly total GB), line overlay (4-week SMA), dual axis with flow record count.

## SPL

```spl
index=cloud sourcetype="aws:cloudwatch:vpcflow"
| eval bytes=tonumber(bytes)
| timechart span=1w sum(bytes) as total_bytes
| eval total_gb=round(total_bytes/1073741824, 2)
| trendline sma4(total_gb) as traffic_trend
```

## CIM SPL

```spl
| tstats summariesonly=t sum(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=1w | sort - agg_value
```

## Visualization

Column chart (weekly total GB), line overlay (4-week SMA), dual axis with flow record count.

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
