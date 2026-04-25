<!-- AUTO-GENERATED from UC-4.3.39.json — DO NOT EDIT -->

---
id: "4.3.39"
title: "Anthos Service Mesh Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.39 · Anthos Service Mesh Health

## Description

Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

## Value

Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

## Implementation

Export Istio canonical metrics (4xx/5xx, request duration) to Cloud Monitoring and Splunk. Dashboard golden signals per service. Alert on error rate > 1% or p99 latency vs SLO. Include control plane (istiod) pod health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`, Anthos Service Mesh telemetry.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (Istio canonical metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export Istio canonical metrics (4xx/5xx, request duration) to Cloud Monitoring and Splunk. Dashboard golden signals per service. Alert on error rate > 1% or p99 latency vs SLO. Include control plane (istiod) pod health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring"
| where match(metric.type, "(istio|kubernetes\.io/istio)")
| stats avg(value) as err_rate by metric.labels.destination_service_name
| where err_rate > 0.01
| sort - err_rate
```

Understanding this SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (Istio canonical metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`, Anthos Service Mesh telemetry. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(metric.type, "(istio|kubernetes\.io/istio)")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by metric.labels.destination_service_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where err_rate > 0.01` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Anthos Service Mesh Health** — Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Service mesh graph (external tool) plus Table (service, error rate), Line chart (p50/p99 latency).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring"
| where match(metric.type, "(istio|kubernetes\.io/istio)")
| stats avg(value) as err_rate by metric.labels.destination_service_name
| where err_rate > 0.01
| sort - err_rate
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Service mesh graph (external tool) plus Table (service, error rate), Line chart (p50/p99 latency).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
