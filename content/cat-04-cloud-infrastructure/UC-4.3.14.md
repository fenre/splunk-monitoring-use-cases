<!-- AUTO-GENERATED from UC-4.3.14.json — DO NOT EDIT -->

---
id: "4.3.14"
title: "GKE Node Pool Autoscaling and Upgrade Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.14 · GKE Node Pool Autoscaling and Upgrade Events

## Description

Node pool scale-up/down and upgrade events affect workload placement and availability. Monitoring supports capacity and upgrade windows.

## Value

Node pool scale-up/down and upgrade events affect workload placement and availability. Monitoring supports capacity and upgrade windows.

## Implementation

Ingest GKE logs (cluster operations, node pool events). Monitor node count and autoscaler events. Track upgrade and maintenance window events. Alert on node pool scaling failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: GKE cluster logs, Cloud Monitoring (container metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest GKE logs (cluster operations, node pool events). Monitor node count and autoscaler events. Track upgrade and maintenance window events. Alert on node pool scaling failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" textPayload=*"upgrade"*
| table _time resource.labels.cluster_name textPayload
| sort -_time
```

Understanding this SPL

**GKE Node Pool Autoscaling and Upgrade Events** — Node pool scale-up/down and upgrade events affect workload placement and availability. Monitoring supports capacity and upgrade windows.

Documented **Data sources**: GKE cluster logs, Cloud Monitoring (container metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **GKE Node Pool Autoscaling and Upgrade Events**): table _time resource.labels.cluster_name textPayload
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (node pool events), Table (cluster, pool, node count), Line chart (node count over time).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" textPayload=*"upgrade"*
| table _time resource.labels.cluster_name textPayload
| sort -_time
```

## Visualization

Timeline (node pool events), Table (cluster, pool, node count), Line chart (node count over time).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
