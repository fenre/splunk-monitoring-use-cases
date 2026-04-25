<!-- AUTO-GENERATED from UC-5.1.11.json — DO NOT EDIT -->

---
id: "5.1.11"
title: "Power Supply / Fan Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.11 · Power Supply / Fan Failures

## Description

Hardware failures reduce redundancy. A second failure causes outage.

## Value

Hardware failures reduce redundancy. A second failure causes outage.

## Implementation

Forward syslog. Poll ENVMON-MIB. Alert immediately on hardware failure. Include device location for dispatch.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, SNMP CISCO-ENVMON-MIB.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Poll ENVMON-MIB. Alert immediately on hardware failure. Include device location for dispatch.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%FAN-3-FAN_FAILED" OR "%PLATFORM_ENV-1-PSU" OR "%ENVIRONMENTAL-1-ALERT"
| table _time host _raw | sort -_time
```

Understanding this SPL

**Power Supply / Fan Failures** — Hardware failures reduce redundancy. A second failure causes outage.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, SNMP CISCO-ENVMON-MIB. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Power Supply / Fan Failures**): table _time host _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator per device, Events list (critical).

## SPL

```spl
index=network sourcetype="cisco:ios" "%FAN-3-FAN_FAILED" OR "%PLATFORM_ENV-1-PSU" OR "%ENVIRONMENTAL-1-ALERT"
| table _time host _raw | sort -_time
```

## Visualization

Status indicator per device, Events list (critical).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
