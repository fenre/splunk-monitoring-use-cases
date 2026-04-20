---
id: "2.6.14"
title: "Citrix Workspace Environment Management (WEM) Optimization Effectiveness"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.14 · Citrix Workspace Environment Management (WEM) Optimization Effectiveness

## Description

Citrix WEM uses CPU spike protection and CPU clamping to prevent individual processes from monopolizing session host resources. Monitoring WEM optimization actions reveals which processes trigger CPU throttling, how often protection engages, and whether the configured thresholds are appropriate. Excessive WEM interventions may indicate undersized VDAs or resource-hungry applications that need attention.

## Value

Citrix WEM uses CPU spike protection and CPU clamping to prevent individual processes from monopolizing session host resources. Monitoring WEM optimization actions reveals which processes trigger CPU throttling, how often protection engages, and whether the configured thresholds are appropriate. Excessive WEM interventions may indicate undersized VDAs or resource-hungry applications that need attention.

## Implementation

Collect WEM agent logs from VDAs. The WEM agent logs CPU spike protection events (process priority lowered) and CPU clamping events (process throttled) with the offending process name, CPU threshold that was exceeded, and duration of the intervention. Alert when a single VDA experiences more than 10 WEM interventions per hour (indicates capacity issue). Track the most frequently throttled processes — these are candidates for application optimization, isolation to dedicated delivery groups, or VDA resource increases. Compare WEM intervention frequency before and after VDA resource changes to validate capacity additions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on VDAs, WEM agent logs.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:wem:agent"` fields `action_type`, `process_name`, `cpu_threshold`, `duration_sec`, `user`, `vda_host`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect WEM agent logs from VDAs. The WEM agent logs CPU spike protection events (process priority lowered) and CPU clamping events (process throttled) with the offending process name, CPU threshold that was exceeded, and duration of the intervention. Alert when a single VDA experiences more than 10 WEM interventions per hour (indicates capacity issue). Track the most frequently throttled processes — these are candidates for application optimization, isolation to dedicated delivery groups, or VD…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:wem:agent" (action_type="CpuSpikeProtection" OR action_type="CpuClamping")
| bin _time span=1h
| stats count as interventions, dc(process_name) as unique_processes, dc(user) as affected_users, values(process_name) as throttled_processes by action_type, vda_host, _time
| where interventions > 10
| table _time, vda_host, action_type, interventions, unique_processes, affected_users, throttled_processes
```

Understanding this SPL

**Citrix Workspace Environment Management (WEM) Optimization Effectiveness** — Citrix WEM uses CPU spike protection and CPU clamping to prevent individual processes from monopolizing session host resources. Monitoring WEM optimization actions reveals which processes trigger CPU throttling, how often protection engages, and whether the configured thresholds are appropriate. Excessive WEM interventions may indicate undersized VDAs or resource-hungry applications that need attention.

Documented **Data sources**: `index=xd` `sourcetype="citrix:wem:agent"` fields `action_type`, `process_name`, `cpu_threshold`, `duration_sec`, `user`, `vda_host`. **App/TA** (typical add-on context): Splunk Universal Forwarder on VDAs, WEM agent logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:wem:agent. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:wem:agent". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by action_type, vda_host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where interventions > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Workspace Environment Management (WEM) Optimization Effectiveness**): table _time, vda_host, action_type, interventions, unique_processes, affected_users, throttled_processes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top throttled processes), Timechart (WEM interventions over time), Table (VDAs with most frequent interventions).

## SPL

```spl
index=xd sourcetype="citrix:wem:agent" (action_type="CpuSpikeProtection" OR action_type="CpuClamping")
| bin _time span=1h
| stats count as interventions, dc(process_name) as unique_processes, dc(user) as affected_users, values(process_name) as throttled_processes by action_type, vda_host, _time
| where interventions > 10
| table _time, vda_host, action_type, interventions, unique_processes, affected_users, throttled_processes
```

## Visualization

Bar chart (top throttled processes), Timechart (WEM interventions over time), Table (VDAs with most frequent interventions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
