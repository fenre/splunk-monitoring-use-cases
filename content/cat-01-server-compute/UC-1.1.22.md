---
id: "1.1.22"
title: "Sysctl Parameter Changes Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.22 · Sysctl Parameter Changes Detection

## Description

Identifies modifications to kernel parameters that affect system behavior, security posture, or performance tuning.

## Value

Identifies modifications to kernel parameters that affect system behavior, security posture, or performance tuning.

## Implementation

Set up auditctl rules to monitor changes to /proc/sys and /etc/sysctl.conf. Create alerts for unexpected sysctl modifications, especially those affecting network (ip_forward, tcp_syncookies) or IPC parameters.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit, /proc/sys monitoring`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set up auditctl rules to monitor changes to /proc/sys and /etc/sysctl.conf. Create alerts for unexpected sysctl modifications, especially those affecting network (ip_forward, tcp_syncookies) or IPC parameters.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit action=modified path=/proc/sys/*
| stats count by host, path, exe, auid
| where count > 0
```

Understanding this SPL

**Sysctl Parameter Changes Detection** — Identifies modifications to kernel parameters that affect system behavior, security posture, or performance tuning.

Documented **Data sources**: `sourcetype=linux_audit, /proc/sys monitoring`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, path, exe, auid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timeline

## SPL

```spl
index=os sourcetype=linux_audit action=modified path=/proc/sys/*
| stats count by host, path, exe, auid
| where count > 0
```

## Visualization

Table, Timeline

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
