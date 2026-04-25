<!-- AUTO-GENERATED from UC-5.1.7.json — DO NOT EDIT -->

---
id: "5.1.7"
title: "Configuration Change Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.7 · Configuration Change Detection

## Description

Unauthorized config changes are a top cause of outages. Essential for compliance.

## Value

Unauthorized config changes are a top cause of outages. Essential for compliance.

## Implementation

Forward syslog. Enable archive logging. Alert on any config change. Correlate with change tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Enable archive logging. Alert on any config change. Correlate with change tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%SYS-5-CONFIG_I"
| rex "Configured from (?<config_source>\S+) by (?<user>\S+)"
| table _time host user config_source
```

Understanding this SPL

**Configuration Change Detection** — Unauthorized config changes are a top cause of outages. Essential for compliance.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Configuration Change Detection**): table _time host user config_source


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, user, time), Timeline, Single value (changes last 24h).

## SPL

```spl
index=network sourcetype="cisco:ios" "%SYS-5-CONFIG_I"
| rex "Configured from (?<config_source>\S+) by (?<user>\S+)"
| table _time host user config_source
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Table (device, user, time), Timeline, Single value (changes last 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
