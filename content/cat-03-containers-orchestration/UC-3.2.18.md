---
id: "3.2.18"
title: "Kubernetes Ingress Backend Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.18 · Kubernetes Ingress Backend Health

## Description

Ingress controller returning 502/503 due to unhealthy backends.

## Value

Ingress controller returning 502/503 due to unhealthy backends.

## Implementation

Forward ingress controller access logs to Splunk. For NGINX Ingress, enable access log format with `$upstream_addr` and `$upstream_status`. For Traefik, enable access logs with backend info. Parse status, host, path, and upstream. Alert when 502/503 rate exceeds 5% over 5 minutes or absolute count >10. Correlate with pod readiness and service endpoints.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes, ingress controller logs.
• Ensure the following data sources are available: nginx-ingress controller logs, traefik logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward ingress controller access logs to Splunk. For NGINX Ingress, enable access log format with `$upstream_addr` and `$upstream_status`. For Traefik, enable access logs with backend info. Parse status, host, path, and upstream. Alert when 502/503 rate exceeds 5% over 5 minutes or absolute count >10. Correlate with pod readiness and service endpoints.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s (sourcetype="kube:ingress:nginx" OR sourcetype="kube:ingress:traefik")
| eval is_backend_error = if(status>=502 AND status<=503, 1, 0)
| bin _time span=5m
| stats sum(is_backend_error) as backend_errors, count as total by host, path, upstream, _time
| eval error_rate = if(total>0, round(backend_errors/total*100, 2), 0)
| where error_rate > 5 OR backend_errors > 10
| table _time host path upstream backend_errors total error_rate
| sort -error_rate
```

Understanding this SPL

**Kubernetes Ingress Backend Health** — Ingress controller returning 502/503 due to unhealthy backends.

Documented **Data sources**: nginx-ingress controller logs, traefik logs. **App/TA** (typical add-on context): Splunk Connect for Kubernetes, ingress controller logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:ingress:nginx, kube:ingress:traefik. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:ingress:nginx". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_backend_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, path, upstream, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 5 OR backend_errors > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes Ingress Backend Health**): table _time host path upstream backend_errors total error_rate
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, path, upstream, errors, rate), Line chart (error rate over time), Single value (current 5xx rate).

## SPL

```spl
index=k8s (sourcetype="kube:ingress:nginx" OR sourcetype="kube:ingress:traefik")
| eval is_backend_error = if(status>=502 AND status<=503, 1, 0)
| bin _time span=5m
| stats sum(is_backend_error) as backend_errors, count as total by host, path, upstream, _time
| eval error_rate = if(total>0, round(backend_errors/total*100, 2), 0)
| where error_rate > 5 OR backend_errors > 10
| table _time host path upstream backend_errors total error_rate
| sort -error_rate
```

## Visualization

Table (host, path, upstream, errors, rate), Line chart (error rate over time), Single value (current 5xx rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
