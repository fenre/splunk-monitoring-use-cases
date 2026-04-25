<!-- AUTO-GENERATED from UC-5.8.16.json — DO NOT EDIT -->

---
id: "5.8.16"
title: "Alert Volume Trending and Alert Fatigue Analysis (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.16 · Alert Volume Trending and Alert Fatigue Analysis (Meraki)

## Description

Analyzes alert volume trends to optimize alerting rules and reduce false positives.

## Value

Analyzes alert volume trends to optimize alerting rules and reduce false positives.

## Implementation

Ingest webhook alerts. Track volume and types over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks).
• Ensure the following data sources are available: `sourcetype=meraki:webhook`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest webhook alerts. Track volume and types over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:webhook"
| timechart count as alert_count by alert_type
| eval alert_ratio=alert_count/sum(alert_count)
```

Understanding this SPL

**Alert Volume Trending and Alert Fatigue Analysis (Meraki)** — Analyzes alert volume trends to optimize alerting rules and reduce false positives.

Documented **Data sources**: `sourcetype=meraki:webhook`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:webhook. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:webhook". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time with a separate series **by alert_type** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **alert_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert volume timeline; alert type pie chart; trend sparklines.

## SPL

```spl
index=cisco_network sourcetype="meraki:webhook"
| timechart count as alert_count by alert_type
| eval alert_ratio=alert_count/sum(alert_count)
```

## Visualization

Alert volume timeline; alert type pie chart; trend sparklines.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
