<!-- AUTO-GENERATED from UC-5.8.5.json — DO NOT EDIT -->

---
id: "5.8.5"
title: "Network Device Backup Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.5 · Network Device Backup Compliance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We check that switch and router configs are saved on schedule so a broken box can be rebuilt quickly instead of by hand from memory.*

---

## Description

Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.

## Value

Network operations teams track configuration backup compliance across all network devices, identifying overdue backups by policy-defined frequency, detecting never-backed-up devices, and meeting PCI-DSS audit requirements.

## Implementation

Integrate config backup tool (Oxidized/RANCID) logs into Splunk. Track success/failure per device. Alert when a device hasn't been backed up in >7 days.

## Detailed Implementation

### Prerequisites
- Network device configuration backups stored in Splunk or accessible via lookup. Common approaches: (1) RANCID/Oxidized exports forwarded to Splunk, (2) Catalyst Center configuration archive via API, (3) Custom scripts that pull running configs and index them.
- Data in `index=network_config` (or `index=network`) with `sourcetype=device:config`. Key fields: `hostname`, `management_ip`, `config_hash` (MD5/SHA256 of running config), `backup_time`, `config_size`.
- Build `backup_policy.csv` lookup: `hostname,backup_frequency_hours,last_successful_backup,compliance_group` (e.g., `core-sw-01,24,2026-05-01T06:00:00,PCI`). Different device groups may have different backup frequency requirements (PCI: daily, standard: weekly).

### Step 1 — Configure data collection
Verify backup data:
```spl
index=network_config sourcetype="device:config" earliest=-7d
| stats count latest(_time) as last_backup by hostname
| eval hours_since_backup=round((now() - last_backup)/3600, 1)
| sort -hours_since_backup
```

### Step 2 — Create the search and alert

**Primary search — Backup compliance assessment:**
```spl
index=network_config sourcetype="device:config" earliest=-30d
| stats latest(_time) as last_backup count as backup_count by hostname
| eval hours_since_backup=round((now() - last_backup)/3600, 1)
| eval days_since_backup=round(hours_since_backup/24, 1)
| lookup backup_policy.csv hostname OUTPUT backup_frequency_hours compliance_group
| eval required_frequency=if(isnotnull(backup_frequency_hours), backup_frequency_hours, 168)
| eval compliant=if(hours_since_backup <= required_frequency, "YES", "NO")
| eval overdue_factor=round(hours_since_backup/required_frequency, 1)
| where compliant="NO"
| eval severity=case(overdue_factor > 7, "CRITICAL", overdue_factor > 3, "HIGH", 1==1, "WARNING")
| sort severity, -hours_since_backup
```

#### Understanding this SPL: Configuration backup compliance prevents the nightmare scenario: a device fails, and you have no backup to restore. For PCI-DSS, daily backup compliance is auditable. The `overdue_factor` quantifies how far behind the backup is — a device 7× overdue (a weekly device not backed up in 7 weeks) is critical because the config may have changed significantly since the last backup.

**Backup trend analysis:**
```spl
index=network_config sourcetype="device:config" earliest=-30d
| bin _time span=1d
| stats dc(hostname) as devices_backed_up by _time
| eventstats avg(devices_backed_up) as avg_daily
| eval pct_of_avg=round(100*devices_backed_up/avg_daily, 1)
```

**Devices never backed up:**
```spl
| inputlookup master_device_inventory.csv
| search role IN ("router", "switch", "firewall")
| eval serial=serial
| join type=left hostname [search index=network_config sourcetype="device:config" earliest=-90d | stats count latest(_time) as last_backup by hostname]
| where isnull(last_backup)
| table hostname, management_ip, model, site, role
```

### Step 3 — Validate
(a) Compare device backup list against the configuration management tool (RANCID/Oxidized). Verify all managed devices have at least one backup in Splunk.
(b) Restore a backup configuration to a lab device and verify it's complete and valid.
(c) Check compliance groups: verify PCI-scoped devices have daily backups as required.

### Step 4 — Operationalize
Dashboard ("Configuration Backup Compliance"):
- Row 1 — Single-value tiles: "Devices compliant", "Devices overdue", "Never backed up", "Last backup run".
- Row 2 — Non-compliant devices table: hostname, last backup, days overdue, compliance group, severity.
- Row 3 — Backup trend: daily backup count over 30 days.
- Row 4 — Never backed up: devices in inventory but with no backup record.

Alerting:
- Critical (PCI device backup > 48 hours overdue): compliance violation risk.
- High (any device > 7× overdue): significant data loss risk on device failure.
- Warning (backup count drops below 80% of average): backup system may be failing.

### Step 5 — Troubleshooting

- **Backup data not arriving** — Check the backup tool (RANCID/Oxidized) logs. Common issues: SSH credential expiry, device unreachable, or the forwarding to Splunk stopped (check UF/HEC).

- **Config hash changes but no configuration change was made** — Some devices include timestamps or counters in the running config output. Normalize the config (strip timestamps, NTP clock lines) before hashing.

- **Backup runs but Splunk shows old data** — Check if the indexed event is the config content or just a backup metadata record. Some setups only log "backup successful" without the actual config.

## SPL

```spl
index=network sourcetype="oxidized"
| stats latest(status) as backup_status, latest(_time) as last_backup by device
| eval days_since=round((now()-last_backup)/86400,0)
| where backup_status!="success" OR days_since > 7
| sort -days_since
```

## Visualization

Table (device, status, days since backup), Single value (compliance %), Status grid.

## Known False Positives

Backup job overlap, slow SSH to old gear, and locked devices during changes can look like missed backups; compare to the backup tool’s own run log.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
