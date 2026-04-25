<!-- AUTO-GENERATED from UC-1.1.44.json — DO NOT EDIT -->

---
id: "1.1.44"
title: "Memory Leak Detection Per Process"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.44 · Memory Leak Detection Per Process

## Description

Process memory leaks cause gradual performance degradation and eventual OOM situations.

## Value

Process memory leaks cause gradual performance degradation and eventual OOM situations.

## Implementation

Use Splunk_TA_nix top input to track RSS memory per process. Calculate linear regression or growth trends over 1-week windows. Alert on processes with sustained >20% RSS growth in a week, indicating memory leaks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=top, custom:proc_rss_tracking`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix top input to track RSS memory per process. Calculate linear regression or growth trends over 1-week windows. Alert on processes with sustained >20% RSS growth in a week, indicating memory leaks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=top host=*
| stats latest(rss) as latest_rss, earliest(rss) as earliest_rss by host, process
| eval rss_growth=(latest_rss-earliest_rss)/earliest_rss*100
| where rss_growth > 20
| stats latest(latest_rss), max(rss_growth) by process, host
```

Understanding this SPL

**Memory Leak Detection Per Process** — Process memory leaks cause gradual performance degradation and eventual OOM situations.

Documented **Data sources**: `sourcetype=top, custom:proc_rss_tracking`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: top. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=top. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, process** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **rss_growth** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where rss_growth > 20` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by process, host** so each row reflects one combination of those dimensions.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Scatter Chart

## SPL

```spl
index=os sourcetype=top host=*
| stats latest(rss) as latest_rss, earliest(rss) as earliest_rss by host, process
| eval rss_growth=(latest_rss-earliest_rss)/earliest_rss*100
| where rss_growth > 20
| stats latest(latest_rss), max(rss_growth) by process, host
```

## Visualization

Table, Scatter Chart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
