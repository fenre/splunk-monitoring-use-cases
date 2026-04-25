<!-- AUTO-GENERATED from UC-5.5.4.json — DO NOT EDIT -->

---
id: "5.5.4"
title: "Path Failover Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.4 · Path Failover Events

## Description

Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.

## Value

Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.

## Implementation

Collect vManage alarm/event data. Track path changes and failover frequency. Alert on frequent failovers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: vManage events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect vManage alarm/event data. Track path changes and failover frequency. Alert on frequent failovers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:events" ("failover" OR "path-change" OR "transport-switch")
| stats count by site, from_transport, to_transport | sort -count
```

Understanding this SPL

**Path Failover Events** — Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.

Documented **Data sources**: vManage events. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by site, from_transport, to_transport** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Sankey diagram (from/to transport), Timeline.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:events" ("failover" OR "path-change" OR "transport-switch")
| stats count by site, from_transport, to_transport | sort -count
```

## Visualization

Table, Sankey diagram (from/to transport), Timeline.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
