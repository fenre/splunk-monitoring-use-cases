<!-- AUTO-GENERATED from UC-3.1.2.json — DO NOT EDIT -->

---
id: "3.1.2"
title: "Container OOM Kills"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.2 · Container OOM Kills

## Description

OOM kills mean the container exceeded its memory limit. The application is either leaking memory or undersized. Data loss is likely.

## Value

OOM kills mean the container exceeded its memory limit. The application is either leaking memory or undersized. Data loss is likely.

## Implementation

Collect Docker events and forward host syslog. Alert immediately on any OOM event. Include container memory limit in the alert context to aid right-sizing decisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker, host syslog.
• Ensure the following data sources are available: `sourcetype=docker:events`, host `dmesg`/syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Docker events and forward host syslog. Alert immediately on any OOM event. Include container memory limit in the alert context to aid right-sizing decisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "Memory cgroup out of memory" OR "oom-kill"
| rex "task (?<process>\S+)"
| table _time host process _raw
```

Understanding this SPL

**Container OOM Kills** — OOM kills mean the container exceeded its memory limit. The application is either leaking memory or undersized. Data loss is likely.

Documented **Data sources**: `sourcetype=docker:events`, host `dmesg`/syslog. **App/TA** (typical add-on context): Splunk Connect for Docker, host syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Container OOM Kills**): table _time host process _raw


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Single value (OOM count last 24h), Table with container details.

## SPL

```spl
index=os sourcetype=syslog "Memory cgroup out of memory" OR "oom-kill"
| rex "task (?<process>\S+)"
| table _time host process _raw
```

## Visualization

Events timeline, Single value (OOM count last 24h), Table with container details.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
