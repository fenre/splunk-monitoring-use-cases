<!-- AUTO-GENERATED from UC-5.1.24.json — DO NOT EDIT -->

---
id: "5.1.24"
title: "Network Device Configuration Backup Freshness"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.24 · Network Device Configuration Backup Freshness

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance

*We help you know early when something looks wrong with network device configuration backup freshness so the team can act before it grows into a bigger outage.*

---

## Description

Last backup age tracking; stale backups risk config loss during failures.

## Value

Operations teams monitor network device configuration backup freshness, identifying stale backups that risk data loss during device failure or RMA replacement.

## Implementation

Ingest backup job output from Oxidized, RANCID, or NCM. Parse success/failure and timestamp. Create lookup or index with device→last_backup mapping. Alert when last successful backup exceeds 24 hours. Schedule backup jobs daily; verify Splunk receives logs via scripted input or syslog.

## Detailed Implementation

### Prerequisites
* Configuration backup freshness data. Data from network management tools (RANCID, Oxidized, Cisco DNA Center, SolarWinds NCM) or custom scripted inputs. Data in `index=network` or `index=cmdb`.
* Configuration backup freshness: tracks when the last known-good backup was taken for each device. Stale backups mean that in case of device failure, the restored configuration may not match current production state.

### Step 1 — - Configure data collection
```
# Scripted input to check backup timestamps
# inputs.conf
[script:///opt/splunk/etc/apps/network_mon/bin/backup_freshness.sh]
interval = 86400
sourcetype = network:backup:freshness
index = network

# backup_freshness.sh
#!/bin/bash
BACKUP_DIR="/var/backups/network"
for f in "$BACKUP_DIR"/*.cfg; do
    device=$(basename "$f" .cfg)
    mod_epoch=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null)
    echo "device=$device backup_file=$f last_backup_epoch=$mod_epoch"
done
```
Verify:
```spl
index=network sourcetype="network:backup:freshness" earliest=-2d
| stats count by device
```

### Step 2 — - Create the search and alert

**Primary search -- Backup freshness monitoring:**
```spl
index=network sourcetype="network:backup:freshness" earliest=-2d
| eval device=coalesce(device, hostname, host)
| eval last_backup=tonumber(last_backup_epoch)
| eval days_since=round((now() - last_backup)/86400, 1)
| eval last_backup_time=strftime(last_backup, "%Y-%m-%d %H:%M:%S")
| lookup network_devices.csv hostname AS device OUTPUT device_type, site, criticality
| eval severity=case(
    days_since > 30, "CRITICAL -- backup older than 30 days",
    days_since > 14, "WARNING -- backup older than 14 days",
    days_since > 7, "INFO -- backup older than 7 days",
    1==1, "OK")
| where severity != "OK"
| table device, device_type, site, criticality, last_backup_time, days_since, severity
| sort severity, -days_since
```

### Step 3 — - Validate
(a) Verify backup tool (RANCID/Oxidized) is running: check process/cron.
(b) Attempt manual backup of a stale device: `copy running-config tftp://...`.
(c) Verify backed-up config matches running-config.

### Step 4 — - Operationalize
Dashboard ("Network -- Backup Freshness"):
* Row 1 -- Single-value: "Stale backups (>14d)", "Fresh backups (<7d)", "Never backed up".
* Row 2 -- Backup freshness table sorted by staleness.

Alert: Warning (critical device backup >14 days stale): take immediate backup.

### Step 5 — - Troubleshooting

* **Backup tool failing** -- Check RANCID/Oxidized logs. Common causes: SSH credential rotation, device unreachable, disk space full.

* **New device not in backup schedule** -- Add to backup tool configuration. Ensure SSH/SNMP credentials are provisioned.

* **Running-config differs from backup** -- Device was changed without triggering a backup. Enable RANCID/Oxidized to poll more frequently or trigger backup on config change (EEM script).

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

## Known False Positives

Backup jobs can slip during holidays, RADIUS lockouts to the repo, or when a device is in RMA—compare to the backup product job history.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
