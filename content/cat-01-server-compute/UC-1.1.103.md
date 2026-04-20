---
id: "1.1.103"
title: "IPMI Sensor Threshold Violations"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.103 · IPMI Sensor Threshold Violations

## Description

IPMI sensor violations indicate hardware conditions (thermal, voltage, power) requiring immediate remediation.

## Value

IPMI sensor violations indicate hardware conditions (thermal, voltage, power) requiring immediate remediation.

## Implementation

Create a scripted input running ipmitool sensor list and parsing status. Alert on CRITICAL or WARNING status. Include sensor readings and recommended actions per sensor type.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:ipmi, ipmitool sensor output`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input running ipmitool sensor list and parsing status. Alert on CRITICAL or WARNING status. Include sensor readings and recommended actions per sensor type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:ipmi host=*
| stats latest(sensor_status) as status by host, sensor_name
| where status IN ("CRITICAL", "WARNING")
```

Understanding this SPL

**IPMI Sensor Threshold Violations** — IPMI sensor violations indicate hardware conditions (thermal, voltage, power) requiring immediate remediation.

Documented **Data sources**: `sourcetype=custom:ipmi, ipmitool sensor output`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:ipmi. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:ipmi. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, sensor_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where status IN ("CRITICAL", "WARNING")` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

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
index=os sourcetype=custom:ipmi host=*
| stats latest(sensor_status) as status by host, sensor_name
| where status IN ("CRITICAL", "WARNING")
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
