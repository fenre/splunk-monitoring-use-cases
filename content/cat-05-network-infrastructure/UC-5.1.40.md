<!-- AUTO-GENERATED from UC-5.1.40.json — DO NOT EDIT -->

---
id: "5.1.40"
title: "Switch Interface Up/Down Events and Link Flapping (Meraki MS)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.40 · Switch Interface Up/Down Events and Link Flapping (Meraki MS)

## Description

Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.

## Value

Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.

## Implementation

Track interface up/down state changes over 24 hours. Alert on flapping (>2 changes/hour).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*link*" OR signature="*Interface*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track interface up/down state changes over 24 hours. Alert on flapping (>2 changes/hour).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*link*" OR signature="*Interface*" OR signature="*up*" OR signature="*down*")
| stats count as event_count by switch_name, port_id
| eval flap_rate=round(event_count/24, 2)
| where flap_rate > 2
```

Understanding this SPL

**Switch Interface Up/Down Events and Link Flapping (Meraki MS)** — Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*link*" OR signature="*Interface*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, port_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **flap_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where flap_rate > 2` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki dashboard, select the same organization, site, and UTC window as the Splunk search. Open Network-wide event log or the device event log and confirm a sample event count and field (for example `event_type` or `carrier_name`) matches what you see in Splunk.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time-series showing flap events; table of affected ports; link state history.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*link*" OR signature="*Interface*" OR signature="*up*" OR signature="*down*")
| stats count as event_count by switch_name, port_id
| eval flap_rate=round(event_count/24, 2)
| where flap_rate > 2
```

## Visualization

Time-series showing flap events; table of affected ports; link state history.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
