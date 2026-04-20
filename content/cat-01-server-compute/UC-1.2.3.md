---
id: "1.2.3"
title: "Disk Space Monitoring (Windows)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.3 · Disk Space Monitoring (Windows)

## Description

Full disks crash applications, stop logging, and corrupt databases. Windows can become unbootable if the system drive fills.

## Value

Full disks crash applications, stop logging, and corrupt databases. Windows can become unbootable if the system drive fills.

## Implementation

Perfmon input: LogicalDisk, counters = `% Free Space`, `Free Megabytes`. Alert at 85%/90%/95% thresholds. Use `predict` for forecasting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:LogicalDisk`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Perfmon input: LogicalDisk, counters = `% Free Space`, `Free Megabytes`. Alert at 85%/90%/95% thresholds. Use `predict` for forecasting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="% Free Space" instance!="_Total"
| stats latest(Value) as free_pct by host, instance
| eval used_pct = 100 - free_pct
| where used_pct > 85
| sort -used_pct
```

Understanding this SPL

**Disk Space Monitoring (Windows)** — Full disks crash applications, stop logging, and corrupt databases. Windows can become unbootable if the system drive fills.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:LogicalDisk. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:LogicalDisk". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, instance** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

Understanding this CIM / accelerated SPL

**Disk Space Monitoring (Windows)** — Full disks crash applications, stop logging, and corrupt databases. Windows can become unbootable if the system drive fills.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where disk_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table sorted by usage, Gauge per drive, Line chart trend per volume.

## SPL

```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="% Free Space" instance!="_Total"
| stats latest(Value) as free_pct by host, instance
| eval used_pct = 100 - free_pct
| where used_pct > 85
| sort -used_pct
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

## Visualization

Table sorted by usage, Gauge per drive, Line chart trend per volume.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
