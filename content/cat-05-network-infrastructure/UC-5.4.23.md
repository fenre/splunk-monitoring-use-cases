<!-- AUTO-GENERATED from UC-5.4.23.json — DO NOT EDIT -->

---
id: "5.4.23"
title: "Multicast and Broadcast Storm Detection (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.23 · Multicast and Broadcast Storm Detection (Meraki MR)

## Description

Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.

## Value

Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.

## Implementation

Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow dest="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```

Understanding this SPL

**Multicast and Broadcast Storm Detection (Meraki MR)** — Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.

Documented **Data sources**: `sourcetype=meraki type=flow`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, src_mac** so each row reflects one combination of those dimensions.
• Filters the current rows with `where pkt_count > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow dest="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dvc span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
