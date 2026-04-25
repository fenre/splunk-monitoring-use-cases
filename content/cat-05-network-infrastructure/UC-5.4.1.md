<!-- AUTO-GENERATED from UC-5.4.1.json — DO NOT EDIT -->

---
id: "5.4.1"
title: "AP Offline Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.1 · AP Offline Detection

## Description

Offline APs create coverage dead zones. Users lose connectivity in affected areas.

## Value

Offline APs create coverage dead zones. Users lose connectivity in affected areas.

## Implementation

For Meraki: configure syslog in Dashboard, or use Meraki API TA. For WLC: forward syslog. Alert when APs go offline. Maintain AP inventory lookup for location context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), WLC syslog.
• Ensure the following data sources are available: `sourcetype=meraki, WLC events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For Meraki: configure syslog in Dashboard, or use Meraki API TA. For WLC: forward syslog. Alert when APs go offline. Maintain AP inventory lookup for location context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="meraki" type="access point" ("went offline" OR "unreachable")
| table _time host ap_name network status | sort -_time
```

Understanding this SPL

**AP Offline Detection** — Offline APs create coverage dead zones. Users lose connectivity in affected areas.

Documented **Data sources**: `sourcetype=meraki, WLC events`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), WLC syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **AP Offline Detection**): table _time host ap_name network status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (AP locations with status), Table, Status grid, Single value (APs offline).

## SPL

```spl
index=network sourcetype="meraki" type="access point" ("went offline" OR "unreachable")
| table _time host ap_name network status | sort -_time
```

## Visualization

Map (AP locations with status), Table, Status grid, Single value (APs offline).

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
