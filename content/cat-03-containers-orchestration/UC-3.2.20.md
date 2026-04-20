---
id: "3.2.20"
title: "Kubernetes Job and CronJob Failure Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.20 · Kubernetes Job and CronJob Failure Rate

## Description

Failed jobs and missed cron schedules.

## Value

Failed jobs and missed cron schedules.

## Implementation

Forward Kubernetes events for Job/CronJob failures. Collect `kube_job_status_failed` and `kube_cronjob_status_last_schedule_time` from kube-state-metrics. Alert on any Job with `failed > 0` or BackoffLimitExceeded. For CronJobs, alert when `last_schedule_time` is older than expected (e.g. 2x the cron interval) indicating missed runs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes.
• Ensure the following data sources are available: kube-state-metrics (`kube_job_status_failed`, `kube_cronjob_status_last_schedule_time`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Kubernetes events for Job/CronJob failures. Collect `kube_job_status_failed` and `kube_cronjob_status_last_schedule_time` from kube-state-metrics. Alert on any Job with `failed > 0` or BackoffLimitExceeded. For CronJobs, alert when `last_schedule_time` is older than expected (e.g. 2x the cron interval) indicating missed runs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since_schedule = (now() - _value) / 3600
| where hours_since_schedule > 2
| table namespace cronjob hours_since_schedule _value
```

Understanding this SPL

**Kubernetes Job and CronJob Failure Rate** — Failed jobs and missed cron schedules.

Documented **Data sources**: kube-state-metrics (`kube_job_status_failed`, `kube_cronjob_status_last_schedule_time`). **App/TA** (typical add-on context): Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hours_since_schedule** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hours_since_schedule > 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes Job and CronJob Failure Rate**): table namespace cronjob hours_since_schedule _value


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (job/cronjob, namespace, failures, message), Line chart (failure rate over time), Single value (failed jobs last 24h).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since_schedule = (now() - _value) / 3600
| where hours_since_schedule > 2
| table namespace cronjob hours_since_schedule _value
```

## Visualization

Table (job/cronjob, namespace, failures, message), Line chart (failure rate over time), Single value (failed jobs last 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
