---
id: "2.6.15"
title: "Citrix Session Recording Compliance Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.15 · Citrix Session Recording Compliance Monitoring

## Description

Citrix Session Recording captures video recordings of user sessions for compliance auditing in regulated industries (healthcare, finance, government). Monitoring ensures that recording policies are consistently applied — sessions that should be recorded are being recorded, storage capacity is adequate, and recordings maintain integrity via digital signatures. Gaps in recording coverage represent compliance violations.

## Value

Citrix Session Recording captures video recordings of user sessions for compliance auditing in regulated industries (healthcare, finance, government). Monitoring ensures that recording policies are consistently applied — sessions that should be recorded are being recorded, storage capacity is adequate, and recordings maintain integrity via digital signatures. Gaps in recording coverage represent compliance violations.

## Implementation

Deploy a Splunk Universal Forwarder on Session Recording servers to collect session recording events and storage metrics. Monitor for: recording failures (disk full, agent disconnected, policy misconfiguration), storage capacity approaching limits (>80%), unsigned recordings (integrity concern), and sessions matching recording policy criteria that were not actually recorded (coverage gap). Generate daily compliance reports listing all recorded sessions by user, duration, and policy applied. Required for PCI DSS, HIPAA, and SOX environments where privileged access monitoring is mandated.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on Session Recording servers.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:sessionrecording"` fields `recording_status`, `session_id`, `user`, `policy_name`, `file_size_mb`, `storage_used_pct`, `signed`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on Session Recording servers to collect session recording events and storage metrics. Monitor for: recording failures (disk full, agent disconnected, policy misconfiguration), storage capacity approaching limits (>80%), unsigned recordings (integrity concern), and sessions matching recording policy criteria that were not actually recorded (coverage gap). Generate daily compliance reports listing all recorded sessions by user, duration, and policy applied. Requ…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:sessionrecording"
| stats sum(eval(if(recording_status="Recording", 1, 0))) as active_recordings,
  sum(eval(if(recording_status="Failed", 1, 0))) as failed_recordings,
  sum(file_size_mb) as total_storage_mb, latest(storage_used_pct) as storage_pct,
  sum(eval(if(signed="false", 1, 0))) as unsigned by policy_name
| eval fail_pct=if((active_recordings+failed_recordings)>0, round(failed_recordings/(active_recordings+failed_recordings)*100,1), 0)
| where failed_recordings > 0 OR storage_pct > 80 OR unsigned > 0
| table policy_name, active_recordings, failed_recordings, fail_pct, total_storage_mb, storage_pct, unsigned
```

Understanding this SPL

**Citrix Session Recording Compliance Monitoring** — Citrix Session Recording captures video recordings of user sessions for compliance auditing in regulated industries (healthcare, finance, government). Monitoring ensures that recording policies are consistently applied — sessions that should be recorded are being recorded, storage capacity is adequate, and recordings maintain integrity via digital signatures. Gaps in recording coverage represent compliance violations.

Documented **Data sources**: `index=xd` `sourcetype="citrix:sessionrecording"` fields `recording_status`, `session_id`, `user`, `policy_name`, `file_size_mb`, `storage_used_pct`, `signed`. **App/TA** (typical add-on context): Splunk Universal Forwarder on Session Recording servers. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:sessionrecording. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:sessionrecording". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by policy_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failed_recordings > 0 OR storage_pct > 80 OR unsigned > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Session Recording Compliance Monitoring**): table policy_name, active_recordings, failed_recordings, fail_pct, total_storage_mb, storage_pct, unsigned


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (recording compliance %), Gauge (storage utilization), Table (failed recordings with error details).

## SPL

```spl
index=xd sourcetype="citrix:sessionrecording"
| stats sum(eval(if(recording_status="Recording", 1, 0))) as active_recordings,
  sum(eval(if(recording_status="Failed", 1, 0))) as failed_recordings,
  sum(file_size_mb) as total_storage_mb, latest(storage_used_pct) as storage_pct,
  sum(eval(if(signed="false", 1, 0))) as unsigned by policy_name
| eval fail_pct=if((active_recordings+failed_recordings)>0, round(failed_recordings/(active_recordings+failed_recordings)*100,1), 0)
| where failed_recordings > 0 OR storage_pct > 80 OR unsigned > 0
| table policy_name, active_recordings, failed_recordings, fail_pct, total_storage_mb, storage_pct, unsigned
```

## Visualization

Single value (recording compliance %), Gauge (storage utilization), Table (failed recordings with error details).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
