<!-- AUTO-GENERATED from UC-2.2.8.json — DO NOT EDIT -->

---
id: "2.2.8"
title: "Checkpoint Age and Sprawl"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.2.8 · Checkpoint Age and Sprawl

## Description

Hyper-V checkpoints (snapshots) accumulate AVHDX differencing disks that grow over time and degrade I/O performance. Old checkpoints complicate backup and recovery, consume unexpected storage, and cause merge storms when finally deleted. Production checkpoints are safer but still grow.

## Value

Hyper-V checkpoints (snapshots) accumulate AVHDX differencing disks that grow over time and degrade I/O performance. Old checkpoints complicate backup and recovery, consume unexpected storage, and cause merge storms when finally deleted. Production checkpoints are safer but still grow.

## Implementation

Create scripted input: `Get-VM | Get-VMCheckpoint | Select VMName, Name, CreationTime, CheckpointType, @{N='SizeGB';E={[math]::Round((Get-VHD $_.HardDrives.Path).FileSize/1GB,2)}}`. Run daily. Alert on checkpoints >3 days old. Distinguish production checkpoints (application-consistent) from standard (crash-consistent).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V), custom scripted input.
• Ensure the following data sources are available: PowerShell scripted input (`Get-VMCheckpoint`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `Get-VM | Get-VMCheckpoint | Select VMName, Name, CreationTime, CheckpointType, @{N='SizeGB';E={[math]::Round((Get-VHD $_.HardDrives.Path).FileSize/1GB,2)}}`. Run daily. Alert on checkpoints >3 days old. Distinguish production checkpoints (application-consistent) from standard (crash-consistent).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hyperv sourcetype="hyperv_checkpoints"
| eval age_days=round((now() - strptime(creation_time, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where age_days > 3
| sort -age_days
| table vm_name, host, checkpoint_name, age_days, size_gb, checkpoint_type
```

Understanding this SPL

**Checkpoint Age and Sprawl** — Hyper-V checkpoints (snapshots) accumulate AVHDX differencing disks that grow over time and degrade I/O performance. Old checkpoints complicate backup and recovery, consume unexpected storage, and cause merge storms when finally deleted. Production checkpoints are safer but still grow.

Documented **Data sources**: PowerShell scripted input (`Get-VMCheckpoint`). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V), custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hyperv; **sourcetype**: hyperv_checkpoints. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hyperv, sourcetype="hyperv_checkpoints". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where age_days > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Checkpoint Age and Sprawl**): table vm_name, host, checkpoint_name, age_days, size_gb, checkpoint_type

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, checkpoint, age, size), Bar chart (checkpoints by age bucket), Single value (total checkpoint count).

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
index=hyperv sourcetype="hyperv_checkpoints"
| eval age_days=round((now() - strptime(creation_time, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where age_days > 3
| sort -age_days
| table vm_name, host, checkpoint_name, age_days, size_gb, checkpoint_type
```

## Visualization

Table (VM, checkpoint, age, size), Bar chart (checkpoints by age bucket), Single value (total checkpoint count).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
