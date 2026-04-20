---
id: "5.1.39"
title: "Port Security Violations and Rogue Device Detection (Meraki MS)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.1.39 · Port Security Violations and Rogue Device Detection (Meraki MS)

## Description

Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.

## Value

Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.

## Implementation

Monitor port security violation events from syslog. Create alert for each unique violation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*Port Security*" OR signature="*Unauthorized MAC*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor port security violation events from syslog. Create alert for each unique violation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Port Security*" OR signature="*Unauthorized*")
| stats count as violation_count by switch_name, port_id, mac_address
| where violation_count > 0
| sort - violation_count
```

Understanding this SPL

**Port Security Violations and Rogue Device Detection (Meraki MS)** — Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*Port Security*" OR signature="*Unauthorized MAC*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name, port_id, mac_address** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where violation_count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of violations; timeline of events; network detail with affected ports.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Port Security*" OR signature="*Unauthorized*")
| stats count as violation_count by switch_name, port_id, mac_address
| where violation_count > 0
| sort - violation_count
```

## Visualization

Table of violations; timeline of events; network detail with affected ports.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
