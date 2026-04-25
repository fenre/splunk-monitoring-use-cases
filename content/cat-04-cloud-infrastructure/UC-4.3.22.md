<!-- AUTO-GENERATED from UC-4.3.22.json — DO NOT EDIT -->

---
id: "4.3.22"
title: "Dataproc Cluster and Job Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.22 · Dataproc Cluster and Job Failures

## Description

Dataproc cluster and job failures break data pipelines. Monitoring supports reliability and cost (preemptible) optimization.

## Value

Dataproc cluster and job failures break data pipelines. Monitoring supports reliability and cost (preemptible) optimization.

## Implementation

Sink Dataproc logs to Pub/Sub. Ingest cluster state and job completion. Alert on cluster ERROR or job FAILED. Monitor preemptible node loss for cost vs. reliability trade-off.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Dataproc logs (cluster and job state), Cloud Monitoring (dataproc cluster metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sink Dataproc logs to Pub/Sub. Ingest cluster state and job completion. Alert on cluster ERROR or job FAILED. Monitor preemptible node loss for cost vs. reliability trade-off.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="dataproc_cluster" severity="ERROR"
| table _time resource.labels.cluster_name textPayload
| sort -_time
```

Understanding this SPL

**Dataproc Cluster and Job Failures** — Dataproc cluster and job failures break data pipelines. Monitoring supports reliability and cost (preemptible) optimization.

Documented **Data sources**: Dataproc logs (cluster and job state), Cloud Monitoring (dataproc cluster metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Dataproc Cluster and Job Failures**): table _time resource.labels.cluster_name textPayload
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cluster, job, state), Timeline (job failures), Bar chart (failures by job type).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="dataproc_cluster" severity="ERROR"
| table _time resource.labels.cluster_name textPayload
| sort -_time
```

## Visualization

Table (cluster, job, state), Timeline (job failures), Bar chart (failures by job type).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
