<!-- AUTO-GENERATED from UC-5.2.8.json — DO NOT EDIT -->

---
id: "5.2.8"
title: "Certificate Inspection Failures"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.8 · Certificate Inspection Failures

## Description

SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.

## Value

SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.

## Implementation

Enable decryption logging. Track failure rates by destination. Tune exclusion lists.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: Firewall decryption logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable decryption logging. Track failure rates by destination. Tune exclusion lists.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest, dest_port, reason | sort -count
```

Understanding this SPL

**Certificate Inspection Failures** — SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.

Documented **Data sources**: Firewall decryption logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:decryption. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:decryption". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dest, dest_port, reason** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Pie chart (reasons), Trend line.

## SPL

```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest, dest_port, reason | sort -count
```

## Visualization

Table, Pie chart (reasons), Trend line.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
