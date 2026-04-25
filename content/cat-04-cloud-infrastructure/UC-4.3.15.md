<!-- AUTO-GENERATED from UC-4.3.15.json — DO NOT EDIT -->

---
id: "4.3.15"
title: "Cloud CDN Cache Hit Ratio and Egress"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.15 · Cloud CDN Cache Hit Ratio and Egress

## Description

Cache hit ratio and egress volume impact latency and cost. Low hit ratio increases origin load and egress charges.

## Value

Cache hit ratio and egress volume impact latency and cost. Low hit ratio increases origin load and egress charges.

## Implementation

Collect CDN metrics. Calculate hit ratio from cache hits and misses. Alert when hit ratio < 70% or egress spike. Optimize cache TTL and key design based on metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring (cdn.googleapis.com/cache/hit_ratio, egress).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect CDN metrics. Calculate hit ratio from cache hits and misses. Alert when hit ratio < 70% or egress spike. Optimize cache TTL and key design based on metrics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cdn.googleapis.com/cache/hit_ratio"
| bin _time span=1h
| stats avg(value) as hit_ratio by _time, resource.labels.origin_name
| where hit_ratio < 0.7
```

Understanding this SPL

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost. Low hit ratio increases origin load and egress charges.

Documented **Data sources**: Cloud Monitoring (cdn.googleapis.com/cache/hit_ratio, egress). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, resource.labels.origin_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where hit_ratio < 0.7` — typically the threshold or rule expression for this monitoring goal.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost.

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

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost.

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

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost.

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

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost.

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

**Cloud CDN Cache Hit Ratio and Egress** — Cache hit ratio and egress volume impact latency and cost.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (hit ratio, egress by origin), Table (origin, hit ratio), Gauge (overall hit ratio).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cdn.googleapis.com/cache/hit_ratio"
| bin _time span=1h
| stats avg(value) as hit_ratio by _time, resource.labels.origin_name
| where hit_ratio < 0.7
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (hit ratio, egress by origin), Table (origin, hit ratio), Gauge (overall hit ratio).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
