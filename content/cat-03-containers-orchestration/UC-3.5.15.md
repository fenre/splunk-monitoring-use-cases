---
id: "3.5.15"
title: "eBPF Auto-Instrumented Service Metrics (Beyla)"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.5.15 · eBPF Auto-Instrumented Service Metrics (Beyla)

## Description

Traditional application instrumentation requires code changes (OTel SDK integration) or agent injection (Java agent, .NET profiler). eBPF auto-instrumentation tools like Grafana Beyla generate RED metrics (Request rate, Error rate, Duration) for HTTP and gRPC services by observing kernel-level syscalls — zero code changes, zero sidecar overhead, zero application awareness required. This provides instant observability for legacy services, third-party applications, and polyglot environments where manual instrumentation is impractical or too slow to roll out.

## Value

Traditional application instrumentation requires code changes (OTel SDK integration) or agent injection (Java agent, .NET profiler). eBPF auto-instrumentation tools like Grafana Beyla generate RED metrics (Request rate, Error rate, Duration) for HTTP and gRPC services by observing kernel-level syscalls — zero code changes, zero sidecar overhead, zero application awareness required. This provides instant observability for legacy services, third-party applications, and polyglot environments where manual instrumentation is impractical or too slow to roll out.

## Implementation

Deploy Beyla as a DaemonSet or sidecar. Beyla uses eBPF to intercept HTTP/gRPC syscalls and generate OpenTelemetry-compatible metrics and traces without any application code changes. Configure Beyla to export via OTLP to the OTel Collector, which forwards to Splunk. Beyla generates standard OTel HTTP semantic conventions: `http.server.request.duration`, `http.server.request.body.size`, `http.request.method`, `http.response.status_code`. Tag Beyla-generated telemetry with `instrumentation_source=beyla` to distinguish from SDK-instrumented data. Use Beyla for immediate coverage of uninstrumented services while teams work on proper OTel SDK integration. Compare Beyla RED metrics with SDK-generated metrics for instrumented services to validate accuracy. Track which services rely on Beyla vs SDK instrumentation to measure manual instrumentation progress.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Grafana Beyla (eBPF auto-instrumentation), Splunk Distribution of OpenTelemetry Collector.
• Ensure the following data sources are available: Beyla-generated OTel metrics and traces, `sourcetype=otel:metrics`, `sourcetype=otel:traces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Beyla as a DaemonSet or sidecar. Beyla uses eBPF to intercept HTTP/gRPC syscalls and generate OpenTelemetry-compatible metrics and traces without any application code changes. Configure Beyla to export via OTLP to the OTel Collector, which forwards to Splunk. Beyla generates standard OTel HTTP semantic conventions: `http.server.request.duration`, `http.server.request.body.size`, `http.request.method`, `http.response.status_code`. Tag Beyla-generated telemetry with `instrumentation_source=…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats avg(_value) as val WHERE index=otel_metrics metric_name IN (
    "http.server.request.duration",
    "http.server.request.body.size",
    "rpc.server.duration"
  ) AND instrumentation_source="beyla" BY metric_name, service_name, http_request_method, http_response_status_code span=5m
| eval signal=case(
    match(metric_name, "duration"), "duration_ms",
    match(metric_name, "body.size"), "request_size",
    match(metric_name, "rpc"), "rpc_duration_ms")
| eval is_error=if(http_response_status_code>=500, 1, 0)
| stats count as requests, sum(is_error) as errors, avg(val) as avg_duration by _time, service_name
| eval error_rate_pct=round(errors*100/requests, 2)
| eval req_per_sec=round(requests/300, 1)
| table _time, service_name, req_per_sec, error_rate_pct, avg_duration
| sort -error_rate_pct
```

Understanding this SPL

**eBPF Auto-Instrumented Service Metrics (Beyla)** — Traditional application instrumentation requires code changes (OTel SDK integration) or agent injection (Java agent, .NET profiler). eBPF auto-instrumentation tools like Grafana Beyla generate RED metrics (Request rate, Error rate, Duration) for HTTP and gRPC services by observing kernel-level syscalls — zero code changes, zero sidecar overhead, zero application awareness required. This provides instant observability for legacy services, third-party applications, and…

Documented **Data sources**: Beyla-generated OTel metrics and traces, `sourcetype=otel:metrics`, `sourcetype=otel:traces`. **App/TA** (typical add-on context): Grafana Beyla (eBPF auto-instrumentation), Splunk Distribution of OpenTelemetry Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: otel_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `eval` defines or adjusts **signal** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by _time, service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **error_rate_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **req_per_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **eBPF Auto-Instrumented Service Metrics (Beyla)**): table _time, service_name, req_per_sec, error_rate_pct, avg_duration
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (service RED metrics from Beyla), Line chart (request rate and error rate per service), Bar chart (services by instrumentation source — Beyla vs SDK), Gauge (error rate per service).

## SPL

```spl
| mstats avg(_value) as val WHERE index=otel_metrics metric_name IN (
    "http.server.request.duration",
    "http.server.request.body.size",
    "rpc.server.duration"
  ) AND instrumentation_source="beyla" BY metric_name, service_name, http_request_method, http_response_status_code span=5m
| eval signal=case(
    match(metric_name, "duration"), "duration_ms",
    match(metric_name, "body.size"), "request_size",
    match(metric_name, "rpc"), "rpc_duration_ms")
| eval is_error=if(http_response_status_code>=500, 1, 0)
| stats count as requests, sum(is_error) as errors, avg(val) as avg_duration by _time, service_name
| eval error_rate_pct=round(errors*100/requests, 2)
| eval req_per_sec=round(requests/300, 1)
| table _time, service_name, req_per_sec, error_rate_pct, avg_duration
| sort -error_rate_pct
```

## Visualization

Table (service RED metrics from Beyla), Line chart (request rate and error rate per service), Bar chart (services by instrumentation source — Beyla vs SDK), Gauge (error rate per service).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
