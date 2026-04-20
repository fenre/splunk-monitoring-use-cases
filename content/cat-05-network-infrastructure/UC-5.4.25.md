---
id: "5.4.25"
title: "Connected Client Count Trending and Capacity Planning (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.25 · Connected Client Count Trending and Capacity Planning (Meraki MR)

## Description

Tracks client density by AP and SSID for capacity planning and performance optimization.

## Value

Tracks client density by AP and SSID for capacity planning and performance optimization.

## Implementation

Query clients API to count connected devices. Track over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query clients API to count connected devices. Track over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by ap_name, ssid
| eval capacity_pct=round(client_count*100/30, 2)
| where capacity_pct > 70
| sort - client_count
```

Understanding this SPL

**Connected Client Count Trending and Capacity Planning (Meraki MR)** — Tracks client density by AP and SSID for capacity planning and performance optimization.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **capacity_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where capacity_pct > 70` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by ap_name, ssid
| eval capacity_pct=round(client_count*100/30, 2)
| where capacity_pct > 70
| sort - client_count
```

## Visualization

Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
