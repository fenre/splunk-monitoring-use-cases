<!-- AUTO-GENERATED from UC-1.1.43.json — DO NOT EDIT -->

---
id: "1.1.43"
title: "Fstrim and TRIM Command Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.43 · Fstrim and TRIM Command Monitoring

## Description

Fstrim failures indicate potential SSD performance degradation from lack of proper space reclamation.

## Value

Fstrim failures indicate potential SSD performance degradation from lack of proper space reclamation.

## Implementation

Create a cron job that runs fstrim -v and logs output to syslog. Create alerts for any failures. Track bytes discarded over time to ensure TRIM operations are completing successfully.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, custom:fstrim_status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a cron job that runs fstrim -v and logs output to syslog. Create alerts for any failures. Track bytes discarded over time to ensure TRIM operations are completing successfully.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:fstrim_status host=*
| stats latest(status) as trim_status, latest(bytes_discarded) as discarded by host, mount_point
| where trim_status!="success"
```

Understanding this SPL

**Fstrim and TRIM Command Monitoring** — Fstrim failures indicate potential SSD performance degradation from lack of proper space reclamation.

Documented **Data sources**: `sourcetype=syslog, custom:fstrim_status`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:fstrim_status. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:fstrim_status. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, mount_point** so each row reflects one combination of those dimensions.
• Filters the current rows with `where trim_status!="success"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=custom:fstrim_status host=*
| stats latest(status) as trim_status, latest(bytes_discarded) as discarded by host, mount_point
| where trim_status!="success"
```

## Visualization

Table, Timechart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
