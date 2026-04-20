---
id: "5.1.24"
title: "Network Device Configuration Backup Freshness"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.24 · Network Device Configuration Backup Freshness

## Description

Last backup age tracking; stale backups risk config loss during failures.

## Value

Last backup age tracking; stale backups risk config loss during failures.

## Implementation

Ingest backup job output from Oxidized, RANCID, or NCM. Parse success/failure and timestamp. Create lookup or index with device→last_backup mapping. Alert when last successful backup exceeds 24 hours. Schedule backup jobs daily; verify Splunk receives logs via scripted input or syslog.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Oxidized/RANCID output, SolarWinds NCM equivalent), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: Backup system logs (timestamps of last successful backup per device).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest backup job output from Oxidized, RANCID, or NCM. Parse success/failure and timestamp. Create lookup or index with device→last_backup mapping. Alert when last successful backup exceeds 24 hours. Schedule backup jobs daily; verify Splunk receives logs via scripted input or syslog.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=config_backup OR sourcetype=oxidized OR sourcetype=rancid
| stats latest(_time) as last_backup by host, device_hostname
| eval age_hours=round((now()-last_backup)/3600,1)
| where age_hours > 24 OR isnull(last_backup)
| table device_hostname host last_backup age_hours
```

Understanding this SPL

**Network Device Configuration Backup Freshness** — Last backup age tracking; stale backups risk config loss during failures.

Documented **Data sources**: Backup system logs (timestamps of last successful backup per device). **App/TA** (typical add-on context): Custom (Oxidized/RANCID output, SolarWinds NCM equivalent), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: config_backup, oxidized, rancid. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=config_backup. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, device_hostname** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **age_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where age_hours > 24 OR isnull(last_backup)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Network Device Configuration Backup Freshness**): table device_hostname host last_backup age_hours


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, last backup, age), Single value (devices with stale backup), Gauge (hours since last backup).

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
index=network sourcetype=config_backup OR sourcetype=oxidized OR sourcetype=rancid
| stats latest(_time) as last_backup by host, device_hostname
| eval age_hours=round((now()-last_backup)/3600,1)
| where age_hours > 24 OR isnull(last_backup)
| table device_hostname host last_backup age_hours
```

## Visualization

Table (device, last backup, age), Single value (devices with stale backup), Gauge (hours since last backup).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
