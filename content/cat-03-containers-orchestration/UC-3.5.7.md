<!-- AUTO-GENERATED from UC-3.5.7.json — DO NOT EDIT -->

---
id: "3.5.7"
title: "Envoy Proxy Error Rates"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.7 · Envoy Proxy Error Rates

## Description

Envoy aggregates L7 failures; trending 4xx/5xx and upstream errors isolates bad clusters and config rollouts quickly.

## Value

Envoy aggregates L7 failures; trending 4xx/5xx and upstream errors isolates bad clusters and config rollouts quickly.

## Implementation

Configure Envoy access logs (JSON) to stdout and collect via OTel filelog receiver or Fluent Bit to Splunk. Include `response_code`, `route_name`, `upstream_cluster`, `duration`. Optionally scrape `envoy_cluster_upstream_rq_xx` from Prometheus. Baseline error percentages per route and alert on spikes after deployments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (Envoy admin `/stats` or access log pipeline), `envoy.access_log`.
• Ensure the following data sources are available: `sourcetype=envoy:access` or `sourcetype=otel:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Envoy access logs (JSON) to stdout and collect via OTel filelog receiver or Fluent Bit to Splunk. Include `response_code`, `route_name`, `upstream_cluster`, `duration`. Optionally scrape `envoy_cluster_upstream_rq_xx` from Prometheus. Baseline error percentages per route and alert on spikes after deployments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="envoy:access"
| eval status=tonumber(response_code)
| eval is_err=if(status>=400 OR upstream_cluster="-" , 1, 0)
| stats count as total, sum(is_err) as err by route_name, upstream_cluster, cluster_name
| eval err_pct=round(100*err/total, 2)
| where err_pct>1 AND total>100
| sort -err_pct
```

Understanding this SPL

**Envoy Proxy Error Rates** — Envoy aggregates L7 failures; trending 4xx/5xx and upstream errors isolates bad clusters and config rollouts quickly.

Documented **Data sources**: `sourcetype=envoy:access` or `sourcetype=otel:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector (Envoy admin `/stats` or access log pipeline), `envoy.access_log`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: envoy:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="envoy:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **is_err** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by route_name, upstream_cluster, cluster_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **err_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where err_pct>1 AND total>100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (4xx/5xx rate by route), Table (top routes by error %), Heatmap (cluster vs status).

## SPL

```spl
index=containers sourcetype="envoy:access"
| eval status=tonumber(response_code)
| eval is_err=if(status>=400 OR upstream_cluster="-" , 1, 0)
| stats count as total, sum(is_err) as err by route_name, upstream_cluster, cluster_name
| eval err_pct=round(100*err/total, 2)
| where err_pct>1 AND total>100
| sort -err_pct
```

## Visualization

Time chart (4xx/5xx rate by route), Table (top routes by error %), Heatmap (cluster vs status).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
