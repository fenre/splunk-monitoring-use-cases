---
id: "5.2.32"
title: "Bandwidth by Application and Department (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.32 · Bandwidth by Application and Department (Meraki MX)

## Description

Tracks bandwidth consumption by application and business unit for chargeback and optimization.

## Value

Tracks bandwidth consumption by application and business unit for chargeback and optimization.

## Implementation

Correlate flows with IP-to-department mapping. Aggregate by app and dept.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Correlate flows with IP-to-department mapping. Aggregate by app and dept.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort -total_mb
```

Understanding this SPL

**Bandwidth by Application and Department (Meraki MX)** — Tracks bandwidth consumption by application and business unit for chargeback and optimization.

Documented **Data sources**: `sourcetype=meraki type=flow`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by application, department** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort -total_mb
```

## Visualization

Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
