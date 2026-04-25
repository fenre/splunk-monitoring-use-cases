<!-- AUTO-GENERATED from UC-4.3.7.json — DO NOT EDIT -->

---
id: "4.3.7"
title: "BigQuery Audit and Cost"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.7 · BigQuery Audit and Cost

## Description

BigQuery can generate massive costs from poorly optimized queries. Audit and cost tracking prevents bill shock and identifies optimization opportunities.

## Value

BigQuery can generate massive costs from poorly optimized queries. Audit and cost tracking prevents bill shock and identifies optimization opportunities.

## Implementation

Forward BigQuery audit logs via Pub/Sub. Calculate cost from billed bytes ($5/TB). Create dashboard showing cost per user, top expensive queries, and slot utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: BigQuery audit logs via Pub/Sub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward BigQuery audit logs via Pub/Sub. Calculate cost from billed bytes ($5/TB). Create dashboard showing cost per user, top expensive queries, and slot utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="bigquery.googleapis.com" protoPayload.methodName="jobservice.jobcompleted"
| spath output=bytes_billed path=protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes
| spath output=user path=protoPayload.authenticationInfo.principalEmail
| eval cost_usd = round(bytes_billed / 1099511627776 * 5, 4)
| stats sum(cost_usd) as total_cost, count as queries by user
| sort -total_cost
```

Understanding this SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries. Audit and cost tracking prevents bill shock and identifies optimization opportunities.

Documented **Data sources**: BigQuery audit logs via Pub/Sub. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• `eval` defines or adjusts **cost_usd** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by user** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model `Change.All_Changes` — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**BigQuery Audit and Cost** — BigQuery can generate massive costs from poorly optimized queries.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, queries, cost), Bar chart (top costly queries), Trend line (daily cost).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="bigquery.googleapis.com" protoPayload.methodName="jobservice.jobcompleted"
| spath output=bytes_billed path=protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes
| spath output=user path=protoPayload.authenticationInfo.principalEmail
| eval cost_usd = round(bytes_billed / 1099511627776 * 5, 4)
| stats sum(cost_usd) as total_cost, count as queries by user
| sort -total_cost
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (user, queries, cost), Bar chart (top costly queries), Trend line (daily cost).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
