---
id: "5.2.20"
title: "Content Filtering and URL Category Blocks (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.20 · Content Filtering and URL Category Blocks (Meraki MX)

## Description

Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.

## Value

Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.

## Implementation

Ingest URL filtering events from MX syslog. Categorize by policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=urls action="blocked"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest URL filtering events from MX syslog. Categorize by policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```

Understanding this SPL

**Content Filtering and URL Category Blocks (Meraki MX)** — Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.

Documented **Data sources**: `sourcetype=meraki type=urls action="blocked"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by url_category, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of top blocked categories; bar chart by category; user detail table.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```

## Visualization

Table of top blocked categories; bar chart by category; user detail table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
