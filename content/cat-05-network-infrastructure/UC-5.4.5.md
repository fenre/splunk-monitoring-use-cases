<!-- AUTO-GENERATED from UC-5.4.5.json — DO NOT EDIT -->

---
id: "5.4.5"
title: "Client Count Trending"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.5 · Client Count Trending

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We watch client count trending so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Client count trending informs capacity planning and AP density decisions.

## Value

Network operations teams track wireless client counts per AP against model-specific capacity limits, identifying overloaded access points and generating capacity planning data for building and floor-level wireless density management.

## Implementation

1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki and configure a Meraki Dashboard alert profile that includes 'client connection changed' and 'unique client connected'. 2. Each webhook event carries alertData.clientMac and deviceName (the AP). 3. Use dc(client_mac) over a sliding window for concurrent clients per AP. 4. For the network-wide totals (not per-AP), the polled meraki:summarytopclientsbyusage input lists the top 10 clients by usage but does not give a complete client roster.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Meraki API, WLC SNMP.
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) configured for client connectivity alerts. The polled Dashboard API does NOT expose a per-AP client list; per-association events come via webhook only..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki and configure a Meraki Dashboard alert profile that includes 'client connection changed' and 'unique client connected'. 2. Each webhook event carries alertData.clientMac and deviceName (the AP). 3. Use dc(client_mac) over a sliding window for concurrent clients per AP. 4. For the network-wide totals (not per-AP), the polled meraki:summarytopclientsbyusage input lists the top 10 clients by usage but does not give a complete client r…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="client_connectivity" OR alertTypeId="client_connection_changed"
     OR alertType="association")
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac', 'alertData.mac')
| eval ap_name = coalesce(deviceName, 'alertData.deviceName')
| timechart span=1h dc(client_mac) as concurrent_clients by ap_name
```

#### Understanding this SPL

**Client Count Trending** — Network operations teams track wireless client counts per AP against model-specific capacity limits, identifying overloaded access points and generating capacity planning data for building and floor-level wireless density management.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) configured for client connectivity alerts. The polled Dashboard API does NOT expose a per-AP client list; per-association events come via webhook only. **App/TA** (typical add-on context): Meraki API, WLC SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **ap_name** — often to normalize units, derive a ratio, or prepare for thresholds.
- `timechart` plots the metric over time using **span=1h** buckets with a separate series **by ap_name** — ideal for trending and alerting on this use case.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (clients over time), Table (AP, count), Heatmap.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="client_connectivity" OR alertTypeId="client_connection_changed"
     OR alertType="association")
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac', 'alertData.mac')
| eval ap_name = coalesce(deviceName, 'alertData.deviceName')
| timechart span=1h dc(client_mac) as concurrent_clients by ap_name
```

## Visualization

Line chart (clients over time), Table (AP, count), Heatmap.

## Known False Positives

Wireless client counts spike during shift changes, big events, or back-to-school style rushes; compare against the calendar before calling it an incident.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
