---
id: "5.2.38"
title: "Connection Rate Analysis and DOS Detection (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.38 · Connection Rate Analysis and DOS Detection (Meraki MX)

## Description

Detects denial of service attacks by analyzing abnormal connection establishment rates.

## Value

Detects denial of service attacks by analyzing abnormal connection establishment rates.

## Implementation

Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow protocol="tcp" tcp_flags="SYN"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src
| where new_connections > 1000
```

Understanding this SPL

**Connection Rate Analysis and DOS Detection (Meraki MX)** — Detects denial of service attacks by analyzing abnormal connection establishment rates.

Documented **Data sources**: `sourcetype=meraki type=flow protocol="tcp" tcp_flags="SYN"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time with a separate series **by src** — ideal for trending and alerting on this use case.
• Filters the current rows with `where new_connections > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Connection rate timeline; source IP detail table; DOS alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src
| where new_connections > 1000
```

## Visualization

Connection rate timeline; source IP detail table; DOS alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
