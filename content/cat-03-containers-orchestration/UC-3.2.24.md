---
id: "3.2.24"
title: "HPA Scale-Out Event Correlation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.24 · HPA Scale-Out Event Correlation

## Description

Correlating HPA decisions with replica metrics explains surprise scale-outs and validates max replica settings under load.

## Value

Correlating HPA decisions with replica metrics explains surprise scale-outs and validates max replica settings under load.

## Implementation

Ingest HPA events and kube-state-metrics HPA series. Join current replicas with event stream for postmortems. Alert when scaling messages repeat while replicas stay at max.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:objects:events`, `sourcetype=kube:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest HPA events and kube-state-metrics HPA series. Join current replicas with event stream for postmortems. Alert when scaling messages repeat while replicas stay at max.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_status_current_replicas"
| stats latest(_value) as current by namespace, horizontalpodautoscaler
| join type=left max=1 namespace horizontalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_spec_max_replicas"
    | stats latest(_value) as max_rep by namespace, horizontalpodautoscaler
]
| where current>=max_rep AND max_rep>0
| table namespace horizontalpodautoscaler current max_rep
```

Understanding this SPL

**HPA Scale-Out Event Correlation** — Correlating HPA decisions with replica metrics explains surprise scale-outs and validates max replica settings under load.

Documented **Data sources**: `sourcetype=kube:objects:events`, `sourcetype=kube:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector, kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, horizontalpodautoscaler** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where current>=max_rep AND max_rep>0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **HPA Scale-Out Event Correlation**): table namespace horizontalpodautoscaler current max_rep


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replicas over time), Table (HPA, events), Single value (scale events/hour).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_status_current_replicas"
| stats latest(_value) as current by namespace, horizontalpodautoscaler
| join type=left max=1 namespace horizontalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_spec_max_replicas"
    | stats latest(_value) as max_rep by namespace, horizontalpodautoscaler
]
| where current>=max_rep AND max_rep>0
| table namespace horizontalpodautoscaler current max_rep
```

## Visualization

Line chart (replicas over time), Table (HPA, events), Single value (scale events/hour).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
