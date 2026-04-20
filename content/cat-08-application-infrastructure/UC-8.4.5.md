---
id: "8.4.5"
title: "Service-to-Service Call Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.5 · Service-to-Service Call Failures

## Description

Inter-service communication failures in microservices architectures cascade quickly. Detection enables rapid isolation of failing services.

## Value

Inter-service communication failures in microservices architectures cascade quickly. Detection enables rapid isolation of failing services.

## Implementation

Configure Envoy/Istio to export access logs to Splunk. Parse source service, destination service, status code, and latency. Build service dependency map. Alert on inter-service error rate spikes. Track per-service error budgets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Istio/Envoy access logs, Linkerd tap.
• Ensure the following data sources are available: Envoy access logs (upstream_cluster, response_code), Istio telemetry.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Envoy/Istio to export access logs to Splunk. Parse source service, destination service, status code, and latency. Build service dependency map. Alert on inter-service error rate spikes. Track per-service error budgets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="envoy:access"
| where response_code >= 500
| stats count by upstream_cluster, downstream_cluster, response_code
| sort -count
```

Understanding this SPL

**Service-to-Service Call Failures** — Inter-service communication failures in microservices architectures cascade quickly. Detection enables rapid isolation of failing services.

Documented **Data sources**: Envoy access logs (upstream_cluster, response_code), Istio telemetry. **App/TA** (typical add-on context): Istio/Envoy access logs, Linkerd tap. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: mesh; **sourcetype**: envoy:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=mesh, sourcetype="envoy:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where response_code >= 500` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by upstream_cluster, downstream_cluster, response_code** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Service dependency map (with error highlighting), Table (failing service pairs), Heatmap (service × service error rate).

## SPL

```spl
index=mesh sourcetype="envoy:access"
| where response_code >= 500
| stats count by upstream_cluster, downstream_cluster, response_code
| sort -count
```

## Visualization

Service dependency map (with error highlighting), Table (failing service pairs), Heatmap (service × service error rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
