---
id: "7.4.13"
title: "Snowflake Query Spillage (Bytes Spilled to Local/Remote Storage)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.13 · Snowflake Query Spillage (Bytes Spilled to Local/Remote Storage)

## Description

Spillage indicates insufficient warehouse size or poorly written queries (exploding joins). Drives warehouse tier and query tuning decisions.

## Value

Spillage indicates insufficient warehouse size or poorly written queries (exploding joins). Drives warehouse tier and query tuning decisions.

## Implementation

Poll `QUERY_HISTORY` for completed queries. Alert on spill_bytes >1GB. Join with warehouse size for context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Snowflake `QUERY_HISTORY`, `QUERY_ACCELERATION_HISTORY`.
• Ensure the following data sources are available: `BYTES_SPILLED_TO_LOCAL_STORAGE`, `BYTES_SPILLED_TO_REMOTE_STORAGE`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `QUERY_HISTORY` for completed queries. Alert on spill_bytes >1GB. Join with warehouse size for context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval spill_bytes=BYTES_SPILLED_TO_LOCAL_STORAGE+BYTES_SPILLED_TO_REMOTE_STORAGE
| where spill_bytes > 1073741824
| stats sum(spill_bytes) as total_spill, count as qcount by USER_NAME, QUERY_ID
| sort -total_spill
```

Understanding this SPL

**Snowflake Query Spillage (Bytes Spilled to Local/Remote Storage)** — Spillage indicates insufficient warehouse size or poorly written queries (exploding joins). Drives warehouse tier and query tuning decisions.

Documented **Data sources**: `BYTES_SPILLED_TO_LOCAL_STORAGE`, `BYTES_SPILLED_TO_REMOTE_STORAGE`. **App/TA** (typical add-on context): Snowflake `QUERY_HISTORY`, `QUERY_ACCELERATION_HISTORY`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:query_history. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="snowflake:query_history". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **spill_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where spill_bytes > 1073741824` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by USER_NAME, QUERY_ID** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (queries with spill), Bar chart (spill by user), Line chart (daily spill volume).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval spill_bytes=BYTES_SPILLED_TO_LOCAL_STORAGE+BYTES_SPILLED_TO_REMOTE_STORAGE
| where spill_bytes > 1073741824
| stats sum(spill_bytes) as total_spill, count as qcount by USER_NAME, QUERY_ID
| sort -total_spill
```

## Visualization

Table (queries with spill), Bar chart (spill by user), Line chart (daily spill volume).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
