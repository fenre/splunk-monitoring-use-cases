<!-- AUTO-GENERATED from UC-6.3.10.json — DO NOT EDIT -->

---
id: "6.3.10"
title: "Backup Data Growth Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.10 · Backup Data Growth Rate

## Description

Backup repository consumption trending enables capacity planning and prevents surprise exhaustion. Proactive forecasting supports budget and procurement decisions.

## Value

Backup repository consumption trending enables capacity planning and prevents surprise exhaustion. Proactive forecasting supports budget and procurement decisions.

## Implementation

Poll backup repository capacity via vendor API (Veeam, Commvault, etc.) or scripted input (filesystem df, REST endpoint). Collect used_bytes and capacity_bytes per repository daily. Index to Splunk. Use `predict` or `trendline` for 30/60/90-day forecasts. Alert when projected full date is within 90 days. Correlate growth rate with backup job data volume trends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (backup software API/CLI).
• Ensure the following data sources are available: Backup repository size over time.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll backup repository capacity via vendor API (Veeam, Commvault, etc.) or scripted input (filesystem df, REST endpoint). Collect used_bytes and capacity_bytes per repository daily. Index to Splunk. Use `predict` or `trendline` for 30/60/90-day forecasts. Alert when projected full date is within 90 days. Correlate growth rate with backup job data volume trends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:repository" OR sourcetype="backup:repository"
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| timechart span=1d latest(used_bytes) as used, latest(capacity_bytes) as capacity by repository_name
| eval used_pct=round(used/capacity*100, 1)
| predict used as predicted future_timespan=30
```

Understanding this SPL

**Backup Data Growth Rate** — Backup repository consumption trending enables capacity planning and prevents surprise exhaustion. Proactive forecasting supports budget and procurement decisions.

Documented **Data sources**: Backup repository size over time. **App/TA** (typical add-on context): Custom (backup software API/CLI). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:repository, backup:repository. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:repository". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by repository_name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Backup Data Growth Rate**): predict used as predicted future_timespan=30


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Line chart (repository usage % over time with prediction), Table (repositories with growth rate and ETA to full), Single value (days until first repository full).

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
index=backup sourcetype="veeam:repository" OR sourcetype="backup:repository"
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| timechart span=1d latest(used_bytes) as used, latest(capacity_bytes) as capacity by repository_name
| eval used_pct=round(used/capacity*100, 1)
| predict used as predicted future_timespan=30
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (repository usage % over time with prediction), Table (repositories with growth rate and ETA to full), Single value (days until first repository full).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
