---
id: "5.5.6"
title: "Certificate Expiration"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.6 · Certificate Expiration

## Description

SD-WAN device certificates must be valid for overlay connectivity.

## Value

SD-WAN device certificates must be valid for overlay connectivity.

## Implementation

Poll vManage for certificate status. Alert at 60/30/7 day thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage certificate inventory.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage for certificate status. Alert at 60/30/7 day thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:certificate"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<60
| table hostname system_ip days_left | sort days_left
```

Understanding this SPL

**Certificate Expiration** — SD-WAN device certificates must be valid for overlay connectivity.

Documented **Data sources**: vManage certificate inventory. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:certificate. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:certificate". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left<60` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Certificate Expiration**): table hostname system_ip days_left
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Single value, Status indicator.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:certificate"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<60
| table hostname system_ip days_left | sort days_left
```

## Visualization

Table, Single value, Status indicator.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
