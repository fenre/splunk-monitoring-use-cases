<!-- AUTO-GENERATED from UC-1.1.36.json — DO NOT EDIT -->

---
id: "1.1.36"
title: "Multipath I/O Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.36 · Multipath I/O Failover Events

## Description

Multipath failovers indicate storage path degradation requiring immediate investigation to prevent I/O loss.

## Value

Multipath failovers indicate storage path degradation requiring immediate investigation to prevent I/O loss.

## Implementation

Configure multipathd logging to syslog. Create alerts on any failover event. Include search to show path status before/after failover to help storage team troubleshoot.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, multipathd logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure multipathd logging to syslog. Create alerts on any failover event. Include search to show path status before/after failover to help storage team troubleshoot.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "multipathd" "failover" OR "path failed" OR "path recovered"
| stats count by host, device
| timechart count by host
```

Understanding this SPL

**Multipath I/O Failover Events** — Multipath failovers indicate storage path degradation requiring immediate investigation to prevent I/O loss.

Documented **Data sources**: `sourcetype=syslog, multipathd logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, device** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Alert

## SPL

```spl
index=os sourcetype=syslog "multipathd" "failover" OR "path failed" OR "path recovered"
| stats count by host, device
| timechart count by host
```

## Visualization

Timechart, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
