---
id: "7.1.25"
title: "MySQL / MariaDB InnoDB Buffer Pool Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.25 · MySQL / MariaDB InnoDB Buffer Pool Hit Ratio

## Description

Buffer pool effectiveness; low hit ratio means excessive disk I/O and degraded query performance.

## Value

Buffer pool effectiveness; low hit ratio means excessive disk I/O and degraded query performance.

## Implementation

Poll `SHOW GLOBAL STATUS` via DB Connect every 15 minutes. Extract `Innodb_buffer_pool_read_requests` and `Innodb_buffer_pool_reads`. Compute hit ratio = (1 - reads/requests) * 100. Alert when hit ratio drops below 99% for sustained periods. Correlate with memory allocation and workload changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk DB Connect or custom scripted input.
• Ensure the following data sources are available: `SHOW GLOBAL STATUS` (Innodb_buffer_pool_read_requests, Innodb_buffer_pool_reads).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `SHOW GLOBAL STATUS` via DB Connect every 15 minutes. Extract `Innodb_buffer_pool_read_requests` and `Innodb_buffer_pool_reads`. Compute hit ratio = (1 - reads/requests) * 100. Alert when hit ratio drops below 99% for sustained periods. Correlate with memory allocation and workload changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)), 2)
| where hit_ratio < 99
| timechart span=15m avg(hit_ratio) as buffer_pool_hit_ratio by host
```

Understanding this SPL

**MySQL / MariaDB InnoDB Buffer Pool Hit Ratio** — Buffer pool effectiveness; low hit ratio means excessive disk I/O and degraded query performance.

Documented **Data sources**: `SHOW GLOBAL STATUS` (Innodb_buffer_pool_read_requests, Innodb_buffer_pool_reads). **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:mysql_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:mysql_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 99` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest span=15m | sort - count
```

Understanding this CIM / accelerated SPL

**MySQL / MariaDB InnoDB Buffer Pool Hit Ratio** — Buffer pool effectiveness; low hit ratio means excessive disk I/O and degraded query performance.

Documented **Data sources**: `SHOW GLOBAL STATUS` (Innodb_buffer_pool_read_requests, Innodb_buffer_pool_reads). **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (buffer pool hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).

## SPL

```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)), 2)
| where hit_ratio < 99
| timechart span=15m avg(hit_ratio) as buffer_pool_hit_ratio by host
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest span=15m | sort - count
```

## Visualization

Gauge (buffer pool hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
