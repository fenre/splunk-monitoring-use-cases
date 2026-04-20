---
id: "5.1.12"
title: "ARP/MAC Table Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.12 · ARP/MAC Table Anomalies

## Description

MAC flapping indicates loops, misconfigurations, or layer-2 attacks.

## Value

MAC flapping indicates loops, misconfigurations, or layer-2 attacks.

## Implementation

Forward syslog. Alert on MACFLAP events. Investigate the MAC to find the device.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Alert on MACFLAP events. Investigate the MAC to find the device.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%SW_MATM-4-MACFLAP_NOTIF"
| rex "(?<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| stats count by host, mac | sort -count
```

Understanding this SPL

**ARP/MAC Table Anomalies** — MAC flapping indicates loops, misconfigurations, or layer-2 attacks.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timeline, Bar chart.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SW_MATM-4-MACFLAP_NOTIF"
| rex "(?<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| stats count by host, mac | sort -count
```

## Visualization

Table, Timeline, Bar chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
