---
id: "6.3.4"
title: "Backup Storage Capacity"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.4 · Backup Storage Capacity

## Description

Running out of backup repository space causes all backup jobs to fail. Proactive monitoring prevents cascading failures.

## Value

Running out of backup repository space causes all backup jobs to fail. Proactive monitoring prevents cascading failures.

## Implementation

Poll backup repository capacity via API or scripted input. Alert at 80% and 90% thresholds. Track growth rate and forecast when capacity will be exhausted using `predict`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, scripted input.
• Ensure the following data sources are available: Backup repository/tape library capacity metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll backup repository capacity via API or scripted input. Alert at 80% and 90% thresholds. Track growth rate and forecast when capacity will be exhausted using `predict`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:repository"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository_name, total_space_gb, used_space_gb, pct_used
```

Understanding this SPL

**Backup Storage Capacity** — Running out of backup repository space causes all backup jobs to fail. Proactive monitoring prevents cascading failures.

Documented **Data sources**: Backup repository/tape library capacity metrics. **App/TA** (typical add-on context): Vendor TA, scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:repository. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:repository". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct_used > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup Storage Capacity**): table repository_name, total_space_gb, used_space_gb, pct_used


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% used per repository), Line chart (capacity trend), Table (repositories above threshold).

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
index=backup sourcetype="veeam:repository"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository_name, total_space_gb, used_space_gb, pct_used
```

## Visualization

Gauge (% used per repository), Line chart (capacity trend), Table (repositories above threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
