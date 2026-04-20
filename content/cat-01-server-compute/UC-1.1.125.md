---
id: "1.1.125"
title: "Linux Journal / Journald Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.125 · Linux Journal / Journald Health

## Description

Journal corruption, excessive disk usage, and rate-limited entries indicate logging problems that can hide critical events and fill disk.

## Value

Journal corruption, excessive disk usage, and rate-limited entries indicate logging problems that can hide critical events and fill disk.

## Implementation

Create a scripted input that runs `journalctl --disk-usage` (parse "Archived and active: X.XG" or similar) and `journalctl --verify 2>&1` (check exit code and output for "corrupt" or "inconsistent"). For suppressed messages, parse `journalctl -u systemd-journald` for "Suppressed" or use `journalctl --output=short-full` rate stats. Run every 300 seconds. Alert on corruption; alert when journal exceeds 4GB or suppressed count is high.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `journalctl --disk-usage`, `journalctl --verify`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `journalctl --disk-usage` (parse "Archived and active: X.XG" or similar) and `journalctl --verify 2>&1` (check exit code and output for "corrupt" or "inconsistent"). For suppressed messages, parse `journalctl -u systemd-journald` for "Suppressed" or use `journalctl --output=short-full` rate stats. Run every 300 seconds. Alert on corruption; alert when journal exceeds 4GB or suppressed count is high.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=journal_health host=*
| timechart span=1h avg(disk_usage_mb) as journal_mb by host
```

Understanding this SPL

**Linux Journal / Journald Health** — Journal corruption, excessive disk usage, and rate-limited entries indicate logging problems that can hide critical events and fill disk.

Documented **Data sources**: `journalctl --disk-usage`, `journalctl --verify`. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: journal_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=journal_health. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, size, corruption status), Line chart (journal size over time), Single value (corruption count).

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
index=os sourcetype=journal_health host=*
| timechart span=1h avg(disk_usage_mb) as journal_mb by host
```

## Visualization

Table (host, size, corruption status), Line chart (journal size over time), Single value (corruption count).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
