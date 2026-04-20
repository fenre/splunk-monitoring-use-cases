---
id: "1.4.3"
title: "Power Supply Failure"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.4.3 · Power Supply Failure

## Description

Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.

## Value

Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.

## Implementation

Forward IPMI System Event Log data. Enable syslog forwarding from iLO/iDRAC to Splunk. Alert immediately on PSU failure events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`), SNMP, vendor management syslog (iLO/iDRAC).
• Ensure the following data sources are available: IPMI SEL (System Event Log) via scripted input, syslog from BMC.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward IPMI System Event Log data. Enable syslog forwarding from iLO/iDRAC to Splunk. Alert immediately on PSU failure events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=ipmi:sel ("Power Supply" OR "PS" OR "power_supply") ("Failure" OR "Absent" OR "fault" OR "lost")
| table _time host sensor event_description
| sort -_time
```

Understanding this SPL

**Power Supply Failure** — Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.

Documented **Data sources**: IPMI SEL (System Event Log) via scripted input, syslog from BMC. **App/TA** (typical add-on context): Custom scripted input (`ipmitool`), SNMP, vendor management syslog (iLO/iDRAC). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: ipmi:sel. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=ipmi:sel. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Power Supply Failure**): table _time host sensor event_description
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Status indicator per host, Alert panel.

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
index=hardware sourcetype=ipmi:sel ("Power Supply" OR "PS" OR "power_supply") ("Failure" OR "Absent" OR "fault" OR "lost")
| table _time host sensor event_description
| sort -_time
```

## Visualization

Events timeline, Status indicator per host, Alert panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
