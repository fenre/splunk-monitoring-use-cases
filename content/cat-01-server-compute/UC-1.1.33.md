---
id: "1.1.33"
title: "Inode Exhaustion Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.33 · Inode Exhaustion Detection

## Description

Inode exhaustion causes file creation failures even when disk space remains available, stopping applications.

## Value

Inode exhaustion causes file creation failures even when disk space remains available, stopping applications.

## Implementation

Use Splunk_TA_nix df input which includes inode usage percentages. Create alerts for filesystems exceeding 85% inode usage. Add search to identify which directories consuming excessive inodes to guide cleanup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=df`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix df input which includes inode usage percentages. Create alerts for filesystems exceeding 85% inode usage. Add search to identify which directories consuming excessive inodes to guide cleanup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=df host=*
| stats latest(inode_usage) as inode_pct by host, mount_point
| where inode_pct > 85
```

Understanding this SPL

**Inode Exhaustion Detection** — Inode exhaustion causes file creation failures even when disk space remains available, stopping applications.

Documented **Data sources**: `sourcetype=df`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: df. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=df. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, mount_point** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where inode_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

Understanding this CIM / accelerated SPL

**Inode Exhaustion Detection** — Inode exhaustion causes file creation failures even when disk space remains available, stopping applications.

Documented **Data sources**: `sourcetype=df`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where disk_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Gauge

## SPL

```spl
index=os sourcetype=df host=*
| stats latest(inode_usage) as inode_pct by host, mount_point
| where inode_pct > 85
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

## Visualization

Table, Gauge

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
