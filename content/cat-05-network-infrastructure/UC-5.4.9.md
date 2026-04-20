---
id: "5.4.9"
title: "Client Roaming Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.9 · Client Roaming Analysis

## Description

Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.

## Value

Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.

## Implementation

Enable client roaming event logging on the WLC. Track roaming frequency per client. Investigate clients with >10 roams/hour — indicates poor RF design or sticky client behavior.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco WLC syslog, Meraki API.
• Ensure the following data sources are available: `sourcetype=cisco:wlc`, `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable client roaming event logging on the WLC. Track roaming frequency per client. Investigate clients with >10 roams/hour — indicates poor RF design or sticky client behavior.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h maxpause=5m
| eval roam_count=eventcount-1
| stats avg(roam_count) as avg_roams, max(roam_count) as max_roams by client_mac, ssid
| where avg_roams > 10
```

Understanding this SPL

**Client Roaming Analysis** — Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.

Documented **Data sources**: `sourcetype=cisco:wlc`, `sourcetype=meraki:api`. **App/TA** (typical add-on context): Cisco WLC syslog, Meraki API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:wlc. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:wlc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Groups related events into transactions — prefer `maxspan`/`maxpause`/`maxevents` for bounded memory.
• `eval` defines or adjusts **roam_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by client_mac, ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_roams > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (client, SSID, roam count), Heatmap (AP-to-AP roaming), Choropleth (floor plan).

## SPL

```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h maxpause=5m
| eval roam_count=eventcount-1
| stats avg(roam_count) as avg_roams, max(roam_count) as max_roams by client_mac, ssid
| where avg_roams > 10
```

## Visualization

Table (client, SSID, roam count), Heatmap (AP-to-AP roaming), Choropleth (floor plan).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
