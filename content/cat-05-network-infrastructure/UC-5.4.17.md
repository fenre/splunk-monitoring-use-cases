---
id: "5.4.17"
title: "Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.17 · Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)

## Description

Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.

## Value

Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.

## Implementation

Enable Air Marshal on MR APs and ingest syslog events. Create alert for new rogue AP detections with risk scoring.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=air_marshal`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Air Marshal on MR APs and ingest syslog events. Create alert for new rogue AP detections with risk scoring.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=air_marshal signature="*Rogue*" OR signature="*Unauthorized*"
| stats count by ssid, bssid, first_detected, last_seen, threat_level
| where threat_level="high" OR threat_level="critical"
| sort - first_detected
```

Understanding this SPL

**Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)** — Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.

Documented **Data sources**: `sourcetype=meraki type=air_marshal`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ssid, bssid, first_detected, last_seen, threat_level** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where threat_level="high" OR threat_level="critical"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=air_marshal signature="*Rogue*" OR signature="*Unauthorized*"
| stats count by ssid, bssid, first_detected, last_seen, threat_level
| where threat_level="high" OR threat_level="critical"
| sort - first_detected
```

## Visualization

Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
