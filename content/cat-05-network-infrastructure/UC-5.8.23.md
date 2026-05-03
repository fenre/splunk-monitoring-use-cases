<!-- AUTO-GENERATED from UC-5.8.23.json — DO NOT EDIT -->

---
id: "5.8.23"
title: "Dashboard Configuration and Export Backup (Meraki)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.8.23 · Dashboard Configuration and Export Backup (Meraki)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you back up and track Meraki dashboard exports, so a bad change does not erase a good layout when you need it most.*

---

## Description

Tracks dashboard configuration backups to enable disaster recovery and configuration review.

## Value

Network operations teams maintain indexed Meraki configuration backups in Splunk for disaster recovery, audit compliance, and configuration drift detection across all networks and configuration sections.

## Implementation

Periodically backup organization configurations. Track backup history.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard configuration export capability. The Meraki API allows exporting network and organization configurations programmatically via: `GET /networks/{networkId}` (network settings), `GET /networks/{networkId}/devices` (device configs), `GET /organizations/{orgId}` (org settings).
- A scheduled script or TA input exports Meraki configurations and indexes them in Splunk. Data in `index=meraki_config` (or `index=meraki`) with `sourcetype=meraki:config:backup`. Key fields: `networkId`, `networkName`, `config_hash`, `config_section` (ssid, firewall, vlan, vpn), `backup_time`.

### Step 1 — Configure data collection
Verify config backup data:
```spl
index=meraki_config sourcetype="meraki:config:backup" earliest=-7d
| stats count latest(_time) as last_backup by networkName, config_section
| eval hours_since_backup=round((now() - last_backup)/3600, 1)
| sort -hours_since_backup
```

### Step 2 — Create the search and alert

**Primary search — Configuration backup status:**
```spl
index=meraki_config sourcetype="meraki:config:backup" earliest=-30d
| stats latest(_time) as last_backup count as backup_count dc(config_hash) as unique_configs by networkName, config_section
| eval hours_since=round((now() - last_backup)/3600, 1)
| eval days_since=round(hours_since/24, 1)
| eval backup_status=case(hours_since > 168, "OVERDUE_WEEK", hours_since > 48, "OVERDUE", 1==1, "CURRENT")
| eval config_changes=unique_configs - 1
| where backup_status!="CURRENT" OR config_changes > 5
| sort backup_status, -config_changes
```

#### Understanding this SPL: Meraki configs live in the cloud, but having a Splunk-indexed backup provides: (1) audit trail of all config changes over time, (2) disaster recovery — if the Meraki org is compromised or accidentally modified, you have a known-good baseline, (3) compliance evidence. The `config_hash` change count reveals configuration drift frequency.

**Configuration drift detection:**
```spl
index=meraki_config sourcetype="meraki:config:backup" earliest=-7d
| sort networkName, config_section, _time
| streamstats current=t window=2 earliest(config_hash) as prev_hash by networkName, config_section
| where config_hash != prev_hash AND isnotnull(prev_hash)
| table _time, networkName, config_section, prev_hash, config_hash
| sort -_time
```

### Step 3 — Validate
(a) Trigger a config backup and verify it appears in Splunk with the correct network and section.
(b) Make a config change in Meraki Dashboard and verify the next backup shows a different config_hash.
(c) Verify backup coverage: all production networks should have recent backups.

### Step 4 — Operationalize
Dashboard ("Meraki Config Backup"):
- Row 1 — Single-value tiles: "Networks backed up", "Overdue backups", "Config changes (7d)", "Last backup run".
- Row 2 — Backup status table: network, section, last backup, days since, status.
- Row 3 — Configuration change timeline.

Alerting:
- Warning (backup overdue > 7 days): backup system may have failed.
- Info (config hash changed): configuration modified since last backup.

### Step 5 — Troubleshooting

- **Backup script fails** — Check API key permissions (read access to networks), API rate limits, and network connectivity to the Meraki cloud API.

- **Config hash always changes** — Some Meraki config elements include timestamps or dynamic values. Strip volatile fields before hashing for stable drift detection.

- **Missing networks in backups** — The backup script may only process networks explicitly listed. Use the organization networks API (`GET /organizations/{orgId}/networks`) to discover all networks dynamically.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" backup_timestamp=*
| stats latest(backup_timestamp) as last_backup, count as backup_count by organization
| eval backup_age_days=round((now()-strptime(backup_timestamp, "%Y-%m-%d"))/86400, 0)
| where backup_age_days > 7
```

## Visualization

Last backup timestamp by org; backup recency gauge; backup history timeline.

## Known False Positives

Exports before big dashboard edits look like noise; only alert when backup is missing for longer than the scheduled export interval.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
