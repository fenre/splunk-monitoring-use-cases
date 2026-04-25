<!-- AUTO-GENERATED from UC-1.1.39.json — DO NOT EDIT -->

---
id: "1.1.39"
title: "Ext4 Filesystem Errors and Recovery"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.39 · Ext4 Filesystem Errors and Recovery

## Description

Ext4 errors may indicate filesystem corruption or hardware issues requiring immediate diagnostic action.

## Value

Ext4 errors may indicate filesystem corruption or hardware issues requiring immediate diagnostic action.

## Implementation

Monitor for ext4-specific error messages in kernel logs. Create a baseline of expected errors and alert on increases. Correlate with disk smart data and I/O error rates to identify hardware vs. filesystem issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, dmesg`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor for ext4-specific error messages in kernel logs. Create a baseline of expected errors and alert on increases. Correlate with disk smart data and I/O error rates to identify hardware vs. filesystem issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog host=* ("ext4" AND ("error" OR "abort" OR "FS-error"))
| stats count by host, mount_point
| eval severity="high"
```

Understanding this SPL

**Ext4 Filesystem Errors and Recovery** — Ext4 errors may indicate filesystem corruption or hardware issues requiring immediate diagnostic action.

Documented **Data sources**: `sourcetype=syslog, dmesg`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, mount_point** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=syslog host=* ("ext4" AND ("error" OR "abort" OR "FS-error"))
| stats count by host, mount_point
| eval severity="high"
```

## Visualization

Table, Timechart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
