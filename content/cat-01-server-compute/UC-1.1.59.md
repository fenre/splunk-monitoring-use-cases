---
id: "1.1.59"
title: "Network Team Failover Detection (Linux)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.59 · Network Team Failover Detection (Linux)

## Description

Teamed interface failovers indicate critical network path failures affecting server connectivity.

## Value

Teamed interface failovers indicate critical network path failures affecting server connectivity.

## Implementation

Monitor teamd daemon logs for port state changes. Create alerts on any port disable/enable events. Correlate with physical switch logs to validate network-side issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, teamd logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor teamd daemon logs for port state changes. Create alerts on any port disable/enable events. Correlate with physical switch logs to validate network-side issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "teamd" ("port" OR "link") ("down" OR "up" OR "enabled" OR "disabled")
| stats count by host, team_interface
| where count > 0
```

Understanding this SPL

**Network Team Failover Detection (Linux)** — Teamed interface failovers indicate critical network path failures affecting server connectivity.

Documented **Data sources**: `sourcetype=syslog, teamd logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, team_interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

Understanding this CIM / accelerated SPL

**Network Team Failover Detection (Linux)** — Teamed interface failovers indicate critical network path failures affecting server connectivity.

Documented **Data sources**: `sourcetype=syslog, teamd logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=syslog "teamd" ("port" OR "link") ("down" OR "up" OR "enabled" OR "disabled")
| stats count by host, team_interface
| where count > 0
```

## CIM SPL

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

## Visualization

Alert, Table

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
