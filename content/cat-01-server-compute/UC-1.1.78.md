---
id: "1.1.78"
title: "Open Port Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.78 · Open Port Changes

## Description

New listening ports indicate service configuration changes or malware opening backdoors.

## Value

New listening ports indicate service configuration changes or malware opening backdoors.

## Implementation

Use Splunk_TA_nix openPorts input to track listening ports per host. Baseline expected ports. Create alerts on new listening ports with escalation to change management. Include process information showing which service opened port.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=openPorts`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix openPorts input to track listening ports per host. Baseline expected ports. Create alerts on new listening ports with escalation to change management. Include process information showing which service opened port.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=openPorts host=*
| stats latest(port_list) as current_ports by host
| eval new_ports=port_list - previous_ports
| where isnotnull(new_ports)
```

Understanding this SPL

**Open Port Changes** — New listening ports indicate service configuration changes or malware opening backdoors.

Documented **Data sources**: `sourcetype=openPorts`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: openPorts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=openPorts. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **new_ports** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where isnotnull(new_ports)` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=openPorts host=*
| stats latest(port_list) as current_ports by host
| eval new_ports=port_list - previous_ports
| where isnotnull(new_ports)
```

## Visualization

Alert, Table

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
