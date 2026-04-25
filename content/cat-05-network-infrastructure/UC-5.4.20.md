<!-- AUTO-GENERATED from UC-5.4.20.json — DO NOT EDIT -->

---
id: "5.4.20"
title: "802.1X Authentication Failures and RADIUS Issues (Meraki MR)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.20 · 802.1X Authentication Failures and RADIUS Issues (Meraki MR)

## Description

Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.

## Value

Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.

## Implementation

Ingest 802.1X and RADIUS-related syslog events. Correlate with RADIUS server logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*802.1X*" OR signature="*Radius*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest 802.1X and RADIUS-related syslog events. Correlate with RADIUS server logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*802.1X*" OR signature="*Radius*" OR signature="*authentication*")
| stats count as auth_failures by client_mac, ap_name, signature
| eventstats sum(auth_failures) as total_failures by client_mac
| where total_failures > 10
| sort -total_failures
```

Understanding this SPL

**802.1X Authentication Failures and RADIUS Issues (Meraki MR)** — Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*802.1X*" OR signature="*Radius*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by client_mac, ap_name, signature** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by client_mac** so each row reflects one combination of those dimensions.
• Filters the current rows with `where total_failures > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of failing clients; time-series of auth failures; client-level detail dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*802.1X*" OR signature="*Radius*" OR signature="*authentication*")
| stats count as auth_failures by client_mac, ap_name, signature
| eventstats sum(auth_failures) as total_failures by client_mac
| where total_failures > 10
| sort -total_failures
```

## Visualization

Table of failing clients; time-series of auth failures; client-level detail dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
