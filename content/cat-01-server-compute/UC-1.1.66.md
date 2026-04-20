---
id: "1.1.66"
title: "SELinux Denial Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.66 · SELinux Denial Monitoring

## Description

SELinux denials indicate policy violations that may require tuning or signal legitimate attack attempts.

## Value

SELinux denials indicate policy violations that may require tuning or signal legitimate attack attempts.

## Implementation

Enable SELinux audit logging. Monitor /var/log/audit/audit.log for denial messages. Create alerts for denial spikes indicating possible policy misconfigurations or attacks. Include context in alerts to help debugging.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, /var/log/audit/audit.log`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable SELinux audit logging. Monitor /var/log/audit/audit.log for denial messages. Create alerts for denial spikes indicating possible policy misconfigurations or attacks. Include context in alerts to help debugging.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "SELinux" "denied"
| stats count by host, source_context, target_context, action
| where count > 5
```

Understanding this SPL

**SELinux Denial Monitoring** — SELinux denials indicate policy violations that may require tuning or signal legitimate attack attempts.

Documented **Data sources**: `sourcetype=syslog, /var/log/audit/audit.log`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, source_context, target_context, action** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=syslog "SELinux" "denied"
| stats count by host, source_context, target_context, action
| where count > 5
```

## Visualization

Table, Timechart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
