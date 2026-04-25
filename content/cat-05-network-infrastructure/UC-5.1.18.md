<!-- AUTO-GENERATED from UC-5.1.18.json — DO NOT EDIT -->

---
id: "5.1.18"
title: "CDP/LLDP Neighbor Changes"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.18 · CDP/LLDP Neighbor Changes

## Description

Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.

## Value

Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.

## Implementation

Poll CDP-MIB/LLDP-MIB at 600s intervals. Create a baseline lookup via `outputlookup`. Compare current neighbors against baseline. Alert on new/removed neighbors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, CISCO-CDP-MIB, LLDP-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:cdp`, `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll CDP-MIB/LLDP-MIB at 600s intervals. Create a baseline lookup via `outputlookup`. Compare current neighbors against baseline. Alert on new/removed neighbors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:cdp"
| stats latest(cdpCacheDeviceId) as neighbor, latest(cdpCachePlatform) as platform by host, cdpCacheIfIndex
| appendpipe [| inputlookup cdp_baseline.csv]
| eventstats latest(neighbor) as current, first(neighbor) as baseline by host, cdpCacheIfIndex
| where current!=baseline | table host, cdpCacheIfIndex, baseline, current, platform
```

Understanding this SPL

**CDP/LLDP Neighbor Changes** — Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.

Documented **Data sources**: `sourcetype=snmp:cdp`, `sourcetype=cisco:ios`. **App/TA** (typical add-on context): SNMP Modular Input, CISCO-CDP-MIB, LLDP-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:cdp. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:cdp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cdpCacheIfIndex** so each row reflects one combination of those dimensions.
• Appends rows from a subsearch with `append`.
• `eventstats` rolls up events into metrics; results are split **by host, cdpCacheIfIndex** so each row reflects one combination of those dimensions.
• Filters the current rows with `where current!=baseline` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **CDP/LLDP Neighbor Changes**): table host, cdpCacheIfIndex, baseline, current, platform
Step 3 — Validate
On the device, use `show cdp neighbor` and `show lldp neighbor` to confirm neighbor device and port match the syslog for the same minute.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, interface, old neighbor, new neighbor), Change log timeline.

## SPL

```spl
index=network sourcetype="snmp:cdp"
| stats latest(cdpCacheDeviceId) as neighbor, latest(cdpCachePlatform) as platform by host, cdpCacheIfIndex
| appendpipe [| inputlookup cdp_baseline.csv]
| eventstats latest(neighbor) as current, first(neighbor) as baseline by host, cdpCacheIfIndex
| where current!=baseline | table host, cdpCacheIfIndex, baseline, current, platform
```

## Visualization

Table (host, interface, old neighbor, new neighbor), Change log timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
