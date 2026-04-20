---
id: "8.3.2"
title: "Queue Depth Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.2 · Queue Depth Trending

## Description

Growing queue depths indicate consumers can't keep up or are down. Trending prevents message loss and processing delays.

## Value

Growing queue depths indicate consumers can't keep up or are down. Trending prevents message loss and processing delays.

## Implementation

Poll RabbitMQ management API every minute via scripted input. Track message count, publish/deliver rates per queue. Alert when depth exceeds threshold or grows consistently. Correlate with consumer status.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RabbitMQ management API, ActiveMQ JMX.
• Ensure the following data sources are available: RabbitMQ management API (`/api/queues`), ActiveMQ JMX.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll RabbitMQ management API every minute via scripted input. Track message count, publish/deliver rates per queue. Alert when depth exceeds threshold or grows consistently. Correlate with consumer status.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:queue"
| timechart span=5m max(messages) as depth by queue_name, vhost
| where depth > 1000
```

Understanding this SPL

**Queue Depth Trending** — Growing queue depths indicate consumers can't keep up or are down. Trending prevents message loss and processing delays.

Documented **Data sources**: RabbitMQ management API (`/api/queues`), ActiveMQ JMX. **App/TA** (typical add-on context): RabbitMQ management API, ActiveMQ JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:queue. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:queue". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by queue_name, vhost** — ideal for trending and alerting on this use case.
• Filters the current rows with `where depth > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue depth over time), Bar chart (top queues by depth), Table (queues exceeding threshold).

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
index=messaging sourcetype="rabbitmq:queue"
| timechart span=5m max(messages) as depth by queue_name, vhost
| where depth > 1000
```

## Visualization

Line chart (queue depth over time), Bar chart (top queues by depth), Table (queues exceeding threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
