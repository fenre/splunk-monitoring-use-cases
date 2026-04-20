---
id: "5.2.39"
title: "Data Loss Prevention (DLP) Event Analysis (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.39 · Data Loss Prevention (DLP) Event Analysis (Meraki MX)

## Description

Detects and alerts on sensitive data transmission to prevent data exfiltration.

## Value

Detects and alerts on sensitive data transmission to prevent data exfiltration.

## Implementation

Enable DLP on MX appliance. Ingest DLP match events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*DLP*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DLP on MX appliance. Ingest DLP match events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src, dest, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```

Understanding this SPL

**Data Loss Prevention (DLP) Event Analysis (Meraki MX)** — Detects and alerts on sensitive data transmission to prevent data exfiltration.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*DLP*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest, dlp_policy, data_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where dlp_match_count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: DLP incident timeline; data type breakdown; source/destination detail.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src, dest, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```

## Visualization

DLP incident timeline; data type breakdown; source/destination detail.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
