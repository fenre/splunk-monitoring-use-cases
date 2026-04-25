<!-- AUTO-GENERATED from UC-5.1.9.json — DO NOT EDIT -->

---
id: "5.1.9"
title: "Device Uptime / Reload Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.9 · Device Uptime / Reload Tracking

## Description

Unexpected reboots indicate hardware failure or unauthorized reload.

## Value

Unexpected reboots indicate hardware failure or unauthorized reload.

## Implementation

Poll SNMP sysUpTime. Forward syslog reload messages. Alert when uptime drops. Cross-reference with maintenance windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: SNMP sysUpTime, `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll SNMP sysUpTime. Forward syslog reload messages. Alert when uptime drops. Cross-reference with maintenance windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%SYS-5-RESTART" OR "%SYS-5-RELOAD"
| table _time host _raw | sort -_time
```

Understanding this SPL

**Device Uptime / Reload Tracking** — Unexpected reboots indicate hardware failure or unauthorized reload.

Documented **Data sources**: SNMP sysUpTime, `sourcetype=cisco:ios`. **App/TA** (typical add-on context): SNMP, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Device Uptime / Reload Tracking**): table _time host _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, uptime), Timeline, Single value (unexpected reboots).

## SPL

```spl
index=network sourcetype="cisco:ios" "%SYS-5-RESTART" OR "%SYS-5-RELOAD"
| table _time host _raw | sort -_time
```

## Visualization

Table (device, uptime), Timeline, Single value (unexpected reboots).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
