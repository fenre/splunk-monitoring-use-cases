---
id: "1.1.126"
title: "Chrony / NTP Time Synchronization Drift"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.126 · Chrony / NTP Time Synchronization Drift

## Description

Clock offset, stratum, and reachability issues cause authentication failures, log correlation errors, and certificate validation problems. Time drift is a root cause of many subtle failures.

## Value

Clock offset, stratum, and reachability issues cause authentication failures, log correlation errors, and certificate validation problems. Time drift is a root cause of many subtle failures.

## Implementation

Create a scripted input that runs `chronyc tracking` (parse Last offset, Stratum, Leap status) or `ntpq -p` for ntpd. Extract offset_ms (convert to milliseconds), stratum, and reachability (octal 377 = all peers reachable). Run every 300 seconds. Alert when offset exceeds 100ms; alert when stratum > 10 or reachability indicates no peers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `chronyc tracking`, `ntpq -p`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `chronyc tracking` (parse Last offset, Stratum, Leap status) or `ntpq -p` for ntpd. Extract offset_ms (convert to milliseconds), stratum, and reachability (octal 377 = all peers reachable). Run every 300 seconds. Alert when offset exceeds 100ms; alert when stratum > 10 or reachability indicates no peers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=ntp_status host=*
| timechart span=15m avg(offset_ms) as offset_ms by host
| where abs(offset_ms) > 50
```

Understanding this SPL

**Chrony / NTP Time Synchronization Drift** — Clock offset, stratum, and reachability issues cause authentication failures, log correlation errors, and certificate validation problems. Time drift is a root cause of many subtle failures.

Documented **Data sources**: `chronyc tracking`, `ntpq -p`. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: ntp_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=ntp_status. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where abs(offset_ms) > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (offset over time by host), Table (host, offset, stratum), Single value (hosts with drift).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=ntp_status host=*
| timechart span=15m avg(offset_ms) as offset_ms by host
| where abs(offset_ms) > 50
```

## Visualization

Line chart (offset over time by host), Table (host, offset, stratum), Single value (hosts with drift).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
