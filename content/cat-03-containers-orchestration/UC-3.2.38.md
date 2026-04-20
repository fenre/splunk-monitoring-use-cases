---
id: "3.2.38"
title: "Vertical Pod Autoscaler Recommendations"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.38 · Vertical Pod Autoscaler Recommendations

## Description

VPA recommendation divergence from actual requests drives right-sizing and prevents CPU starvation when recommendations are not applied.

## Value

VPA recommendation divergence from actual requests drives right-sizing and prevents CPU starvation when recommendations are not applied.

## Implementation

Ingest VPA recommendation metrics (or periodic JSON status). Compare recommendation to live requests. Alert on large sustained gaps for tier-1 workloads.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: VPA metrics export, `kubectl describe vpa` JSON job.
• Ensure the following data sources are available: `sourcetype=kube:metrics`, `sourcetype=kube:vpa:status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest VPA recommendation metrics (or periodic JSON status). Compare recommendation to live requests. Alert on large sustained gaps for tier-1 workloads.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="vpa_recommendation_target_cpu"
| stats latest(_value) as target_millicores by namespace, verticalpodautoscaler
| join type=left max=1 namespace verticalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_pod_container_resource_requests" resource="cpu"
    | stats latest(_value) as request_millicores by namespace, pod
]
| eval gap_m=abs(target_millicores-request_millicores)
| where gap_m>500
| table namespace verticalpodautoscaler target_millicores request_millicores gap_m
```

Understanding this SPL

**Vertical Pod Autoscaler Recommendations** — VPA recommendation divergence from actual requests drives right-sizing and prevents CPU starvation when recommendations are not applied.

Documented **Data sources**: `sourcetype=kube:metrics`, `sourcetype=kube:vpa:status`. **App/TA** (typical add-on context): VPA metrics export, `kubectl describe vpa` JSON job. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, verticalpodautoscaler** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **gap_m** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where gap_m>500` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Vertical Pod Autoscaler Recommendations**): table namespace verticalpodautoscaler target_millicores request_millicores gap_m


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (workload, target vs request), Line chart (recommendation drift), Bar chart (gap).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="vpa_recommendation_target_cpu"
| stats latest(_value) as target_millicores by namespace, verticalpodautoscaler
| join type=left max=1 namespace verticalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_pod_container_resource_requests" resource="cpu"
    | stats latest(_value) as request_millicores by namespace, pod
]
| eval gap_m=abs(target_millicores-request_millicores)
| where gap_m>500
| table namespace verticalpodautoscaler target_millicores request_millicores gap_m
```

## Visualization

Table (workload, target vs request), Line chart (recommendation drift), Bar chart (gap).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
