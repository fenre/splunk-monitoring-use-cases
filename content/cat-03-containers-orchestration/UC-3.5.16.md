<!-- AUTO-GENERATED from UC-3.5.16.json — DO NOT EDIT -->

---
id: "3.5.16"
title: "Kubernetes Event Correlation with Application Traces"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.16 · Kubernetes Event Correlation with Application Traces

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*When something breaks in the building's plumbing and the restaurant upstairs starts getting complaints, we connect those two events together so the maintenance crew knows the real problem is pipes, not the chef.*

---

## Description

Correlates **Kubernetes infrastructure events** (OOMKill, Eviction, FailedScheduling, NodeNotReady, BackOff) with **OpenTelemetry application traces** in the same namespace and time window to determine whether infrastructure failures caused application-visible impact — classifying correlations as CONFIRMED_IMPACT, LATENCY_IMPACT, PROBABLE_IMPACT, or NO_VISIBLE_IMPACT and detecting **causal sequences** where OOMKills precede application error spikes by minutes.

## Value

When an application starts throwing 500 errors, the debugging instinct is to blame application code. But if a Kubernetes OOMKill terminated a dependent microservice 3 minutes earlier, the root cause is infrastructure resource exhaustion, not a code bug. Without cross-domain correlation, platform teams see OOMKill events with no application context, and application teams see error spikes with no infrastructure context — both teams investigate independently, doubling the MTTR. This use case bridges the gap by automatically linking infrastructure events to their application impact within a ±15 minute window, routing the incident to the correct team with the full causal chain.

## Implementation

Ingest Kubernetes Warning events via the OTel Collector k8s_events receiver and application traces via OTLP, both into index=containers. Build two search variants: infrastructure-to-application impact correlation with severity and impact classification, and OOMKill-to-error causal timeline detection. Alert when CONFIRMED_IMPACT or STRONG_CAUSAL correlations are detected.

## Detailed Implementation

### Prerequisites
- **Kubernetes cluster** with the **OTel Collector** deployed as a **DaemonSet** running the **k8s_events receiver** to collect all Warning events from the Kubernetes API. The receiver watches the **Event API** and emits structured events with reason, type, message, and involvedObject metadata.
- **Application traces** collected via the **OTLP receiver** (gRPC port 4317, HTTP port 4318) from applications instrumented with **OpenTelemetry SDKs** or auto-instrumented via **Beyla** (UC-3.5.15). Traces must include **Kubernetes resource attributes** (`k8s.namespace.name`, `k8s.pod.name`, `k8s.deployment.name`) for accurate correlation with infrastructure events.
- **Splunk HEC** token for **`index=containers`** with sourcetype routing for **`kube:events`**, **`otel:traces`**, **`kube:pod:status`**, **`kube:container:logs`**, and **`otel:metrics`**.
- **Namespace-level correlation**: the correlation works by matching infrastructure events and application traces within the **same Kubernetes namespace**. This assumes that services within a namespace are related — which is the standard multi-tenant Kubernetes deployment pattern. If your architecture uses **cross-namespace service dependencies**, you will need to extend the correlation to include upstream/downstream namespaces.
- **Trace volume consideration**: the correlation join queries traces within a **±15 minute window** around each infrastructure event. High-volume trace environments (>10,000 spans/minute) should use **summary indexes** or pre-computed **error rate metrics** to avoid expensive join operations.
- **OTel Collector pipeline**: configure the **k8sattributes processor** to enrich traces with Kubernetes metadata (namespace, pod, deployment, node). Without this enrichment, the `k8s_namespace` field is missing from traces and the correlation join fails.
- **License estimate**: Kubernetes events are low-volume — a healthy 200-pod cluster generates 100–1,000 events/day (~200 KB–2 MB). The trace volume depends on application instrumentation depth and traffic — typically 1–50 GB/day for a mid-size cluster.
- Splunk RBAC: assign an **`sre_analyst`** role with **`srchIndexesAllowed`** including `containers`.

### Step 1 — Configure data collection
(1) **Kubernetes events**: the OTel Collector's **k8s_events receiver** watches the Kubernetes **Event API** and collects all Warning and Normal events. Key event **reasons** for infrastructure correlation:
  — **OOMKilling**: the **kubelet** terminated a container because it exceeded its **memory limit**. This is the most common infrastructure-caused application failure.
  — **Evicted**: the node is under **resource pressure** (disk, memory, PID) and the **kubelet** evicted pods to reclaim resources.
  — **FailedScheduling**: the **scheduler** cannot find a node with sufficient resources for the pod. This indicates **cluster capacity exhaustion**.
  — **NodeNotReady**: a node has become **unresponsive** — all pods on that node are affected.
  — **BackOff**: the container is in a **crash loop** — it starts, crashes, and restarts repeatedly with exponential backoff.
  — **Unhealthy**: a **liveness** or **readiness probe** failed — the pod may be restarted or removed from service endpoints.
  — **FailedMount**: a **persistent volume** could not be mounted — the pod cannot start because its storage is unavailable.
  — **ImagePullBackOff**: the container image could not be pulled — registry connectivity, authentication, or image tag issues.

(2) **Application traces**: collect traces via the **OTLP receiver** and ensure the **k8sattributes processor** adds Kubernetes context. Critical trace fields for correlation:
  — **`service_name`**: the application service generating the trace
  — **`status_code`**: ERROR indicates a failed span
  — **`duration_ms`** or **`duration_nano`**: span duration for latency analysis
  — **`http_status_code`**: HTTP response code (5xx indicates server errors)
  — **`k8s_namespace`**: the namespace where the service runs — this is the **correlation key** with infrastructure events

(3) **Pod status collection**: collect **`sourcetype=kube:pod:status`** to enrich the correlation with container **restart counts**, **termination reasons**, and **exit codes**. A container terminated with `reason=OOMKilled` and `exitCode=137` confirms the OOMKill event.

(4) **Application container logs**: collect **`sourcetype=kube:container:logs`** from affected pods. When the correlation detects impact, the logs provide root-cause detail — **stack traces**, **error messages**, and **connection timeout** patterns that explain how the infrastructure event propagated to application failures.

(5) **Correlation window tuning**: the default ±15 minute window captures most infrastructure-to-application impact chains. However, some impacts are immediate (OOMKill → instant restart → 503 errors) while others are delayed (NodeNotReady → pod rescheduling → 2-minute gap → service recovery). Use the **causal sequence** SPL variant to determine the typical time-to-impact for your environment and tune the window accordingly.

### Step 2 — Create the search and alert
The primary SPL correlates **infrastructure events** with **application traces** by joining on namespace within a ±15 minute window. The **app_impact** classification:
  — **CONFIRMED_IMPACT**: error rate > 10% AND the infrastructure event is CRITICAL or HIGH severity — strong evidence that the infrastructure event caused application failures
  — **LATENCY_IMPACT**: p95 latency > 2000ms AND the infrastructure event is CRITICAL or HIGH — the infrastructure event degraded application performance
  — **PROBABLE_IMPACT**: error rate > 5% — elevated errors correlate with the infrastructure event but the evidence is weaker
  — **NO_VISIBLE_IMPACT**: traces exist but show no error or latency increase — the infrastructure event did not visibly affect the application
  — **NO_TRACES**: no traces available for the namespace — cannot determine application impact (instrumentation gap)

The **causal sequence** variant focuses specifically on **OOMKill events** and detects the temporal pattern where an OOMKill precedes an error spike. The **causality** classification uses time difference:
  — **STRONG_CAUSAL**: error spike within 2 minutes of OOMKill — the OOMKill very likely caused the errors
  — **PROBABLE_CAUSAL**: error spike within 5 minutes — likely related
  — **POSSIBLE_CORRELATION**: error spike within 15 minutes — may be related or coincidental

Schedule the correlation search every **5 minutes** and alert on CONFIRMED_IMPACT (PagerDuty P2) or STRONG_CAUSAL (PagerDuty P2 + Slack). Schedule a **daily summary** of all correlations for trend analysis.

### Step 3 — Validate
(a) Verify event collection: `index=containers sourcetype="kube:events" type="Warning" earliest=-24h | stats count by reason | sort -count`. Should show OOMKilling, BackOff, and other expected events.
(b) Verify trace collection: `index=containers sourcetype="otel:traces" earliest=-1h | stats dc(service_name) as services, count as spans`. Should show active services.
(c) Test correlation: find a known OOMKill event and check for trace errors in the same namespace: `index=containers sourcetype="otel:traces" k8s_namespace="<ns>" status_code="ERROR" earliest=<oom_time-15m> latest=<oom_time+15m>`.
(d) Verify Kubernetes enrichment: `index=containers sourcetype="otel:traces" earliest=-1h | stats count by k8s_namespace | where isnotnull(k8s_namespace)`. All traces should have namespace information.
(e) Validate impact classification: review recent CONFIRMED_IMPACT correlations and verify the infrastructure event plausibly caused the application errors.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — correlated incidents (last 24h), CONFIRMED_IMPACT count (red if > 0), average time-to-impact (minutes), namespaces with no traces (instrumentation gaps).
- Row B: **dual-axis timeline** — primary axis shows infrastructure event counts by severity (stacked bars), secondary axis shows application error rate (line) — visual alignment reveals causal patterns.
- Row C: **correlation table** — ns, infra_severity, reasons, affected_pods, app_impact, error_rate, p95_latency, affected_services. Color-coded by app_impact.
- Row D: **causal sequence table** — ns, pod, oom_time, svc, errors_per_min, time_diff_min, causality. Ordered by causality strength.
- **Alerting**: CONFIRMED_IMPACT → PagerDuty P2 + Slack `#sre-incidents` with full context (infrastructure event + application impact metrics); STRONG_CAUSAL OOMKill → PagerDuty P2; PROBABLE_IMPACT sustained > 15 minutes → Slack `#sre-alerts`; NO_TRACES for production namespace → weekly instrumentation gap report.
- **Runbook** (owner: SRE team): (1) for OOMKill+CONFIRMED_IMPACT: increase memory limits or optimize application memory usage, (2) for FailedScheduling+CONFIRMED_IMPACT: check cluster capacity and autoscaler configuration, (3) for NodeNotReady: check node health and reschedule affected pods, (4) for LATENCY_IMPACT without error spike: the infrastructure event caused degradation but not failure — may resolve with pod rescheduling.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **swimlane timeline** with one lane per namespace showing infrastructure events (markers) and application error rate (line). When an event marker aligns with an error rate spike in the same lane, the visual correlation is immediately apparent. Color markers by **infra_severity** (red for CRITICAL, orange for HIGH) and shade the error rate line by **app_impact**.
- **Alert design**: include `ns`, `infra_severity`, `reasons`, `affected_pods`, `event_count`, `app_impact`, `error_rate`, `p95_latency`, `affected_services`, and `last_msg` in the alert payload. For causal alerts include `pod`, `oom_time`, `time_diff_min`, and `causality`.
- **Join returns no results** — the `k8s_namespace` field in traces may not match the namespace format in events. Verify field names: events use `involvedObject.namespace` while traces use `k8s.namespace.name`. The SPL uses coalesce to handle both.
- **False correlations in shared namespaces** — if multiple unrelated services share a namespace, an OOMKill in one service may correlate with errors in an unrelated service. Use pod-level (not namespace-level) correlation for shared namespaces.
- **Trace latency shows no impact but users report errors** — the issue may be at the **network** level (load balancer, ingress) rather than within the application. Check Ingress controller metrics (UC-3.6.6) and service mesh telemetry (UC-3.5.2) for external-facing impact.
- **High join cost with large trace volumes** — the join operation scans all traces in the ±15 minute window. For high-volume environments, pre-compute namespace-level error rate metrics in a **summary index** and join against the summary instead of raw traces.

## SPL

```spl
`comment("--- Infrastructure Event to Application Impact Correlation ---")`
index=containers sourcetype="kube:events" type="Warning"
    reason IN ("OOMKilling", "Evicted", "FailedScheduling", "NodeNotReady", "BackOff", "Unhealthy", "FailedMount", "ImagePullBackOff")
| eval ns=coalesce(involvedObject.namespace, namespace, object_namespace)
| eval pod=coalesce(involvedObject.name, object_name)
| eval obj_kind=coalesce(involvedObject.kind, object_kind)
| eval infra_severity=case(
    reason IN ("OOMKilling", "NodeNotReady"), "CRITICAL",
    reason IN ("Evicted", "FailedScheduling"), "HIGH",
    reason IN ("BackOff", "Unhealthy"), "MEDIUM",
    1=1, "LOW")
| bin _time span=5m
| stats count as event_count,
    dc(pod) as affected_pods,
    values(reason) as reasons,
    latest(message) as last_msg
    by _time, ns, infra_severity
| join type=left ns [
    search index=containers sourcetype="otel:traces" earliest=-15m latest=+15m
    | eval is_error=if(status_code="ERROR" OR http_status_code >= 500, 1, 0)
    | eval latency_ms=coalesce(duration_ms, duration_nano/1000000)
    | stats count as span_count,
        sum(is_error) as error_spans,
        avg(latency_ms) as avg_latency,
        perc95(latency_ms) as p95_latency,
        dc(service_name) as affected_services
        by k8s_namespace
    | rename k8s_namespace as ns
]
| eval error_rate=if(span_count > 0, round(error_spans / span_count * 100, 2), 0)
| eval app_impact=case(
    error_rate > 10 AND infra_severity IN ("CRITICAL", "HIGH"), "CONFIRMED_IMPACT",
    p95_latency > 2000 AND infra_severity IN ("CRITICAL", "HIGH"), "LATENCY_IMPACT",
    error_rate > 5, "PROBABLE_IMPACT",
    isnotnull(span_count) AND span_count > 0, "NO_VISIBLE_IMPACT",
    1=1, "NO_TRACES")
| where app_impact IN ("CONFIRMED_IMPACT", "LATENCY_IMPACT", "PROBABLE_IMPACT")
| table _time ns infra_severity reasons affected_pods event_count app_impact error_rate p95_latency affected_services last_msg
| sort -infra_severity, -error_rate

`comment("--- OOMKill to Error Spike Timeline — Causal Sequence Detection ---")`
index=containers sourcetype="kube:events" reason="OOMKilling"
| eval ns=coalesce(involvedObject.namespace, namespace)
| eval pod=coalesce(involvedObject.name, object_name)
| eval oom_time=_time
| table oom_time ns pod message
| join type=left ns [
    search index=containers sourcetype="otel:traces" status_code="ERROR"
    | eval ns=coalesce(k8s_namespace, namespace)
    | eval svc=coalesce(service_name, service)
    | bin _time span=1m
    | stats count as errors_per_min by _time, ns, svc
]
| eval time_diff_min=round(abs(_time - oom_time) / 60, 1)
| where time_diff_min <= 15
| eval causality=case(
    time_diff_min <= 2, "STRONG_CAUSAL",
    time_diff_min <= 5, "PROBABLE_CAUSAL",
    time_diff_min <= 15, "POSSIBLE_CORRELATION",
    1=1, "UNLIKELY")
| sort ns, oom_time, _time
| table ns pod oom_time svc _time errors_per_min time_diff_min causality
```

## Visualization

Dual-axis timeline (K8s events on primary axis, trace error rate on secondary), correlation matrix table, OOMKill causal sequence diagram, single-value tiles (correlated incidents, confirmed impacts, avg time-to-impact).

## Known False Positives

**coincidental_timing** — An application error spike may occur within the same 15-minute window as an infrastructure event without any causal relationship. Two independent issues — a code deployment causing errors and a separate OOMKill on an unrelated pod — appear correlated because they share a namespace and time window. Cross-reference with deployment records and change management logs.

**graceful_pod_termination** — When Kubernetes evicts a pod gracefully, the pod receives SIGTERM and has a shutdown grace period to complete in-flight requests. If the application handles shutdown correctly, no errors are visible in traces even though an infrastructure event occurred. The correlation correctly shows NO_VISIBLE_IMPACT.

**autoscaler_induced_events** — Horizontal Pod Autoscaler scale-down generates pod termination events that are normal operational behavior. These events may briefly correlate with trace latency increases as connections are rebalanced across remaining pods. Filter HPA-initiated events via the event message.

**preemptible_node_rotation** — Cloud providers may preempt spot/preemptible nodes, generating NodeNotReady events followed by pod rescheduling. If the application is designed for this (with pod disruption budgets and graceful migration), the transient events do not indicate real impact. Check PDB compliance before escalating.

**batch_job_memory_patterns** — Batch processing jobs intentionally consume large amounts of memory and may trigger OOMKill events at completion. These OOMKills are expected behavior for memory-intensive workloads and do not indicate a problem requiring remediation. Classify batch job namespaces separately.

**probe_configuration_drift** — Readiness and liveness probe thresholds may become too aggressive after an application update changes startup time. The resulting Unhealthy events are not infrastructure problems but probe misconfiguration. Correlate with recent deployment events to identify configuration drift.

## References

- [Kubernetes — Events and Event API](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [OpenTelemetry — Trace Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/general/trace/)
- [Splunk OTel Collector — k8s_events Receiver](https://docs.splunk.com/observability/en/gdi/opentelemetry/components/k8s-events-receiver.html)
- [Splunk — join Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Join)
- [Kubernetes — Resource Management for Pods](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
