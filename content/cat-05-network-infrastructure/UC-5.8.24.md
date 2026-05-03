<!-- AUTO-GENERATED from UC-5.8.24.json — DO NOT EDIT -->

---
id: "5.8.24"
title: "Network Device Configuration Backup and Drift"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.24 · Network Device Configuration Backup and Drift

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We help you prove configs are stored and can be compared over time, which is a lifesaver when a device fails or someone mis-clicks in the middle of the night.*

---

## Description

Missing or stale configuration backups complicate recovery after failure or bad change. Detecting backup failure or config drift supports change control and RTO.

## Value

Network operations teams detect configuration drift on routers, switches, and firewalls by comparing running configs against known-good baselines, identifying unauthorized changes and devices with stale or missing backups.

## Implementation

Run config backup (RANCID, Oxidized, or vendor API) on schedule. Ingest success/failure and timestamp. Alert when backup fails or last successful backup is older than 24 hours. Optionally diff current vs. last backup for drift.

## Detailed Implementation

### Prerequisites
- Network device configuration backup tool (RANCID, Oxidized, Catalyst Center config archive, or custom scripts) storing device running configurations in Splunk. Data in `index=network_config` with `sourcetype=device:config`. Key fields: `hostname`, `config_hash`, `config_content` (full running config or diff), `backup_time`.
- For drift detection, the tool must store either: (1) the full running config each time, allowing Splunk to compare hashes across backups, or (2) a diff between current and previous config.
- This UC differs from UC-5.8.7 (which focuses on change window compliance) by focusing on the actual configuration content differences between the current state and a known-good baseline.

### Step 1 — Configure data collection
Verify config backup data from network devices:
```spl
index=network_config sourcetype="device:config" earliest=-7d
| stats count latest(_time) as last_backup dc(config_hash) as unique_configs by hostname
| eval days_since=round((now() - last_backup)/86400, 1)
| sort -days_since
```

### Step 2 — Create the search and alert

**Primary search — Configuration drift from baseline:**
```spl
index=network_config sourcetype="device:config" earliest=-30d
| sort hostname, _time
| streamstats current=t window=2 earliest(config_hash) as prev_hash earliest(_time) as prev_time by hostname
| where config_hash != prev_hash AND isnotnull(prev_hash)
| eval drift_hours=round((_time - prev_time)/3600, 1)
| lookup master_device_inventory.csv hostname OUTPUT site role tier
| stats count as drift_count latest(_time) as last_drift by hostname, site, role, tier
| eval last_drift_str=strftime(last_drift, "%Y-%m-%d %H:%M")
| sort -drift_count
```

#### Understanding this SPL: Configuration drift represents any change to a device's running configuration. While some changes are planned (maintenance, upgrades), others are unplanned (emergency fixes, unauthorized changes). High drift counts indicate either a device that's frequently tuned (needs stabilization) or one that's subject to unauthorized changes (needs access control review).

**Devices with no recent backup (stale configs):**
```spl
| inputlookup master_device_inventory.csv
| search role IN ("router", "switch", "firewall")
| join type=left hostname [search index=network_config sourcetype="device:config" earliest=-30d | stats latest(_time) as last_backup by hostname]
| eval days_since=if(isnotnull(last_backup), round((now() - last_backup)/86400, 1), 999)
| where days_since > 7
| table hostname, management_ip, model, site, role, days_since
| sort -days_since
```

**Configuration section analysis (what changed):**
```spl
index=network_config sourcetype="config:change" earliest=-7d
| stats count by hostname, changed_section
| chart sum(count) by hostname changed_section
| sort -interface
```

### Step 3 — Validate
(a) Make a test change on a lab device and verify the config drift is detected in the next backup cycle.
(b) Compare the config hash change with the actual diff output to confirm accuracy.
(c) Verify that all critical devices (Tier1 routers, core switches, firewalls) have recent backups.

### Step 4 — Operationalize
Dashboard ("Network Config Drift"):
- Row 1 — Single-value tiles: "Devices with drift (7d)", "Total changes", "Stale configs (> 7d)", "Devices never backed up".
- Row 2 — Drift frequency table: device, site, role, drift count, last drift.
- Row 3 — Stale config list: devices without recent backups.
- Row 4 — Changed sections breakdown.

Alerting:
- High (Tier1 device config drift detected): review change — was it authorized?
- Warning (device backup > 14 days old): backup system may have lost access.
- Info (weekly): drift summary report.

### Step 5 — Troubleshooting

- **Config hash changes every backup but no actual change** — The device includes timestamps, uptime counters, or NTP clock lines in the running config. Normalize the config before hashing: strip dynamic lines.

- **Backup tool can't reach device** — SSH credentials may have expired, or the device's management ACL blocks the backup server. Check TACACS/RADIUS logs for failed authentication attempts from the backup server IP.

- **Diff output too large to index** — Some config changes (e.g., replacing all ACLs) generate huge diffs. Set a max event size or store diffs as summary events with key statistics (lines added, lines removed, sections changed).

## SPL

```spl
index=network sourcetype=config_backup
| stats latest(backup_ok) as ok, latest(backup_time) as last_backup by device_hostname
| where ok != 1 OR (now()-last_backup) > 86400
| table device_hostname ok last_backup
```

## Visualization

Table (device, last backup, status), Single value (devices without backup today), Timeline (backup runs).

## Known False Positives

Lab devices and out-of-support gear may be intentionally absent from NCM; scope compliance to production tags.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
