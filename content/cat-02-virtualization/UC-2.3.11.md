<!-- AUTO-GENERATED from UC-2.3.11.json — DO NOT EDIT -->

---
id: "2.3.11"
title: "Proxmox Backup Server Job Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.3.11 · Proxmox Backup Server Job Status

## Description

Proxmox Backup Server (PBS) provides incremental, deduplicated VM backups. Failed backup jobs mean VMs have no recovery point. Monitoring backup status, duration, and deduplication ratio ensures recoverability and optimizes storage efficiency.

## Value

Proxmox Backup Server (PBS) provides incremental, deduplicated VM backups. Failed backup jobs mean VMs have no recovery point. Monitoring backup status, duration, and deduplication ratio ensures recoverability and optimizes storage efficiency.

## Implementation

Poll the PBS API (`/api2/json/nodes/{node}/tasks`) or forward PBS task logs to Splunk. Track backup success/failure per VM, backup duration, transferred size, and deduplication factor. Alert on any failed backup. Also alert when no backup has been taken for a VM in >24 hours. Monitor datastore capacity on PBS.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input, Proxmox syslog.
• Ensure the following data sources are available: Proxmox Backup Server API, `/var/log/proxmox-backup/tasks/`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the PBS API (`/api2/json/nodes/{node}/tasks`) or forward PBS task logs to Splunk. Track backup success/failure per VM, backup duration, transferred size, and deduplication factor. Alert on any failed backup. Also alert when no backup has been taken for a VM in >24 hours. Monitor datastore capacity on PBS.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="proxmox_backup"
| eval duration_min=round(duration_sec/60, 1)
| eval status_ok=if(status="OK", 1, 0)
| stats latest(status) as last_status, latest(duration_min) as last_duration_min, latest(backup_size_gb) as size_gb, latest(dedup_ratio) as dedup by vm_name, backup_type
| where last_status!="OK"
| table vm_name, backup_type, last_status, last_duration_min, size_gb, dedup
```

Understanding this SPL

**Proxmox Backup Server Job Status** — Proxmox Backup Server (PBS) provides incremental, deduplicated VM backups. Failed backup jobs mean VMs have no recovery point. Monitoring backup status, duration, and deduplication ratio ensures recoverability and optimizes storage efficiency.

Documented **Data sources**: Proxmox Backup Server API, `/var/log/proxmox-backup/tasks/`. **App/TA** (typical add-on context): Custom API input, Proxmox syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: proxmox_backup. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="proxmox_backup". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **status_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by vm_name, backup_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where last_status!="OK"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Proxmox Backup Server Job Status**): table vm_name, backup_type, last_status, last_duration_min, size_gb, dedup

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, status, duration, size), Bar chart (backup success rate), Timechart (backup duration trending).

## SPL

```spl
index=virtualization sourcetype="proxmox_backup"
| eval duration_min=round(duration_sec/60, 1)
| eval status_ok=if(status="OK", 1, 0)
| stats latest(status) as last_status, latest(duration_min) as last_duration_min, latest(backup_size_gb) as size_gb, latest(dedup_ratio) as dedup by vm_name, backup_type
| where last_status!="OK"
| table vm_name, backup_type, last_status, last_duration_min, size_gb, dedup
```

## Visualization

Table (VM, status, duration, size), Bar chart (backup success rate), Timechart (backup duration trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
