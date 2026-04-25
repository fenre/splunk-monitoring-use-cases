<!-- AUTO-GENERATED from UC-4.3.40.json — DO NOT EDIT -->

---
id: "4.3.40"
title: "GCP Cloud Run Task Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.40 · GCP Cloud Run Task Health

## Description

Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

## Value

Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

## Implementation

Export Cloud Run request, latency, and instance metrics via GCP monitoring sink to Pub/Sub and ingest with `Splunk_TA_google-cloudplatform`, or forward OpenTelemetry from a sidecar/collector if you run hybrid instrumentation. Ensure `service_name` and `revision_name` are extracted. Alert on elevated `server_request_latencies` and `5xx` ratio versus SLO.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform` (Pub/Sub logging/metrics) or OTel export from Cloud Ops.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` or `sourcetype=gcp:monitoring:timeseries`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export Cloud Run request, latency, and instance metrics via GCP monitoring sink to Pub/Sub and ingest with `Splunk_TA_google-cloudplatform`, or forward OpenTelemetry from a sidecar/collector if you run hybrid instrumentation. Ensure `service_name` and `revision_name` are extracted. Alert on elevated `server_request_latencies` and `5xx` ratio versus SLO.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="gcp:monitoring:timeseries"
| where like(metric.type, "run.googleapis.com%")
| stats avg(value) as val_avg, max(value) as val_max by metric.type
| where match(metric.type, "(?i)request|latency|instance|container")
| sort -val_max
```

Understanding this SPL

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` or `sourcetype=gcp:monitoring:timeseries`. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform` (Pub/Sub logging/metrics) or OTel export from Cloud Ops. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: gcp:monitoring:timeseries. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="gcp:monitoring:timeseries". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(metric.type, "run.googleapis.com%")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by metric.type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where match(metric.type, "(?i)request|latency|instance|container")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

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

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

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

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

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

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

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

**GCP Cloud Run Task Health** — Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (p95 latency, request rate), Table (service, revision, error rate), Single value (active instances).

## SPL

```spl
index=cloud sourcetype="gcp:monitoring:timeseries"
| where like(metric.type, "run.googleapis.com%")
| stats avg(value) as val_avg, max(value) as val_max by metric.type
| where match(metric.type, "(?i)request|latency|instance|container")
| sort -val_max
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Time chart (p95 latency, request rate), Table (service, revision, error rate), Single value (active instances).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
