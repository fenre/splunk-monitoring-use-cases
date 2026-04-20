---
id: "4.2.7"
title: "AKS Cluster Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.7 · AKS Cluster Health

## Description

AKS cluster health monitoring ensures Kubernetes workloads are running reliably on Azure's managed platform.

## Value

AKS cluster health monitoring ensures Kubernetes workloads are running reliably on Azure's managed platform.

## Implementation

Enable AKS diagnostic logging to Event Hub (kube-apiserver, kube-controller-manager, kube-scheduler, kube-audit). Deploy OTel Collector in the AKS cluster for deeper K8s-level monitoring (see Category 3.2).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Splunk OTel Collector.
• Ensure the following data sources are available: AKS diagnostics, kube-state-metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AKS diagnostic logging to Event Hub (kube-apiserver, kube-controller-manager, kube-scheduler, kube-audit). Deploy OTel Collector in the AKS cluster for deeper K8s-level monitoring (see Category 3.2).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="kube-apiserver" level="Error"
| stats count by host, message
| sort -count
```

Understanding this SPL

**AKS Cluster Health** — AKS cluster health monitoring ensures Kubernetes workloads are running reliably on Azure's managed platform.

Documented **Data sources**: AKS diagnostics, kube-state-metrics. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel, Error timeline, Table.

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="kube-apiserver" level="Error"
| stats count by host, message
| sort -count
```

## Visualization

Status panel, Error timeline, Table.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
