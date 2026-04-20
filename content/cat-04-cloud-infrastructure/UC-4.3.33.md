---
id: "4.3.33"
title: "GKE Node Auto-Repair Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.33 · GKE Node Auto-Repair Events

## Description

Auto-repair replaces unhealthy nodes; frequent repairs indicate image, disk, or hardware issues affecting workload stability.

## Value

Auto-repair replaces unhealthy nodes; frequent repairs indicate image, disk, or hardware issues affecting workload stability.

## Implementation

Correlate repairs with container restarts and kernel OOM. Alert when repairs per day exceed baseline for a pool. Review node image version skew.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: GKE node pool operations in `sourcetype=google:gcp:pubsub:message`, cluster operations log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Correlate repairs with container restarts and kernel OOM. Alert when repairs per day exceed baseline for a pool. Review node image version skew.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="repairNodePool" OR textPayload="*auto-repair*"
| stats count by resource.labels.cluster_name, resource.labels.node_pool
| sort -count
```

Understanding this SPL

**GKE Node Auto-Repair Events** — Auto-repair replaces unhealthy nodes; frequent repairs indicate image, disk, or hardware issues affecting workload stability.

Documented **Data sources**: GKE node pool operations in `sourcetype=google:gcp:pubsub:message`, cluster operations log. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.cluster_name, resource.labels.node_pool** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (repairs by pool), Timeline (repair events), Table (cluster, pool, count).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="repairNodePool" OR textPayload="*auto-repair*"
| stats count by resource.labels.cluster_name, resource.labels.node_pool
| sort -count
```

## Visualization

Bar chart (repairs by pool), Timeline (repair events), Table (cluster, pool, count).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
