<!-- AUTO-GENERATED from UC-8.4.6.json — DO NOT EDIT -->

---
id: "8.4.6"
title: "Circuit Breaker Activations"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.6 · Circuit Breaker Activations

## Description

Circuit breaker trips indicate a downstream service is failing. Quick detection enables proactive communication and remediation.

## Value

Circuit breaker trips indicate a downstream service is failing. Quick detection enables proactive communication and remediation.

## Implementation

Monitor Envoy circuit breaker metrics. Alert on any circuit breaker opening. Track circuit breaker state transitions. Correlate with upstream service health to validate circuit breaker configuration thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Service mesh metrics, Envoy stats.
• Ensure the following data sources are available: Envoy cluster stats (circuit breaker metrics), Istio DestinationRule events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Envoy circuit breaker metrics. Alert on any circuit breaker opening. Track circuit breaker state transitions. Correlate with upstream service health to validate circuit breaker configuration thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="envoy:stats"
| search "circuit_breaker" "cx_open" OR "rq_open"
| stats count by upstream_cluster
| where count > 0
```

Understanding this SPL

**Circuit Breaker Activations** — Circuit breaker trips indicate a downstream service is failing. Quick detection enables proactive communication and remediation.

Documented **Data sources**: Envoy cluster stats (circuit breaker metrics), Istio DestinationRule events. **App/TA** (typical add-on context): Service mesh metrics, Envoy stats. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: mesh; **sourcetype**: envoy:stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=mesh, sourcetype="envoy:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by upstream_cluster** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (service × circuit breaker state), Timeline (circuit breaker events), Table (active circuit breakers).

## SPL

```spl
index=mesh sourcetype="envoy:stats"
| search "circuit_breaker" "cx_open" OR "rq_open"
| stats count by upstream_cluster
| where count > 0
```

## Visualization

Status grid (service × circuit breaker state), Timeline (circuit breaker events), Table (active circuit breakers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
