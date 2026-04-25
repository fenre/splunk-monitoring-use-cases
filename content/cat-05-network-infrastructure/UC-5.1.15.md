<!-- AUTO-GENERATED from UC-5.1.15.json — DO NOT EDIT -->

---
id: "5.1.15"
title: "Environmental Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.15 · Environmental Monitoring

## Description

Temperature alerts catch cooling failures before they cause device outages.

## Value

Temperature alerts catch cooling failures before they cause device outages.

## Implementation

Poll ENVMON-MIB temperature sensors every 300s. Alert when >45°C.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP, CISCO-ENVMON-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:environment`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll ENVMON-MIB temperature sensors every 300s. Alert when >45°C.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:environment"
| stats latest(ciscoEnvMonTemperatureValue) as temp_c by host | where temp_c > 45
```

Understanding this SPL

**Environmental Monitoring** — Temperature alerts catch cooling failures before they cause device outages.

Documented **Data sources**: `sourcetype=snmp:environment`. **App/TA** (typical add-on context): SNMP, CISCO-ENVMON-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:environment. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:environment". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where temp_c > 45` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per device, Line chart (trending), Table.

## SPL

```spl
index=network sourcetype="snmp:environment"
| stats latest(ciscoEnvMonTemperatureValue) as temp_c by host | where temp_c > 45
```

## Visualization

Gauge per device, Line chart (trending), Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
