---
id: "8.1.8"
title: "Connection Pool Saturation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.8 · Connection Pool Saturation

## Description

Saturated worker threads/processes cause request queuing and timeouts. Monitoring enables proactive scaling.

## Value

Saturated worker threads/processes cause request queuing and timeouts. Monitoring enables proactive scaling.

## Implementation

Enable Apache `mod_status` or NGINX `stub_status` module. Poll via scripted input every minute. Alert when busy workers exceed 80% of total. Correlate with request rate to distinguish capacity limits from slow backends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input (Apache `server-status`, NGINX `stub_status`).
• Ensure the following data sources are available: Apache mod_status, NGINX stub_status, IIS performance counters.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Apache `mod_status` or NGINX `stub_status` module. Poll via scripted input every minute. Alert when busy workers exceed 80% of total. Correlate with request rate to distinguish capacity limits from slow backends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="apache:server_status"
| eval pct_busy=round(BusyWorkers/(BusyWorkers+IdleWorkers)*100,1)
| timechart span=5m avg(pct_busy) as worker_pct by host
| where worker_pct > 80
```

Understanding this SPL

**Connection Pool Saturation** — Saturated worker threads/processes cause request queuing and timeouts. Monitoring enables proactive scaling.

Documented **Data sources**: Apache mod_status, NGINX stub_status, IIS performance counters. **App/TA** (typical add-on context): Scripted input (Apache `server-status`, NGINX `stub_status`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: apache:server_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="apache:server_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct_busy** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where worker_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% workers busy), Line chart (worker utilization over time), Table (hosts at capacity).

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
index=web sourcetype="apache:server_status"
| eval pct_busy=round(BusyWorkers/(BusyWorkers+IdleWorkers)*100,1)
| timechart span=5m avg(pct_busy) as worker_pct by host
| where worker_pct > 80
```

## Visualization

Gauge (% workers busy), Line chart (worker utilization over time), Table (hosts at capacity).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
