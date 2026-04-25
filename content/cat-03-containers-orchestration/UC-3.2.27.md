<!-- AUTO-GENERATED from UC-3.2.27.json — DO NOT EDIT -->

---
id: "3.2.27"
title: "Ingress Controller Error Rates"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.27 · Ingress Controller Error Rates

## Description

Controller-level 5xx and upstream errors isolate bad ingress classes, TLS backends, and canary routes before user-facing SLO breach.

## Value

Controller-level 5xx and upstream errors isolate bad ingress classes, TLS backends, and canary routes before user-facing SLO breach.

## Implementation

Standardize access log JSON with `ingress_class`, `upstream`, `status`. Baseline per ingress. Alert on error rate versus 7-day same-hour baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Ingress controller log pipeline (NGINX, Traefik, HAProxy).
• Ensure the following data sources are available: `sourcetype=kube:ingress:nginx`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Standardize access log JSON with `ingress_class`, `upstream`, `status`. Baseline per ingress. Alert on error rate versus 7-day same-hour baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval err=if(status>=500,1,0)
| bin _time span=5m
| stats sum(err) as e, count as n by ingress_class, upstream, _time
| eval err_rate=if(n>0, round(100*e/n,2), 0)
| where err_rate>2
| sort -err_rate
```

Understanding this SPL

**Ingress Controller Error Rates** — Controller-level 5xx and upstream errors isolate bad ingress classes, TLS backends, and canary routes before user-facing SLO breach.

Documented **Data sources**: `sourcetype=kube:ingress:nginx`. **App/TA** (typical add-on context): Ingress controller log pipeline (NGINX, Traefik, HAProxy). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:ingress:nginx. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:ingress:nginx". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **err** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by ingress_class, upstream, _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where err_rate>2` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (5xx rate by class), Table (upstream, err %), Single value (global ingress 5xx/min).

## SPL

```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval err=if(status>=500,1,0)
| bin _time span=5m
| stats sum(err) as e, count as n by ingress_class, upstream, _time
| eval err_rate=if(n>0, round(100*e/n,2), 0)
| where err_rate>2
| sort -err_rate
```

## Visualization

Line chart (5xx rate by class), Table (upstream, err %), Single value (global ingress 5xx/min).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
