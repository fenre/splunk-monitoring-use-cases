<!-- AUTO-GENERATED from UC-1.1.120.json — DO NOT EDIT -->

---
id: "1.1.120"
title: "Symbolic Link Chain Depth Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.120 · Symbolic Link Chain Depth Monitoring

## Description

Excessive symbolic link chains can cause performance issues and may indicate directory traversal vulnerabilities.

## Value

Excessive symbolic link chains can cause performance issues and may indicate directory traversal vulnerabilities.

## Implementation

Create a scripted input that recursively follows symbolic links counting chain depth. Alert when exceeding 10 levels. Include directory path for investigation of circular or excessive chains.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:symlink_scan`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that recursively follows symbolic links counting chain depth. Alert when exceeding 10 levels. Include directory path for investigation of circular or excessive chains.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:symlink_scan host=*
| stats max(chain_depth) as max_depth by host, directory
| where max_depth > 10
```

Understanding this SPL

**Symbolic Link Chain Depth Monitoring** — Excessive symbolic link chains can cause performance issues and may indicate directory traversal vulnerabilities.

Documented **Data sources**: `sourcetype=custom:symlink_scan`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:symlink_scan. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:symlink_scan. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, directory** so each row reflects one combination of those dimensions.
• Filters the current rows with `where max_depth > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

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
index=os sourcetype=custom:symlink_scan host=*
| stats max(chain_depth) as max_depth by host, directory
| where max_depth > 10
```

## Visualization

Table, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
