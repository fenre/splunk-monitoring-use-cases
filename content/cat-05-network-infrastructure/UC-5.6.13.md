<!-- AUTO-GENERATED from UC-5.6.13.json — DO NOT EDIT -->

---
id: "5.6.13"
title: "Failed DHCP Assignments and IP Pool Exhaustion (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.13 · Failed DHCP Assignments and IP Pool Exhaustion (Meraki)

## Description

Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.

## Value

Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.

## Implementation

Monitor syslog for DHCP NACK and failure events. Alert on sustained failure rate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*DHCP*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor syslog for DHCP NACK and failure events. Alert on sustained failure rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*" (signature="*failure*" OR signature="*NACK*")
| stats count as failure_count by ap_name, signature
| where failure_count > 5
| sort - failure_count
```

Understanding this SPL

**Failed DHCP Assignments and IP Pool Exhaustion (Meraki)** — Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*DHCP*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, signature** so each row reflects one combination of those dimensions.
• Filters the current rows with `where failure_count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*" (signature="*failure*" OR signature="*NACK*")
| stats count as failure_count by ap_name, signature
| where failure_count > 5
| sort - failure_count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

## Visualization

Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
