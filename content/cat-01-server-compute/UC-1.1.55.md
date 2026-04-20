---
id: "1.1.55"
title: "DNS Resolution Failure Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.55 · DNS Resolution Failure Rate

## Description

DNS failures impact application availability and user experience, requiring immediate investigation.

## Value

DNS failures impact application availability and user experience, requiring immediate investigation.

## Implementation

Monitor systemd-resolved or BIND logs for DNS query failures. Track NXDOMAIN, SERVFAIL, and TIMEOUT responses. Alert on failure rate spikes with correlation to specific nameservers or query types.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, systemd-resolved logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor systemd-resolved or BIND logs for DNS query failures. Track NXDOMAIN, SERVFAIL, and TIMEOUT responses. Alert on failure rate spikes with correlation to specific nameservers or query types.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "systemd-resolved" ("SERVFAIL" OR "NXDOMAIN" OR "TIMEOUT")
| stats count as failures by host, query_name
| eval failure_rate=count
| where failure_rate > 10
```

Understanding this SPL

**DNS Resolution Failure Rate** — DNS failures impact application availability and user experience, requiring immediate investigation.

Documented **Data sources**: `sourcetype=syslog, systemd-resolved logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, query_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **failure_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failure_rate > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=syslog "systemd-resolved" ("SERVFAIL" OR "NXDOMAIN" OR "TIMEOUT")
| stats count as failures by host, query_name
| eval failure_rate=count
| where failure_rate > 10
```

## Visualization

Table, Timechart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
