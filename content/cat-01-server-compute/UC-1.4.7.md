---
id: "1.4.7"
title: "BMC Out-of-Band Connectivity Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.7 · BMC Out-of-Band Connectivity Health

## Description

BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.

## Value

BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.

## Implementation

Create scripted input: `ipmitool lan print` or vendor-specific tools (racadm, hpasm) to verify BMC reachability and LAN channel. Run every 5 minutes. Alert when BMC becomes unreachable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, IPMI.
• Ensure the following data sources are available: `ipmitool lan print`, BMC health sensors, SNMP (if BMC supports it).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `ipmitool lan print` or vendor-specific tools (racadm, hpasm) to verify BMC reachability and LAN channel. Run every 5 minutes. Alert when BMC becomes unreachable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=bmc_health host=*
| stats latest(channel_voltage) as voltage, latest(link_detected) as link by host
| where link="no" OR voltage < 3.0
| table host link voltage _time
```

Understanding this SPL

**BMC Out-of-Band Connectivity Health** — BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.

Documented **Data sources**: `ipmitool lan print`, BMC health sensors, SNMP (if BMC supports it). **App/TA** (typical add-on context): Custom scripted input, IPMI. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: bmc_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=bmc_health. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where link="no" OR voltage < 3.0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **BMC Out-of-Band Connectivity Health**): table host link voltage _time


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (BMC up/down per host), Table of unreachable BMCs, Single value (count of healthy BMCs).

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
index=hardware sourcetype=bmc_health host=*
| stats latest(channel_voltage) as voltage, latest(link_detected) as link by host
| where link="no" OR voltage < 3.0
| table host link voltage _time
```

## Visualization

Status grid (BMC up/down per host), Table of unreachable BMCs, Single value (count of healthy BMCs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
