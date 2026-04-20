---
id: "8.2.11"
title: "PHP-FPM Pool Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.11 · PHP-FPM Pool Monitoring

## Description

Active/idle process counts, listen queue depth, and slow request detection indicate PHP-FPM capacity and backend saturation. Exhausted pools cause 502 errors and request timeouts.

## Value

Active/idle process counts, listen queue depth, and slow request detection indicate PHP-FPM capacity and backend saturation. Exhausted pools cause 502 errors and request timeouts.

## Implementation

Enable PHP-FPM status via `pm.status_path = /status` and `pm.status_listen` in pool config. Add `fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name`; protect with auth. Poll `/status?json` via scripted input every minute. Parse active_processes, idle_processes, listen_queue, max_listen_queue, slow_requests. Forward to Splunk via HEC. Alert when pool_util >80% or listen_queue >5. Track slow_requests for endpoints needing optimization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (PHP-FPM status page).
• Ensure the following data sources are available: PHP-FPM status page (JSON output, `/status?json`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable PHP-FPM status via `pm.status_path = /status` and `pm.status_listen` in pool config. Add `fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name`; protect with auth. Poll `/status?json` via scripted input every minute. Parse active_processes, idle_processes, listen_queue, max_listen_queue, slow_requests. Forward to Splunk via HEC. Alert when pool_util >80% or listen_queue >5. Track slow_requests for endpoints needing optimization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=php sourcetype="phpfpm:status"
| eval pool_util=round(active_processes/(active_processes+idle_processes)*100,1)
| where pool_util > 80 OR listen_queue > 5
| timechart span=5m max(pool_util) as util_pct, max(listen_queue) as queue_depth by host, pool
```

Understanding this SPL

**PHP-FPM Pool Monitoring** — Active/idle process counts, listen queue depth, and slow request detection indicate PHP-FPM capacity and backend saturation. Exhausted pools cause 502 errors and request timeouts.

Documented **Data sources**: PHP-FPM status page (JSON output, `/status?json`). **App/TA** (typical add-on context): Custom scripted input (PHP-FPM status page). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: php; **sourcetype**: phpfpm:status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=php, sourcetype="phpfpm:status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pool_util** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pool_util > 80 OR listen_queue > 5` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, pool** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% pool used), Line chart (pool utilization and queue depth), Table (pools with high utilization), Single value (slow requests).

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
index=php sourcetype="phpfpm:status"
| eval pool_util=round(active_processes/(active_processes+idle_processes)*100,1)
| where pool_util > 80 OR listen_queue > 5
| timechart span=5m max(pool_util) as util_pct, max(listen_queue) as queue_depth by host, pool
```

## Visualization

Gauge (% pool used), Line chart (pool utilization and queue depth), Table (pools with high utilization), Single value (slow requests).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
