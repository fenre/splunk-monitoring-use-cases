---
id: "7.1.16"
title: "Open Cursor Leak Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.16 · Open Cursor Leak Detection

## Description

Open cursors that are never closed accumulate in the database session context and eventually exhaust the cursor limit (Oracle ORA-01000, SQL Server max open cursors), causing application errors and forcing emergency restarts. Nagios detects this via threshold checks on V$OPEN_CURSOR; Splunk enables trending, per-session attribution, and correlation with application deployments.

## Value

Open cursors that are never closed accumulate in the database session context and eventually exhaust the cursor limit (Oracle ORA-01000, SQL Server max open cursors), causing application errors and forcing emergency restarts. Nagios detects this via threshold checks on V$OPEN_CURSOR; Splunk enables trending, per-session attribution, and correlation with application deployments.

## Implementation

Use Splunk DB Connect to poll `V$OPEN_CURSOR` every 5 minutes. Join with `V$SESSION` to identify which application user or service is leaking cursors. Alert when any single session exceeds 400 open cursors (WARNING) or 800 (CRITICAL). Correlate spikes with deployment events from CI/CD logs to pinpoint root cause. For SQL Server, poll `sys.dm_exec_cursors` grouped by `login_name`. Set `OPEN_CURSORS` init parameter baseline in a lookup for dynamic threshold comparison.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `splunk-db-connect` or `Splunk_TA_oracle`.
• Ensure the following data sources are available: Oracle `V$OPEN_CURSOR`, `V$SESSION`; SQL Server `sys.dm_exec_cursors`; PostgreSQL `pg_cursors`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk DB Connect to poll `V$OPEN_CURSOR` every 5 minutes. Join with `V$SESSION` to identify which application user or service is leaking cursors. Alert when any single session exceeds 400 open cursors (WARNING) or 800 (CRITICAL). Correlate spikes with deployment events from CI/CD logs to pinpoint root cause. For SQL Server, poll `sys.dm_exec_cursors` grouped by `login_name`. Set `OPEN_CURSORS` init parameter baseline in a lookup for dynamic threshold comparison.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| dbxquery connection="oracle_prod" query="SELECT s.username, s.program, COUNT(*) AS open_cursors FROM v\$open_cursor oc JOIN v\$session s ON oc.sid=s.sid GROUP BY s.username, s.program ORDER BY open_cursors DESC"
| where open_cursors > 200
| eval alert=if(open_cursors > 800, "CRITICAL", if(open_cursors > 400, "WARNING", "OK"))
| table username, program, open_cursors, alert
```

Understanding this SPL

**Open Cursor Leak Detection** — Open cursors that are never closed accumulate in the database session context and eventually exhaust the cursor limit (Oracle ORA-01000, SQL Server max open cursors), causing application errors and forcing emergency restarts. Nagios detects this via threshold checks on V$OPEN_CURSOR; Splunk enables trending, per-session attribution, and correlation with application deployments.

Documented **Data sources**: Oracle `V$OPEN_CURSOR`, `V$SESSION`; SQL Server `sys.dm_exec_cursors`; PostgreSQL `pg_cursors`. **App/TA** (typical add-on context): `splunk-db-connect` or `Splunk_TA_oracle`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Pipeline stage (see **Open Cursor Leak Detection**): dbxquery connection="oracle_prod" query="SELECT s.username, s.program, COUNT(*) AS open_cursors FROM v\$open_cursor oc JOIN v\$session s …
• Filters the current rows with `where open_cursors > 200` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **alert** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Open Cursor Leak Detection**): table username, program, open_cursors, alert


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (total open cursors over time by application), Table (top sessions by cursor count), Single value (current max), Bar chart (cursors by application/service).

## SPL

```spl
| dbxquery connection="oracle_prod" query="SELECT s.username, s.program, COUNT(*) AS open_cursors FROM v\$open_cursor oc JOIN v\$session s ON oc.sid=s.sid GROUP BY s.username, s.program ORDER BY open_cursors DESC"
| where open_cursors > 200
| eval alert=if(open_cursors > 800, "CRITICAL", if(open_cursors > 400, "WARNING", "OK"))
| table username, program, open_cursors, alert
```

## Visualization

Line chart (total open cursors over time by application), Table (top sessions by cursor count), Single value (current max), Bar chart (cursors by application/service).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
