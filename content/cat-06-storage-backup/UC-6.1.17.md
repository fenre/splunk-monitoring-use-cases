---
id: "6.1.17"
title: "RAID Rebuild Progress and Estimated Completion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.17 · RAID Rebuild Progress and Estimated Completion

## Description

During array rebuilds, progress percentage and ETA help plan maintenance and detect stalled rebuilds. Stalled rebuilds increase risk of data loss if another disk fails.

## Value

During array rebuilds, progress percentage and ETA help plan maintenance and detect stalled rebuilds. Stalled rebuilds increase risk of data loss if another disk fails.

## Implementation

Create scripted input that runs `mdadm --detail /dev/md*` (Linux software RAID) or vendor CLIs (`MegaCli64 -AdpAllInfo -aAll`, `perccli64 /c0 show` for Dell PERC). Parse rebuild/resync state, progress %, speed, and ETA. Run every 5–15 minutes during rebuilds. Index to Splunk. Alert when rebuild is active and progress has not increased in 2+ hours (stalled). Track ETA for maintenance planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (mdadm, MegaCli, perccli).
• Ensure the following data sources are available: mdadm --detail, vendor RAID CLI output (MegaCli, perccli).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input that runs `mdadm --detail /dev/md*` (Linux software RAID) or vendor CLIs (`MegaCli64 -AdpAllInfo -aAll`, `perccli64 /c0 show` for Dell PERC). Parse rebuild/resync state, progress %, speed, and ETA. Run every 5–15 minutes during rebuilds. Index to Splunk. Alert when rebuild is active and progress has not increased in 2+ hours (stalled). Track ETA for maintenance planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="raid:rebuild"
| search state="rebuild" OR state="resync"
| eval progress_pct=if(isnum(progress), progress, tonumber(replace(progress, "%", "")))
| where progress_pct < 100
| table _time, array_name, state, progress_pct, speed_mb_s, eta_hours, spare_disk
| sort -_time
```

Understanding this SPL

**RAID Rebuild Progress and Estimated Completion** — During array rebuilds, progress percentage and ETA help plan maintenance and detect stalled rebuilds. Stalled rebuilds increase risk of data loss if another disk fails.

Documented **Data sources**: mdadm --detail, vendor RAID CLI output (MegaCli, perccli). **App/TA** (typical add-on context): Custom scripted input (mdadm, MegaCli, perccli). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: raid:rebuild. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="raid:rebuild". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **progress_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where progress_pct < 100` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **RAID Rebuild Progress and Estimated Completion**): table _time, array_name, state, progress_pct, speed_mb_s, eta_hours, spare_disk
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (rebuild progress %), Table (arrays in rebuild with ETA), Line chart (progress over time), Single value (hours until rebuild complete).

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
index=storage sourcetype="raid:rebuild"
| search state="rebuild" OR state="resync"
| eval progress_pct=if(isnum(progress), progress, tonumber(replace(progress, "%", "")))
| where progress_pct < 100
| table _time, array_name, state, progress_pct, speed_mb_s, eta_hours, spare_disk
| sort -_time
```

## Visualization

Gauge (rebuild progress %), Table (arrays in rebuild with ETA), Line chart (progress over time), Single value (hours until rebuild complete).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
