---
id: "2.6.6"
title: "Citrix Machine Power State Management"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.6 · Citrix Machine Power State Management

## Description

Citrix Delivery Controllers manage VM power states through power policy schedules — powering on machines before business hours and off after hours to save resources. Failed power actions (VM failed to start, hypervisor timeout, stuck in boot) reduce available session capacity during peak hours. Monitoring power action success rates and queue depth ensures machines are ready when users arrive.

## Value

Citrix Delivery Controllers manage VM power states through power policy schedules — powering on machines before business hours and off after hours to save resources. Failed power actions (VM failed to start, hypervisor timeout, stuck in boot) reduce available session capacity during peak hours. Monitoring power action success rates and queue depth ensures machines are ready when users arrive.

## Implementation

The Broker Service logs power management actions with Event IDs in the 2000–3000 range. Track power actions (TurnOn, TurnOff, Shutdown, Reset, Restart) and their results (Success, Failed, Pending, Canceled). The Broker throttles power actions per hypervisor connection to avoid overloading — a large pending queue indicates throttling bottleneck or hypervisor slowness. Alert on: any failed power actions, pending queue exceeding 10 actions (backlog), or power-on failures during scheduled scale-out windows. Use `Get-BrokerHostingPowerAction` via PowerShell scripted input for real-time queue visibility.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`).
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"` fields `power_action`, `power_state`, `machine_name`, `delivery_group`, `action_result`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The Broker Service logs power management actions with Event IDs in the 2000–3000 range. Track power actions (TurnOn, TurnOff, Shutdown, Reset, Restart) and their results (Success, Failed, Pending, Canceled). The Broker throttles power actions per hypervisor connection to avoid overloading — a large pending queue indicates throttling bottleneck or hypervisor slowness. Alert on: any failed power actions, pending queue exceeding 10 actions (backlog), or power-on failures during scheduled scale-out …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:broker:events" event_type="PowerAction"
| bin _time span=1h
| stats sum(eval(if(action_result="Success", 1, 0))) as success,
  sum(eval(if(action_result="Failed", 1, 0))) as failed,
  sum(eval(if(action_result="Pending", 1, 0))) as pending,
  count as total by power_action, delivery_group, _time
| eval fail_pct=if(total>0, round(failed/total*100,1), 0)
| where failed > 0 OR pending > 10
| table _time, delivery_group, power_action, total, success, failed, pending, fail_pct
```

Understanding this SPL

**Citrix Machine Power State Management** — Citrix Delivery Controllers manage VM power states through power policy schedules — powering on machines before business hours and off after hours to save resources. Failed power actions (VM failed to start, hypervisor timeout, stuck in boot) reduce available session capacity during peak hours. Monitoring power action success rates and queue depth ensures machines are ready when users arrive.

Documented **Data sources**: `index=xd` `sourcetype="citrix:broker:events"` fields `power_action`, `power_state`, `machine_name`, `delivery_group`, `action_result`. **App/TA** (typical add-on context): Template for Citrix XenDesktop 7 (`TA-XD7-Broker`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:broker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:broker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by power_action, delivery_group, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failed > 0 OR pending > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Machine Power State Management**): table _time, delivery_group, power_action, total, success, failed, pending, fail_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (power actions by result), Bar chart (failures by delivery group), Single value (pending queue depth).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=xd sourcetype="citrix:broker:events" event_type="PowerAction"
| bin _time span=1h
| stats sum(eval(if(action_result="Success", 1, 0))) as success,
  sum(eval(if(action_result="Failed", 1, 0))) as failed,
  sum(eval(if(action_result="Pending", 1, 0))) as pending,
  count as total by power_action, delivery_group, _time
| eval fail_pct=if(total>0, round(failed/total*100,1), 0)
| where failed > 0 OR pending > 10
| table _time, delivery_group, power_action, total, success, failed, pending, fail_pct
```

## Visualization

Timechart (power actions by result), Bar chart (failures by delivery group), Single value (pending queue depth).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
