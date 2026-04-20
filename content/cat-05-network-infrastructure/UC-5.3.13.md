---
id: "5.3.13"
title: "Citrix ADC Virtual Server Health and State (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.13 · Citrix ADC Virtual Server Health and State (NetScaler)

## Description

Citrix ADC (NetScaler) virtual servers (vServers) are the front-end load-balancing endpoints that distribute traffic to back-end service groups. A vServer transitions from UP to DOWN when all bound services fail health checks, causing a complete outage for the application it serves. Monitoring vServer state changes provides immediate alerting when applications lose load-balanced availability.

## Value

Citrix ADC (NetScaler) virtual servers (vServers) are the front-end load-balancing endpoints that distribute traffic to back-end service groups. A vServer transitions from UP to DOWN when all bound services fail health checks, causing a complete outage for the application it serves. Monitoring vServer state changes provides immediate alerting when applications lose load-balanced availability.

## Implementation

Configure Citrix ADC to send syslog to Splunk via Splunk Connect for Syslog (SC4S). The ADC generates syslog messages for vServer state transitions (SNMP trap equivalent). Alternatively, use the NITRO API via scripted input to poll `lbvserver` statistics including `state`, `curclntconnections`, `tothits`, and `health` (percentage of UP services). Alert immediately on any vServer transitioning to DOWN. Track vServer health percentage — a vServer at 50% health means half its services are down and may be approaching failure. Correlate with service group member health checks for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), Splunk Connect for Syslog.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `vserver_name`, `vserver_state`, `vserver_type`, `service_name`, `service_state`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Citrix ADC to send syslog to Splunk via Splunk Connect for Syslog (SC4S). The ADC generates syslog messages for vServer state transitions (SNMP trap equivalent). Alternatively, use the NITRO API via scripted input to poll `lbvserver` statistics including `state`, `curclntconnections`, `tothits`, and `health` (percentage of UP services). Alert immediately on any vServer transitioning to DOWN. Track vServer health percentage — a vServer at 50% health means half its services are down and …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:syslog" "Vserver" ("DOWN" OR "UP" OR "OUT OF SERVICE")
| rex "Vserver (?<vserver_name>\S+) - State (?<state>\w+)"
| where state="DOWN" OR state="OUTOFSERVICE"
| bin _time span=5m
| stats count as state_changes, latest(state) as current_state, values(host) as adc_node by vserver_name, _time
| table _time, vserver_name, current_state, state_changes, adc_node
```

Understanding this SPL

**Citrix ADC Virtual Server Health and State (NetScaler)** — Citrix ADC (NetScaler) virtual servers (vServers) are the front-end load-balancing endpoints that distribute traffic to back-end service groups. A vServer transitions from UP to DOWN when all bound services fail health checks, causing a complete outage for the application it serves. Monitoring vServer state changes provides immediate alerting when applications lose load-balanced availability.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `vserver_name`, `vserver_state`, `vserver_type`, `service_name`, `service_state`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), Splunk Connect for Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where state="DOWN" OR state="OUTOFSERVICE"` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by vserver_name, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Citrix ADC Virtual Server Health and State (NetScaler)**): table _time, vserver_name, current_state, state_changes, adc_node


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (vServer name x state), Timeline (state transitions), Table (DOWN vServers with service count).

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
index=network sourcetype="citrix:netscaler:syslog" "Vserver" ("DOWN" OR "UP" OR "OUT OF SERVICE")
| rex "Vserver (?<vserver_name>\S+) - State (?<state>\w+)"
| where state="DOWN" OR state="OUTOFSERVICE"
| bin _time span=5m
| stats count as state_changes, latest(state) as current_state, values(host) as adc_node by vserver_name, _time
| table _time, vserver_name, current_state, state_changes, adc_node
```

## Visualization

Status grid (vServer name x state), Timeline (state transitions), Table (DOWN vServers with service count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
