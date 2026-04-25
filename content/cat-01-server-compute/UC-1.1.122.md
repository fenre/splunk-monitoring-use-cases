<!-- AUTO-GENERATED from UC-1.1.122.json — DO NOT EDIT -->

---
id: "1.1.122"
title: "Systemd Unit State Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.122 · Systemd Unit State Monitoring

## Description

Track failed/inactive systemd services, auto-restart counts, and service startup time to prevent cascading failures and identify misconfigured or unhealthy units.

## Value

Track failed/inactive systemd services, auto-restart counts, and service startup time to prevent cascading failures and identify misconfigured or unhealthy units.

## Implementation

Create a scripted input that runs `systemctl list-units --all --no-pager --plain` and `systemctl show --property=ActiveState,SubState,NRestarts` for critical units. Parse ActiveState, SubState, and NRestarts. Run every 60 seconds. For startup time, use `systemd-analyze` output. Alert on any failed units; alert when NRestarts exceeds 5 in 1 hour for critical services.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `systemctl list-units` output, systemd journal.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `systemctl list-units --all --no-pager --plain` and `systemctl show --property=ActiveState,SubState,NRestarts` for critical units. Parse ActiveState, SubState, and NRestarts. Run every 60 seconds. For startup time, use `systemd-analyze` output. Alert on any failed units; alert when NRestarts exceeds 5 in 1 hour for critical services.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=systemd_units host=* NRestarts>0
| stats sum(NRestarts) as total_restarts by host, Unit
| where total_restarts > 5
| sort -total_restarts
```

Understanding this SPL

**Systemd Unit State Monitoring** — Track failed/inactive systemd services, auto-restart counts, and service startup time to prevent cascading failures and identify misconfigured or unhealthy units.

Documented **Data sources**: `systemctl list-units` output, systemd journal. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: systemd_units. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=systemd_units. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, Unit** so each row reflects one combination of those dimensions.
• Filters the current rows with `where total_restarts > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed/inactive units by host), Single value (count of failed units), Timechart of restart counts.

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
index=os sourcetype=systemd_units host=* NRestarts>0
| stats sum(NRestarts) as total_restarts by host, Unit
| where total_restarts > 5
| sort -total_restarts
```

## Visualization

Table (failed/inactive units by host), Single value (count of failed units), Timechart of restart counts.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
