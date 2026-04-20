---
id: "4.1.69"
title: "CloudFront Error Rates by Distribution"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.69 · CloudFront Error Rates by Distribution

## Description

Origin or edge errors vary by distribution; breaking out 4xx/5xx by `DistributionId` isolates bad releases and misconfigured behaviors.

## Value

Origin or edge errors vary by distribution; breaking out 4xx/5xx by `DistributionId` isolates bad releases and misconfigured behaviors.

## Implementation

Ingest metrics per distribution ID. Correlate spikes with deployments and origin health. Use real-time logs for URI-level detail. Alert when 5xx error rate exceeds SLO for 10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/CloudFront — 4xxErrorRate, 5xxErrorRate), real-time logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest metrics per distribution ID. Correlate spikes with deployments and origin health. Use real-time logs for URI-level detail. Alert when 5xx error rate exceeds SLO for 10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate")
| stats latest(Average) as err_rate by DistributionId, metric_name, bin(_time, 5m)
| where err_rate > 1
| sort - err_rate
```

Understanding this SPL

**CloudFront Error Rates by Distribution** — Origin or edge errors vary by distribution; breaking out 4xx/5xx by `DistributionId` isolates bad releases and misconfigured behaviors.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/CloudFront — 4xxErrorRate, 5xxErrorRate), real-time logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by DistributionId, metric_name, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where err_rate > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate by distribution), Table (distribution, metric), Map (viewer country if from logs).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate")
| stats latest(Average) as err_rate by DistributionId, metric_name, bin(_time, 5m)
| where err_rate > 1
| sort - err_rate
```

## Visualization

Line chart (error rate by distribution), Table (distribution, metric), Map (viewer country if from logs).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
