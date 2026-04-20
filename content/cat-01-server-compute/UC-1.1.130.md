---
id: "1.1.130"
title: "TCP Connection State Distribution (Linux)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.130 · TCP Connection State Distribution (Linux)

## Description

Count of ESTABLISHED, TIME_WAIT, CLOSE_WAIT, SYN_RECV connections. Detects connection leaks (accumulating CLOSE_WAIT), exhaustion (TIME_WAIT), and half-open buildup.

## Value

Count of ESTABLISHED, TIME_WAIT, CLOSE_WAIT, SYN_RECV connections. Detects connection leaks (accumulating CLOSE_WAIT), exhaustion (TIME_WAIT), and half-open buildup.

## Implementation

Create a scripted input that runs `ss -s` (parse TCP: inuse X orphaned X tw X alloc X mem X) or `netstat -an | awk` to count by state. Parse ESTAB, TIME-WAIT, CLOSE-WAIT, SYN-RECV. Run every 60 seconds. Alert when CLOSE_WAIT exceeds 1000 (possible connection leak); alert when TIME_WAIT exceeds 10000 (port exhaustion risk).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `ss -s` or `netstat` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `ss -s` (parse TCP: inuse X orphaned X tw X alloc X mem X) or `netstat -an | awk` to count by state. Parse ESTAB, TIME-WAIT, CLOSE-WAIT, SYN-RECV. Run every 60 seconds. Alert when CLOSE_WAIT exceeds 1000 (possible connection leak); alert when TIME_WAIT exceeds 10000 (port exhaustion risk).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=tcp_states host=*
| timechart span=15m avg(CLOSE-WAIT) as close_wait by host
| where close_wait > 500
```

Understanding this SPL

**TCP Connection State Distribution (Linux)** — Count of ESTABLISHED, TIME_WAIT, CLOSE_WAIT, SYN_RECV connections. Detects connection leaks (accumulating CLOSE_WAIT), exhaustion (TIME_WAIT), and half-open buildup.

Documented **Data sources**: `ss -s` or `netstat` output. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: tcp_states. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=tcp_states. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where close_wait > 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart (state distribution by host), Line chart (CLOSE_WAIT over time), Table of hosts exceeding thresholds.

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
index=os sourcetype=tcp_states host=*
| timechart span=15m avg(CLOSE-WAIT) as close_wait by host
| where close_wait > 500
```

## Visualization

Stacked bar chart (state distribution by host), Line chart (CLOSE_WAIT over time), Table of hosts exceeding thresholds.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
