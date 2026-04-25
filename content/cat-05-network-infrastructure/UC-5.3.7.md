<!-- AUTO-GENERATED from UC-5.3.7.json — DO NOT EDIT -->

---
id: "5.3.7"
title: "Session Persistence Issues (F5 BIG-IP)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.7 · Session Persistence Issues (F5 BIG-IP)

## Description

Broken persistence causes lost sessions, shopping carts, or random logouts.

## Value

Broken persistence causes lost sessions, shopping carts, or random logouts.

## Implementation

Monitor persistence failures. Track same client hitting different backends from request logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`.
• Ensure the following data sources are available: F5 LTM logs, request logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor persistence failures. Track same client hitting different backends from request logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:syslog" "persistence" ("failed" OR "expired")
| stats count by virtual_server, persistence_type | sort -count
```

Understanding this SPL

**Session Persistence Issues (F5 BIG-IP)** — Broken persistence causes lost sessions, shopping carts, or random logouts.

Documented **Data sources**: F5 LTM logs, request logs. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:syslog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by virtual_server, persistence_type** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In the F5 virtual server, pool, and persistence profile, confirm a sample client and cookie path matches the Splunk-parsed fields.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Line chart, Bar chart.

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" "persistence" ("failed" OR "expired")
| stats count by virtual_server, persistence_type | sort -count
```

## Visualization

Table, Line chart, Bar chart.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
