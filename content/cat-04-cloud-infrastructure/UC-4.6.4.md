<!-- AUTO-GENERATED from UC-4.6.4.json — DO NOT EDIT -->

---
id: "4.6.4"
title: "S3/Blob Storage Growth Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.6.4 · S3/Blob Storage Growth Trending

## Description

Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication. Supports budgeting and lifecycle policy decisions before bills spike.

## Value

Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication. Supports budgeting and lifecycle policy decisions before bills spike.

## Implementation

Ingest daily CloudWatch BucketSizeBytes per bucket or storage account metrics for Azure/Blob. Use span=1mon aligned to calendar months for FinOps reporting. Convert bytes to TB for readability. Optionally exclude archive buckets matched to a lookup. Alert on month-over-month growth above a percentage threshold. Use predict to forecast 3 months ahead for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for AWS (S3 storage metrics), Azure Monitor metrics.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:cloudwatch` (BucketSizeBytes metric); `sourcetype=azure:monitor:metrics` for storage accounts.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest daily CloudWatch BucketSizeBytes per bucket or storage account metrics for Azure/Blob. Use span=1mon aligned to calendar months for FinOps reporting. Convert bytes to TB for readability. Optionally exclude archive buckets matched to a lookup. Alert on month-over-month growth above a percentage threshold. Use predict to forecast 3 months ahead for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/S3" MetricName="BucketSizeBytes"
| bin _time span=1mon
| stats latest(Average) as bytes by _time, BucketName
| eval tb=round(bytes/1099511627776, 2)
| timechart span=1mon sum(tb) as total_tb
| predict total_tb as predicted algorithm=LLP future_timespan=3
```

Understanding this SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication. Supports budgeting and lifecycle policy decisions before bills spike.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudwatch` (BucketSizeBytes metric); `sourcetype=azure:monitor:metrics` for storage accounts. **App/TA** (typical add-on context): Splunk Add-on for AWS (S3 storage metrics), Azure Monitor metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, BucketName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **tb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1mon** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **S3/Blob Storage Growth Trending**): predict total_tb as predicted algorithm=LLP future_timespan=3


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model `Performance.Storage` — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Storage node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Storage node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Storage node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**S3/Blob Storage Growth Trending** — Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Storage node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (total TB monthly with 3-month forecast), bar chart (top buckets by size), table (month-over-month growth %).

## SPL

```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/S3" MetricName="BucketSizeBytes"
| bin _time span=1mon
| stats latest(Average) as bytes by _time, BucketName
| eval tb=round(bytes/1099511627776, 2)
| timechart span=1mon sum(tb) as total_tb
| predict total_tb as predicted algorithm=LLP future_timespan=3
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

## Visualization

Line chart (total TB monthly with 3-month forecast), bar chart (top buckets by size), table (month-over-month growth %).

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
