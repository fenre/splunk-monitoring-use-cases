---
id: "3.3.6"
title: "Operator Health Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.6 · Operator Health Monitoring

## Description

OpenShift operators reconcile cluster components; tracking Available/Progressing/Degraded across the full operator set surfaces partial failures before user-facing symptoms.

## Value

OpenShift operators reconcile cluster components; tracking Available/Progressing/Degraded across the full operator set surfaces partial failures before user-facing symptoms.

## Implementation

Ingest ClusterOperator status on a 5-minute cadence. Build a health matrix per cluster. Alert when any operator is `Degraded=True` or `Available=False` beyond the remediation SLA.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (`oc get clusteroperator -o json`).
• Ensure the following data sources are available: `sourcetype=openshift:clusteroperator`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest ClusterOperator status on a 5-minute cadence. Build a health matrix per cluster. Alert when any operator is `Degraded=True` or `Available=False` beyond the remediation SLA.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:clusteroperator"
| where progressing="True" OR degraded="True" OR available="False"
| stats values(available) as avail, values(degraded) as deg, values(progressing) as prog by cluster, operator
| sort cluster, operator
```

Understanding this SPL

**Operator Health Monitoring** — OpenShift operators reconcile cluster components; tracking Available/Progressing/Degraded across the full operator set surfaces partial failures before user-facing symptoms.

Documented **Data sources**: `sourcetype=openshift:clusteroperator`. **App/TA** (typical add-on context): Custom API input (`oc get clusteroperator -o json`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:clusteroperator. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:clusteroperator". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where progressing="True" OR degraded="True" OR available="False"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cluster, operator** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Operator matrix (green/yellow/red), Table (operator, conditions), Timeline of flapping.

## SPL

```spl
index=openshift sourcetype="openshift:clusteroperator"
| where progressing="True" OR degraded="True" OR available="False"
| stats values(available) as avail, values(degraded) as deg, values(progressing) as prog by cluster, operator
| sort cluster, operator
```

## Visualization

Operator matrix (green/yellow/red), Table (operator, conditions), Timeline of flapping.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
