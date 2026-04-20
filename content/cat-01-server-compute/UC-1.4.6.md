---
id: "1.4.6"
title: "Memory ECC Error Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.6 · Memory ECC Error Trending

## Description

Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.

## Value

Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.

## Implementation

Create scripted input: `edac-util -s` or parse `/sys/devices/system/edac/mc/mc*/ce_count`. Run hourly. Alert when correctable errors increase by >10/week. Track per-DIMM slot for targeted replacement.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`edac-util`, IPMI SEL).
• Ensure the following data sources are available: `edac-util`, `/sys/devices/system/edac/mc/`, IPMI SEL.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `edac-util -s` or parse `/sys/devices/system/edac/mc/mc*/ce_count`. Run hourly. Alert when correctable errors increase by >10/week. Track per-DIMM slot for targeted replacement.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=ecc_errors
| timechart span=1d sum(correctable_errors) as ecc_errors by host
| where ecc_errors > 0
| streamstats window=7 sum(ecc_errors) as weekly_errors by host
| where weekly_errors > 10
```

Understanding this SPL

**Memory ECC Error Trending** — Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.

Documented **Data sources**: `edac-util`, `/sys/devices/system/edac/mc/`, IPMI SEL. **App/TA** (typical add-on context): Custom scripted input (`edac-util`, IPMI SEL). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: ecc_errors. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=ecc_errors. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where ecc_errors > 0` — typically the threshold or rule expression for this monitoring goal.
• `streamstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where weekly_errors > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors over time by host), Table (host, DIMM, error count), Trend chart.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ecc_errors
| timechart span=1d sum(correctable_errors) as ecc_errors by host
| where ecc_errors > 0
| streamstats window=7 sum(ecc_errors) as weekly_errors by host
| where weekly_errors > 10
```

## Visualization

Line chart (errors over time by host), Table (host, DIMM, error count), Trend chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
