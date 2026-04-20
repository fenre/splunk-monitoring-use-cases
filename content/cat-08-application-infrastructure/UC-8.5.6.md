---
id: "8.5.6"
title: "Slow Command Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.6 · Slow Command Detection

## Description

Slow Redis commands block the single-threaded event loop, impacting all clients. Detection enables command optimization.

## Value

Slow Redis commands block the single-threaded event loop, impacting all clients. Detection enables command optimization.

## Implementation

Run `redis-cli SLOWLOG GET 100` via scripted input every minute. Parse command, duration, and key pattern. Alert on commands exceeding 10ms. Identify O(N) commands (KEYS, SMEMBERS on large sets) for optimization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`SLOWLOG GET`).
• Ensure the following data sources are available: Redis SLOWLOG.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `redis-cli SLOWLOG GET 100` via scripted input every minute. Parse command, duration, and key pattern. Alert on commands exceeding 10ms. Identify O(N) commands (KEYS, SMEMBERS on large sets) for optimization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:slowlog"
| table _time, host, duration_ms, command, key
| where duration_ms > 10
| sort -duration_ms
```

Understanding this SPL

**Slow Command Detection** — Slow Redis commands block the single-threaded event loop, impacting all clients. Detection enables command optimization.

Documented **Data sources**: Redis SLOWLOG. **App/TA** (typical add-on context): Custom scripted input (`SLOWLOG GET`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:slowlog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:slowlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Slow Command Detection**): table _time, host, duration_ms, command, key
• Filters the current rows with `where duration_ms > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow commands with details), Bar chart (slow commands by type), Line chart (slow command frequency).

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
index=cache sourcetype="redis:slowlog"
| table _time, host, duration_ms, command, key
| where duration_ms > 10
| sort -duration_ms
```

## Visualization

Table (slow commands with details), Bar chart (slow commands by type), Line chart (slow command frequency).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
