---
id: "5.4.26"
title: "Top Talker Analysis and Bandwidth Hogs (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.26 · Top Talker Analysis and Bandwidth Hogs (Meraki MR)

## Description

Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.

## Value

Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.

## Implementation

Analyze flow records from syslog; track data usage by client and application.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Analyze flow records from syslog; track data usage by client and application.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort -total_bytes
| head 20
```

Understanding this SPL

**Top Talker Analysis and Bandwidth Hogs (Meraki MR)** — Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.

Documented **Data sources**: `sourcetype=meraki type=flow`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by client_mac, application** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort -total_bytes
| head 20
```

## Visualization

Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
