---
id: "1.1.118"
title: "System Reboot Frequency Anomaly"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.118 · System Reboot Frequency Anomaly

## Description

Unexpected reboot frequency indicates system instability, crashes, or possible security incident response.

## Value

Unexpected reboot frequency indicates system instability, crashes, or possible security incident response.

## Implementation

Monitor system boot/reboot messages in syslog. Create alerts when reboot frequency exceeds normal baseline. Include reboot cause analysis and incident correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor system boot/reboot messages in syslog. Create alerts when reboot frequency exceeds normal baseline. Include reboot cause analysis and incident correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "Kernel panic" OR "reboot" OR "system shutdown"
| stats count as reboot_count by host
| where reboot_count > 2 in 7 days
```

Understanding this SPL

**System Reboot Frequency Anomaly** — Unexpected reboot frequency indicates system instability, crashes, or possible security incident response.

Documented **Data sources**: `sourcetype=syslog`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where reboot_count > 2 in 7 days` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Alert

## SPL

```spl
index=os sourcetype=syslog "Kernel panic" OR "reboot" OR "system shutdown"
| stats count as reboot_count by host
| where reboot_count > 2 in 7 days
```

## Visualization

Timechart, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
