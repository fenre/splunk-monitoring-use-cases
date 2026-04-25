<!-- AUTO-GENERATED from UC-5.1.22.json — DO NOT EDIT -->

---
id: "5.1.22"
title: "Syslog Source Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.22 · Syslog Source Health

## Description

Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.

## Value

Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.

## Implementation

Maintain a device inventory lookup. Schedule a search comparing active syslog sources against inventory. Alert on devices missing for >1 hour.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk core (metadata search), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`, `sourcetype=syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain a device inventory lookup. Schedule a search comparing active syslog sources against inventory. Alert on devices missing for >1 hour.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| tstats count where index=network sourcetype="cisco:ios" by host
| append [| inputlookup network_device_inventory.csv | rename device as host | fields host]
| stats sum(count) as event_count by host | where event_count=0 OR isnull(event_count)
| table host | rename host as "Silent Devices"
```

Understanding this SPL

**Syslog Source Health** — Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.

Documented **Data sources**: `sourcetype=cisco:ios`, `sourcetype=syslog`. **App/TA** (typical add-on context): Splunk core (metadata search), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Uses `tstats` against precomputed summaries; ensure the referenced data model is accelerated.
• Appends rows from a subsearch with `append`.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where event_count=0 OR isnull(event_count)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Syslog Source Health**): table host
• Renames fields with `rename` for clarity or joins.
Step 3 — Validate
On a heavy forwarder or syslog receiver, `telnet` or `openssl s_client` to the device and confirm UDP or TCP 514 is still accepted. Compare 24h `timechart` counts per host to a device you know is online; silent periods often mean a network ACL or NTP issue, not the switch.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (silent devices), Single value (count of silent devices), Status grid (all devices).

## SPL

```spl
| tstats count where index=network sourcetype="cisco:ios" by host
| append [| inputlookup network_device_inventory.csv | rename device as host | fields host]
| stats sum(count) as event_count by host | where event_count=0 OR isnull(event_count)
| table host | rename host as "Silent Devices"
```

## Visualization

Table (silent devices), Single value (count of silent devices), Status grid (all devices).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
