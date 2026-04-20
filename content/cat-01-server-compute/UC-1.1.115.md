---
id: "1.1.115"
title: "Listening Port Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.115 · Listening Port Compliance

## Description

Port compliance ensures only authorized services are listening, reducing attack surface.

## Value

Port compliance ensures only authorized services are listening, reducing attack surface.

## Implementation

Use Splunk_TA_nix openPorts input with baseline of expected listening ports per host. Create alerts for unexpected listening ports. Include service identification and change management correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=openPorts, netstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix openPorts input with baseline of expected listening ports per host. Create alerts for unexpected listening ports. Include service identification and change management correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=openPorts host=*
| where NOT (port IN (approved_port_list))
| stats count by host, port
| where count > 0
```

Understanding this SPL

**Listening Port Compliance** — Port compliance ensures only authorized services are listening, reducing attack surface.

Documented **Data sources**: `sourcetype=openPorts, netstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: openPorts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=openPorts. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT (port IN (approved_port_list))` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, port** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Listening Port Compliance** — Port compliance ensures only authorized services are listening, reducing attack surface.

Documented **Data sources**: `sourcetype=openPorts, netstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=openPorts host=*
| where NOT (port IN (approved_port_list))
| stats count by host, port
| where count > 0
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

## Visualization

Table, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
