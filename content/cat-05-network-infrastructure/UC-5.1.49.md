---
id: "5.1.49"
title: "Port Access Control List (ACL) Hits and Block Events (Meraki MS)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.49 · Port Access Control List (ACL) Hits and Block Events (Meraki MS)

## Description

Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.

## Value

Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.

## Implementation

Monitor ACL deny/block events from syslog. Track frequently blocked source/destinations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*ACL*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor ACL deny/block events from syslog. Track frequently blocked source/destinations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*ACL*" action="block"
| stats count as block_count by switch_name, src_mac, dest_mac
| sort - block_count
```

Understanding this SPL

**Port Access Control List (ACL) Hits and Block Events (Meraki MS)** — Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*ACL*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, src_mac, dest_mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*ACL*" action="block"
| stats count as block_count by switch_name, src_mac, dest_mac
| sort - block_count
```

## Visualization

Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
