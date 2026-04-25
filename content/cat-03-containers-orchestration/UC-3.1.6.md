<!-- AUTO-GENERATED from UC-3.1.6.json — DO NOT EDIT -->

---
id: "3.1.6"
title: "Privileged Container Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.6 · Privileged Container Detection

## Description

Privileged containers have full host access — a container escape gives root on the host. Should be flagged and justified in production.

## Value

Privileged containers have full host access — a container escape gives root on the host. Should be flagged and justified in production.

## Implementation

Create scripted input: `docker inspect --format '{{.Name}} {{.HostConfig.Privileged}}' $(docker ps -q)`. Run every 300 seconds. Alert on any privileged container in production. Maintain an allowlist for justified exceptions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Docker events, custom audit input.
• Ensure the following data sources are available: `docker inspect` output, Kubernetes pod security.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `docker inspect --format '{{.Name}} {{.HostConfig.Privileged}}' $(docker ps -q)`. Run every 300 seconds. Alert on any privileged container in production. Maintain an allowlist for justified exceptions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:inspect"
| where Privileged="true"
| table container_name image host Privileged
```

Understanding this SPL

**Privileged Container Detection** — Privileged containers have full host access — a container escape gives root on the host. Should be flagged and justified in production.

Documented **Data sources**: `docker inspect` output, Kubernetes pod security. **App/TA** (typical add-on context): Docker events, custom audit input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:inspect. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:inspect". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Privileged="true"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Privileged Container Detection**): table container_name image host Privileged


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (container, image, host), Single value (count of privileged), Status indicator.

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
index=containers sourcetype="docker:inspect"
| where Privileged="true"
| table container_name image host Privileged
```

## Visualization

Table (container, image, host), Single value (count of privileged), Status indicator.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
