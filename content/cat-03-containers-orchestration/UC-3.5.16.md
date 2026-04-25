<!-- AUTO-GENERATED from UC-3.5.16.json — DO NOT EDIT -->

---
id: "3.5.16"
title: "Kubernetes Event Correlation with Application Traces"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.16 · Kubernetes Event Correlation with Application Traces

## Description

When a Kubernetes OOMKill, pod eviction, or node pressure event coincides with an application error spike, the root cause is infrastructure — not application code. Without correlating K8s events with application traces, teams waste hours debugging application logic for failures caused by resource constraints. This correlation automatically links infrastructure events to their application impact, routing the incident to the right team (platform vs application) and reducing MTTR by eliminating misdiagnosis.

## Value

When a Kubernetes OOMKill, pod eviction, or node pressure event coincides with an application error spike, the root cause is infrastructure — not application code. Without correlating K8s events with application traces, teams waste hours debugging application logic for failures caused by resource constraints. This correlation automatically links infrastructure events to their application impact, routing the incident to the right team (platform vs application) and reducing MTTR by eliminating misdiagnosis.

## Implementation

Ingest Kubernetes events via the OTel Collector's `k8s_events` receiver or via Splunk Connect for Kubernetes. Focus on resource-related events: OOMKilling (memory limit exceeded), Evicted (node under pressure), FailedScheduling (no capacity), NodeNotReady (node failure), BackOff (crash loops). For each infrastructure event, query application traces in a ±15 minute window around the event timestamp, filtered by the affected namespace. Look for concurrent error spikes or latency increases. Classify the correlation: if app errors spike within 5 minutes of an OOMKill in the same namespace, the infrastructure event likely caused the app errors. Generate a correlated incident report that links the K8s event with the affected traces, enabling platform teams to see the application impact and application teams to see the infrastructure root cause. Feed into ITSI as correlated notable events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Distribution of OpenTelemetry Collector (k8s_events receiver), Splunk Observability Cloud.
• Ensure the following data sources are available: `sourcetype=kube:events`, `sourcetype=otel:traces`, `index=containers`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Kubernetes events via the OTel Collector's `k8s_events` receiver or via Splunk Connect for Kubernetes. Focus on resource-related events: OOMKilling (memory limit exceeded), Evicted (node under pressure), FailedScheduling (no capacity), NodeNotReady (node failure), BackOff (crash loops). For each infrastructure event, query application traces in a ±15 minute window around the event timestamp, filtered by the affected namespace. Look for concurrent error spikes or latency increases. Classif…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="kube:events" (reason="OOMKilling" OR reason="Evicted" OR reason="FailedScheduling" OR reason="NodeNotReady" OR reason="BackOff")
| eval k8s_event_severity=case(
    reason=="OOMKilling", "Critical",
    reason=="Evicted", "High",
    reason=="NodeNotReady", "Critical",
    1==1, "Medium")
| rename involvedObject.name as pod_name, involvedObject.namespace as namespace
| join type=left namespace [search index=traces sourcetype="otel:traces" earliest=-15m latest=+15m
    | eval is_error=if(status_code=="ERROR", 1, 0)
    | stats count as span_count, sum(is_error) as error_count, avg(eval(duration_nano/1000000)) as avg_duration_ms by k8s_namespace
    | rename k8s_namespace as namespace]
| eval app_impact=case(
    error_count > 10, "Application Error Spike Detected",
    avg_duration_ms > 2000, "Application Latency Spike Detected",
    isnotnull(span_count), "Application Running — No Visible Impact",
    1==1, "No Application Traces Available")
| table _time, namespace, pod_name, reason, k8s_event_severity, app_impact, error_count, avg_duration_ms, message
| sort -k8s_event_severity
```

Understanding this SPL

**Kubernetes Event Correlation with Application Traces** — When a Kubernetes OOMKill, pod eviction, or node pressure event coincides with an application error spike, the root cause is infrastructure — not application code. Without correlating K8s events with application traces, teams waste hours debugging application logic for failures caused by resource constraints. This correlation automatically links infrastructure events to their application impact, routing the incident to the right team (platform vs application) and reducing…

Documented **Data sources**: `sourcetype=kube:events`, `sourcetype=otel:traces`, `index=containers`. **App/TA** (typical add-on context): Splunk Distribution of OpenTelemetry Collector (k8s_events receiver), Splunk Observability Cloud. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **k8s_event_severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Renames fields with `rename` for clarity or joins.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **app_impact** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Kubernetes Event Correlation with Application Traces**): table _time, namespace, pod_name, reason, k8s_event_severity, app_impact, error_count, avg_duration_ms, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (K8s events overlaid with trace error rate), Table (correlated events with app impact), Bar chart (K8s events by reason), Line chart (trace error rate with event markers).

## SPL

```spl
index=containers sourcetype="kube:events" (reason="OOMKilling" OR reason="Evicted" OR reason="FailedScheduling" OR reason="NodeNotReady" OR reason="BackOff")
| eval k8s_event_severity=case(
    reason=="OOMKilling", "Critical",
    reason=="Evicted", "High",
    reason=="NodeNotReady", "Critical",
    1==1, "Medium")
| rename involvedObject.name as pod_name, involvedObject.namespace as namespace
| join type=left namespace [search index=traces sourcetype="otel:traces" earliest=-15m latest=+15m
    | eval is_error=if(status_code=="ERROR", 1, 0)
    | stats count as span_count, sum(is_error) as error_count, avg(eval(duration_nano/1000000)) as avg_duration_ms by k8s_namespace
    | rename k8s_namespace as namespace]
| eval app_impact=case(
    error_count > 10, "Application Error Spike Detected",
    avg_duration_ms > 2000, "Application Latency Spike Detected",
    isnotnull(span_count), "Application Running — No Visible Impact",
    1==1, "No Application Traces Available")
| table _time, namespace, pod_name, reason, k8s_event_severity, app_impact, error_count, avg_duration_ms, message
| sort -k8s_event_severity
```

## Visualization

Timeline (K8s events overlaid with trace error rate), Table (correlated events with app impact), Bar chart (K8s events by reason), Line chart (trace error rate with event markers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
