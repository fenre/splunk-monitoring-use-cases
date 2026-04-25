<!-- AUTO-GENERATED from UC-3.2.41.json — DO NOT EDIT -->

---
id: "3.2.41"
title: "Service Endpoint Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.41 · Service Endpoint Health

## Description

Services with zero ready endpoints drop traffic for ClusterIP clients; fast detection isolates label selector and readiness probe issues.

## Value

Services with zero ready endpoints drop traffic for ClusterIP clients; fast detection isolates label selector and readiness probe issues.

## Implementation

Scrape EndpointSlice metrics (`kube_endpoint_*`). Exclude headless where appropriate. Alert when `available==0` for production Services.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape EndpointSlice metrics (`kube_endpoint_*`). Exclude headless where appropriate. Alert when `available==0` for production Services.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_available"
| stats latest(_value) as avail by namespace, service
| join type=left max=1 namespace service [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_not_ready"
    | stats latest(_value) as not_ready by namespace, service
]
| where avail=0 OR not_ready>0
| table namespace service avail not_ready
```

Understanding this SPL

**Service Endpoint Health** — Services with zero ready endpoints drop traffic for ClusterIP clients; fast detection isolates label selector and readiness probe issues.

Documented **Data sources**: `sourcetype=kube:metrics`. **App/TA** (typical add-on context): kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, service** so each row reflects one combination of those dimensions.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where avail=0 OR not_ready>0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Service Endpoint Health**): table namespace service avail not_ready


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (service, endpoints), Status grid, Line chart (ready endpoints).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_available"
| stats latest(_value) as avail by namespace, service
| join type=left max=1 namespace service [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_not_ready"
    | stats latest(_value) as not_ready by namespace, service
]
| where avail=0 OR not_ready>0
| table namespace service avail not_ready
```

## Visualization

Table (service, endpoints), Status grid, Line chart (ready endpoints).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
