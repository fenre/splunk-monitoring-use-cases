<!-- AUTO-GENERATED from UC-4.5.15.json — DO NOT EDIT -->

---
id: "4.5.15"
title: "GCP Cloud Functions Retry and Error Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.15 · GCP Cloud Functions Retry and Error Rate Trending

## Description

Rising retries and error rates signal unstable dependencies or quota issues before quotas hard-stop traffic; trending supports SLO review and incident prevention.

## Value

Rising retries and error rates signal unstable dependencies or quota issues before quotas hard-stop traffic; trending supports SLO review and incident prevention.

## Implementation

Ingest execution count metrics with result/status labels from Cloud Monitoring. Supplement with log-based counts from Cloud Logging for detailed error classes. Baseline hourly error and retry rates per function. Alert when error share exceeds threshold or retries spike versus invocations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (Cloud Logging), optional `sourcetype=google:gcp:monitoring` (execution metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest execution count metrics with result/status labels from Cloud Monitoring. Supplement with log-based counts from Cloud Logging for detailed error classes. Baseline hourly error and retry rates per function. Alert when error share exceeds threshold or retries spike versus invocations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| eval fn=resource.labels.function_name
| eval is_err=if(severity="ERROR", 1, 0)
| timechart span=1h sum(is_err) as errors, count as invocations by fn
| eval err_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where err_rate > 5
```

Understanding this SPL

**GCP Cloud Functions Retry and Error Rate Trending** — Rising retries and error rates signal unstable dependencies or quota issues before quotas hard-stop traffic; trending supports SLO review and incident prevention.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (Cloud Logging), optional `sourcetype=google:gcp:monitoring` (execution metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **fn** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **is_err** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by fn** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where err_rate > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area chart (executions by outcome), Line chart (error rate % over time), Table (function_name, invocations, errors, retry estimate).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| eval fn=resource.labels.function_name
| eval is_err=if(severity="ERROR", 1, 0)
| timechart span=1h sum(is_err) as errors, count as invocations by fn
| eval err_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where err_rate > 5
```

## Visualization

Stacked area chart (executions by outcome), Line chart (error rate % over time), Table (function_name, invocations, errors, retry estimate).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
