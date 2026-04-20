---
id: "2.1.38"
title: "ESXi Host Syslog Forwarding Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.38 · ESXi Host Syslog Forwarding Health

## Description

If ESXi syslog forwarding breaks, you lose visibility into host-level events — PSOD messages, hardware errors, authentication attempts, and kernel warnings. Since syslog is often the only real-time data source from ESXi (vs. the polling-based TA), silent forwarding failures create dangerous blind spots.

## Value

If ESXi syslog forwarding breaks, you lose visibility into host-level events — PSOD messages, hardware errors, authentication attempts, and kernel warnings. Since syslog is often the only real-time data source from ESXi (vs. the polling-based TA), silent forwarding failures create dangerous blind spots.

## Implementation

Verify syslog configuration via Splunk_TA_vmware host inventory. Monitor for gaps in syslog data per host — if a host stops sending syslog for >1 hour, investigate. Alert on hosts without syslog configured. Validate syslog protocol (UDP vs TCP vs TLS) meets security requirements.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, ESXi syslog.
• Ensure the following data sources are available: ESXi syslog, `sourcetype=vmware:inv:hostsystem`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Verify syslog configuration via Splunk_TA_vmware host inventory. Monitor for gaps in syslog data per host — if a host stops sending syslog for >1 hour, investigate. Alert on hosts without syslog configured. Validate syslog protocol (UDP vs TCP vs TLS) meets security requirements.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(syslogConfig_logHost) as syslog_target by host
| eval syslog_configured=if(isnotnull(syslog_target) AND syslog_target!="", "Yes", "No")
| append [search index=esxi sourcetype=syslog | stats latest(_time) as last_seen by host]
| stats latest(syslog_configured) as configured, latest(last_seen) as last_event by host
| eval hours_silent=round((now()-last_event)/3600, 1)
| where configured="No" OR hours_silent > 2
| table host, configured, syslog_target, last_event, hours_silent
```

Understanding this SPL

**ESXi Host Syslog Forwarding Health** — If ESXi syslog forwarding breaks, you lose visibility into host-level events — PSOD messages, hardware errors, authentication attempts, and kernel warnings. Since syslog is often the only real-time data source from ESXi (vs. the polling-based TA), silent forwarding failures create dangerous blind spots.

Documented **Data sources**: ESXi syslog, `sourcetype=vmware:inv:hostsystem`. **App/TA** (typical add-on context): `Splunk_TA_vmware`, ESXi syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:hostsystem. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:hostsystem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **syslog_configured** — often to normalize units, derive a ratio, or prepare for thresholds.
• Appends rows from a subsearch with `append`.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **hours_silent** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where configured="No" OR hours_silent > 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ESXi Host Syslog Forwarding Health**): table host, configured, syslog_target, last_event, hours_silent


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (syslog health per host), Table (misconfigured hosts), Single value (hosts with gaps).

## SPL

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(syslogConfig_logHost) as syslog_target by host
| eval syslog_configured=if(isnotnull(syslog_target) AND syslog_target!="", "Yes", "No")
| append [search index=esxi sourcetype=syslog | stats latest(_time) as last_seen by host]
| stats latest(syslog_configured) as configured, latest(last_seen) as last_event by host
| eval hours_silent=round((now()-last_event)/3600, 1)
| where configured="No" OR hours_silent > 2
| table host, configured, syslog_target, last_event, hours_silent
```

## Visualization

Status grid (syslog health per host), Table (misconfigured hosts), Single value (hosts with gaps).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
