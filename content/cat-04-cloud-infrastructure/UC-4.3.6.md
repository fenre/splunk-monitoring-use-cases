<!-- AUTO-GENERATED from UC-4.3.6.json — DO NOT EDIT -->

---
id: "4.3.6"
title: "GCE Instance Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.6 · GCE Instance Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Performance

*Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.*

---

## Description

Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

## Value

Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

## Implementation

Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
- Ensure the following data sources are available: Cloud Monitoring metrics via API.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```

#### Understanding this SPL

**GCE Instance Monitoring** — Compute Engine VM native OS monitoring toolsing for capacity planning and baseline trending without guest-level agents.

Documented **Data sources**: Cloud Monitoring metrics via API. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `timechart` plots the metric over time using **span=1h** buckets with a separate series **by resource.labels.instance_id** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart, Heatmap, Gauge.


## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart, Heatmap, Gauge.

## Known False Positives

Short spikes at deploy time, autoscale thrash, or a noisy neighbor on shared hosts can look bad for a few minutes. We require the condition to last across several intervals or clear on its own before we wake someone.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
