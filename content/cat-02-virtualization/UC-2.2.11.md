---
id: "2.2.11"
title: "Storage Spaces Direct (S2D) Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.2.11 · Storage Spaces Direct (S2D) Health

## Description

Storage Spaces Direct pools local storage across cluster nodes into a shared storage fabric. Disk failures, network partitions, or capacity exhaustion degrade the storage pool, risking data loss. S2D self-heals by rebuilding data on remaining disks, consuming significant I/O during repair.

## Value

Storage Spaces Direct pools local storage across cluster nodes into a shared storage fabric. Disk failures, network partitions, or capacity exhaustion degrade the storage pool, risking data loss. S2D self-heals by rebuilding data on remaining disks, consuming significant I/O during repair.

## Implementation

Create scripted inputs: `Get-StoragePool | Select FriendlyName, HealthStatus, OperationalStatus, Size, AllocatedSize` and `Get-PhysicalDisk | Select FriendlyName, HealthStatus, OperationalStatus, MediaType, Size, CanPool`. Run every 5 minutes. Alert on any non-Healthy status or capacity >80%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V), custom scripted input.
• Ensure the following data sources are available: PowerShell scripted input (`Get-StorageSubsystem`, `Get-PhysicalDisk`, `Get-StoragePool`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted inputs: `Get-StoragePool | Select FriendlyName, HealthStatus, OperationalStatus, Size, AllocatedSize` and `Get-PhysicalDisk | Select FriendlyName, HealthStatus, OperationalStatus, MediaType, Size, CanPool`. Run every 5 minutes. Alert on any non-Healthy status or capacity >80%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hyperv sourcetype="s2d_health"
| stats latest(pool_health) as health, latest(pool_operational_status) as op_status, latest(capacity_pct) as capacity by pool_name, host
| where health!="Healthy" OR capacity > 80
| sort -capacity
| table pool_name, host, health, op_status, capacity
```

Understanding this SPL

**Storage Spaces Direct (S2D) Health** — Storage Spaces Direct pools local storage across cluster nodes into a shared storage fabric. Disk failures, network partitions, or capacity exhaustion degrade the storage pool, risking data loss. S2D self-heals by rebuilding data on remaining disks, consuming significant I/O during repair.

Documented **Data sources**: PowerShell scripted input (`Get-StorageSubsystem`, `Get-PhysicalDisk`, `Get-StoragePool`). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V), custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hyperv; **sourcetype**: s2d_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hyperv, sourcetype="s2d_health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by pool_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where health!="Healthy" OR capacity > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Storage Spaces Direct (S2D) Health**): table pool_name, host, health, op_status, capacity


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (pool health), Table (disk status), Gauge (capacity utilization), Events (repair operations).

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
index=hyperv sourcetype="s2d_health"
| stats latest(pool_health) as health, latest(pool_operational_status) as op_status, latest(capacity_pct) as capacity by pool_name, host
| where health!="Healthy" OR capacity > 80
| sort -capacity
| table pool_name, host, health, op_status, capacity
```

## Visualization

Status grid (pool health), Table (disk status), Gauge (capacity utilization), Events (repair operations).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
