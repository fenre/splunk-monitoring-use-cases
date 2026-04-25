<!-- AUTO-GENERATED from UC-5.2.14.json — DO NOT EDIT -->

---
id: "5.2.14"
title: "Firewall HA Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.14 · Firewall HA Failover Events

## Description

HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.

## Value

HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.

## Implementation

Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:system`, `sourcetype=fgt_event`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```

Understanding this SPL

**Firewall HA Failover Events** — HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.

Documented **Data sources**: `sourcetype=pan:system`, `sourcetype=fgt_event`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:system, fgt_event. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Firewall HA Failover Events**): table _time, dvc, old_state, new_state
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Single value (failovers this month), Table (history).

## SPL

```spl
index=firewall (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```

## Visualization

Timeline (failover events), Single value (failovers this month), Table (history).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
