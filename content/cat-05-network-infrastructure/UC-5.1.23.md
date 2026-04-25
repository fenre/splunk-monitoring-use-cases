<!-- AUTO-GENERATED from UC-5.1.23.json — DO NOT EDIT -->

---
id: "5.1.23"
title: "HSRP/VRRP State Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.23 · HSRP/VRRP State Changes

## Description

Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages.

## Value

Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages.

## Implementation

Enable HSRP/VRRP syslog notifications. Alert on Active/Master transitions. Correlate with interface or device failures to validate failover cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable HSRP/VRRP syslog notifications. Alert on Active/Master transitions. Correlate with interface or device failures to validate failover cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%HSRP-5-STATECHANGE" OR "%VRRP-6-STATECHANGE"
| rex "Grp (?<group>\d+) state (?<old_state>\w+) -> (?<new_state>\w+)"
| where new_state="Active" OR new_state="Master"
| stats count by host, group, old_state, new_state | sort -_time
```

Understanding this SPL

**HSRP/VRRP State Changes** — Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where new_state="Active" OR new_state="Master"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, group, old_state, new_state** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (state changes), Table (group, host, transition), Alert panel.

## SPL

```spl
index=network sourcetype="cisco:ios" "%HSRP-5-STATECHANGE" OR "%VRRP-6-STATECHANGE"
| rex "Grp (?<group>\d+) state (?<old_state>\w+) -> (?<new_state>\w+)"
| where new_state="Active" OR new_state="Master"
| stats count by host, group, old_state, new_state | sort -_time
```

## Visualization

Timeline (state changes), Table (group, host, transition), Alert panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
