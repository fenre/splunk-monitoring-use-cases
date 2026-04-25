<!-- AUTO-GENERATED from UC-8.4.9.json — DO NOT EDIT -->

---
id: "8.4.9"
title: "HAProxy Backend and Frontend Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.9 · HAProxy Backend and Frontend Health

## Description

Backend server state, connection queue depth, and HTTP response distribution indicate load balancer effectiveness and backend capacity. Detection of DOWN backends or saturated queues enables rapid failover and scaling decisions.

## Value

Backend server state, connection queue depth, and HTTP response distribution indicate load balancer effectiveness and backend capacity. Detection of DOWN backends or saturated queues enables rapid failover and scaling decisions.

## Implementation

Enable HAProxy stats via `stats uri /haproxy?stats` and `stats enable` in the frontend. Poll stats CSV via scripted input (curl or socket) every 30–60 seconds. Parse backend/frontend rows; extract status (UP/DOWN), qcur (current queued requests), scur (current sessions), and response code distribution. Forward to Splunk via HEC. Alert when any backend is DOWN or queue_depth exceeds 10. Correlate with syslog for connection errors and backend health transitions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (HAProxy stats socket/CSV, syslog).
• Ensure the following data sources are available: HAProxy stats CSV (`/haproxy?stats;csv`), syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable HAProxy stats via `stats uri /haproxy?stats` and `stats enable` in the frontend. Poll stats CSV via scripted input (curl or socket) every 30–60 seconds. Parse backend/frontend rows; extract status (UP/DOWN), qcur (current queued requests), scur (current sessions), and response code distribution. Forward to Splunk via HEC. Alert when any backend is DOWN or queue_depth exceeds 10. Correlate with syslog for connection errors and backend health transitions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=haproxy sourcetype="haproxy:stats"
| eval backend_status=case(status=="UP",1, status=="DOWN",0, 1=1,null())
| stats latest(backend_status) as up, latest(qcur) as queue_depth, latest(scur) as sessions by pxname, svname, type
| where type=="backend" AND (up==0 OR queue_depth>10)
| table pxname, svname, up, queue_depth, sessions
```

Understanding this SPL

**HAProxy Backend and Frontend Health** — Backend server state, connection queue depth, and HTTP response distribution indicate load balancer effectiveness and backend capacity. Detection of DOWN backends or saturated queues enables rapid failover and scaling decisions.

Documented **Data sources**: HAProxy stats CSV (`/haproxy?stats;csv`), syslog. **App/TA** (typical add-on context): Custom (HAProxy stats socket/CSV, syslog). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: haproxy; **sourcetype**: haproxy:stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=haproxy, sourcetype="haproxy:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **backend_status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by pxname, svname, type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where type=="backend" AND (up==0 OR queue_depth>10)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **HAProxy Backend and Frontend Health**): table pxname, svname, up, queue_depth, sessions


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (backend × health), Table (backends with queue depth), Line chart (queue depth over time), Single value (DOWN backends count).

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
index=haproxy sourcetype="haproxy:stats"
| eval backend_status=case(status=="UP",1, status=="DOWN",0, 1=1,null())
| stats latest(backend_status) as up, latest(qcur) as queue_depth, latest(scur) as sessions by pxname, svname, type
| where type=="backend" AND (up==0 OR queue_depth>10)
| table pxname, svname, up, queue_depth, sessions
```

## Visualization

Status grid (backend × health), Table (backends with queue depth), Line chart (queue depth over time), Single value (DOWN backends count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
