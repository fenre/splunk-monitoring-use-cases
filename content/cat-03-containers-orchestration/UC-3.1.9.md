<!-- AUTO-GENERATED from UC-3.1.9.json — DO NOT EDIT -->

---
id: "3.1.9"
title: "Docker Daemon Health and Version Drift"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.9 · Docker Daemon Health and Version Drift

## Description

Mixed Docker Engine versions break image compatibility and CVE patching cadence; silent `ServerErrors` in the daemon log precede pull and run failures. Standardize on a patch channel and alert before user-facing container failures cascade.

## Value

Mixed Docker Engine versions break image compatibility and CVE patching cadence; silent `ServerErrors` in the daemon log precede pull and run failures. Standardize on a patch channel and alert before user-facing container failures cascade.

## Implementation

Create scripted input that runs `docker info --format '{{json .}}'` and `docker version --format '{{json .}}'` every 300 seconds. Parse ServerVersion, ServerErrors, Containers, Images, and DriverStatus. Forward to Splunk via HEC. Alert when Docker daemon is unresponsive (no data for >5 minutes) or when ServerErrors is non-empty. Report version drift: alert when multiple Engine versions exist across the fleet.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (docker info, docker version).
• Ensure the following data sources are available: docker info JSON output, docker version.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input that runs `docker info --format '{{json .}}'` and `docker version --format '{{json .}}'` every 300 seconds. Parse ServerVersion, ServerErrors, Containers, Images, and DriverStatus. Forward to Splunk via HEC. Alert when Docker daemon is unresponsive (no data for >5 minutes) or when ServerErrors is non-empty. Report version drift: alert when multiple Engine versions exist across the fleet.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:info"
| stats values(ServerVersion) as versions by host
| eval version_count = mvcount(versions)
| where version_count > 1
| mvexpand versions limit=100
| table host versions
```

Understanding this SPL

**Docker Daemon Health and Version Drift** — Mixed Docker Engine versions break image compatibility and CVE patching cadence; silent `ServerErrors` in the daemon log precede pull and run failures. Standardize on a patch channel and alert before user-facing container failures cascade.

Documented **Data sources**: docker info JSON output, docker version. **App/TA** (typical add-on context): Custom scripted input (docker info, docker version). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **version_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where version_count > 1` — typically the threshold or rule expression for this monitoring goal.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Pipeline stage (see **Docker Daemon Health and Version Drift**): table host versions


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, version, containers, images), Single value (version count), Status grid (host health).

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
index=containers sourcetype="docker:info"
| stats values(ServerVersion) as versions by host
| eval version_count = mvcount(versions)
| where version_count > 1
| mvexpand versions limit=100
| table host versions
```

## Visualization

Table (host, version, containers, images), Single value (version count), Status grid (host health).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
