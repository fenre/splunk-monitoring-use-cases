<!-- AUTO-GENERATED from UC-3.2.9.json — DO NOT EDIT -->

---
id: "3.2.9"
title: "Ingress Error Rates"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.9 · Ingress Error Rates

## Description

Ingress controllers are the front door to your services. High error rates mean users are getting errors. Catches backend failures and misconfigurations.

## Value

Ingress controllers are the front door to your services. High error rates mean users are getting errors. Catches backend failures and misconfigurations.

## Implementation

Forward ingress controller access logs. Parse status code, upstream response time, and backend server. Alert when 5xx error rate exceeds 5% over 5 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Ingress controller log forwarding (NGINX, Traefik, etc.).
• Ensure the following data sources are available: `sourcetype=kube:ingress:nginx` or similar.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward ingress controller access logs. Parse status code, upstream response time, and backend server. Alert when 5xx error rate exceeds 5% over 5 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval is_error = if(status >= 500, 1, 0)
| timechart span=5m sum(is_error) as errors, count as total
| eval error_rate = if(total>0, round(errors/total*100, 2), 0)
| where error_rate > 5
```

Understanding this SPL

**Ingress Error Rates** — Ingress controllers are the front door to your services. High error rates mean users are getting errors. Catches backend failures and misconfigurations.

Documented **Data sources**: `sourcetype=kube:ingress:nginx` or similar. **App/TA** (typical add-on context): Ingress controller log forwarding (NGINX, Traefik, etc.). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:ingress:nginx. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:ingress:nginx". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate over time), Table (top error paths), Single value (current error rate).

## SPL

```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval is_error = if(status >= 500, 1, 0)
| timechart span=5m sum(is_error) as errors, count as total
| eval error_rate = if(total>0, round(errors/total*100, 2), 0)
| where error_rate > 5
```

## Visualization

Line chart (error rate over time), Table (top error paths), Single value (current error rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
