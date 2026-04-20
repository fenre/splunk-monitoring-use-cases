---
id: "7.1.26"
title: "MySQL Binary Log Space Usage"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.26 · MySQL Binary Log Space Usage

## Description

Binlog accumulation on disk can exhaust disk space and impact replication. Monitoring enables proactive purging or archival.

## Value

Binlog accumulation on disk can exhaust disk space and impact replication. Monitoring enables proactive purging or archival.

## Implementation

Poll `SHOW BINARY LOGS` via DB Connect daily or every 6 hours. Sum `File_size` across all binlogs. Optionally measure binlog directory on disk. Alert when total binlog size exceeds threshold (e.g., >50 GB). Track binlog purge lag (oldest binlog age). Correlate with replication lag and `expire_logs_days`/`binlog_expire_logs_seconds` settings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk DB Connect or custom scripted input.
• Ensure the following data sources are available: `SHOW BINARY LOGS`, filesystem binlog directory size.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `SHOW BINARY LOGS` via DB Connect daily or every 6 hours. Sum `File_size` across all binlogs. Optionally measure binlog directory on disk. Alert when total binlog size exceeds threshold (e.g., >50 GB). Track binlog purge lag (oldest binlog age). Correlate with replication lag and `expire_logs_days`/`binlog_expire_logs_seconds` settings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:mysql_binlogs"
| eval size_gb=round(File_size/1073741824, 2)
| stats sum(File_size) as total_bytes by host
| eval total_gb=round(total_bytes/1073741824, 2)
| where total_gb > 50
| table host, total_gb, binlog_count
```

Understanding this SPL

**MySQL Binary Log Space Usage** — Binlog accumulation on disk can exhaust disk space and impact replication. Monitoring enables proactive purging or archival.

Documented **Data sources**: `SHOW BINARY LOGS`, filesystem binlog directory size. **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:mysql_binlogs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:mysql_binlogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where total_gb > 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MySQL Binary Log Space Usage**): table host, total_gb, binlog_count

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest | sort - count
```

Understanding this CIM / accelerated SPL

**MySQL Binary Log Space Usage** — Binlog accumulation on disk can exhaust disk space and impact replication. Monitoring enables proactive purging or archival.

Documented **Data sources**: `SHOW BINARY LOGS`, filesystem binlog directory size. **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (binlog total size over time), Single value (current binlog size GB), Table (host, size, count).

## SPL

```spl
index=database sourcetype="dbconnect:mysql_binlogs"
| eval size_gb=round(File_size/1073741824, 2)
| stats sum(File_size) as total_bytes by host
| eval total_gb=round(total_bytes/1073741824, 2)
| where total_gb > 50
| table host, total_gb, binlog_count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest | sort - count
```

## Visualization

Line chart (binlog total size over time), Single value (current binlog size GB), Table (host, size, count).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
