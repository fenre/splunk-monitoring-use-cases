<!-- AUTO-GENERATED from UC-4.4.16.json — DO NOT EDIT -->

---
id: "4.4.16"
title: "Cross-Region Replication and Backup Verification"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.16 · Cross-Region Replication and Backup Verification

## Description

Replication lag or failed backup copies leave RPO/RTO at risk. Monitoring ensures DR readiness and supports audit of backup and replication jobs.

## Value

Replication lag or failed backup copies leave RPO/RTO at risk. Monitoring ensures DR readiness and supports audit of backup and replication jobs.

## Implementation

Collect S3 ReplicationTime and ReplicationLatency from CloudWatch. For RDS, use ReplicaLag. For Azure, ingest Backup job state from Monitor or automation runbooks. Alert when replication lag exceeds RPO (e.g. 15 min) or backup job fails.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure Monitor, GCP operations.
• Ensure the following data sources are available: S3 replication metrics, RDS cross-region replica lag, Azure Backup job status, GCP snapshot schedule.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect S3 ReplicationTime and ReplicationLatency from CloudWatch. For RDS, use ReplicaLag. For Azure, ingest Backup job state from Monitor or automation runbooks. Alert when replication lag exceeds RPO (e.g. 15 min) or backup job fails.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:metric" metric_name=ReplicationLatency namespace=AWS/S3
| stats latest(value) as lag_seconds by dimension.BucketName, dimension.DestinationBucket
| where lag_seconds > 900
| table dimension.BucketName dimension.DestinationBucket lag_seconds
```

Understanding this SPL

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk. Monitoring ensures DR readiness and supports audit of backup and replication jobs.

Documented **Data sources**: S3 replication metrics, RDS cross-region replica lag, Azure Backup job status, GCP snapshot schedule. **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure Monitor, GCP operations. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:metric. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dimension.BucketName, dimension.DestinationBucket** so each row reflects one combination of those dimensions.
• Filters the current rows with `where lag_seconds > 900` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cross-Region Replication and Backup Verification**): table dimension.BucketName dimension.DestinationBucket lag_seconds


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk.

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

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk.

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

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk.

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

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk.

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

**Cross-Region Replication and Backup Verification** — Replication lag or failed backup copies leave RPO/RTO at risk.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replication lag by bucket/replica), Table (failed backup jobs), Single value (max lag).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:metric" metric_name=ReplicationLatency namespace=AWS/S3
| stats latest(value) as lag_seconds by dimension.BucketName, dimension.DestinationBucket
| where lag_seconds > 900
| table dimension.BucketName dimension.DestinationBucket lag_seconds
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (replication lag by bucket/replica), Table (failed backup jobs), Single value (max lag).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
