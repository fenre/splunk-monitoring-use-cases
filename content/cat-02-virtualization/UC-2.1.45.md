---
id: "2.1.45"
title: "VM Snapshot Age Alerting"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.45 · VM Snapshot Age Alerting

## Description

Snapshots older than N days degrade VM I/O performance and complicate backups — distinct from snapshot count or space. Old snapshots cause delta disk growth, extended backup windows, and increased risk of consolidation failures. Age-based alerting ensures timely cleanup.

## Value

Snapshots older than N days degrade VM I/O performance and complicate backups — distinct from snapshot count or space. Old snapshots cause delta disk growth, extended backup windows, and increased risk of consolidation failures. Age-based alerting ensures timely cleanup.

## Implementation

TA-vmware collects VM inventory including snapshot metadata. Define policy: alert on snapshots >7 days (high), >3 days (warning). Run daily report. Escalate to VM owners. Include snapshot size to prioritize cleanup. Correlate with datastore capacity for storage impact.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm` (snapshot info: snapshot_createTime, snapshot_name).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
TA-vmware collects VM inventory including snapshot metadata. Define policy: alert on snapshots >7 days (high), >3 days (warning). Run daily report. Escalate to VM owners. Include snapshot size to prioritize cleanup. Correlate with datastore capacity for storage impact.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" snapshot_name=*
| eval snapshot_age_days = round((now() - strptime(snapshot_createTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where snapshot_age_days > 7
| eval snapshot_size_gb = round(snapshot_sizeBytes / 1073741824, 2)
| sort -snapshot_age_days
| table vm_name, host, snapshot_name, snapshot_age_days, snapshot_size_gb, snapshot_createTime
```

Understanding this SPL

**VM Snapshot Age Alerting** — Snapshots older than N days degrade VM I/O performance and complicate backups — distinct from snapshot count or space. Old snapshots cause delta disk growth, extended backup windows, and increased risk of consolidation failures. Age-based alerting ensures timely cleanup.

Documented **Data sources**: `sourcetype=vmware:inv:vm` (snapshot info: snapshot_createTime, snapshot_name). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **snapshot_age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where snapshot_age_days > 7` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **snapshot_size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Snapshot Age Alerting**): table vm_name, host, snapshot_name, snapshot_age_days, snapshot_size_gb, snapshot_createTime


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, snapshot, age, size), Bar chart (snapshots by age bucket), Single value (snapshots >7 days).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" snapshot_name=*
| eval snapshot_age_days = round((now() - strptime(snapshot_createTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where snapshot_age_days > 7
| eval snapshot_size_gb = round(snapshot_sizeBytes / 1073741824, 2)
| sort -snapshot_age_days
| table vm_name, host, snapshot_name, snapshot_age_days, snapshot_size_gb, snapshot_createTime
```

## Visualization

Table (VM, snapshot, age, size), Bar chart (snapshots by age bucket), Single value (snapshots >7 days).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
