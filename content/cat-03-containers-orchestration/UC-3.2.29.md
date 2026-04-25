<!-- AUTO-GENERATED from UC-3.2.29.json — DO NOT EDIT -->

---
id: "3.2.29"
title: "CronJob Failure Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.29 · CronJob Failure Tracking

## Description

Missed batch jobs break SLAs for reporting and cleanup; tracking last successful run and Job failures closes blind spots.

## Value

Missed batch jobs break SLAs for reporting and cleanup; tracking last successful run and Job failures closes blind spots.

## Implementation

Combine event-based failures with `kube_cronjob_status_last_schedule_time` staleness versus expected schedule. Alert when no successful Job completion in expected window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector.
• Ensure the following data sources are available: `sourcetype=kube:events`, `sourcetype=kube:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Combine event-based failures with `kube_cronjob_status_last_schedule_time` staleness versus expected schedule. Alert when no successful Job completion in expected window.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since=(now()-_value)/3600
| where hours_since>24
| table namespace cronjob hours_since
```

Understanding this SPL

**CronJob Failure Tracking** — Missed batch jobs break SLAs for reporting and cleanup; tracking last successful run and Job failures closes blind spots.

Documented **Data sources**: `sourcetype=kube:events`, `sourcetype=kube:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hours_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hours_since>24` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **CronJob Failure Tracking**): table namespace cronjob hours_since


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cronjob, last schedule, failures), Line chart (failure count), Single value (failed jobs 24h).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since=(now()-_value)/3600
| where hours_since>24
| table namespace cronjob hours_since
```

## Visualization

Table (cronjob, last schedule, failures), Line chart (failure count), Single value (failed jobs 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
