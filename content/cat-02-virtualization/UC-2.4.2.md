---
id: "2.4.2"
title: "VM Backup Coverage Validation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.4.2 · VM Backup Coverage Validation

## Description

VMs without recent successful backups have no recovery point — a single failure causes permanent data loss. By comparing VM inventory across all hypervisors against backup job success records, this use case identifies VMs that have fallen through the cracks of the backup policy.

## Value

VMs without recent successful backups have no recovery point — a single failure causes permanent data loss. By comparing VM inventory across all hypervisors against backup job success records, this use case identifies VMs that have fallen through the cracks of the backup policy.

## Implementation

Combine VM inventory from all hypervisors with backup job results from your backup product. Left-join to find VMs with no matching backup job. Alert on VMs with no backup in >24 hours (for daily policy) or >48 hours (with buffer). Exclude development/test VMs via a lookup if appropriate. Run daily and send report to backup administrators.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, `Splunk_TA_windows`, backup vendor TA.
• Ensure the following data sources are available: VM inventory from all hypervisors, backup job logs (Veeam, Commvault, Cohesity, PBS).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Combine VM inventory from all hypervisors with backup job results from your backup product. Left-join to find VMs with no matching backup job. Alert on VMs with no backup in >24 hours (for daily policy) or >48 hours (with buffer). Exclude development/test VMs via a lookup if appropriate. Run daily and send report to backup administrators.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats latest(vm_name) as vm_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" state="Running" | stats latest(vm_name) as vm_name by vm_name]
| sort 0 vm_name, -_time
| dedup vm_name
| join type=left max=1 vm_name [search index=backup sourcetype="backup_jobs" status="Success" earliest=-48h | stats latest(_time) as last_backup, latest(status) as backup_status by vm_name]
| eval backup_age_hours=if(isnotnull(last_backup), round((now()-last_backup)/3600, 0), 999)
| where backup_age_hours > 48 OR isnull(last_backup)
| sort -backup_age_hours
| table vm_name, backup_status, last_backup, backup_age_hours
```

Understanding this SPL

**VM Backup Coverage Validation** — VMs without recent successful backups have no recovery point — a single failure causes permanent data loss. By comparing VM inventory across all hypervisors against backup job success records, this use case identifies VMs that have fallen through the cracks of the backup policy.

Documented **Data sources**: VM inventory from all hypervisors, backup job logs (Veeam, Commvault, Cohesity, PBS). **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`, backup vendor TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Appends rows from a subsearch with `append`.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Removes duplicate values with `dedup` — pair with `sort` when order matters.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **backup_age_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where backup_age_hours > 48 OR isnull(last_backup)` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Backup Coverage Validation**): table vm_name, backup_status, last_backup, backup_age_hours


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (unprotected VMs), Single value (backup coverage %), Pie chart (backed up vs unprotected), Bar chart (backup age distribution).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats latest(vm_name) as vm_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" state="Running" | stats latest(vm_name) as vm_name by vm_name]
| sort 0 vm_name, -_time
| dedup vm_name
| join type=left max=1 vm_name [search index=backup sourcetype="backup_jobs" status="Success" earliest=-48h | stats latest(_time) as last_backup, latest(status) as backup_status by vm_name]
| eval backup_age_hours=if(isnotnull(last_backup), round((now()-last_backup)/3600, 0), 999)
| where backup_age_hours > 48 OR isnull(last_backup)
| sort -backup_age_hours
| table vm_name, backup_status, last_backup, backup_age_hours
```

## Visualization

Table (unprotected VMs), Single value (backup coverage %), Pie chart (backed up vs unprotected), Bar chart (backup age distribution).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
